"""Event streaming for CLI session tracking.

Sends events to the API for real-time visibility. Best-effort - failures
don't block task execution.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from hte_cli.api_client import APIClient, APIError

logger = logging.getLogger(__name__)


class EventStreamer:
    """Streams session events to the API."""

    # Valid event types per spec
    VALID_EVENTS = {
        "session_started",
        "session_paused",
        "session_resumed",
        "docker_started",
        "docker_stopped",
        "session_completed",
        # Overhead tracking events
        "setup_started",
        "image_pull_completed",
        "setup_completed",
        "upload_started",
        "upload_completed",
    }

    def __init__(self, api: APIClient, session_id: str):
        """
        Initialize the event streamer.

        Args:
            api: API client instance
            session_id: Session ID to stream events for
        """
        self.api = api
        self.session_id = session_id

    def _now_iso(self) -> str:
        """Get current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()

    def send(
        self,
        event_type: str,
        data: dict[str, Any] | None = None,
        blocking: bool = False,
    ) -> bool:
        """
        Send an event to the API.

        Args:
            event_type: Type of event (must be in VALID_EVENTS)
            data: Optional event data
            blocking: If True, raise on failure. If False, log and continue.

        Returns:
            True if event was sent successfully, False otherwise
        """
        if event_type not in self.VALID_EVENTS:
            logger.warning(f"Invalid event type: {event_type}")
            return False

        try:
            self.api.post_event(
                session_id=self.session_id,
                event_type=event_type,
                event_data=data,
            )
            logger.debug(f"Sent event: {event_type}")
            return True
        except APIError as e:
            msg = f"Failed to send event {event_type}: {e}"
            if blocking:
                raise
            logger.warning(msg)
            return False
        except Exception as e:
            msg = f"Unexpected error sending event {event_type}: {e}"
            if blocking:
                raise
            logger.warning(msg)
            return False

    def session_started(self, data: dict[str, Any] | None = None) -> bool:
        """Record session start."""
        return self.send("session_started", data)

    def session_paused(self, elapsed_seconds: float | None = None) -> bool:
        """Record session pause."""
        data = {}
        if elapsed_seconds is not None:
            data["elapsed_seconds"] = elapsed_seconds
        return self.send("session_paused", data or None)

    def session_resumed(self) -> bool:
        """Record session resume."""
        return self.send("session_resumed")

    def docker_started(self, container_id: str | None = None) -> bool:
        """Record Docker container start."""
        data = {}
        if container_id:
            data["container_id"] = container_id
        return self.send("docker_started", data or None)

    def docker_stopped(self, container_id: str | None = None, exit_code: int | None = None) -> bool:
        """Record Docker container stop."""
        data = {}
        if container_id:
            data["container_id"] = container_id
        if exit_code is not None:
            data["exit_code"] = exit_code
        return self.send("docker_stopped", data or None)

    def session_completed(
        self,
        elapsed_seconds: float | None = None,
        answer: str | None = None,
    ) -> bool:
        """Record session completion."""
        data = {}
        if elapsed_seconds is not None:
            data["elapsed_seconds"] = elapsed_seconds
        if answer is not None:
            data["answer_submitted"] = True
        return self.send("session_completed", data or None)

    # Overhead tracking events

    def setup_started(self, images: list[str], cli_version: str | None = None) -> bool:
        """Record start of setup phase (before image pulls)."""
        data = {"images": images}
        if cli_version:
            data["cli_version"] = cli_version
        return self.send("setup_started", data)

    def image_pull_completed(
        self,
        duration_seconds: float,
        pulled: list[str],
        cached: list[str],
        failed: list[str],
    ) -> bool:
        """Record image pull results with timing."""
        return self.send(
            "image_pull_completed",
            {
                "duration_seconds": duration_seconds,
                "pulled": pulled,
                "cached": cached,
                "failed": failed,
            },
        )

    def setup_completed(self, total_seconds: float) -> bool:
        """Record end of setup phase (environment ready for work)."""
        return self.send("setup_completed", {"total_seconds": total_seconds})

    def upload_started(self, size_bytes: int) -> bool:
        """Record start of result upload."""
        return self.send("upload_started", {"size_bytes": size_bytes})

    def upload_completed(self, duration_seconds: float, size_bytes: int) -> bool:
        """Record end of result upload with timing."""
        return self.send(
            "upload_completed",
            {
                "duration_seconds": duration_seconds,
                "size_bytes": size_bytes,
            },
        )
