"""Favorites management for meeting transcripts."""

from __future__ import annotations

import click
from pathlib import Path
from datetime import datetime
from typing import Optional

from meeting_noter.config import get_config


def list_favorites(transcripts_dir: Path) -> None:
    """List all favorite transcripts.

    Args:
        transcripts_dir: Directory containing transcript files
    """
    config = get_config()
    favorites = config.favorites

    if not favorites:
        click.echo(click.style("No favorites yet.", fg="yellow"))
        click.echo("\nAdd favorites with: meeting-noter favorites add <filename>")
        click.echo("Or use: meeting-noter favorites add --latest")
        return

    click.echo()
    click.echo(click.style("Favorite Transcripts", bold=True))
    click.echo("=" * 50)
    click.echo()

    found_count = 0
    missing_count = 0

    for idx, filename in enumerate(favorites, 1):
        filepath = transcripts_dir / filename
        if filepath.exists():
            found_count += 1
            # Get file info
            stat = filepath.stat()
            mod_time = datetime.fromtimestamp(stat.st_mtime)
            date_str = mod_time.strftime("%Y-%m-%d %H:%M")

            # Display: index, filename prominently, then date
            click.echo(
                click.style(f"  {idx}. ", fg="cyan")
                + click.style(filename, fg="green", bold=True)
            )
            click.echo(f"     ★ {date_str}")
        else:
            missing_count += 1
            click.echo(
                click.style(f"  {idx}. ", fg="cyan")
                + click.style(filename, fg="red", strikethrough=True)
            )
            click.echo(click.style("     (file not found)", fg="red"))

    click.echo()
    click.echo(f"Total: {found_count} favorites")
    if missing_count > 0:
        click.echo(
            click.style(
                f"Warning: {missing_count} favorite(s) no longer exist",
                fg="yellow"
            )
        )
    click.echo()


def add_favorite(
    transcripts_dir: Path,
    filename: Optional[str] = None,
    latest: bool = False
) -> None:
    """Add a transcript to favorites.

    Args:
        transcripts_dir: Directory containing transcript files
        filename: Name of transcript file to add
        latest: If True, add the most recent transcript
    """
    config = get_config()

    if latest:
        # Find the most recent transcript
        txt_files = sorted(
            transcripts_dir.glob("*.txt"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not txt_files:
            click.echo(click.style("No transcripts found.", fg="red"))
            return
        filename = txt_files[0].name

    if not filename:
        click.echo(click.style("Error: Specify a filename or use --latest", fg="red"))
        return

    # Check if file exists
    filepath = transcripts_dir / filename
    if not filepath.exists():
        # Try adding .txt extension
        if not filename.endswith(".txt"):
            filepath = transcripts_dir / f"{filename}.txt"
            if filepath.exists():
                filename = f"{filename}.txt"
            else:
                click.echo(click.style(f"File not found: {filename}", fg="red"))
                click.echo(f"Looking in: {transcripts_dir}")
                return
        else:
            click.echo(click.style(f"File not found: {filename}", fg="red"))
            click.echo(f"Looking in: {transcripts_dir}")
            return

    if config.add_favorite(filename):
        click.echo(
            click.style("★ ", fg="yellow")
            + f"Added to favorites: "
            + click.style(filename, fg="green")
        )
    else:
        click.echo(click.style(f"Already a favorite: {filename}", fg="yellow"))


def remove_favorite(filename: str) -> None:
    """Remove a transcript from favorites.

    Args:
        filename: Name of transcript file to remove
    """
    config = get_config()

    # Handle with or without .txt extension
    if not filename.endswith(".txt"):
        if f"{filename}.txt" in config.favorites:
            filename = f"{filename}.txt"

    if config.remove_favorite(filename):
        click.echo(
            click.style("☆ ", fg="cyan")
            + f"Removed from favorites: "
            + click.style(filename, fg="green")
        )
    else:
        click.echo(click.style(f"Not a favorite: {filename}", fg="yellow"))


def list_transcripts_with_favorites(transcripts_dir: Path, limit: int = 10) -> None:
    """List transcripts with favorite status indicated.

    Args:
        transcripts_dir: Directory containing transcript files
        limit: Maximum number of transcripts to show
    """
    config = get_config()

    if not transcripts_dir.exists():
        click.echo(click.style(f"Directory not found: {transcripts_dir}", fg="red"))
        return

    txt_files = sorted(
        transcripts_dir.glob("*.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not txt_files:
        click.echo(click.style("No transcripts found.", fg="yellow"))
        return

    click.echo(f"\nTranscripts in {transcripts_dir}:\n")

    for txt_file in txt_files[:limit]:
        stat = txt_file.stat()
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        date_str = mod_time.strftime("%Y-%m-%d %H:%M")

        is_fav = config.is_favorite(txt_file.name)
        star = click.style("★ ", fg="yellow") if is_fav else "  "

        click.echo(f"{star}{date_str}  {txt_file.name}")

    if len(txt_files) > limit:
        click.echo(f"\n  ... and {len(txt_files) - limit} more")

    click.echo(f"\nTotal: {len(txt_files)} transcripts")
