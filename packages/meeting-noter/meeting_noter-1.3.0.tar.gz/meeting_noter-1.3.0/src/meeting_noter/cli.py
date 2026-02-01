"""CLI commands for Meeting Noter."""

from __future__ import annotations

import difflib
import click
from pathlib import Path
from typing import Optional

from meeting_noter import __version__
from meeting_noter.config import (
    get_config,
    require_setup,
    is_setup_complete,
    generate_meeting_name,
)


# Default paths
DEFAULT_PID_FILE = Path.home() / ".meeting-noter.pid"


class SuggestGroup(click.Group):
    """Custom Click group that suggests similar commands on typos."""

    # Use SuggestCommand for all commands in this group
    command_class = None  # Will be set after SuggestCommand is defined

    def resolve_command(self, ctx, args):
        """Override to suggest similar commands on error."""
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError as e:
            if args:
                cmd_name = args[0]
                # Find similar commands
                matches = difflib.get_close_matches(
                    cmd_name, self.list_commands(ctx), n=3, cutoff=0.5
                )
                if matches:
                    suggestion = f"\n\nDid you mean: {', '.join(matches)}?"
                    raise click.UsageError(str(e) + suggestion)
            raise

    def get_command(self, ctx, cmd_name):
        """Override to handle partial command matching."""
        # Try exact match first
        rv = super().get_command(ctx, cmd_name)
        if rv is not None:
            return rv

        # Try prefix match
        matches = [cmd for cmd in self.list_commands(ctx) if cmd.startswith(cmd_name)]
        if len(matches) == 1:
            return super().get_command(ctx, matches[0])

        return None


class SuggestCommand(click.Command):
    """Custom Click command that suggests similar options on typos."""

    def make_context(self, info_name, args, parent=None, **extra):
        """Override to catch and improve option errors."""
        try:
            return super().make_context(info_name, args, parent, **extra)
        except click.UsageError as e:
            error_msg = str(e)
            if "No such option:" in error_msg:
                # Extract the bad option
                bad_opt = error_msg.split("No such option:")[-1].strip()
                # Get available options
                all_opts = []
                for param in self.params:
                    all_opts.extend(param.opts)

                matches = difflib.get_close_matches(bad_opt, all_opts, n=3, cutoff=0.4)
                if matches:
                    suggestion = f"\n\nDid you mean: {', '.join(matches)}?"
                    raise click.UsageError(error_msg + suggestion)
                else:
                    # Show available options
                    raise click.UsageError(
                        error_msg + f"\n\nAvailable options: {', '.join(sorted(all_opts))}"
                    )
            raise


# Set the default command class for SuggestGroup
SuggestGroup.command_class = SuggestCommand


def _handle_version():
    """Handle --version: show version, check for updates, auto-update if enabled."""
    import subprocess

    from meeting_noter.update_checker import check_for_update

    config = get_config()

    click.echo(f"meeting-noter {__version__}")

    # Check for updates
    click.echo("Checking for updates...", nl=False)
    new_version = check_for_update()

    if new_version:
        click.echo(f" update available: {new_version}")

        if config.auto_update:
            click.echo(f"Auto-updating to {new_version}...")
            result = subprocess.run(
                ["pipx", "upgrade", "meeting-noter"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                click.echo(click.style(f"Updated to {new_version}", fg="green"))
            else:
                click.echo(click.style("Update failed. Run manually:", fg="yellow"))
                click.echo("  pipx upgrade meeting-noter")
        else:
            click.echo("Run to update: pipx upgrade meeting-noter")
            click.echo("Or enable auto-update: mn config auto-update true")
    else:
        click.echo(" up to date")


@click.group(cls=SuggestGroup, invoke_without_command=True)
@click.option("--version", "-V", is_flag=True, help="Show version and check for updates")
@click.pass_context
def cli(ctx, version):
    """Meeting Noter - Offline meeting transcription.

    \b
    Quick start:
      meeting-noter           Start watching for meetings (background)
      meeting-noter status    Show current status
      meeting-noter shutdown  Stop all processes
      meeting-noter open      Open recordings in Finder

    \b
    Configuration:
      meeting-noter config                        Show all settings
      meeting-noter config recordings-dir ~/path  Set recordings directory
      meeting-noter config whisper-model base.en  Set transcription model
      meeting-noter config auto-transcribe false  Disable auto-transcribe
    """
    if version:
        _handle_version()
        ctx.exit(0)

    if ctx.invoked_subcommand is None:
        # No subcommand - start background watcher
        ctx.invoke(watcher)


@cli.command()
@click.argument("name", required=False)
@click.option("--live", "-l", is_flag=True, help="Show live transcription in terminal")
@require_setup
def start(name: Optional[str], live: bool):
    """Start an interactive foreground recording session.

    NAME is the meeting name (optional). If not provided, uses a timestamp
    like "29_Jan_2026_1430".

    Examples:
        meeting-noter start                    # Uses timestamp name
        meeting-noter start "Weekly Standup"   # Uses custom name
        meeting-noter start "Meeting" --live   # With live transcription

    Press Ctrl+C to stop recording. The recording will be automatically
    transcribed if auto_transcribe is enabled in settings.
    """
    from meeting_noter.daemon import run_foreground_capture
    import threading
    import time

    config = get_config()
    output_dir = config.recordings_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use default timestamp name if not provided
    meeting_name = name if name else generate_meeting_name()

    # Live transcription display thread
    stop_live_display = threading.Event()

    def display_live_transcript():
        """Background thread to display live transcription."""
        live_dir = output_dir / "live"
        last_content = ""

        # Wait for live file to appear
        while not stop_live_display.is_set():
            live_files = list(live_dir.glob("*.live.txt")) if live_dir.exists() else []
            if live_files:
                live_file = max(live_files, key=lambda p: p.stat().st_mtime)
                break
            time.sleep(0.5)
        else:
            return

        # Tail the file
        while not stop_live_display.is_set():
            try:
                content = live_file.read_text()
                if len(content) > len(last_content):
                    new_content = content[len(last_content):]
                    for line in new_content.splitlines():
                        # Only show timestamp lines (transcriptions)
                        if line.strip() and line.startswith("["):
                            click.echo(click.style(line, fg="cyan"))
                    last_content = content
            except Exception:
                pass
            time.sleep(0.5)

    # Start live display thread if requested
    live_thread = None
    if live:
        click.echo(click.style("Live transcription enabled", fg="cyan"))
        live_thread = threading.Thread(target=display_live_transcript, daemon=True)
        live_thread.start()

    try:
        run_foreground_capture(
            output_dir=output_dir,
            meeting_name=meeting_name,
            auto_transcribe=config.auto_transcribe,
            whisper_model=config.whisper_model,
            transcripts_dir=config.transcripts_dir,
            silence_timeout_minutes=config.silence_timeout,
        )
    finally:
        stop_live_display.set()
        if live_thread:
            live_thread.join(timeout=1.0)


@cli.command(hidden=True)  # Internal command used by watcher
@click.option("--output-dir", "-o", type=click.Path(), default=None)
@click.option("--foreground", "-f", is_flag=True)
@click.option("--name", "-n", default=None)
@require_setup
def daemon(output_dir: Optional[str], foreground: bool, name: Optional[str]):
    """Internal: Start recording daemon."""
    from meeting_noter.daemon import run_daemon

    config = get_config()
    output_path = Path(output_dir) if output_dir else config.recordings_dir
    output_path.mkdir(parents=True, exist_ok=True)

    run_daemon(
        output_path,
        foreground=foreground,
        pid_file=DEFAULT_PID_FILE,
        meeting_name=name,
    )


@cli.command()
def status():
    """Show Meeting Noter status.

    \b
    Examples:
        meeting-noter status    # Check if recording or watching
    """
    import os
    from meeting_noter.daemon import read_pid_file, is_process_running

    # Check watcher
    watcher_running = False
    if WATCHER_PID_FILE.exists():
        try:
            pid = int(WATCHER_PID_FILE.read_text().strip())
            os.kill(pid, 0)
            watcher_running = True
        except (ProcessLookupError, ValueError, FileNotFoundError):
            pass

    # Check daemon (recording)
    daemon_running = False
    daemon_pid = read_pid_file(DEFAULT_PID_FILE)
    if daemon_pid and is_process_running(daemon_pid):
        daemon_running = True

    # Determine status
    click.echo()
    if daemon_running:
        # Get current recording name from log
        recording_name = _get_current_recording_name()
        click.echo(f"🔴 Recording: {recording_name or 'In progress'}")
    elif watcher_running:
        click.echo("👀 Ready to record (watcher active)")
    else:
        click.echo("⏹️  Stopped (run 'meeting-noter' to start)")

    click.echo()

    # Show details
    click.echo("Components:")
    click.echo(f"  Watcher:  {'running' if watcher_running else 'stopped'}")
    click.echo(f"  Recorder: {'recording' if daemon_running else 'idle'}")
    click.echo()


def _get_current_recording_name() -> str | None:
    """Get the name of the current recording from the log file."""
    log_path = Path.home() / ".meeting-noter.log"
    if not log_path.exists():
        return None

    try:
        with open(log_path, "r") as f:
            lines = f.readlines()

        for line in reversed(lines[-50:]):
            if "Recording started:" in line:
                parts = line.split("Recording started:")
                if len(parts) > 1:
                    filename = parts[1].strip().replace(".mp3", "")
                    # Extract name from timestamp_name format
                    name_parts = filename.split("_", 2)
                    if len(name_parts) >= 3:
                        return name_parts[2]
                    return filename
            elif "Recording saved:" in line or "Recording discarded" in line:
                break
        return None
    except Exception:
        return None


@cli.command()
def shutdown():
    """Stop all Meeting Noter processes (daemon, watcher).

    \b
    Examples:
        meeting-noter shutdown    # Stop recording and watcher
    """
    import subprocess
    import os
    import signal
    from meeting_noter.daemon import stop_daemon

    stopped = []

    # Stop daemon
    if DEFAULT_PID_FILE.exists():
        stop_daemon(DEFAULT_PID_FILE)
        stopped.append("daemon")

    # Stop watcher
    if WATCHER_PID_FILE.exists():
        try:
            pid = int(WATCHER_PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            WATCHER_PID_FILE.unlink()
            stopped.append("watcher")
        except (ProcessLookupError, ValueError):
            WATCHER_PID_FILE.unlink(missing_ok=True)

    # Kill any remaining meeting-noter processes
    result = subprocess.run(
        ["pkill", "-f", "meeting_noter"],
        capture_output=True
    )
    if result.returncode == 0:
        stopped.append("other processes")

    if stopped:
        click.echo(f"Stopped: {', '.join(stopped)}")
    else:
        click.echo("No Meeting Noter processes were running.")


@cli.command()
@click.option("--follow", "-f", is_flag=True, help="Follow log output (like tail -f)")
@click.option("--lines", "-n", default=50, help="Number of lines to show")
def logs(follow: bool, lines: int):
    """View Meeting Noter logs.

    \b
    Examples:
        meeting-noter logs           # Show last 50 lines
        meeting-noter logs -n 100    # Show last 100 lines
        meeting-noter logs -f        # Follow log output (Ctrl+C to stop)
    """
    import subprocess

    log_file = Path.home() / ".meeting-noter.log"

    if not log_file.exists():
        click.echo("No log file found.")
        return

    if follow:
        click.echo(f"Following {log_file} (Ctrl+C to stop)...")
        try:
            subprocess.run(["tail", "-f", str(log_file)])
        except KeyboardInterrupt:
            pass
    else:
        subprocess.run(["tail", f"-{lines}", str(log_file)])


@cli.command("list")
@click.option(
    "--transcripts", "-t",
    is_flag=True,
    help="List transcripts instead of recordings",
)
@click.option(
    "--output-dir", "-o",
    type=click.Path(exists=True),
    default=None,
    help="Directory containing recordings (overrides config)",
)
@click.option(
    "--limit", "-n",
    type=int,
    default=10,
    help="Number of items to show",
)
@require_setup
def list_recordings(transcripts: bool, output_dir: Optional[str], limit: int):
    """List recent meeting recordings or transcripts.

    \b
    Examples:
        meeting-noter list             # Show last 10 recordings
        meeting-noter list -t          # Show last 10 transcripts
        meeting-noter list -t -n 20    # Show last 20 transcripts
    """
    config = get_config()

    if transcripts:
        from meeting_noter.output.favorites import list_transcripts_with_favorites
        path = Path(output_dir) if output_dir else config.transcripts_dir
        list_transcripts_with_favorites(path, limit)
    else:
        from meeting_noter.output.writer import list_recordings as _list_recordings
        path = Path(output_dir) if output_dir else config.recordings_dir
        _list_recordings(path, limit)


@cli.command("search")
@click.argument("query")
@click.option(
    "--case-sensitive", "-c",
    is_flag=True,
    help="Case-sensitive search",
)
@click.option(
    "--limit", "-n",
    type=int,
    default=20,
    help="Max results to show",
)
@click.option(
    "--transcripts-dir", "-d",
    type=click.Path(),
    default=None,
    help="Override transcripts directory",
)
@require_setup
def search(query: str, case_sensitive: bool, limit: int, transcripts_dir: Optional[str]):
    """Search across all meeting transcripts.

    \b
    Examples:
        meeting-noter search "action items"
        meeting-noter search "API" --case-sensitive
        meeting-noter search "standup" -n 5
    """
    from meeting_noter.output.searcher import search_transcripts

    config = get_config()
    path = Path(transcripts_dir) if transcripts_dir else config.transcripts_dir
    search_transcripts(path, query, case_sensitive, limit)


@cli.group("favorites", invoke_without_command=True)
@click.pass_context
@require_setup
def favorites(ctx):
    """Manage favorite transcripts.

    \b
    Examples:
        meeting-noter favorites              # List all favorites
        meeting-noter favorites add file.txt # Add to favorites
        meeting-noter favorites add --latest # Add most recent transcript
        meeting-noter favorites remove file  # Remove from favorites
    """
    if ctx.invoked_subcommand is None:
        # Default: list favorites
        from meeting_noter.output.favorites import list_favorites

        config = get_config()
        list_favorites(config.transcripts_dir)


@favorites.command("add")
@click.argument("filename", required=False)
@click.option("--latest", "-l", is_flag=True, help="Add the most recent transcript")
@require_setup
def favorites_add(filename: Optional[str], latest: bool):
    """Add a transcript to favorites.

    \b
    Examples:
        meeting-noter favorites add meeting.txt
        meeting-noter favorites add --latest
    """
    from meeting_noter.output.favorites import add_favorite

    config = get_config()
    add_favorite(config.transcripts_dir, filename, latest)


@favorites.command("remove")
@click.argument("filename")
@require_setup
def favorites_remove(filename: str):
    """Remove a transcript from favorites.

    \b
    Examples:
        meeting-noter favorites remove meeting.txt
    """
    from meeting_noter.output.favorites import remove_favorite

    remove_favorite(filename)


@cli.command()
@click.argument("file", required=False)
@click.option(
    "--output-dir", "-o",
    type=click.Path(exists=True),
    default=None,
    help="Directory containing recordings (overrides config)",
)
@click.option(
    "--model", "-m",
    type=click.Choice(["tiny.en", "base.en", "small.en", "medium.en", "large-v3"]),
    default=None,
    help="Whisper model size (overrides config)",
)
@require_setup
def transcribe(file: Optional[str], output_dir: Optional[str], model: Optional[str]):
    """Transcribe a meeting recording.

    \b
    Examples:
        meeting-noter transcribe                    # Transcribe latest recording
        meeting-noter transcribe recording.mp3      # Transcribe specific file
        meeting-noter transcribe -m base.en         # Use larger model for accuracy
    """
    from meeting_noter.transcription.engine import transcribe_file

    config = get_config()
    output_path = Path(output_dir) if output_dir else config.recordings_dir
    whisper_model = model or config.whisper_model

    transcribe_file(file, output_path, whisper_model, config.transcripts_dir)


@cli.command()
@require_setup
def live():
    """Show live transcription of an active recording.

    Displays the real-time transcript as it's being generated.
    Use in a separate terminal while recording with 'meeting-noter start'.

    \b
    Examples:
        # Terminal 1: Start recording
        meeting-noter start "Team Meeting"

        # Terminal 2: Watch live transcript
        meeting-noter live

    Or use 'meeting-noter start "name" --live' to see both in one terminal.
    """
    import time

    config = get_config()
    live_dir = config.recordings_dir / "live"

    # Find the most recent .live.txt file in the live/ subfolder
    if not live_dir.exists():
        click.echo(click.style("No live transcript found.", fg="yellow"))
        click.echo("Start a recording with: meeting-noter start")
        return

    live_files = sorted(
        live_dir.glob("*.live.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not live_files:
        click.echo(click.style("No live transcript found.", fg="yellow"))
        click.echo("Start a recording with: meeting-noter start")
        return

    live_file = live_files[0]

    # Check if file is actively being written (modified in last 30 seconds)
    file_age = time.time() - live_file.stat().st_mtime
    if file_age > 30:
        click.echo(click.style("No active recording found.", fg="yellow"))
        click.echo(f"Most recent transcript ({live_file.name}) is {int(file_age)}s old.")
        click.echo("Start a recording with: meeting-noter start")
        return

    click.echo(click.style("Live Transcription", fg="cyan", bold=True))
    click.echo(f"Source: {live_file.name.replace('.live.txt', '.mp3')}")
    click.echo("Press Ctrl+C to stop watching.\n")
    click.echo("-" * 40)

    # Tail the file
    try:
        last_content = ""
        no_update_count = 0

        while True:
            try:
                with open(live_file, "r") as f:
                    content = f.read()

                # Print only new content
                if len(content) > len(last_content):
                    new_content = content[len(last_content):]
                    # Print line by line for better formatting
                    for line in new_content.splitlines():
                        if line.strip():
                            click.echo(line)
                    last_content = content
                    no_update_count = 0
                else:
                    no_update_count += 1

                # Check if file hasn't been updated for 30+ seconds (recording likely ended)
                file_age = time.time() - live_file.stat().st_mtime
                if file_age > 30 and no_update_count > 5:
                    click.echo("\n" + click.style("Recording ended.", fg="yellow"))
                    break

            except FileNotFoundError:
                click.echo("\n" + click.style("Live transcript file removed.", fg="yellow"))
                break

            time.sleep(1)

    except KeyboardInterrupt:
        click.echo("\n" + click.style("Stopped watching.", fg="cyan"))


# Config key mappings (CLI name -> config attribute)
CONFIG_KEYS = {
    "recordings-dir": ("recordings_dir", "path", "Directory for audio recordings"),
    "transcripts-dir": ("transcripts_dir", "path", "Directory for transcripts"),
    "whisper-model": ("whisper_model", "choice:tiny.en,base.en,small.en,medium.en,large-v3", "Whisper model for transcription"),
    "auto-transcribe": ("auto_transcribe", "bool", "Auto-transcribe after recording"),
    "auto-update": ("auto_update", "bool", "Auto-update when running --version"),
    "silence-timeout": ("silence_timeout", "int", "Minutes of silence before auto-stop"),
    "capture-system-audio": ("capture_system_audio", "bool", "Capture meeting participants via ScreenCaptureKit"),
}


@cli.command()
@click.argument("key", required=False)
@click.argument("value", required=False)
def config(key: Optional[str], value: Optional[str]):
    """View or set configuration options.

    \b
    Examples:
        meeting-noter config                     # Show all settings
        meeting-noter config recordings-dir      # Get specific setting
        meeting-noter config recordings-dir ~/meetings  # Set setting

    \b
    Available settings:
        recordings-dir       Directory for audio recordings
        transcripts-dir      Directory for transcripts
        whisper-model        Model: tiny.en, base.en, small.en, medium.en, large-v3
        auto-transcribe      Auto-transcribe after recording (true/false)
        silence-timeout      Minutes of silence before auto-stop
        capture-system-audio Capture system audio (true/false)
    """
    cfg = get_config()

    if key is None:
        # Show all settings
        click.echo()
        click.echo("Meeting Noter Configuration")
        click.echo("=" * 40)
        for cli_key, (attr, _, desc) in CONFIG_KEYS.items():
            val = getattr(cfg, attr)
            click.echo(f"  {cli_key}: {val}")
        click.echo()
        click.echo(f"Config file: {cfg.config_path}")
        click.echo()
        return

    # Normalize key (allow underscores too)
    key = key.replace("_", "-").lower()

    if key not in CONFIG_KEYS:
        click.echo(f"Unknown config key: {key}")
        click.echo(f"Available keys: {', '.join(CONFIG_KEYS.keys())}")
        return

    attr, val_type, desc = CONFIG_KEYS[key]

    if value is None:
        # Get setting
        click.echo(getattr(cfg, attr))
        return

    # Set setting
    try:
        if val_type == "bool":
            if value.lower() in ("true", "1", "yes", "on"):
                parsed = True
            elif value.lower() in ("false", "0", "no", "off"):
                parsed = False
            else:
                raise ValueError(f"Invalid boolean: {value}")
        elif val_type == "int":
            parsed = int(value)
        elif val_type == "path":
            parsed = Path(value).expanduser()
            # Create directory if it doesn't exist
            parsed.mkdir(parents=True, exist_ok=True)
        elif val_type.startswith("choice:"):
            choices = val_type.split(":")[1].split(",")
            if value not in choices:
                raise ValueError(f"Must be one of: {', '.join(choices)}")
            parsed = value
        else:
            parsed = value

        setattr(cfg, attr, parsed)
        cfg.save()
        click.echo(f"Set {key} = {parsed}")

    except ValueError as e:
        click.echo(f"Invalid value: {e}")


WATCHER_PID_FILE = Path.home() / ".meeting-noter-watcher.pid"


@cli.command(hidden=True)
@click.option(
    "--foreground", "-f",
    is_flag=True,
    help="Run in foreground instead of background",
)
@require_setup
def watcher(foreground: bool):
    """Start background watcher that auto-detects and records meetings.

    This is the default command when running 'meeting-noter' without arguments.
    Runs in background by default. Use 'meeting-noter shutdown' to stop.

    Use -f/--foreground for interactive mode (shows prompts in terminal).
    """
    import subprocess
    import sys
    import os

    if foreground:
        _run_watcher_loop()
    else:
        # Check if already running
        if WATCHER_PID_FILE.exists():
            try:
                pid = int(WATCHER_PID_FILE.read_text().strip())
                os.kill(pid, 0)  # Check if process exists
                click.echo(f"Watcher already running (PID {pid}). Use 'meeting-noter shutdown' to stop.")
                return
            except (ProcessLookupError, ValueError):
                WATCHER_PID_FILE.unlink(missing_ok=True)

        # Start in background
        subprocess.Popen(
            [sys.executable, "-m", "meeting_noter.cli", "watcher", "-f"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        click.echo("Meeting Noter watcher started in background.")
        click.echo("Use 'meeting-noter shutdown' to stop.")


def _run_watcher_loop():
    """Run the watcher loop (foreground)."""
    import time
    import sys
    import os
    import atexit
    from meeting_noter.mic_monitor import MicrophoneMonitor, get_meeting_window_title, is_meeting_app_active
    from meeting_noter.daemon import is_process_running, read_pid_file, stop_daemon

    # Write PID file
    WATCHER_PID_FILE.write_text(str(os.getpid()))
    atexit.register(lambda: WATCHER_PID_FILE.unlink(missing_ok=True))

    config = get_config()
    output_dir = config.recordings_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    mic_monitor = MicrophoneMonitor()
    current_meeting_name = None

    try:
        while True:
            mic_started, mic_stopped, app_name = mic_monitor.check()

            is_recording = read_pid_file(DEFAULT_PID_FILE) is not None and \
                           is_process_running(read_pid_file(DEFAULT_PID_FILE))

            if mic_started and not is_recording:
                # Meeting detected - auto-start recording silently
                app_name = app_name or is_meeting_app_active() or "Unknown"
                meeting_name = get_meeting_window_title() or generate_meeting_name()
                current_meeting_name = meeting_name

                # Start daemon
                import subprocess
                subprocess.Popen(
                    [sys.executable, "-m", "meeting_noter.cli", "daemon", "--name", meeting_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                mic_monitor.set_recording(True, app_name)

            elif mic_stopped and is_recording:
                # Meeting ended - stop silently
                stop_daemon(DEFAULT_PID_FILE)
                mic_monitor.set_recording(False)

                # Auto-transcribe
                if config.auto_transcribe:
                    time.sleep(2)
                    mp3_files = sorted(output_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime)
                    if mp3_files:
                        latest = mp3_files[-1]
                        import subprocess
                        subprocess.Popen(
                            [sys.executable, "-m", "meeting_noter.cli", "transcribe", str(latest)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )

                current_meeting_name = None

            time.sleep(2)

    except KeyboardInterrupt:
        if is_recording:
            stop_daemon(DEFAULT_PID_FILE)


@cli.command(hidden=True)
@require_setup
def watch():
    """Watch for meetings interactively (foreground with prompts).

    Like 'meeting-noter' but runs in foreground and prompts before recording.
    Press Ctrl+C to exit.
    """
    import time
    import sys
    from meeting_noter.mic_monitor import MicrophoneMonitor, get_meeting_window_title, is_meeting_app_active
    from meeting_noter.daemon import is_process_running, read_pid_file, stop_daemon

    config = get_config()
    output_dir = config.recordings_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    mic_monitor = MicrophoneMonitor()
    current_meeting_name = None

    click.echo("👀 Watching for meetings... (Ctrl+C to exit)")
    click.echo()

    try:
        while True:
            mic_started, mic_stopped, app_name = mic_monitor.check()

            is_recording = read_pid_file(DEFAULT_PID_FILE) is not None and \
                           is_process_running(read_pid_file(DEFAULT_PID_FILE))

            if mic_started and not is_recording:
                app_name = app_name or is_meeting_app_active() or "Unknown"
                meeting_name = get_meeting_window_title() or generate_meeting_name()

                click.echo(f"🎤 Meeting detected: {app_name}")
                click.echo(f"   Name: {meeting_name}")

                if click.confirm("   Start recording?", default=True):
                    current_meeting_name = meeting_name
                    click.echo(f"🔴 Recording: {meeting_name}")

                    import subprocess
                    subprocess.Popen(
                        [sys.executable, "-m", "meeting_noter.cli", "daemon", "--name", meeting_name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    mic_monitor.set_recording(True, app_name)
                else:
                    click.echo("   Skipped.")
                    mic_monitor._was_mic_in_use = True

                click.echo()

            elif mic_stopped and is_recording:
                click.echo(f"📴 Meeting ended: {current_meeting_name or 'Unknown'}")
                stop_daemon(DEFAULT_PID_FILE)
                mic_monitor.set_recording(False)
                current_meeting_name = None

                if config.auto_transcribe:
                    click.echo("📝 Auto-transcribing...")
                    time.sleep(2)
                    mp3_files = sorted(output_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime)
                    if mp3_files:
                        latest = mp3_files[-1]
                        click.echo(f"   Transcribing: {latest.name}")
                        import subprocess
                        subprocess.Popen(
                            [sys.executable, "-m", "meeting_noter.cli", "transcribe", str(latest)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )

                click.echo()
                click.echo("👀 Watching for meetings... (Ctrl+C to exit)")
                click.echo()

            time.sleep(2)

    except KeyboardInterrupt:
        click.echo()
        if is_recording:
            click.echo("Stopping recording...")
            stop_daemon(DEFAULT_PID_FILE)
        click.echo("Stopped watching.")


@cli.command("open")
@click.argument("what", type=click.Choice(["recordings", "transcripts", "config"]), default="recordings")
def open_folder(what: str):
    """Open recordings, transcripts, or config folder in Finder.

    \b
    Examples:
        meeting-noter open              # Open recordings folder
        meeting-noter open recordings   # Open recordings folder
        meeting-noter open transcripts  # Open transcripts folder
        meeting-noter open config       # Open config folder
    """
    import subprocess

    config = get_config()

    paths = {
        "recordings": config.recordings_dir,
        "transcripts": config.transcripts_dir,
        "config": config.config_path.parent,
    }

    path = paths[what]
    path.mkdir(parents=True, exist_ok=True)

    subprocess.run(["open", str(path)])
    click.echo(f"Opened: {path}")


@cli.command()
@click.option("--shell", type=click.Choice(["zsh", "bash", "fish"]), default="zsh")
def completion(shell: str):
    """Install shell tab completion.

    \b
    For zsh (default on macOS):
        eval "$(_MEETING_NOTER_COMPLETE=zsh_source meeting-noter)"

    Add to your ~/.zshrc for permanent completion.
    """
    import os

    shell_configs = {
        "zsh": ("~/.zshrc", '_MEETING_NOTER_COMPLETE=zsh_source meeting-noter'),
        "bash": ("~/.bashrc", '_MEETING_NOTER_COMPLETE=bash_source meeting-noter'),
        "fish": ("~/.config/fish/completions/meeting-noter.fish", '_MEETING_NOTER_COMPLETE=fish_source meeting-noter'),
    }

    config_file, env_cmd = shell_configs[shell]
    config_path = Path(config_file).expanduser()

    completion_line = f'eval "$({env_cmd})"'

    # Check if already installed
    if config_path.exists():
        content = config_path.read_text()
        if "MEETING_NOTER_COMPLETE" in content:
            click.echo(f"Completion already installed in {config_file}")
            return

    # Install
    click.echo(f"Installing {shell} completion...")

    if shell == "fish":
        config_path.parent.mkdir(parents=True, exist_ok=True)
        import subprocess
        result = subprocess.run(
            ["sh", "-c", f"{env_cmd}"],
            capture_output=True, text=True
        )
        config_path.write_text(result.stdout)
    else:
        with open(config_path, "a") as f:
            f.write(f"\n# Meeting Noter tab completion\n{completion_line}\n")

    click.echo(f"Added to {config_file}")
    click.echo(f"Run: source {config_file}")
    click.echo("Or restart your terminal.")


if __name__ == "__main__":
    cli()
