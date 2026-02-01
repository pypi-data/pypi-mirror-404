"""Search functionality for meeting transcripts."""

from __future__ import annotations

import re
import click
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchMatch:
    """A single match within a transcript file."""

    line_number: int
    line: str
    timestamp: Optional[str] = None


@dataclass
class FileSearchResult:
    """Search results for a single transcript file."""

    filepath: Path
    matches: list[SearchMatch]

    @property
    def match_count(self) -> int:
        return len(self.matches)


def _extract_timestamp(line: str) -> Optional[str]:
    """Extract timestamp from line if present (e.g., [05:32] or [01:23:45])."""
    match = re.match(r"^\[(\d{1,2}:\d{2}(?::\d{2})?)\]", line.strip())
    if match:
        return match.group(1)
    return None


def _truncate_line(line: str, max_length: int = 80) -> str:
    """Truncate line to max length with ellipsis."""
    line = line.strip()
    if len(line) <= max_length:
        return line
    return line[: max_length - 3] + "..."


def _highlight_match(line: str, query: str, case_sensitive: bool) -> str:
    """Highlight matching text in the line."""
    if case_sensitive:
        pattern = re.escape(query)
    else:
        pattern = re.compile(re.escape(query), re.IGNORECASE)

    def replace_with_highlight(match):
        return click.style(match.group(0), bold=True, fg="yellow")

    if case_sensitive:
        return re.sub(pattern, replace_with_highlight, line)
    else:
        return pattern.sub(replace_with_highlight, line)


def _search_file(
    filepath: Path,
    query: str,
    case_sensitive: bool,
    context_lines: int = 1,
) -> Optional[FileSearchResult]:
    """Search a single file for the query.

    Returns FileSearchResult if matches found, None otherwise.
    """
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    lines = content.splitlines()
    matches: list[SearchMatch] = []

    search_query = query if case_sensitive else query.lower()

    for i, line in enumerate(lines):
        search_line = line if case_sensitive else line.lower()

        if search_query in search_line:
            timestamp = _extract_timestamp(line)
            matches.append(
                SearchMatch(
                    line_number=i + 1,
                    line=line,
                    timestamp=timestamp,
                )
            )

    if matches:
        return FileSearchResult(filepath=filepath, matches=matches)
    return None


def search_transcripts(
    transcripts_dir: Path,
    query: str,
    case_sensitive: bool = False,
    limit: int = 20,
    context_lines: int = 1,
) -> None:
    """Search across all meeting transcripts.

    Args:
        transcripts_dir: Directory containing transcript files
        query: Search query string
        case_sensitive: Whether to perform case-sensitive search
        limit: Maximum number of matches to display
        context_lines: Number of context lines around matches (not yet implemented)
    """
    if not query.strip():
        click.echo(click.style("Error: Search query cannot be empty.", fg="red"))
        return

    if not transcripts_dir.exists():
        click.echo(click.style(f"Directory not found: {transcripts_dir}", fg="red"))
        return

    # Find all transcript files
    txt_files = sorted(
        transcripts_dir.glob("*.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not txt_files:
        click.echo(click.style("No transcripts found.", fg="yellow"))
        click.echo(f"\nTranscripts directory: {transcripts_dir}")
        click.echo("Record and transcribe meetings to search them.")
        return

    # Search all files
    results: list[FileSearchResult] = []
    for txt_file in txt_files:
        result = _search_file(txt_file, query, case_sensitive, context_lines)
        if result:
            results.append(result)

    if not results:
        click.echo(click.style(f'No results found for "{query}"', fg="yellow"))
        click.echo(f"\nSearched {len(txt_files)} transcripts in {transcripts_dir}")
        if not case_sensitive:
            click.echo("Tip: Use --case-sensitive for exact matching.")
        return

    # Sort by match count (most matches first)
    results.sort(key=lambda r: r.match_count, reverse=True)

    # Count total matches
    total_matches = sum(r.match_count for r in results)
    total_files = len(results)

    # Display header
    click.echo()
    matches_word = "match" if total_matches == 1 else "matches"
    files_word = "transcript" if total_files == 1 else "transcripts"
    click.echo(
        click.style(
            f"Found {total_matches} {matches_word} in {total_files} {files_word}:",
            bold=True,
        )
    )
    click.echo()

    # Display results
    matches_shown = 0
    limit_reached = False
    for result in results:
        if matches_shown >= limit:
            limit_reached = True
            break

        # File header
        match_word = "match" if result.match_count == 1 else "matches"
        click.echo(
            click.style(f"{result.filepath.name}", fg="green", bold=True)
            + f" ({result.match_count} {match_word})"
        )

        # Show matches (limited)
        for match in result.matches:
            if matches_shown >= limit:
                limit_reached = True
                break

            # Format the line
            prefix = f"  [{match.timestamp}] " if match.timestamp else "  "
            line_text = match.line
            if match.timestamp:
                # Remove timestamp from line since we're showing it in prefix
                line_text = re.sub(r"^\[\d{1,2}:\d{2}(?::\d{2})?\]\s*", "", line_text)

            truncated = _truncate_line(line_text, 70)
            highlighted = _highlight_match(truncated, query, case_sensitive)

            click.echo(f"{prefix}...{highlighted}...")
            matches_shown += 1

        click.echo()

    # Show remaining count if limit was reached
    if limit_reached and matches_shown < total_matches:
        remaining = total_matches - matches_shown
        click.echo(
            click.style(f"... and {remaining} more matches", fg="cyan")
        )
        click.echo()

    # Footer
    click.echo(f"Searched {len(txt_files)} transcripts in {transcripts_dir}")
