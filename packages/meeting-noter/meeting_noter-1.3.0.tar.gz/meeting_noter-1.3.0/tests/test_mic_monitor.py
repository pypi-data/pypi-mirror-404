"""Tests for the mic monitor module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from meeting_noter.mic_monitor import (
    MicrophoneMonitor,
    MicStatus,
    _clean_meeting_title,
    _is_meaningful_title,
    get_meeting_window_title,
    is_meeting_app_active,
    is_mic_in_use_by_another_app,
)


class TestMicStatus:
    """Tests for MicStatus dataclass."""

    def test_mic_status_fields(self):
        """MicStatus should have correct fields."""
        status = MicStatus(is_in_use=True, app_name="Zoom")

        assert status.is_in_use is True
        assert status.app_name == "Zoom"

    def test_mic_status_optional_app_name(self):
        """app_name should be optional."""
        status = MicStatus(is_in_use=True)

        assert status.is_in_use is True
        assert status.app_name is None


class TestIsMeetingAppActive:
    """Tests for is_meeting_app_active function."""

    def test_detect_zoom_meeting(self, mock_quartz):
        """Should detect Zoom meeting window."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "zoom.us",
                "kCGWindowName": "Zoom Meeting - Team Standup",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = is_meeting_app_active()

            assert result == "Zoom"

    def test_detect_teams_meeting(self, mock_quartz):
        """Should detect Teams meeting window."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "Microsoft Teams",
                "kCGWindowName": "Planning Meeting | Microsoft Teams",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = is_meeting_app_active()

            assert result == "Teams"

    def test_detect_google_meet(self, mock_quartz):
        """Should detect Google Meet in browser."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "Google Chrome",
                "kCGWindowName": "Meet - abc-defg-hij",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = is_meeting_app_active()

            assert result == "Google Meet"

    def test_detect_slack_huddle(self, mock_quartz):
        """Should detect Slack huddle."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "Slack",
                "kCGWindowName": "Huddle in #team-chat",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = is_meeting_app_active()

            assert result == "Slack"

    def test_skip_zoom_workplace(self, mock_quartz):
        """Should skip Zoom Workplace (not a meeting)."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "zoom.us",
                "kCGWindowName": "Zoom Workplace",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = is_meeting_app_active()

            assert result is None

    def test_no_meeting_app(self, mock_quartz):
        """Should return None when no meeting app active."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "Finder",
                "kCGWindowName": "Documents",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = is_meeting_app_active()

            assert result is None


class TestGetMeetingWindowTitle:
    """Tests for get_meeting_window_title function."""

    def test_get_zoom_title(self, mock_quartz):
        """Should get Zoom meeting title."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "zoom.us",
                "kCGWindowName": "Zoom Meeting - Weekly Standup",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = get_meeting_window_title()

            # Should clean up title
            assert result is not None
            assert "Weekly" in result or "Zoom" in result

    def test_get_meet_code(self, mock_quartz):
        """Should get Google Meet code."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "Safari",
                "kCGWindowName": "Meet - abc-defg-hij",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = get_meeting_window_title()

            assert result is not None
            assert "abc-defg-hij" in result

    def test_primary_over_secondary(self, mock_quartz):
        """Primary meeting apps should take precedence."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "Slack",
                "kCGWindowName": "Huddle in #channel",
            },
            {
                "kCGWindowOwnerName": "zoom.us",
                "kCGWindowName": "Important Meeting",
            },
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = get_meeting_window_title()

            # Zoom should be detected, not Slack
            assert result is not None
            assert "Important" in result or "Zoom" in result


class TestIsMeaningfulTitle:
    """Tests for _is_meaningful_title function."""

    def test_meaningful_title(self):
        """Specific meeting names should be meaningful."""
        assert _is_meaningful_title("Weekly Team Standup", "zoom.us") is True
        assert _is_meaningful_title("Project Planning", "Microsoft Teams") is True

    def test_generic_title_not_meaningful(self):
        """Generic titles should not be meaningful."""
        assert _is_meaningful_title("Zoom", "zoom.us") is False
        assert _is_meaningful_title("Zoom Workplace", "zoom.us") is False
        assert _is_meaningful_title("Microsoft Teams", "Microsoft Teams") is False
        assert _is_meaningful_title("", "zoom.us") is False


class TestCleanMeetingTitle:
    """Tests for _clean_meeting_title function."""

    def test_clean_meet_title(self):
        """Should clean Google Meet titles."""
        result = _clean_meeting_title("Meet - abc-defg-hij 🔊")

        assert "abc-defg-hij" in result
        assert "🔊" not in result

    def test_clean_zoom_title(self):
        """Should clean Zoom titles."""
        result = _clean_meeting_title("Zoom Meeting - Team Call")

        assert result == "Team Call" or "Team_Call" in result

    def test_clean_teams_title(self):
        """Should clean Teams titles."""
        result = _clean_meeting_title("Sprint Planning | Microsoft Teams")

        assert "Sprint" in result or "Planning" in result
        assert "Microsoft Teams" not in result

    def test_clean_invalid_chars(self):
        """Should replace invalid filename characters."""
        result = _clean_meeting_title("Meeting: 2024/01/15")

        assert ":" not in result
        assert "/" not in result


class TestMicrophoneMonitor:
    """Tests for MicrophoneMonitor class."""

    def test_microphone_monitor_init(self):
        """MicrophoneMonitor should initialize correctly."""
        monitor = MicrophoneMonitor()

        assert monitor._was_mic_in_use is False
        assert monitor._is_recording is False
        assert monitor._recording_app is None

    def test_set_recording(self):
        """set_recording should update state."""
        monitor = MicrophoneMonitor()

        monitor.set_recording(True, "Zoom")

        assert monitor._is_recording is True
        assert monitor._was_mic_in_use is True
        assert monitor._recording_app == "Zoom"

    def test_set_recording_stop(self):
        """set_recording(False) should clear state."""
        monitor = MicrophoneMonitor()
        monitor.set_recording(True, "Zoom")

        monitor.set_recording(False)

        assert monitor._is_recording is False
        assert monitor._recording_app is None

    def test_check_debounce(self):
        """check should debounce calls."""
        monitor = MicrophoneMonitor()

        # First call
        started1, stopped1, app1 = monitor.check()

        # Immediate second call should be debounced
        started2, stopped2, app2 = monitor.check()

        assert started2 is False
        assert stopped2 is False

    def test_is_mic_active(self, mocker):
        """is_mic_active should check mic usage."""
        mocker.patch(
            "meeting_noter.mic_monitor.is_mic_in_use_by_another_app",
            return_value=True,
        )

        monitor = MicrophoneMonitor()

        assert monitor.is_mic_active() is True

    def test_check_mic_started(self, mocker):
        """Should detect when mic starts being used."""
        monitor = MicrophoneMonitor()
        monitor._last_check_time = 0  # Reset debounce

        # Mock mic in use and meeting app active
        mocker.patch(
            "meeting_noter.mic_monitor.is_mic_in_use_by_another_app",
            return_value=True,
        )
        mocker.patch(
            "meeting_noter.mic_monitor.is_meeting_app_active",
            return_value="Zoom",
        )

        # Need multiple consecutive readings to trigger
        monitor._last_check_time = 0
        monitor.check()
        monitor._last_check_time = 0
        started, stopped, app = monitor.check()

        assert started is True
        assert stopped is False
        assert app == "Zoom"

    def test_check_mic_stopped(self, mocker):
        """Should detect when meeting app closes."""
        monitor = MicrophoneMonitor()
        monitor._is_recording = True
        monitor._was_mic_in_use = True
        monitor._last_check_time = 0
        monitor._off_threshold = 3

        # Meeting app no longer active
        mocker.patch(
            "meeting_noter.mic_monitor.is_meeting_app_active",
            return_value=None,
        )

        # Need multiple consecutive readings to trigger (off_threshold = 3)
        stopped = False
        for _ in range(5):
            monitor._last_check_time = 0
            started, current_stopped, _ = monitor.check()
            if current_stopped:
                stopped = True
                break

        assert stopped is True


class TestIsMicInUseByAnotherApp:
    """Tests for is_mic_in_use_by_another_app function."""

    def test_coreaudio_not_available(self, mocker):
        """Should return False when CoreAudio not available."""
        mocker.patch(
            "meeting_noter.mic_monitor._init_coreaudio",
            return_value=False,
        )

        from meeting_noter.mic_monitor import is_mic_in_use_by_another_app

        result = is_mic_in_use_by_another_app()

        assert result is False


class TestGetMeetingWindowTitleExtended:
    """Extended tests for get_meeting_window_title function."""

    def test_no_quartz(self, mocker):
        """Should return None when Quartz not available."""
        mocker.patch.dict("sys.modules", {"Quartz": None})

        from meeting_noter.mic_monitor import get_meeting_window_title

        # Force reimport to pick up the mock
        result = get_meeting_window_title()

        assert result is None

    def test_exception_handling(self, mock_quartz):
        """Should return None on exception."""
        mock_quartz.CGWindowListCopyWindowInfo.side_effect = Exception("Error")

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = get_meeting_window_title()

            assert result is None

    def test_get_teams_title(self, mock_quartz):
        """Should get Teams meeting title."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "Microsoft Teams",
                "kCGWindowName": "Sprint Planning | Microsoft Teams",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = get_meeting_window_title()

            assert result is not None
            assert "Sprint" in result or "Planning" in result

    def test_get_facetime_title(self, mock_quartz):
        """Should get FaceTime title."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "FaceTime",
                "kCGWindowName": "John Smith",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = get_meeting_window_title()

            assert result is not None

    def test_get_webex_title(self, mock_quartz):
        """Should get Webex meeting title."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "Webex",
                "kCGWindowName": "Team Meeting",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = get_meeting_window_title()

            assert result is not None


class TestIsMeetingAppActiveExtended:
    """Extended tests for is_meeting_app_active function."""

    def test_detect_facetime(self, mock_quartz):
        """Should detect FaceTime call."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "FaceTime",
                "kCGWindowName": "John Smith",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = is_meeting_app_active()

            assert result == "FaceTime"

    def test_detect_webex_meeting(self, mock_quartz):
        """Should detect Webex meeting."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "Webex",
                "kCGWindowName": "Team Meeting",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = is_meeting_app_active()

            assert result == "Webex"

    def test_detect_discord_voice(self, mock_quartz):
        """Should detect Discord voice channel."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "Discord",
                "kCGWindowName": "Voice Connected - #general",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = is_meeting_app_active()

            assert result == "Discord"

    def test_detect_browser_meeting(self, mock_quartz):
        """Should detect browser-based meeting."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "Safari",
                "kCGWindowName": "Zoom Meeting | zoom.us",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = is_meeting_app_active()

            assert result == "Browser Meeting"

    def test_empty_windows(self, mock_quartz):
        """Should return None with no windows."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = []

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = is_meeting_app_active()

            assert result is None

    def test_exception_returns_none(self, mock_quartz):
        """Should return None on exception."""
        mock_quartz.CGWindowListCopyWindowInfo.side_effect = Exception("Error")

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            result = is_meeting_app_active()

            assert result is None


class TestMicrophoneMonitorExtended:
    """Extended tests for MicrophoneMonitor class."""

    def test_monitor_recording_state_persistence(self):
        """Recording app should persist after set_recording(True)."""
        monitor = MicrophoneMonitor()

        monitor.set_recording(True, "Zoom")
        assert monitor._recording_app == "Zoom"

        # Update without app_name should preserve it
        monitor.set_recording(True)
        assert monitor._recording_app == "Zoom"

    def test_monitor_off_count_reset(self, mocker):
        """Off count should reset when meeting app reappears."""
        monitor = MicrophoneMonitor()
        monitor._is_recording = True
        monitor._was_mic_in_use = True
        monitor._last_check_time = 0
        monitor._off_count = 2

        # Meeting app reappears
        mocker.patch(
            "meeting_noter.mic_monitor.is_meeting_app_active",
            return_value="Zoom",
        )

        monitor._last_check_time = 0
        monitor.check()

        assert monitor._off_count == 0

    def test_monitor_on_count_reset(self, mocker):
        """On count should reset when mic goes idle."""
        monitor = MicrophoneMonitor()
        monitor._last_check_time = 0
        monitor._on_count = 1

        # Mic not in use
        mocker.patch(
            "meeting_noter.mic_monitor.is_mic_in_use_by_another_app",
            return_value=False,
        )

        monitor._last_check_time = 0
        monitor.check()

        assert monitor._on_count == 0


class TestCleanMeetingTitleExtended:
    """Extended tests for _clean_meeting_title function."""

    def test_clean_zoom_suffix(self):
        """Should clean ' - Zoom' suffix."""
        result = _clean_meeting_title("Team Meeting - Zoom")

        assert "Zoom" not in result
        assert "Team" in result or "Meeting" in result

    def test_truncate_long_title(self):
        """Should truncate titles over 50 characters."""
        long_title = "A" * 60

        result = _clean_meeting_title(long_title)

        assert len(result) <= 50

    def test_replace_multiple_spaces(self):
        """Should replace multiple spaces/underscores."""
        result = _clean_meeting_title("Meeting   With   Spaces")

        assert "   " not in result
        assert "_" in result or " " in result

    def test_strip_trailing_underscores(self):
        """Should strip trailing underscores."""
        result = _clean_meeting_title("Meeting___")

        assert not result.endswith("_")


class TestGetAppUsingMic:
    """Tests for get_app_using_mic function."""

    def test_get_app_using_mic_delegates(self, mock_quartz):
        """Should delegate to is_meeting_app_active."""
        mock_quartz.CGWindowListCopyWindowInfo.return_value = [
            {
                "kCGWindowOwnerName": "zoom.us",
                "kCGWindowName": "Test Meeting",
            }
        ]

        with patch.dict("sys.modules", {"Quartz": mock_quartz}):
            from meeting_noter.mic_monitor import get_app_using_mic

            result = get_app_using_mic()

            assert result == "Zoom"
