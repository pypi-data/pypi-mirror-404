"""Configuration management for Lucid CLI.

Stores credentials and API settings in ~/.lucid/config.yaml.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

CONFIG_DIR = Path.home() / ".lucid"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


class LucidConfig(BaseModel):
    api_url: str = "https://api.lucid.engineering"
    auth_token: Optional[str] = None
    api_key: Optional[str] = None
    token_expires_at: Optional[str] = None


def load_config(config_file: Path = CONFIG_FILE) -> LucidConfig:
    """Load config from disk, returning defaults if file doesn't exist."""
    if config_file.exists():
        with open(config_file) as f:
            data = yaml.safe_load(f) or {}
        return LucidConfig(**data)
    return LucidConfig()


def save_config(config: LucidConfig, config_file: Path = CONFIG_FILE) -> None:
    """Save config to disk with restricted permissions."""
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        yaml.safe_dump(config.model_dump(exclude_none=True), f, default_flow_style=False)
    os.chmod(config_file, 0o600)


def require_auth(config_file: Path = CONFIG_FILE) -> LucidConfig:
    """Load config and verify credentials are present. Exit if not authenticated."""
    config = load_config(config_file)
    if config.api_key:
        return config
    if config.auth_token:
        if config.token_expires_at:
            try:
                expires = datetime.fromisoformat(config.token_expires_at)
                if expires < datetime.now(timezone.utc):
                    print("Session expired. Please run 'lucid login' to re-authenticate.", file=sys.stderr)
                    sys.exit(1)
            except ValueError:
                pass
        return config
    print("Not authenticated. Please run 'lucid login' first.", file=sys.stderr)
    sys.exit(1)
