"""Menu bar app for Meeting Noter daemon control."""

from __future__ import annotations

import atexit
import os
import subprocess
import threading
from pathlib import Path
from typing import Optional

import rumps

from meeting_noter.daemon import read_pid_file, is_process_running, stop_daemon
from meeting_noter.config import get_config, generate_meeting_name
from meeting_noter.mic_monitor import MicrophoneMonitor, get_meeting_window_title


DEFAULT_PID_FILE = Path.home() / ".meeting-noter.pid"
MENUBAR_PID_FILE = Path.home() / ".meeting-noter-menubar.pid"
RECORDING_STATE_FILE = Path.home() / ".meeting-noter-recording.json"


def _write_menubar_pid():
    """Write the menubar PID file."""
    with open(MENUBAR_PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def _remove_menubar_pid():
    """Remove the menubar PID file."""
    try:
        MENUBAR_PID_FILE.unlink()
    except FileNotFoundError:
        pass


class MeetingNoterApp(rumps.App):
    """Menu bar app for controlling the Meeting Noter daemon."""

    def __init__(self):
        super().__init__("Meeting Noter", title="▷")
        self.pid_file = DEFAULT_PID_FILE
        self.config = get_config()
        self.mic_monitor = MicrophoneMonitor()
        self.current_meeting_name: Optional[str] = None
        self.pending_notification = False  # Avoid duplicate notifications
        self._pending_app_name: Optional[str] = None
        self.menu = [
            "Start Recording",
            "Stop Recording",
            None,  # Separator
            "Open Recordings",
            "Open UI",
        ]
        self._update_title()

    def _is_running(self) -> bool:
        """Check if daemon is currently running."""
        pid = read_pid_file(self.pid_file)
        return pid is not None and is_process_running(pid)

    def _get_current_recording_name(self) -> Optional[str]:
        """Get the name of the current recording from the log file.

        Parses the daemon log to find the most recent 'Recording started:' entry.
        Returns the filename (without extension) or None if not recording.
        """
        if not self._is_running():
            return None

        log_path = Path.home() / ".meeting-noter.log"
        if not log_path.exists():
            return None

        try:
            with open(log_path, "r") as f:
                lines = f.readlines()

            # Find the most recent recording start/save
            recording_name = None
            for line in reversed(lines[-50:]):  # Check last 50 lines
                if "Recording started:" in line:
                    # Extract filename from "Recording started: filename.mp3"
                    parts = line.split("Recording started:")
                    if len(parts) > 1:
                        filename = parts[1].strip()
                        # Remove extension and timestamp prefix
                        name = filename.replace(".mp3", "")
                        # If format is timestamp_name, extract just the name
                        parts = name.split("_", 2)  # Split max 2 times
                        if len(parts) >= 3:
                            # Format: YYYY-MM-DD_HHMMSS_MeetingName
                            recording_name = parts[2]
                        else:
                            recording_name = name
                        break
                elif "Recording saved:" in line or "Recording discarded" in line:
                    # Recording ended, no active recording
                    break

            return recording_name
        except Exception:
            return None

    def _truncate_name(self, name: str, max_length: int = 15) -> str:
        """Truncate a name to fit in the menu bar."""
        if len(name) <= max_length:
            return name
        return name[:max_length - 1] + "..."

    def _update_title(self):
        """Update menu bar title based on daemon status."""
        if self._is_running():
            self.title = "▶"  # Filled triangle = recording
        else:
            self.title = "▷"  # Outline triangle = idle

    def _save_recording_state(self, meeting_name: str, file_path: Optional[str] = None):
        """Save current recording state to file."""
        import json
        state = {
            "recording": True,
            "meeting_name": meeting_name,
            "file_path": file_path,
        }
        try:
            with open(RECORDING_STATE_FILE, "w") as f:
                json.dump(state, f)
        except Exception:
            pass

    def _clear_recording_state(self):
        """Clear recording state file."""
        try:
            RECORDING_STATE_FILE.unlink()
        except FileNotFoundError:
            pass

    def _start_recording_with_name(self, meeting_name: str, app_name: Optional[str] = None):
        """Start recording with a specific meeting name."""
        import sys

        if self._is_running():
            return

        self.current_meeting_name = meeting_name
        self._save_recording_state(meeting_name)
        self.mic_monitor.set_recording(True, app_name)

        # Start daemon with the meeting name using current Python
        subprocess.Popen(
            [sys.executable, "-m", "meeting_noter.cli", "daemon", "--name", meeting_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._update_title()

    @rumps.clicked("Start Recording")
    def start_recording(self, _):
        """Start the daemon via subprocess."""
        if self._is_running():
            rumps.notification(
                title="Meeting Noter",
                subtitle="Already Running",
                message="The daemon is already recording.",
            )
            return

        meeting_name = generate_meeting_name()
        self._start_recording_with_name(meeting_name)

        rumps.notification(
            title="Meeting Noter",
            subtitle="Recording Started",
            message=meeting_name,
        )

    def _get_latest_recording(self) -> Optional[Path]:
        """Get the most recent recording file."""
        recordings_dir = self.config.recordings_dir
        if not recordings_dir.exists():
            return None
        mp3_files = sorted(recordings_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime)
        return mp3_files[-1] if mp3_files else None

    def _get_transcript_path(self, audio_path: Path) -> Path:
        """Get the transcript path for an audio file."""
        return self.config.transcripts_dir / audio_path.with_suffix(".txt").name

    def _transcribe_in_background(self, audio_path: Path):
        """Transcribe a recording in background subprocess."""
        import sys
        # Use subprocess to run transcription - more reliable than threading with rumps
        subprocess.Popen(
            [sys.executable, "-m", "meeting_noter.cli", "transcribe", str(audio_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @rumps.clicked("Stop Recording")
    def stop_recording(self, _):
        """Stop the running daemon and optionally transcribe."""
        if not self._is_running():
            rumps.notification(
                title="Meeting Noter",
                subtitle="Not Running",
                message="The daemon is not running.",
            )
            return

        # Get latest recording before stopping (to compare after)
        latest_before = self._get_latest_recording()
        before_mtime = latest_before.stat().st_mtime if latest_before else 0

        stop_daemon(self.pid_file)
        self._update_title()

        # Check for new recording after stopping
        import time
        time.sleep(2)  # Give daemon time to save file

        # Reload config to get current settings
        self.config.load()

        latest_after = self._get_latest_recording()

        # Check if there's a new or updated recording
        is_new_recording = False
        if latest_after:
            after_mtime = latest_after.stat().st_mtime
            if latest_before is None or str(latest_after) != str(latest_before) or after_mtime > before_mtime:
                is_new_recording = True

        # Clear recording state
        self._clear_recording_state()
        self.current_meeting_name = None

        if is_new_recording:
            # New recording was saved
            if self.config.auto_transcribe:
                rumps.notification(
                    title="Meeting Noter",
                    subtitle="Recording Saved",
                    message=f"Transcribing {latest_after.name}...",
                )
                self._transcribe_in_background(latest_after)
            else:
                rumps.notification(
                    title="Meeting Noter",
                    subtitle="Recording Saved",
                    message=latest_after.name,
                )
        else:
            rumps.notification(
                title="Meeting Noter",
                subtitle="Stopped",
                message="Recording daemon stopped.",
            )

    @rumps.clicked("Open Recordings")
    def open_recordings(self, _):
        """Open the recordings folder in Finder."""
        recordings_dir = self.config.recordings_dir
        recordings_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["open", str(recordings_dir)])

    @rumps.clicked("Open UI")
    def open_ui(self, _):
        """Open the desktop GUI application."""
        import sys
        subprocess.Popen(
            [sys.executable, "-m", "meeting_noter.cli", "gui"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @rumps.timer(2)
    def poll_status(self, _):
        """Periodically update the menu bar title and check for mic usage."""
        self._update_title()

        is_recording = self._is_running()

        # Tell mic monitor our recording state
        self.mic_monitor.set_recording(is_recording)

        # Check for mic usage changes
        mic_started, mic_stopped, app_name = self.mic_monitor.check()

        # Auto-stop recording when mic stops being used
        if mic_stopped and is_recording:
            rumps.notification(
                title="Meeting Noter",
                subtitle="Call Ended",
                message="Stopping recording...",
            )
            self._auto_stop_recording()
            return

        # Prompt to record when mic starts being used
        if mic_started and not is_recording and not self.pending_notification:
            self.pending_notification = True
            self._pending_app_name = app_name or "Unknown App"
            # Try to get meeting name from window title, fall back to timestamp
            window_title = get_meeting_window_title()
            self._pending_meeting_name = window_title or generate_meeting_name()

    def _auto_stop_recording(self):
        """Stop recording automatically when meeting ends."""
        if not self._is_running():
            return

        # Get latest recording before stopping
        latest_before = self._get_latest_recording()
        before_mtime = latest_before.stat().st_mtime if latest_before else 0

        stop_daemon(self.pid_file)
        self._update_title()

        # Wait for file to be saved
        import time
        time.sleep(2)

        # Reload config
        self.config.load()

        latest_after = self._get_latest_recording()

        # Check for new recording
        is_new_recording = False
        if latest_after:
            after_mtime = latest_after.stat().st_mtime
            if latest_before is None or str(latest_after) != str(latest_before) or after_mtime > before_mtime:
                is_new_recording = True

        # Clear state
        self._clear_recording_state()
        self.current_meeting_name = None

        if is_new_recording:
            if self.config.auto_transcribe:
                rumps.notification(
                    title="Meeting Noter",
                    subtitle="Recording Saved",
                    message=f"Transcribing {latest_after.name}...",
                )
                self._transcribe_in_background(latest_after)
            else:
                rumps.notification(
                    title="Meeting Noter",
                    subtitle="Recording Saved",
                    message=latest_after.name,
                )

    @rumps.timer(1)
    def check_pending_prompt(self, _):
        """Check if we need to show a recording prompt (runs on main thread)."""
        if self.pending_notification and hasattr(self, '_pending_meeting_name'):
            app_name = self._pending_app_name or "App"
            meeting_name = self._pending_meeting_name

            # Clear first to prevent re-triggering
            self._pending_app_name = None
            self.pending_notification = False

            # Build message with meeting name if available
            if meeting_name and not meeting_name[0].isdigit():
                # Has a real meeting name (not timestamp-based)
                message = f"Meeting: {meeting_name}\n\nDo you want to record?"
            else:
                message = "Do you want to record this call?"

            # Show alert on main thread
            response = rumps.alert(
                title=f"Microphone in use: {app_name}",
                message=message,
                ok="Record",
                cancel="Skip",
            )

            if response == 1:  # Record clicked
                self._start_recording_with_name(meeting_name, app_name)
                rumps.notification(
                    title="Meeting Noter",
                    subtitle="Recording Started",
                    message=meeting_name,
                )


def _hide_dock_icon():
    """Hide the dock icon on macOS (make it a background agent app)."""
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
        NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    except ImportError:
        pass


def run_menubar():
    """Run the menu bar app."""
    _hide_dock_icon()
    _write_menubar_pid()
    atexit.register(_remove_menubar_pid)

    app = MeetingNoterApp()
    app.run()


if __name__ == "__main__":
    run_menubar()
