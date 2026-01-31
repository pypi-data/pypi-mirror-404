"""lucid passport – View AI passports via the Verifier API."""

import json as _json

import typer

from lucid_cli.client import APIError, LucidClient
from lucid_cli.config import require_auth

app = typer.Typer()


def _get_client() -> LucidClient:
    return LucidClient(require_auth())


@app.command("list")
def list_passports(
    limit: int = typer.Option(20, "--limit", help="Max results"),
    offset: int = typer.Option(0, "--offset", help="Offset for pagination"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List AI passports."""
    client = _get_client()

    try:
        data = client.list_passports(limit=limit, offset=offset)
    except APIError as exc:
        typer.echo(f"Error: {exc.detail}", err=True)
        raise typer.Exit(code=1)

    items = data if isinstance(data, list) else data.get("items", data.get("passports", []))

    if output_json:
        typer.echo(_json.dumps(data, indent=2))
        return

    if not items:
        typer.echo("No passports found.")
        return

    typer.echo(
        f"{'PASSPORT ID':<38} {'MODEL':<20} {'SESSION':<20} {'EVIDENCE':<12} {'CREATED':<20}"
    )
    typer.echo("-" * 110)
    for p in items:
        typer.echo(
            f"{str(p.get('id', '')):<38} "
            f"{str(p.get('model', '')):<20} "
            f"{str(p.get('session_id', '')):<20} "
            f"{str(p.get('evidence_count', '')):<12} "
            f"{str(p.get('created_at', '')):<20}"
        )


@app.command("show")
def show(
    passport_id: str = typer.Argument(..., help="Passport ID"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show passport details."""
    client = _get_client()

    try:
        data = client.get_passport(passport_id)
    except APIError as exc:
        typer.echo(f"Error: {exc.detail}", err=True)
        raise typer.Exit(code=1)

    if output_json:
        typer.echo(_json.dumps(data, indent=2))
    else:
        for key, val in data.items():
            if key == "hardware_attestation" and isinstance(val, dict):
                typer.echo(f"  {key}:")
                for hk, hv in val.items():
                    typer.echo(f"    {hk}: {hv}")
            elif key == "evidence" and isinstance(val, list):
                typer.echo(f"  {key}: ({len(val)} items)")
                for i, ev in enumerate(val):
                    typer.echo(f"    [{i}] {ev}")
            else:
                typer.echo(f"  {key}: {val}")


@app.callback()
def callback() -> None:
    """View AI passports."""
