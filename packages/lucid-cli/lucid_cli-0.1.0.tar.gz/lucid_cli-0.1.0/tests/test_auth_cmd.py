"""Tests for lucid_cli.auth CLI command."""

import os
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from lucid_cli.auth import app
from lucid_cli.client import APIError
from lucid_cli.config import LucidConfig

runner = CliRunner()


@patch("lucid_cli.auth.save_config")
@patch("lucid_cli.auth.load_config")
@patch("lucid_cli.auth.LucidClient")
def test_login_email_password(mock_client_cls: MagicMock, mock_load: MagicMock, mock_save: MagicMock) -> None:
    mock_load.return_value = LucidConfig()
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.login.return_value = {"access_token": "tok123", "expires_at": "2099-01-01T00:00:00Z"}
    mock_client.get_me.return_value = {"email": "user@test.com"}

    with patch.dict(os.environ, {"LUCID_PASSWORD": "secret"}, clear=False):
        os.environ.pop("LUCID_API_KEY", None)
        result = runner.invoke(app, ["-e", "user@test.com"], input="n\n")
    assert result.exit_code == 0
    assert "Logged in as user@test.com" in result.output


@patch("lucid_cli.auth.save_config")
@patch("lucid_cli.auth.load_config")
@patch("lucid_cli.auth.LucidClient")
def test_login_api_key_direct(mock_client_cls: MagicMock, mock_load: MagicMock, mock_save: MagicMock) -> None:
    mock_load.return_value = LucidConfig()
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.get_me.return_value = {"email": "apikey@test.com"}

    with patch.dict(os.environ, {"LUCID_API_KEY": "my-api-key-123"}, clear=False):
        result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Authenticated as apikey@test.com" in result.output


@patch("lucid_cli.auth.save_config")
@patch("lucid_cli.auth.load_config")
@patch("lucid_cli.auth.LucidClient")
def test_login_with_generate_key(mock_client_cls: MagicMock, mock_load: MagicMock, mock_save: MagicMock) -> None:
    mock_load.return_value = LucidConfig()
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.login.return_value = {"access_token": "tok"}
    mock_client.get_me.return_value = {"email": "user@test.com"}
    mock_client.create_api_key.return_value = {"key": "generated-key"}

    with patch.dict(os.environ, {"LUCID_PASSWORD": "pass"}, clear=False):
        os.environ.pop("LUCID_API_KEY", None)
        result = runner.invoke(app, ["-e", "user@test.com", "--generate-key"], input="n\n")
    assert result.exit_code == 0
    assert "Generated persistent API key" in result.output


@patch("lucid_cli.auth.save_config")
@patch("lucid_cli.auth.load_config")
@patch("lucid_cli.auth.LucidClient")
def test_login_custom_url(mock_client_cls: MagicMock, mock_load: MagicMock, mock_save: MagicMock) -> None:
    mock_load.return_value = LucidConfig()
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.login.return_value = {"access_token": "tok"}
    mock_client.get_me.return_value = {"email": "user@test.com"}

    with patch.dict(os.environ, {"LUCID_PASSWORD": "pass"}, clear=False):
        os.environ.pop("LUCID_API_KEY", None)
        result = runner.invoke(app, ["--api-url", "https://custom.api", "-e", "user@test.com"], input="n\n")
    assert result.exit_code == 0


@patch("lucid_cli.auth.save_config")
@patch("lucid_cli.auth.load_config")
@patch("lucid_cli.auth.LucidClient")
def test_login_failure(mock_client_cls: MagicMock, mock_load: MagicMock, mock_save: MagicMock) -> None:
    mock_load.return_value = LucidConfig()
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.login.side_effect = APIError(401, "Invalid credentials")

    with patch.dict(os.environ, {"LUCID_PASSWORD": "wrong"}, clear=False):
        os.environ.pop("LUCID_API_KEY", None)
        result = runner.invoke(app, ["-e", "bad@test.com"], input="n\n")
    assert result.exit_code == 1
    assert "Login failed" in result.output


@patch("lucid_cli.auth.save_config")
@patch("lucid_cli.auth.load_config")
@patch("lucid_cli.auth.LucidClient")
def test_api_key_validation_failure(mock_client_cls: MagicMock, mock_load: MagicMock, mock_save: MagicMock) -> None:
    mock_load.return_value = LucidConfig()
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.get_me.side_effect = APIError(401, "Invalid API key")

    with patch.dict(os.environ, {"LUCID_API_KEY": "bad-key"}, clear=False):
        result = runner.invoke(app, [])
    assert result.exit_code == 1
    assert "API key validation failed" in result.output
