"""lucid catalog – Browse the app catalog via the Verifier API."""

import json as _json

import typer

from lucid_cli.client import APIError, LucidClient
from lucid_cli.config import require_auth

app = typer.Typer()


def _get_client() -> LucidClient:
    return LucidClient(require_auth())


@app.command("apps")
def apps(
    category: str = typer.Option("", "-c", "--category", help="Filter by category"),
    verified: bool = typer.Option(False, "--verified", help="Show only verified apps"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List apps in the catalog."""
    client = _get_client()

    try:
        data = client.list_catalog_apps(
            category=category or None,
            verified_only=verified,
        )
    except APIError as exc:
        typer.echo(f"Error: {exc.detail}", err=True)
        raise typer.Exit(code=1)

    items = data if isinstance(data, list) else data.get("items", data.get("apps", []))

    if output_json:
        typer.echo(_json.dumps(data, indent=2))
        return

    if not items:
        typer.echo("No apps found.")
        return

    typer.echo(f"{'ID':<38} {'NAME':<25} {'CATEGORY':<15} {'VERIFIED':<10} {'TEE':<8}")
    typer.echo("-" * 96)
    for a in items:
        typer.echo(
            f"{str(a.get('id', '')):<38} "
            f"{str(a.get('name', '')):<25} "
            f"{str(a.get('category', '')):<15} "
            f"{str(a.get('verified', '')):<10} "
            f"{str(a.get('tee', '')):<8}"
        )


@app.command("show")
def show(
    app_id: str = typer.Argument(..., help="App ID"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show details for a catalog app."""
    client = _get_client()

    try:
        data = client.get_catalog_app(app_id)
    except APIError as exc:
        typer.echo(f"Error: {exc.detail}", err=True)
        raise typer.Exit(code=1)

    if output_json:
        typer.echo(_json.dumps(data, indent=2))
    else:
        for key, val in data.items():
            typer.echo(f"  {key}: {val}")


@app.callback()
def callback() -> None:
    """Browse the app catalog."""
