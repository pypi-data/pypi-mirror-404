"""lucid login – Authenticate with the Lucid platform."""

import os
from urllib.parse import urlparse

import typer

from lucid_cli.client import APIError, LucidClient
from lucid_cli.config import LucidConfig, load_config, save_config

app = typer.Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
def login(
    email: str = typer.Option("", "-e", "--email", help="Account email address"),
    api_url: str = typer.Option("", "--api-url", help="Override API base URL"),
    generate_key: bool = typer.Option(
        False, "--generate-key", help="Generate a persistent API key after login"
    ),
) -> None:
    """Authenticate with the Lucid platform.

    Supports two modes:
      1. Email/password login (JWT, optionally generates API key)
      2. Direct API key via LUCID_API_KEY environment variable

    Credentials are accepted via environment variables or interactive prompt
    to avoid exposure in process listings and shell history.

    Environment variables:
      LUCID_API_KEY   - API key for direct authentication
      LUCID_PASSWORD  - Password (falls back to interactive prompt)
    """
    config = load_config()

    if api_url:
        config.api_url = api_url

    # ── Warn on unencrypted HTTP (except localhost) ───────────
    _parsed = urlparse(config.api_url)
    if _parsed.scheme == "http" and _parsed.hostname not in ("localhost", "127.0.0.1"):
        typer.echo(
            "[!] WARNING: API URL uses unencrypted HTTP. "
            "Credentials may be transmitted in plain text."
        )

    # ── Direct API key mode ───────────────────────────────────
    api_key = os.environ.get("LUCID_API_KEY", "")
    if not api_key:
        # Offer interactive prompt if no env var set
        if typer.confirm("Authenticate with API key?", default=False):
            api_key = typer.prompt("API Key", hide_input=True)

    if api_key:
        config.api_key = api_key
        config.auth_token = None
        config.token_expires_at = None
        save_config(config)

        client = LucidClient(config)
        try:
            me = client.get_me()
            typer.echo(f"Authenticated as {me.get('email', 'unknown')}")
        except APIError as exc:
            typer.echo(f"API key validation failed: {exc.detail}", err=True)
            raise typer.Exit(code=1)
        return

    # ── Email/password mode ───────────────────────────────────
    if not email:
        email = typer.prompt("Email")
    password = os.environ.get("LUCID_PASSWORD", "")
    if not password:
        password = typer.prompt("Password", hide_input=True)

    tmp_config = LucidConfig(api_url=config.api_url)
    client = LucidClient(tmp_config)

    try:
        token_data = client.login(email, password)
    except APIError as exc:
        typer.echo(f"Login failed: {exc.detail}", err=True)
        raise typer.Exit(code=1)

    config.auth_token = token_data.get("access_token", "")
    config.token_expires_at = token_data.get("expires_at")
    config.api_key = None
    save_config(config)

    # Verify
    authed_client = LucidClient(config)
    try:
        me = authed_client.get_me()
        typer.echo(f"Logged in as {me.get('email', 'unknown')}")
    except APIError as exc:
        typer.echo(f"Token verification failed: {exc.detail}", err=True)
        raise typer.Exit(code=1)

    # ── Optional: generate persistent API key ─────────────────
    if generate_key:
        try:
            key_data = authed_client.create_api_key("lucid-cli")
            config.api_key = key_data.get("key", "")
            config.auth_token = None
            config.token_expires_at = None
            save_config(config)
            typer.echo("Generated persistent API key (stored in config)")
        except APIError as exc:
            typer.echo(f"API key generation failed: {exc.detail}", err=True)
