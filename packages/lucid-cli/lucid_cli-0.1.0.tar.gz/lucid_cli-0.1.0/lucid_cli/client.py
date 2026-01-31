"""HTTP client wrapper for the Lucid Verifier API."""

from typing import Any, Generator, Optional

import httpx
import httpx_sse

from lucid_cli.config import LucidConfig


class APIError(Exception):
    """Raised when the Verifier API returns an error response."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API error {status_code}: {detail}")


_ERROR_MESSAGES = {
    401: "Authentication failed. Run 'lucid login' to re-authenticate.",
    403: "Permission denied. You don't have access to this resource.",
    404: "Resource not found.",
    422: "Invalid request. Check your parameters.",
}


class LucidClient:
    """Thin wrapper around the Verifier API."""

    def __init__(self, config: LucidConfig):
        self.config = config

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key
        elif self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        return headers

    def _url(self, path: str) -> str:
        return f"{self.config.api_url.rstrip('/')}{path}"

    def _handle_response(self, resp: httpx.Response) -> Any:
        if resp.is_success:
            if resp.headers.get("content-type", "").startswith("application/json"):
                return resp.json()
            return resp.text
        detail = _ERROR_MESSAGES.get(resp.status_code, "")
        try:
            body = resp.json()
            detail = body.get("detail", detail) if isinstance(body, dict) else detail
        except Exception:
            if not detail:
                detail = resp.text or f"HTTP {resp.status_code}"
        raise APIError(resp.status_code, detail)

    # ── Auth ──────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> dict:
        with httpx.Client() as c:
            resp = c.post(
                self._url("/auth/jwt/login"),
                data={"username": email, "password": password},
            )
            return self._handle_response(resp)

    def create_api_key(self, alias: str = "lucid-cli") -> dict:
        with httpx.Client() as c:
            resp = c.post(
                self._url(f"/users/me/api-key?alias={alias}"),
                headers=self._headers(),
            )
            return self._handle_response(resp)

    def get_me(self) -> dict:
        with httpx.Client() as c:
            resp = c.get(self._url("/v1/me"), headers=self._headers())
            return self._handle_response(resp)

    # ── Agents ────────────────────────────────────────────────────

    def create_agent(self, body: dict) -> dict:
        with httpx.Client() as c:
            resp = c.post(self._url("/v1/agents"), json=body, headers=self._headers())
            return self._handle_response(resp)

    def list_agents(
        self,
        limit: int = 20,
        offset: int = 0,
        management_type: Optional[str] = None,
    ) -> Any:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if management_type:
            params["management_type"] = management_type
        with httpx.Client() as c:
            resp = c.get(self._url("/v1/agents"), params=params, headers=self._headers())
            return self._handle_response(resp)

    def get_agent(self, agent_id: str) -> dict:
        with httpx.Client() as c:
            resp = c.get(self._url(f"/v1/agents/{agent_id}"), headers=self._headers())
            return self._handle_response(resp)

    def delete_agent(self, agent_id: str) -> Any:
        with httpx.Client() as c:
            resp = c.delete(self._url(f"/v1/agents/{agent_id}"), headers=self._headers())
            return self._handle_response(resp)

    def start_agent(self, agent_id: str) -> dict:
        with httpx.Client() as c:
            resp = c.post(
                self._url(f"/v1/agents/{agent_id}/start"), headers=self._headers()
            )
            return self._handle_response(resp)

    def stop_agent(self, agent_id: str) -> dict:
        with httpx.Client() as c:
            resp = c.post(
                self._url(f"/v1/agents/{agent_id}/stop"), headers=self._headers()
            )
            return self._handle_response(resp)

    def stream_agent_logs(self, agent_id: str) -> Generator[str, None, None]:
        with httpx.Client(timeout=None) as c:
            with httpx_sse.connect_sse(
                c, "GET", self._url(f"/v1/agents/{agent_id}/logs"), headers=self._headers()
            ) as sse:
                for event in sse.iter_sse():
                    yield event.data

    def get_agent_k8s_status(self, agent_id: str) -> dict:
        with httpx.Client() as c:
            resp = c.get(
                self._url(f"/v1/agents/{agent_id}/k8s-status"), headers=self._headers()
            )
            return self._handle_response(resp)

    def list_agent_containers(self, agent_id: str) -> Any:
        with httpx.Client() as c:
            resp = c.get(
                self._url(f"/v1/agents/{agent_id}/containers"), headers=self._headers()
            )
            return self._handle_response(resp)

    def get_container_logs(
        self, agent_id: str, container: str, tail_lines: int = 100
    ) -> Any:
        with httpx.Client() as c:
            resp = c.get(
                self._url(f"/v1/agents/{agent_id}/containers/{container}/logs"),
                params={"tail_lines": tail_lines},
                headers=self._headers(),
            )
            return self._handle_response(resp)

    # ── Catalog ───────────────────────────────────────────────────

    def list_catalog_apps(
        self,
        category: Optional[str] = None,
        verified_only: bool = False,
    ) -> Any:
        params: dict[str, Any] = {}
        if category:
            params["category"] = category
        if verified_only:
            params["verified_only"] = True
        with httpx.Client() as c:
            resp = c.get(
                self._url("/v1/apps/catalog"), params=params, headers=self._headers()
            )
            return self._handle_response(resp)

    def get_catalog_app(self, app_id: str) -> dict:
        with httpx.Client() as c:
            resp = c.get(
                self._url(f"/v1/apps/catalog/{app_id}"), headers=self._headers()
            )
            return self._handle_response(resp)

    # ── Passports ─────────────────────────────────────────────────

    def list_passports(self, limit: int = 20, offset: int = 0) -> Any:
        with httpx.Client() as c:
            resp = c.get(
                self._url("/v1/passports"),
                params={"limit": limit, "offset": offset},
                headers=self._headers(),
            )
            return self._handle_response(resp)

    def get_passport(self, passport_id: str) -> dict:
        with httpx.Client() as c:
            resp = c.get(
                self._url(f"/v1/passports/{passport_id}"), headers=self._headers()
            )
            return self._handle_response(resp)
