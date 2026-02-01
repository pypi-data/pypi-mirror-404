"""Check for updates from PyPI."""

import threading
import urllib.request
import json
from typing import Optional, Tuple

from meeting_noter import __version__


PYPI_URL = "https://pypi.org/pypi/meeting-noter/json"


def parse_version(version: str) -> Tuple[int, ...]:
    """Parse version string into tuple for comparison."""
    try:
        return tuple(int(x) for x in version.split("."))
    except ValueError:
        return (0, 0, 0)


def get_latest_version() -> Optional[str]:
    """Fetch the latest version from PyPI."""
    try:
        req = urllib.request.Request(
            PYPI_URL,
            headers={"Accept": "application/json", "User-Agent": "meeting-noter"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get("info", {}).get("version")
    except Exception:
        return None


def check_for_update() -> Optional[str]:
    """Check if an update is available.

    Returns the new version string if an update is available, None otherwise.
    """
    latest = get_latest_version()
    if not latest:
        return None

    current = parse_version(__version__)
    latest_parsed = parse_version(latest)

    if latest_parsed > current:
        return latest
    return None


def check_for_update_async(callback):
    """Check for updates in a background thread.

    Args:
        callback: Function to call with the new version string (or None if no update).
    """
    def _check():
        new_version = check_for_update()
        if new_version:
            callback(new_version)

    thread = threading.Thread(target=_check, daemon=True)
    thread.start()
