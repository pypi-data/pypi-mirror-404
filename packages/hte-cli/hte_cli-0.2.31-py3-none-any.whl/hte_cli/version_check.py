"""Version checking against PyPI to ensure users are on the latest version."""

import json
import sys
import time
from pathlib import Path

import httpx
from packaging.version import Version

from hte_cli import __version__

CACHE_FILE = Path.home() / ".hte-cli" / "version_cache.json"
CACHE_TTL_SECONDS = 60 * 60  # 1 hour
PYPI_URL = "https://pypi.org/pypi/hte-cli/json"


def check_version(*, skip_check: bool = False) -> None:
    """Check if current version is outdated. Exits if outdated."""
    if skip_check:
        return

    latest = _get_latest_version()
    if latest is None:
        return  # Network error, fail open

    installed = Version(__version__)
    if installed < latest:
        sys.exit(
            f"Error: hte-cli {__version__} is outdated. "
            f"Latest: {latest}. Upgrade with: pip install -U hte-cli"
        )


def _get_latest_version() -> Version | None:
    """Fetch latest version from PyPI, with caching."""
    # Check cache first
    if CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text())
            if time.time() - cache.get("timestamp", 0) < CACHE_TTL_SECONDS:
                return Version(cache["version"])
        except (json.JSONDecodeError, KeyError):
            pass

    # Fetch from PyPI
    try:
        resp = httpx.get(PYPI_URL, timeout=2.0)
        resp.raise_for_status()
        latest = resp.json()["info"]["version"]

        # Cache result
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({"version": latest, "timestamp": time.time()}))

        return Version(latest)
    except Exception:
        return None  # Fail open on network errors
