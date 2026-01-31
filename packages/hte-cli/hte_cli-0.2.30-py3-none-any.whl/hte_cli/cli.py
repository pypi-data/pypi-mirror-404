"""CLI commands for hte-cli.

Uses Click for command parsing and Rich for pretty output.
"""

import os
import sys
import webbrowser

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from hte_cli import __version__, API_BASE_URL
from hte_cli.config import Config
from hte_cli.api_client import APIClient, APIError

console = Console()

# Support email per spec
SUPPORT_EMAIL = "jacktpayne51@gmail.com"


@click.group()
@click.version_option(__version__, prog_name="hte-cli")
@click.pass_context
def cli(ctx):
    """Human Time-to-Completion Evaluation CLI.

    Run assigned cybersecurity tasks via Docker and sync results.
    """
    ctx.ensure_object(dict)
    ctx.obj["config"] = Config.load()


# =============================================================================
# Auth Commands
# =============================================================================


@cli.group()
def auth():
    """Authentication commands."""
    pass


@auth.command("login")
@click.pass_context
def auth_login(ctx):
    """Log in via browser to get an API key."""
    config: Config = ctx.obj["config"]

    if config.is_authenticated():
        days = config.days_until_expiry()
        console.print(f"[green]Already logged in as {config.user_email}[/green]")
        if days is not None:
            console.print(f"API key expires in {days} days")
        if not click.confirm("Log in again?"):
            return

    # Show login URL
    login_url = f"{API_BASE_URL.replace('/api/v1/cli', '')}/cli/auth"
    console.print()
    console.print(
        Panel(
            f"[bold]Visit this URL to log in:[/bold]\n\n{login_url}",
            title="Login",
        )
    )
    console.print()

    # Try to open browser
    try:
        webbrowser.open(login_url)
        console.print("[dim]Browser opened. Complete login in browser.[/dim]")
    except Exception:
        console.print("[dim]Open the URL manually in your browser.[/dim]")

    console.print()

    # Get code from user
    code = click.prompt("Enter the code from the browser")

    # Exchange code for API key
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Authenticating...", total=None)

        try:
            api = APIClient(config)
            result = api.exchange_code_for_token(code)

            config.api_key = result["api_key"]
            config.api_key_expires_at = result["expires_at"]
            config.user_email = result["user_email"]
            config.user_name = result["user_name"]
            config.api_url = API_BASE_URL
            config.save()

        except APIError as e:
            console.print(f"[red]Login failed: {e}[/red]")
            sys.exit(1)

    console.print()
    console.print(f"[green]Logged in as {config.user_name} ({config.user_email})[/green]")
    days = config.days_until_expiry()
    if days is not None:
        console.print(f"API key expires in {days} days")


@auth.command("logout")
@click.pass_context
def auth_logout(ctx):
    """Clear stored credentials."""
    config: Config = ctx.obj["config"]
    config.clear()
    console.print("[green]Logged out successfully[/green]")


@auth.command("status")
@click.pass_context
def auth_status(ctx):
    """Show current authentication status."""
    config: Config = ctx.obj["config"]

    if not config.is_authenticated():
        console.print("[yellow]Not logged in[/yellow]")
        console.print("Run: hte-cli auth login")
        return

    console.print(f"[green]Logged in as:[/green] {config.user_name}")
    console.print(f"[green]Email:[/green] {config.user_email}")

    days = config.days_until_expiry()
    if days is not None:
        if days <= 7:
            console.print(f"[yellow]API key expires in {days} days[/yellow]")
        else:
            console.print(f"API key expires in {days} days")


# =============================================================================
# Session Commands (New flow: session join <session_id>)
# =============================================================================


@cli.group()
def session():
    """Session management commands."""
    pass


@session.command("join")
@click.argument("session_id")
@click.option("--force-setup", is_flag=True, help="Re-run setup even if reconnecting")
@click.pass_context
def session_join(ctx, session_id: str, force_setup: bool):
    """Join an existing session by ID.

    This is the primary way to start working on a task:
    1. Start the task from the web UI (creates session)
    2. Run this command with the session ID shown in the web UI
    3. The environment will be set up and the timer will start
    """
    config: Config = ctx.obj["config"]

    if not config.is_authenticated():
        console.print("[red]Not logged in. Run: hte-cli auth login[/red]")
        sys.exit(1)

    # Check Docker is running before we start (with retry prompt)
    # In non-interactive mode (CI/automation), fail immediately instead of prompting
    non_interactive = os.environ.get("HTE_NON_INTERACTIVE", "").lower() in ("1", "true", "yes")

    while True:
        docker_ok, docker_error = _check_docker()
        if docker_ok:
            console.print("[dim]✓ Docker running[/dim]")
            break
        console.print(f"[red]{docker_error}[/red]")
        if non_interactive:
            console.print("[dim]Non-interactive mode - exiting[/dim]")
            sys.exit(1)
        console.print()
        if not click.confirm("Start Docker and retry?", default=True):
            sys.exit(1)
        console.print("[dim]Checking Docker again...[/dim]")

    api = APIClient(config)

    # Step 1: Join session
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Joining session...", total=None)

        try:
            session_info = api.join_session(session_id)
        except APIError as e:
            if "Invalid session ID format" in str(e):
                console.print(f"[red]{e}[/red]")
            elif e.status_code == 404:
                console.print("[red]Session not found. Check the session ID and try again.[/red]")
            elif e.status_code == 400 and "paused" in str(e).lower():
                console.print(
                    "[yellow]Session is paused. Please resume from the web UI first.[/yellow]"
                )
            else:
                console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

    # Check if reconnecting (session already in_progress)
    is_reconnect = session_info.get("status") == "in_progress"

    # Always run setup on reconnect - previous attempt may have failed
    # (e.g., image pull failed, Docker wasn't running, etc.)
    if is_reconnect:
        force_setup = True
        console.print("[yellow]Reconnecting to existing session (re-running setup)...[/yellow]")
        console.print()

    console.print(
        Panel(
            f"[bold]Task:[/bold] {session_info['task_id']}\n"
            f"[bold]Benchmark:[/bold] {session_info['benchmark']}\n"
            f"[bold]Mode:[/bold] {session_info['mode']}",
            title="Session Joined",
        )
    )
    console.print()

    # Import runner components
    import time
    from hte_cli.events import EventStreamer
    from hte_cli.runner import TaskRunner
    from hte_cli.image_utils import (
        extract_images_from_compose,
        extract_image_platforms_from_compose,
        pull_image_with_progress,
        check_image_architecture_matches_host,
        fix_image_architecture,
        get_host_docker_platform,
        is_running_in_linux_vm_on_arm,
    )

    # Create event streamer
    events = EventStreamer(api, session_id)

    # Step 2: Download task files and compose (skip if reconnecting without force)
    files_zip = None
    compose_yaml = None

    if not is_reconnect or force_setup:
        console.print("[bold]Step 1:[/bold] Downloading task resources...")

        with console.status("[dim]Fetching task files...[/dim]"):
            try:
                files_zip = api.get_session_files(session_id)
                console.print("  [green]✓[/green] Task files downloaded")
            except APIError:
                console.print("  [dim]○ No task files (optional)[/dim]")
                files_zip = None

        with console.status("[dim]Fetching compose configuration...[/dim]"):
            try:
                compose_yaml = api.get_session_compose(session_id)
                console.print("  [green]✓[/green] Docker compose downloaded")
            except APIError:
                console.print("  [dim]○ No compose file (optional)[/dim]")
                compose_yaml = None

        console.print()

    # Validate compose for sandbox-required benchmarks
    benchmark = session_info.get("benchmark", "").lower()
    SANDBOX_REQUIRED_BENCHMARKS = {"cybench", "intercode-ctf", "cvebench", "cybergym", "nyuctf"}

    # NYU CTF requires a shared Docker network for agent/game-server communication
    if benchmark == "nyuctf":
        _ensure_nyuctf_network()

    if benchmark in SANDBOX_REQUIRED_BENCHMARKS and not compose_yaml and not is_reconnect:
        console.print(
            f"[red]Error: {benchmark} requires a Docker sandbox but no compose file was found.[/red]"
        )
        console.print()
        console.print(f"Please contact support: {SUPPORT_EMAIL}")
        sys.exit(1)

    # Build assignment dict for runner compatibility
    assignment = {
        "assignment_id": session_info.get("assignment_id"),
        "session_id": session_id,
        "task_id": session_info["task_id"],
        "benchmark": session_info["benchmark"],
        "mode": session_info["mode"],
        "time_cap_seconds": session_info.get("time_cap_seconds"),
        "task": {
            "instructions": session_info.get("instructions", ""),
            "metadata": session_info.get("metadata", {}),
            "target": session_info.get("target", ""),
            "scorer_type": session_info.get("scorer_type"),
            "intermediate_scoring": session_info.get("intermediate_scoring", False),
        },
    }

    # Step 3: Run setup (skip if reconnecting without force)
    setup_start_time = time.monotonic()
    images = []
    pulled_images = []
    cached_images = []
    failed_images = []

    if not is_reconnect or force_setup:
        # Extract images and their platforms from compose
        image_platforms = {}
        if compose_yaml:
            images = extract_images_from_compose(compose_yaml)
            image_platforms = extract_image_platforms_from_compose(compose_yaml)

        # Send setup_started event (includes CLI version for debugging)
        events.setup_started(images=images, cli_version=__version__)

        # Pull images if we have any
        if images:
            from hte_cli.image_utils import check_image_exists_locally

            # Detect host architecture for smart image handling
            is_linux_arm = is_running_in_linux_vm_on_arm()
            host_platform = get_host_docker_platform()

            if is_linux_arm:
                console.print(
                    f"[yellow]![/yellow] Detected [bold]Linux ARM64[/bold] environment"
                )
                console.print(
                    f"  [dim]Will verify cached images match host architecture ({host_platform})[/dim]"
                )
                console.print(
                    f"  [dim]Mismatched images will be automatically re-pulled[/dim]"
                )
                console.print()

            console.print(f"[bold]Step 2:[/bold] Pulling {len(images)} Docker image(s)...")
            pull_start = time.monotonic()
            pull_errors = {}
            x86_images_on_arm = []  # Track x86 images that need QEMU

            for img in images:
                short_name = img.split("/")[-1][:40]
                platform = image_platforms.get(img)

                # Check if already cached
                if check_image_exists_locally(img):
                    # Verify architecture matches host (important for Linux ARM64)
                    matches, image_arch, host_arch = check_image_architecture_matches_host(img)

                    if matches:
                        # Show architecture info on Linux ARM64 for transparency
                        if is_linux_arm and image_arch:
                            console.print(
                                f"  [green]✓[/green] {short_name} [dim](cached, arch: {image_arch})[/dim]"
                            )
                        else:
                            console.print(f"  [green]✓[/green] {short_name} [dim](cached)[/dim]")
                        cached_images.append(img)
                        continue
                    else:
                        # Architecture mismatch detected - this is the key fix for Linux ARM64
                        console.print(
                            f"  [yellow]⚠[/yellow] {short_name} [yellow]architecture mismatch![/yellow]"
                        )
                        console.print(
                            f"      [dim]Cached image: {image_arch} | Host: {host_arch}[/dim]"
                        )
                        console.print(
                            f"      [dim]Removing cached image and re-pulling correct architecture...[/dim]"
                        )

                        needed_fix, fix_msg = fix_image_architecture(img)
                        if needed_fix:
                            console.print(
                                f"  [green]✓[/green] {short_name} [green]fixed![/green] [dim]({fix_msg})[/dim]"
                            )
                            pulled_images.append(img)
                            continue
                        elif "failed to re-pull" in fix_msg:
                            # No ARM variant available - this is an x86-only image
                            # Re-pull the amd64 version and warn about QEMU
                            console.print(
                                f"      [dim]No ARM variant available - re-pulling x86 version...[/dim]"
                            )
                            success = pull_image_with_progress(img)
                            if success:
                                console.print(
                                    f"  [yellow]![/yellow] {short_name} [dim](x86-only image, needs QEMU)[/dim]"
                                )
                                x86_images_on_arm.append(img)
                                pulled_images.append(img)
                                continue
                            else:
                                console.print(f"  [red]✗[/red] {short_name} [dim](failed to pull)[/dim]")
                                failed_images.append(img)
                                pull_errors[img] = "failed to pull x86 fallback"
                                continue
                        else:
                            console.print(f"  [red]✗[/red] {short_name} [dim]({fix_msg})[/dim]")
                            failed_images.append(img)
                            pull_errors[img] = fix_msg
                            continue

                # Need to pull - show progress
                last_status = ["connecting..."]
                last_error = [""]

                # Use platform from compose if specified, otherwise let Docker decide
                # (Docker will prefer native arch for multi-arch images, or pull what's available)
                pull_platform = platform

                with console.status(
                    f"[yellow]↓[/yellow] {short_name} [dim]connecting...[/dim]"
                ) as status:

                    def show_progress(image: str, line: str):
                        # Show docker output directly - includes MB progress from PTY
                        # Lines look like: "abc123: Downloading  360.9MB/4.075GB"
                        if ": " in line:
                            parts = line.split(": ", 1)
                            if len(parts) == 2:
                                layer_id = parts[0][-8:]
                                layer_status = parts[1][:45]
                                display = f"{layer_id}: {layer_status}"
                                if display != last_status[0]:
                                    last_status[0] = display
                                    status.update(
                                        f"[yellow]↓[/yellow] {short_name} [dim]{display}[/dim]"
                                    )
                        # Capture error messages
                        if "error" in line.lower() or "denied" in line.lower():
                            last_error[0] = line

                    success = pull_image_with_progress(
                        img, platform=pull_platform, on_progress=show_progress
                    )

                if success:
                    # On Linux ARM64, verify pulled image architecture
                    if is_linux_arm:
                        from hte_cli.image_utils import get_image_architecture
                        pulled_arch = get_image_architecture(img)

                        if pulled_arch == "arm64":
                            console.print(
                                f"  [green]✓[/green] {short_name} [dim](downloaded, arch: arm64)[/dim]"
                            )
                        elif pulled_arch == "amd64":
                            # x86 image on ARM host - needs QEMU emulation
                            console.print(
                                f"  [yellow]![/yellow] {short_name} [dim](downloaded, arch: amd64)[/dim]"
                            )
                            console.print(
                                f"      [yellow]This is an x86 image - requires QEMU emulation on ARM[/yellow]"
                            )
                            x86_images_on_arm.append(img)
                        else:
                            console.print(
                                f"  [green]✓[/green] {short_name} [dim](downloaded)[/dim]"
                            )
                    else:
                        console.print(f"  [green]✓[/green] {short_name} [dim](downloaded)[/dim]")
                    pulled_images.append(img)
                else:
                    platform_note = f" (platform: {pull_platform})" if pull_platform else ""
                    console.print(f"  [red]✗[/red] {short_name}{platform_note} [dim](failed)[/dim]")
                    if last_error[0]:
                        console.print(f"      [dim]{last_error[0][:60]}[/dim]")
                        pull_errors[img] = last_error[0]
                    failed_images.append(img)

            pull_duration = time.monotonic() - pull_start
            events.image_pull_completed(
                duration_seconds=pull_duration,
                pulled=pulled_images,
                cached=cached_images,
                failed=failed_images,
            )
            console.print()

            # Warn about x86 images on ARM that need QEMU
            if x86_images_on_arm:
                console.print(
                    f"[yellow]⚠ Warning:[/yellow] {len(x86_images_on_arm)} x86 image(s) detected on ARM host"
                )
                console.print(
                    "  These require QEMU emulation. If container fails to start, run:"
                )
                console.print(
                    "  [bold]docker run --privileged --rm tonistiigi/binfmt --install all[/bold]"
                )
                console.print()

            # Fail fast if any required image couldn't be pulled
            if failed_images:
                console.print(
                    f"[red]Error: Failed to pull {len(failed_images)} required Docker image(s).[/red]"
                )
                console.print()
                console.print("[yellow]Troubleshooting:[/yellow]")
                console.print("  1. Check Docker is running: docker info")

                # Architecture-specific advice
                if is_linux_arm:
                    console.print(f"  2. You're on Linux ARM64 - try: docker pull <image> --platform linux/arm64")
                    console.print("  3. For x86-only images, enable QEMU: docker run --privileged --rm tonistiigi/binfmt --install all")
                else:
                    console.print("  2. Try manual pull: docker pull <image>")

                console.print("  4. Check network connectivity")
                console.print()
                console.print("Session remains active - you can retry with: hte-cli session join " + session_id)
                sys.exit(1)

        # Send setup_completed - THIS STARTS THE TIMER ON SERVER
        total_setup = time.monotonic() - setup_start_time
        events.setup_completed(total_seconds=total_setup)
        console.print("[green]Environment ready! Timer started.[/green]")
        console.print()
    else:
        # Reconnecting - compose should already be running
        console.print("[dim]Skipping setup (use --force-setup to re-run)[/dim]")
        console.print()

    # Check if session was cancelled during setup
    try:
        updated_session = api.join_session(session_id)
        if updated_session.get("status") == "cancelled":
            console.print("[yellow]Session was cancelled. Exiting.[/yellow]")
            sys.exit(0)
    except APIError:
        pass  # Continue if we can't check - server might be temporarily unavailable

    # Step 4: Show instructions
    if session_info.get("instructions"):
        console.print(Panel(session_info["instructions"], title="Task Instructions"))
        console.print()

    # Step 3: Run the task using TaskRunner
    step_num = (
        "3"
        if (not is_reconnect or force_setup) and images
        else "2"
        if (not is_reconnect or force_setup)
        else "1"
    )
    console.print(f"[bold]Step {step_num}:[/bold] Starting task environment...")
    console.print("[dim]Launching Docker containers...[/dim]")
    console.print()

    events.docker_started()

    runner = TaskRunner()
    eval_log_bytes = None
    try:
        result = runner.run_from_assignment(
            assignment=assignment,
            compose_yaml=compose_yaml,
            files_zip=files_zip,
        )
        # Read eval log before cleanup
        if result.eval_log_path and result.eval_log_path.exists():
            eval_log_bytes = result.eval_log_path.read_bytes()
    except KeyboardInterrupt:
        events.docker_stopped(exit_code=130)
        console.print()
        console.print(
            "[yellow]Interrupted. Session remains active - you can reconnect later.[/yellow]"
        )
        sys.exit(0)
    except Exception as e:
        events.docker_stopped(exit_code=1)
        console.print(f"[red]Task execution failed: {e}[/red]")
        sys.exit(1)
    finally:
        runner.cleanup()

    events.docker_stopped(exit_code=0)

    # Step 6: Upload result
    if result and result.answer:
        events.session_completed(
            elapsed_seconds=result.time_seconds,
            answer=result.answer,
        )

        # Extract agent_id from task files for CyberGym post-hoc verification
        agent_id = None
        if files_zip:
            try:
                from io import BytesIO
                from zipfile import ZipFile

                with ZipFile(BytesIO(files_zip)) as zf:
                    if "difficulty_levels.json" in zf.namelist():
                        with zf.open("difficulty_levels.json") as f:
                            import json

                            difficulty_info = json.load(f)
                            agent_id = difficulty_info.get("agent_id")
            except Exception:
                pass  # Not a CyberGym task or malformed zip

        console.print()
        console.print("[green]Task completed![/green]")
        console.print(f"Answer: {result.answer}")
        console.print(f"Time: {result.time_seconds:.1f}s")

        # Track upload size and timing
        upload_size_bytes = len(eval_log_bytes) if eval_log_bytes else 0
        upload_size_kb = upload_size_bytes / 1024

        events.upload_started(size_bytes=upload_size_bytes)
        upload_start_time = time.monotonic()

        # Upload to server
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            size_str = f" ({upload_size_kb:.0f} KB)" if upload_size_kb > 0 else ""
            progress.add_task(f"Uploading result{size_str}...", total=None)
            try:
                upload_result = api.upload_result(
                    session_id=session_id,
                    answer=result.answer or "",
                    client_active_seconds=result.time_seconds,
                    eval_log_bytes=eval_log_bytes,
                    score=result.score,
                    score_binarized=result.score_binarized,
                    agent_id=agent_id,
                )
            except APIError as e:
                console.print(f"[red]Failed to upload result: {e}[/red]")
                sys.exit(1)

        # Record upload completion
        upload_duration = time.monotonic() - upload_start_time
        events.upload_completed(duration_seconds=upload_duration, size_bytes=upload_size_bytes)

        if upload_result.get("score") is not None:
            console.print(f"Score: {upload_result['score']}")

        console.print()
        console.print("[green]Done! Return to the web UI to see your results.[/green]")


# =============================================================================
# Tasks Commands (DEPRECATED - use 'session join' instead)
# =============================================================================


@cli.group()
def tasks():
    """Task commands (deprecated - use 'session join' instead)."""
    pass


@tasks.command("list")
@click.pass_context
def tasks_list(ctx):
    """List pending task assignments."""
    config: Config = ctx.obj["config"]

    if not config.is_authenticated():
        console.print("[red]Not logged in. Run: hte-cli auth login[/red]")
        sys.exit(1)

    api = APIClient(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Fetching assignments...", total=None)

        try:
            assignments = api.get_assignments()
        except APIError as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

    if not assignments:
        console.print("[yellow]No pending assignments[/yellow]")
        return

    table = Table(title="Pending Assignments")
    table.add_column("Task ID", style="cyan")
    table.add_column("Benchmark", style="green")
    table.add_column("Mode")
    table.add_column("Priority", justify="right")
    table.add_column("Status")

    for a in assignments:
        # Determine status and style based on session state
        session_status = a.get("session_status")
        if session_status == "paused":
            status = "Paused"
            status_style = "magenta"
        elif a.get("session_id"):
            status = "In Progress"
            status_style = "yellow"
        else:
            status = "Pending"
            status_style = ""

        table.add_row(
            a["task_id"],
            a["benchmark"],
            a["mode"],
            str(a["priority"]),
            f"[{status_style}]{status}[/{status_style}]" if status_style else status,
        )

    console.print(table)
    console.print()
    console.print("Run: [bold]hte-cli tasks run[/bold] to start the highest priority task")


@tasks.command("run")
@click.argument("task_id", required=False)
@click.pass_context
def tasks_run(ctx, task_id: str | None):
    """[DEPRECATED] Run a task - use 'session join' instead."""
    console.print()
    console.print("[red]This command is deprecated.[/red]")
    console.print()
    console.print("The new workflow is:")
    console.print("  1. Start the task from the web UI: https://cyber-task-horizons.com")
    console.print("  2. Run the command shown: [bold]hte-cli session join <session_id>[/bold]")
    console.print()
    console.print("This ensures accurate timing by starting the timer only when")
    console.print("the environment is ready, not including Docker setup time.")
    console.print()
    sys.exit(1)


@tasks.command("pull-images")
@click.option("--count", "-n", default=5, help="Number of upcoming tasks to pull images for")
@click.pass_context
def tasks_pull_images(ctx, count: int):
    """Pre-pull Docker images for upcoming tasks."""
    config: Config = ctx.obj["config"]

    if not config.is_authenticated():
        console.print("[red]Not logged in. Run: hte-cli auth login[/red]")
        sys.exit(1)

    # Check Docker and Compose version
    docker_ok, docker_error = _check_docker()
    if not docker_ok:
        console.print(f"[red]{docker_error}[/red]")
        sys.exit(1)

    api = APIClient(config)

    # Get assignments
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Fetching assignments...", total=None)
        try:
            assignments = api.get_assignments()
        except APIError as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

    if not assignments:
        console.print("[yellow]No pending assignments[/yellow]")
        return

    # Take first N
    to_pull = assignments[:count]

    console.print(f"Pulling images for {len(to_pull)} task(s)...")
    console.print()

    # TODO: Download compose files and extract image names, then pull
    console.print("[yellow]Image pulling not yet implemented.[/yellow]")


@cli.command("diagnose")
def diagnose_cmd():
    """
    Diagnose Docker and architecture setup.

    Checks Docker installation, architecture detection, and image compatibility.
    Useful for troubleshooting before running tasks.
    """
    import subprocess
    import sys as system_module
    from hte_cli.image_utils import (
        get_host_architecture,
        get_host_docker_platform,
        is_running_in_linux_vm_on_arm,
        get_image_architecture,
        check_image_exists_locally,
    )

    console.print("[bold]HTE-CLI Diagnostics[/bold]")
    console.print("=" * 50)
    console.print()

    # CLI version
    console.print(f"[bold]CLI Version:[/bold] {__version__}")
    console.print()

    # Platform info
    console.print("[bold]Platform:[/bold]")
    host_arch = get_host_architecture()
    host_platform = get_host_docker_platform()
    is_linux_arm = is_running_in_linux_vm_on_arm()

    console.print(f"  OS: {system_module.platform}")
    console.print(f"  Architecture: {host_arch}")
    console.print(f"  Docker platform: {host_platform or 'unknown'}")

    if is_linux_arm:
        console.print()
        console.print("[yellow]⚠ Linux ARM64 detected![/yellow]")
        console.print("  This environment may have architecture compatibility issues.")
        console.print("  The CLI will automatically handle multi-arch images.")
        console.print("  For x86-only images (CTF challenges), QEMU emulation is required.")
    console.print()

    # Docker checks
    console.print("[bold]Docker:[/bold]")

    # Check Docker installed
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            console.print(f"  [green]✓[/green] Docker: {result.stdout.strip()}")
        else:
            console.print("  [red]✗[/red] Docker not working")
    except Exception as e:
        console.print(f"  [red]✗[/red] Docker not found: {e}")

    # Check Docker daemon
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            console.print("  [green]✓[/green] Docker daemon running")
        else:
            console.print("  [red]✗[/red] Docker daemon not running")
    except Exception:
        console.print("  [red]✗[/red] Cannot connect to Docker daemon")

    # Check Compose version
    try:
        result = subprocess.run(
            ["docker", "compose", "version", "--short"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            console.print(f"  [green]✓[/green] Docker Compose: {version}")
        else:
            console.print("  [yellow]![/yellow] Docker Compose not available")
    except Exception:
        console.print("  [yellow]![/yellow] Docker Compose not found")

    console.print()

    # Test images
    console.print("[bold]Image Architecture Test:[/bold]")
    test_images = [
        ("python:3.12-slim", "multi-arch (nl2bash/cybashbench)"),
        ("cybench/cybench:latest", "x86-only (cybench/cybergym)"),
    ]

    for image, description in test_images:
        if check_image_exists_locally(image):
            arch = get_image_architecture(image)
            if arch:
                if is_linux_arm and arch == "amd64":
                    console.print(
                        f"  [yellow]![/yellow] {image}: {arch} [dim](x86 on ARM - needs QEMU)[/dim]"
                    )
                else:
                    console.print(f"  [green]✓[/green] {image}: {arch}")
            else:
                console.print(f"  [dim]?[/dim] {image}: cached (unknown arch)")
        else:
            console.print(f"  [dim]-[/dim] {image}: not cached - {description}")

    console.print()

    # QEMU check (for Linux ARM64)
    if is_linux_arm:
        console.print("[bold]QEMU Emulation:[/bold]")
        try:
            # Check if binfmt is set up for x86
            result = subprocess.run(
                ["docker", "run", "--rm", "--platform", "linux/amd64", "alpine", "uname", "-m"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and "x86_64" in result.stdout:
                console.print("  [green]✓[/green] QEMU x86 emulation working")
            else:
                console.print("  [red]✗[/red] QEMU x86 emulation NOT working")
                console.print()
                console.print("  [yellow]To enable QEMU emulation, run:[/yellow]")
                console.print("  [bold]docker run --privileged --rm tonistiigi/binfmt --install all[/bold]")
        except subprocess.TimeoutExpired:
            console.print("  [yellow]![/yellow] QEMU test timed out")
        except Exception as e:
            console.print(f"  [red]✗[/red] QEMU test failed: {e}")
        console.print()

    console.print("[bold]Recommendation:[/bold]")
    if is_linux_arm:
        console.print("  For nl2bash/cybashbench: Should work with native ARM images")
        console.print("  For CTF challenges (cybench, nyuctf, etc.): Requires QEMU emulation")
    else:
        console.print("  [green]✓[/green] Standard platform - all benchmarks should work")

    console.print()
    console.print("[dim]Run 'hte-cli session join <id>' to test with a real task[/dim]")


# =============================================================================
# Helper Functions
# =============================================================================


def _check_docker() -> tuple[bool, str | None]:
    """Check if Docker is installed, running, and has required Compose version.

    Returns:
        (success, error_message) - success is True if all checks pass,
        otherwise error_message explains what's wrong.
    """
    import subprocess
    import re

    # Required versions (must match inspect_ai/util/_sandbox/docker/prereqs.py)
    REQUIRED_COMPOSE_VERSION = (2, 21, 0)

    # Check Docker is running
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            return False, "Docker is not running. Start Docker (Docker Desktop, colima, or dockerd)."
    except FileNotFoundError:
        return False, "Docker is not installed. Install from https://docs.docker.com/get-docker/"
    except Exception as e:
        return False, f"Error checking Docker: {e}"

    # Check Docker Compose version
    # Use --short flag which works on older versions (unlike --format json)
    try:
        result = subprocess.run(
            ["docker", "compose", "version", "--short"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            # Compose not available as plugin
            return False, (
                "Docker Compose v2 is not installed.\n"
                "Install: https://docs.docker.com/compose/install/"
            )

        # Parse version string like "v2.21.0" or "2.21.0"
        version_str = result.stdout.strip().lstrip("v")
        match = re.match(r"(\d+)\.(\d+)\.(\d+)", version_str)
        if not match:
            return False, f"Could not parse Docker Compose version: {version_str}"

        version = tuple(int(x) for x in match.groups())
        if version < REQUIRED_COMPOSE_VERSION:
            required_str = ".".join(str(x) for x in REQUIRED_COMPOSE_VERSION)
            return False, (
                f"Docker Compose version {version_str} is too old (need >= {required_str}).\n\n"
                "Update options:\n"
                "  - Update Docker Desktop to 4.25+ (macOS/Windows)\n"
                "  - Update compose plugin: sudo apt-get update && sudo apt-get install docker-compose-plugin (Linux)"
            )

    except FileNotFoundError:
        return False, (
            "Docker Compose v2 is not installed.\n"
            "Install: https://docs.docker.com/compose/install/"
        )
    except Exception as e:
        return False, f"Error checking Docker Compose version: {e}"

    return True, None


def _ensure_nyuctf_network() -> None:
    """Ensure the ctfnet Docker network exists for NYU CTF challenges.

    NYU CTF tasks use a shared Docker network ('ctfnet') for communication
    between the agent container and game-server container. This network must
    exist before docker compose up is called, since it's declared as external.
    """
    import subprocess

    NETWORK_NAME = "ctfnet"

    try:
        # Check if network exists
        result = subprocess.run(
            ["docker", "network", "inspect", NETWORK_NAME],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return  # Network exists

        # Create the network
        subprocess.run(
            ["docker", "network", "create", NETWORK_NAME],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except subprocess.CalledProcessError:
        pass  # Network creation failed, will error later with clearer message
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # Docker not available, will error later


if __name__ == "__main__":
    cli()
