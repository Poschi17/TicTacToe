"""
Application configuration helpers.
Loads environment variables from a local .env file and provides typed getters.
"""
import os
from pathlib import Path
from typing import List


def load_env_file() -> None:
    """Load key=value pairs from .env into process environment (if present)."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env_str(name: str, default: str) -> str:
    """Read a string value from environment."""
    return os.getenv(name, default)


def env_int(name: str, default: int) -> int:
    """Read an integer value from environment with safe fallback."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def env_bool(name: str, default: bool) -> bool:
    """Read a boolean value from environment with safe fallback."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: List[str]) -> List[str]:
    """Read a comma-separated list from environment."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    values = [item.strip() for item in raw_value.split(",") if item.strip()]
    return values if values else default


# Load .env once at import time so all modules can read from os.environ.
load_env_file()