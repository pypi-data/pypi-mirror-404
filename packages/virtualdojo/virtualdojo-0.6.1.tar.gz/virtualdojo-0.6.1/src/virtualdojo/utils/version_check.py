"""Version checking utility for update notifications."""

import json
import time
from pathlib import Path

import httpx
from platformdirs import user_cache_dir

from .. import __app_name__, __version__

# Cache settings
CACHE_DURATION_HOURS = 24
CACHE_FILENAME = "version_check.json"
PYPI_URL = "https://pypi.org/pypi/virtualdojo/json"
REQUEST_TIMEOUT = 2.0  # seconds - keep it short to not slow down CLI


def _get_cache_path() -> Path:
    """Get the path to the version cache file."""
    cache_dir = Path(user_cache_dir(__app_name__))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / CACHE_FILENAME


def _read_cache() -> dict | None:
    """Read the cached version info."""
    cache_path = _get_cache_path()
    if not cache_path.exists():
        return None

    try:
        with open(cache_path) as f:
            data = json.load(f)

        # Check if cache is still valid
        cached_time = data.get("checked_at", 0)
        cache_age_hours = (time.time() - cached_time) / 3600

        if cache_age_hours < CACHE_DURATION_HOURS:
            return data
    except Exception:
        pass

    return None


def _write_cache(latest_version: str) -> None:
    """Write version info to cache."""
    cache_path = _get_cache_path()
    try:
        with open(cache_path, "w") as f:
            json.dump(
                {
                    "latest_version": latest_version,
                    "checked_at": time.time(),
                },
                f,
            )
    except Exception:
        pass  # Fail silently


def _fetch_latest_version() -> str | None:
    """Fetch the latest version from PyPI."""
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(PYPI_URL)
            if response.status_code == 200:
                data = response.json()
                return data.get("info", {}).get("version")
    except Exception:
        pass  # Fail silently on network errors

    return None


def _parse_version(version: str) -> tuple[int, ...]:
    """Parse a version string into a tuple for comparison."""
    try:
        # Handle versions like "0.4.0", "1.0.0a1", etc.
        # Strip any pre-release/build metadata for simple comparison
        clean_version = version.split("a")[0].split("b")[0].split("rc")[0]
        return tuple(int(x) for x in clean_version.split("."))
    except Exception:
        return (0, 0, 0)


def check_for_updates() -> tuple[str, str] | None:
    """Check if a newer version is available.

    Returns:
        Tuple of (current_version, latest_version) if update available,
        None otherwise.
    """
    current_version = __version__

    # Check cache first
    cache = _read_cache()
    if cache:
        latest_version = cache.get("latest_version")
    else:
        # Fetch from PyPI and update cache
        latest_version = _fetch_latest_version()
        if latest_version:
            _write_cache(latest_version)

    if not latest_version:
        return None

    # Compare versions
    current_tuple = _parse_version(current_version)
    latest_tuple = _parse_version(latest_version)

    if latest_tuple > current_tuple:
        return (current_version, latest_version)

    return None


def get_update_message() -> str | None:
    """Get the update notification message if an update is available.

    Returns:
        Formatted message string, or None if no update available.
    """
    result = check_for_updates()
    if result:
        current, latest = result
        return (
            f"[yellow]A new version of virtualdojo is available: "
            f"{current} → {latest}[/yellow]\n"
            f"[dim]Run `pip install --upgrade virtualdojo` to update[/dim]\n"
        )
    return None
