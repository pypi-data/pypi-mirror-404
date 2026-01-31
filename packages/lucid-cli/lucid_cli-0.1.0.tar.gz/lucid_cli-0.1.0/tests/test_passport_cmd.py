"""Tests for lucid_cli.passport CLI commands."""

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from lucid_cli.passport import app
from lucid_cli.client import APIError

runner = CliRunner()

MOCK_PASSPORT = {
    "id": "p-1",
    "model": "llama3",
    "session_id": "sess-abc",
    "evidence_count": 3,
    "created_at": "2025-01-01",
    "hardware_attestation": {"vendor": "AMD", "model": "SEV-SNP"},
    "evidence": [{"type": "tee", "hash": "abc"}, {"type": "model", "hash": "def"}, {"type": "audit", "hash": "ghi"}],
}
MOCK_PASSPORTS_LIST = {"items": [MOCK_PASSPORT]}


@patch("lucid_cli.passport._get_client")
class TestList:
    def test_list_table(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.list_passports.return_value = MOCK_PASSPORTS_LIST

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "p-1" in result.output
        assert "llama3" in result.output

    def test_list_json(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.list_passports.return_value = MOCK_PASSPORTS_LIST

        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "items" in data

    def test_list_empty(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.list_passports.return_value = {"items": []}

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No passports found" in result.output

    def test_list_with_pagination(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.list_passports.return_value = MOCK_PASSPORTS_LIST

        result = runner.invoke(app, ["list", "--limit", "5", "--offset", "10"])
        assert result.exit_code == 0
        client.list_passports.assert_called_once_with(limit=5, offset=10)

    def test_list_error(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.list_passports.side_effect = APIError(500, "Server error")

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 1


@patch("lucid_cli.passport._get_client")
class TestShow:
    def test_show_passport(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.get_passport.return_value = MOCK_PASSPORT

        result = runner.invoke(app, ["show", "p-1"])
        assert result.exit_code == 0
        assert "llama3" in result.output
        assert "AMD" in result.output

    def test_show_json(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.get_passport.return_value = MOCK_PASSPORT

        result = runner.invoke(app, ["show", "p-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "p-1"
        assert data["hardware_attestation"]["vendor"] == "AMD"

    def test_show_not_found(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.get_passport.side_effect = APIError(404, "Resource not found.")

        result = runner.invoke(app, ["show", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_show_evidence_display(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.get_passport.return_value = MOCK_PASSPORT

        result = runner.invoke(app, ["show", "p-1"])
        assert result.exit_code == 0
        assert "3 items" in result.output
        assert "hardware_attestation" in result.output
