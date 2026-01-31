#!/usr/bin/env python3
"""
Verify Docker image has all required dependencies before deploying.

This script builds the backend Docker image locally and runs import tests
inside the container to catch missing dependencies BEFORE deploying.

Usage:
    uv run python tests/e2e/verify_docker_deps.py
"""

import subprocess
import sys

from rich.console import Console
from rich.table import Table

console = Console()

# Modules that must be importable in the backend container
REQUIRED_IMPORTS = [
    # Core app
    "from app.main import app",
    # Human eval datasets (triggers inspect_ai imports)
    "from human_ttc_eval.datasets import HUMAN_REGISTRY",
    # LLM utils
    "from human_ttc_eval.llm_utils import LLMClient, LLMConfig",
    # Config
    "from human_ttc_eval.config import PROJECT_ROOT",
    # All benchmark adapters
    "from human_ttc_eval.datasets.cybench.cybench_human import CybenchHuman",
    "from human_ttc_eval.datasets.cybergym.cybergym_human import CyberGymHuman",
    "from human_ttc_eval.datasets.cvebench.cvebench_human import CVEBenchHuman",
    "from human_ttc_eval.datasets.intercode_ctf.intercode_ctf_human import InterCodeCTFHuman",
    "from human_ttc_eval.datasets.nyuctf.nyuctf_human import NyuctfHuman",
    "from human_ttc_eval.datasets.cybashbench.cybashbench_human import CyBashBenchHuman",
]


def build_image() -> bool:
    """Build the backend Docker image."""
    console.print("\n[bold]Building backend Docker image...[/bold]\n")

    result = subprocess.run(
        [
            "docker",
            "build",
            "--no-cache",
            "-f",
            "web/backend/Dockerfile",
            "-t",
            "hte-backend-test",
            ".",
        ],
        capture_output=True,
        text=True,
        timeout=600,  # 10 minutes
    )

    if result.returncode != 0:
        console.print(f"[red]Build failed:[/red]\n{result.stderr}")
        return False

    console.print("[green]Build successful[/green]")
    return True


def test_import(import_statement: str) -> tuple[bool, str]:
    """Test a single import in the container."""
    result = subprocess.run(
        ["docker", "run", "--rm", "hte-backend-test", "python", "-c", import_statement],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode == 0:
        return True, ""
    else:
        return False, result.stderr.strip().split("\n")[-1]  # Last line of error


def run_import_tests() -> bool:
    """Run all import tests in the container."""
    console.print("\n[bold]Testing imports in container...[/bold]\n")

    table = Table(title="Import Tests")
    table.add_column("Import", style="cyan", max_width=60)
    table.add_column("Status")
    table.add_column("Error", max_width=40)

    all_passed = True
    for import_stmt in REQUIRED_IMPORTS:
        passed, error = test_import(import_stmt)

        if passed:
            table.add_row(import_stmt[:60], "[green]PASS[/green]", "")
        else:
            table.add_row(import_stmt[:60], "[red]FAIL[/red]", error[:40])
            all_passed = False

    console.print(table)

    if all_passed:
        console.print("\n[bold green]All imports passed![/bold green]")
    else:
        console.print("\n[bold red]Some imports failed - DO NOT DEPLOY[/bold red]")

    return all_passed


def test_uvicorn_startup() -> bool:
    """Test that uvicorn can start the app."""
    console.print("\n[bold]Testing uvicorn startup...[/bold]\n")

    # Start container, wait for startup, then kill
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-d",
            "--name",
            "hte-test",
            "hte-backend-test",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        console.print(f"[red]Failed to start container:[/red] {result.stderr}")
        return False

    import time

    time.sleep(5)

    # Get logs
    logs_result = subprocess.run(
        ["docker", "logs", "hte-test"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    # Stop container
    subprocess.run(["docker", "stop", "hte-test"], capture_output=True, timeout=10)

    logs = logs_result.stdout + logs_result.stderr

    if "Application startup complete" in logs:
        console.print("[green]Uvicorn started successfully[/green]")
        return True
    elif "Error" in logs or "error" in logs.lower():
        console.print(f"[red]Startup failed:[/red]\n{logs}")
        return False
    else:
        console.print(f"[yellow]Unclear status:[/yellow]\n{logs}")
        return False


def main():
    console.print("[bold]Pre-Deploy Dependency Verification[/bold]")
    console.print("=" * 50)

    # Build image
    if not build_image():
        sys.exit(1)

    # Test imports
    if not run_import_tests():
        sys.exit(1)

    # Test uvicorn
    if not test_uvicorn_startup():
        sys.exit(1)

    console.print("\n[bold green]All checks passed - safe to deploy![/bold green]")


if __name__ == "__main__":
    main()
