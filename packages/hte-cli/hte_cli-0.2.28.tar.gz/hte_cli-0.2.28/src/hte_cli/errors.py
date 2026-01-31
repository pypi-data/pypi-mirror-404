"""Error handling and logging for HTE-CLI.

Writes detailed errors to log file while showing friendly messages to user.
"""

import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path

from rich.console import Console

from hte_cli.config import get_log_dir

console = Console(stderr=True)


def setup_logging(debug: bool = False) -> None:
    """Set up logging to file and optionally console."""
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "hte-cli.log"

    # Rotate log if too large (>10MB)
    if log_file.exists() and log_file.stat().st_size > 10 * 1024 * 1024:
        old_log = log_dir / f"hte-cli.{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file.rename(old_log)

    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
        ],
    )

    # Also log to console if debug
    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(console_handler)


def handle_error(e: Exception, context: str = "") -> None:
    """Handle an error with user-friendly output and detailed logging."""
    logger = logging.getLogger(__name__)

    # Log full details
    logger.error(f"{context}: {e}", exc_info=True)

    # Show user-friendly message
    message = str(e)

    console.print(f"\n[red]Error: {message}[/red]")

    if context:
        console.print(f"[dim]Context: {context}[/dim]")

    # Show log file location
    log_file = get_log_dir() / "hte-cli.log"
    console.print(f"\n[dim]Details logged to: {log_file}[/dim]")
    console.print("[dim]Run with --debug for verbose output[/dim]")


def write_error_report(e: Exception, context: str = "") -> Path:
    """Write a detailed error report for potential submission."""
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = log_dir / f"error_report_{timestamp}.txt"

    with open(report_file, "w") as f:
        f.write("HTE-CLI Error Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Context: {context}\n")
        f.write(f"Error Type: {type(e).__name__}\n")
        f.write(f"Error Message: {e}\n\n")
        f.write("Traceback:\n")
        f.write(traceback.format_exc())
        f.write("\n")
        f.write("System Info:\n")
        f.write(f"  Python: {sys.version}\n")
        f.write(f"  Platform: {sys.platform}\n")

    return report_file
