"""lucid agent – Manage AI agents via the Verifier API."""

import json as _json
from typing import Annotated, Optional

import typer
import yaml

from lucid_cli.client import APIError, LucidClient
from lucid_cli.config import require_auth

app = typer.Typer()


def _get_client() -> LucidClient:
    return LucidClient(require_auth())


# ── create ────────────────────────────────────────────────────────


@app.command()
def create(
    name: str = typer.Option("", "--name", "-n", help="Agent name"),
    model: str = typer.Option("", "--model", help="Model identifier"),
    model_name: str = typer.Option("", "--model-name", help="Model display name"),
    gpu: str = typer.Option("", "--gpu", help="GPU type (e.g. A100, H100)"),
    region: str = typer.Option("", "--region", help="Deployment region"),
    gpu_provider: str = typer.Option("", "--gpu-provider", help="GPU provider"),
    cc_mode: str = typer.Option("", "--cc-mode", help="Confidential computing mode"),
    app_list: Annotated[Optional[list[str]], typer.Option("--app", help="App to install (repeatable)")] = None,
    auditor_profile: str = typer.Option("", "--auditor-profile", help="Auditor profile name"),
    file: str = typer.Option("", "-f", "--file", help="YAML manifest file"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Create a new AI agent."""
    client = _get_client()

    if file:
        with open(file) as fh:
            body = yaml.safe_load(fh)
    else:
        body: dict = {}
        if name:
            body["name"] = name
        if model:
            body["model"] = model
        if model_name:
            body["model_name"] = model_name
        if gpu:
            body["gpu"] = gpu
        if region:
            body["region"] = region
        if gpu_provider:
            body["gpu_provider"] = gpu_provider
        if cc_mode:
            body["cc_mode"] = cc_mode
        if app_list:
            body["apps"] = app_list
        if auditor_profile:
            body["auditor_profile"] = auditor_profile

    try:
        result = client.create_agent(body)
    except APIError as exc:
        typer.echo(f"Error: {exc.detail}", err=True)
        raise typer.Exit(code=1)

    if output_json:
        typer.echo(_json.dumps(result, indent=2))
    else:
        typer.echo(f"Agent created: {result.get('id', 'unknown')}")
        if result.get("name"):
            typer.echo(f"  Name:   {result['name']}")
        if result.get("status"):
            typer.echo(f"  Status: {result['status']}")


# ── list ──────────────────────────────────────────────────────────


@app.command("list")
def list_agents(
    limit: int = typer.Option(20, "--limit", help="Max results"),
    offset: int = typer.Option(0, "--offset", help="Offset for pagination"),
    management_type: str = typer.Option("", "--type", help="Filter by management type"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List AI agents."""
    client = _get_client()

    try:
        data = client.list_agents(
            limit=limit,
            offset=offset,
            management_type=management_type or None,
        )
    except APIError as exc:
        typer.echo(f"Error: {exc.detail}", err=True)
        raise typer.Exit(code=1)

    items = data if isinstance(data, list) else data.get("items", data.get("agents", []))

    if output_json:
        typer.echo(_json.dumps(data, indent=2))
        return

    if not items:
        typer.echo("No agents found.")
        return

    # Table header
    typer.echo(f"{'ID':<38} {'NAME':<20} {'STATUS':<12} {'MODEL':<15} {'GPU':<8} {'CREATED':<20}")
    typer.echo("-" * 113)
    for a in items:
        typer.echo(
            f"{str(a.get('id', '')):<38} "
            f"{str(a.get('name', '')):<20} "
            f"{str(a.get('status', '')):<12} "
            f"{str(a.get('model', '')):<15} "
            f"{str(a.get('gpu', '')):<8} "
            f"{str(a.get('created_at', '')):<20}"
        )


# ── status ────────────────────────────────────────────────────────


@app.command()
def status(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    k8s: bool = typer.Option(False, "--k8s", help="Show Kubernetes status details"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show agent status."""
    client = _get_client()

    try:
        if k8s:
            data = client.get_agent_k8s_status(agent_id)
        else:
            data = client.get_agent(agent_id)
    except APIError as exc:
        typer.echo(f"Error: {exc.detail}", err=True)
        raise typer.Exit(code=1)

    if output_json:
        typer.echo(_json.dumps(data, indent=2))
    else:
        for key, val in data.items():
            typer.echo(f"  {key}: {val}")


# ── logs ──────────────────────────────────────────────────────────


@app.command()
def logs(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    follow: bool = typer.Option(True, "--follow/--no-follow", help="Stream logs via SSE"),
    container: str = typer.Option("", "-c", "--container", help="Specific container name"),
    tail: int = typer.Option(100, "--tail", help="Number of tail lines"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """View agent logs."""
    client = _get_client()

    try:
        if container:
            data = client.get_container_logs(agent_id, container, tail_lines=tail)
            if output_json:
                typer.echo(_json.dumps(data, indent=2))
            else:
                if isinstance(data, dict):
                    for line in data.get("logs", []):
                        typer.echo(line)
                else:
                    typer.echo(data)
            return

        if follow:
            for line in client.stream_agent_logs(agent_id):
                typer.echo(line)
        else:
            data = client.get_container_logs(agent_id, "", tail_lines=tail)
            if output_json:
                typer.echo(_json.dumps(data, indent=2))
            else:
                if isinstance(data, dict):
                    for line in data.get("logs", []):
                        typer.echo(line)
                else:
                    typer.echo(data)
    except APIError as exc:
        typer.echo(f"Error: {exc.detail}", err=True)
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        typer.echo("\nLog streaming stopped.")


# ── start ─────────────────────────────────────────────────────────


@app.command()
def start(agent_id: str = typer.Argument(..., help="Agent ID")) -> None:
    """Start an agent."""
    client = _get_client()
    try:
        client.start_agent(agent_id)
        typer.echo(f"Agent {agent_id} started.")
    except APIError as exc:
        typer.echo(f"Error: {exc.detail}", err=True)
        raise typer.Exit(code=1)


# ── stop ──────────────────────────────────────────────────────────


@app.command()
def stop(agent_id: str = typer.Argument(..., help="Agent ID")) -> None:
    """Stop an agent."""
    client = _get_client()
    try:
        client.stop_agent(agent_id)
        typer.echo(f"Agent {agent_id} stopped.")
    except APIError as exc:
        typer.echo(f"Error: {exc.detail}", err=True)
        raise typer.Exit(code=1)


# ── delete ────────────────────────────────────────────────────────


@app.command()
def delete(
    agent_id: str = typer.Argument(..., help="Agent ID"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation"),
) -> None:
    """Delete an agent."""
    if not yes:
        confirm = typer.confirm(f"Delete agent {agent_id}?")
        if not confirm:
            typer.echo("Aborted.")
            raise typer.Exit()

    client = _get_client()
    try:
        client.delete_agent(agent_id)
        typer.echo(f"Agent {agent_id} deleted.")
    except APIError as exc:
        typer.echo(f"Error: {exc.detail}", err=True)
        raise typer.Exit(code=1)


@app.callback()
def callback() -> None:
    """Manage AI agents."""
