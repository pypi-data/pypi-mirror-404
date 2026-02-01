"""HTE-CLI: Human Time-to-Completion Evaluation CLI.

A standalone CLI for experts to run assigned tasks via Docker + Inspect's human_cli,
with results synced back to the web API.
"""

import os
from importlib.metadata import version

# Version from pyproject.toml - single source of truth
__version__ = version("hte-cli")

# Minimum API version required
MIN_API_VERSION = "0.1.0"

# API URL - configurable via HTE_API_URL env var for custom deployments
# Default points to production deployment
_DEFAULT_API_URL = "https://cyber-task-horizons.com/api/v1/cli"
API_BASE_URL = os.environ.get("HTE_API_URL", _DEFAULT_API_URL)


def main():
    """Entry point for hte-cli command."""
    import os

    from hte_cli.cli import cli
    from hte_cli.version_check import check_version

    skip = os.environ.get("HTE_SKIP_VERSION_CHECK", "").lower() in ("1", "true", "yes")
    check_version(skip_check=skip)

    cli()
