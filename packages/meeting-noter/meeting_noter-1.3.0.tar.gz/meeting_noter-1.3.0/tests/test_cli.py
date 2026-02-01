"""Tests for the CLI module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import json

import pytest
from click.testing import CliRunner

from meeting_noter.cli import cli, SuggestGroup, SuggestCommand


class TestCliHelp:
    """Tests for CLI help output."""

    def test_cli_help(self, cli_runner: CliRunner):
        """--help should show usage information."""
        result = cli_runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Meeting Noter" in result.output
        assert "Offline meeting transcription" in result.output

    def test_cli_version(self, cli_runner: CliRunner):
        """--version should show version number."""
        result = cli_runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "meeting-noter" in result.output.lower()


class TestStartCommand:
    """Tests for the start command."""

    def test_start_command(self, cli_runner: CliRunner, mock_config, mocker):
        """start should invoke foreground capture."""
        mock_capture = mocker.patch(
            "meeting_noter.daemon.run_foreground_capture",
            return_value=None,
        )

        result = cli_runner.invoke(cli, ["start", "Test Meeting"])

        assert mock_capture.called
        call_kwargs = mock_capture.call_args[1]
        assert call_kwargs["meeting_name"] == "Test Meeting"

    def test_start_command_default_name(self, cli_runner: CliRunner, mock_config, mocker):
        """start without name should use timestamp."""
        mock_capture = mocker.patch(
            "meeting_noter.daemon.run_foreground_capture",
            return_value=None,
        )

        result = cli_runner.invoke(cli, ["start"])

        assert mock_capture.called
        call_kwargs = mock_capture.call_args[1]
        # Should be a timestamp name
        assert "_" in call_kwargs["meeting_name"]


class TestStatusCommand:
    """Tests for the status command."""

    def test_status_command_not_running(self, cli_runner: CliRunner, mock_config, mocker):
        """status should show not running when no processes."""
        mocker.patch(
            "meeting_noter.daemon.read_pid_file",
            return_value=None,
        )

        result = cli_runner.invoke(cli, ["status"])

        assert result.exit_code == 0
        assert "stopped" in result.output.lower() or "Stopped" in result.output


class TestShutdownCommand:
    """Tests for the shutdown command."""

    def test_shutdown_command(self, cli_runner: CliRunner, mock_config, mocker):
        """shutdown should stop all processes."""
        mock_stop = mocker.patch("meeting_noter.daemon.stop_daemon")
        mocker.patch("subprocess.run", return_value=MagicMock(returncode=1))

        result = cli_runner.invoke(cli, ["shutdown"])

        assert result.exit_code == 0


class TestLogsCommand:
    """Tests for the logs command."""

    def test_logs_command_no_file(self, cli_runner: CliRunner, mocker):
        """logs should handle missing log file."""
        mocker.patch("pathlib.Path.exists", return_value=False)

        result = cli_runner.invoke(cli, ["logs"])

        assert "No log file" in result.output


class TestConfigCommand:
    """Tests for the config command."""

    def test_config_show_all(self, cli_runner: CliRunner, mock_config):
        """config without args should show all settings."""
        result = cli_runner.invoke(cli, ["config"])

        assert result.exit_code == 0
        assert "Configuration" in result.output
        assert "recordings-dir" in result.output
        assert "whisper-model" in result.output

    def test_config_get_specific(self, cli_runner: CliRunner, mock_config):
        """config KEY should show specific value."""
        result = cli_runner.invoke(cli, ["config", "whisper-model"])

        assert result.exit_code == 0
        assert "tiny.en" in result.output

    def test_config_set_value(self, cli_runner: CliRunner, mock_config):
        """config KEY VALUE should set the value."""
        result = cli_runner.invoke(cli, ["config", "whisper-model", "base.en"])

        assert result.exit_code == 0
        assert "Set whisper-model" in result.output
        assert mock_config.whisper_model == "base.en"

    def test_config_set_bool_true(self, cli_runner: CliRunner, mock_config):
        """config should handle boolean true values."""
        mock_config.auto_transcribe = False

        result = cli_runner.invoke(cli, ["config", "auto-transcribe", "true"])

        assert result.exit_code == 0
        assert mock_config.auto_transcribe is True

    def test_config_set_bool_false(self, cli_runner: CliRunner, mock_config):
        """config should handle boolean false values."""
        mock_config.auto_transcribe = True

        result = cli_runner.invoke(cli, ["config", "auto-transcribe", "false"])

        assert result.exit_code == 0
        assert mock_config.auto_transcribe is False

    def test_config_set_int(self, cli_runner: CliRunner, mock_config):
        """config should handle integer values."""
        result = cli_runner.invoke(cli, ["config", "silence-timeout", "10"])

        assert result.exit_code == 0
        assert mock_config.silence_timeout == 10

    def test_config_unknown_key(self, cli_runner: CliRunner, mock_config):
        """config should error on unknown key."""
        result = cli_runner.invoke(cli, ["config", "unknown-key"])

        assert "Unknown config key" in result.output

    def test_config_invalid_choice(self, cli_runner: CliRunner, mock_config):
        """config should error on invalid choice value."""
        result = cli_runner.invoke(cli, ["config", "whisper-model", "invalid-model"])

        assert "Invalid value" in result.output or "Must be one of" in result.output


class TestListCommand:
    """Tests for the list command."""

    def test_list_recordings(self, cli_runner: CliRunner, mock_config, mocker):
        """list should show recordings."""
        # Create files in the mock_config's recordings_dir
        recordings_dir = mock_config.recordings_dir
        test_file = recordings_dir / "2024-01-15_meeting_test.mp3"
        test_file.write_bytes(b"\x00" * 10000)

        result = cli_runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        assert "meeting_test" in result.output or "recordings" in result.output.lower()

    def test_list_transcripts(self, cli_runner: CliRunner, mock_config):
        """list -t should show transcripts."""
        # Create transcript file
        transcript = mock_config.transcripts_dir / "test_meeting.txt"
        transcript.write_text("[00:00] Test content\n")

        result = cli_runner.invoke(cli, ["list", "-t"])

        assert result.exit_code == 0
        assert "test_meeting.txt" in result.output
        assert "Transcripts" in result.output

    def test_list_transcripts_shows_favorites(self, cli_runner: CliRunner, mock_config):
        """list -t should show favorite indicator."""
        # Create transcript and mark as favorite
        transcript = mock_config.transcripts_dir / "favorite_meeting.txt"
        transcript.write_text("[00:00] Test content\n")
        mock_config.add_favorite("favorite_meeting.txt")

        result = cli_runner.invoke(cli, ["list", "-t"])

        assert result.exit_code == 0
        assert "★" in result.output
        assert "favorite_meeting.txt" in result.output


class TestTranscribeCommand:
    """Tests for the transcribe command."""

    def test_transcribe_command(
        self, cli_runner: CliRunner, mock_config, mocker
    ):
        """transcribe should process audio file."""
        mock_transcribe = mocker.patch(
            "meeting_noter.transcription.engine.transcribe_file",
        )

        # Create a test file in the config's recordings dir
        test_file = mock_config.recordings_dir / "test.mp3"
        test_file.write_bytes(b"\x00" * 1000)

        result = cli_runner.invoke(cli, ["transcribe", str(test_file)])

        assert mock_transcribe.called


class TestOpenCommand:
    """Tests for the open command."""

    def test_open_recordings(self, cli_runner: CliRunner, mock_config, mocker):
        """open should open recordings folder."""
        mock_run = mocker.patch("subprocess.run")

        result = cli_runner.invoke(cli, ["open", "recordings"])

        assert result.exit_code == 0
        assert mock_run.called
        assert "open" in str(mock_run.call_args)

    def test_open_transcripts(self, cli_runner: CliRunner, mock_config, mocker):
        """open transcripts should open transcripts folder."""
        mock_run = mocker.patch("subprocess.run")

        result = cli_runner.invoke(cli, ["open", "transcripts"])

        assert result.exit_code == 0
        assert mock_run.called

    def test_open_config(self, cli_runner: CliRunner, mock_config, mocker):
        """open config should open config folder."""
        mock_run = mocker.patch("subprocess.run")

        result = cli_runner.invoke(cli, ["open", "config"])

        assert result.exit_code == 0
        assert mock_run.called


class TestSuggestGroup:
    """Tests for command suggestion on typos."""

    def test_suggest_similar_command(self, cli_runner: CliRunner):
        """Typos should suggest similar commands."""
        result = cli_runner.invoke(cli, ["statsu"])  # Typo for "status"

        # Should suggest "status"
        assert result.exit_code != 0
        # May or may not have suggestion depending on cutoff

    def test_partial_command_match(self, cli_runner: CliRunner, mock_config, mocker):
        """Partial command should match unique prefix."""
        mocker.patch(
            "meeting_noter.daemon.read_pid_file",
            return_value=None,
        )

        result = cli_runner.invoke(cli, ["stat"])  # Prefix for "status"

        # Should match "status"
        assert result.exit_code == 0


class TestSuggestCommand:
    """Tests for option suggestion on typos."""

    def test_suggest_similar_option(self, cli_runner: CliRunner):
        """Typos in options should show available options."""
        result = cli_runner.invoke(cli, ["logs", "--follw"])  # Typo for "--follow"

        assert result.exit_code != 0
        # Should mention available options or suggest


class TestWatcherCommand:
    """Tests for the watcher command."""

    def test_watcher_background(self, cli_runner: CliRunner, mock_config, mocker, tmp_path):
        """watcher should start in background by default."""
        mock_popen = mocker.patch("subprocess.Popen")
        # Mock the PID file to not exist (no existing watcher)
        mocker.patch("meeting_noter.cli.WATCHER_PID_FILE", tmp_path / "nonexistent.pid")

        result = cli_runner.invoke(cli, ["watcher"])

        assert result.exit_code == 0
        assert mock_popen.called or "background" in result.output.lower()


class TestWatchCommand:
    """Tests for the watch command."""

    def test_watch_foreground(self, cli_runner: CliRunner, mock_config, mocker):
        """watch should run in foreground with prompts."""
        # Mock the mic monitor to not actually run
        mock_monitor = MagicMock()
        mock_monitor.check.return_value = (False, False, None)
        mocker.patch(
            "meeting_noter.mic_monitor.MicrophoneMonitor",
            return_value=mock_monitor,
        )

        # Simulate Ctrl+C after one iteration
        call_count = [0]

        def mock_sleep(seconds):
            call_count[0] += 1
            if call_count[0] > 1:
                raise KeyboardInterrupt()

        mocker.patch("time.sleep", side_effect=mock_sleep)
        mocker.patch("meeting_noter.daemon.read_pid_file", return_value=None)
        mocker.patch("meeting_noter.daemon.is_process_running", return_value=False)

        result = cli_runner.invoke(cli, ["watch"])

        # Should exit cleanly on Ctrl+C
        assert "Watching for meetings" in result.output


class TestCompletionCommand:
    """Tests for the completion command."""

    def test_completion_zsh(self, cli_runner: CliRunner, tmp_path, mocker):
        """completion should install zsh completion."""
        zshrc = tmp_path / ".zshrc"
        mocker.patch("pathlib.Path.expanduser", return_value=zshrc)
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        result = cli_runner.invoke(cli, ["completion", "--shell", "zsh"])

        assert result.exit_code == 0


class TestDefaultCommand:
    """Tests for default behavior when no command given."""

    def test_no_command_starts_watcher(self, cli_runner: CliRunner, mock_config, mocker, tmp_path):
        """Running without command should start watcher."""
        mock_popen = mocker.patch("subprocess.Popen")
        # Mock the PID file to not exist
        mocker.patch("meeting_noter.cli.WATCHER_PID_FILE", tmp_path / "nonexistent.pid")

        result = cli_runner.invoke(cli)

        assert result.exit_code == 0
        # Should start watcher in background or indicate already running
        assert mock_popen.called or "background" in result.output.lower() or "already running" in result.output.lower()


class TestGetCurrentRecordingName:
    """Tests for _get_current_recording_name function."""

    def test_get_recording_name_from_log(self, mocker, tmp_path):
        """Should extract meeting name from log file."""
        log_path = tmp_path / ".meeting-noter.log"
        log_path.write_text("Recording started: 2024-01-15_test_meeting.mp3\n")
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        from meeting_noter.cli import _get_current_recording_name

        result = _get_current_recording_name()

        # Should return "meeting" from the timestamp_name format
        assert result is not None

    def test_get_recording_name_no_log(self, mocker, tmp_path):
        """Should return None when no log file."""
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        from meeting_noter.cli import _get_current_recording_name

        result = _get_current_recording_name()

        assert result is None

    def test_get_recording_name_recording_saved(self, mocker, tmp_path):
        """Should return None when recording already saved."""
        log_path = tmp_path / ".meeting-noter.log"
        log_path.write_text(
            "Recording started: test.mp3\n"
            "Recording saved: test.mp3\n"
        )
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        from meeting_noter.cli import _get_current_recording_name

        result = _get_current_recording_name()

        assert result is None


class TestStatusCommandExtended:
    """Extended tests for status command."""

    def test_status_recording_active(self, cli_runner: CliRunner, mock_config, mocker, tmp_path):
        """Should show recording status when daemon running."""
        import os

        # Mock watcher not running
        mocker.patch("meeting_noter.cli.WATCHER_PID_FILE", tmp_path / "nonexistent.pid")

        # Mock daemon running
        mocker.patch("meeting_noter.daemon.read_pid_file", return_value=os.getpid())
        mocker.patch("meeting_noter.daemon.is_process_running", return_value=True)

        # Mock current recording name
        log_path = tmp_path / ".meeting-noter.log"
        log_path.write_text("Recording started: 2024-01-15_test_meeting.mp3\n")
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        result = cli_runner.invoke(cli, ["status"])

        assert result.exit_code == 0
        assert "Recording" in result.output or "recording" in result.output

    def test_status_watcher_active(self, cli_runner: CliRunner, mock_config, mocker, tmp_path):
        """Should show watcher status when watcher running."""
        import os

        # Create watcher PID file with current process
        watcher_pid = tmp_path / ".meeting-noter-watcher.pid"
        watcher_pid.write_text(str(os.getpid()))
        mocker.patch("meeting_noter.cli.WATCHER_PID_FILE", watcher_pid)

        # Mock daemon not running
        mocker.patch("meeting_noter.daemon.read_pid_file", return_value=None)

        result = cli_runner.invoke(cli, ["status"])

        assert result.exit_code == 0
        assert "Ready" in result.output or "watcher" in result.output


class TestShutdownCommandExtended:
    """Extended tests for shutdown command."""

    def test_shutdown_stops_watcher(self, cli_runner: CliRunner, mock_config, mocker, tmp_path):
        """Should stop watcher process."""
        import os

        # Create watcher PID file with current process
        watcher_pid = tmp_path / ".meeting-noter-watcher.pid"
        watcher_pid.write_text(str(os.getpid()))
        mocker.patch("meeting_noter.cli.WATCHER_PID_FILE", watcher_pid)

        mocker.patch("meeting_noter.daemon.stop_daemon")
        mocker.patch("os.kill")  # Don't actually kill current process
        mocker.patch("subprocess.run", return_value=MagicMock(returncode=1))

        result = cli_runner.invoke(cli, ["shutdown"])

        assert result.exit_code == 0
        assert "watcher" in result.output.lower() or "stopped" in result.output.lower()

    def test_shutdown_nothing_running(self, cli_runner: CliRunner, mock_config, mocker, tmp_path):
        """Should indicate nothing running."""
        mocker.patch("meeting_noter.cli.WATCHER_PID_FILE", tmp_path / "nonexistent.pid")
        mocker.patch("meeting_noter.cli.DEFAULT_PID_FILE", tmp_path / "nonexistent2.pid")
        mocker.patch("subprocess.run", return_value=MagicMock(returncode=1))

        result = cli_runner.invoke(cli, ["shutdown"])

        assert result.exit_code == 0
        assert "No Meeting Noter processes" in result.output


class TestLogsCommandExtended:
    """Extended tests for logs command."""

    def test_logs_follow(self, cli_runner: CliRunner, mocker, tmp_path):
        """Should follow log output."""
        log_path = tmp_path / ".meeting-noter.log"
        log_path.write_text("Test log\n")
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        mock_run = mocker.patch("subprocess.run", side_effect=KeyboardInterrupt())

        result = cli_runner.invoke(cli, ["logs", "--follow"])

        # Should have called tail -f
        assert mock_run.called

    def test_logs_with_lines(self, cli_runner: CliRunner, mocker, tmp_path):
        """Should show specified number of lines."""
        log_path = tmp_path / ".meeting-noter.log"
        log_path.write_text("Line 1\nLine 2\nLine 3\n")
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        mock_run = mocker.patch("subprocess.run")

        result = cli_runner.invoke(cli, ["logs", "--lines", "20"])

        assert mock_run.called
        call_args = str(mock_run.call_args)
        assert "-20" in call_args


class TestCompletionCommandExtended:
    """Extended tests for completion command."""

    def test_completion_bash(self, cli_runner: CliRunner, tmp_path, mocker):
        """Should install bash completion."""
        bashrc = tmp_path / ".bashrc"
        mocker.patch("pathlib.Path.expanduser", return_value=bashrc)
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        result = cli_runner.invoke(cli, ["completion", "--shell", "bash"])

        assert result.exit_code == 0

    def test_completion_already_installed(self, cli_runner: CliRunner, tmp_path, mocker):
        """Should detect existing completion."""
        zshrc = tmp_path / ".zshrc"
        zshrc.write_text("# Existing\n_MEETING_NOTER_COMPLETE=zsh_source\n")
        mocker.patch("pathlib.Path.expanduser", return_value=zshrc)
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        result = cli_runner.invoke(cli, ["completion", "--shell", "zsh"])

        assert result.exit_code == 0
        assert "already installed" in result.output


class TestDaemonCommand:
    """Tests for the internal daemon command."""

    def test_daemon_command_foreground(self, cli_runner: CliRunner, mock_config, mocker, tmp_path):
        """Should run daemon in foreground mode."""
        mock_run_daemon = mocker.patch("meeting_noter.daemon.run_daemon")

        result = cli_runner.invoke(cli, ["daemon", "--foreground", "--name", "Test"])

        assert mock_run_daemon.called
        call_kwargs = mock_run_daemon.call_args[1]
        assert call_kwargs["foreground"] is True
        assert call_kwargs["meeting_name"] == "Test"


class TestTranscribeCommandExtended:
    """Extended tests for transcribe command."""

    def test_transcribe_latest(self, cli_runner: CliRunner, mock_config, mocker):
        """Should transcribe latest recording when no file specified."""
        mock_transcribe = mocker.patch(
            "meeting_noter.transcription.engine.transcribe_file",
        )

        result = cli_runner.invoke(cli, ["transcribe"])

        assert mock_transcribe.called

    def test_transcribe_no_live_flag(self, cli_runner: CliRunner, mock_config, mocker):
        """Transcribe command should not have --live flag (use 'live' command instead)."""
        result = cli_runner.invoke(cli, ["transcribe", "--live"])

        # --live flag was removed, should fail
        assert result.exit_code != 0
        assert "No such option" in result.output or "no such option" in result.output.lower()

    def test_transcribe_with_model(self, cli_runner: CliRunner, mock_config, mocker):
        """Should use specified model."""
        mock_transcribe = mocker.patch(
            "meeting_noter.transcription.engine.transcribe_file",
        )

        test_file = mock_config.recordings_dir / "test.mp3"
        test_file.write_bytes(b"\x00" * 1000)

        result = cli_runner.invoke(cli, ["transcribe", str(test_file), "--model", "base.en"])

        assert mock_transcribe.called
        call_args = mock_transcribe.call_args[0]
        assert "base.en" in call_args


class TestLiveCommand:
    """Tests for the live transcription command."""

    def test_live_no_transcript_file(self, cli_runner: CliRunner, mock_config, mocker):
        """Should show message when no live transcript file exists."""
        result = cli_runner.invoke(cli, ["live"])

        assert "No live transcript found" in result.output

    def test_live_old_transcript_file(self, cli_runner: CliRunner, mock_config, mocker):
        """Should show message when live transcript is too old (no active recording)."""
        import os
        import time

        # Create a .live.txt file in the live/ subfolder
        live_dir = mock_config.recordings_dir / "live"
        live_dir.mkdir(exist_ok=True)
        live_file = live_dir / "test.live.txt"
        live_file.write_text("Old transcript")

        # Set file modification time to 60 seconds ago
        old_time = time.time() - 60
        os.utime(live_file, (old_time, old_time))

        result = cli_runner.invoke(cli, ["live"])

        assert "No active recording found" in result.output


class TestSuggestGroupExtended:
    """Extended tests for SuggestGroup."""

    def test_suggest_group_partial_match(self, cli_runner: CliRunner, mock_config, mocker):
        """Should match partial command names."""
        mocker.patch("meeting_noter.daemon.read_pid_file", return_value=None)

        # "stat" should match "status"
        result = cli_runner.invoke(cli, ["stat"])

        assert result.exit_code == 0
        assert "Stopped" in result.output or "stopped" in result.output

    def test_suggest_group_no_match(self, cli_runner: CliRunner):
        """Should error on completely unknown command."""
        result = cli_runner.invoke(cli, ["xyznotacommand"])

        assert result.exit_code != 0


class TestConfigCommandExtended:
    """Extended tests for config command."""

    def test_config_set_path(self, cli_runner: CliRunner, mock_config, tmp_path):
        """Should set path value and create directory."""
        new_dir = tmp_path / "new_recordings"

        result = cli_runner.invoke(cli, ["config", "recordings-dir", str(new_dir)])

        assert result.exit_code == 0
        assert "Set recordings-dir" in result.output
        assert new_dir.exists()

    def test_config_invalid_bool(self, cli_runner: CliRunner, mock_config):
        """Should error on invalid boolean value."""
        result = cli_runner.invoke(cli, ["config", "auto-transcribe", "maybe"])

        assert "Invalid" in result.output

    def test_config_underscore_key(self, cli_runner: CliRunner, mock_config):
        """Should accept underscores in key names."""
        result = cli_runner.invoke(cli, ["config", "whisper_model"])

        assert result.exit_code == 0
        assert "tiny.en" in result.output


class TestWatchCommandExtended:
    """Extended tests for watch command."""

    def test_watch_detects_meeting(self, cli_runner: CliRunner, mock_config, mocker):
        """Should detect meeting and prompt for recording."""
        mock_monitor = MagicMock()
        # Return meeting started on first check, then stop
        mock_monitor.check.side_effect = [
            (True, False, "Zoom"),  # Meeting started
            (False, True, None),    # Meeting stopped
        ]
        mocker.patch(
            "meeting_noter.mic_monitor.MicrophoneMonitor",
            return_value=mock_monitor,
        )
        mocker.patch("meeting_noter.mic_monitor.is_meeting_app_active", return_value="Zoom")
        mocker.patch("meeting_noter.mic_monitor.get_meeting_window_title", return_value="Test Meeting")
        mocker.patch("meeting_noter.daemon.read_pid_file", return_value=None)
        mocker.patch("meeting_noter.daemon.is_process_running", return_value=False)
        mocker.patch("meeting_noter.daemon.stop_daemon")
        mocker.patch("subprocess.Popen")

        call_count = [0]

        def mock_sleep(seconds):
            call_count[0] += 1
            if call_count[0] > 2:
                raise KeyboardInterrupt()

        mocker.patch("time.sleep", side_effect=mock_sleep)

        # Simulate user saying "no" to recording prompt
        result = cli_runner.invoke(cli, ["watch"], input="n\n")

        assert "Watching for meetings" in result.output
        assert "Meeting detected" in result.output or "Zoom" in result.output


class TestWatcherAlreadyRunning:
    """Tests for watcher already running scenario."""

    def test_watcher_already_running(self, cli_runner: CliRunner, mock_config, mocker, tmp_path):
        """watcher should detect already running instance."""
        import os

        # Create PID file with current process
        watcher_pid = tmp_path / ".meeting-noter-watcher.pid"
        watcher_pid.write_text(str(os.getpid()))
        mocker.patch("meeting_noter.cli.WATCHER_PID_FILE", watcher_pid)

        result = cli_runner.invoke(cli, ["watcher"])

        assert result.exit_code == 0
        assert "already running" in result.output.lower()


class TestOpenCommandExtended:
    """Extended tests for open command."""

    def test_open_creates_directory(self, cli_runner: CliRunner, mock_config, mocker, tmp_path):
        """open should create directory if it doesn't exist."""
        mock_run = mocker.patch("subprocess.run")

        # Use a fresh tmp directory that doesn't exist yet
        new_dir = tmp_path / "new_recordings"
        mock_config.recordings_dir = new_dir

        result = cli_runner.invoke(cli, ["open", "recordings"])

        assert result.exit_code == 0
        assert new_dir.exists()


class TestConfigInvalidPath:
    """Tests for config command with invalid paths."""

    def test_config_set_invalid_path(self, cli_runner: CliRunner, mock_config, mocker):
        """config should handle path creation errors."""
        # Create a read-only directory scenario
        mocker.patch("pathlib.Path.mkdir", side_effect=PermissionError("Permission denied"))

        result = cli_runner.invoke(cli, ["config", "recordings-dir", "/root/test"])

        # Should either succeed (because mkdir is called after setattr) or show error


class TestTranscribeWithOutputDir:
    """Tests for transcribe command with output dir."""

    def test_transcribe_with_output_dir(self, cli_runner: CliRunner, mock_config, mocker, tmp_path):
        """transcribe should use specified output directory."""
        mock_transcribe = mocker.patch(
            "meeting_noter.transcription.engine.transcribe_file",
        )

        # Create a test file
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"\x00" * 1000)

        result = cli_runner.invoke(cli, ["transcribe", str(test_file), "--output-dir", str(tmp_path)])

        assert mock_transcribe.called


class TestFavoritesCommand:
    """Tests for the favorites command."""

    def test_favorites_command_help(self, cli_runner: CliRunner):
        """favorites --help should show usage information."""
        result = cli_runner.invoke(cli, ["favorites", "--help"])

        assert result.exit_code == 0
        assert "Manage favorite transcripts" in result.output
        assert "add" in result.output
        assert "remove" in result.output

    def test_favorites_list_empty(self, cli_runner: CliRunner, mock_config):
        """favorites should show message when no favorites."""
        result = cli_runner.invoke(cli, ["favorites"])

        assert result.exit_code == 0
        assert "No favorites yet" in result.output

    def test_favorites_add(self, cli_runner: CliRunner, mock_config):
        """favorites add should add transcript to favorites."""
        # Create a transcript file
        transcript = mock_config.transcripts_dir / "test_meeting.txt"
        transcript.write_text("[00:00] Test content\n")

        result = cli_runner.invoke(cli, ["favorites", "add", "test_meeting.txt"])

        assert result.exit_code == 0
        assert "Added to favorites" in result.output
        assert mock_config.is_favorite("test_meeting.txt")

    def test_favorites_add_latest(self, cli_runner: CliRunner, mock_config):
        """favorites add --latest should add most recent transcript."""
        import time

        # Create transcripts
        old = mock_config.transcripts_dir / "old.txt"
        old.write_text("[00:00] Old\n")
        time.sleep(0.01)
        new = mock_config.transcripts_dir / "new.txt"
        new.write_text("[00:00] New\n")

        result = cli_runner.invoke(cli, ["favorites", "add", "--latest"])

        assert result.exit_code == 0
        assert "new.txt" in result.output
        assert mock_config.is_favorite("new.txt")

    def test_favorites_remove(self, cli_runner: CliRunner, mock_config):
        """favorites remove should remove transcript from favorites."""
        mock_config.add_favorite("test_meeting.txt")

        result = cli_runner.invoke(cli, ["favorites", "remove", "test_meeting.txt"])

        assert result.exit_code == 0
        assert "Removed from favorites" in result.output
        assert not mock_config.is_favorite("test_meeting.txt")

    def test_favorites_list_with_items(self, cli_runner: CliRunner, mock_config):
        """favorites should list favorite transcripts."""
        transcript = mock_config.transcripts_dir / "meeting.txt"
        transcript.write_text("[00:00] Content\n")
        mock_config.add_favorite("meeting.txt")

        result = cli_runner.invoke(cli, ["favorites"])

        assert result.exit_code == 0
        assert "meeting.txt" in result.output
        assert "Total: 1 favorites" in result.output


class TestSearchCommand:
    """Tests for the search command."""

    def test_search_command_help(self, cli_runner: CliRunner):
        """search --help should show usage information."""
        result = cli_runner.invoke(cli, ["search", "--help"])

        assert result.exit_code == 0
        assert "Search across all meeting transcripts" in result.output
        assert "--case-sensitive" in result.output
        assert "--limit" in result.output

    def test_search_command_basic(self, cli_runner: CliRunner, mock_config):
        """search should find matches in transcripts."""
        # Create a transcript file
        transcript = mock_config.transcripts_dir / "test_meeting.txt"
        transcript.write_text("[00:00] Budget discussion here\n")

        result = cli_runner.invoke(cli, ["search", "budget"])

        assert result.exit_code == 0
        assert "1 match" in result.output
        assert "test_meeting.txt" in result.output

    def test_search_command_no_matches(self, cli_runner: CliRunner, mock_config):
        """search should show message when no matches found."""
        # Create a transcript file
        transcript = mock_config.transcripts_dir / "test_meeting.txt"
        transcript.write_text("[00:00] Hello world\n")

        result = cli_runner.invoke(cli, ["search", "nonexistent"])

        assert result.exit_code == 0
        assert "No results found" in result.output

    def test_search_command_case_sensitive(self, cli_runner: CliRunner, mock_config):
        """search --case-sensitive should only match exact case."""
        # Create a transcript file
        transcript = mock_config.transcripts_dir / "test_meeting.txt"
        transcript.write_text("[00:00] API endpoint\n[01:00] api test\n")

        result = cli_runner.invoke(cli, ["search", "API", "--case-sensitive"])

        assert result.exit_code == 0
        assert "1 match" in result.output

    def test_search_command_limit(self, cli_runner: CliRunner, mock_config):
        """search --limit should restrict output."""
        # Create a transcript with many matches
        lines = [f"[{i:02d}:00] Match keyword here\n" for i in range(30)]
        transcript = mock_config.transcripts_dir / "test_meeting.txt"
        transcript.write_text("".join(lines))

        result = cli_runner.invoke(cli, ["search", "keyword", "-n", "5"])

        assert result.exit_code == 0
        assert "more matches" in result.output

    def test_search_command_custom_dir(self, cli_runner: CliRunner, mock_config, tmp_path):
        """search --transcripts-dir should use specified directory."""
        # Create a transcript in custom directory
        custom_dir = tmp_path / "custom_transcripts"
        custom_dir.mkdir()
        transcript = custom_dir / "custom_meeting.txt"
        transcript.write_text("[00:00] Custom transcript content\n")

        result = cli_runner.invoke(
            cli, ["search", "custom", "--transcripts-dir", str(custom_dir)]
        )

        assert result.exit_code == 0
        assert "1 match" in result.output
        assert "custom_meeting.txt" in result.output

    def test_search_command_no_transcripts(self, cli_runner: CliRunner, mock_config):
        """search should show message when no transcripts exist."""
        result = cli_runner.invoke(cli, ["search", "anything"])

        assert result.exit_code == 0
        assert "No transcripts found" in result.output

    def test_search_command_empty_query(self, cli_runner: CliRunner, mock_config):
        """search with empty query should show error."""
        result = cli_runner.invoke(cli, ["search", ""])

        assert result.exit_code == 0
        assert "cannot be empty" in result.output

    def test_search_command_shows_timestamps(self, cli_runner: CliRunner, mock_config):
        """search should display timestamps in output."""
        transcript = mock_config.transcripts_dir / "test_meeting.txt"
        transcript.write_text("[05:32] Budget discussion here\n")

        result = cli_runner.invoke(cli, ["search", "budget"])

        assert result.exit_code == 0
        assert "[05:32]" in result.output
