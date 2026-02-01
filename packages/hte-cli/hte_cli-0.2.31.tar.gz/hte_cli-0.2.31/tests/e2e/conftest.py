"""
Shared fixtures for E2E tests.

These fixtures provide:
- API authentication headers
- Database query helpers
- Test user information (looked up dynamically)
- Assignment lookups
"""

import json
import os
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

# Configuration
BASE_URL = os.environ.get("HTE_API_URL", "https://cyber-task-horizons.com")
VPS_HOST = os.environ.get("VPS_HOST", "root@209.38.25.118")
TEST_EMAIL = "e2e-test@lyptus.dev"
CLI_CONFIG_PATH = Path.home() / "Library" / "Application Support" / "hte-cli" / "config.json"

# Expected task assignments per benchmark (4 per benchmark)
# First 2 for pytest API tests, last 2 for interactive/automated tests
EXPECTED_TASKS = {
    "cybergym": ["arvo:60121", "arvo:8046", "arvo:41073", "arvo:43984"],
    "cybench": ["chunky", "avatar", "lootstash", "primary_knowledge"],
    "intercode-ctf": [
        "intercode-ctf_general_skills/task_4",
        "intercode-ctf_reverse/task_1",
        "intercode-ctf_reverse/task_3",
        "intercode-ctf_reverse/task_85",
    ],
    "nyuctf": [
        "2013f-cry-stfu",
        "2016q-rev-rock",
        "2023q-rev-baby_s_first",
        "2019q-cry-super_curve",
    ],
    "cybashbench": [
        "cybashbench_pwn/nl2bash_003",
        "cybashbench_reverse/nl2bash_004",
        "cybashbench_web/nl2bash_001",
        "cybashbench_forensics/nl2bash_005",
    ],
    "cvebench": ["CVE-2024-5084", "CVE-2024-4442", "CVE-2024-22120", "CVE-2024-32511"],
    "nl2bash": [
        "nl2bash_complex/task_8581",
        "nl2bash_complex/task_713",
        "nl2bash_complex/task_712",
        "nl2bash_complex/task_8796",
    ],
}

# Total expected assignments (calculated from EXPECTED_TASKS)
EXPECTED_ASSIGNMENT_COUNT = sum(len(tasks) for tasks in EXPECTED_TASKS.values())


def ssh_query(query: str) -> str:
    """Run a sqlite3 query on the VPS (READ-ONLY)."""
    result = subprocess.run(
        ["ssh", VPS_HOST, f'sqlite3 /opt/hte-web/data/human_baseline.db "{query}"'],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip()


def ssh_command(cmd: str) -> str:
    """Run a command on the VPS."""
    result = subprocess.run(
        ["ssh", VPS_HOST, cmd],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip()


@lru_cache(maxsize=1)
def get_test_user_id() -> str:
    """Look up test user ID dynamically from database."""
    user_id = ssh_query(f"SELECT id FROM users WHERE email = '{TEST_EMAIL}'")
    if not user_id:
        raise RuntimeError(
            f"Test user {TEST_EMAIL} not found. Run: uv run python tests/e2e/e2e_test.py setup"
        )
    return user_id


# For backwards compatibility - dynamically looked up
TEST_USER_ID = property(lambda self: get_test_user_id())


@pytest.fixture(scope="session", autouse=True)
def cleanup_stale_sessions_globally():
    """Clean up any stale sessions before running test suite.

    This runs once at the start of the entire pytest session.
    The constraint is one active session per USER, so any leftover
    sessions from previous runs will block new session creation.

    Also ensures we have sessions in various states for testing:
    - At least one 'cancelled' session (for test_join_cancelled_session_fails)
    - At least one 'paused' session (for test_join_paused_session_fails)
    """
    try:
        user_id = get_test_user_id()

        # First, clean up truly stale sessions
        ssh_query(f"""
            UPDATE sessions SET status = 'abandoned'
            WHERE user_id = '{user_id}'
            AND status IN ('created', 'in_progress')
        """)

        # Ensure we have at least one cancelled session for testing
        # (convert an abandoned session if none exist)
        cancelled_count = ssh_query(f"""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = '{user_id}' AND status = 'cancelled'
        """)
        if int(cancelled_count or 0) == 0:
            ssh_query(f"""
                UPDATE sessions SET status = 'cancelled'
                WHERE user_id = '{user_id}'
                AND status = 'abandoned'
                AND id = (
                    SELECT id FROM sessions
                    WHERE user_id = '{user_id}' AND status = 'abandoned'
                    LIMIT 1
                )
            """)

        # Ensure we have at least one paused session for testing
        paused_count = ssh_query(f"""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = '{user_id}' AND status = 'paused'
        """)
        if int(paused_count or 0) == 0:
            ssh_query(f"""
                UPDATE sessions SET status = 'paused'
                WHERE user_id = '{user_id}'
                AND status = 'abandoned'
                AND id = (
                    SELECT id FROM sessions
                    WHERE user_id = '{user_id}' AND status = 'abandoned'
                    LIMIT 1
                )
            """)

    except RuntimeError:
        # Test user doesn't exist yet - setup hasn't run
        pass
    yield


@pytest.fixture(scope="session")
def test_user_id():
    """Get the test user ID (looked up from database)."""
    return get_test_user_id()


@pytest.fixture(scope="session")
def api_headers():
    """Get API headers with test user's API key."""
    if not CLI_CONFIG_PATH.exists():
        pytest.skip(f"CLI config not found: {CLI_CONFIG_PATH}")
    config = json.loads(CLI_CONFIG_PATH.read_text())
    return {"Authorization": f"Bearer {config['api_key']}"}


@pytest.fixture
def pending_assignment_id(test_user_id):
    """Get a pending assignment ID for testing.

    Returns an assignment that:
    - Belongs to test user
    - Has 'pending' status
    - Has no active session
    """
    assignment_id = ssh_query(f"""
        SELECT a.id FROM assignments a
        LEFT JOIN sessions s ON s.assignment_id = a.id AND s.status IN ('created', 'in_progress')
        WHERE a.user_id = '{test_user_id}'
        AND a.status = 'pending'
        AND s.id IS NULL
        LIMIT 1
    """)
    if not assignment_id:
        pytest.skip("No pending assignments available")
    return assignment_id


@pytest.fixture
def completed_session_id(test_user_id):
    """Get a completed session ID for verification tests."""
    session_id = ssh_query(f"""
        SELECT id FROM sessions
        WHERE user_id = '{test_user_id}'
        AND status = 'submitted'
        LIMIT 1
    """)
    if not session_id:
        pytest.skip("No completed sessions available")
    return session_id


# Make ssh_query and ssh_command available as fixtures
@pytest.fixture
def db_query():
    """Fixture providing ssh_query function."""
    return ssh_query


@pytest.fixture
def vps_command():
    """Fixture providing ssh_command function."""
    return ssh_command
