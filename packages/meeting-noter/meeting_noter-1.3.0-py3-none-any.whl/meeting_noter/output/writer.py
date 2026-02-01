"""Output handling for recordings and transcripts."""

from __future__ import annotations

import click
from pathlib import Path
from datetime import datetime
from typing import Optional


def format_duration(seconds: float) -> str:
    """Format duration as human-readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_size(bytes: int) -> str:
    """Format file size as human-readable string."""
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024 * 1024:
        return f"{bytes / 1024:.1f} KB"
    else:
        return f"{bytes / (1024 * 1024):.1f} MB"


def get_audio_duration(filepath: Path) -> Optional[float]:
    """Get duration of an audio file in seconds.

    Uses a simple estimation based on file size and bitrate.
    """
    try:
        # Rough estimation: 128kbps MP3 = 16KB per second
        size = filepath.stat().st_size
        return size / (128 * 1000 / 8)  # 128kbps = 16000 bytes/sec
    except:
        return None


def list_recordings(output_dir: Path, limit: int = 10):
    """List recent meeting recordings."""
    if not output_dir.exists():
        click.echo(click.style(f"Directory not found: {output_dir}", fg="red"))
        return

    # Find all MP3 files
    mp3_files = sorted(
        output_dir.glob("*.mp3"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not mp3_files:
        click.echo(click.style("No recordings found.", fg="yellow"))
        click.echo(f"\nRecordings directory: {output_dir}")
        click.echo("Run 'meeting-noter daemon' to start capturing audio.")
        return

    click.echo(f"\nRecent recordings in {output_dir}:\n")

    # Show header
    click.echo(f"  {'Date':<20} {'Duration':<12} {'Size':<10} {'Transcript':<12} File")
    click.echo("  " + "-" * 75)

    for mp3 in mp3_files[:limit]:
        # Get file info
        stat = mp3.stat()
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        date_str = mod_time.strftime("%Y-%m-%d %H:%M")

        # Duration estimate
        duration = get_audio_duration(mp3)
        duration_str = format_duration(duration) if duration else "?"

        # File size
        size_str = format_size(stat.st_size)

        # Check for transcript
        transcript = mp3.with_suffix(".txt")
        has_transcript = click.style("Yes", fg="green") if transcript.exists() else click.style("No", fg="yellow")

        click.echo(f"  {date_str:<20} {duration_str:<12} {size_str:<10} {has_transcript:<12} {mp3.name}")

    if len(mp3_files) > limit:
        click.echo(f"\n  ... and {len(mp3_files) - limit} more recordings")

    click.echo(f"\nTotal: {len(mp3_files)} recordings")
    click.echo("\nTo transcribe: meeting-noter transcribe [filename]")
