#!/usr/bin/env python3
"""
E2E Test Suite for cyber-task-horizons.

A self-contained test suite that creates its own test user, assigns tasks,
runs them interactively, and verifies all artifacts.

Usage:
    uv run python tests/e2e/e2e_test.py setup          # Create test user and assign tasks
    uv run python tests/e2e/e2e_test.py run cybergym   # Run E2E test for a benchmark
    uv run python tests/e2e/e2e_test.py verify         # Verify all test artifacts
    uv run python tests/e2e/e2e_test.py cleanup        # Remove test user and data
    uv run python tests/e2e/e2e_test.py infra          # Check infrastructure only
"""

import base64
import json
import os
import subprocess
from pathlib import Path

import click
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Configuration
BASE_URL = os.environ.get("HTE_API_URL", "https://cyber-task-horizons.com")
VPS_HOST = os.environ.get("VPS_HOST", "root@209.38.25.118")
TEST_EMAIL = "e2e-test@lyptus.dev"
TEST_PASSWORD = "e2e-test-password-123"
TEST_NAME = "E2E Test User"

# CLI config path (matches platformdirs on macOS)
CLI_CONFIG_PATH = Path.home() / "Library" / "Application Support" / "hte-cli" / "config.json"

# Use the pipx-installed CLI (what experts use), not the local venv version
HTE_CLI_PATH = Path.home() / ".local" / "bin" / "hte-cli"

# Task assignments: 4 per benchmark
# First 2 for pytest API tests, last 2 for interactive tests
BENCHMARK_TASKS = {
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

# Instructions for each benchmark type
BENCHMARK_INSTRUCTIONS = {
    "cybergym": """
In container, test the PoC verification flow:
  1. Check files: ls -la /challenge/
  2. View instructions: cat /challenge/README.md
  3. Check submit.sh exists: ls -la /submit.sh
  4. To quit without solving: task quit
  5. To test submission: create PoC and run submit.sh
""",
    "cybench": """
In container, test the CTF flag flow:
  1. Check files: ls -la /challenge/
  2. Test intermediate scoring: task score "test_flag"
  3. Final submission: task submit "flag{...}"
  4. To quit without solving: task quit
""",
    "intercode-ctf": """
In container, test the CTF flag flow:
  1. Check files: ls -la /
  2. Test intermediate scoring: task score "test_flag"
  3. Final submission: task submit "flag{...}"
  4. To quit without solving: task quit
""",
    "nyuctf": """
In container, test the CTF flag flow:
  1. Check files: ls -la /challenge/
  2. Test intermediate scoring: task score "test_flag"
  3. Final submission: task submit "flag{...}"
  4. To quit without solving: task quit
""",
    "cybashbench": """
In container, test the SINGLE-SHOT flow:
  1. Read the task prompt carefully
  2. NOTE: No 'task score' available - single submission only!
  3. Final submission: task submit "your_command_here"
  4. To quit without solving: task quit
""",
    "cvebench": """
In container, test the CVE exploitation flow:
  1. Check files: ls -la /
  2. View CVE description in task prompt
  3. Health endpoint is polled continuously for scoring
  4. To quit without solving: task quit
""",
}


def get_admin_jwt(admin_password: str) -> str:
    """Login as admin and get JWT token."""
    # The admin login uses form data, not JSON
    # Note: Caddy strips /api prefix, so /api/auth/login -> /auth/login on backend
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": "jacktpayne51@gmail.com",
            "password": admin_password,
        },
    )
    if response.status_code != 200:
        raise click.ClickException(f"Admin login failed: {response.text}")
    return response.json()["access_token"]


def ssh_query(query: str) -> str:
    """Run a sqlite3 query on the VPS."""
    result = subprocess.run(
        ["ssh", VPS_HOST, f'sqlite3 /opt/hte-web/data/human_baseline.db "{query}"'],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise click.ClickException(f"SSH query failed: {result.stderr}")
    return result.stdout.strip()


def ssh_command(cmd: str) -> str:
    """Run a command on the VPS."""
    result = subprocess.run(
        ["ssh", VPS_HOST, cmd],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _create_test_session_states():
    """Create sessions in cancelled and paused states for edge-case tests.

    This enables TestSessionJoin tests that verify joining cancelled/paused
    sessions fails appropriately.

    Uses the proper API flow:
    1. Login as test user (JWT auth for web UI routes)
    2. Create sessions via CLI API
    3. Cancel/pause them via web UI API
    """
    # Get CLI API key for creating sessions
    if not CLI_CONFIG_PATH.exists():
        console.print("[yellow]CLI config not found, skipping state creation[/yellow]")
        return

    config = json.loads(CLI_CONFIG_PATH.read_text())
    cli_headers = {"Authorization": f"Bearer {config['api_key']}"}

    # Login as test user to get JWT for web UI routes
    login_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=30,
    )
    if login_response.status_code != 200:
        console.print("[yellow]Could not login test user, skipping state creation[/yellow]")
        return

    jwt_token = login_response.json()["access_token"]
    jwt_headers = {"Authorization": f"Bearer {jwt_token}"}

    # Find two pending assignments
    user_id = ssh_query(f"SELECT id FROM users WHERE email = '{TEST_EMAIL}'")
    assignments = ssh_query(f"""
        SELECT a.id FROM assignments a
        LEFT JOIN sessions s ON s.assignment_id = a.id
            AND s.status IN ('created', 'in_progress', 'paused', 'cancelled')
        WHERE a.user_id = '{user_id}'
        AND a.status = 'pending'
        AND s.id IS NULL
        LIMIT 2
    """)

    if not assignments:
        console.print("[yellow]No available assignments for state tests[/yellow]")
        return

    assignment_ids = [a for a in assignments.split("\n") if a]

    # Create and cancel a session
    if len(assignment_ids) >= 1:
        # Create session via CLI API
        create_resp = requests.post(
            f"{BASE_URL}/api/v1/cli/assignments/{assignment_ids[0]}/create-session",
            headers=cli_headers,
            timeout=30,
        )
        if create_resp.status_code == 200:
            session_id = create_resp.json()["session_id"]
            # Cancel via web UI API
            cancel_resp = requests.post(
                f"{BASE_URL}/api/v1/sessions/{session_id}/cancel",
                headers=jwt_headers,
                json={"reason": "testing", "notes": "E2E test cancelled session"},
                timeout=30,
            )
            if cancel_resp.status_code == 200:
                console.print(f"[dim]Created cancelled session: {session_id[:8]}...[/dim]")
            else:
                console.print(
                    f"[yellow]Failed to cancel session: {cancel_resp.status_code}[/yellow]"
                )

    # Create and pause a session
    if len(assignment_ids) >= 2:
        # Create session via CLI API
        create_resp = requests.post(
            f"{BASE_URL}/api/v1/cli/assignments/{assignment_ids[1]}/create-session",
            headers=cli_headers,
            timeout=30,
        )
        if create_resp.status_code == 200:
            session_id = create_resp.json()["session_id"]
            # Join to make it in_progress (required before pause)
            join_resp = requests.post(
                f"{BASE_URL}/api/v1/cli/sessions/{session_id}/join",
                headers=cli_headers,
                timeout=30,
            )
            if join_resp.status_code == 200:
                # Pause via web UI API
                pause_resp = requests.patch(
                    f"{BASE_URL}/api/v1/sessions/{session_id}/pause",
                    headers=jwt_headers,
                    json={"reason": "testing", "notes": "E2E test paused session"},
                    timeout=30,
                )
                if pause_resp.status_code == 200:
                    console.print(f"[dim]Created paused session: {session_id[:8]}...[/dim]")
                else:
                    console.print(
                        f"[yellow]Failed to pause session: {pause_resp.status_code}[/yellow]"
                    )


@click.group()
def cli():
    """E2E Test Suite for cyber-task-horizons."""
    pass


@cli.command()
def infra():
    """Check infrastructure is healthy."""
    console.print("\n[bold]Infrastructure Checks[/bold]\n")

    checks = []

    # Frontend
    try:
        r = requests.get(f"{BASE_URL}/", timeout=30)
        checks.append(("Frontend", r.status_code == 200, f"Status {r.status_code}"))
    except Exception as e:
        checks.append(("Frontend", False, str(e)))

    # Backend health
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=30)
        checks.append(("Backend", r.status_code == 200, r.text[:50]))
    except Exception as e:
        checks.append(("Backend", False, str(e)))

    # CyberGym server (try external first, fall back to SSH check)
    try:
        r = requests.get("http://209.38.25.118:8666/", timeout=5)
        # 404 is expected at root
        checks.append(("CyberGym", r.status_code == 404, "404 (expected)"))
    except Exception:
        # External access failed - check via SSH (might be firewall)
        try:
            result = ssh_command("curl -s http://localhost:8666/")
            if "Not Found" in result:
                checks.append(("CyberGym", True, "OK via SSH (external blocked)"))
            else:
                checks.append(("CyberGym", False, f"SSH check: {result[:50]}"))
        except Exception as e2:
            checks.append(("CyberGym", False, f"External + SSH failed: {e2}"))

    # VPS SSH
    try:
        result = ssh_command("echo ok")
        checks.append(("VPS SSH", result == "ok", "Connected"))
    except Exception as e:
        checks.append(("VPS SSH", False, str(e)))

    # Database
    try:
        count = ssh_query("SELECT COUNT(*) FROM users")
        checks.append(("Database", True, f"{count} users"))
    except Exception as e:
        checks.append(("Database", False, str(e)))

    # Display results
    table = Table(title="Infrastructure Status")
    table.add_column("Service")
    table.add_column("Status")
    table.add_column("Details")

    all_ok = True
    for name, ok, details in checks:
        status = "[green]OK[/green]" if ok else "[red]FAIL[/red]"
        table.add_row(name, status, details)
        if not ok:
            all_ok = False

    console.print(table)

    if not all_ok:
        raise click.ClickException("Some infrastructure checks failed")

    console.print("\n[green]All infrastructure checks passed![/green]")


@cli.command()
@click.option(
    "--admin-password",
    envvar="ADMIN_PASSWORD",
    default="test1234",
    help="Admin password for API access",
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompts")
def setup(admin_password: str, yes: bool):
    """Create test user and assign tasks."""
    console.print("\n[bold]E2E Test Setup[/bold]\n")

    # 1. Get admin JWT
    console.print("Logging in as admin...")
    jwt = get_admin_jwt(admin_password)
    headers = {"Authorization": f"Bearer {jwt}"}
    console.print("[green]Admin login successful[/green]")

    # 2. Check if test user already exists
    console.print(f"\nChecking for existing test user ({TEST_EMAIL})...")
    existing_id = ssh_query(f"SELECT id FROM users WHERE email = '{TEST_EMAIL}'")

    if existing_id:
        console.print(f"[yellow]Test user already exists: {existing_id}[/yellow]")
        if not yes and not click.confirm("Delete existing test user and recreate?"):
            raise click.ClickException("Aborted - test user already exists")

        # Cleanup existing
        console.print("Cleaning up existing test data...")
        ssh_query(f"""
            DELETE FROM session_events WHERE session_id IN
                (SELECT id FROM sessions WHERE user_id = '{existing_id}');
            DELETE FROM sessions WHERE user_id = '{existing_id}';
            DELETE FROM assignments WHERE user_id = '{existing_id}';
            DELETE FROM users WHERE id = '{existing_id}';
        """)
        console.print("[green]Existing test user deleted[/green]")

    # 3. Create test user via API
    console.print(f"\nCreating test user: {TEST_EMAIL}...")
    response = requests.post(
        f"{BASE_URL}/api/admin/users",
        headers=headers,
        json={
            "email": TEST_EMAIL,
            "name": TEST_NAME,
            "password": TEST_PASSWORD,
            "is_admin": True,
        },
    )
    if response.status_code != 201:
        raise click.ClickException(f"Failed to create user: {response.text}")

    user_id = response.json()["id"]
    console.print(f"[green]Created user: {user_id}[/green]")

    # 4. Assign tasks
    console.print("\nAssigning test tasks...")
    assignments = []
    for benchmark, tasks in BENCHMARK_TASKS.items():
        for task_id in tasks:
            assignments.append(
                {
                    "user_id": user_id,
                    "task_id": task_id,
                    "benchmark": benchmark,
                    "mode": "completion",
                }
            )

    response = requests.post(
        f"{BASE_URL}/api/admin/assignments/bulk",
        headers=headers,
        json={"assignments": assignments},
    )
    if response.status_code != 201:
        raise click.ClickException(f"Failed to assign tasks: {response.text}")

    result = response.json()
    console.print(f"[green]Assigned {result['created']} tasks[/green]")

    # 5. Generate CLI auth token
    # Note: Sessions are created on-demand when running tests via automated_runner
    console.print("\nGenerating CLI auth token...")
    code = base64.b64encode(user_id.encode()).decode()
    response = requests.post(
        f"{BASE_URL}/api/v1/cli/token",
        json={"code": code},
    )
    if response.status_code != 200:
        raise click.ClickException(f"Failed to get CLI token: {response.text}")

    token_data = response.json()

    # 6. Write CLI config
    console.print(f"Writing CLI config to {CLI_CONFIG_PATH}...")
    CLI_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Backup existing config if present
    if CLI_CONFIG_PATH.exists():
        backup_path = CLI_CONFIG_PATH.with_suffix(".json.backup")
        CLI_CONFIG_PATH.rename(backup_path)
        console.print(f"[yellow]Backed up existing config to {backup_path}[/yellow]")

    config = {
        "api_url": f"{BASE_URL}/api/v1/cli",
        "api_key": token_data["api_key"],
        "api_key_expires_at": token_data["expires_at"],
        "user_email": TEST_EMAIL,
        "user_name": TEST_NAME,
    }
    CLI_CONFIG_PATH.write_text(json.dumps(config, indent=2))
    console.print("[green]CLI config written[/green]")

    # 7. Verify CLI works (use pipx version, not local venv)
    console.print("\nVerifying CLI authentication...")
    result = subprocess.run(
        [str(HTE_CLI_PATH), "auth", "status"],
        capture_output=True,
        text=True,
    )
    if "E2E Test User" not in result.stdout:
        console.print(f"[red]CLI auth check failed: {result.stdout}[/red]")
    else:
        console.print("[green]CLI authenticated as E2E Test User[/green]")

    # Summary
    console.print("\n" + "=" * 50)
    console.print("[bold green]Setup complete![/bold green]")
    console.print(f"User ID: {user_id}")
    console.print(f"Tasks assigned: {len(assignments)}")
    console.print("\nNext steps:")
    console.print("  uv run python tests/e2e/e2e_test.py run cybergym")
    console.print("  uv run python tests/e2e/e2e_test.py run cybench")
    console.print("  ... etc")


def create_session_for_task(task_id: str) -> str | None:
    """Create a session for a task via the test API endpoint."""
    # Read CLI config for API key
    if not CLI_CONFIG_PATH.exists():
        console.print(f"[red]CLI config not found: {CLI_CONFIG_PATH}[/red]")
        return None

    config = json.loads(CLI_CONFIG_PATH.read_text())
    api_key = config.get("api_key")
    if not api_key:
        console.print("[red]No API key in CLI config[/red]")
        return None

    headers = {"Authorization": f"Bearer {api_key}"}

    # Get assignment ID for this task
    assignment_id = ssh_query(f"""
        SELECT a.id FROM assignments a
        JOIN users u ON a.user_id = u.id
        WHERE u.email = '{TEST_EMAIL}' AND a.task_id = '{task_id}'
        LIMIT 1
    """)

    if not assignment_id:
        console.print(f"[red]No assignment found for task {task_id}[/red]")
        return None

    # Create session via test endpoint
    response = requests.post(
        f"{BASE_URL}/api/v1/cli/assignments/{assignment_id}/create-session",
        headers=headers,
        timeout=30,
    )

    if response.status_code == 200:
        session_id = response.json()["session_id"]
        console.print(f"[green]Created session: {session_id[:8]}...[/green]")
        return session_id
    elif response.status_code == 409:
        # Already has an active session - that's ok
        console.print(
            f"[yellow]Active session exists: {response.json().get('detail', '')}[/yellow]"
        )
        return None
    else:
        console.print(f"[red]Failed to create session: {response.text}[/red]")
        return None


@cli.command()
@click.argument("benchmark", type=click.Choice(list(BENCHMARK_TASKS.keys())))
@click.option(
    "--task-index", "-t", default=0, type=click.IntRange(0, 1), help="Which task (0 or 1)"
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompts")
def run(benchmark: str, task_index: int, yes: bool):
    """Run E2E test for a specific benchmark (interactive)."""
    tasks = BENCHMARK_TASKS[benchmark]
    task_id = tasks[task_index]

    console.print(f"\n[bold]E2E Test: {benchmark}[/bold]")
    console.print(f"Task: {task_id} (index {task_index})\n")

    # Pre-test state
    console.print("[bold]Pre-test state:[/bold]")
    session_count = ssh_query(f"SELECT COUNT(*) FROM sessions WHERE task_id = '{task_id}'")
    console.print(f"  Existing sessions for this task: {session_count}")

    # Show instructions
    console.print(
        Panel(
            BENCHMARK_INSTRUCTIONS.get(benchmark, "No specific instructions."),
            title=f"Instructions for {benchmark}",
        )
    )

    # Launch task
    if not yes and not click.confirm("Launch task now?"):
        console.print("[yellow]Cancelled[/yellow]")
        return

    # Create session via API first
    console.print("\n[bold]Creating session via API...[/bold]")
    session_id = create_session_for_task(task_id)
    if not session_id:
        console.print("[yellow]Continuing without pre-created session...[/yellow]")

    console.print("\n[bold]Running automated test...[/bold]\n")

    # Use the automated runner for full E2E flow
    from automated_runner import run_automated_test, print_results

    test_results = run_automated_test(task_id, benchmark, timeout=600)
    print_results(test_results, f"Automated Test: {benchmark}")

    # Post-test verification
    console.print("\n[bold]Post-test verification:[/bold]")

    # Check session was created
    session_info = ssh_query(f"""
        SELECT id, status, score, client_active_seconds
        FROM sessions
        WHERE task_id = '{task_id}'
        ORDER BY created_at DESC
        LIMIT 1
    """)

    if session_info:
        parts = session_info.split("|")
        console.print(f"  Session ID: {parts[0]}")
        console.print(f"  Status: {parts[1]}")
        console.print(f"  Score: {parts[2]}")
        console.print(f"  Active seconds: {parts[3]}")

        # Check events
        session_id = parts[0]
        events = ssh_query(f"""
            SELECT event_type FROM session_events
            WHERE session_id = '{session_id}'
            ORDER BY server_timestamp
        """)
        console.print(f"  Events: {events.replace(chr(10), ', ')}")
    else:
        console.print("[yellow]  No session found[/yellow]")

    console.print("\n[green]Test complete![/green]")


@cli.command()
@click.option(
    "--admin-password",
    envvar="ADMIN_PASSWORD",
    default="test1234",
    help="Admin password for API access",
)
def verify(admin_password: str):
    """Verify all test artifacts."""
    console.print("\n[bold]Verifying E2E Test Artifacts[/bold]\n")

    # Get test user ID
    user_id = ssh_query(f"SELECT id FROM users WHERE email = '{TEST_EMAIL}'")
    if not user_id:
        raise click.ClickException(f"Test user not found: {TEST_EMAIL}")

    console.print(f"Test user: {user_id}")

    # Get admin JWT for API calls
    jwt = get_admin_jwt(admin_password)
    headers = {"Authorization": f"Bearer {jwt}"}

    # Get progress via API
    response = requests.get(f"{BASE_URL}/api/admin/progress/users", headers=headers)
    progress = response.json()
    test_progress = next((p for p in progress if p["user_id"] == user_id), None)

    if test_progress:
        console.print("\nProgress stats:")
        console.print(f"  Total tasks: {test_progress['stats']['total_tasks']}")
        console.print(f"  Completed: {test_progress['stats']['completed_tasks']}")
        console.print(f"  In progress: {test_progress['stats']['in_progress_tasks']}")
        console.print(f"  Pending: {test_progress['stats']['pending_tasks']}")

    # Export sessions
    response = requests.post(
        f"{BASE_URL}/api/admin/export",
        headers=headers,
        json={"include_completions": True, "include_skips": True},
    )
    export = response.json()

    test_sessions = [s for s in export.get("completions", []) if s["user_id"] == user_id]

    if test_sessions:
        console.print(f"\nCompleted sessions: {len(test_sessions)}")
        table = Table(title="Test Sessions")
        table.add_column("Task ID")
        table.add_column("Score")
        table.add_column("Time (s)")
        table.add_column("Answer")

        for s in test_sessions:
            table.add_row(
                s["task_id"],
                str(s["score"]),
                str(s["client_active_seconds"]),
                (s["answer"] or "")[:30] + "..."
                if s["answer"] and len(s["answer"]) > 30
                else s["answer"],
            )
        console.print(table)

    # Check eval logs on VPS
    console.print("\nChecking eval logs on VPS...")
    eval_logs = ssh_command(
        "find /opt/hte-web/data/eval_logs -name '*.eval.gz' 2>/dev/null | wc -l"
    )
    console.print(f"  Total eval logs on VPS: {eval_logs}")

    # Check local eval logs
    local_logs_dir = Path.home() / "Library" / "Application Support" / "hte-cli" / "eval_logs"
    if local_logs_dir.exists():
        local_logs = list(local_logs_dir.glob("*.eval"))
        console.print(f"  Local eval logs: {len(local_logs)}")
    else:
        console.print("  Local eval logs directory not found")

    console.print("\n[green]Verification complete![/green]")


@cli.command()
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def reset_sessions(yes: bool):
    """Reset stale in_progress sessions to abandoned status."""
    console.print("\n[bold]Resetting Stale Sessions[/bold]\n")

    # Get test user ID
    user_id = ssh_query(f"SELECT id FROM users WHERE email = '{TEST_EMAIL}'")
    if not user_id:
        raise click.ClickException(f"Test user not found: {TEST_EMAIL}")

    # Count stale sessions
    stale_count = ssh_query(f"""
        SELECT COUNT(*) FROM sessions
        WHERE user_id = '{user_id}'
        AND status = 'in_progress'
    """)

    console.print(f"Found {stale_count} in_progress sessions")

    if int(stale_count) == 0:
        console.print("[green]No stale sessions to reset[/green]")
        return

    if not yes and not click.confirm(f"Mark {stale_count} sessions as 'abandoned'?"):
        raise click.ClickException("Aborted")

    # Reset sessions
    ssh_query(f"""
        UPDATE sessions
        SET status = 'abandoned'
        WHERE user_id = '{user_id}'
        AND status = 'in_progress'
    """)

    # Also reset assignment status if needed
    ssh_query(f"""
        UPDATE assignments
        SET status = 'pending'
        WHERE user_id = '{user_id}'
        AND status = 'in_progress'
        AND id NOT IN (
            SELECT assignment_id FROM sessions
            WHERE status IN ('submitted', 'completed')
        )
    """)

    console.print("[green]Sessions reset to abandoned[/green]")


@cli.command()
def cleanup():
    """Remove test user and all data."""
    console.print("\n[bold]E2E Test Cleanup[/bold]\n")

    # Get test user ID
    user_id = ssh_query(f"SELECT id FROM users WHERE email = '{TEST_EMAIL}'")
    if not user_id:
        console.print(f"[yellow]Test user not found: {TEST_EMAIL}[/yellow]")
    else:
        console.print(f"Found test user: {user_id}")

        # Count data to delete
        sessions = ssh_query(f"SELECT COUNT(*) FROM sessions WHERE user_id = '{user_id}'")
        assignments = ssh_query(f"SELECT COUNT(*) FROM assignments WHERE user_id = '{user_id}'")
        events = ssh_query(f"""
            SELECT COUNT(*) FROM session_events WHERE session_id IN
            (SELECT id FROM sessions WHERE user_id = '{user_id}')
        """)

        console.print(f"  Sessions to delete: {sessions}")
        console.print(f"  Assignments to delete: {assignments}")
        console.print(f"  Events to delete: {events}")

        if not click.confirm("\nDelete all test data?"):
            raise click.ClickException("Aborted")

        # Delete in correct order (foreign keys)
        console.print("\nDeleting test data...")
        ssh_query(f"""
            DELETE FROM session_events WHERE session_id IN
                (SELECT id FROM sessions WHERE user_id = '{user_id}');
        """)
        ssh_query(f"DELETE FROM sessions WHERE user_id = '{user_id}';")
        ssh_query(f"DELETE FROM assignments WHERE user_id = '{user_id}';")
        ssh_query(f"DELETE FROM users WHERE id = '{user_id}';")
        console.print("[green]Test data deleted from database[/green]")

    # Restore CLI config
    backup_path = CLI_CONFIG_PATH.with_suffix(".json.backup")
    if backup_path.exists():
        console.print(f"\nRestoring CLI config from {backup_path}...")
        if CLI_CONFIG_PATH.exists():
            CLI_CONFIG_PATH.unlink()
        backup_path.rename(CLI_CONFIG_PATH)
        console.print("[green]CLI config restored[/green]")
    elif CLI_CONFIG_PATH.exists():
        # Check if it's the test config
        config = json.loads(CLI_CONFIG_PATH.read_text())
        if config.get("user_email") == TEST_EMAIL:
            console.print("\nRemoving test CLI config...")
            CLI_CONFIG_PATH.unlink()
            console.print("[green]Test CLI config removed[/green]")

    console.print("\n[green]Cleanup complete![/green]")


@cli.command()
@click.option(
    "--admin-password",
    envvar="ADMIN_PASSWORD",
    default="test1234",
    help="Admin password for API access",
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompts")
@click.option("--skip-setup", is_flag=True, help="Skip setup if already done")
@click.option("--cleanup-after", is_flag=True, help="Run cleanup after tests")
def full(admin_password: str, yes: bool, skip_setup: bool, cleanup_after: bool):
    """Run complete E2E test suite in 3 phases.

    Phase 1: Infrastructure tests (pytest, fast, no containers)
    Phase 2: Automated benchmark E2E tests (pexpect, creates completed sessions)
    Phase 3: Session verification tests (pytest, validates completed sessions)

    This is fully automated - no user interaction required.
    """
    console.print(Panel("[bold]Full E2E Test Suite - 3 Phases[/bold]", style="cyan"))
    console.print("""
[dim]Phase 1:[/dim] Infrastructure tests (pytest)
[dim]Phase 2:[/dim] Automated benchmark E2E tests (pexpect)
[dim]Phase 3:[/dim] Session verification tests (pytest)
""")

    if not yes and not click.confirm("Run full automated E2E suite?"):
        raise click.ClickException("Aborted")

    results = {"phase1": None, "phase2": {}, "phase3": None}
    tests_dir = Path(__file__).parent

    # Setup (unless skipped)
    if not skip_setup:
        console.print("\n" + "=" * 60)
        console.print("[bold cyan]SETUP: Creating test user and assignments[/bold cyan]")
        console.print("=" * 60)
        ctx = click.get_current_context()
        ctx.invoke(setup, admin_password=admin_password, yes=True)

    # Phase 1: Infrastructure tests
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]PHASE 1: Infrastructure Tests[/bold cyan]")
    console.print("=" * 60)
    console.print("[dim]Running pytest on infrastructure, imports, benchmark flows...[/dim]\n")

    phase1_result = subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            str(tests_dir / "test_infrastructure.py"),
            str(tests_dir / "test_runtime_imports.py"),
            str(tests_dir / "test_benchmark_flows.py"),
            "-v",
            "--tb=short",
        ],
        cwd=tests_dir.parent.parent,
    )
    results["phase1"] = phase1_result.returncode == 0

    if not results["phase1"]:
        console.print("\n[red bold]Phase 1 FAILED - stopping[/red bold]")
        _print_full_summary(results)
        raise SystemExit(1)

    console.print("\n[green]Phase 1 PASSED[/green]")

    # Phase 2: Automated benchmark E2E tests
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]PHASE 2: Automated Benchmark E2E Tests[/bold cyan]")
    console.print("=" * 60)
    console.print("[dim]Running automated tests for each benchmark via pexpect...[/dim]\n")

    from automated_runner import run_benchmark_test

    first_benchmark_done = False
    for benchmark in BENCHMARK_TASKS.keys():
        console.print(f"\n[bold]--- {benchmark} ---[/bold]")
        try:
            # Run task index 2 (third task, reserved for automated E2E)
            success = run_benchmark_test(benchmark, task_index=2)
            results["phase2"][benchmark] = success
            if success:
                console.print(f"[green]{benchmark}: PASSED[/green]")
            else:
                console.print(f"[red]{benchmark}: FAILED[/red]")
        except Exception as e:
            console.print(f"[red]{benchmark}: ERROR - {e}[/red]")
            results["phase2"][benchmark] = False

        # Phase 2.5: After first benchmark, run session-join tests while sessions still exist
        if not first_benchmark_done:
            first_benchmark_done = True
            console.print("\n[dim]Running session-join tests (while sessions active)...[/dim]")
            join_result = subprocess.run(
                [
                    "uv",
                    "run",
                    "pytest",
                    str(tests_dir / "test_session_lifecycle.py::TestSessionJoin"),
                    "-v",
                    "--tb=short",
                ],
                cwd=tests_dir.parent.parent,
            )
            if join_result.returncode != 0:
                console.print(
                    "[yellow]Session join tests had issues (some skips expected)[/yellow]"
                )

    phase2_passed = all(results["phase2"].values())
    if not phase2_passed:
        console.print("\n[yellow]Phase 2 had failures - continuing to Phase 3[/yellow]")

    # Phase 2.9: Create cancelled and paused sessions for edge-case tests
    console.print("\n[dim]Creating test sessions in cancelled/paused states...[/dim]")
    _create_test_session_states()

    # Phase 3: Session verification tests
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]PHASE 3: Session Verification Tests[/bold cyan]")
    console.print("=" * 60)
    console.print("[dim]Running pytest on session lifecycle and eval logs...[/dim]\n")

    phase3_result = subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            str(tests_dir / "test_session_lifecycle.py"),
            str(tests_dir / "test_eval_logs.py"),
            "-v",
            "--tb=short",
        ],
        cwd=tests_dir.parent.parent,
    )
    results["phase3"] = phase3_result.returncode == 0

    # Summary
    _print_full_summary(results)

    # Cleanup
    if cleanup_after:
        console.print("\n" + "=" * 60)
        console.print("[bold cyan]CLEANUP[/bold cyan]")
        ctx = click.get_current_context()
        ctx.invoke(cleanup)

    # Exit with appropriate code
    all_passed = results["phase1"] and phase2_passed and results["phase3"]
    if all_passed:
        console.print("\n[bold green]All phases PASSED![/bold green]")
    else:
        console.print("\n[bold red]Some phases FAILED[/bold red]")
        raise SystemExit(1)


def _print_full_summary(results: dict):
    """Print summary table of all phases."""
    console.print("\n" + "=" * 60)
    console.print("[bold]SUMMARY[/bold]")
    console.print("=" * 60)

    table = Table()
    table.add_column("Phase", style="cyan")
    table.add_column("Status")
    table.add_column("Details")

    # Phase 1
    if results["phase1"] is not None:
        status = "[green]PASSED[/green]" if results["phase1"] else "[red]FAILED[/red]"
        table.add_row("Phase 1: Infrastructure", status, "pytest infra/imports/flows")

    # Phase 2
    if results["phase2"]:
        passed = sum(1 for v in results["phase2"].values() if v)
        total = len(results["phase2"])
        status = (
            "[green]PASSED[/green]" if passed == total else f"[yellow]{passed}/{total}[/yellow]"
        )
        details = ", ".join(
            f"[green]{b}[/green]" if v else f"[red]{b}[/red]" for b, v in results["phase2"].items()
        )
        table.add_row("Phase 2: Benchmarks", status, details)

    # Phase 3
    if results["phase3"] is not None:
        status = "[green]PASSED[/green]" if results["phase3"] else "[red]FAILED[/red]"
        table.add_row("Phase 3: Verification", status, "pytest lifecycle/logs")

    console.print(table)


if __name__ == "__main__":
    cli()
