"""Auto-detect meetings and get meeting info from running apps."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Meeting apps - split into primary (dedicated) and secondary (chat apps with call features)
# Primary apps are checked first and take precedence

# Primary: Dedicated meeting/video call apps
PRIMARY_MEETING_APPS = {
    "zoom.us": {
        "name": "Zoom",
        "title_pattern": r"(?:Zoom Meeting|Zoom Webinar)(?:\s*-\s*(.+))?",
        "title_contains": ["zoom meeting", "zoom webinar", "zoom"],
    },
    "Microsoft Teams": {
        "name": "Teams",
        "title_pattern": r"(.+?)(?:\s*\|\s*Microsoft Teams)?",
        "title_contains": ["microsoft teams", "| teams"],
    },
    "Google Chrome": {
        "name": "Meet",
        "title_pattern": r"Meet\s*-\s*([a-z]{3,4}-[a-z]{4}-[a-z]{3,4})",
        "title_contains": ["meet - "],
        "title_excludes": ["google meet"],
    },
    "Safari": {
        "name": "Meet",
        "title_pattern": r"Meet\s*-\s*([a-z]{3,4}-[a-z]{4}-[a-z]{3,4})",
        "title_contains": ["meet - "],
        "title_excludes": ["google meet"],
    },
    "Arc": {
        "name": "Meet",
        "title_pattern": r"Meet\s*-\s*([a-z]{3,4}-[a-z]{4}-[a-z]{3,4})",
        "title_contains": ["meet - "],
        "title_excludes": ["google meet"],
    },
    "FaceTime": {
        "name": "FaceTime",
        "title_pattern": r"(.+)",
        "title_contains": ["facetime"],
    },
    "Webex": {
        "name": "Webex",
        "title_pattern": r"(.+?)(?:\s*-\s*Webex)?",
        "title_contains": ["webex", "meeting"],
    },
}

# Secondary: Chat apps with huddle/call features (only checked if no primary meeting found)
SECONDARY_MEETING_APPS = {
    "Slack": {
        "name": "Slack Huddle",
        # Only match window titles that explicitly contain huddle/call
        "title_pattern": r"(?:Huddle|Call)(?:\s+(?:in|with)\s+)?(.+)?",
        "title_contains": ["huddle", "slack call"],
    },
    "Discord": {
        "name": "Discord",
        "title_pattern": r"(.+)",
        # Only match when actually connected to voice
        "title_contains": ["voice connected"],
    },
}

# Combined for backwards compatibility
MEETING_APPS = {**PRIMARY_MEETING_APPS, **SECONDARY_MEETING_APPS}


@dataclass
class MeetingInfo:
    """Information about a detected meeting."""
    app_name: str
    meeting_name: Optional[str]
    window_title: str
    is_active: bool = True


def _get_running_apps() -> list[dict]:
    """Get list of running applications."""
    try:
        from AppKit import NSWorkspace
        workspace = NSWorkspace.sharedWorkspace()
        apps = workspace.runningApplications()
        return [
            {
                "name": app.localizedName(),
                "bundle_id": app.bundleIdentifier(),
                "is_active": app.isActive(),
            }
            for app in apps
            if app.localizedName()
        ]
    except ImportError:
        return []


def _get_frontmost_app() -> Optional[str]:
    """Get the frontmost (active) application name."""
    try:
        from AppKit import NSWorkspace
        workspace = NSWorkspace.sharedWorkspace()
        app = workspace.frontmostApplication()
        return app.localizedName() if app else None
    except ImportError:
        return None


def _get_window_titles(app_name: str) -> list[str]:
    """Get window titles for a specific app."""
    try:
        import Quartz

        windows = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID
        )

        titles = []
        for window in windows:
            owner = window.get(Quartz.kCGWindowOwnerName, "")
            title = window.get(Quartz.kCGWindowName, "")
            if owner == app_name and title:
                titles.append(title)

        return titles
    except ImportError:
        return []


def _is_microphone_in_use() -> bool:
    """Check if any app is currently using the microphone."""
    try:
        import subprocess
        # Check for apps using microphone via system_profiler or log
        # This is a simplified check - looks for common audio processes
        result = subprocess.run(
            ["lsof", "+D", "/dev"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Check for audio device access
        audio_indicators = ["coreaudiod", "audiod"]
        return any(ind in result.stdout.lower() for ind in audio_indicators)
    except Exception:
        return False


def _extract_meeting_name(window_title: str, pattern: str) -> Optional[str]:
    """Extract meeting name from window title using pattern."""
    match = re.search(pattern, window_title, re.IGNORECASE)
    if match and match.groups():
        name = match.group(1)
        if name:
            # Clean up the name
            name = name.strip()
            name = re.sub(r'\s+', ' ', name)
            # Remove common suffixes
            name = re.sub(r'\s*\([\d\s:APMapm]+\)$', '', name)  # Remove time
            return name if name else None
    return None


def _check_windows_for_apps(windows, app_configs: dict) -> Optional[MeetingInfo]:
    """Check windows against a set of app configurations.

    Args:
        windows: List of window info from CGWindowListCopyWindowInfo
        app_configs: Dict mapping app patterns to their config

    Returns:
        MeetingInfo if a meeting is detected, None otherwise.
    """
    import Quartz

    for window in windows:
        owner = window.get(Quartz.kCGWindowOwnerName, "")
        title = window.get(Quartz.kCGWindowName, "")

        if not owner or not title:
            continue

        for app_pattern, app_info in app_configs.items():
            if app_pattern.lower() not in owner.lower():
                continue

            # Check if title contains meeting indicators
            title_lower = title.lower()
            title_matches = False

            if "title_contains" in app_info:
                for indicator in app_info["title_contains"]:
                    if indicator.lower() in title_lower:
                        title_matches = True
                        break
            else:
                title_matches = True

            if not title_matches:
                continue

            # Check for exclusions (e.g., "Google Meet" homepage)
            if "title_excludes" in app_info:
                excluded = False
                for exclude in app_info["title_excludes"]:
                    if title_lower == exclude.lower():
                        excluded = True
                        break
                if excluded:
                    continue

            # Extract meeting name from title
            pattern = app_info["title_pattern"]
            meeting_name = _extract_meeting_name(title, pattern)

            return MeetingInfo(
                app_name=app_info["name"],
                meeting_name=meeting_name,
                window_title=title,
                is_active=True,
            )

    return None


def detect_active_meeting() -> Optional[MeetingInfo]:
    """Detect if there's an active meeting and get its info.

    Checks primary meeting apps (Zoom, Teams, Meet, etc.) first.
    Only checks secondary apps (Slack, Discord) if no primary meeting is found.

    Returns MeetingInfo if a meeting is detected, None otherwise.
    """
    try:
        from AppKit import NSWorkspace
        import Quartz
    except ImportError:
        return None

    # Get all windows
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID
    )

    # First, check for primary meeting apps (dedicated video conferencing)
    result = _check_windows_for_apps(windows, PRIMARY_MEETING_APPS)
    if result:
        return result

    # Only check secondary apps (chat apps with call features) if no primary meeting found
    return _check_windows_for_apps(windows, SECONDARY_MEETING_APPS)


def get_calendar_meeting() -> Optional[str]:
    """Get the name of current meeting from calendar.

    Note: Requires calendar access permission.
    """
    try:
        from EventKit import EKEventStore, EKEntityTypeEvent
        from Foundation import NSDate

        store = EKEventStore.alloc().init()

        # Check if we have access
        # Note: This will prompt for permission on first run

        now = NSDate.date()
        # Get events from 5 minutes ago to 5 minutes from now
        start = now.dateByAddingTimeInterval_(-300)
        end = now.dateByAddingTimeInterval_(300)

        calendars = store.calendarsForEntityType_(EKEntityTypeEvent)
        predicate = store.predicateForEventsWithStartDate_endDate_calendars_(
            start, end, calendars
        )
        events = store.eventsMatchingPredicate_(predicate)

        for event in events:
            title = event.title()
            if title:
                return title

        return None
    except Exception:
        return None


class MeetingMonitor:
    """Monitor for active meetings."""

    def __init__(self):
        self.last_meeting: Optional[MeetingInfo] = None
        self._was_in_meeting = False

    def check(self) -> tuple[bool, bool, Optional[MeetingInfo]]:
        """Check for meeting status change.

        Returns:
            Tuple of (meeting_started, meeting_ended, meeting_info)
            - meeting_started is True if a new meeting was just detected
            - meeting_ended is True if the meeting just ended
            - meeting_info contains the meeting details (or None if no meeting)
        """
        current = detect_active_meeting()

        meeting_started = False
        meeting_ended = False

        if current and not self._was_in_meeting:
            # New meeting started
            meeting_started = True
            self.last_meeting = current
            self._was_in_meeting = True
        elif not current and self._was_in_meeting:
            # Meeting ended
            meeting_ended = True
            self._was_in_meeting = False
        elif current:
            # Still in meeting, update info
            self.last_meeting = current

        return meeting_started, meeting_ended, current

    def is_in_meeting(self) -> bool:
        """Check if currently in a meeting."""
        return self._was_in_meeting
