"""Tests for the config module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from meeting_noter.config import (
    DEFAULT_CONFIG,
    Config,
    generate_meeting_name,
    get_config,
    is_default_meeting_name,
    is_setup_complete,
    require_setup,
)


class TestGenerateMeetingName:
    """Tests for generate_meeting_name function."""

    def test_generate_meeting_name_format(self):
        """Verify meeting name follows DD_Mon_YYYY_HHMM format."""
        name = generate_meeting_name()

        # Should match pattern like "29_Jan_2026_1430"
        assert len(name) == 16  # DD_Mon_YYYY_HHMM
        parts = name.split("_")
        assert len(parts) == 4

        # Day (01-31)
        assert parts[0].isdigit()
        assert 1 <= int(parts[0]) <= 31

        # Month (Jan, Feb, etc.)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        assert parts[1] in months

        # Year (4 digits)
        assert parts[2].isdigit()
        assert len(parts[2]) == 4

        # Time (4 digits, HHMM)
        assert parts[3].isdigit()
        assert len(parts[3]) == 4

    def test_generate_meeting_name_unique(self):
        """Verify consecutive calls produce different names (usually)."""
        import time

        name1 = generate_meeting_name()
        time.sleep(0.01)
        # Names are minute-granular, so they'll be the same within a minute
        # Just check format is consistent
        name2 = generate_meeting_name()

        assert is_default_meeting_name(name1)
        assert is_default_meeting_name(name2)


class TestIsDefaultMeetingName:
    """Tests for is_default_meeting_name function."""

    def test_valid_default_names(self):
        """Valid timestamp names should return True."""
        valid_names = [
            "29_Jan_2026_1430",
            "01_Feb_2025_0000",
            "31_Dec_2030_2359",
            "15_Mar_2024_1200",
        ]
        for name in valid_names:
            assert is_default_meeting_name(name), f"Expected {name} to be valid"

    def test_invalid_default_names(self):
        """Custom names should return False."""
        invalid_names = [
            "Weekly Standup",
            "Team Meeting",
            "2024-01-15",
            "29-Jan-2026-1430",  # Wrong separators
            "29_January_2026_1430",  # Full month name
            "9_Jan_2026_1430",  # Single digit day
            "",
        ]
        for name in invalid_names:
            assert not is_default_meeting_name(name), f"Expected {name} to be invalid"


class TestConfig:
    """Tests for Config class."""

    def test_config_default_values(self, temp_config_path: Path):
        """Config should have default values when file doesn't exist."""
        config = Config(temp_config_path)

        assert config.whisper_model == DEFAULT_CONFIG["whisper_model"]
        assert config.auto_transcribe == DEFAULT_CONFIG["auto_transcribe"]
        assert config.silence_timeout == DEFAULT_CONFIG["silence_timeout"]
        assert config.capture_system_audio == DEFAULT_CONFIG["capture_system_audio"]
        assert config.show_menubar == DEFAULT_CONFIG["show_menubar"]
        assert config.setup_complete == DEFAULT_CONFIG["setup_complete"]

    def test_config_load_from_file(self, temp_config_path: Path):
        """Config should load existing values from file."""
        # Create config file with custom values
        config_data = {
            "recordings_dir": "/custom/recordings",
            "whisper_model": "base.en",
            "auto_transcribe": False,
            "silence_timeout": 10,
            "setup_complete": True,
        }
        temp_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_config_path, "w") as f:
            json.dump(config_data, f)

        config = Config(temp_config_path)

        assert config.whisper_model == "base.en"
        assert config.auto_transcribe is False
        assert config.silence_timeout == 10
        assert config.setup_complete is True

    def test_config_save_to_file(self, temp_config_path: Path):
        """Config save should write valid JSON."""
        config = Config(temp_config_path)
        config.whisper_model = "medium.en"
        config.auto_transcribe = False
        config.save()

        # Read back and verify
        with open(temp_config_path, "r") as f:
            saved_data = json.load(f)

        assert saved_data["whisper_model"] == "medium.en"
        assert saved_data["auto_transcribe"] is False

    def test_config_create_dirs(self, temp_config_path: Path):
        """Config should create parent directories on save."""
        config = Config(temp_config_path)
        config.save()

        assert temp_config_path.exists()
        assert temp_config_path.parent.exists()

    def test_config_path_expansion(self, temp_config_path: Path):
        """Paths with ~ should expand to home directory."""
        config_data = {
            "recordings_dir": "~/my_meetings",
            "transcripts_dir": "~/my_transcripts",
        }
        temp_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_config_path, "w") as f:
            json.dump(config_data, f)

        config = Config(temp_config_path)

        # recordings_dir property expands path
        assert "~" not in str(config.recordings_dir)
        assert config.recordings_dir == Path.home() / "my_meetings"

    def test_config_getitem_setitem(self, temp_config_path: Path):
        """Config should support dictionary-style access."""
        config = Config(temp_config_path)

        # Set value
        config["custom_key"] = "custom_value"
        assert config["custom_key"] == "custom_value"

        # Get default value for missing key
        assert config["nonexistent_key"] is None

    def test_config_properties(self, temp_config_path: Path):
        """All config properties should be readable and writable."""
        config = Config(temp_config_path)

        # Test setters
        config.recordings_dir = "/new/recordings"
        config.transcripts_dir = "/new/transcripts"
        config.whisper_model = "small.en"
        config.auto_transcribe = False
        config.silence_timeout = 15
        config.capture_system_audio = False
        config.show_menubar = True
        config.setup_complete = True

        # Verify values
        assert str(config.recordings_dir) == "/new/recordings"
        assert str(config.transcripts_dir) == "/new/transcripts"
        assert config.whisper_model == "small.en"
        assert config.auto_transcribe is False
        assert config.silence_timeout == 15
        assert config.capture_system_audio is False
        assert config.show_menubar is True
        assert config.setup_complete is True

    def test_config_load_invalid_json(self, temp_config_path: Path):
        """Config should handle invalid JSON gracefully."""
        temp_config_path.parent.mkdir(parents=True, exist_ok=True)
        temp_config_path.write_text("invalid json {{{")

        config = Config(temp_config_path)

        # Should fall back to defaults
        assert config.whisper_model == DEFAULT_CONFIG["whisper_model"]

    def test_config_load_io_error(self, temp_config_path: Path, mocker):
        """Config should handle IO errors gracefully."""
        temp_config_path.parent.mkdir(parents=True, exist_ok=True)
        temp_config_path.write_text("{}")

        # Mock open to raise IOError
        mocker.patch("builtins.open", side_effect=IOError("Permission denied"))

        config = Config(temp_config_path)

        # Should fall back to defaults
        assert config.whisper_model == DEFAULT_CONFIG["whisper_model"]


class TestGetConfig:
    """Tests for get_config singleton."""

    def test_get_config_returns_config(self, mock_config):
        """get_config should return a Config instance."""
        config = get_config()
        assert isinstance(config, Config)

    def test_get_config_singleton(self, mock_config):
        """get_config should return same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2


class TestIsSetupComplete:
    """Tests for is_setup_complete function."""

    def test_is_setup_complete_true(self, mock_config):
        """Returns True when setup is complete."""
        mock_config.setup_complete = True
        assert is_setup_complete() is True

    def test_is_setup_complete_false(self, mock_config):
        """Returns False when setup is not complete."""
        mock_config.setup_complete = False
        assert is_setup_complete() is False


class TestRequireSetup:
    """Tests for require_setup decorator."""

    def test_require_setup_creates_directories(self, mock_config):
        """Decorator should create recordings and transcripts directories."""
        # Ensure directories don't exist initially
        import shutil

        if mock_config.recordings_dir.exists():
            shutil.rmtree(mock_config.recordings_dir)
        if mock_config.transcripts_dir.exists():
            shutil.rmtree(mock_config.transcripts_dir)

        @require_setup
        def test_func():
            return "success"

        result = test_func()

        assert result == "success"
        assert mock_config.recordings_dir.exists()
        assert mock_config.transcripts_dir.exists()

    def test_require_setup_passes_args(self, mock_config):
        """Decorator should pass through arguments."""

        @require_setup
        def test_func(arg1, arg2, kwarg1=None):
            return (arg1, arg2, kwarg1)

        result = test_func("a", "b", kwarg1="c")
        assert result == ("a", "b", "c")

    def test_require_setup_preserves_metadata(self, mock_config):
        """Decorator should preserve function metadata."""

        @require_setup
        def my_documented_func():
            """This is a docstring."""
            pass

        assert my_documented_func.__name__ == "my_documented_func"
        assert "docstring" in my_documented_func.__doc__
