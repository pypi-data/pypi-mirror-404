"""Tests for lucid_cli.catalog CLI commands."""

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from lucid_cli.catalog import app
from lucid_cli.client import APIError

runner = CliRunner()

MOCK_APP = {"id": "app-1", "name": "Test App", "category": "llm", "verified": True, "tee": "coco"}
MOCK_APPS_LIST = [MOCK_APP]


@patch("lucid_cli.catalog._get_client")
class TestApps:
    def test_apps_list(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.list_catalog_apps.return_value = MOCK_APPS_LIST

        result = runner.invoke(app, ["apps"])
        assert result.exit_code == 0
        assert "app-1" in result.output
        assert "Test App" in result.output

    def test_apps_category_filter(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.list_catalog_apps.return_value = MOCK_APPS_LIST

        result = runner.invoke(app, ["apps", "-c", "llm"])
        assert result.exit_code == 0
        client.list_catalog_apps.assert_called_once_with(category="llm", verified_only=False)

    def test_apps_verified_filter(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.list_catalog_apps.return_value = MOCK_APPS_LIST

        result = runner.invoke(app, ["apps", "--verified"])
        assert result.exit_code == 0
        client.list_catalog_apps.assert_called_once_with(category=None, verified_only=True)

    def test_apps_json(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.list_catalog_apps.return_value = MOCK_APPS_LIST

        result = runner.invoke(app, ["apps", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["id"] == "app-1"

    def test_apps_empty(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.list_catalog_apps.return_value = []

        result = runner.invoke(app, ["apps"])
        assert result.exit_code == 0
        assert "No apps found" in result.output

    def test_apps_error(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.list_catalog_apps.side_effect = APIError(500, "Server error")

        result = runner.invoke(app, ["apps"])
        assert result.exit_code == 1


@patch("lucid_cli.catalog._get_client")
class TestShow:
    def test_show_app(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.get_catalog_app.return_value = MOCK_APP

        result = runner.invoke(app, ["show", "app-1"])
        assert result.exit_code == 0
        assert "Test App" in result.output

    def test_show_app_json(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.get_catalog_app.return_value = MOCK_APP

        result = runner.invoke(app, ["show", "app-1", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "Test App"

    def test_show_not_found(self, mock_gc: MagicMock) -> None:
        client = MagicMock()
        mock_gc.return_value = client
        client.get_catalog_app.side_effect = APIError(404, "Resource not found.")

        result = runner.invoke(app, ["show", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output
