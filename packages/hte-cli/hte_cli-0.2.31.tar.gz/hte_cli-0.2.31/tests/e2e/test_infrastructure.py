"""
Automated infrastructure and database verification tests.

These tests verify:
1. All services are healthy (frontend, backend, cybergym, VPS)
2. Test user exists with correct configuration
3. Assignments are correctly set up
4. Sessions and events are properly recorded
5. Eval logs are created and uploaded

Run with: uv run pytest tests/e2e/test_infrastructure.py -v
"""

import json

import pytest
import requests

from tests.e2e.conftest import (
    BASE_URL,
    CLI_CONFIG_PATH,
    TEST_EMAIL,
    get_test_user_id,
    ssh_command,
    ssh_query,
)

# Import shared constants from conftest
from tests.e2e.conftest import EXPECTED_TASKS, EXPECTED_ASSIGNMENT_COUNT


# =============================================================================
# Infrastructure Tests
# =============================================================================


class TestInfrastructure:
    """Test that all infrastructure components are healthy."""

    def test_frontend_responds(self):
        """Frontend should return 200."""
        response = requests.get(f"{BASE_URL}/", timeout=30)
        assert response.status_code == 200

    def test_backend_health(self):
        """Backend health endpoint should return healthy status."""
        response = requests.get(f"{BASE_URL}/health", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_vps_ssh_access(self):
        """Should be able to SSH to VPS."""
        result = ssh_command("echo ok")
        assert result == "ok"

    def test_database_accessible(self):
        """Should be able to query the database."""
        count = ssh_query("SELECT COUNT(*) FROM users")
        assert int(count) > 0

    def test_cybergym_server_running(self):
        """CyberGym server should be accessible via SSH."""
        result = ssh_command("curl -s http://localhost:8666/")
        # 404 is expected at root - it means server is running
        assert "Not Found" in result or "404" in result


# =============================================================================
# Test User Configuration Tests
# =============================================================================


class TestUserConfiguration:
    """Test that the E2E test user is correctly configured."""

    def test_test_user_exists(self):
        """Test user should exist in database."""
        user_id = ssh_query(f"SELECT id FROM users WHERE email = '{TEST_EMAIL}'")
        assert user_id == get_test_user_id()

    def test_test_user_has_correct_name(self):
        """Test user should have correct name."""
        name = ssh_query(f"SELECT name FROM users WHERE id = '{get_test_user_id()}'")
        assert name == "E2E Test User"

    def test_cli_config_exists(self):
        """CLI config file should exist."""
        assert CLI_CONFIG_PATH.exists(), f"CLI config not found at {CLI_CONFIG_PATH}"

    def test_cli_config_has_correct_user(self):
        """CLI config should be configured for test user."""
        config = json.loads(CLI_CONFIG_PATH.read_text())
        assert config.get("user_email") == TEST_EMAIL

    def test_cli_config_has_valid_api_key(self):
        """CLI config should have a valid API key format."""
        config = json.loads(CLI_CONFIG_PATH.read_text())
        api_key = config.get("api_key", "")
        assert api_key.startswith("hte_"), "API key should start with 'hte_'"
        assert len(api_key) > 20, "API key should be reasonably long"


# =============================================================================
# Assignment Tests
# =============================================================================


class TestAssignments:
    """Test that task assignments are correctly set up."""

    def test_correct_number_of_assignments(self):
        """Test user should have expected number of assignments."""
        count = ssh_query(
            f"SELECT COUNT(*) FROM assignments WHERE user_id = '{get_test_user_id()}'"
        )
        assert (
            int(count) == EXPECTED_ASSIGNMENT_COUNT
        ), f"Expected {EXPECTED_ASSIGNMENT_COUNT} assignments, got {count}"

    @pytest.mark.parametrize("benchmark,tasks", EXPECTED_TASKS.items())
    def test_benchmark_tasks_assigned(self, benchmark, tasks):
        """Each benchmark should have its expected tasks assigned."""
        for task_id in tasks:
            exists = ssh_query(f"""
                SELECT COUNT(*) FROM assignments
                WHERE user_id = '{get_test_user_id()}'
                AND task_id = '{task_id}'
                AND benchmark = '{benchmark}'
            """)
            assert int(exists) == 1, f"Task {task_id} not assigned for {benchmark}"

    def test_all_assignments_have_valid_status(self):
        """All assignments should have valid status values."""
        statuses = ssh_query(f"""
            SELECT DISTINCT status FROM assignments
            WHERE user_id = '{get_test_user_id()}'
        """)
        valid_statuses = {"pending", "in_progress", "completed", "skipped"}
        for status in statuses.split("\n"):
            if status:
                assert status in valid_statuses, f"Invalid status: {status}"


# =============================================================================
# Session Tests
# =============================================================================


class TestSessions:
    """Test session management and state."""

    def test_no_stuck_in_progress_sessions(self):
        """There should be no stuck in_progress sessions (older than 24h)."""
        stuck = ssh_query(f"""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'in_progress'
            AND created_at < datetime('now', '-24 hours')
        """)
        assert int(stuck) == 0, "Found stuck in_progress sessions"

    def test_completed_sessions_have_answer(self):
        """Completed sessions should have an answer recorded."""
        missing_answer = ssh_query(f"""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'submitted'
            AND (answer IS NULL OR answer = '')
        """)
        assert int(missing_answer) == 0, "Found completed sessions without answer"

    def test_completed_sessions_have_active_time(self):
        """Completed sessions should have active time recorded."""
        missing_time = ssh_query(f"""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'submitted'
            AND (client_active_seconds IS NULL OR client_active_seconds = 0)
        """)
        assert int(missing_time) == 0, "Found completed sessions without active time"


# =============================================================================
# API Tests
# =============================================================================


class TestAPIEndpoints:
    """Test that API endpoints work correctly."""

    @pytest.fixture
    def api_headers(self):
        """Get API headers with test user's API key."""
        config = json.loads(CLI_CONFIG_PATH.read_text())
        return {"Authorization": f"Bearer {config['api_key']}"}

    def test_assignments_list_endpoint(self, api_headers):
        """CLI assignments endpoint should return assigned tasks."""
        # Use internal endpoint (public /assignments is deprecated, returns 410)
        response = requests.get(
            f"{BASE_URL}/api/v1/cli/assignments-internal",
            headers=api_headers,
            timeout=30,
        )
        assert response.status_code == 200
        assignments = response.json()
        # Test user should have assignments from E2E setup
        assert isinstance(assignments, list), "Expected list of assignments"
        assert len(assignments) > 0, "Test user should have at least one assignment"

    def test_assignment_has_task_info(self, api_headers):
        """Assignments should include task information."""
        response = requests.get(
            f"{BASE_URL}/api/v1/cli/assignments-internal",
            headers=api_headers,
            timeout=30,
        )
        assert response.status_code == 200
        assignments = response.json()

        if not assignments:
            pytest.skip("No assignments for current user")

        # Check first assignment has required fields
        first = assignments[0]
        assert "task_id" in first
        assert "benchmark" in first

    def test_files_endpoint_works(self, api_headers):
        """Files endpoint should work (tests runtime imports)."""
        # Get assignments for current user
        response = requests.get(
            f"{BASE_URL}/api/v1/cli/assignments-internal",
            headers=api_headers,
            timeout=30,
        )
        assignments = response.json()

        if not assignments:
            pytest.skip("No assignments for current user")

        # Find a cybergym assignment (has file generation)
        cybergym = next((a for a in assignments if a.get("benchmark") == "cybergym"), None)
        if not cybergym:
            pytest.skip("No cybergym assignment for current user")

        # Try to get files - this triggers runtime imports
        files_response = requests.get(
            f"{BASE_URL}/api/v1/cli/assignments/{cybergym['assignment_id']}/files",
            headers=api_headers,
            timeout=30,
        )
        # Should not get 500 (import error)
        assert (
            files_response.status_code != 500
        ), f"Files endpoint failed (likely import error): {files_response.text}"


# =============================================================================
# Cleanup Verification
# =============================================================================


class TestCleanupPrerequisites:
    """Test that the system is ready for clean test runs."""

    def test_one_active_session_per_assignment(self):
        """Verify each assignment has at most one active session."""
        duplicates = ssh_query(f"""
            SELECT assignment_id, COUNT(*) as cnt
            FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'in_progress'
            GROUP BY assignment_id
            HAVING cnt > 1
        """)
        assert not duplicates, f"Found assignments with multiple active sessions: {duplicates}"

    def test_one_active_session_per_user(self):
        """Verify user has at most one active session across all assignments."""
        active = ssh_query(f"""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'in_progress'
        """)
        # Note: After code fix, this should pass. Currently may fail with stale sessions.
        assert int(active) <= 1, f"Found {active} active sessions, should be 0 or 1"

    def test_session_endpoint_exists(self):
        """Verify the session creation endpoint exists and responds."""
        config = json.loads(CLI_CONFIG_PATH.read_text())
        headers = {"Authorization": f"Bearer {config['api_key']}"}

        # Test with a fake assignment ID - should get 404, not 500
        response = requests.post(
            f"{BASE_URL}/api/v1/cli/assignments/fake-uuid-1234/create-session",
            headers=headers,
            timeout=30,
        )

        # Should get a proper error response, not server error
        assert response.status_code in [
            400,
            404,
            422,
        ], f"Endpoint returned unexpected status: {response.status_code}"

    def test_can_create_session_via_api(self):
        """Verify session creation works via API (mimics CLI behavior)."""
        config = json.loads(CLI_CONFIG_PATH.read_text())
        headers = {"Authorization": f"Bearer {config['api_key']}"}

        # Get a pending assignment via DB read
        assignment_id = ssh_query(f"""
            SELECT a.id FROM assignments a
            LEFT JOIN sessions s ON s.assignment_id = a.id AND s.status IN ('created', 'in_progress')
            WHERE a.user_id = '{get_test_user_id()}'
            AND a.status = 'pending'
            AND s.id IS NULL
            LIMIT 1
        """)

        if not assignment_id:
            pytest.skip("No pending assignments available")

        # Create session via API (like CLI would)
        response = requests.post(
            f"{BASE_URL}/api/v1/cli/assignments/{assignment_id}/create-session",
            headers=headers,
            timeout=30,
        )

        assert response.status_code == 200, f"Failed to create session: {response.text}"
        session_id = response.json()["session_id"]

        # Verify session exists in DB
        db_status = ssh_query(f"SELECT status FROM sessions WHERE id = '{session_id}'")
        assert db_status in ("created", "in_progress"), f"Session status is {db_status}"

        # Clean up: Mark session as abandoned via direct DB update
        # We can't use API submit because session is in 'created' state (not joined yet)
        ssh_query(f"UPDATE sessions SET status = 'abandoned' WHERE id = '{session_id}'")
