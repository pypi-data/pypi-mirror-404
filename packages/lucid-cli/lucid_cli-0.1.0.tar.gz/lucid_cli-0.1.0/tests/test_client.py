"""Tests for lucid_cli.client."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from lucid_cli.client import APIError, LucidClient
from lucid_cli.config import LucidConfig


def _make_response(status_code: int = 200, json_data=None, text: str = "") -> httpx.Response:
    import json as _json

    if json_data is not None:
        return httpx.Response(
            status_code=status_code,
            content=_json.dumps(json_data).encode(),
            headers={"content-type": "application/json"},
            request=httpx.Request("GET", "https://test"),
        )
    return httpx.Response(
        status_code=status_code,
        text=text,
        request=httpx.Request("GET", "https://test"),
    )


@pytest.fixture()
def client() -> LucidClient:
    return LucidClient(LucidConfig(api_url="https://api.test", api_key="test-key"))


@pytest.fixture()
def jwt_client() -> LucidClient:
    return LucidClient(LucidConfig(api_url="https://api.test", auth_token="jwt-tok"))


class TestHeaders:
    def test_api_key_header(self, client: LucidClient) -> None:
        h = client._headers()
        assert h["X-API-Key"] == "test-key"
        assert "Authorization" not in h

    def test_jwt_header(self, jwt_client: LucidClient) -> None:
        h = jwt_client._headers()
        assert h["Authorization"] == "Bearer jwt-tok"
        assert "X-API-Key" not in h

    def test_api_key_precedence(self) -> None:
        c = LucidClient(LucidConfig(api_key="k", auth_token="t"))
        h = c._headers()
        assert "X-API-Key" in h
        assert "Authorization" not in h


class TestHandleResponse:
    def test_success_json(self, client: LucidClient) -> None:
        resp = _make_response(200, json_data={"ok": True})
        assert client._handle_response(resp) == {"ok": True}

    def test_error_401(self, client: LucidClient) -> None:
        resp = _make_response(401, json_data={"detail": "Bad token"})
        with pytest.raises(APIError) as exc_info:
            client._handle_response(resp)
        assert exc_info.value.status_code == 401

    def test_error_404(self, client: LucidClient) -> None:
        resp = _make_response(404, text="not found")
        with pytest.raises(APIError) as exc_info:
            client._handle_response(resp)
        assert exc_info.value.status_code == 404

    def test_error_500(self, client: LucidClient) -> None:
        resp = _make_response(500, text="server error")
        with pytest.raises(APIError) as exc_info:
            client._handle_response(resp)
        assert exc_info.value.status_code == 500


class TestLogin:
    @patch("lucid_cli.client.httpx.Client")
    def test_login_success(self, mock_cls: MagicMock) -> None:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_http.post.return_value = _make_response(200, json_data={"access_token": "tok123"})

        c = LucidClient(LucidConfig(api_url="https://api.test"))
        result = c.login("user@test.com", "pass")
        assert result["access_token"] == "tok123"
        mock_http.post.assert_called_once()

    @patch("lucid_cli.client.httpx.Client")
    def test_login_failure(self, mock_cls: MagicMock) -> None:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_http.post.return_value = _make_response(401, json_data={"detail": "Invalid credentials"})

        c = LucidClient(LucidConfig(api_url="https://api.test"))
        with pytest.raises(APIError):
            c.login("bad@test.com", "wrong")


class TestAgentMethods:
    @patch("lucid_cli.client.httpx.Client")
    def test_create_agent(self, mock_cls: MagicMock, client: LucidClient) -> None:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_http.post.return_value = _make_response(200, json_data={"id": "a1", "name": "test"})

        result = client.create_agent({"name": "test"})
        assert result["id"] == "a1"

    @patch("lucid_cli.client.httpx.Client")
    def test_list_agents(self, mock_cls: MagicMock, client: LucidClient) -> None:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_http.get.return_value = _make_response(200, json_data={"items": [{"id": "a1"}]})

        result = client.list_agents()
        assert result["items"][0]["id"] == "a1"

    @patch("lucid_cli.client.httpx.Client")
    def test_get_agent(self, mock_cls: MagicMock, client: LucidClient) -> None:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_http.get.return_value = _make_response(200, json_data={"id": "a1", "status": "running"})

        result = client.get_agent("a1")
        assert result["status"] == "running"

    @patch("lucid_cli.client.httpx.Client")
    def test_delete_agent(self, mock_cls: MagicMock, client: LucidClient) -> None:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_http.delete.return_value = _make_response(200, json_data={"deleted": True})

        result = client.delete_agent("a1")
        assert result["deleted"] is True

    @patch("lucid_cli.client.httpx.Client")
    def test_start_agent(self, mock_cls: MagicMock, client: LucidClient) -> None:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_http.post.return_value = _make_response(200, json_data={"status": "starting"})

        result = client.start_agent("a1")
        assert result["status"] == "starting"

    @patch("lucid_cli.client.httpx.Client")
    def test_stop_agent(self, mock_cls: MagicMock, client: LucidClient) -> None:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_http.post.return_value = _make_response(200, json_data={"status": "stopped"})

        result = client.stop_agent("a1")
        assert result["status"] == "stopped"


class TestCatalogMethods:
    @patch("lucid_cli.client.httpx.Client")
    def test_list_catalog_apps(self, mock_cls: MagicMock, client: LucidClient) -> None:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_http.get.return_value = _make_response(200, json_data=[{"id": "app1"}])

        result = client.list_catalog_apps()
        assert result[0]["id"] == "app1"

    @patch("lucid_cli.client.httpx.Client")
    def test_get_catalog_app(self, mock_cls: MagicMock, client: LucidClient) -> None:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_http.get.return_value = _make_response(200, json_data={"id": "app1", "name": "Test App"})

        result = client.get_catalog_app("app1")
        assert result["name"] == "Test App"


class TestPassportMethods:
    @patch("lucid_cli.client.httpx.Client")
    def test_list_passports(self, mock_cls: MagicMock, client: LucidClient) -> None:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_http.get.return_value = _make_response(200, json_data={"items": [{"id": "p1"}]})

        result = client.list_passports()
        assert result["items"][0]["id"] == "p1"

    @patch("lucid_cli.client.httpx.Client")
    def test_get_passport(self, mock_cls: MagicMock, client: LucidClient) -> None:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_http)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_http.get.return_value = _make_response(200, json_data={"id": "p1", "model": "gpt-4"})

        result = client.get_passport("p1")
        assert result["model"] == "gpt-4"
