# Lucid CLI (`lucid`)

Command-line interface for deploying and managing AI agents on the Lucid platform.

## Installation

```bash
# From monorepo
uv sync

# External users
pip install lucid-cli
```

## Authentication

```bash
lucid login                           # Interactive login
LUCID_API_KEY=<key> lucid login       # API key via environment
```

## Commands

| Command | Description |
|---------|-------------|
| `lucid login` | Authenticate with Lucid platform |
| `lucid agent` | Manage AI agents (create, list, start, stop, delete, logs) |
| `lucid environment` | Deploy full environments from YAML |
| `lucid catalog` | Browse app catalog |
| `lucid passport` | View AI passports |
| `lucid auditor` | Verify and publish auditor images |

## Quick Start

```bash
# Authenticate
lucid login

# List agents
lucid agent list

# Deploy from environment file
lucid environment apply -f my-environment.yaml

# Preview what would be deployed
lucid environment plan -f my-environment.yaml
```

## LucidEnvironment: Shared Contract

The `LucidEnvironment` YAML format is the shared contract between the CLI and the Observer GUI:

- **Observer GUI**: Users configure deployments via the wizard, then export as `LucidEnvironment` YAML
- **CLI**: Users write or import `LucidEnvironment` YAML, then deploy with `lucid environment apply`

Both tools produce/consume the same format, enabling:
- Version control of environment configurations
- Reproducible deployments across teams
- Migration between self-hosted and Lucid-managed deployments

### Example LucidEnvironment

```yaml
apiVersion: lucid.io/v1alpha1
kind: LucidEnvironment
metadata:
  name: my-platform
spec:
  infrastructure:
    provider: gcp                    # gcp | aws | azure | local
    region: us-central1
    projectId: my-project
    confidentialComputing:
      enabled: true
      teeType: sev-snp
    cluster:
      name: lucid-prod
      kubernetesVersion: "1.29"
      nodePools:
        - name: gpu-pool
          machineType: a3-highgpu-8g
          gpuType: nvidia-h100-80gb
          gpuCount: 8

  agents:
    - name: llama-assistant
      model:
        id: meta-llama/Llama-3.3-70B
      gpu:
        type: H100
        memory: 80GB
      auditChain:
        preRequest:
          - auditorId: injection-detector
            name: Injection Detector

  apps:
    - appId: openhands
      teeMode: adjacent

  services:
    observability:
      enabled: true
    gateway:
      type: istio
```

### Deployment Workflow

```bash
# 1. Export from Observer GUI or write manually
#    → my-environment.yaml

# 2. Preview the deployment
lucid environment plan -f my-environment.yaml

# 3. Deploy everything (infra + operator + agents)
lucid environment apply -f my-environment.yaml

# 4. Skip infrastructure if cluster already exists
lucid environment apply -f my-environment.yaml --skip-infra

# 5. Use mock mode for local development
lucid environment apply -f my-environment.yaml --mock
```

## Self-Hosted vs Lucid-Managed

| Aspect | Self-Hosted (CLI) | Lucid-Managed (Observer GUI) |
|--------|-------------------|------------------------------|
| Infrastructure | You provision via CLI or existing cluster | Lucid provisions |
| Operator | CLI installs automatically | Lucid manages |
| Agents | Deployed to your cluster | Deployed to Lucid infrastructure |
| Control | Full control, your cluster | Managed service |
| Format | LucidEnvironment YAML | LucidEnvironment YAML |

The same `LucidEnvironment` YAML works in both scenarios—only the deployment target differs.

## Documentation

- [CLI Reference](../../packages/lucid-docs/reference/cli-reference.md)
- [LucidEnvironment Schema](../../packages/lucid-schemas/lucid_schemas/environment.py)
