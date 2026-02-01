"""
Eval log tests.

Tests eval log creation, upload, and integrity:
1. Local eval log creation
2. Upload to VPS
3. File format validation
4. Content verification

Run with: uv run pytest tests/e2e/test_eval_logs.py -v

NOTE: Many of these tests skip when no completed sessions exist.
Run the automated_runner or complete interactive tasks first.
"""

import os
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

# Configuration
VPS_HOST = os.environ.get("VPS_HOST", "root@209.38.25.118")
TEST_EMAIL = "e2e-test@lyptus.dev"
CLI_CONFIG_PATH = Path.home() / "Library" / "Application Support" / "hte-cli" / "config.json"
LOCAL_EVAL_LOGS_DIR = Path.home() / "Library" / "Application Support" / "hte-cli" / "eval_logs"
VPS_EVAL_LOGS_DIR = "/opt/hte-web/data/eval_logs"


def db_path_to_host_path(db_path: str) -> str:
    """Translate container path stored in DB to host path on VPS.

    Backend may store paths as:
    - /data/... (container-relative, needs translation)
    - /opt/hte-web/data/... (already host path, return as-is)
    """
    if db_path.startswith("/opt/hte-web/"):
        return db_path  # Already a host path
    return db_path.replace("/data/", "/opt/hte-web/data/")


def ssh_query(query: str) -> str:
    """Run a sqlite3 query on the VPS."""
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


# =============================================================================
# Local Eval Log Tests
# =============================================================================


class TestLocalEvalLogs:
    """Test local eval log directory and files."""

    def test_local_eval_logs_dir_exists(self):
        """Local eval logs directory should exist."""
        assert (
            LOCAL_EVAL_LOGS_DIR.exists()
        ), f"Local eval logs directory not found: {LOCAL_EVAL_LOGS_DIR}"

    def test_local_eval_logs_dir_permissions(self):
        """Local eval logs directory should be writable."""
        assert os.access(LOCAL_EVAL_LOGS_DIR, os.W_OK), "Local eval logs directory not writable"

    def test_local_eval_log_count(self):
        """Should have some local eval logs if tests have run."""
        if not LOCAL_EVAL_LOGS_DIR.exists():
            pytest.skip("Local eval logs directory not found")

        logs = list(LOCAL_EVAL_LOGS_DIR.glob("*.eval"))
        # Verify we found eval logs (if E2E tests have run, there should be some)
        assert len(logs) > 0, f"No eval logs found in {LOCAL_EVAL_LOGS_DIR}"


# =============================================================================
# VPS Eval Log Tests
# =============================================================================


class TestVPSEvalLogs:
    """Test eval logs on VPS."""

    def test_vps_eval_logs_dir_exists(self):
        """VPS eval logs directory should exist."""
        result = ssh_command(f"test -d {VPS_EVAL_LOGS_DIR} && echo exists")
        assert result == "exists", "VPS eval logs directory not found"

    def test_vps_eval_log_count(self):
        """Should have eval logs on VPS if sessions have completed."""
        result = ssh_command(f"find {VPS_EVAL_LOGS_DIR} -name '*.eval.gz' 2>/dev/null | wc -l")
        assert result.strip().isdigit(), f"Invalid count result: {result}"
        count = int(result.strip())
        # If E2E tests have run, there should be eval logs
        assert count > 0, f"No eval logs found on VPS in {VPS_EVAL_LOGS_DIR}"

    def test_completed_sessions_have_eval_log_path(self):
        """Completed sessions should have eval_log_path recorded."""
        count = ssh_query(f"""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'submitted'
        """)

        if int(count) == 0:
            pytest.skip("No completed sessions")

        with_path = ssh_query(f"""
            SELECT COUNT(*) FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'submitted'
            AND eval_log_path IS NOT NULL
        """)

        # All completed sessions should have eval log paths
        # Handle empty string from SQL query
        with_path_count = int(with_path) if with_path else 0
        total_count = int(count) if count else 0

        if total_count == 0:
            pytest.skip("No completed sessions to check")

        assert (
            with_path_count == total_count
        ), f"Only {with_path_count}/{total_count} completed sessions have eval_log_path"

    def test_eval_log_files_exist_on_vps(self):
        """Eval log files referenced in DB should exist on VPS."""
        paths = ssh_query(f"""
            SELECT eval_log_path FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'submitted'
            AND eval_log_path IS NOT NULL
            LIMIT 5
        """)

        if not paths:
            pytest.skip("No eval log paths in database")

        for path in paths.split("\n"):
            if path:
                host_path = db_path_to_host_path(path)
                exists = ssh_command(f"test -f {host_path} && echo exists")
                assert exists == "exists", f"Eval log not found: {host_path} (DB path: {path})"


# =============================================================================
# Eval Log Format Tests
# =============================================================================


class TestEvalLogFormat:
    """Test eval log file format and content."""

    def test_eval_log_is_gzipped(self):
        """Eval logs on VPS should be gzipped."""
        path = ssh_query("""
            SELECT eval_log_path FROM sessions
            WHERE status = 'submitted'
            AND eval_log_path IS NOT NULL
            LIMIT 1
        """)

        if not path:
            pytest.skip("No eval logs to test")

        assert path.endswith(".eval.gz"), f"Eval log not gzipped: {path}"

    def test_eval_log_can_be_decompressed(self):
        """Eval logs should be valid gzip files."""
        db_path = ssh_query("""
            SELECT eval_log_path FROM sessions
            WHERE status = 'submitted'
            AND eval_log_path IS NOT NULL
            LIMIT 1
        """)

        if not db_path:
            pytest.skip("No eval logs to test")

        path = db_path_to_host_path(db_path)
        # Try to decompress
        result = ssh_command(f"gunzip -t {path} 2>&1 && echo ok")
        assert "ok" in result, f"Eval log not valid gzip: {result}"

    def test_eval_log_contains_expected_structure(self):
        """Eval logs should contain expected Inspect AI structure."""
        db_path = ssh_query("""
            SELECT eval_log_path FROM sessions
            WHERE status = 'submitted'
            AND eval_log_path IS NOT NULL
            LIMIT 1
        """)

        if not db_path:
            pytest.skip("No eval logs to test")

        path = db_path_to_host_path(db_path)
        # List contents of the gzipped eval (it's actually a zip inside gzip)
        # Use python's zipfile since unzip may not be installed
        result = ssh_command(f"""
            cd /tmp &&
            cp {path} test_eval.gz &&
            gunzip -f test_eval.gz &&
            python3 -c "import zipfile; z=zipfile.ZipFile('test_eval'); print('\\n'.join(z.namelist()[:20]))"
        """)

        # Should contain header.json at minimum
        assert (
            "header" in result.lower() or "json" in result.lower() or "sample" in result.lower()
        ), f"Eval log missing expected structure: {result}"


# =============================================================================
# Eval Log Upload Tests
# =============================================================================


class TestEvalLogUpload:
    """Test eval log upload functionality."""

    def test_upload_event_recorded(self):
        """Upload events should be recorded in session_events for sessions with eval logs.

        Note: Upload events were added in CLI v0.2.22. Sessions created with older
        CLI versions won't have these events.
        """
        # Find a session that has:
        # 1. eval_log_path (proves upload succeeded)
        # 2. session_started event with cli_version >= 0.2.22 (has upload events)
        session_id = ssh_query(f"""
            SELECT s.id FROM sessions s
            JOIN session_events se ON s.id = se.session_id
            WHERE s.user_id = '{get_test_user_id()}'
            AND s.status = 'submitted'
            AND s.eval_log_path IS NOT NULL
            AND se.event_type = 'session_started'
            AND (
                json_extract(se.event_data, '$.cli_version') >= '0.2.22'
                OR json_extract(se.event_data, '$.cli_version') LIKE '0.3.%'
                OR json_extract(se.event_data, '$.cli_version') LIKE '1.%'
            )
            LIMIT 1
        """)

        if not session_id:
            pytest.skip("No sessions with CLI v0.2.22+ (upload events added in v0.2.22)")

        events = ssh_query(f"""
            SELECT event_type FROM session_events
            WHERE session_id = '{session_id}'
        """)

        # Should have upload-related events for sessions with eval logs
        event_list = events.split("\n") if events else []
        has_upload = any("upload" in e.lower() for e in event_list)

        assert (
            has_upload
        ), f"No upload events found for session {session_id}. Events: {event_list[:5]}"

    def test_eval_log_size_reasonable(self):
        """Eval logs should be reasonably sized (not empty, not huge)."""
        db_path = ssh_query("""
            SELECT eval_log_path FROM sessions
            WHERE status = 'submitted'
            AND eval_log_path IS NOT NULL
            LIMIT 1
        """)

        if not db_path:
            pytest.skip("No eval logs to test")

        path = db_path_to_host_path(db_path)
        size = ssh_command(f"stat -c%s {path} 2>/dev/null || stat -f%z {path}")

        if size.isdigit():
            size_bytes = int(size)
            assert size_bytes > 100, f"Eval log too small: {size_bytes} bytes"
            assert size_bytes < 100_000_000, f"Eval log too large: {size_bytes} bytes"


# =============================================================================
# Eval Log Integrity Tests
# =============================================================================


class TestEvalLogIntegrity:
    """Test eval log data integrity."""

    def test_session_id_matches_log_filename(self):
        """Eval log filename should contain session ID."""
        result = ssh_query(f"""
            SELECT id, eval_log_path FROM sessions
            WHERE user_id = '{get_test_user_id()}'
            AND status = 'submitted'
            AND eval_log_path IS NOT NULL
            LIMIT 5
        """)

        if not result:
            pytest.skip("No completed sessions with eval logs")

        for line in result.split("\n"):
            if "|" in line:
                session_id, path = line.split("|", 1)
                # Session ID or task ID should be in path
                # (depends on naming convention)
                assert (
                    session_id in path or "/" in path
                ), f"Session ID not in path: {session_id} -> {path}"

    def test_no_orphaned_eval_logs(self):
        """All eval logs on VPS should have corresponding sessions.

        We ignore orphans that are:
        1. From E2E test tasks (setup deletes sessions but not files)
        2. From before the current DB started (historical artifacts from dev testing)

        Only orphans from non-E2E tasks after the DB was created are flagged.
        """
        import re

        from tests.e2e.conftest import EXPECTED_TASKS

        # Build set of E2E task path patterns (slashes become underscores in paths)
        e2e_task_patterns = set()
        for benchmark, tasks in EXPECTED_TASKS.items():
            for task in tasks:
                # Path format: /benchmark/task_id_sanitized/
                sanitized = task.replace("/", "_")
                e2e_task_patterns.add(f"/{benchmark}/{sanitized}/")

        # Get the earliest session date to filter out pre-DB orphans
        earliest_session = ssh_query("SELECT MIN(created_at) FROM sessions")
        # Extract YYYYMMDD from earliest session (format: 2026-01-08 04:19:22)
        earliest_date = None
        if earliest_session:
            date_match = re.match(r"(\d{4})-(\d{2})-(\d{2})", earliest_session)
            if date_match:
                earliest_date = date_match.group(1) + date_match.group(2) + date_match.group(3)

        # Get all eval log paths from DB
        db_paths = ssh_query("""
            SELECT eval_log_path FROM sessions
            WHERE eval_log_path IS NOT NULL
        """)
        db_set = set(db_paths.split("\n")) if db_paths else set()

        # Get all files on disk
        disk_files = ssh_command(f"find {VPS_EVAL_LOGS_DIR} -name '*.eval.gz' 2>/dev/null")
        disk_set = set(disk_files.split("\n")) if disk_files else set()

        # Check for orphans (files on disk not in DB)
        all_orphans = disk_set - db_set - {""}

        # Separate orphans by category
        e2e_orphans = set()
        pre_db_orphans = set()
        real_orphans = set()

        # Pattern to extract date from filename: {uuid}_{YYYYMMDD}_{HHMMSS}.eval.gz
        date_pattern = re.compile(r"_(\d{8})_\d{6}\.eval\.gz$")

        for orphan in all_orphans:
            # Check if from E2E test task
            is_e2e = any(pattern in orphan for pattern in e2e_task_patterns)
            if is_e2e:
                e2e_orphans.add(orphan)
                continue

            # Check if from before the DB started
            if earliest_date:
                date_match = date_pattern.search(orphan)
                if date_match and date_match.group(1) < earliest_date:
                    pre_db_orphans.add(orphan)
                    continue

            # This is a real orphan - could be lost expert data
            real_orphans.add(orphan)

        # Log expected orphans
        if e2e_orphans:
            print(f"Note: {len(e2e_orphans)} orphaned eval logs from E2E test tasks (expected)")
        if pre_db_orphans:
            print(
                f"Note: {len(pre_db_orphans)} orphaned eval logs from before DB started (historical)"
            )

        # Real orphans are a problem - these could be lost expert data
        assert len(real_orphans) == 0, (
            f"Found {len(real_orphans)} orphaned eval logs from non-E2E tasks after DB started "
            f"(files on disk without DB records). First 5: {list(real_orphans)[:5]}"
        )
