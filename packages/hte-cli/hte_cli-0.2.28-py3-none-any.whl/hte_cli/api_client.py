"""HTTP API client for HTE web backend.

Handles authentication, retry logic, and API calls.
"""

import base64
import logging
from datetime import datetime
from typing import Any

import httpx

from hte_cli import API_BASE_URL, __version__
from hte_cli.config import Config

logger = logging.getLogger(__name__)

# Timeouts
DEFAULT_TIMEOUT = 30.0  # seconds
UPLOAD_TIMEOUT = 300.0  # 5 minutes for large eval log uploads

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [1, 5, 30]  # seconds


class APIError(Exception):
    """API request error."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class APIClient:
    """HTTP client for HTE API."""

    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.api_url or API_BASE_URL
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=DEFAULT_TIMEOUT,
                headers={
                    "User-Agent": f"hte-cli/{__version__}",
                    "X-CLI-Version": __version__,
                },
            )
        return self._client

    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        if not self.config.api_key:
            raise APIError("Not authenticated. Run: hte-cli auth login")
        return {"Authorization": f"Bearer {self.config.api_key}"}

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response, raising appropriate errors."""
        if response.status_code == 401:
            raise APIError("Authentication failed. Run: hte-cli auth login", 401)

        if response.status_code == 403:
            raise APIError("Access denied", 403)

        if response.status_code == 404:
            raise APIError("Resource not found", 404)

        if response.status_code == 413:
            raise APIError("Upload too large (max 200MB)", 413)

        if response.status_code == 426:
            raise APIError(
                "CLI version too old. Run: pip install --upgrade hte-cli",
                426,
            )

        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise APIError(f"API error: {detail}", response.status_code)

        if response.status_code == 204:
            return None

        return response.json()

    def get(self, path: str, **kwargs) -> Any:
        """Make GET request."""
        headers = self._get_auth_headers()
        headers.update(kwargs.pop("headers", {}))

        response = self.client.get(path, headers=headers, **kwargs)
        return self._handle_response(response)

    def post(self, path: str, json: dict | None = None, **kwargs) -> Any:
        """Make POST request with retry for transient failures."""
        headers = self._get_auth_headers()
        headers.update(kwargs.pop("headers", {}))

        timeout = kwargs.pop("timeout", DEFAULT_TIMEOUT)

        last_error = None
        for attempt, delay in enumerate(RETRY_DELAYS):
            try:
                response = self.client.post(
                    path,
                    json=json,
                    headers=headers,
                    timeout=timeout,
                    **kwargs,
                )
                return self._handle_response(response)
            except httpx.TimeoutException as e:
                last_error = APIError(f"Request timed out: {e}")
                logger.warning(f"Attempt {attempt + 1} failed: timeout. Retrying in {delay}s...")
            except httpx.NetworkError as e:
                last_error = APIError(f"Network error: {e}")
                logger.warning(f"Attempt {attempt + 1} failed: network. Retrying in {delay}s...")
            except APIError as e:
                # Don't retry client errors (4xx)
                if e.status_code and 400 <= e.status_code < 500:
                    raise
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")

            import time

            time.sleep(delay)

        raise last_error or APIError("Request failed after retries")

    def get_raw(self, path: str, **kwargs) -> bytes:
        """Make GET request returning raw bytes (for file downloads)."""
        headers = self._get_auth_headers()
        headers.update(kwargs.pop("headers", {}))

        response = self.client.get(path, headers=headers, **kwargs)

        if response.status_code >= 400:
            self._handle_response(response)  # Will raise

        return response.content

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    # =========================================================================
    # API Methods
    # =========================================================================

    def exchange_code_for_token(self, code: str) -> dict:
        """Exchange one-time code for API key."""
        # This endpoint doesn't require auth
        response = self.client.post(
            "/token",
            json={"code": code},
            headers={"X-CLI-Version": __version__},
        )
        return self._handle_response(response)

    def get_assignments(self) -> list[dict]:
        """Get pending assignments for current user."""
        return self.get("/assignments")

    def get_assignment_files(self, assignment_id: str) -> bytes:
        """Download task files as zip."""
        return self.get_raw(f"/assignments/{assignment_id}/files")

    def get_assignment_compose(self, assignment_id: str) -> str:
        """Get compose.yaml content."""
        content = self.get_raw(f"/assignments/{assignment_id}/compose")
        return content.decode("utf-8")

    def start_session(self, assignment_id: str) -> dict:
        """Start a session for an assignment.

        Returns session info including session_id.
        If session already exists, returns that session.
        """
        return self.post(f"/assignments/{assignment_id}/start")

    def post_event(self, session_id: str, event_type: str, event_data: dict | None = None) -> dict:
        """Post a session event."""
        return self.post(
            f"/sessions/{session_id}/events",
            json={
                "event_type": event_type,
                "event_data": event_data,
                "client_timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )

    # =========================================================================
    # Session-based API (new flow: hte-cli session join <session_id>)
    # =========================================================================

    def join_session(self, session_id: str) -> dict:
        """Join an existing session created by web UI.

        Returns session info including task data, benchmark, mode, etc.
        Sets cli_connected_at on the server.
        """
        return self.post(f"/sessions/{session_id}/join")

    def get_session_files(self, session_id: str) -> bytes:
        """Download task files for a session as zip."""
        return self.get_raw(f"/sessions/{session_id}/files")

    def get_session_compose(self, session_id: str) -> str:
        """Get compose.yaml content for a session."""
        content = self.get_raw(f"/sessions/{session_id}/compose")
        return content.decode("utf-8")

    # =========================================================================
    # Result Upload
    # =========================================================================

    def upload_result(
        self,
        session_id: str,
        answer: str,
        client_active_seconds: float,
        eval_log_bytes: bytes | None = None,
        score: float | None = None,
        score_binarized: int | None = None,
        agent_id: str | None = None,
    ) -> dict:
        """Upload task result with optional eval log.

        Args:
            session_id: The session ID
            answer: The user's answer
            client_active_seconds: Active time in seconds
            eval_log_bytes: Optional eval log content
            score: Optional pre-computed score
            score_binarized: Optional binarized score (0 or 1)
            agent_id: Optional CyberGym agent ID for post-hoc verification
        """
        payload = {
            "answer": answer,
            "client_active_seconds": client_active_seconds,
            "score": score,
            "score_binarized": score_binarized,
        }

        if eval_log_bytes:
            payload["eval_log_base64"] = base64.b64encode(eval_log_bytes).decode("ascii")

        if agent_id:
            payload["agent_id"] = agent_id

        return self.post(
            f"/sessions/{session_id}/result",
            json=payload,
            timeout=UPLOAD_TIMEOUT,
        )
