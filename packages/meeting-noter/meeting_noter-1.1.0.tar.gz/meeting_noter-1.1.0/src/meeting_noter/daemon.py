"""Background daemon for capturing meeting audio."""

from __future__ import annotations

import os
import sys
import signal
import time
import click
from pathlib import Path
from threading import Event
from typing import Optional

# IMPORTANT: Do NOT import audio modules at top level!
# CoreAudio crashes when Python forks after loading audio libraries.
# Audio imports are deferred until after daemonize() is called.


# Global stop event for signal handling
_stop_event = Event()


def _signal_handler(signum, frame):
    """Handle termination signals."""
    _stop_event.set()


def daemonize():
    """Fork the process to run as a daemon."""
    # First fork
    try:
        pid = os.fork()
        if pid > 0:
            # Parent exits
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"Fork #1 failed: {e}\n")
        sys.exit(1)

    # Decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(0)

    # Second fork
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"Fork #2 failed: {e}\n")
        sys.exit(1)

    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()

    with open("/dev/null", "r") as devnull:
        os.dup2(devnull.fileno(), sys.stdin.fileno())

    # Keep stdout/stderr for logging to a file
    log_path = Path.home() / ".meeting-noter.log"
    log_file = open(log_path, "a")
    os.dup2(log_file.fileno(), sys.stdout.fileno())
    os.dup2(log_file.fileno(), sys.stderr.fileno())


def write_pid_file(pid_file: Path):
    """Write the current PID to file."""
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))


def remove_pid_file(pid_file: Path):
    """Remove the PID file."""
    try:
        pid_file.unlink()
    except FileNotFoundError:
        pass


def read_pid_file(pid_file: Path) -> Optional[int]:
    """Read PID from file."""
    try:
        with open(pid_file, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def is_process_running(pid: int) -> bool:
    """Check if a process with given PID is running."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def check_audio_available() -> bool:
    """Check if any audio input device is available."""
    import sounddevice as sd
    try:
        devices = sd.query_devices()
        for device in devices:
            if device["max_input_channels"] > 0:
                return True
    except Exception:
        pass
    return False


def run_daemon(
    output_dir: Path,
    foreground: bool = False,
    pid_file: Optional[Path] = None,
    meeting_name: Optional[str] = None,
):
    """Run the audio capture daemon.

    IMPORTANT: We must NOT import any audio libraries (sounddevice, etc.) before
    forking, because CoreAudio crashes when Python forks after loading audio libs.
    All audio-related imports happen in _run_capture_loop() AFTER daemonize().
    """
    # Check if already running (no audio imports needed)
    if pid_file:
        existing_pid = read_pid_file(pid_file)
        if existing_pid and is_process_running(existing_pid):
            click.echo(click.style(
                f"Daemon already running (PID {existing_pid})",
                fg="yellow"
            ))
            return

    if not foreground:
        click.echo("Starting daemon in background...")
        daemonize()

    # NOW it's safe to check audio (after fork)
    if not check_audio_available():
        print("Error: No audio input device found.")
        print("Please check your microphone settings.")
        return

    # Set up signal handlers
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    # Write PID file
    if pid_file:
        write_pid_file(pid_file)

    try:
        _run_capture_loop(output_dir, meeting_name=meeting_name)
    finally:
        if pid_file:
            remove_pid_file(pid_file)


def _run_capture_loop(
    output_dir: Path,
    meeting_name: Optional[str] = None,
    enable_live_transcription: bool = True,
):
    """Main capture loop.

    Audio imports happen HERE, safely AFTER the fork.
    """
    import sys
    from meeting_noter.config import get_config

    # Import audio modules AFTER fork to avoid CoreAudio crash
    from meeting_noter.audio.capture import AudioCapture, SilenceDetector
    from meeting_noter.audio.encoder import RecordingSession

    config = get_config()

    # Live transcription (imported here to avoid loading Whisper before fork)
    live_transcriber = None
    if enable_live_transcription:
        try:
            from meeting_noter.transcription.live_transcription import LiveTranscriber
            LiveTranscriber  # Just verify import works, create later
        except ImportError as e:
            print(f"Live transcription not available: {e}")
            enable_live_transcription = False

    print(f"Meeting Noter daemon started. Saving to {output_dir}")
    sys.stdout.flush()
    if meeting_name:
        print(f"Meeting: {meeting_name}")
        sys.stdout.flush()

    # Use combined capture (mic + system audio) if enabled
    use_combined = False
    if config.capture_system_audio:
        try:
            from meeting_noter.audio.system_audio import CombinedAudioCapture
            capture = CombinedAudioCapture()
            use_combined = True
        except Exception as e:
            print(f"Combined capture not available: {e}")
            sys.stdout.flush()

    if not use_combined:
        print("Listening for audio...")
        sys.stdout.flush()
        try:
            capture = AudioCapture()
        except RuntimeError as e:
            print(f"Error creating AudioCapture: {e}")
            sys.stdout.flush()
            return
        except Exception as e:
            print(f"Unexpected error creating AudioCapture: {type(e).__name__}: {e}")
            sys.stdout.flush()
            return

    # Start capture first (CombinedAudioCapture updates channels during start)
    try:
        capture.start()
        print("Capture started. Waiting for audio...")
        sys.stdout.flush()
    except Exception as e:
        print(f"Error starting capture: {type(e).__name__}: {e}")
        sys.stdout.flush()
        return

    try:
        # Get sample rate and channels from capture device AFTER start
        sample_rate = capture.sample_rate
        channels = capture.channels

        silence_detector = SilenceDetector(
            threshold=0.01,  # Higher threshold to ignore background noise
            silence_duration=30.0,  # 30 seconds of silence = meeting ended
            sample_rate=sample_rate,
        )

        # Use same sample rate and channels as capture device
        session = RecordingSession(
            output_dir,
            sample_rate=sample_rate,
            channels=channels,
            meeting_name=meeting_name,
        )
        recording_started = False
        audio_detected = False

        while not _stop_event.is_set():
            audio = capture.get_audio(timeout=0.5)
            if audio is None:
                continue

            # Flatten if needed
            if audio.ndim > 1:
                audio = audio.flatten()

            has_audio = silence_detector.is_audio_present(audio)
            is_silence = silence_detector.update(audio)

            # State machine for recording
            if not session.is_active:
                # Not recording - wait for audio to start
                if has_audio:
                    filepath = session.start()
                    print(f"Recording started: {filepath.name}")
                    recording_started = True
                    audio_detected = True

                    # Start live transcription
                    if enable_live_transcription:
                        try:
                            from meeting_noter.transcription.live_transcription import LiveTranscriber
                            live_transcriber = LiveTranscriber(
                                output_path=filepath,
                                sample_rate=sample_rate,
                                channels=channels,
                                window_seconds=5.0,
                                slide_seconds=2.0,
                                model_size=config.whisper_model,
                            )
                            live_transcriber.start()
                            print(f"Live transcription: {live_transcriber.live_file_path.name}")
                        except Exception as e:
                            print(f"Failed to start live transcription: {e}")
                            live_transcriber = None
            else:
                # Currently recording
                session.write(audio)

                # Feed audio to live transcriber
                if live_transcriber is not None:
                    live_transcriber.write(audio)

                if has_audio:
                    audio_detected = True

                # Check for extended silence (meeting ended)
                if is_silence and audio_detected:
                    # Stop live transcription first
                    if live_transcriber is not None:
                        live_transcriber.stop()
                        live_transcriber = None

                    filepath, duration = session.stop()
                    if filepath:
                        print(f"Recording saved: {filepath.name} ({duration:.1f}s)")
                    else:
                        print("Recording discarded (too short)")
                    silence_detector.reset()
                    audio_detected = False

    except Exception as e:
        print(f"Error in capture loop: {e}")
    finally:
        capture.stop()

        # Stop live transcription
        if live_transcriber is not None:
            live_transcriber.stop()

        # Save any ongoing recording
        if 'session' in locals() and session.is_active:
            filepath, duration = session.stop()
            if filepath:
                print(f"Recording saved: {filepath.name} ({duration:.1f}s)")

        print("Daemon stopped.")


def check_screencapturekit_available() -> bool:
    """Check if ScreenCaptureKit is available and has permission."""
    try:
        from Quartz import CGPreflightScreenCaptureAccess
        return CGPreflightScreenCaptureAccess()
    except Exception:
        return False


def check_status(pid_file: Path):
    """Check daemon status."""
    # Check audio devices
    audio_ok = check_audio_available()
    screencapture_ok = check_screencapturekit_available()

    if audio_ok:
        click.echo("Microphone: " + click.style("available", fg="green"))
    else:
        click.echo("Microphone: " + click.style("not found", fg="red"))
        click.echo("  Please check your microphone settings")

    # System audio capture
    if screencapture_ok:
        click.echo("System audio: " + click.style("enabled", fg="green") + " (Screen Recording permission granted)")
    else:
        click.echo("System audio: " + click.style("not available", fg="yellow"))
        click.echo("  Grant Screen Recording permission to capture other participants")

    # Check daemon
    pid = read_pid_file(pid_file)

    if pid is None:
        click.echo("Daemon: " + click.style("not running", fg="red"))
        return

    if is_process_running(pid):
        click.echo("Daemon: " + click.style("running", fg="green") + f" (PID {pid})")

        # Show log tail
        log_path = Path.home() / ".meeting-noter.log"
        if log_path.exists():
            click.echo("\nRecent log entries:")
            with open(log_path, "r") as f:
                lines = f.readlines()
                for line in lines[-5:]:
                    click.echo(f"  {line.rstrip()}")
    else:
        click.echo("Daemon: " + click.style("not running", fg="red") + " (stale PID file)")
        remove_pid_file(pid_file)


def stop_daemon(pid_file: Path):
    """Stop the running daemon."""
    pid = read_pid_file(pid_file)

    if pid is None:
        click.echo("Daemon is not running")
        return

    if not is_process_running(pid):
        click.echo("Daemon is not running (cleaning up stale PID file)")
        remove_pid_file(pid_file)
        return

    click.echo(f"Stopping daemon (PID {pid})...")

    try:
        os.kill(pid, signal.SIGTERM)

        # Wait for process to stop
        for _ in range(10):
            time.sleep(0.5)
            if not is_process_running(pid):
                break

        if is_process_running(pid):
            click.echo("Daemon did not stop gracefully, forcing...")
            os.kill(pid, signal.SIGKILL)

        click.echo(click.style("Daemon stopped", fg="green"))
    except ProcessLookupError:
        click.echo("Daemon already stopped")
    finally:
        remove_pid_file(pid_file)


def run_foreground_capture(
    output_dir: Path,
    meeting_name: str,
    auto_transcribe: bool = True,
    whisper_model: str = "tiny.en",
    transcripts_dir: Optional[Path] = None,
    silence_timeout_minutes: int = 5,
    enable_live_transcription: bool = True,
) -> Optional[Path]:
    """Run audio capture in foreground with a named meeting.

    This function is used by the 'start' command for interactive recording.
    Records until Ctrl+C is pressed or silence timeout, then optionally transcribes.

    Args:
        output_dir: Directory to save recordings
        meeting_name: Name of the meeting (used in filename)
        auto_transcribe: Whether to transcribe after recording stops
        whisper_model: Whisper model to use for transcription
        transcripts_dir: Directory for transcripts
        silence_timeout_minutes: Stop after this many minutes of silence
        enable_live_transcription: Whether to enable real-time transcription

    Returns:
        Path to the saved recording, or None if recording was too short
    """
    # Import audio modules (safe since no fork)
    from meeting_noter.audio.capture import AudioCapture, SilenceDetector
    from meeting_noter.audio.encoder import RecordingSession
    from meeting_noter.config import get_config

    config = get_config()

    # Initialize live transcriber
    live_transcriber = None

    # Check audio device
    if not check_audio_available():
        click.echo(click.style("Error: ", fg="red") + "No audio input device found.")
        click.echo("Please check your microphone settings.")
        return None

    # Set up signal handlers
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    click.echo(f"Meeting: {click.style(meeting_name, fg='cyan', bold=True)}")
    click.echo(f"Output: {output_dir}")
    click.echo(f"Silence timeout: {silence_timeout_minutes} minutes")
    click.echo("Press Ctrl+C to stop recording.\n")

    # Use combined capture (mic + system audio) if enabled
    capture = None
    if config.capture_system_audio:
        try:
            from meeting_noter.audio.system_audio import CombinedAudioCapture
            capture = CombinedAudioCapture()
        except Exception as e:
            click.echo(click.style(f"Combined capture not available: {e}", fg="yellow"))

    if capture is None:
        try:
            capture = AudioCapture()
        except RuntimeError as e:
            click.echo(click.style(f"Error: {e}", fg="red"))
            return None

    saved_filepath = None
    stopped_by_silence = False

    try:
        # Start capture FIRST (CombinedAudioCapture updates channels during start)
        capture.start()

        # Get sample rate and channels AFTER start
        sample_rate = capture.sample_rate
        channels = capture.channels

        session = RecordingSession(
            output_dir,
            sample_rate=sample_rate,
            channels=channels,
            meeting_name=meeting_name,
        )

        # Silence detection
        silence_detector = SilenceDetector(
            threshold=0.01,
            silence_duration=silence_timeout_minutes * 60.0,  # Convert to seconds
            sample_rate=sample_rate,
        )

        # Start recording immediately
        filepath = session.start()
        click.echo(click.style("Recording: ", fg="green") + filepath.name)

        # Start live transcription
        if enable_live_transcription:
            try:
                from meeting_noter.transcription.live_transcription import LiveTranscriber
                live_transcriber = LiveTranscriber(
                    output_path=filepath,
                    sample_rate=sample_rate,
                    channels=channels,
                    window_seconds=5.0,
                    slide_seconds=2.0,
                    model_size=whisper_model,
                )
                live_transcriber.start()
                click.echo(
                    click.style("Live transcript: ", fg="cyan") +
                    str(live_transcriber.live_file_path)
                )
            except Exception as e:
                click.echo(click.style(f"Live transcription not available: {e}", fg="yellow"))
                live_transcriber = None

        while not _stop_event.is_set():
            audio = capture.get_audio(timeout=0.5)
            if audio is None:
                continue

            # Flatten if needed
            if audio.ndim > 1:
                audio = audio.flatten()

            session.write(audio)

            # Feed audio to live transcriber
            if live_transcriber is not None:
                live_transcriber.write(audio)

            # Check for extended silence
            if silence_detector.update(audio):
                click.echo("\n" + click.style("Stopped: ", fg="yellow") + "silence timeout reached")
                stopped_by_silence = True
                break

            # Show live duration every few seconds
            duration = session.duration
            if int(duration) % 5 == 0 and duration > 0:
                mins, secs = divmod(int(duration), 60)
                click.echo(f"\r  Duration: {mins:02d}:{secs:02d}", nl=False)

    except Exception as e:
        click.echo(click.style(f"\nError: {e}", fg="red"))
    finally:
        # Stop live transcription
        if live_transcriber is not None:
            live_transcriber.stop()

        capture.stop()

        # Save recording
        if 'session' in locals() and session.is_active:
            saved_filepath, duration = session.stop()
            if not stopped_by_silence:
                click.echo()  # New line after duration display

            if saved_filepath:
                mins, secs = divmod(int(duration), 60)
                click.echo(
                    click.style("\nSaved: ", fg="green") +
                    f"{saved_filepath.name} ({mins:02d}:{secs:02d})"
                )

                # Auto-transcribe if enabled
                if auto_transcribe:
                    click.echo(click.style("\nTranscribing...", fg="cyan"))
                    try:
                        from meeting_noter.transcription.engine import transcribe_file
                        transcribe_file(str(saved_filepath), output_dir, whisper_model, transcripts_dir)
                    except Exception as e:
                        click.echo(click.style(f"Transcription error: {e}", fg="red"))
            else:
                click.echo(click.style("\nRecording discarded", fg="yellow") + " (too short)")

    # Reset stop event for potential future use
    _stop_event.clear()

    return saved_filepath
