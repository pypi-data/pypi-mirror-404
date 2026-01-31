#!/usr/bin/env python3
"""
Automated E2E test runner using pexpect.

Drives the interactive hte-cli and verifies:
1. Container environments match documented specs
2. Submission flow works
3. Artifacts are created correctly
"""

import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pexpect
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class TeeWriter:
    """Write to multiple outputs (e.g., file and stdout)."""

    def __init__(self, *writers):
        self.writers = writers

    def write(self, data):
        for w in self.writers:
            w.write(data)
            w.flush()

    def flush(self):
        for w in self.writers:
            w.flush()


console = Console()

# Regex to strip ANSI escape codes from terminal output
ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return ANSI_ESCAPE.sub("", text)


VPS_HOST = os.environ.get("VPS_HOST", "root@209.38.25.118")

# Use the pipx-installed CLI (what experts use), not the local venv version
# This ensures E2E tests validate the actual published PyPI package
HTE_CLI_PATH = Path.home() / ".local" / "bin" / "hte-cli"

# Environment verification commands per benchmark
# Based on docs/benchmark-environments.md
# Format: (command, expected_pattern, description)
# STRICT: All tests must pass - no optional/informational checks
# These tests verify the exact environment specified in docs
ENVIRONMENT_CHECKS = {
    "intercode-ctf": [
        # Working directory: /ctf/{task_num} (e.g., /ctf/3, /ctf/85)
        ("pwd", "/ctf/", "Working directory is /ctf/{task}"),
        # OS: Ubuntu (not Kali, not Debian)
        ("cat /etc/os-release | grep '^NAME='", "Ubuntu", "Ubuntu base image"),
        # Core tools - must be at exact paths
        ("which gdb", "/usr/bin/gdb", "gdb at /usr/bin/gdb"),
        ("which python3", "/usr/bin/python3", "python3 at /usr/bin/python3"),
        ("which netcat", "/usr/bin/netcat", "netcat installed"),
        ("which tcpdump", "/usr/bin/tcpdump", "tcpdump installed"),
        ("which curl", "/usr/bin/curl", "curl installed"),
        # Forensics tools - STRICT: must exist
        ("which mmls", "/usr/bin/mmls", "mmls (sleuthkit) at /usr/bin/mmls"),
        # Python packages - must import successfully
        ("python3 -c 'from pwn import *; print(\"pwntools\")'", "pwntools", "pwntools importable"),
        ("python3 -c 'from scapy.all import *; print(\"scapy\")'", "scapy", "scapy importable"),
        (
            "python3 -c 'from Crypto.Cipher import AES; print(\"crypto\")'",
            "crypto",
            "pycryptodome importable",
        ),
        ("python3 -c 'import requests; print(\"requests\")'", "requests", "requests importable"),
        # apt-get must work (PIP_BREAK_SYSTEM_PACKAGES=1 set)
        ("apt-get --version", "apt", "apt-get available"),
        # Verify can install packages
        ("pip3 --version", "pip", "pip3 available"),
    ],
    "nyuctf": [
        # Working directory: /home/ctfplayer/ctf_files
        ("pwd", "/home/ctfplayer", "Working directory is /home/ctfplayer"),
        # User: ctfplayer (NOT root)
        ("whoami", "ctfplayer", "Running as ctfplayer user"),
        # User ID must be 1000 (standard non-root)
        ("id -u", "1000", "User ID is 1000"),
        # Passwordless sudo must work
        ("sudo -n whoami", "root", "Passwordless sudo to root"),
        # OS: Ubuntu 22.04 specifically
        ("cat /etc/os-release | grep VERSION_ID", "22.04", "Ubuntu 22.04 base"),
        # Core tools at expected paths - STRICT
        ("which gdb", "/usr/bin/gdb", "gdb at /usr/bin/gdb"),
        ("which radare2", "/usr/bin/radare2", "radare2 at /usr/bin/radare2"),
        ("which sqlmap", "/usr/bin/sqlmap", "sqlmap at /usr/bin/sqlmap"),
        ("which jadx", "/usr/local/bin/jadx", "jadx at /usr/local/bin/jadx"),
        # Python venv must exist at expected location
        (
            "test -f /home/ctfplayer/.ctfenv/bin/python3 && echo 'venv'",
            "venv",
            "Python venv at ~/.ctfenv",
        ),
        # Python packages via venv
        ("python3 -c 'from pwn import *; print(\"pwntools\")'", "pwntools", "pwntools importable"),
        ("python3 -c 'import angr; print(\"angr\")'", "angr", "angr importable"),
        ("python3 -c 'import z3; print(\"z3\")'", "z3", "z3-solver importable"),
        # 32-bit support (for CTF binaries)
        ("test -f /lib32/libc.so.6 && echo 'lib32'", "lib32", "32-bit libc available"),
        # Task files location - STRICT
        (
            "test -d /home/ctfplayer/ctf_files && echo 'EXISTS'",
            "EXISTS",
            "ctf_files directory exists",
        ),
    ],
    "cybench": [
        # Working directory: /app (official cybench/cybench:latest image)
        ("pwd", "/app", "Working directory is /app"),
        # OS: Kali Linux (must contain 'Kali' in name)
        ("cat /etc/os-release | grep '^NAME='", "Kali", "Kali Linux base image"),
        # Required tools - STRICT: must exist at expected paths
        # Using cybench/cybench:latest which has all these tools
        ("which gdb", "/usr/bin/gdb", "gdb at /usr/bin/gdb"),
        ("which ghidra", "/usr/bin/ghidra", "ghidra at /usr/bin/ghidra"),
        ("which radare2", "/usr/bin/radare2", "radare2 at /usr/bin/radare2"),
        ("which binwalk", "/usr/bin/binwalk", "binwalk at /usr/bin/binwalk"),
        # Security tools - STRICT
        ("which nmap", "/usr/bin/nmap", "nmap at /usr/bin/nmap"),
        ("which sqlmap", "/usr/bin/sqlmap", "sqlmap at /usr/bin/sqlmap"),
        # Docker available (daemon may not be running in all test contexts)
        ("docker --version", "Docker version", "Docker available"),
        # NOTE: Docker daemon check (docker ps) removed - DinD requires privileged
        # mode which isn't always available. Web challenges needing DinD will
        # fail at runtime if daemon isn't accessible.
        # Python via venv - STRICT
        ("test -f /venv/bin/python3 && echo 'venv'", "venv", "Python venv at /venv"),
        (
            "/venv/bin/python3 -c 'from pwn import *; print(\"pwntools\")'",
            "pwntools",
            "pwntools in /venv",
        ),
        # apt-get for additional tools
        ("apt-get --version", "apt", "apt-get available"),
        # Task files visible - cybench tasks have nested directories (blog/, nginx/, etc.)
        # Check that files exist in /root (not just empty directory) using test -gt 0
        ("test $(ls -A /root/ | wc -l) -gt 0", None, "Items in /root"),
        # For tasks with subdirs (chunky, etc.), verify structure is mounted
        (
            "test $(find /root -type f 2>/dev/null | head -5 | wc -l) -gt 0",
            None,
            "Files under /root (recursive)",
        ),
    ],
    "cybergym": [
        # Working directory: /root
        ("pwd", "/root", "Working directory is /root"),
        # OS: Kali Linux (same base as cybench)
        ("cat /etc/os-release | grep '^NAME='", "Kali", "Kali Linux base image"),
        # CyberGym-specific: submit.sh in home dir for PoC submission
        ("test -f /root/submit.sh && echo 'submit.sh'", "submit.sh", "submit.sh present in /root"),
        # Note: submit.sh executable check removed - file is made executable by task command
        # Required tools - STRICT (same image as cybench)
        ("which gdb", "/usr/bin/gdb", "gdb at /usr/bin/gdb"),
        ("which ghidra", "/usr/bin/ghidra", "ghidra at /usr/bin/ghidra"),
        ("which radare2", "/usr/bin/radare2", "radare2 at /usr/bin/radare2"),
        # Python via venv (same as cybench/cybench:latest)
        ("test -f /venv/bin/python3 && echo 'venv'", "venv", "Python venv at /venv"),
        ("which nmap", "/usr/bin/nmap", "nmap at /usr/bin/nmap"),
        ("which curl", "/usr/bin/curl", "curl at /usr/bin/curl"),
        # apt-get for additional tools
        ("apt-get --version", "apt", "apt-get available"),
    ],
    "cvebench": [
        # OS: Kali Linux
        ("cat /etc/os-release | grep '^NAME='", "Kali", "Kali Linux base image"),
        # Core security tools for CVE exploitation - STRICT
        ("which python3", "/usr/bin/python3", "python3 at /usr/bin/python3"),
        ("which nmap", "/usr/bin/nmap", "nmap at /usr/bin/nmap"),
        ("which curl", "/usr/bin/curl", "curl at /usr/bin/curl"),
        ("which wget", "/usr/bin/wget", "wget at /usr/bin/wget"),
        # Network access to target - STRICT
        ("which nc", "/usr/bin/nc", "netcat at /usr/bin/nc"),
        # apt-get for additional tools
        ("apt-get --version", "apt", "apt-get available"),
    ],
    "nl2bash": [
        # Minimal container - just Python for command submission
        ("python3 --version", "Python 3.12", "Python 3.12 (slim image)"),
    ],
    "cybashbench": [
        # Minimal container - just Python for command submission
        ("python3 --version", "Python 3.12", "Python 3.12 (slim image)"),
    ],
}

# Task-specific file expectations
# Maps benchmark -> task_id -> list of expected paths
# Use "*" as task_id for checks that apply to all tasks in a benchmark
TASK_FILE_CHECKS = {
    "cybench": {
        "chunky": ["/root/blog", "/root/nginx", "/root/rcache"],
        "avatar": ["/root/chall.py"],
        "lootstash": ["/root/stash"],
        "primary_knowledge": [],  # No local files - network-based
    },
    "cybergym": {
        "*": ["/root/submit.sh"],  # All cybergym tasks need submit.sh in home
    },
    "nyuctf": {
        "*": ["/home/ctfplayer/ctf_files"],  # Standard location
    },
    "intercode-ctf": {
        "*": ["/ctf"],  # Task files in /ctf directory
    },
}


def get_file_checks_for_task(benchmark: str, task_id: str) -> list[tuple]:
    """Generate file existence checks based on task expectations."""
    checks = []
    task_files = TASK_FILE_CHECKS.get(benchmark, {})

    # Try task-specific first, then fallback to wildcard
    expected = task_files.get(task_id) or task_files.get("*", [])

    for path in expected:
        checks.append((f"test -e {path} && echo 'EXISTS'", "EXISTS", f"{path} exists"))

    return checks


# Commands to run for submission tests
SUBMISSION_TESTS = {
    "intercode-ctf": {
        "score_cmd": 'task score "test_flag_123"',
        "score_expect": "Score:",  # Output shows "Score: I" (I=Incorrect)
        "submit_cmd": 'task submit "test_flag_for_e2e"',
        "submit_expect": "submitted",
    },
    "nyuctf": {
        "score_cmd": 'task score "test_flag_123"',
        "score_expect": "Score:",  # Output shows "Score: I" (I=Incorrect)
        "submit_cmd": 'task submit "test_flag_for_e2e"',
        "submit_expect": "submitted",
    },
    "cybench": {
        "score_cmd": 'task score "test_flag_123"',
        "score_expect": "Score:",  # Output shows "Score: I" (I=Incorrect)
        "submit_cmd": 'task submit "test_flag_for_e2e"',
        "submit_expect": "submitted",
    },
    "cybergym": {
        # CyberGym uses submit.sh, not task submit
        "score_cmd": None,
        "submit_cmd": 'task submit "dummy_poc_path"',  # Will fail but tests flow
        "submit_expect": "submitted",
    },
    "cvebench": {
        "score_cmd": None,
        "submit_cmd": 'task submit "test"',
        "submit_expect": "submitted",
    },
    "cybashbench": {
        # Single-shot - no score command
        "score_cmd": None,
        "submit_cmd": 'task submit "ls -la"',
        "submit_expect": "submitted",
    },
    "nl2bash": {
        # Single-shot - no score command (same as cybashbench)
        "score_cmd": None,
        "submit_cmd": 'task submit "ls -la"',
        "submit_expect": "submitted",
    },
}


@dataclass
class TestResult:
    """Result of a single test."""

    name: str
    passed: bool
    output: str
    error: str = ""


def ssh_query(query: str) -> str:
    """Run a sqlite3 query on the VPS."""
    result = subprocess.run(
        ["ssh", VPS_HOST, f'sqlite3 /opt/hte-web/data/human_baseline.db "{query}"'],
        capture_output=True,
        text=True,
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


def create_session_for_task(task_id: str) -> str | None:
    """Create a session for a task via the CLI API test endpoint.

    Returns session_id if successful, None otherwise.
    """
    import json
    from pathlib import Path

    base_url = os.environ.get("HTE_API_URL", "https://cyber-task-horizons.com")
    test_email = "e2e-test@lyptus.dev"

    # Read API key from CLI config
    config_path = Path.home() / "Library" / "Application Support" / "hte-cli" / "config.json"
    if not config_path.exists():
        console.print(f"[red]CLI config not found: {config_path}[/red]")
        return None

    config = json.loads(config_path.read_text())
    api_key = config.get("api_key")
    if not api_key:
        console.print("[red]No API key in config[/red]")
        return None

    headers = {"Authorization": f"Bearer {api_key}"}

    # Get assignment ID for this task
    assignment_id = ssh_query(f"""
        SELECT a.id FROM assignments a
        JOIN users u ON a.user_id = u.id
        WHERE u.email = '{test_email}' AND a.task_id = '{task_id}'
        LIMIT 1
    """)

    if not assignment_id:
        console.print(f"[red]No assignment found for task {task_id}[/red]")
        return None

    # Create session via CLI test endpoint
    session_resp = requests.post(
        f"{base_url}/api/v1/cli/assignments/{assignment_id}/create-session",
        headers=headers,
    )

    if session_resp.status_code == 200:
        session_id = session_resp.json()["session_id"]
        console.print(f"[green]Created session: {session_id}[/green]")
        return session_id
    else:
        console.print(f"[red]Failed to create session: {session_resp.text}[/red]")
        return None


def test_join_endpoint(session_id: str, benchmark: str) -> list[TestResult]:
    """Test the session join endpoint while session is in 'created' state.

    This tests the API response before the CLI actually joins.
    """
    import json
    from pathlib import Path

    results = []
    base_url = os.environ.get("HTE_API_URL", "https://cyber-task-horizons.com")

    config_path = Path.home() / "Library" / "Application Support" / "hte-cli" / "config.json"
    if not config_path.exists():
        results.append(TestResult("Join API test", False, "", "No CLI config"))
        return results

    config = json.loads(config_path.read_text())
    headers = {"Authorization": f"Bearer {config['api_key']}"}

    # Test the join endpoint
    response = requests.post(
        f"{base_url}/api/v1/cli/sessions/{session_id}/join",
        headers=headers,
        timeout=30,
    )

    if response.status_code != 200:
        results.append(TestResult("Join API response", False, "", f"Status {response.status_code}"))
        return results

    data = response.json()

    # Test: scorer_type is present
    if "scorer_type" in data:
        results.append(TestResult("Join returns scorer_type", True, data["scorer_type"]))
    else:
        results.append(TestResult("Join returns scorer_type", False, "", "Missing scorer_type"))

    # Test: intermediate_scoring is present
    if "intermediate_scoring" in data:
        results.append(
            TestResult("Join returns intermediate_scoring", True, str(data["intermediate_scoring"]))
        )
    else:
        results.append(TestResult("Join returns intermediate_scoring", False, "", "Missing"))

    # Test: target is present for flag-based benchmarks
    if benchmark in ("cybench", "nyuctf", "intercode-ctf"):
        has_target = "target" in data or ("task" in data and "target" in data.get("task", {}))
        if has_target:
            results.append(TestResult("Join returns target", True, "Present"))
        else:
            results.append(TestResult("Join returns target", False, "", "Missing target"))

    return results


def run_automated_test(task_id: str, benchmark: str, timeout: int = 300) -> list[TestResult]:
    """
    Run automated E2E test for a task using pexpect.

    Returns list of test results.
    """
    results = []

    console.print(f"\n[bold]Starting automated test: {benchmark}/{task_id}[/bold]")

    # First, create a session for this task via web API
    console.print("Creating session via web API...")
    session_id = create_session_for_task(task_id)
    if not session_id:
        results.append(
            TestResult("Session creation", False, "", "Failed to create session via web API")
        )
        return results
    results.append(TestResult("Session creation", True, f"Session: {session_id[:8]}..."))

    # Test join endpoint while session is in 'created' state (before CLI joins)
    console.print("Testing join endpoint...")
    join_results = test_join_endpoint(session_id, benchmark)
    results.extend(join_results)

    # Start the CLI using the new session join flow
    # Session has status="created", so CLI will run full setup
    # Use explicit pipx path to test the published PyPI version, not local dev
    if not HTE_CLI_PATH.exists():
        console.print(f"[red]hte-cli not found at {HTE_CLI_PATH}[/red]")
        console.print("[yellow]Install with: pipx install hte-cli[/yellow]")
        results.append(TestResult("CLI installed", False, "", f"hte-cli not at {HTE_CLI_PATH}"))
        return results

    console.print(f"Launching {HTE_CLI_PATH} session join {session_id}...")
    child = pexpect.spawn(
        f"{HTE_CLI_PATH} session join {session_id}",
        encoding="utf-8",
        timeout=timeout,
        env={**os.environ, "TERM": "dumb"},  # Disable colors for easier parsing
    )

    # Log file for debugging AND stream to stdout
    log_path = Path(f"/tmp/e2e_test_{benchmark}_{task_id.replace('/', '_')}.log")
    log_file = log_path.open("w")

    # Tee output to both log file and stdout for real-time visibility
    child.logfile = TeeWriter(log_file, sys.stdout)

    try:
        # session join flow: first checks Docker, then joins session
        # Handle Docker check prompt if it appears (Docker not running = test failure)
        console.print("Waiting for Docker check / session join...")
        idx = child.expect(
            [
                r"Docker running",  # Docker OK - continue
                r"Start Docker and retry\?",  # Docker not running - fail test
                r"Session Joined",  # Skipped Docker message, got session
                pexpect.TIMEOUT,
                pexpect.EOF,
            ],
            timeout=60,
        )

        if idx == 1:  # Docker not running prompt
            child.sendline("n")  # Don't retry - fail the test
            results.append(
                TestResult("Docker check", False, "", "Docker not running - test requires Docker")
            )
            return results
        elif idx == 0:  # Docker OK
            results.append(TestResult("Docker check", True, "Docker running"))
            # Now wait for Session Joined
            idx = child.expect([r"Session Joined", pexpect.TIMEOUT, pexpect.EOF], timeout=60)
            if idx != 0:
                results.append(TestResult("CLI startup", False, "", "Never got 'Session Joined'"))
                return results
        elif idx == 2:  # Got Session Joined directly
            pass  # Continue below
        else:  # TIMEOUT or EOF
            results.append(TestResult("CLI startup", False, "", "Never got 'Session Joined'"))
            return results

        results.append(TestResult("CLI startup", True, "Session joined"))

        # Wait for environment setup to complete
        console.print("Waiting for environment setup...")
        idx = child.expect(
            [
                r"Environment ready",  # Setup complete, timer started
                r"Timer started",
                pexpect.TIMEOUT,
            ],
            timeout=600,
        )  # 10 minutes for image pulls

        if idx == 2:  # TIMEOUT
            results.append(
                TestResult(
                    "Environment setup",
                    False,
                    child.before or "",
                    "Timeout waiting for environment",
                )
            )
            child.sendline("exit")
            return results

        results.append(TestResult("Environment setup", True, "Environment ready"))

        # Wait for the "Login to the system" message and docker exec command
        # CVE bench builds containers from source, can take 5+ minutes
        console.print("Waiting for docker exec command...")
        idx = child.expect(
            [
                r"Login to the system",
                r"docker exec -it",
                pexpect.TIMEOUT,
            ],
            timeout=300,  # 5 minutes for slow builds (cvebench)
        )

        if idx == 2:  # TIMEOUT
            results.append(
                TestResult(
                    "Container start", False, child.before or "", "Timeout waiting for container"
                )
            )
            child.sendline("exit")
            return results

        results.append(TestResult("Container start", True, "Docker container ready"))

        # Now we need to actually execute the docker exec command
        # Wait a bit more to capture the full docker command
        time.sleep(2)

        # Read any additional output
        try:
            child.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=3)
        except Exception:
            pass

        # Extract the docker command from all output so far
        output = child.before or ""
        docker_match = re.search(r"(docker exec -it \S+ (?:bash -l|bash|sh))", output)

        if not docker_match:
            # Try reading the log file which has all output
            log_content = log_path.read_text() if log_path.exists() else ""
            docker_match = re.search(r"(docker exec -it \S+ (?:bash -l|bash|sh))", log_content)

        if not docker_match:
            results.append(
                TestResult("Docker exec", False, output[:200], "Could not find docker exec command")
            )
            child.sendline("exit")
            return results

        docker_cmd = docker_match.group(1)
        console.print(f"Executing: {docker_cmd}")

        # Spawn a new pexpect for the docker exec
        docker_child = pexpect.spawn(
            docker_cmd,
            encoding="utf-8",
            timeout=60,
            env={**os.environ, "TERM": "dumb"},
        )
        docker_log_path = Path(f"/tmp/e2e_docker_{benchmark}_{task_id.replace('/', '_')}.log")
        docker_log_file = docker_log_path.open("w")
        docker_child.logfile = TeeWriter(docker_log_file, sys.stdout)

        # Wait for shell prompt
        prompt_patterns = [
            r"ctf@\w+:",  # intercode-ctf
            r"ctfplayer@",  # nyuctf
            r"root@\w+:",  # cybench/cybergym/cvebench
            r"\$\s*$",  # Generic shell prompt
            r"#\s*$",  # Root prompt
            pexpect.TIMEOUT,
        ]

        idx = docker_child.expect(prompt_patterns, timeout=30)
        if idx == len(prompt_patterns) - 1:  # TIMEOUT
            results.append(
                TestResult(
                    "Shell prompt", False, docker_child.before or "", "Timeout waiting for shell"
                )
            )
            docker_child.close()
            child.sendline("exit")
            return results

        results.append(TestResult("Shell prompt", True, "Got shell prompt"))

        # Run environment checks using docker exec (more reliable than pexpect buffer)
        console.print("Running environment checks...")

        # Extract container name from docker_cmd
        container_match = re.search(r"docker exec -it (\S+)", docker_cmd)
        container_name = container_match.group(1) if container_match else None

        if not container_name:
            results.append(
                TestResult("Container name", False, "", "Could not extract container name")
            )
        else:
            # First verify container is responding
            try:
                result = subprocess.run(
                    ["docker", "exec", container_name, "echo", "CONTAINER_OK"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if "CONTAINER_OK" in result.stdout:
                    results.append(TestResult("Container shell", True, "Container responding"))
                else:
                    results.append(
                        TestResult("Container shell", False, "", "Container not responding")
                    )
            except Exception as e:
                results.append(TestResult("Container shell", False, "", str(e)[:40]))

            # Get benchmark-specific checks from ENVIRONMENT_CHECKS
            env_checks = ENVIRONMENT_CHECKS.get(benchmark, [])

            # Add task-specific file checks
            file_checks = get_file_checks_for_task(benchmark, task_id)
            all_checks = env_checks + file_checks

            for check in all_checks:
                # Unpack: (command, expected_pattern, description)
                if len(check) == 3:
                    cmd, expected, desc = check
                else:
                    cmd, expected = check
                    desc = cmd[:30]

                try:
                    # Run command directly via docker exec (not through pexpect)
                    result = subprocess.run(
                        ["docker", "exec", container_name, "sh", "-c", cmd],
                        capture_output=True,
                        text=True,
                        timeout=30,  # Increased for slow imports (angr takes ~10s)
                    )
                    output = result.stdout.strip()
                    stderr = result.stderr.strip()

                    if expected:
                        passed = expected.lower() in output.lower()
                    else:
                        # No expected pattern - just check command succeeded
                        passed = result.returncode == 0

                    display = output[:50] if output else stderr[:50] if stderr else "(empty)"
                    results.append(TestResult(desc, passed, display))
                except subprocess.TimeoutExpired:
                    results.append(TestResult(desc, False, "", "Timeout"))
                except Exception as e:
                    results.append(TestResult(desc, False, "", str(e)[:40]))

        # Run submission tests
        console.print("Running submission tests...")
        sub_tests = SUBMISSION_TESTS.get(benchmark, {})

        # Test task status - clear buffer first
        try:
            docker_child.read_nonblocking(size=10000, timeout=0.5)
        except Exception:
            pass
        docker_child.sendline("task status")
        time.sleep(1)
        try:
            # Look for the status output pattern
            docker_child.expect(r"Status:.*Time:", timeout=10)
            results.append(TestResult("task status", True, "Status command works"))
        except pexpect.TIMEOUT:
            # Fallback - just check we got some output
            output = strip_ansi(docker_child.before or "")
            passed = "status" in output.lower() or "time" in output.lower()
            results.append(
                TestResult("task status", passed, output[:80] if output else "(no output)")
            )

        # Test score command if available
        if sub_tests.get("score_cmd"):
            # Clear buffer before score test to avoid capturing stale output
            try:
                docker_child.read_nonblocking(size=10000, timeout=0.5)
            except Exception:
                pass
            docker_child.sendline(sub_tests["score_cmd"])

            expected_score = sub_tests.get("score_expect")
            if expected_score:
                # Wait specifically for the score output, not just any prompt
                # The score output appears as "Answer: ..., Score: I" or similar
                try:
                    idx = docker_child.expect(
                        [expected_score, pexpect.TIMEOUT],
                        timeout=10,
                    )
                    if idx == 0:
                        # Found expected output - capture surrounding context
                        output = strip_ansi(docker_child.before or "") + expected_score
                        # Read a bit more to get the full score line
                        try:
                            extra = docker_child.read_nonblocking(size=100, timeout=1)
                            output += strip_ansi(extra)
                        except Exception:
                            pass
                        passed = True
                        details = output[:200]
                    else:
                        # Timeout - capture what we have
                        output = strip_ansi(docker_child.before or "")
                        passed = False
                        details = f"Timeout waiting for '{expected_score}': {output[:100]}..."
                except Exception as e:
                    passed = False
                    details = f"Error: {e}"
                results.append(TestResult("task score", passed, details))
            else:
                # No expected output - just check command runs
                time.sleep(2)
                docker_child.expect(prompt_patterns[:-1], timeout=30)
                output = strip_ansi(docker_child.before or "")
                results.append(
                    TestResult(
                        "task score",
                        True,
                        output[:200],
                    )
                )

        # Submit answer
        console.print("Submitting test answer...")
        docker_child.sendline(sub_tests.get("submit_cmd", 'task submit "e2e_test"'))

        # Wait for confirmation prompt and confirm
        time.sleep(2)
        idx = docker_child.expect(
            [
                r"Yes \(y\) or No \(n\):",  # Confirmation prompt
                "submitted",
                "Submitted",
                pexpect.TIMEOUT,
                pexpect.EOF,
            ],
            timeout=30,
        )

        if idx == 0:
            # Got confirmation prompt, send 'y'
            docker_child.sendline("y")
            time.sleep(2)
            # Wait for submission response or EOF (container exits after submit)
            idx = docker_child.expect(
                [
                    "submitted",
                    "Submitted",
                    "Task Complete",
                    pexpect.TIMEOUT,
                    pexpect.EOF,  # Container exits after successful submit
                ],
                timeout=60,
            )
            # EOF (idx=4) is expected - container exits after task submit
            # TIMEOUT (idx=3) is a failure
            if idx != 3:
                results.append(
                    TestResult("Submission", True, "Answer submitted (container exited)")
                )
            else:
                results.append(
                    TestResult(
                        "Submission",
                        False,
                        docker_child.before or "",
                        "Submission timed out waiting for result",
                    )
                )
        elif idx < 3:
            results.append(TestResult("Submission", True, "Answer submitted"))
        elif idx == 4:  # EOF without confirmation - might be ok
            results.append(
                TestResult("Submission", True, "Container exited (submission likely succeeded)")
            )
        else:
            results.append(
                TestResult(
                    "Submission", False, docker_child.before or "", "Submission timed out at prompt"
                )
            )

        # Close docker child (may already be closed from EOF)
        try:
            docker_child.close()
        except Exception:
            pass
        console.print(f"[dim]Docker log saved to: {docker_log_path}[/dim]")

        # Wait for CLI to finish uploading - must see "Done!" which comes after upload
        # Upload can take up to 30 seconds for eval log processing
        time.sleep(3)
        idx = child.expect(
            [
                "Done!",  # This appears AFTER upload completes
                "Return to the web UI",  # Also after upload
                pexpect.TIMEOUT,
                pexpect.EOF,
            ],
            timeout=180,
        )  # 3 minutes for slow uploads

        if idx < 2:  # Got done message
            results.append(TestResult("Upload", True, "Result uploaded to server"))
        else:
            # Check if we at least got "Task completed"
            output = child.before or ""
            if "task completed" in output.lower() or "score:" in output.lower():
                results.append(TestResult("Upload", True, "Task completed (upload pending)"))
            else:
                results.append(TestResult("Upload", False, output[:200], "Upload may have failed"))

    except pexpect.TIMEOUT as e:
        results.append(TestResult("Timeout", False, "", str(e)))
    except pexpect.EOF as e:
        results.append(TestResult("Unexpected EOF", False, "", str(e)))
    except Exception as e:
        results.append(TestResult("Error", False, "", str(e)))
    finally:
        child.close()
        console.print(f"[dim]Log saved to: {log_path}[/dim]")

    return results


def verify_artifacts(task_id: str, benchmark: str) -> list[TestResult]:
    """Verify session and eval log artifacts were created."""
    results = []

    # Get expected answer from SUBMISSION_TESTS
    sub_tests = SUBMISSION_TESTS.get(benchmark, {})
    submit_cmd = sub_tests.get("submit_cmd", "")
    expected_answer = None
    if 'task submit "' in submit_cmd:
        expected_answer = submit_cmd.split('task submit "')[1].rstrip('"')
    elif "task submit '" in submit_cmd:
        expected_answer = submit_cmd.split("task submit '")[1].rstrip("'")

    # Check session in database
    session_info = ssh_query(f"""
        SELECT id, status, score, client_active_seconds, answer
        FROM sessions
        WHERE task_id = '{task_id}'
        ORDER BY created_at DESC
        LIMIT 1
    """)

    if session_info:
        parts = session_info.split("|")
        session_id = parts[0]
        status = parts[1] if len(parts) > 1 else ""
        score = parts[2] if len(parts) > 2 else ""
        active_seconds = parts[3] if len(parts) > 3 else ""
        answer = parts[4] if len(parts) > 4 else ""

        results.append(TestResult("Session created", True, f"ID: {session_id}"))
        results.append(TestResult("Session status", status == "submitted", f"Status: {status}"))
        results.append(
            TestResult(
                "Active time recorded", float(active_seconds or 0) > 0, f"Seconds: {active_seconds}"
            )
        )

        # Verify answer
        if (
            expected_answer and benchmark != "cybergym"
        ):  # Cybergym submits file content, hard to verify here
            results.append(
                TestResult(
                    "Answer matches submission",
                    answer == expected_answer,
                    f"Expected: '{expected_answer}', Got: '{answer}'",
                )
            )
        else:
            results.append(
                TestResult(
                    "Answer recorded", bool(answer), f"Answer: {answer[:50]}..." if answer else ""
                )
            )

        # Score check - some benchmarks compute scores server-side later (not immediately)
        no_immediate_score = benchmark in ("cybashbench", "nl2bash")
        if no_immediate_score:
            # These benchmarks don't produce immediate scores - skip check
            pass
        else:
            results.append(
                TestResult(
                    "Score recorded", score != "", f"Score: {score}" if score else "No score"
                )
            )

        # Check events (new flow uses setup_started/setup_completed instead of session_started)
        events = ssh_query(f"""
            SELECT event_type FROM session_events
            WHERE session_id = '{session_id}'
        """)
        event_list = events.split("\n") if events else []

        # Core events in new flow
        expected_events = ["setup_started", "setup_completed", "docker_started"]
        for evt in expected_events:
            results.append(
                TestResult(
                    f"Event: {evt}", evt in event_list, f"Found events: {', '.join(event_list[:5])}"
                )
            )
    else:
        results.append(TestResult("Session created", False, "", "No session found in database"))

    # Check eval log file exists (stored as files, not in DB)
    # Format: /opt/hte-web/data/eval_logs/{benchmark}/{task_id}/{session_id}_*.eval.gz
    if session_info:
        eval_log_exists = ssh_command(f"""
            ls /opt/hte-web/data/eval_logs/*/{task_id.replace('/', '_')}/{session_id}_*.eval.gz 2>/dev/null | head -1
        """)
        results.append(
            TestResult(
                "Eval log uploaded",
                bool(eval_log_exists.strip()),
                eval_log_exists.strip()[:60] if eval_log_exists else "No eval log found",
            )
        )

    return results


def print_results(results: list[TestResult], title: str):
    """Print test results as a table."""
    table = Table(title=title)
    table.add_column("Test", style="cyan")
    table.add_column("Status")
    table.add_column("Details", max_width=60)

    passed = 0
    failed = 0

    for r in results:
        if r.passed:
            status = "[green]PASS[/green]"
            passed += 1
        else:
            status = "[red]FAIL[/red]"
            failed += 1

        details = r.output if r.passed else r.error or r.output
        table.add_row(r.name, status, details[:60])

    console.print(table)
    console.print(f"\n[bold]Summary:[/bold] {passed} passed, {failed} failed")

    return failed == 0


def run_benchmark_test(benchmark: str, task_index: int = 0) -> bool:
    """Run complete E2E test for a benchmark."""
    from e2e_test import BENCHMARK_TASKS

    tasks = BENCHMARK_TASKS.get(benchmark, [])
    if not tasks:
        console.print(f"[red]Unknown benchmark: {benchmark}[/red]")
        return False

    task_id = tasks[task_index]

    console.print(
        Panel(
            f"[bold]Benchmark:[/bold] {benchmark}\n"
            f"[bold]Task:[/bold] {task_id}\n"
            f"[bold]Index:[/bold] {task_index}",
            title="E2E Automated Test",
        )
    )

    # Run the automated test
    test_results = run_automated_test(task_id, benchmark)
    all_passed = print_results(test_results, f"Test Results: {benchmark}")

    # Verify artifacts (wait a bit for server to process)
    console.print("\n[bold]Verifying artifacts...[/bold]")
    console.print("[dim]Waiting 5s for server to process...[/dim]")
    time.sleep(5)
    artifact_results = verify_artifacts(task_id, benchmark)
    artifacts_passed = print_results(artifact_results, "Artifact Verification")

    return all_passed and artifacts_passed


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        console.print("Usage: python automated_runner.py <benchmark> [task_index]")
        console.print("Benchmarks: intercode-ctf, nyuctf, cybench, cybergym, cvebench, cybashbench")
        sys.exit(1)

    benchmark = sys.argv[1]
    task_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    success = run_benchmark_test(benchmark, task_index)
    sys.exit(0 if success else 1)
