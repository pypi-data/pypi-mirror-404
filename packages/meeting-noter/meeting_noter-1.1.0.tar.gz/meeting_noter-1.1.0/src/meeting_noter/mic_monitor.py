"""Monitor microphone usage to detect when meetings start/end."""

from __future__ import annotations

import ctypes
from ctypes import c_uint32, c_int32, byref, POINTER, Structure
import time
from typing import Optional
from dataclasses import dataclass


@dataclass
class MicStatus:
    """Status of microphone usage."""
    is_in_use: bool
    app_name: Optional[str] = None


# CoreAudio constants
_kAudioObjectSystemObject = 1
_kAudioHardwarePropertyDefaultInputDevice = 1682533920  # 'dIn '
_kAudioDevicePropertyDeviceIsRunningSomewhere = 1735356005  # 'gone'
_kAudioObjectPropertyScopeGlobal = 1735159650  # 'glob'
_kAudioObjectPropertyElementMain = 0


class _AudioObjectPropertyAddress(Structure):
    _fields_ = [
        ('mSelector', c_uint32),
        ('mScope', c_uint32),
        ('mElement', c_uint32),
    ]


# Load CoreAudio framework lazily
_core_audio = None
_AudioObjectGetPropertyDataSize = None
_AudioObjectGetPropertyData = None


def _init_coreaudio():
    """Initialize CoreAudio framework."""
    global _core_audio, _AudioObjectGetPropertyDataSize, _AudioObjectGetPropertyData

    if _core_audio is not None:
        return True

    try:
        _core_audio = ctypes.CDLL('/System/Library/Frameworks/CoreAudio.framework/CoreAudio')

        _AudioObjectGetPropertyDataSize = _core_audio.AudioObjectGetPropertyDataSize
        _AudioObjectGetPropertyDataSize.argtypes = [
            c_uint32, POINTER(_AudioObjectPropertyAddress), c_uint32, ctypes.c_void_p, POINTER(c_uint32)
        ]
        _AudioObjectGetPropertyDataSize.restype = c_int32

        _AudioObjectGetPropertyData = _core_audio.AudioObjectGetPropertyData
        _AudioObjectGetPropertyData.argtypes = [
            c_uint32, POINTER(_AudioObjectPropertyAddress), c_uint32, ctypes.c_void_p, POINTER(c_uint32), ctypes.c_void_p
        ]
        _AudioObjectGetPropertyData.restype = c_int32

        return True
    except Exception:
        return False


def is_mic_in_use_by_another_app() -> bool:
    """Check if the microphone is being used by another application.

    Uses CoreAudio's kAudioDevicePropertyDeviceIsRunningSomewhere property
    to detect if any app has an active audio input session.

    Returns:
        True if another app is using the microphone
    """
    if not _init_coreaudio():
        return False

    try:
        # Get default input device
        addr = _AudioObjectPropertyAddress(
            _kAudioHardwarePropertyDefaultInputDevice,
            _kAudioObjectPropertyScopeGlobal,
            _kAudioObjectPropertyElementMain
        )

        size = c_uint32(4)
        device_id = c_uint32(0)

        err = _AudioObjectGetPropertyData(
            _kAudioObjectSystemObject, byref(addr), 0, None, byref(size), byref(device_id)
        )

        if err != 0 or device_id.value == 0:
            return False

        # Check if device is running somewhere (another app using it)
        addr_running = _AudioObjectPropertyAddress(
            _kAudioDevicePropertyDeviceIsRunningSomewhere,
            _kAudioObjectPropertyScopeGlobal,
            _kAudioObjectPropertyElementMain
        )

        is_running = c_uint32(0)
        size = c_uint32(4)

        err = _AudioObjectGetPropertyData(
            device_id.value, byref(addr_running), 0, None, byref(size), byref(is_running)
        )

        return err == 0 and is_running.value != 0

    except Exception:
        return False


def is_meeting_app_active() -> Optional[str]:
    """Check if a meeting app has an ACTIVE MEETING window.

    Prioritizes dedicated meeting apps over chat apps.
    Returns the app name only if there's an active call/meeting,
    not just because the app is open.
    """
    try:
        import Quartz

        # Get all on-screen windows
        windows = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID
        )

        # First pass: check for primary meeting apps (dedicated video conferencing)
        for win in windows:
            owner = win.get(Quartz.kCGWindowOwnerName, "")
            title = win.get(Quartz.kCGWindowName, "") or ""

            if not owner:
                continue

            owner_lower = owner.lower()
            title_lower = title.lower()

            # Zoom: detect meeting windows (not just "Zoom Workplace" or "Zoom")
            if "zoom.us" in owner_lower:
                # Skip non-meeting windows
                if title_lower in ["", "zoom", "zoom workplace", "zoom.us"]:
                    continue
                # This is likely a meeting window
                return "Zoom"

            # Microsoft Teams: detect call windows
            if "microsoft teams" in owner_lower:
                # Skip main app windows
                if title_lower in ["", "microsoft teams"]:
                    continue
                return "Teams"

            # FaceTime
            if "facetime" in owner_lower:
                if title and title_lower != "facetime":
                    return "FaceTime"

            # Webex
            if "webex" in owner_lower:
                if title and "meeting" in title_lower:
                    return "Webex"

            # Browser-based meetings (Google Meet, etc.)
            if any(browser in owner_lower for browser in ["chrome", "safari", "firefox", "edge", "brave", "arc"]):
                # Skip video streaming sites (YouTube, Vimeo, etc.)
                if any(x in title_lower for x in ["youtube", "vimeo", "twitch", "netflix"]):
                    continue
                if title_lower.startswith("meet -") or "meet.google.com" in title_lower:
                    return "Google Meet"
                if " meeting" in title_lower and any(x in title_lower for x in ["zoom", "teams", "webex"]):
                    return "Browser Meeting"

        # Second pass: check for secondary apps (chat apps with call features)
        for win in windows:
            owner = win.get(Quartz.kCGWindowOwnerName, "")
            title = win.get(Quartz.kCGWindowName, "") or ""

            if not owner:
                continue

            owner_lower = owner.lower()
            title_lower = title.lower()

            # Slack: detect huddle/call windows only
            if "slack" in owner_lower:
                if any(x in title_lower for x in ["huddle", "call"]):
                    return "Slack"

            # Discord: detect voice channel
            if "discord" in owner_lower:
                if "voice connected" in title_lower:
                    return "Discord"

        return None
    except Exception:
        return None


def get_meeting_window_title() -> Optional[str]:
    """Get the window title of the active meeting app.

    Prioritizes dedicated meeting apps (Zoom, Teams, Meet) over chat apps (Slack, Discord).
    Returns the window title (meeting name) if found, or app name as fallback.
    """
    try:
        import Quartz

        # Primary meeting apps (checked first) - dedicated video conferencing
        primary_apps = {
            "zoom.us": "Zoom",
            "microsoft teams": "Teams",
            "facetime": "FaceTime",
            "webex": "Webex",
        }
        # Secondary apps (chat apps with call features) - only used if no primary found
        secondary_apps = {"slack": "Slack_Huddle", "discord": "Discord"}
        browsers = ["chrome", "safari", "firefox", "edge", "brave", "arc"]

        # Get all on-screen windows
        windows = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID
        )

        # First pass: check for primary meeting apps
        found_primary_app = None  # Track if we found a primary app (for fallback)

        for win in windows:
            owner = win.get(Quartz.kCGWindowOwnerName, "")
            title = win.get(Quartz.kCGWindowName, "") or ""

            if not owner:
                continue

            owner_lower = owner.lower()
            title_lower = title.lower()

            # Check primary meeting apps
            for app_id, app_name in primary_apps.items():
                if app_id.lower() in owner_lower:
                    # Remember we found this app (for fallback)
                    if found_primary_app is None:
                        # Check if it looks like an active meeting window
                        if "zoom.us" in owner_lower and title_lower not in ["", "zoom workplace"]:
                            found_primary_app = app_name
                        elif "microsoft teams" in owner_lower and title_lower not in ["", "microsoft teams"]:
                            found_primary_app = app_name
                        elif title and title_lower not in ["", app_name.lower()]:
                            found_primary_app = app_name

                    # Return specific title if meaningful
                    if title and _is_meaningful_title(title, owner):
                        return _clean_meeting_title(title)

            # Check browser-based meetings (Google Meet)
            if any(browser in owner_lower for browser in browsers):
                if title_lower.startswith("meet -"):
                    return _clean_meeting_title(title)

        # If we found a primary meeting app but no specific title, use app name
        if found_primary_app:
            return found_primary_app

        # Second pass: only check secondary apps if no primary meeting found
        for win in windows:
            owner = win.get(Quartz.kCGWindowOwnerName, "")
            title = win.get(Quartz.kCGWindowName, "") or ""

            if not owner:
                continue

            owner_lower = owner.lower()

            for app_id, app_name in secondary_apps.items():
                if app_id.lower() in owner_lower:
                    # For Slack/Discord, only match if it looks like a call window
                    if "slack" in owner_lower:
                        if "huddle" in title.lower() or "call" in title.lower():
                            return _clean_meeting_title(title) if title else app_name
                    elif "discord" in owner_lower:
                        if "voice connected" in title.lower():
                            return _clean_meeting_title(title) if title else app_name

        return None
    except Exception:
        return None


def _is_meaningful_title(title: str, app_name: str) -> bool:
    """Check if a window title is meaningful (not just the app name)."""
    # Skip generic titles
    generic_titles = [
        "zoom", "zoom.us", "zoom meeting", "zoom workplace",
        "microsoft teams", "teams",
        "slack", "discord", "facetime", "webex",
        "", " "
    ]

    title_lower = title.lower().strip()

    # Skip if it's just the app name or a generic title
    if title_lower in generic_titles:
        return False

    # Skip Zoom's generic windows
    if "zoom.us" in app_name.lower():
        if title_lower in ["zoom", "zoom meeting", "zoom workplace"]:
            return False

    return True


def _clean_meeting_title(title: str) -> str:
    """Clean up a meeting title for use as a filename."""
    import re

    # Remove common prefixes/suffixes
    title = title.strip()

    # Google Meet: "Meet - xyz-abc-123 🔊" -> "Meet_xyz-abc-123"
    if title.lower().startswith("meet - "):
        title = "Meet_" + title[7:]
        # Remove speaker emoji and other indicators
        title = re.sub(r'[🔊🔇📹]', '', title).strip()

    # Remove "Zoom Meeting - " prefix
    if title.lower().startswith("zoom meeting - "):
        title = title[15:]

    # Remove " - Zoom" suffix
    if title.lower().endswith(" - zoom"):
        title = title[:-7]

    # Remove " | Microsoft Teams" suffix
    if " | Microsoft Teams" in title:
        title = title.split(" | Microsoft Teams")[0]

    # Replace invalid filename characters
    title = re.sub(r'[<>:"/\\|?*]', '_', title)

    # Replace multiple spaces/underscores with single underscore
    title = re.sub(r'[\s_]+', '_', title)

    # Limit length
    if len(title) > 50:
        title = title[:50]

    return title.strip('_')


def get_app_using_mic() -> Optional[str]:
    """Get the name of the meeting app that might be using the microphone.

    Note: This returns any active meeting app, but doesn't guarantee
    that specific app is the one using the mic.
    """
    return is_meeting_app_active()


class MicrophoneMonitor:
    """Monitor microphone usage to detect meeting start/end.

    Start detection: Another app starts using the microphone
    Stop detection: The meeting app window is no longer visible

    This approach works because:
    - Start: CoreAudio tells us when mic is activated (before we start recording)
    - Stop: We can't rely on mic state (our recording uses it), so we check if meeting app is gone
    """

    def __init__(self):
        self._was_mic_in_use = False
        self._is_recording = False
        self._recording_app: Optional[str] = None  # Which app triggered recording
        self._last_check_time = 0
        self._on_count = 0   # Count consecutive "on" readings
        self._off_count = 0  # Count consecutive "off" readings
        self._on_threshold = 2   # Require 2 consecutive "on" readings to trigger start
        self._off_threshold = 3  # Require 3 consecutive "off" readings to trigger stop

    def set_recording(self, is_recording: bool, app_name: Optional[str] = None):
        """Tell the monitor whether we're currently recording."""
        self._is_recording = is_recording

        if is_recording:
            self._was_mic_in_use = True
            self._on_count = 0
            # Only set app_name if provided (don't overwrite on status updates)
            if app_name:
                self._recording_app = app_name
        else:
            self._recording_app = None

    def check(self) -> tuple[bool, bool, Optional[str]]:
        """Check for microphone usage changes.

        Returns:
            Tuple of (mic_started, mic_stopped, app_name)
            - mic_started: True if another app started using mic (should prompt to record)
            - mic_stopped: True if meeting app closed (should stop recording)
            - app_name: Name of meeting app (if detected)
        """
        now = time.time()

        # Debounce - check every 2 seconds
        if now - self._last_check_time < 2.0:
            return False, False, None
        self._last_check_time = now

        mic_started = False
        mic_stopped = False
        app_name = None

        if self._is_recording:
            # While recording: check if meeting app is still visible
            # (Can't rely on mic state since our app is using it)
            current_app = is_meeting_app_active()

            if current_app is None:
                # Meeting app window is gone
                self._off_count += 1
                if self._off_count >= self._off_threshold:
                    mic_stopped = True
                    self._was_mic_in_use = False
                    self._off_count = 0
            else:
                self._off_count = 0
        else:
            # Not recording: check if mic is being used by another app
            mic_in_use = is_mic_in_use_by_another_app()

            if mic_in_use:
                self._off_count = 0
                # Get app name for display (optional, doesn't affect start decision)
                app_name = is_meeting_app_active()

                if not self._was_mic_in_use:
                    self._on_count += 1
                    # Require consecutive readings to avoid false positives
                    if self._on_count >= self._on_threshold:
                        mic_started = True
                        self._was_mic_in_use = True
                        self._on_count = 0
            else:
                self._on_count = 0
                self._was_mic_in_use = False

        return mic_started, mic_stopped, app_name

    def is_mic_active(self) -> bool:
        """Check if microphone is currently in use by another app."""
        return is_mic_in_use_by_another_app()
