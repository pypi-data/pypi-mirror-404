"""Tests for the favorites management module."""

from __future__ import annotations

from pathlib import Path

import pytest

from meeting_noter.output.favorites import (
    list_favorites,
    add_favorite,
    remove_favorite,
    list_transcripts_with_favorites,
)


class TestListFavorites:
    """Tests for list_favorites function."""

    def test_list_favorites_empty(self, mock_config, capsys):
        """Should show message when no favorites."""
        list_favorites(mock_config.transcripts_dir)

        captured = capsys.readouterr()
        assert "No favorites yet" in captured.out

    def test_list_favorites_with_items(self, mock_config, capsys):
        """Should list favorite transcripts."""
        # Create transcript file
        transcript = mock_config.transcripts_dir / "meeting.txt"
        transcript.write_text("[00:00] Test content\n")

        # Add to favorites
        mock_config.add_favorite("meeting.txt")

        list_favorites(mock_config.transcripts_dir)

        captured = capsys.readouterr()
        assert "meeting.txt" in captured.out
        assert "1." in captured.out  # Index number
        assert "★" in captured.out
        assert "Total: 1 favorites" in captured.out

    def test_list_favorites_missing_file(self, mock_config, capsys):
        """Should indicate when favorite file no longer exists."""
        # Add favorite without creating file
        mock_config.add_favorite("nonexistent.txt")

        list_favorites(mock_config.transcripts_dir)

        captured = capsys.readouterr()
        assert "nonexistent.txt" in captured.out
        assert "file not found" in captured.out


class TestAddFavorite:
    """Tests for add_favorite function."""

    def test_add_favorite_success(self, mock_config, capsys):
        """Should add transcript to favorites."""
        transcript = mock_config.transcripts_dir / "meeting.txt"
        transcript.write_text("[00:00] Test content\n")

        add_favorite(mock_config.transcripts_dir, "meeting.txt")

        captured = capsys.readouterr()
        assert "Added to favorites" in captured.out
        assert mock_config.is_favorite("meeting.txt")

    def test_add_favorite_already_exists(self, mock_config, capsys):
        """Should show message when already a favorite."""
        transcript = mock_config.transcripts_dir / "meeting.txt"
        transcript.write_text("[00:00] Test content\n")

        mock_config.add_favorite("meeting.txt")
        add_favorite(mock_config.transcripts_dir, "meeting.txt")

        captured = capsys.readouterr()
        assert "Already a favorite" in captured.out

    def test_add_favorite_latest(self, mock_config, capsys):
        """Should add most recent transcript with --latest."""
        import time

        # Create two transcripts with different mtimes
        old = mock_config.transcripts_dir / "old.txt"
        old.write_text("[00:00] Old content\n")
        time.sleep(0.01)
        new = mock_config.transcripts_dir / "new.txt"
        new.write_text("[00:00] New content\n")

        add_favorite(mock_config.transcripts_dir, latest=True)

        captured = capsys.readouterr()
        assert "new.txt" in captured.out
        assert mock_config.is_favorite("new.txt")
        assert not mock_config.is_favorite("old.txt")

    def test_add_favorite_file_not_found(self, mock_config, capsys):
        """Should show error when file not found."""
        add_favorite(mock_config.transcripts_dir, "nonexistent.txt")

        captured = capsys.readouterr()
        assert "File not found" in captured.out

    def test_add_favorite_auto_adds_extension(self, mock_config, capsys):
        """Should auto-add .txt extension if missing."""
        transcript = mock_config.transcripts_dir / "meeting.txt"
        transcript.write_text("[00:00] Test content\n")

        add_favorite(mock_config.transcripts_dir, "meeting")

        captured = capsys.readouterr()
        assert "Added to favorites" in captured.out
        assert mock_config.is_favorite("meeting.txt")

    def test_add_favorite_no_filename_no_latest(self, mock_config, capsys):
        """Should show error when no filename and not using --latest."""
        add_favorite(mock_config.transcripts_dir)

        captured = capsys.readouterr()
        assert "Specify a filename or use --latest" in captured.out

    def test_add_favorite_latest_no_transcripts(self, mock_config, capsys):
        """Should show error when using --latest with no transcripts."""
        add_favorite(mock_config.transcripts_dir, latest=True)

        captured = capsys.readouterr()
        assert "No transcripts found" in captured.out


class TestRemoveFavorite:
    """Tests for remove_favorite function."""

    def test_remove_favorite_success(self, mock_config, capsys):
        """Should remove transcript from favorites."""
        mock_config.add_favorite("meeting.txt")

        remove_favorite("meeting.txt")

        captured = capsys.readouterr()
        assert "Removed from favorites" in captured.out
        assert not mock_config.is_favorite("meeting.txt")

    def test_remove_favorite_not_found(self, mock_config, capsys):
        """Should show message when not a favorite."""
        remove_favorite("nonexistent.txt")

        captured = capsys.readouterr()
        assert "Not a favorite" in captured.out

    def test_remove_favorite_auto_adds_extension(self, mock_config, capsys):
        """Should auto-add .txt extension if missing."""
        mock_config.add_favorite("meeting.txt")

        remove_favorite("meeting")

        captured = capsys.readouterr()
        assert "Removed from favorites" in captured.out
        assert not mock_config.is_favorite("meeting.txt")


class TestListTranscriptsWithFavorites:
    """Tests for list_transcripts_with_favorites function."""

    def test_list_with_favorites_indicator(self, mock_config, capsys):
        """Should show star indicator for favorites."""
        # Create transcripts
        fav = mock_config.transcripts_dir / "favorite.txt"
        fav.write_text("[00:00] Favorite content\n")
        regular = mock_config.transcripts_dir / "regular.txt"
        regular.write_text("[00:00] Regular content\n")

        # Mark one as favorite
        mock_config.add_favorite("favorite.txt")

        list_transcripts_with_favorites(mock_config.transcripts_dir)

        captured = capsys.readouterr()
        # Should show star for favorite
        assert "★" in captured.out
        assert "favorite.txt" in captured.out
        assert "regular.txt" in captured.out

    def test_list_empty_directory(self, mock_config, capsys):
        """Should show message when no transcripts."""
        list_transcripts_with_favorites(mock_config.transcripts_dir)

        captured = capsys.readouterr()
        assert "No transcripts found" in captured.out

    def test_list_directory_not_found(self, tmp_path, capsys):
        """Should show error for non-existent directory."""
        nonexistent = tmp_path / "nonexistent"

        list_transcripts_with_favorites(nonexistent)

        captured = capsys.readouterr()
        assert "Directory not found" in captured.out

    def test_list_respects_limit(self, mock_config, capsys):
        """Should limit output to specified count."""
        # Create multiple transcripts
        for i in range(15):
            transcript = mock_config.transcripts_dir / f"meeting_{i:02d}.txt"
            transcript.write_text(f"[00:00] Content {i}\n")

        list_transcripts_with_favorites(mock_config.transcripts_dir, limit=5)

        captured = capsys.readouterr()
        assert "... and 10 more" in captured.out


class TestConfigFavorites:
    """Tests for Config favorites methods."""

    def test_favorites_default_empty(self, mock_config):
        """Favorites should default to empty list."""
        assert mock_config.favorites == []

    def test_add_favorite_to_config(self, mock_config):
        """add_favorite should add to list."""
        result = mock_config.add_favorite("test.txt")

        assert result is True
        assert "test.txt" in mock_config.favorites

    def test_add_duplicate_favorite(self, mock_config):
        """add_favorite should return False for duplicates."""
        mock_config.add_favorite("test.txt")
        result = mock_config.add_favorite("test.txt")

        assert result is False
        assert mock_config.favorites.count("test.txt") == 1

    def test_remove_favorite_from_config(self, mock_config):
        """remove_favorite should remove from list."""
        mock_config.add_favorite("test.txt")
        result = mock_config.remove_favorite("test.txt")

        assert result is True
        assert "test.txt" not in mock_config.favorites

    def test_remove_nonexistent_favorite(self, mock_config):
        """remove_favorite should return False for non-existent."""
        result = mock_config.remove_favorite("nonexistent.txt")

        assert result is False

    def test_is_favorite(self, mock_config):
        """is_favorite should check membership."""
        mock_config.add_favorite("test.txt")

        assert mock_config.is_favorite("test.txt") is True
        assert mock_config.is_favorite("other.txt") is False
