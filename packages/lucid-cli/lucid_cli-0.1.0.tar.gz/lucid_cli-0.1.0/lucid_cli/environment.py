"""lucid environment – Deploy LucidEnvironment CRD to a cluster."""

import json as _json
import subprocess
from pathlib import Path
from typing import Optional

import typer
import yaml

from lucid_schemas import LucidEnvironment, LucidEnvironmentSpec, CloudProvider
from pydantic import ValidationError

from lucid_cli.client import APIError, LucidClient
from lucid_cli.config import require_auth

app = typer.Typer()


# ── Infrastructure helpers ────────────────────────────────────────────


def _check_kubectl() -> bool:
    """Check if kubectl is available and configured."""
    try:
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _check_operator_installed(namespace: str = "lucid-system") -> bool:
    """Check if Lucid operator is installed in the cluster."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "deployment", "lucid-operator", "-n", namespace],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _provision_infrastructure(env: LucidEnvironment) -> bool:
    """Provision cloud infrastructure based on the environment spec."""
    infra = env.spec.infrastructure
    provider = infra.provider

    if provider == CloudProvider.LOCAL:
        typer.echo("[*] Local provider - skipping infrastructure provisioning")
        return True

    # Import cloud providers
    try:
        from lucid_cli.providers import get_provider
    except ImportError:
        typer.echo("[!] Cloud providers not available", err=True)
        return False

    project_id = infra.project_id or ""
    if provider == CloudProvider.AZURE:
        project_id = infra.resource_group or project_id

    if not project_id:
        typer.echo(f"[!] Project/account ID required for {provider.value}", err=True)
        return False

    typer.echo(f"[*] Provisioning {provider.value.upper()} infrastructure...")
    try:
        p = get_provider(provider.value, project_id, infra.region)
        p.provision_cluster(infra.cluster.name)
        p.get_kubeconfig(infra.cluster.name)
        typer.echo(f"[+] Infrastructure provisioned: {infra.cluster.name}")
        return True
    except Exception as e:
        typer.echo(f"[!] Infrastructure provisioning failed: {e}", err=True)
        return False


def _setup_cluster(env: LucidEnvironment, mock: bool = False) -> bool:
    """Setup Lucid operator in the cluster.

    Creates namespace and deploys the Lucid operator with basic RBAC.
    """
    import os

    namespace = "lucid-system"
    is_mock = mock or env.spec.infrastructure.provider == CloudProvider.LOCAL

    # Resolve operator image
    registry = os.getenv("LUCID_REGISTRY", "")
    tag = os.getenv("LUCID_TAG", "latest")
    if registry:
        if not registry.endswith("/"):
            registry += "/"
        operator_image = f"{registry}lucid-operator:{tag}"
    else:
        operator_image = f"lucid-operator:{tag}"

    typer.echo(f"[*] Setting up Lucid operator (image: {operator_image})...")

    # 1. Create namespace
    try:
        subprocess.run(
            ["kubectl", "create", "namespace", namespace],
            check=True, capture_output=True
        )
        typer.echo(f"[+] Namespace '{namespace}' created")
    except subprocess.CalledProcessError:
        typer.echo(f"[*] Namespace '{namespace}' already exists")

    # 2. Apply operator manifest
    operator_manifest = f"""
apiVersion: v1
kind: ServiceAccount
metadata:
  name: lucid-operator
  namespace: {namespace}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: lucid-operator-role
rules:
- apiGroups: [""]
  resources: ["configmaps", "pods"]
  verbs: ["get", "list", "watch", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: lucid-operator-binding
subjects:
- kind: ServiceAccount
  name: lucid-operator
  namespace: {namespace}
roleRef:
  kind: ClusterRole
  name: lucid-operator-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lucid-operator
  namespace: {namespace}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: lucid-operator
  template:
    metadata:
      labels:
        app: lucid-operator
    spec:
      serviceAccountName: lucid-operator
      containers:
      - name: operator
        image: {operator_image}
        imagePullPolicy: {"Never" if is_mock else "IfNotPresent"}
        ports:
        - containerPort: 8443
        env:
        - name: TEE_PROVIDER
          value: {"MOCK" if is_mock else "COCO"}
---
apiVersion: v1
kind: Service
metadata:
  name: lucid-operator
  namespace: {namespace}
spec:
  ports:
  - port: 443
    targetPort: 8443
  selector:
    app: lucid-operator
"""

    try:
        subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=operator_manifest.encode(),
            check=True,
            capture_output=True
        )
        typer.echo("[+] Lucid operator deployed")

        # Wait for rollout
        typer.echo("[*] Waiting for operator to be ready...")
        result = subprocess.run(
            ["kubectl", "rollout", "status", "deployment/lucid-operator",
             f"-n={namespace}", "--timeout=120s"],
            capture_output=True
        )
        if result.returncode == 0:
            typer.echo("[+] Lucid operator is ready")
            return True
        else:
            typer.echo("[!] Operator rollout timed out, continuing anyway...")
            return True

    except subprocess.CalledProcessError as e:
        typer.echo(f"[!] Failed to deploy operator: {e}", err=True)
        return False


def _load_environment(file: str) -> LucidEnvironment:
    """Load and validate a LucidEnvironment from a YAML file."""
    path = Path(file)
    if not path.exists():
        raise typer.BadParameter(f"File not found: {file}")

    with open(path) as f:
        data = yaml.safe_load(f)

    # Validate it's a LucidEnvironment
    kind = data.get("kind", "")
    if kind != "LucidEnvironment":
        raise typer.BadParameter(
            f"Invalid kind: '{kind}'. Expected 'LucidEnvironment'. "
            f"Is this a LucidEnvironment YAML file?"
        )

    try:
        return LucidEnvironment(**data)
    except ValidationError as e:
        typer.echo("Validation errors:", err=True)
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            typer.echo(f"  {loc}: {error['msg']}", err=True)
        raise typer.Exit(code=1)


def _get_client() -> LucidClient:
    """Get authenticated API client."""
    return LucidClient(require_auth())


# ── plan ─────────────────────────────────────────────────────────────


@app.command()
def plan(
    file: str = typer.Option(..., "-f", "--file", help="LucidEnvironment YAML file"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show what would be deployed (dry-run)."""
    env = _load_environment(file)

    if output_json:
        typer.echo(_json.dumps(env.model_dump(by_alias=True), indent=2))
        return

    typer.echo(f"Environment: {env.metadata.name}")
    typer.echo(f"  Namespace: {env.metadata.namespace}")
    typer.echo()

    # Infrastructure
    infra = env.spec.infrastructure
    typer.echo("Infrastructure:")
    typer.echo(f"  Provider: {infra.provider.value}")
    typer.echo(f"  Region:   {infra.region}")
    if infra.project_id:
        typer.echo(f"  Project:  {infra.project_id}")
    typer.echo(f"  Cluster:  {infra.cluster.name}")
    typer.echo(f"  CC Mode:  {infra.confidential_computing.enabled}")
    if infra.cluster.node_pools:
        typer.echo(f"  Node Pools:")
        for pool in infra.cluster.node_pools:
            gpu_info = f", GPU: {pool.gpu_type} x{pool.gpu_count}" if pool.gpu_type else ""
            typer.echo(f"    - {pool.name} ({pool.machine_type}{gpu_info})")
    typer.echo()

    # Agents
    typer.echo(f"Agents ({len(env.spec.agents)}):")
    for agent in env.spec.agents:
        status = "enabled" if agent.enabled else "disabled"
        typer.echo(f"  - {agent.name} [{status}]")
        typer.echo(f"      Model: {agent.model.id}")
        typer.echo(f"      GPU:   {agent.gpu.type} ({agent.gpu.memory})")
        if agent.audit_chain:
            auditor_count = (
                len(agent.audit_chain.pre_request) +
                len(agent.audit_chain.request) +
                len(agent.audit_chain.response) +
                len(agent.audit_chain.post_response)
            )
            typer.echo(f"      Auditors: {auditor_count}")
    typer.echo()

    # Apps
    if env.spec.apps:
        typer.echo(f"Apps ({len(env.spec.apps)}):")
        for app_spec in env.spec.apps:
            status = "enabled" if app_spec.enabled else "disabled"
            typer.echo(f"  - {app_spec.app_id} [{status}]")
            typer.echo(f"      TEE Mode: {app_spec.tee_mode.value}")
        typer.echo()

    # Services
    services = env.spec.services
    typer.echo("Services:")
    typer.echo(f"  Observability: {'enabled' if services.observability.enabled else 'disabled'}")
    typer.echo(f"  Gateway:       {'enabled' if services.gateway.enabled else 'disabled'} ({services.gateway.type.value})")
    typer.echo(f"  Vector DB:     {'enabled' if services.vector_db.enabled else 'disabled'}")

    typer.echo()
    typer.echo("Run 'lucid environment apply -f <file>' to deploy.")


# ── apply ────────────────────────────────────────────────────────────


@app.command()
def apply(
    file: str = typer.Option(..., "-f", "--file", help="LucidEnvironment YAML file"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate only, don't deploy"),
    skip_infra: bool = typer.Option(False, "--skip-infra", help="Skip infrastructure provisioning"),
    skip_cluster: bool = typer.Option(False, "--skip-cluster", help="Skip cluster setup"),
    mock: bool = typer.Option(False, "--mock", help="Use mock attestation mode"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Deploy a LucidEnvironment to the cluster.

    This command orchestrates the full deployment:
    1. Provisions cloud infrastructure (if provider != local)
    2. Sets up Lucid operator in the cluster (if not present)
    3. Deploys agents via the Verifier API
    4. Deploys apps (when available)

    Use --skip-infra to skip infrastructure provisioning.
    Use --skip-cluster to skip operator setup.
    """
    env = _load_environment(file)
    infra = env.spec.infrastructure

    if dry_run:
        typer.echo("Dry run: validation passed.")
        typer.echo(f"Would deploy:")
        typer.echo(f"  - Infrastructure: {infra.provider.value} / {infra.region}")
        typer.echo(f"  - Cluster: {infra.cluster.name}")
        typer.echo(f"  - {len(env.spec.agents)} agent(s)")
        typer.echo(f"  - {len(env.spec.apps)} app(s)")
        return

    # Confirmation
    if not yes:
        typer.echo(f"This will deploy:")
        typer.echo(f"  - Infrastructure: {infra.provider.value} / {infra.region}")
        typer.echo(f"  - Cluster: {infra.cluster.name}")
        typer.echo(f"  - {len(env.spec.agents)} agent(s)")
        typer.echo(f"  - {len(env.spec.apps)} app(s)")
        if infra.provider != CloudProvider.LOCAL and not skip_infra:
            typer.echo(f"  - Will provision {infra.provider.value.upper()} resources (this may incur costs)")
        confirm = typer.confirm("Proceed?")
        if not confirm:
            typer.echo("Aborted.")
            raise typer.Exit()

    results = {"infrastructure": None, "cluster": None, "agents": [], "apps": [], "errors": []}

    # Step 1: Provision infrastructure (if needed)
    if not skip_infra and infra.provider != CloudProvider.LOCAL:
        typer.echo()
        typer.echo("=" * 50)
        typer.echo("Step 1: Infrastructure Provisioning")
        typer.echo("=" * 50)
        if _provision_infrastructure(env):
            results["infrastructure"] = "provisioned"
        else:
            results["errors"].append({"step": "infrastructure", "error": "provisioning failed"})
            if not yes:
                if not typer.confirm("Infrastructure provisioning failed. Continue anyway?"):
                    raise typer.Exit(code=1)

    # Step 2: Setup cluster (if operator not present)
    if not skip_cluster:
        typer.echo()
        typer.echo("=" * 50)
        typer.echo("Step 2: Cluster Setup")
        typer.echo("=" * 50)
        if _check_kubectl():
            if _check_operator_installed():
                typer.echo("[+] Lucid operator already installed")
                results["cluster"] = "already_installed"
            else:
                typer.echo("[*] Lucid operator not found, installing...")
                if _setup_cluster(env, mock=mock):
                    results["cluster"] = "installed"
                else:
                    results["errors"].append({"step": "cluster", "error": "setup failed"})
                    if not yes:
                        if not typer.confirm("Cluster setup failed. Continue anyway?"):
                            raise typer.Exit(code=1)
        else:
            typer.echo("[!] kubectl not available or cluster not reachable", err=True)
            results["errors"].append({"step": "cluster", "error": "kubectl not available"})

    # Step 3: Deploy agents
    typer.echo()
    typer.echo("=" * 50)
    typer.echo("Step 3: Agent Deployment")
    typer.echo("=" * 50)

    client = _get_client()

    # Deploy agents
    for agent_spec in env.spec.agents:
        if not agent_spec.enabled:
            typer.echo(f"Skipping disabled agent: {agent_spec.name}")
            continue

        typer.echo(f"Creating agent: {agent_spec.name}...")

        # Convert AgentSpec to CreateAgentRequest format
        agent_body = {
            "name": agent_spec.name,
            "model": {
                "id": agent_spec.model.id,
                "name": agent_spec.model.name or agent_spec.model.id.split("/")[-1],
            },
            "gpu": {
                "type": agent_spec.gpu.type,
                "region": env.spec.infrastructure.region,
                "ccMode": env.spec.infrastructure.confidential_computing.enabled,
                "provider": env.spec.infrastructure.provider.value,
            },
            "auditChain": {},
        }

        # Convert audit chain if present
        if agent_spec.audit_chain:
            agent_body["auditChain"] = {
                "pre_request": [a.model_dump(by_alias=True) for a in agent_spec.audit_chain.pre_request],
                "request": [a.model_dump(by_alias=True) for a in agent_spec.audit_chain.request],
                "response": [a.model_dump(by_alias=True) for a in agent_spec.audit_chain.response],
                "post_response": [a.model_dump(by_alias=True) for a in agent_spec.audit_chain.post_response],
            }

        if agent_spec.frontend_app:
            agent_body["frontendApp"] = agent_spec.frontend_app.model_dump(by_alias=True)

        if agent_spec.passport_display:
            agent_body["passportDisplay"] = agent_spec.passport_display.model_dump(by_alias=True)

        try:
            result = client.create_agent(agent_body)
            results["agents"].append({"name": agent_spec.name, "id": result.get("id"), "status": "created"})
            typer.echo(f"  Created: {result.get('id', 'unknown')}")
        except APIError as exc:
            results["errors"].append({"name": agent_spec.name, "error": exc.detail})
            typer.echo(f"  Error: {exc.detail}", err=True)

    # Step 4: Deploy apps (placeholder)
    if env.spec.apps:
        typer.echo()
        typer.echo("=" * 50)
        typer.echo("Step 4: App Deployment")
        typer.echo("=" * 50)
        typer.echo(f"[*] {len(env.spec.apps)} app(s) configured (app deployment via API coming soon)")

    # Summary
    typer.echo()
    typer.echo("=" * 50)
    typer.echo("Deployment Summary")
    typer.echo("=" * 50)

    if output_json:
        typer.echo(_json.dumps(results, indent=2))
    else:
        if results.get("infrastructure"):
            typer.echo(f"  Infrastructure: {results['infrastructure']}")
        if results.get("cluster"):
            typer.echo(f"  Cluster:        {results['cluster']}")
        typer.echo(f"  Agents:         {len(results['agents'])} deployed")
        if results["errors"]:
            typer.echo(f"  Errors:         {len(results['errors'])}")
            for err in results["errors"]:
                typer.echo(f"    - {err}")
        typer.echo()
        if not results["errors"]:
            typer.echo("[+] Environment deployed successfully!")
        else:
            typer.echo("[!] Environment deployed with errors")


# ── validate ─────────────────────────────────────────────────────────


@app.command()
def validate(
    file: str = typer.Option(..., "-f", "--file", help="LucidEnvironment YAML file"),
) -> None:
    """Validate a LucidEnvironment YAML file."""
    env = _load_environment(file)
    typer.echo(f"Valid LucidEnvironment: {env.metadata.name}")
    typer.echo(f"  Agents: {len(env.spec.agents)}")
    typer.echo(f"  Apps:   {len(env.spec.apps)}")


# ── export ───────────────────────────────────────────────────────────


@app.command("export")
def export_env(
    name: str = typer.Argument(..., help="Environment name to export"),
    output: str = typer.Option("", "-o", "--output", help="Output file (default: stdout)"),
) -> None:
    """Export current cluster state as LucidEnvironment YAML."""
    client = _get_client()

    try:
        # Get all agents
        agents_data = client.list_agents(limit=100)
        agents = agents_data if isinstance(agents_data, list) else agents_data.get("agents", [])
    except APIError as exc:
        typer.echo(f"Error fetching agents: {exc.detail}", err=True)
        raise typer.Exit(code=1)

    # Build LucidEnvironment from current state
    env_dict = {
        "apiVersion": "lucid.io/v1alpha1",
        "kind": "LucidEnvironment",
        "metadata": {
            "name": name,
            "namespace": "default",
            "labels": {},
            "annotations": {"lucid.io/exported-from": "cluster"},
        },
        "spec": {
            "infrastructure": {
                "provider": "local",
                "region": "local",
                "confidentialComputing": {"enabled": False, "teeType": "sev-snp"},
                "cluster": {
                    "name": f"{name}-cluster",
                    "kubernetesVersion": "1.29",
                    "nodePools": [],
                    "networking": {},
                    "security": {},
                },
            },
            "agents": [],
            "apps": [],
            "services": {
                "observability": {"enabled": True},
                "gateway": {"enabled": True, "type": "istio"},
                "vectorDb": {"enabled": False},
            },
        },
    }

    # Convert agents to AgentSpec format
    for agent in agents:
        agent_spec = {
            "name": agent.get("name", ""),
            "model": agent.get("model", {}),
            "gpu": {
                "type": agent.get("gpu", {}).get("type", "CPU"),
                "memory": "80GB",
                "count": 1,
            },
            "auditChain": agent.get("auditChain", agent.get("audit_chain", {})),
            "replicas": 1,
            "enabled": agent.get("status") != "stopped",
        }
        env_dict["spec"]["agents"].append(agent_spec)

    yaml_output = yaml.dump(env_dict, default_flow_style=False, sort_keys=False)

    if output:
        with open(output, "w") as f:
            f.write(yaml_output)
        typer.echo(f"Exported to {output}")
    else:
        typer.echo(yaml_output)


@app.callback()
def callback() -> None:
    """Manage LucidEnvironment deployments."""
