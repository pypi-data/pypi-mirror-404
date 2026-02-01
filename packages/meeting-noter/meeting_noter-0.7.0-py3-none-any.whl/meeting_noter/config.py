"""Configuration management for Meeting Noter."""

from __future__ import annotations

import functools
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import click


def generate_meeting_name() -> str:
    """Generate a default meeting name with current timestamp."""
    now = datetime.now()
    return now.strftime("%d_%b_%Y_%H%M")  # e.g., "29_Jan_2026_1430"


def is_default_meeting_name(name: str) -> bool:
    """Check if a name matches the default timestamp pattern."""
    # Pattern: DD_Mon_YYYY_HHMM (e.g., 29_Jan_2026_1430)
    return bool(re.match(r"^\d{2}_[A-Z][a-z]{2}_\d{4}_\d{4}$", name))


DEFAULT_CONFIG_DIR = Path.home() / ".config" / "meeting-noter"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "recordings_dir": str(Path.home() / "meetings"),
    "transcripts_dir": str(Path.home() / "meetings"),
    "whisper_model": "tiny.en",
    "auto_transcribe": True,
    "silence_timeout": 5,  # Minutes of silence before stopping recording
    "capture_system_audio": True,  # Capture other participants via ScreenCaptureKit
    "show_menubar": False,
    "setup_complete": False,
}


class Config:
    """Configuration manager for Meeting Noter."""

    def __init__(self, config_path: Path = DEFAULT_CONFIG_FILE):
        self.config_path = config_path
        self._data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from disk."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}
        else:
            self._data = {}

        # Fill in missing defaults
        for key, value in DEFAULT_CONFIG.items():
            if key not in self._data:
                self._data[key] = value

    def save(self) -> None:
        """Save configuration to disk."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self._data, f, indent=4)

    @property
    def recordings_dir(self) -> Path:
        """Get recordings directory."""
        return Path(self._data["recordings_dir"]).expanduser()

    @recordings_dir.setter
    def recordings_dir(self, value: Path | str) -> None:
        """Set recordings directory."""
        self._data["recordings_dir"] = str(value)

    @property
    def transcripts_dir(self) -> Path:
        """Get transcripts directory."""
        return Path(self._data["transcripts_dir"]).expanduser()

    @transcripts_dir.setter
    def transcripts_dir(self, value: Path | str) -> None:
        """Set transcripts directory."""
        self._data["transcripts_dir"] = str(value)

    @property
    def whisper_model(self) -> str:
        """Get Whisper model name."""
        return self._data["whisper_model"]

    @whisper_model.setter
    def whisper_model(self, value: str) -> None:
        """Set Whisper model name."""
        self._data["whisper_model"] = value

    @property
    def auto_transcribe(self) -> bool:
        """Get auto-transcribe setting."""
        return self._data["auto_transcribe"]

    @auto_transcribe.setter
    def auto_transcribe(self, value: bool) -> None:
        """Set auto-transcribe setting."""
        self._data["auto_transcribe"] = value

    @property
    def silence_timeout(self) -> int:
        """Get silence timeout in minutes."""
        return self._data.get("silence_timeout", 5)

    @silence_timeout.setter
    def silence_timeout(self, value: int) -> None:
        """Set silence timeout in minutes."""
        self._data["silence_timeout"] = value

    @property
    def capture_system_audio(self) -> bool:
        """Get capture system audio setting."""
        return self._data.get("capture_system_audio", True)

    @capture_system_audio.setter
    def capture_system_audio(self, value: bool) -> None:
        """Set capture system audio setting."""
        self._data["capture_system_audio"] = value

    @property
    def show_menubar(self) -> bool:
        """Get show menubar setting."""
        return self._data.get("show_menubar", False)

    @show_menubar.setter
    def show_menubar(self, value: bool) -> None:
        """Set show menubar setting."""
        self._data["show_menubar"] = value

    @property
    def setup_complete(self) -> bool:
        """Check if setup has been completed."""
        return self._data.get("setup_complete", False)

    @setup_complete.setter
    def setup_complete(self, value: bool) -> None:
        """Set setup completion status."""
        self._data["setup_complete"] = value

    def __getitem__(self, key: str) -> Any:
        """Get config value by key."""
        return self._data.get(key, DEFAULT_CONFIG.get(key))

    def __setitem__(self, key: str, value: Any) -> None:
        """Set config value by key."""
        self._data[key] = value


# Global config instance (lazy loaded)
_config: Config | None = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def is_setup_complete() -> bool:
    """Check if setup has been completed."""
    return get_config().setup_complete


def require_setup(f):
    """Decorator that ensures basic config exists.

    Now more lenient - just ensures config directories exist.
    Setup is optional since we can use any microphone.

    Usage:
        @cli.command()
        @require_setup
        def my_command():
            ...
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        config = get_config()
        # Ensure directories exist
        config.recordings_dir.mkdir(parents=True, exist_ok=True)
        config.transcripts_dir.mkdir(parents=True, exist_ok=True)
        return f(*args, **kwargs)
    return wrapper
