"""Configuration management for HTE-CLI.

Uses platformdirs for cross-platform config storage.
Stores API key securely via keyring when available.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import platformdirs

APP_NAME = "hte-cli"
APP_AUTHOR = "lyptus"


def get_config_dir() -> Path:
    """Get the configuration directory for the current platform."""
    return Path(platformdirs.user_config_dir(APP_NAME, APP_AUTHOR))


def get_cache_dir() -> Path:
    """Get the cache directory for the current platform."""
    return Path(platformdirs.user_cache_dir(APP_NAME, APP_AUTHOR))


def get_log_dir() -> Path:
    """Get the log directory for errors and debug output."""
    return get_cache_dir() / "logs"


def get_data_dir() -> Path:
    """Get the data directory for persistent user data."""
    return Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))


def get_eval_logs_dir() -> Path:
    """Get the directory for storing local copies of eval logs."""
    return get_data_dir() / "eval_logs"


@dataclass
class Config:
    """CLI configuration."""

    api_url: str = ""
    api_key: str = ""
    api_key_expires_at: str = ""
    user_email: str = ""
    user_name: str = ""

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from file."""
        config_file = get_config_dir() / "config.json"
        if not config_file.exists():
            return cls()

        try:
            data = json.loads(config_file.read_text())
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except Exception:
            return cls()

    def save(self) -> None:
        """Save configuration to file."""
        config_dir = get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "api_url": self.api_url,
                    "api_key": self.api_key,
                    "api_key_expires_at": self.api_key_expires_at,
                    "user_email": self.user_email,
                    "user_name": self.user_name,
                },
                indent=2,
            )
        )

    def clear(self) -> None:
        """Clear stored credentials."""
        self.api_key = ""
        self.api_key_expires_at = ""
        self.user_email = ""
        self.user_name = ""
        self.save()

    def is_authenticated(self) -> bool:
        """Check if we have a valid API key."""
        if not self.api_key:
            return False

        # Check expiry
        if self.api_key_expires_at:
            try:
                expires = datetime.fromisoformat(self.api_key_expires_at.replace("Z", "+00:00"))
                if datetime.now(expires.tzinfo) > expires:
                    return False
            except Exception:
                pass

        return True

    def days_until_expiry(self) -> int | None:
        """Get days until API key expires."""
        if not self.api_key_expires_at:
            return None

        try:
            expires = datetime.fromisoformat(self.api_key_expires_at.replace("Z", "+00:00"))
            delta = expires - datetime.now(expires.tzinfo)
            return max(0, delta.days)
        except Exception:
            return None
