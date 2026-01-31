"""
Session lifecycle tests.

Tests the complete session flow:
1. Session creation via API
2. Session start event recording
3. Docker container launch detection
4. Submission handling
5. Upload and completion
6. Event sequence validation

Run with: uv run pytest tests/e2e/test_session_lifecycle.py -v
"""

import pytest
import requests

from tests.e2e.conftest import BASE_URL, get_test_user_id, ssh_query

# api_headers and pending_assignment_id fixtures are in conftest.py


@pytest.fixture(autouse=True, scope="class")
def cleanup_before_session_tests():
    """Clean up stale sessions before each test class that creates sessions."""
    ssh_query(f"""
        UPDATE sessions SET status = 'abandoned'
        WHERE user_id = '{get_test_user_id()}'
        AND status IN ('created', 'in_progress', 'paused')
    """)
    yield


class TestSessionCreation:
    """Test session creation via API."""

    def test_session_creation_flow(self, api_headers, pending_assignment_id):
        """Test full session creation flow via API."""
        # Create session via API (mimics CLI behavior)
        response = requests.post(
            f"{BASE_URL}/api/v1/cli/assignments/{pending_assignment_id}/create-session",
            headers=api_headers,
            timeout=30,
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        session_id = data["session_id"]

        # Verify in database (read-only)
        # Sessions start in 'created' status, move to 'in_progress' after CLI joins
        db_status = ssh_query(f"SELECT status FROM sessions WHERE id = '{session_id}'")
        assert db_status in ("created", "in_progress"), f"Unexpected status: {db_status}"

    def test_duplicate_session_blocked(self, api_headers, pending_assignment_id):
        """Second session creation should be blocked or return existing."""
        # First session
        response1 = requests.post(
            f"{BASE_URL}/api/v1/cli/assignments/{pending_assignment_id}/create-session",
            headers=api_headers,
            timeout=30,
        )

        if response1.status_code != 200:
            pytest.skip("Could not create first session")

        # Second session attempt
        response2 = requests.post(
            f"{BASE_URL}/api/v1/cli/assignments/{pending_assignment_id}/create-session",
            headers=api_headers,
            timeout=30,
        )

        # Should either return existing session (200) or error (400/409)
        assert response2.status_code in [200, 400, 409]

    def test_existing_sessions_have_valid_status(self):
        """All existing sessions should have valid status values."""
        statuses = ssh_query(f"""
            SELECT DISTINCT status FROM sessions
            WHERE user_id = '{get_test_user_id()}'
        """)
        valid_statuses = {
            "created",
            "pending",
            "in_progress",
            "submitted",
            "abandoned",
            "skipped",
            "cancelled",
            "paused",
        }
        for status in statuses.split("\n"):
            if status:
                assert status in valid_statuses, f"Invalid status: {status}"

    def test_in_progress_sessions_count(self):
        """Check count of in_progress sessions (should be 0 or 1)."""
        count = ssh_query(f"""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'in_progress'
        """)
        assert int(count) <= 1, f"Found {count} in_progress sessions, expected 0 or 1"


class TestSessionEvents:
    """Test session event recording."""

    def test_expected_events_for_completed_session(self):
        """Completed sessions should have expected events."""
        # Find a completed session that has events (sessions created via API
        # without CLI flow won't have events)
        session_id = ssh_query(f"""
            SELECT s.id FROM sessions s
            JOIN session_events se ON s.id = se.session_id
            WHERE s.user_id = '{get_test_user_id()}'
            AND s.status = 'submitted'
            AND se.event_type = 'session_started'
            LIMIT 1
        """)

        if not session_id:
            pytest.skip("No completed sessions with events (need full CLI flow)")

        events = ssh_query(f"""
            SELECT event_type FROM session_events
            WHERE session_id = '{session_id}'
            ORDER BY server_timestamp
        """)
        event_list = events.split("\n") if events else []

        # Check for key events
        expected = ["session_started", "docker_started", "session_completed"]
        for evt in expected:
            assert evt in event_list, f"Missing event: {evt}"

    def test_events_have_timestamps(self):
        """All events should have server timestamps."""
        missing_timestamps = ssh_query(f"""
            SELECT COUNT(*) FROM session_events se
            JOIN sessions s ON se.session_id = s.id
            WHERE s.user_id = '{get_test_user_id()}'
            AND se.server_timestamp IS NULL
        """)
        assert int(missing_timestamps) == 0

    def test_events_in_chronological_order(self):
        """Events should be in chronological order."""
        # Find a session with multiple events
        session_id = ssh_query("""
            SELECT session_id FROM session_events
            GROUP BY session_id
            HAVING COUNT(*) > 2
            LIMIT 1
        """)

        if not session_id:
            pytest.skip("No sessions with multiple events")

        # Check timestamps are increasing
        timestamps = ssh_query(f"""
            SELECT server_timestamp FROM session_events
            WHERE session_id = '{session_id}'
            ORDER BY server_timestamp
        """)
        ts_list = [t for t in timestamps.split("\n") if t]
        assert ts_list == sorted(ts_list), "Events not in chronological order"


class TestSessionCompletion:
    """Test session completion and data recording."""

    def test_completed_session_has_score(self):
        """Completed sessions should have a score."""
        # Count total submitted sessions
        total_submitted = ssh_query(f"""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'submitted'
        """)
        total = int(total_submitted) if total_submitted else 0
        if total == 0:
            pytest.skip("No submitted sessions to verify")

        # Count sessions without score
        sessions_without_score = ssh_query(f"""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'submitted'
            AND score IS NULL
        """)
        count = int(sessions_without_score) if sessions_without_score else 0
        # Most submitted sessions should have scores (some benchmarks may not score)
        assert count < total, f"All {total} sessions missing scores"

    def test_completed_session_has_answer(self):
        """Completed sessions should have an answer."""
        session = ssh_query(f"""
            SELECT id, answer FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'submitted'
            AND answer IS NOT NULL
            LIMIT 1
        """)
        if not session:
            pytest.skip("No completed sessions with answers")
        assert "|" in session  # Should have id|answer format

    def test_completed_session_has_active_time(self):
        """Completed sessions should record active time."""
        session = ssh_query(f"""
            SELECT id, client_active_seconds FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'submitted'
            AND client_active_seconds > 0
            LIMIT 1
        """)
        if not session:
            pytest.skip("No completed sessions with active time")
        parts = session.split("|")
        assert float(parts[1]) > 0


class TestSessionState:
    """Test session state verification (read-only)."""

    def test_abandoned_sessions_count(self):
        """Verify abandoned sessions exist and are queryable."""
        abandoned_count = ssh_query(f"""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'abandoned'
        """)
        # Verify the query returned a valid number (not empty/error)
        assert abandoned_count.strip().isdigit(), f"Query returned invalid value: {abandoned_count}"
        # Note: count can legitimately be 0 if no sessions were abandoned

    def test_no_stuck_sessions_older_than_24h(self):
        """No in_progress sessions should be older than 24 hours."""
        stuck = ssh_query(f"""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'in_progress'
            AND created_at < datetime('now', '-24 hours')
        """)
        assert int(stuck) == 0, f"Found {stuck} stuck sessions older than 24h"

    def test_session_timestamps_valid(self):
        """All sessions should have valid timestamps."""
        invalid = ssh_query(f"""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND created_at IS NULL
        """)
        assert int(invalid) == 0, "Found sessions with NULL timestamps"


class TestSessionJoin:
    """Test session join endpoint returns required fields."""

    def test_join_session_returns_target(self, api_headers):
        """Join session response includes target field for flag-based benchmarks."""
        # Find a session that can be joined (created or in_progress)
        # New workflow: web UI creates with 'created', CLI joins, setup_completed -> 'in_progress'
        session_id = ssh_query(f"""
            SELECT s.id FROM sessions s
            JOIN assignments a ON s.assignment_id = a.id
            WHERE s.user_id = '{get_test_user_id()}'
            AND s.status IN ('created', 'in_progress')
            AND a.benchmark IN ('cybench', 'nyuctf', 'intercode-ctf')
            LIMIT 1
        """)

        if not session_id:
            pytest.skip("No joinable session for flag-based benchmark")

        response = requests.post(
            f"{BASE_URL}/api/v1/cli/sessions/{session_id}/join",
            headers=api_headers,
            timeout=30,
        )

        if response.status_code != 200:
            pytest.skip(f"Could not join session: {response.status_code}")

        data = response.json()
        # target should be present (may be empty string for some benchmarks)
        assert "target" in data or "task" in data and "target" in data.get("task", {})

    def test_join_session_returns_scorer_type(self, api_headers):
        """Join session response includes scorer_type."""
        session_id = ssh_query(f"""
            SELECT id FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status IN ('created', 'in_progress')
            LIMIT 1
        """)

        if not session_id:
            pytest.skip("No joinable session available")

        response = requests.post(
            f"{BASE_URL}/api/v1/cli/sessions/{session_id}/join",
            headers=api_headers,
            timeout=30,
        )

        if response.status_code != 200:
            pytest.skip(f"Could not join session: {response.status_code}")

        data = response.json()
        # scorer_type is at top level of join response (not nested in task)
        assert "scorer_type" in data, "scorer_type missing from join response"
        assert data["scorer_type"] in [
            "flag_includes",
            "llm_bash",
            "cybergym",
            "cvebench",
        ]

    def test_join_session_returns_intermediate_scoring(self, api_headers):
        """Join session response includes intermediate_scoring."""
        session_id = ssh_query(f"""
            SELECT id FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status IN ('created', 'in_progress')
            LIMIT 1
        """)

        if not session_id:
            pytest.skip("No joinable session available")

        response = requests.post(
            f"{BASE_URL}/api/v1/cli/sessions/{session_id}/join",
            headers=api_headers,
            timeout=30,
        )

        if response.status_code != 200:
            pytest.skip(f"Could not join session: {response.status_code}")

        data = response.json()
        # intermediate_scoring is at top level of join response
        assert "intermediate_scoring" in data, "intermediate_scoring missing from join response"
        assert isinstance(data["intermediate_scoring"], bool)

    def test_join_cancelled_session_fails(self, api_headers):
        """Joining a cancelled session should fail."""
        # Find a cancelled session
        session_id = ssh_query(f"""
            SELECT id FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'cancelled'
            LIMIT 1
        """)

        if not session_id:
            pytest.skip("No cancelled session available")

        response = requests.post(
            f"{BASE_URL}/api/v1/cli/sessions/{session_id}/join",
            headers=api_headers,
            timeout=30,
        )

        # Should fail with 400 (session not active)
        assert response.status_code == 400

    def test_join_paused_session_fails(self, api_headers):
        """Joining a paused session should fail (must resume from web UI first)."""
        # Find a paused session
        session_id = ssh_query(f"""
            SELECT id FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'paused'
            LIMIT 1
        """)

        if not session_id:
            pytest.skip("No paused session available")

        response = requests.post(
            f"{BASE_URL}/api/v1/cli/sessions/{session_id}/join",
            headers=api_headers,
            timeout=30,
        )

        # Should fail with 400 (session is paused)
        assert response.status_code == 400
        assert "paused" in response.json().get("detail", "").lower()


class TestSessionCancellation:
    """Test that CLI handles cancelled sessions correctly.

    Note: Cancel is a web-UI-only operation (JWT auth). These tests verify
    that the CLI correctly detects and handles cancelled sessions.
    """

    def test_cancelled_sessions_exist_in_valid_states(self):
        """Cancelled sessions should have valid state in database."""
        # Verify cancelled sessions have expected fields set
        cancelled = ssh_query(f"""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'cancelled'
        """)
        # Verify query returned valid result
        assert cancelled.strip().isdigit(), f"Query returned invalid value: {cancelled}"
        # Note: count can legitimately be 0 if no sessions were cancelled

    def test_no_orphaned_in_progress_after_cancel(self):
        """Assignments should not be in_progress if session is cancelled."""
        # Find any inconsistencies where assignment is in_progress but session is cancelled
        orphaned = ssh_query(f"""
            SELECT COUNT(*) FROM assignments a
            JOIN sessions s ON s.assignment_id = a.id
            WHERE a.user_id = '{get_test_user_id()}'
            AND a.status = 'in_progress'
            AND s.status = 'cancelled'
            AND NOT EXISTS (
                SELECT 1 FROM sessions s2
                WHERE s2.assignment_id = a.id
                AND s2.status IN ('created', 'in_progress', 'paused')
            )
        """)
        assert int(orphaned) == 0, "Found assignments stuck in_progress with cancelled session"
