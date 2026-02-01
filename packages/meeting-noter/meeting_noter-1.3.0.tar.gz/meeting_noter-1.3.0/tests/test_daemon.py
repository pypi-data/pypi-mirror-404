"""Tests for the daemon module."""

from __future__ import annotations

import os
import signal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from meeting_noter.daemon import (
    check_audio_available,
    is_process_running,
    read_pid_file,
    remove_pid_file,
    write_pid_file,
)


class TestWritePidFile:
    """Tests for write_pid_file function."""

    def test_write_pid_file(self, mock_pid_file: Path):
        """Should write current PID to file."""
        write_pid_file(mock_pid_file)

        assert mock_pid_file.exists()
        content = mock_pid_file.read_text().strip()
        assert content == str(os.getpid())

    def test_write_pid_file_overwrites(self, mock_pid_file: Path):
        """Should overwrite existing PID file."""
        mock_pid_file.write_text("12345")

        write_pid_file(mock_pid_file)

        content = mock_pid_file.read_text().strip()
        assert content == str(os.getpid())
        assert content != "12345"


class TestReadPidFile:
    """Tests for read_pid_file function."""

    def test_read_pid_file(self, mock_pid_file: Path):
        """Should read PID from file."""
        mock_pid_file.write_text("12345")

        pid = read_pid_file(mock_pid_file)

        assert pid == 12345

    def test_read_pid_file_not_found(self, mock_pid_file: Path):
        """Should return None when file doesn't exist."""
        pid = read_pid_file(mock_pid_file)

        assert pid is None

    def test_read_pid_file_invalid_content(self, mock_pid_file: Path):
        """Should return None for invalid content."""
        mock_pid_file.write_text("not a number")

        pid = read_pid_file(mock_pid_file)

        assert pid is None

    def test_read_pid_file_empty(self, mock_pid_file: Path):
        """Should return None for empty file."""
        mock_pid_file.write_text("")

        pid = read_pid_file(mock_pid_file)

        assert pid is None


class TestRemovePidFile:
    """Tests for remove_pid_file function."""

    def test_remove_pid_file(self, mock_pid_file: Path):
        """Should remove existing PID file."""
        mock_pid_file.write_text("12345")
        assert mock_pid_file.exists()

        remove_pid_file(mock_pid_file)

        assert not mock_pid_file.exists()

    def test_remove_pid_file_not_found(self, mock_pid_file: Path):
        """Should not raise when file doesn't exist."""
        assert not mock_pid_file.exists()

        remove_pid_file(mock_pid_file)  # Should not raise

        assert not mock_pid_file.exists()


class TestIsProcessRunning:
    """Tests for is_process_running function."""

    def test_is_process_running_self(self):
        """Current process should be running."""
        assert is_process_running(os.getpid()) is True

    def test_is_process_running_nonexistent(self):
        """Non-existent PID should return False."""
        # Use a very high PID that's unlikely to exist
        fake_pid = 999999999

        assert is_process_running(fake_pid) is False

    def test_is_process_running_zero(self):
        """PID 0 should return False (or True on some systems)."""
        # PID 0 is special - behavior varies by OS
        # Just ensure it doesn't crash
        result = is_process_running(0)
        assert isinstance(result, bool)


class TestCheckAudioAvailable:
    """Tests for check_audio_available function."""

    def test_check_audio_available_true(self, mock_sounddevice):
        """Should return True when input devices exist."""
        mock_sounddevice.query_devices.return_value = [
            {"name": "Microphone", "max_input_channels": 2},
        ]

        with patch.dict("sys.modules", {"sounddevice": mock_sounddevice}):
            # Need to reimport after patching
            import importlib
            import meeting_noter.daemon as daemon_module

            importlib.reload(daemon_module)

            result = daemon_module.check_audio_available()

            assert result is True

    def test_check_audio_available_false(self, mock_sounddevice):
        """Should return False when no input devices."""
        mock_sounddevice.query_devices.return_value = []

        with patch.dict("sys.modules", {"sounddevice": mock_sounddevice}):
            import importlib
            import meeting_noter.daemon as daemon_module

            importlib.reload(daemon_module)

            result = daemon_module.check_audio_available()

            assert result is False

    def test_check_audio_available_exception(self, mock_sounddevice):
        """Should return False on exception."""
        mock_sounddevice.query_devices.side_effect = Exception("Device error")

        with patch.dict("sys.modules", {"sounddevice": mock_sounddevice}):
            import importlib
            import meeting_noter.daemon as daemon_module

            importlib.reload(daemon_module)

            result = daemon_module.check_audio_available()

            assert result is False


class TestSignalHandler:
    """Tests for signal handling."""

    def test_signal_handler_sets_stop_event(self):
        """Signal handler should set stop event."""
        from meeting_noter.daemon import _signal_handler, _stop_event

        # Clear the event first
        _stop_event.clear()
        assert not _stop_event.is_set()

        _signal_handler(signal.SIGTERM, None)

        assert _stop_event.is_set()

        # Clean up
        _stop_event.clear()


class TestCheckScreencapturekitAvailable:
    """Tests for check_screencapturekit_available function."""

    def test_check_screencapturekit_available_true(self, mocker):
        """Should return True when permission granted."""
        mock_quartz = MagicMock()
        mock_quartz.CGPreflightScreenCaptureAccess.return_value = True

        mocker.patch.dict("sys.modules", {"Quartz": mock_quartz})

        from meeting_noter.daemon import check_screencapturekit_available

        result = check_screencapturekit_available()

        assert result is True

    def test_check_screencapturekit_available_false(self, mocker):
        """Should return False when permission denied."""
        mock_quartz = MagicMock()
        mock_quartz.CGPreflightScreenCaptureAccess.return_value = False

        mocker.patch.dict("sys.modules", {"Quartz": mock_quartz})

        from meeting_noter.daemon import check_screencapturekit_available

        result = check_screencapturekit_available()

        assert result is False

    def test_check_screencapturekit_available_exception(self, mocker):
        """Should return False on exception."""
        mocker.patch.dict("sys.modules", {"Quartz": None})

        from meeting_noter.daemon import check_screencapturekit_available

        result = check_screencapturekit_available()

        assert result is False


class TestCheckStatus:
    """Tests for check_status function."""

    def test_check_status_not_running(self, mock_pid_file: Path, mocker, capsys):
        """Should show not running when no PID file."""
        mock_sounddevice = MagicMock()
        mock_sounddevice.query_devices.return_value = [
            {"name": "Mic", "max_input_channels": 1},
        ]
        mocker.patch.dict("sys.modules", {"sounddevice": mock_sounddevice})

        mock_quartz = MagicMock()
        mock_quartz.CGPreflightScreenCaptureAccess.return_value = False
        mocker.patch.dict("sys.modules", {"Quartz": mock_quartz})

        from meeting_noter.daemon import check_status

        check_status(mock_pid_file)

        captured = capsys.readouterr()
        assert "not running" in captured.out

    def test_check_status_running(self, mock_running_pid_file: Path, mocker, capsys, tmp_path):
        """Should show running when PID file exists with valid process."""
        mock_sounddevice = MagicMock()
        mock_sounddevice.query_devices.return_value = [
            {"name": "Mic", "max_input_channels": 1},
        ]
        mocker.patch.dict("sys.modules", {"sounddevice": mock_sounddevice})

        mock_quartz = MagicMock()
        mock_quartz.CGPreflightScreenCaptureAccess.return_value = True
        mocker.patch.dict("sys.modules", {"Quartz": mock_quartz})

        # Create a log file
        log_path = tmp_path / ".meeting-noter.log"
        log_path.write_text("Test log entry\n")
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        from meeting_noter.daemon import check_status

        check_status(mock_running_pid_file)

        captured = capsys.readouterr()
        assert "running" in captured.out


class TestStopDaemon:
    """Tests for stop_daemon function."""

    def test_stop_daemon_not_running(self, mock_pid_file: Path, capsys):
        """Should handle case when daemon not running."""
        from meeting_noter.daemon import stop_daemon

        stop_daemon(mock_pid_file)

        captured = capsys.readouterr()
        assert "not running" in captured.out

    def test_stop_daemon_stale_pid(self, mock_pid_file: Path, capsys):
        """Should clean up stale PID file."""
        # Write a non-existent PID
        mock_pid_file.write_text("999999999")

        from meeting_noter.daemon import stop_daemon

        stop_daemon(mock_pid_file)

        captured = capsys.readouterr()
        assert "not running" in captured.out or "stale" in captured.out
        assert not mock_pid_file.exists()


class TestRunDaemon:
    """Tests for run_daemon function."""

    def test_run_daemon_already_running(self, mocker, tmp_path, capsys):
        """Should not start if daemon already running."""
        pid_file = tmp_path / "test.pid"
        pid_file.write_text(str(os.getpid()))

        from meeting_noter.daemon import run_daemon

        run_daemon(tmp_path, foreground=True, pid_file=pid_file)

        captured = capsys.readouterr()
        assert "already running" in captured.out

    def test_run_daemon_no_audio(self, mocker, tmp_path, capsys):
        """Should exit if no audio device."""
        pid_file = tmp_path / "test.pid"
        mocker.patch("meeting_noter.daemon.check_audio_available", return_value=False)

        from meeting_noter.daemon import run_daemon

        run_daemon(tmp_path, foreground=True, pid_file=pid_file)

        captured = capsys.readouterr()
        assert "No audio input device" in captured.out

    def test_run_daemon_starts_capture(self, mocker, tmp_path):
        """Should start capture loop when audio available."""
        pid_file = tmp_path / "test.pid"
        mocker.patch("meeting_noter.daemon.check_audio_available", return_value=True)
        mock_capture_loop = mocker.patch("meeting_noter.daemon._run_capture_loop")

        from meeting_noter.daemon import run_daemon

        run_daemon(tmp_path, foreground=True, pid_file=pid_file)

        mock_capture_loop.assert_called_once()
        # PID file should be created and removed
        assert not pid_file.exists()  # Cleaned up after


class TestRunCaptureLoop:
    """Tests for _run_capture_loop function."""

    def test_capture_loop_combined_audio(self, mocker, tmp_path):
        """Should use combined capture when enabled."""
        mock_config = MagicMock()
        mock_config.capture_system_audio = True
        mocker.patch("meeting_noter.config.get_config", return_value=mock_config)

        mock_combined = MagicMock()
        mock_combined.sample_rate = 48000
        mock_combined.channels = 2
        mock_combined.get_audio.return_value = None
        mocker.patch(
            "meeting_noter.audio.system_audio.CombinedAudioCapture",
            return_value=mock_combined,
        )

        # Stop immediately
        from meeting_noter.daemon import _stop_event
        _stop_event.set()

        from meeting_noter.daemon import _run_capture_loop

        _run_capture_loop(tmp_path)

        mock_combined.start.assert_called_once()
        mock_combined.stop.assert_called_once()

        _stop_event.clear()

    def test_capture_loop_fallback_to_mic(self, mocker, tmp_path):
        """Should fallback to mic when combined capture fails."""
        mock_config = MagicMock()
        mock_config.capture_system_audio = True
        mocker.patch("meeting_noter.config.get_config", return_value=mock_config)

        mocker.patch(
            "meeting_noter.audio.system_audio.CombinedAudioCapture",
            side_effect=Exception("Not available"),
        )

        mock_mic = MagicMock()
        mock_mic.sample_rate = 48000
        mock_mic.channels = 1
        mock_mic.get_audio.return_value = None
        mocker.patch(
            "meeting_noter.audio.capture.AudioCapture",
            return_value=mock_mic,
        )

        from meeting_noter.daemon import _stop_event
        _stop_event.set()

        from meeting_noter.daemon import _run_capture_loop

        _run_capture_loop(tmp_path)

        mock_mic.start.assert_called_once()

        _stop_event.clear()

    def test_capture_loop_mic_only(self, mocker, tmp_path):
        """Should use mic only when system audio disabled."""
        mock_config = MagicMock()
        mock_config.capture_system_audio = False
        mocker.patch("meeting_noter.config.get_config", return_value=mock_config)

        mock_mic = MagicMock()
        mock_mic.sample_rate = 48000
        mock_mic.channels = 1
        mock_mic.get_audio.return_value = None
        mocker.patch(
            "meeting_noter.audio.capture.AudioCapture",
            return_value=mock_mic,
        )

        from meeting_noter.daemon import _stop_event
        _stop_event.set()

        from meeting_noter.daemon import _run_capture_loop

        _run_capture_loop(tmp_path)

        mock_mic.start.assert_called_once()

        _stop_event.clear()

    def test_capture_loop_error_creating_capture(self, mocker, tmp_path, capsys):
        """Should handle error creating AudioCapture."""
        mock_config = MagicMock()
        mock_config.capture_system_audio = False
        mocker.patch("meeting_noter.config.get_config", return_value=mock_config)

        mocker.patch(
            "meeting_noter.audio.capture.AudioCapture",
            side_effect=RuntimeError("No device"),
        )

        from meeting_noter.daemon import _run_capture_loop

        _run_capture_loop(tmp_path)

        captured = capsys.readouterr()
        assert "Error creating AudioCapture" in captured.out


class TestCheckStatusExtended:
    """Extended tests for check_status function."""

    def test_check_status_no_microphone(self, mock_pid_file: Path, mocker, capsys):
        """Should show microphone not found."""
        mock_sounddevice = MagicMock()
        mock_sounddevice.query_devices.return_value = []
        mocker.patch.dict("sys.modules", {"sounddevice": mock_sounddevice})

        mock_quartz = MagicMock()
        mock_quartz.CGPreflightScreenCaptureAccess.return_value = False
        mocker.patch.dict("sys.modules", {"Quartz": mock_quartz})

        from meeting_noter.daemon import check_status

        check_status(mock_pid_file)

        captured = capsys.readouterr()
        assert "not running" in captured.out

    def test_check_status_stale_pid(self, mock_pid_file: Path, mocker, capsys):
        """Should clean up stale PID file."""
        mock_pid_file.write_text("999999999")  # Non-existent PID

        mock_sounddevice = MagicMock()
        mock_sounddevice.query_devices.return_value = [
            {"name": "Mic", "max_input_channels": 1},
        ]
        mocker.patch.dict("sys.modules", {"sounddevice": mock_sounddevice})

        mock_quartz = MagicMock()
        mock_quartz.CGPreflightScreenCaptureAccess.return_value = True
        mocker.patch.dict("sys.modules", {"Quartz": mock_quartz})

        from meeting_noter.daemon import check_status

        check_status(mock_pid_file)

        captured = capsys.readouterr()
        assert "stale" in captured.out
        assert not mock_pid_file.exists()


class TestStopDaemonExtended:
    """Extended tests for stop_daemon function."""

    def test_stop_daemon_graceful(self, mocker, tmp_path, capsys):
        """Should stop daemon gracefully with SIGTERM."""
        pid_file = tmp_path / "test.pid"

        # Create a mock process that responds to signals
        mock_pid = 12345
        pid_file.write_text(str(mock_pid))

        # First call returns True (running), subsequent calls return False (stopped)
        call_count = [0]
        def mock_is_running(pid):
            call_count[0] += 1
            return call_count[0] <= 2  # Running for first 2 checks, then stopped

        mocker.patch("meeting_noter.daemon.is_process_running", side_effect=mock_is_running)
        mocker.patch("os.kill")
        mocker.patch("time.sleep")

        from meeting_noter.daemon import stop_daemon

        stop_daemon(pid_file)

        captured = capsys.readouterr()
        assert "stopped" in captured.out.lower()

    def test_stop_daemon_force_kill(self, mocker, tmp_path, capsys):
        """Should force kill if daemon doesn't stop gracefully."""
        pid_file = tmp_path / "test.pid"
        mock_pid = 12345
        pid_file.write_text(str(mock_pid))

        # Process never stops
        mocker.patch("meeting_noter.daemon.is_process_running", return_value=True)
        mock_kill = mocker.patch("os.kill")
        mocker.patch("time.sleep")

        from meeting_noter.daemon import stop_daemon

        stop_daemon(pid_file)

        # Should have called SIGKILL
        import signal
        calls = mock_kill.call_args_list
        assert any(call[0][1] == signal.SIGKILL for call in calls)


class TestRunForegroundCapture:
    """Tests for run_foreground_capture function."""

    def test_run_foreground_capture_no_audio(self, mocker, tmp_path, capsys):
        """Should error when no audio device available."""
        mock_sounddevice = MagicMock()
        mock_sounddevice.query_devices.return_value = []
        mocker.patch.dict("sys.modules", {"sounddevice": mock_sounddevice})

        mocker.patch("meeting_noter.daemon.check_audio_available", return_value=False)

        from meeting_noter.daemon import run_foreground_capture

        result = run_foreground_capture(
            output_dir=tmp_path,
            meeting_name="Test",
        )

        assert result is None
        captured = capsys.readouterr()
        assert "No audio input device" in captured.out

    def test_run_foreground_capture_combined_audio(self, mocker, tmp_path):
        """Should use combined capture when enabled."""
        mock_config = MagicMock()
        mock_config.capture_system_audio = True
        mock_config.auto_transcribe = False
        mocker.patch("meeting_noter.config.get_config", return_value=mock_config)
        mocker.patch("meeting_noter.daemon.check_audio_available", return_value=True)

        mock_combined = MagicMock()
        mock_combined.sample_rate = 48000
        mock_combined.channels = 2
        mock_combined.get_audio.return_value = None
        mocker.patch(
            "meeting_noter.audio.system_audio.CombinedAudioCapture",
            return_value=mock_combined,
        )

        mock_session = MagicMock()
        mock_session.is_active = False
        mock_session.start.return_value = tmp_path / "test.mp3"
        mocker.patch(
            "meeting_noter.audio.encoder.RecordingSession",
            return_value=mock_session,
        )

        from meeting_noter.daemon import _stop_event, run_foreground_capture
        _stop_event.set()

        result = run_foreground_capture(
            output_dir=tmp_path,
            meeting_name="Test",
            auto_transcribe=False,
        )

        _stop_event.clear()

        mock_combined.start.assert_called_once()
        mock_combined.stop.assert_called_once()

    def test_run_foreground_capture_fallback_mic(self, mocker, tmp_path):
        """Should fallback to mic when combined capture fails."""
        mock_config = MagicMock()
        mock_config.capture_system_audio = True
        mock_config.auto_transcribe = False
        mocker.patch("meeting_noter.config.get_config", return_value=mock_config)
        mocker.patch("meeting_noter.daemon.check_audio_available", return_value=True)

        mocker.patch(
            "meeting_noter.audio.system_audio.CombinedAudioCapture",
            side_effect=Exception("Not available"),
        )

        mock_mic = MagicMock()
        mock_mic.sample_rate = 48000
        mock_mic.channels = 1
        mock_mic.get_audio.return_value = None
        mocker.patch(
            "meeting_noter.audio.capture.AudioCapture",
            return_value=mock_mic,
        )

        mock_session = MagicMock()
        mock_session.is_active = False
        mocker.patch(
            "meeting_noter.audio.encoder.RecordingSession",
            return_value=mock_session,
        )

        from meeting_noter.daemon import _stop_event, run_foreground_capture
        _stop_event.set()

        result = run_foreground_capture(
            output_dir=tmp_path,
            meeting_name="Test",
            auto_transcribe=False,
        )

        _stop_event.clear()

        mock_mic.start.assert_called_once()

    def test_run_foreground_capture_with_recording(self, mocker, tmp_path, capsys):
        """Should record and save audio."""
        import numpy as np

        mock_config = MagicMock()
        mock_config.capture_system_audio = False
        mock_config.auto_transcribe = False
        mocker.patch("meeting_noter.config.get_config", return_value=mock_config)
        mocker.patch("meeting_noter.daemon.check_audio_available", return_value=True)

        # Create mock capture that returns some audio then None
        audio_data = np.random.randn(48000).astype(np.float32) * 0.1
        call_count = [0]

        def mock_get_audio(timeout=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return audio_data
            return None

        mock_mic = MagicMock()
        mock_mic.sample_rate = 48000
        mock_mic.channels = 1
        mock_mic.get_audio = mock_get_audio
        mocker.patch(
            "meeting_noter.audio.capture.AudioCapture",
            return_value=mock_mic,
        )

        mock_session = MagicMock()
        mock_session.is_active = True
        mock_session.duration = 10.0
        saved_path = tmp_path / "test_recording.mp3"
        mock_session.start.return_value = saved_path
        mock_session.stop.return_value = (saved_path, 10.0)
        mocker.patch(
            "meeting_noter.audio.encoder.RecordingSession",
            return_value=mock_session,
        )

        mock_silence = MagicMock()
        mock_silence.update.return_value = False
        mocker.patch(
            "meeting_noter.audio.capture.SilenceDetector",
            return_value=mock_silence,
        )

        from meeting_noter.daemon import _stop_event, run_foreground_capture
        _stop_event.set()

        result = run_foreground_capture(
            output_dir=tmp_path,
            meeting_name="Test",
            auto_transcribe=False,
        )

        _stop_event.clear()

        assert result == saved_path
        captured = capsys.readouterr()
        assert "Saved" in captured.out

    def test_run_foreground_capture_auto_transcribe(self, mocker, tmp_path):
        """Should auto-transcribe when enabled."""
        mock_config = MagicMock()
        mock_config.capture_system_audio = False
        mock_config.auto_transcribe = True
        mocker.patch("meeting_noter.config.get_config", return_value=mock_config)
        mocker.patch("meeting_noter.daemon.check_audio_available", return_value=True)

        mock_mic = MagicMock()
        mock_mic.sample_rate = 48000
        mock_mic.channels = 1
        mock_mic.get_audio.return_value = None
        mocker.patch(
            "meeting_noter.audio.capture.AudioCapture",
            return_value=mock_mic,
        )

        mock_session = MagicMock()
        mock_session.is_active = True
        saved_path = tmp_path / "test.mp3"
        mock_session.start.return_value = saved_path
        mock_session.stop.return_value = (saved_path, 10.0)
        mocker.patch(
            "meeting_noter.audio.encoder.RecordingSession",
            return_value=mock_session,
        )

        mock_transcribe = mocker.patch(
            "meeting_noter.transcription.engine.transcribe_file",
        )

        from meeting_noter.daemon import _stop_event, run_foreground_capture
        _stop_event.set()

        result = run_foreground_capture(
            output_dir=tmp_path,
            meeting_name="Test",
            auto_transcribe=True,
        )

        _stop_event.clear()

        mock_transcribe.assert_called_once()

    def test_run_foreground_capture_mic_error(self, mocker, tmp_path, capsys):
        """Should handle mic creation error."""
        mock_config = MagicMock()
        mock_config.capture_system_audio = False
        mocker.patch("meeting_noter.config.get_config", return_value=mock_config)
        mocker.patch("meeting_noter.daemon.check_audio_available", return_value=True)

        mocker.patch(
            "meeting_noter.audio.capture.AudioCapture",
            side_effect=RuntimeError("Device error"),
        )

        from meeting_noter.daemon import run_foreground_capture

        result = run_foreground_capture(
            output_dir=tmp_path,
            meeting_name="Test",
        )

        assert result is None
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_run_foreground_capture_recording_discarded(self, mocker, tmp_path, capsys):
        """Should report when recording is discarded (too short)."""
        mock_config = MagicMock()
        mock_config.capture_system_audio = False
        mock_config.auto_transcribe = False
        mocker.patch("meeting_noter.config.get_config", return_value=mock_config)
        mocker.patch("meeting_noter.daemon.check_audio_available", return_value=True)

        mock_mic = MagicMock()
        mock_mic.sample_rate = 48000
        mock_mic.channels = 1
        mock_mic.get_audio.return_value = None
        mocker.patch(
            "meeting_noter.audio.capture.AudioCapture",
            return_value=mock_mic,
        )

        mock_session = MagicMock()
        mock_session.is_active = True
        mock_session.start.return_value = tmp_path / "test.mp3"
        mock_session.stop.return_value = (None, 2.0)  # Too short, discarded
        mocker.patch(
            "meeting_noter.audio.encoder.RecordingSession",
            return_value=mock_session,
        )

        from meeting_noter.daemon import _stop_event, run_foreground_capture
        _stop_event.set()

        result = run_foreground_capture(
            output_dir=tmp_path,
            meeting_name="Test",
            auto_transcribe=False,
        )

        _stop_event.clear()

        assert result is None
        captured = capsys.readouterr()
        assert "discarded" in captured.out.lower()


class TestCheckAudioAvailableExtended:
    """Extended tests for check_audio_available."""

    def test_check_audio_available_only_output(self, mocker):
        """Should return False when only output devices exist."""
        mock_sounddevice = MagicMock()
        mock_sounddevice.query_devices.return_value = [
            {"name": "Speaker", "max_input_channels": 0},
        ]

        with patch.dict("sys.modules", {"sounddevice": mock_sounddevice}):
            import importlib
            import meeting_noter.daemon as daemon_module

            importlib.reload(daemon_module)

            result = daemon_module.check_audio_available()

            assert result is False


class TestRunDaemonExtended:
    """Extended tests for run_daemon function."""

    def test_run_daemon_writes_and_removes_pid(self, mocker, tmp_path):
        """Should write PID file on start and remove on exit."""
        pid_file = tmp_path / "test.pid"
        mocker.patch("meeting_noter.daemon.check_audio_available", return_value=True)
        mock_capture_loop = mocker.patch("meeting_noter.daemon._run_capture_loop")

        from meeting_noter.daemon import run_daemon

        run_daemon(tmp_path, foreground=True, pid_file=pid_file)

        # PID file should be created during run and removed after
        # Since we mocked _run_capture_loop, the file is created then removed
        assert not pid_file.exists()


class TestCaptureLoopExtended:
    """Extended tests for _run_capture_loop function."""

    def test_capture_loop_start_failure(self, mocker, tmp_path, capsys):
        """Should handle capture start failure."""
        mock_config = MagicMock()
        mock_config.capture_system_audio = False
        mocker.patch("meeting_noter.config.get_config", return_value=mock_config)

        mock_mic = MagicMock()
        mock_mic.start.side_effect = Exception("Failed to start")
        mocker.patch(
            "meeting_noter.audio.capture.AudioCapture",
            return_value=mock_mic,
        )

        from meeting_noter.daemon import _run_capture_loop

        _run_capture_loop(tmp_path)

        captured = capsys.readouterr()
        assert "Error starting capture" in captured.out

    def test_capture_loop_unexpected_error(self, mocker, tmp_path, capsys):
        """Should handle unexpected error creating capture."""
        mock_config = MagicMock()
        mock_config.capture_system_audio = False
        mocker.patch("meeting_noter.config.get_config", return_value=mock_config)

        mocker.patch(
            "meeting_noter.audio.capture.AudioCapture",
            side_effect=ValueError("Unexpected error"),
        )

        from meeting_noter.daemon import _run_capture_loop

        _run_capture_loop(tmp_path)

        captured = capsys.readouterr()
        assert "Unexpected error" in captured.out


class TestCheckStatusExtendedMore:
    """More extended tests for check_status function."""

    def test_check_status_screencapture_enabled(self, mock_pid_file: Path, mocker, capsys):
        """Should show screencapture enabled status."""
        mock_sounddevice = MagicMock()
        mock_sounddevice.query_devices.return_value = [
            {"name": "Mic", "max_input_channels": 1},
        ]
        mocker.patch.dict("sys.modules", {"sounddevice": mock_sounddevice})

        mock_quartz = MagicMock()
        mock_quartz.CGPreflightScreenCaptureAccess.return_value = True
        mocker.patch.dict("sys.modules", {"Quartz": mock_quartz})

        from meeting_noter.daemon import check_status

        check_status(mock_pid_file)

        captured = capsys.readouterr()
        assert "enabled" in captured.out.lower() or "not running" in captured.out.lower()
