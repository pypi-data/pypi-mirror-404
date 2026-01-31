"""
Runtime import tests.

These tests verify that all code paths that trigger lazy imports work correctly.
This catches missing dependencies that aren't imported at startup.

Run with: uv run pytest tests/e2e/test_runtime_imports.py -v
"""

import json
import os
import subprocess
from pathlib import Path

import pytest
import requests

# Configuration
BASE_URL = os.environ.get("HTE_API_URL", "https://cyber-task-horizons.com")
VPS_HOST = os.environ.get("VPS_HOST", "root@209.38.25.118")
TEST_USER_ID = "7809c0b8-5c80-462c-b16c-265ab896f429"
CLI_CONFIG_PATH = Path.home() / "Library" / "Application Support" / "hte-cli" / "config.json"

# All benchmarks that should be testable
BENCHMARKS = ["cybergym", "cybench", "intercode-ctf", "nyuctf", "cybashbench", "cvebench"]


def ssh_query(query: str) -> str:
    """Run a sqlite3 query on the VPS."""
    result = subprocess.run(
        ["ssh", VPS_HOST, f'sqlite3 /opt/hte-web/data/human_baseline.db "{query}"'],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip()


@pytest.fixture(scope="module")
def api_headers():
    """Get API headers."""
    config = json.loads(CLI_CONFIG_PATH.read_text())
    return {"Authorization": f"Bearer {config['api_key']}"}


@pytest.fixture(scope="module")
def assignments(api_headers):
    """Get all assignments for test user."""
    # Use internal endpoint (public /assignments is deprecated, returns 410)
    response = requests.get(
        f"{BASE_URL}/api/v1/cli/assignments-internal",
        headers=api_headers,
        timeout=30,
    )
    assert response.status_code == 200
    return response.json()


class TestRuntimeImports:
    """Test endpoints that trigger runtime/lazy imports."""

    def test_assignments_endpoint_no_import_error(self, api_headers):
        """Assignments endpoint should not have import errors."""
        # Use internal endpoint (public is deprecated)
        response = requests.get(
            f"{BASE_URL}/api/v1/cli/assignments-internal",
            headers=api_headers,
            timeout=30,
        )
        assert response.status_code != 500, f"Import error: {response.text}"
        assert response.status_code == 200

    @pytest.mark.parametrize("benchmark", BENCHMARKS)
    def test_files_endpoint_per_benchmark(self, api_headers, assignments, benchmark):
        """Files endpoint should work for each benchmark (triggers adapter imports)."""
        assignment = next((a for a in assignments if a.get("benchmark") == benchmark), None)
        if not assignment:
            pytest.skip(f"No {benchmark} assignment")

        response = requests.get(
            f"{BASE_URL}/api/v1/cli/assignments/{assignment['assignment_id']}/files",
            headers=api_headers,
            timeout=30,
        )

        # 404 is ok (files might not exist), 500 is import error
        assert (
            response.status_code != 500
        ), f"Files endpoint failed for {benchmark} (likely import error): {response.text}"

    @pytest.mark.parametrize("benchmark", BENCHMARKS)
    def test_compose_endpoint_per_benchmark(self, api_headers, assignments, benchmark):
        """Compose endpoint should work for each benchmark."""
        assignment = next((a for a in assignments if a.get("benchmark") == benchmark), None)
        if not assignment:
            pytest.skip(f"No {benchmark} assignment")

        response = requests.get(
            f"{BASE_URL}/api/v1/cli/assignments/{assignment['assignment_id']}/compose",
            headers=api_headers,
            timeout=30,
        )

        # 404 is ok (compose might not exist), 500 is import error
        assert (
            response.status_code != 500
        ), f"Compose endpoint failed for {benchmark} (likely import error): {response.text}"

    def test_session_creation_endpoint(self, api_headers, assignments):
        """Session creation endpoint should work."""
        # Find an assignment without a session (session_id is None)
        assignment = next((a for a in assignments if a.get("session_id") is None), None)
        if not assignment:
            pytest.skip("No assignments without sessions")

        response = requests.post(
            f"{BASE_URL}/api/v1/cli/assignments/{assignment['assignment_id']}/create-session",
            headers=api_headers,
            timeout=30,
        )

        # 409 (already has session) is ok, 500 is import error
        assert (
            response.status_code != 500
        ), f"Session creation failed (likely import error): {response.text}"


class TestDockerImports:
    """Test that the Docker container can import all modules."""

    def test_backend_can_import_all_datasets(self):
        """Backend should be able to import all dataset modules."""
        # Run import test in Docker container on VPS
        result = subprocess.run(
            [
                "ssh",
                VPS_HOST,
                """docker exec hte-web-backend-1 python -c "
from human_ttc_eval.datasets import HUMAN_REGISTRY
print(f'Loaded {len(HUMAN_REGISTRY)} benchmarks: {list(HUMAN_REGISTRY.keys())}')
" """,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            pytest.fail(f"Import failed in container: {result.stderr}")

        assert "Loaded" in result.stdout
        # Should have exactly 7 benchmarks
        assert "7 benchmarks" in result.stdout, f"Expected 7 benchmarks, got: {result.stdout}"

    def test_backend_can_import_adapters(self):
        """Backend should be able to instantiate adapters."""
        result = subprocess.run(
            [
                "ssh",
                VPS_HOST,
                """docker exec hte-web-backend-1 python -c "
from human_ttc_eval.datasets import HUMAN_REGISTRY
for name, cls in HUMAN_REGISTRY.items():
    try:
        adapter = cls(name)
        print(f'{name}: OK')
    except Exception as e:
        print(f'{name}: FAIL - {e}')
" """,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if "FAIL" in result.stdout:
            pytest.fail(f"Adapter instantiation failed: {result.stdout}")

        # All benchmarks should show OK - STRICT check
        for benchmark in BENCHMARKS:
            assert (
                f"{benchmark}: OK" in result.stdout
            ), f"Benchmark {benchmark} not found or not OK in output: {result.stdout}"


class TestLocalImports:
    """Test local import chains (pre-deploy verification)."""

    def test_local_datasets_import(self):
        """Local human_ttc_eval.datasets should import cleanly."""
        # human_ttc_eval is in the parent project, not the CLI package
        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-c",
                "from human_ttc_eval.datasets import HUMAN_REGISTRY; "
                "print(f'OK: {len(HUMAN_REGISTRY)} benchmarks')",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd="/Users/jack/projects/lyptus-mono/cyber-task-horizons",
        )

        if result.returncode != 0:
            pytest.fail(f"Local import failed: {result.stderr}")

        assert "OK:" in result.stdout
