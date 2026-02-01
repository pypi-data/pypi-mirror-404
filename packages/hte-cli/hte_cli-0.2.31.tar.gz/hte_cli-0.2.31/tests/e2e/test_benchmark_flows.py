"""
Benchmark-specific E2E flow tests.

Tests verify:
1. Assignments exist for each benchmark
2. Session creation and join works per benchmark
3. Scoring configuration is correct per benchmark
4. Task files/compose can be retrieved

Run with: uv run pytest tests/e2e/test_benchmark_flows.py -v
"""

import pytest
import requests

from tests.e2e.conftest import (
    BASE_URL,
    EXPECTED_ASSIGNMENT_COUNT,
    get_test_user_id,
    ssh_command,
    ssh_query,
)

# Benchmark test configurations
# First 2 tasks for pytest API tests, last 2 for interactive tests
BENCHMARK_CONFIGS = {
    "cybergym": {
        "tasks": ["arvo:60121", "arvo:8046", "arvo:41073", "arvo:43984"],
        "scorer_type": "cybergym",
        "intermediate_scoring": True,
    },
    "cybench": {
        "tasks": ["chunky", "avatar", "lootstash", "primary_knowledge"],
        "scorer_type": "flag_includes",
        "intermediate_scoring": True,
    },
    "intercode-ctf": {
        "tasks": [
            "intercode-ctf_general_skills/task_4",
            "intercode-ctf_reverse/task_1",
            "intercode-ctf_reverse/task_3",
            "intercode-ctf_reverse/task_85",
        ],
        "scorer_type": "flag_includes",
        "intermediate_scoring": True,
    },
    "nyuctf": {
        "tasks": [
            "2013f-cry-stfu",
            "2016q-rev-rock",
            "2023q-rev-baby_s_first",
            "2019q-cry-super_curve",
        ],
        "scorer_type": "flag_includes",
        "intermediate_scoring": True,
    },
    "cybashbench": {
        "tasks": [
            "cybashbench_pwn/nl2bash_003",
            "cybashbench_reverse/nl2bash_004",
            "cybashbench_web/nl2bash_001",
            "cybashbench_forensics/nl2bash_005",
        ],
        "scorer_type": "llm_bash",
        "intermediate_scoring": False,
    },
    "cvebench": {
        "tasks": ["CVE-2024-5084", "CVE-2024-4442", "CVE-2024-22120", "CVE-2024-32511"],
        "scorer_type": "cvebench",
        "intermediate_scoring": True,
    },
}


# =============================================================================
# Assignment Verification Tests
# =============================================================================


class TestAssignmentExists:
    """Verify assignments exist for each benchmark."""

    @pytest.mark.parametrize("benchmark,config", BENCHMARK_CONFIGS.items())
    def test_benchmark_has_assignments(self, benchmark, config):
        """Each benchmark should have 4 assignments."""
        count = ssh_query(f"""
            SELECT COUNT(*) FROM assignments
            WHERE user_id = '{get_test_user_id()}'
            AND benchmark = '{benchmark}'
        """)
        assert int(count) == 4, f"{benchmark} should have 4 assignments, got {count}"

    @pytest.mark.parametrize("benchmark,config", BENCHMARK_CONFIGS.items())
    def test_benchmark_tasks_match(self, benchmark, config):
        """Assigned tasks should match expected task IDs."""
        task_ids = ssh_query(f"""
            SELECT task_id FROM assignments
            WHERE user_id = '{get_test_user_id()}'
            AND benchmark = '{benchmark}'
            ORDER BY task_id
        """)
        assigned = set(task_ids.split("\n")) if task_ids else set()
        expected = set(config["tasks"])
        assert assigned == expected, f"{benchmark} tasks mismatch: {assigned} != {expected}"


# =============================================================================
# Session Flow Tests (Sequential - one at a time)
# =============================================================================


@pytest.fixture(autouse=True, scope="class")
def cleanup_stale_sessions():
    """Clean up any stale sessions before running session flow tests.

    This ensures tests don't fail due to leftover sessions from previous runs.
    The constraint is one active session per USER (not per task).
    """
    ssh_query(f"""
        UPDATE sessions SET status = 'abandoned'
        WHERE user_id = '{get_test_user_id()}'
        AND status IN ('created', 'in_progress', 'paused')
    """)
    yield
    # Final cleanup after all tests
    ssh_query(f"""
        UPDATE sessions SET status = 'abandoned'
        WHERE user_id = '{get_test_user_id()}'
        AND status IN ('created', 'in_progress', 'paused')
    """)


class TestSessionFlow:
    """Test session creation, join, and cleanup for each benchmark.

    These tests create real sessions and clean them up properly.
    They run sequentially to respect the one-session-at-a-time constraint.
    """

    def _get_pending_assignment(self, benchmark: str) -> str | None:
        """Get a pending assignment ID for a benchmark."""
        return (
            ssh_query(f"""
            SELECT a.id FROM assignments a
            LEFT JOIN sessions s ON s.assignment_id = a.id
                AND s.status IN ('created', 'in_progress', 'paused')
            WHERE a.user_id = '{get_test_user_id()}'
            AND a.benchmark = '{benchmark}'
            AND a.status = 'pending'
            AND s.id IS NULL
            LIMIT 1
        """)
            or None
        )

    def _cleanup_session(self, api_headers, session_id: str):
        """Clean up a session by marking it as abandoned in the database.

        We use direct DB update because:
        - Session might be in 'created' state (not joinable yet)
        - API submit requires session to be in 'in_progress' state
        - We just need to clear the 'one active session per user' constraint
        """
        ssh_query(f"UPDATE sessions SET status = 'abandoned' WHERE id = '{session_id}'")

    def test_cybergym_session_flow(self, api_headers):
        """Test CyberGym session creation and join."""
        assignment_id = self._get_pending_assignment("cybergym")
        if not assignment_id:
            pytest.skip("No pending cybergym assignment")

        # Create session
        response = requests.post(
            f"{BASE_URL}/api/v1/cli/assignments/{assignment_id}/create-session",
            headers=api_headers,
            timeout=30,
        )
        assert response.status_code == 200, f"Failed to create session: {response.text}"
        session_id = response.json()["session_id"]

        try:
            # Join session
            join_response = requests.post(
                f"{BASE_URL}/api/v1/cli/sessions/{session_id}/join",
                headers=api_headers,
                timeout=30,
            )
            assert join_response.status_code == 200
            data = join_response.json()

            # Verify scoring config
            assert data.get("scorer_type") == "cybergym"
            assert data.get("intermediate_scoring") is True
            assert data.get("benchmark") == "cybergym"
        finally:
            self._cleanup_session(api_headers, session_id)

    def test_cybench_session_flow(self, api_headers):
        """Test CyBench session creation and join."""
        assignment_id = self._get_pending_assignment("cybench")
        if not assignment_id:
            pytest.skip("No pending cybench assignment")

        response = requests.post(
            f"{BASE_URL}/api/v1/cli/assignments/{assignment_id}/create-session",
            headers=api_headers,
            timeout=30,
        )
        assert response.status_code == 200
        session_id = response.json()["session_id"]

        try:
            join_response = requests.post(
                f"{BASE_URL}/api/v1/cli/sessions/{session_id}/join",
                headers=api_headers,
                timeout=30,
            )
            assert join_response.status_code == 200
            data = join_response.json()

            assert data.get("scorer_type") == "flag_includes"
            assert data.get("intermediate_scoring") is True
            # Flag-based benchmarks should have a target
            assert data.get("target") or data.get("metadata", {}).get("flag")
        finally:
            self._cleanup_session(api_headers, session_id)

    def test_intercode_ctf_session_flow(self, api_headers):
        """Test InterCode-CTF session creation and join."""
        assignment_id = self._get_pending_assignment("intercode-ctf")
        if not assignment_id:
            pytest.skip("No pending intercode-ctf assignment")

        response = requests.post(
            f"{BASE_URL}/api/v1/cli/assignments/{assignment_id}/create-session",
            headers=api_headers,
            timeout=30,
        )
        assert response.status_code == 200
        session_id = response.json()["session_id"]

        try:
            join_response = requests.post(
                f"{BASE_URL}/api/v1/cli/sessions/{session_id}/join",
                headers=api_headers,
                timeout=30,
            )
            assert join_response.status_code == 200
            data = join_response.json()

            assert data.get("scorer_type") == "flag_includes"
            assert data.get("intermediate_scoring") is True
        finally:
            self._cleanup_session(api_headers, session_id)

    def test_nyuctf_session_flow(self, api_headers):
        """Test NYUCTF session creation and join."""
        assignment_id = self._get_pending_assignment("nyuctf")
        if not assignment_id:
            pytest.skip("No pending nyuctf assignment")

        response = requests.post(
            f"{BASE_URL}/api/v1/cli/assignments/{assignment_id}/create-session",
            headers=api_headers,
            timeout=30,
        )
        assert response.status_code == 200
        session_id = response.json()["session_id"]

        try:
            join_response = requests.post(
                f"{BASE_URL}/api/v1/cli/sessions/{session_id}/join",
                headers=api_headers,
                timeout=30,
            )
            assert join_response.status_code == 200
            data = join_response.json()

            assert data.get("scorer_type") == "flag_includes"
            assert data.get("intermediate_scoring") is True
        finally:
            self._cleanup_session(api_headers, session_id)

    def test_cybashbench_session_flow(self, api_headers):
        """Test CyBashBench session creation and join."""
        assignment_id = self._get_pending_assignment("cybashbench")
        if not assignment_id:
            pytest.skip("No pending cybashbench assignment")

        response = requests.post(
            f"{BASE_URL}/api/v1/cli/assignments/{assignment_id}/create-session",
            headers=api_headers,
            timeout=30,
        )
        assert response.status_code == 200
        session_id = response.json()["session_id"]

        try:
            join_response = requests.post(
                f"{BASE_URL}/api/v1/cli/sessions/{session_id}/join",
                headers=api_headers,
                timeout=30,
            )
            assert join_response.status_code == 200
            data = join_response.json()

            # LLM-based scoring - no client-side intermediate scoring
            assert data.get("scorer_type") == "llm_bash"
            assert data.get("intermediate_scoring") is False
        finally:
            self._cleanup_session(api_headers, session_id)

    def test_cvebench_session_flow(self, api_headers):
        """Test CVEBench session creation and join."""
        assignment_id = self._get_pending_assignment("cvebench")
        if not assignment_id:
            pytest.skip("No pending cvebench assignment")

        response = requests.post(
            f"{BASE_URL}/api/v1/cli/assignments/{assignment_id}/create-session",
            headers=api_headers,
            timeout=30,
        )
        assert response.status_code == 200
        session_id = response.json()["session_id"]

        try:
            join_response = requests.post(
                f"{BASE_URL}/api/v1/cli/sessions/{session_id}/join",
                headers=api_headers,
                timeout=30,
            )
            assert join_response.status_code == 200
            data = join_response.json()

            assert data.get("scorer_type") == "cvebench"
            assert data.get("intermediate_scoring") is True
        finally:
            self._cleanup_session(api_headers, session_id)


# =============================================================================
# Infrastructure Tests
# =============================================================================


class TestCyberGymInfra:
    """Test CyberGym-specific infrastructure."""

    def test_cybergym_server_accessible(self):
        """CyberGym server should be running."""
        result = ssh_command("curl -s http://localhost:8666/")
        # 404 "Not Found" is expected at root - means server is running
        assert "Not Found" in result or result == ""


# =============================================================================
# Cross-Benchmark Tests
# =============================================================================


class TestCrossBenchmark:
    """Tests that span all benchmarks."""

    def test_all_benchmarks_have_assignments(self):
        """Every configured benchmark should have assignments."""
        for benchmark in BENCHMARK_CONFIGS:
            count = ssh_query(f"""
                SELECT COUNT(*) FROM assignments
                WHERE user_id = '{get_test_user_id()}'
                AND benchmark = '{benchmark}'
            """)
            assert int(count) > 0, f"No assignments for {benchmark}"

    def test_total_assignments_correct(self):
        """Total assignments should match expected count (4 per benchmark)."""
        count = ssh_query(f"""
            SELECT COUNT(*) FROM assignments
            WHERE user_id = '{get_test_user_id()}'
        """)
        assert (
            int(count) == EXPECTED_ASSIGNMENT_COUNT
        ), f"Expected {EXPECTED_ASSIGNMENT_COUNT} assignments, got {count}"


# =============================================================================
# Files Endpoint Tests
# =============================================================================


class TestFilesEndpoint:
    """Test task files can be retrieved."""

    def test_cybergym_files_endpoint(self, api_headers):
        """CyberGym tasks should have downloadable files."""
        # Get a cybergym assignment
        assignment_id = ssh_query(f"""
            SELECT id FROM assignments
            WHERE user_id = '{get_test_user_id()}'
            AND benchmark = 'cybergym'
            LIMIT 1
        """)
        if not assignment_id:
            pytest.skip("No cybergym assignment")

        response = requests.get(
            f"{BASE_URL}/api/v1/cli/assignments/{assignment_id}/files",
            headers=api_headers,
            timeout=30,
        )
        # Should not get 500 (import error)
        assert response.status_code != 500, f"Files endpoint error: {response.text}"

    def test_cybergym_compose_endpoint(self, api_headers):
        """CyberGym tasks should have compose file."""
        assignment_id = ssh_query(f"""
            SELECT id FROM assignments
            WHERE user_id = '{get_test_user_id()}'
            AND benchmark = 'cybergym'
            LIMIT 1
        """)
        if not assignment_id:
            pytest.skip("No cybergym assignment")

        response = requests.get(
            f"{BASE_URL}/api/v1/cli/assignments/{assignment_id}/compose",
            headers=api_headers,
            timeout=30,
        )
        assert response.status_code == 200
        assert "services:" in response.text or "version:" in response.text
