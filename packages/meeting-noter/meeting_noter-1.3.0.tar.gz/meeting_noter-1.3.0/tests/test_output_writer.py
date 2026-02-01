"""Tests for the output writer module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import time

import pytest

from meeting_noter.output.writer import (
    format_duration,
    format_size,
    get_audio_duration,
    list_recordings,
)


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_format_duration_seconds(self):
        """Durations under a minute should show seconds only."""
        assert format_duration(0) == "0s"
        assert format_duration(1) == "1s"
        assert format_duration(30) == "30s"
        assert format_duration(59) == "59s"
        assert format_duration(45.7) == "46s"  # Rounds to nearest

    def test_format_duration_minutes(self):
        """Durations under an hour should show minutes and seconds."""
        assert format_duration(60) == "1m 0s"
        assert format_duration(90) == "1m 30s"
        assert format_duration(330) == "5m 30s"
        assert format_duration(3599) == "59m 59s"

    def test_format_duration_hours(self):
        """Durations over an hour should show hours and minutes."""
        assert format_duration(3600) == "1h 0m"
        assert format_duration(3660) == "1h 1m"
        assert format_duration(4980) == "1h 23m"
        assert format_duration(7200) == "2h 0m"
        assert format_duration(86400) == "24h 0m"


class TestFormatSize:
    """Tests for format_size function."""

    def test_format_size_bytes(self):
        """Small sizes should show bytes."""
        assert format_size(0) == "0 B"
        assert format_size(512) == "512 B"
        assert format_size(1023) == "1023 B"

    def test_format_size_kilobytes(self):
        """Medium sizes should show KB."""
        assert format_size(1024) == "1.0 KB"
        assert format_size(1536) == "1.5 KB"
        assert format_size(102400) == "100.0 KB"
        assert format_size(1048575) == "1024.0 KB"

    def test_format_size_megabytes(self):
        """Large sizes should show MB."""
        assert format_size(1048576) == "1.0 MB"
        assert format_size(1572864) == "1.5 MB"
        assert format_size(10485760) == "10.0 MB"
        assert format_size(104857600) == "100.0 MB"


class TestGetAudioDuration:
    """Tests for get_audio_duration function."""

    def test_estimate_audio_duration(self, temp_recordings_dir: Path):
        """Duration should be estimated from file size at 128kbps."""
        # 128kbps = 16KB/s
        # 160KB should be ~10 seconds
        mp3_path = temp_recordings_dir / "test.mp3"
        mp3_path.write_bytes(b"\x00" * 160000)

        duration = get_audio_duration(mp3_path)

        assert duration is not None
        assert 9 <= duration <= 11  # Allow some tolerance

    def test_get_audio_duration_file_not_found(self, temp_recordings_dir: Path):
        """Non-existent file should return None."""
        mp3_path = temp_recordings_dir / "nonexistent.mp3"

        duration = get_audio_duration(mp3_path)

        assert duration is None

    def test_get_audio_duration_empty_file(self, temp_recordings_dir: Path):
        """Empty file should return 0 duration."""
        mp3_path = temp_recordings_dir / "empty.mp3"
        mp3_path.write_bytes(b"")

        duration = get_audio_duration(mp3_path)

        assert duration == 0.0


class TestListRecordings:
    """Tests for list_recordings function."""

    def test_list_recordings_empty(self, temp_recordings_dir: Path, capsys):
        """Empty directory should show appropriate message."""
        list_recordings(temp_recordings_dir)

        captured = capsys.readouterr()
        assert "No recordings found" in captured.out

    def test_list_recordings_sorted(self, multiple_recordings: list[Path], capsys):
        """Recordings should be listed most recent first."""
        output_dir = multiple_recordings[0].parent

        list_recordings(output_dir, limit=10)

        captured = capsys.readouterr()

        # Most recent should appear first (meeting_4)
        assert "meeting_4" in captured.out
        assert "meeting_0" in captured.out

        # Check order - meeting_4 should come before meeting_0
        pos_4 = captured.out.find("meeting_4")
        pos_0 = captured.out.find("meeting_0")
        assert pos_4 < pos_0, "Most recent recording should appear first"

    def test_list_recordings_with_limit(self, multiple_recordings: list[Path], capsys):
        """Limit parameter should restrict output count."""
        output_dir = multiple_recordings[0].parent

        list_recordings(output_dir, limit=3)

        captured = capsys.readouterr()

        # Should show "and X more recordings"
        assert "more recordings" in captured.out

    def test_list_recordings_shows_transcript_status(
        self, sample_mp3_file: Path, sample_transcript_file: Path, capsys
    ):
        """Should indicate if transcript exists."""
        output_dir = sample_mp3_file.parent

        list_recordings(output_dir)

        captured = capsys.readouterr()

        # Our sample has a transcript
        assert "Yes" in captured.out

    def test_list_recordings_shows_no_transcript(
        self, sample_mp3_file: Path, capsys
    ):
        """Should indicate when no transcript exists."""
        output_dir = sample_mp3_file.parent

        list_recordings(output_dir)

        captured = capsys.readouterr()

        # No transcript for this file
        assert "No" in captured.out

    def test_list_recordings_directory_not_found(self, tmp_path: Path, capsys):
        """Non-existent directory should show error."""
        nonexistent = tmp_path / "nonexistent"

        list_recordings(nonexistent)

        captured = capsys.readouterr()
        assert "Directory not found" in captured.out

    def test_list_recordings_shows_file_info(
        self, sample_mp3_file: Path, capsys
    ):
        """Output should include date, duration, size, and filename."""
        output_dir = sample_mp3_file.parent

        list_recordings(output_dir)

        captured = capsys.readouterr()

        # Should have column headers
        assert "Date" in captured.out
        assert "Duration" in captured.out
        assert "Size" in captured.out
        assert "File" in captured.out

        # Should have the filename
        assert "test_meeting" in captured.out

    def test_list_recordings_shows_total_count(
        self, multiple_recordings: list[Path], capsys
    ):
        """Output should show total count of recordings."""
        output_dir = multiple_recordings[0].parent

        list_recordings(output_dir)

        captured = capsys.readouterr()

        assert "Total: 5 recordings" in captured.out
