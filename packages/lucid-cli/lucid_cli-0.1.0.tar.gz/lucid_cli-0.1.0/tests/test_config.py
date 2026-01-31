"""Tests for lucid_cli.config."""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from lucid_cli.config import LucidConfig, load_config, require_auth, save_config


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    return tmp_path / "config.yaml"


def test_load_config_defaults(config_file: Path) -> None:
    cfg = load_config(config_file)
    assert cfg.api_url == "https://api.lucid.engineering"
    assert cfg.auth_token is None
    assert cfg.api_key is None


def test_save_and_load_roundtrip(config_file: Path) -> None:
    cfg = LucidConfig(api_url="https://test.example.com", api_key="key-123")
    save_config(cfg, config_file)

    loaded = load_config(config_file)
    assert loaded.api_url == "https://test.example.com"
    assert loaded.api_key == "key-123"
    assert loaded.auth_token is None


def test_save_sets_restricted_permissions(config_file: Path) -> None:
    save_config(LucidConfig(), config_file)
    mode = os.stat(config_file).st_mode & 0o777
    assert mode == 0o600


def test_require_auth_with_api_key(config_file: Path) -> None:
    save_config(LucidConfig(api_key="k"), config_file)
    cfg = require_auth(config_file)
    assert cfg.api_key == "k"


def test_require_auth_with_token(config_file: Path) -> None:
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    save_config(LucidConfig(auth_token="tok", token_expires_at=future), config_file)
    cfg = require_auth(config_file)
    assert cfg.auth_token == "tok"


def test_require_auth_expired_token_exits(config_file: Path) -> None:
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    save_config(LucidConfig(auth_token="tok", token_expires_at=past), config_file)
    with pytest.raises(SystemExit):
        require_auth(config_file)


def test_require_auth_no_credentials_exits(config_file: Path) -> None:
    save_config(LucidConfig(), config_file)
    with pytest.raises(SystemExit):
        require_auth(config_file)


def test_api_key_takes_precedence(config_file: Path) -> None:
    """When both api_key and auth_token are set, require_auth returns config with api_key."""
    save_config(LucidConfig(api_key="key-1", auth_token="tok-1"), config_file)
    cfg = require_auth(config_file)
    assert cfg.api_key == "key-1"


def test_load_config_empty_file(config_file: Path) -> None:
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text("")
    cfg = load_config(config_file)
    assert cfg.api_url == "https://api.lucid.engineering"


def test_save_config_creates_parent_dirs(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b" / "config.yaml"
    save_config(LucidConfig(api_key="x"), nested)
    assert nested.exists()
    loaded = load_config(nested)
    assert loaded.api_key == "x"
