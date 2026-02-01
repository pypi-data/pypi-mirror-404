"""macOS setup for Meeting Noter."""

from __future__ import annotations

import sys

import click


def check_screen_recording_permission() -> bool:
    """Check if Screen Recording permission is granted.

    This permission is required to capture system audio via ScreenCaptureKit.
    """
    try:
        from Quartz import CGPreflightScreenCaptureAccess
        return CGPreflightScreenCaptureAccess()
    except ImportError:
        # Quartz not available, assume permission not granted
        return False
    except Exception:
        return False


def request_screen_recording_permission() -> bool:
    """Request Screen Recording permission from the user.

    This will trigger the system permission dialog if not already granted.
    """
    try:
        from Quartz import CGRequestScreenCaptureAccess
        return CGRequestScreenCaptureAccess()
    except ImportError:
        return False
    except Exception:
        return False


def run_setup():
    """Run the setup process for Meeting Noter.

    This simplified setup:
    1. Checks for Screen Recording permission (needed for system audio)
    2. Requests permission if not granted
    3. Initializes the configuration

    No virtual audio devices (BlackHole) are required anymore - we use
    ScreenCaptureKit to capture system audio directly.
    """
    click.echo(click.style("\n=== Meeting Noter Setup ===\n", fg="blue", bold=True))

    # Check macOS
    if sys.platform != "darwin":
        click.echo(click.style(
            "Error: Meeting Noter only supports macOS.",
            fg="red"
        ))
        sys.exit(1)

    # Check/Request Screen Recording permission
    click.echo("Step 1: Checking Screen Recording permission...")

    if check_screen_recording_permission():
        click.echo(click.style("  Screen Recording permission already granted", fg="green"))
    else:
        click.echo("  Screen Recording permission not yet granted")
        click.echo("  This permission is needed to capture meeting audio from other participants.")
        click.echo()
        click.echo("  Requesting permission...")

        request_screen_recording_permission()

        click.echo()
        click.echo(click.style("  A system dialog should appear.", fg="yellow"))
        click.echo("  Please grant Screen Recording permission to Terminal (or your IDE).")
        click.echo()
        click.echo("  If no dialog appeared:")
        click.echo("    1. Open System Settings > Privacy & Security > Screen Recording")
        click.echo("    2. Enable the toggle for Terminal (or your IDE)")
        click.echo("    3. Restart your terminal/IDE")

    click.echo()
    click.echo(click.style("=== Setup Complete ===\n", fg="blue", bold=True))
    click.echo("""
Meeting Noter is ready to use!

How it works:
- Your microphone captures your voice
- ScreenCaptureKit captures other participants (requires Screen Recording permission)
- Both audio sources are combined and saved to MP3

Next steps:
1. Run: meeting-noter menubar    (for menu bar control)
   Or:  meeting-noter gui        (for desktop app)
   Or:  meeting-noter start      (for CLI recording)

2. When you start a meeting, Meeting Noter will detect it and offer to record.

Note: If you denied Screen Recording permission, only your microphone
will be captured. Grant permission in System Settings to capture
meeting participants' audio.
""")
