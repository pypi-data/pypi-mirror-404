"""Tests for the transcript search module."""

from __future__ import annotations

from pathlib import Path
import time

import pytest

from meeting_noter.output.searcher import (
    SearchMatch,
    FileSearchResult,
    _extract_timestamp,
    _truncate_line,
    _search_file,
    search_transcripts,
)


class TestExtractTimestamp:
    """Tests for _extract_timestamp function."""

    def test_extract_mm_ss_timestamp(self):
        """Should extract MM:SS format timestamps."""
        assert _extract_timestamp("[05:32] Some text") == "05:32"
        assert _extract_timestamp("[00:00] Start") == "00:00"
        assert _extract_timestamp("[59:59] End") == "59:59"

    def test_extract_hh_mm_ss_timestamp(self):
        """Should extract HH:MM:SS format timestamps."""
        assert _extract_timestamp("[01:23:45] Long meeting") == "01:23:45"
        assert _extract_timestamp("[00:00:00] Start") == "00:00:00"

    def test_extract_single_digit_hour(self):
        """Should handle single digit hours."""
        assert _extract_timestamp("[1:23:45] Text") == "1:23:45"

    def test_no_timestamp(self):
        """Should return None for lines without timestamps."""
        assert _extract_timestamp("No timestamp here") is None
        assert _extract_timestamp("") is None
        assert _extract_timestamp("Just some text") is None

    def test_timestamp_not_at_start(self):
        """Should only match timestamps at start of line."""
        assert _extract_timestamp("Text [05:32] in middle") is None

    def test_whitespace_handling(self):
        """Should handle leading whitespace."""
        assert _extract_timestamp("  [05:32] Indented") == "05:32"


class TestTruncateLine:
    """Tests for _truncate_line function."""

    def test_short_line_unchanged(self):
        """Lines shorter than max should be unchanged."""
        line = "Short line"
        assert _truncate_line(line, 80) == "Short line"

    def test_long_line_truncated(self):
        """Lines longer than max should be truncated with ellipsis."""
        line = "A" * 100
        result = _truncate_line(line, 80)
        assert len(result) == 80
        assert result.endswith("...")

    def test_exact_length(self):
        """Lines exactly at max length should be unchanged."""
        line = "A" * 80
        assert _truncate_line(line, 80) == line

    def test_strips_whitespace(self):
        """Should strip leading/trailing whitespace."""
        assert _truncate_line("  text  ", 80) == "text"

    def test_custom_max_length(self):
        """Should respect custom max length."""
        line = "A" * 50
        result = _truncate_line(line, 20)
        assert len(result) == 20
        assert result.endswith("...")


class TestSearchFile:
    """Tests for _search_file function."""

    def test_search_finds_matches(self, temp_transcripts_dir: Path):
        """Should find matching lines in file."""
        transcript = temp_transcripts_dir / "meeting.txt"
        transcript.write_text(
            "[00:00] Welcome to the budget discussion\n"
            "[01:00] Let's review the action items\n"
            "[02:00] Back to the budget discussion\n"
        )

        result = _search_file(transcript, "budget", case_sensitive=False)

        assert result is not None
        assert result.match_count == 2
        assert all("budget" in m.line.lower() for m in result.matches)

    def test_search_case_insensitive(self, temp_transcripts_dir: Path):
        """Case-insensitive search should match regardless of case."""
        transcript = temp_transcripts_dir / "meeting.txt"
        transcript.write_text(
            "[00:00] The API is ready\n"
            "[01:00] Testing the api\n"
            "[02:00] API documentation\n"
        )

        result = _search_file(transcript, "api", case_sensitive=False)

        assert result is not None
        assert result.match_count == 3

    def test_search_case_sensitive(self, temp_transcripts_dir: Path):
        """Case-sensitive search should only match exact case."""
        transcript = temp_transcripts_dir / "meeting.txt"
        transcript.write_text(
            "[00:00] The API is ready\n"
            "[01:00] Testing the api\n"
            "[02:00] API documentation\n"
        )

        result = _search_file(transcript, "API", case_sensitive=True)

        assert result is not None
        assert result.match_count == 2  # Only uppercase matches

    def test_search_no_matches(self, temp_transcripts_dir: Path):
        """Should return None when no matches found."""
        transcript = temp_transcripts_dir / "meeting.txt"
        transcript.write_text("[00:00] Hello world\n")

        result = _search_file(transcript, "nonexistent", case_sensitive=False)

        assert result is None

    def test_search_extracts_timestamps(self, temp_transcripts_dir: Path):
        """Should extract timestamps from matching lines."""
        transcript = temp_transcripts_dir / "meeting.txt"
        transcript.write_text("[05:32] Budget discussion here\n")

        result = _search_file(transcript, "budget", case_sensitive=False)

        assert result is not None
        assert result.matches[0].timestamp == "05:32"

    def test_search_handles_missing_file(self, temp_transcripts_dir: Path):
        """Should return None for non-existent file."""
        nonexistent = temp_transcripts_dir / "nonexistent.txt"

        result = _search_file(nonexistent, "test", case_sensitive=False)

        assert result is None

    def test_search_handles_empty_file(self, temp_transcripts_dir: Path):
        """Should return None for empty file."""
        empty = temp_transcripts_dir / "empty.txt"
        empty.write_text("")

        result = _search_file(empty, "test", case_sensitive=False)

        assert result is None


class TestSearchTranscripts:
    """Tests for search_transcripts function."""

    def test_search_across_multiple_files(self, temp_transcripts_dir: Path, capsys):
        """Should search across all transcript files."""
        # Create multiple transcripts
        (temp_transcripts_dir / "meeting1.txt").write_text(
            "[00:00] Budget discussion item 1\n"
        )
        (temp_transcripts_dir / "meeting2.txt").write_text(
            "[00:00] Another budget meeting\n"
            "[01:00] Budget review complete\n"
        )
        (temp_transcripts_dir / "meeting3.txt").write_text(
            "[00:00] No matches here\n"
        )

        search_transcripts(temp_transcripts_dir, "budget")

        captured = capsys.readouterr()
        assert "3 matches" in captured.out
        assert "2 transcripts" in captured.out
        assert "meeting1.txt" in captured.out
        assert "meeting2.txt" in captured.out
        assert "meeting3.txt" not in captured.out  # No matches

    def test_search_empty_query(self, temp_transcripts_dir: Path, capsys):
        """Should show error for empty query."""
        search_transcripts(temp_transcripts_dir, "")

        captured = capsys.readouterr()
        assert "cannot be empty" in captured.out

    def test_search_whitespace_query(self, temp_transcripts_dir: Path, capsys):
        """Should show error for whitespace-only query."""
        search_transcripts(temp_transcripts_dir, "   ")

        captured = capsys.readouterr()
        assert "cannot be empty" in captured.out

    def test_search_no_transcripts(self, temp_transcripts_dir: Path, capsys):
        """Should show message when no transcripts exist."""
        search_transcripts(temp_transcripts_dir, "test")

        captured = capsys.readouterr()
        assert "No transcripts found" in captured.out

    def test_search_no_matches(self, temp_transcripts_dir: Path, capsys):
        """Should show friendly message when no matches found."""
        (temp_transcripts_dir / "meeting.txt").write_text("[00:00] Hello world\n")

        search_transcripts(temp_transcripts_dir, "nonexistent")

        captured = capsys.readouterr()
        assert "No results found" in captured.out
        assert "nonexistent" in captured.out

    def test_search_directory_not_found(self, tmp_path: Path, capsys):
        """Should show error for non-existent directory."""
        nonexistent = tmp_path / "nonexistent"

        search_transcripts(nonexistent, "test")

        captured = capsys.readouterr()
        assert "Directory not found" in captured.out

    def test_search_respects_limit(self, temp_transcripts_dir: Path, capsys):
        """Should limit the number of results shown."""
        # Create transcript with many matches
        lines = [f"[{i:02d}:00] Match keyword here\n" for i in range(30)]
        (temp_transcripts_dir / "meeting.txt").write_text("".join(lines))

        search_transcripts(temp_transcripts_dir, "keyword", limit=5)

        captured = capsys.readouterr()
        assert "more matches" in captured.out

    def test_search_sorts_by_match_count(self, temp_transcripts_dir: Path, capsys):
        """Should sort results by match count (most first)."""
        # File with more matches
        (temp_transcripts_dir / "many_matches.txt").write_text(
            "[00:00] Budget item 1\n"
            "[01:00] Budget item 2\n"
            "[02:00] Budget item 3\n"
        )
        # File with fewer matches
        time.sleep(0.01)  # Ensure different mtime
        (temp_transcripts_dir / "few_matches.txt").write_text(
            "[00:00] Only one budget mention\n"
        )

        search_transcripts(temp_transcripts_dir, "budget")

        captured = capsys.readouterr()
        # File with more matches should appear first
        many_pos = captured.out.find("many_matches.txt")
        few_pos = captured.out.find("few_matches.txt")
        assert many_pos < few_pos

    def test_search_shows_timestamps(self, temp_transcripts_dir: Path, capsys):
        """Should display timestamps in output."""
        (temp_transcripts_dir / "meeting.txt").write_text(
            "[05:32] Budget discussion here\n"
        )

        search_transcripts(temp_transcripts_dir, "budget")

        captured = capsys.readouterr()
        assert "[05:32]" in captured.out

    def test_search_case_sensitive_option(self, temp_transcripts_dir: Path, capsys):
        """Case-sensitive flag should affect matching."""
        (temp_transcripts_dir / "meeting.txt").write_text(
            "[00:00] API endpoint\n"
            "[01:00] api test\n"
        )

        # Case-sensitive search
        search_transcripts(temp_transcripts_dir, "API", case_sensitive=True)

        captured = capsys.readouterr()
        assert "1 match" in captured.out  # Only uppercase match


class TestFileSearchResult:
    """Tests for FileSearchResult dataclass."""

    def test_match_count(self):
        """match_count should return number of matches."""
        result = FileSearchResult(
            filepath=Path("/test.txt"),
            matches=[
                SearchMatch(line_number=1, line="test"),
                SearchMatch(line_number=2, line="test"),
            ],
        )

        assert result.match_count == 2

    def test_empty_matches(self):
        """match_count should be 0 for empty matches."""
        result = FileSearchResult(
            filepath=Path("/test.txt"),
            matches=[],
        )

        assert result.match_count == 0


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_transcripts_dir(tmp_path: Path) -> Path:
    """Temporary transcripts directory."""
    transcripts = tmp_path / "transcripts"
    transcripts.mkdir(parents=True)
    return transcripts
