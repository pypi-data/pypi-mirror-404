"""Version update check for Janus Labs CLI (JL-230).

Checks PyPI for newer versions and displays a banner if an update is available.
Caches results locally with a 24-hour TTL to avoid repeated network calls.
"""

import json
import os
import sys
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Tuple

import httpx


PYPI_URL = "https://pypi.org/pypi/janus-labs/json"
CACHE_TTL_HOURS = 24
REQUEST_TIMEOUT_SECONDS = 2.0


def get_cache_path() -> Path:
    """Get platform-appropriate cache directory for version check."""
    if sys.platform == "win32":
        # Windows: %LOCALAPPDATA%\janus-labs\
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        # Unix: ~/.cache/janus-labs/
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))

    cache_dir = base / "janus-labs"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "version-cache.json"


def read_cache() -> Optional[dict]:
    """Read cached version info if valid (within TTL)."""
    cache_path = get_cache_path()
    if not cache_path.exists():
        return None

    try:
        data = json.loads(cache_path.read_text())
        checked_at = datetime.fromisoformat(data["checked_at"])
        if datetime.now(timezone.utc) - checked_at < timedelta(hours=CACHE_TTL_HOURS):
            return data
    except (json.JSONDecodeError, KeyError, ValueError):
        pass

    return None


def write_cache(latest_version: str) -> None:
    """Write version info to cache."""
    cache_path = get_cache_path()
    try:
        data = {
            "latest_version": latest_version,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "ttl_hours": CACHE_TTL_HOURS,
        }
        cache_path.write_text(json.dumps(data, indent=2))
    except OSError:
        pass  # Fail silently - cache is optional


def fetch_latest_version() -> Optional[str]:
    """Fetch latest version from PyPI with timeout."""
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = client.get(PYPI_URL)
            response.raise_for_status()
            data = response.json()
            return data.get("info", {}).get("version")
    except Exception:
        return None  # Fail silently on any network/parsing error


def parse_version(version_str: str) -> Tuple[int, ...]:
    """Parse version string into comparable tuple.

    Handles versions like: 0.6.3, 1.0.0, 0.6.3a1, 0.6.3.dev1
    """
    # Extract numeric parts, ignoring pre-release suffixes
    match = re.match(r"(\d+(?:\.\d+)*)", version_str)
    if match:
        return tuple(int(x) for x in match.group(1).split("."))
    return (0,)


def is_newer(latest: str, current: str) -> bool:
    """Check if latest version is newer than current."""
    return parse_version(latest) > parse_version(current)


def print_update_banner(current: str, latest: str) -> None:
    """Print update available banner to stderr."""
    banner = f"""
============================================================
  Update available: {current} \u2192 {latest}
  Run: pip install -U janus-labs
============================================================
"""
    print(banner, file=sys.stderr)


def check_for_updates(current_version: str) -> None:
    """Check for updates and display banner if newer version available.

    This function is designed to be non-blocking and fail-safe:
    - Uses cached results when available (24h TTL)
    - Times out after 2 seconds on network requests
    - Fails silently on any error

    Args:
        current_version: The currently installed version string
    """
    # Check cache first
    cached = read_cache()
    if cached:
        latest = cached.get("latest_version")
        if latest and is_newer(latest, current_version):
            print_update_banner(current_version, latest)
        return

    # Fetch from PyPI
    latest = fetch_latest_version()
    if latest:
        write_cache(latest)
        if is_newer(latest, current_version):
            print_update_banner(current_version, latest)
