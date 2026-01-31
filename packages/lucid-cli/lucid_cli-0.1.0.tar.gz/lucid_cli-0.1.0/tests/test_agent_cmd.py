"""Tests for lucid_cli.agent CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from lucid_cli.agent import app
from lucid_cli.client import APIError

runner = CliRunner()

MOCK_AGENT = {"id": "agent-1", "name": "test-agent", "status": "running", "model": "llama3", "gpu": "H100", "created_at": "2025-01-01"}
MOCK_AGENTS_LIST = {"items": [MOCK_AGENT]}


def _mock_get_client() -> MagicMock:
    return MagicMock()


@patch("lucid_cli.agent._get_client")
class TestCreate:
    def test_create_with_flags(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.create_agent.return_value = {"id": "new-1", "name": "my-agent", "status": "pending"}

        result = runner.invoke(app, ["create", "--name", "my-agent", "--model", "llama3", "--gpu", "H100"])
        assert result.exit_code == 0
        assert "new-1" in result.output

    def test_create_with_file(self, mock_gc: MagicMock, tmp_path) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.create_agent.return_value = {"id": "file-1"}

        f = tmp_path / "agent.yaml"
        f.write_text("name: file-agent\nmodel: gpt-4\n")

        result = runner.invoke(app, ["create", "-f", str(f)])
        assert result.exit_code == 0
        assert "file-1" in result.output

    def test_create_json_output(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.create_agent.return_value = {"id": "j-1", "name": "json-agent"}

        result = runner.invoke(app, ["create", "--name", "json-agent", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "j-1"

    def test_create_error(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.create_agent.side_effect = APIError(422, "Invalid body")

        result = runner.invoke(app, ["create", "--name", "bad"])
        assert result.exit_code == 1
        assert "Invalid body" in result.output


@patch("lucid_cli.agent._get_client")
class TestList:
    def test_list_table(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.list_agents.return_value = MOCK_AGENTS_LIST

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "agent-1" in result.output
        assert "test-agent" in result.output

    def test_list_json(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.list_agents.return_value = MOCK_AGENTS_LIST

        result = runner.invoke(app, ["list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "items" in data

    def test_list_empty(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.list_agents.return_value = {"items": []}

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No agents found" in result.output

    def test_list_with_type_filter(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.list_agents.return_value = MOCK_AGENTS_LIST

        result = runner.invoke(app, ["list", "--type", "managed"])
        assert result.exit_code == 0
        client.list_agents.assert_called_once_with(limit=20, offset=0, management_type="managed")


@patch("lucid_cli.agent._get_client")
class TestStatus:
    def test_status_basic(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.get_agent.return_value = MOCK_AGENT

        result = runner.invoke(app, ["status", "agent-1"])
        assert result.exit_code == 0
        assert "running" in result.output

    def test_status_k8s(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.get_agent_k8s_status.return_value = {"phase": "Running", "pod": "agent-pod-xyz"}

        result = runner.invoke(app, ["status", "agent-1", "--k8s"])
        assert result.exit_code == 0
        assert "Running" in result.output

    def test_status_json(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.get_agent.return_value = MOCK_AGENT

        result = runner.invoke(app, ["status", "agent-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "agent-1"

    def test_status_not_found(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.get_agent.side_effect = APIError(404, "Resource not found.")

        result = runner.invoke(app, ["status", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output


@patch("lucid_cli.agent._get_client")
class TestLogs:
    def test_logs_sse_streaming(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.stream_agent_logs.return_value = iter(["line1", "line2", "line3"])

        result = runner.invoke(app, ["logs", "agent-1"])
        assert result.exit_code == 0
        assert "line1" in result.output
        assert "line3" in result.output

    def test_logs_container(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.get_container_logs.return_value = {"logs": ["c-line1", "c-line2"]}

        result = runner.invoke(app, ["logs", "agent-1", "-c", "sidecar"])
        assert result.exit_code == 0
        assert "c-line1" in result.output

    def test_logs_no_follow(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.get_container_logs.return_value = {"logs": ["nf-line1"]}

        result = runner.invoke(app, ["logs", "agent-1", "--no-follow"])
        assert result.exit_code == 0
        assert "nf-line1" in result.output


@patch("lucid_cli.agent._get_client")
class TestStart:
    def test_start(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.start_agent.return_value = {"status": "starting"}

        result = runner.invoke(app, ["start", "agent-1"])
        assert result.exit_code == 0
        assert "started" in result.output

    def test_start_error(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.start_agent.side_effect = APIError(409, "Already running")

        result = runner.invoke(app, ["start", "agent-1"])
        assert result.exit_code == 1


@patch("lucid_cli.agent._get_client")
class TestStop:
    def test_stop(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.stop_agent.return_value = {"status": "stopped"}

        result = runner.invoke(app, ["stop", "agent-1"])
        assert result.exit_code == 0
        assert "stopped" in result.output


@patch("lucid_cli.agent._get_client")
class TestDelete:
    def test_delete_with_yes(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.delete_agent.return_value = {"deleted": True}

        result = runner.invoke(app, ["delete", "agent-1", "-y"])
        assert result.exit_code == 0
        assert "deleted" in result.output

    def test_delete_confirm_prompt(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.delete_agent.return_value = {"deleted": True}

        result = runner.invoke(app, ["delete", "agent-1"], input="y\n")
        assert result.exit_code == 0
        assert "deleted" in result.output

    def test_delete_abort(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client

        result = runner.invoke(app, ["delete", "agent-1"], input="n\n")
        assert "Aborted" in result.output
