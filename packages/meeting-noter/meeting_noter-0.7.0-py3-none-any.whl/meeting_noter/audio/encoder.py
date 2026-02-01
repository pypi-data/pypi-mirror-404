"""MP3 encoding for audio recordings using ffmpeg."""

from __future__ import annotations

import re
import subprocess
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

# Get bundled ffmpeg binary path
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    # Fallback to system ffmpeg
    FFMPEG_PATH = "ffmpeg"


def _sanitize_filename(name: str, max_length: int = 50) -> str:
    """Sanitize a string for use as a filename.

    Args:
        name: The name to sanitize
        max_length: Maximum length for the sanitized name

    Returns:
        A safe filename string with spaces replaced by underscores
    """
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    # Remove any character that isn't alphanumeric, underscore, or hyphen
    name = re.sub(r"[^\w\-]", "", name)
    # Truncate to max length
    if len(name) > max_length:
        name = name[:max_length]
    # Remove trailing underscores/hyphens
    name = name.rstrip("_-")
    return name


def _is_timestamp_name(name: str) -> bool:
    """Check if name is a default timestamp pattern (DD_Mon_YYYY_HHMM)."""
    return bool(re.match(r"^\d{2}_[A-Z][a-z]{2}_\d{4}_\d{4}$", name))


class MP3Encoder:
    """Encodes audio data to MP3 format using ffmpeg."""

    def __init__(
        self,
        output_path: Path,
        sample_rate: int = 16000,
        channels: int = 1,
        bitrate: int = 128,
    ):
        self.output_path = output_path
        self.sample_rate = sample_rate
        self.channels = channels
        self.bitrate = bitrate
        self._process: Optional[subprocess.Popen] = None
        self._start_ffmpeg()

    def _start_ffmpeg(self):
        """Start ffmpeg process for encoding."""
        cmd = [
            FFMPEG_PATH,
            "-y",  # Overwrite output
            "-f", "s16le",  # Input format: signed 16-bit little-endian PCM
            "-ar", str(self.sample_rate),  # Sample rate
            "-ac", str(self.channels),  # Channels
            "-i", "pipe:0",  # Read from stdin
            "-codec:a", "libmp3lame",  # MP3 encoder
            "-b:a", f"{self.bitrate}k",  # Bitrate
            "-f", "mp3",  # Output format
            str(self.output_path),
        ]
        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def encode_chunk(self, audio: np.ndarray) -> bytes:
        """Encode a chunk of audio data.

        Args:
            audio: Float32 audio data, values between -1 and 1

        Returns:
            Empty bytes (ffmpeg writes directly to file)
        """
        if self._process is None or self._process.stdin is None:
            return b""

        # Convert float32 to int16
        int_data = (audio * 32767).astype(np.int16)
        try:
            self._process.stdin.write(int_data.tobytes())
        except BrokenPipeError:
            pass
        return b""  # ffmpeg writes to file, not returning data

    def finalize(self) -> bytes:
        """Finalize encoding."""
        if self._process is not None and self._process.stdin is not None:
            try:
                self._process.stdin.close()
            except Exception:
                pass
            self._process.wait()
            self._process = None
        return b""


class RecordingSession:
    """Manages a single recording session (one meeting)."""

    def __init__(
        self,
        output_dir: Path,
        sample_rate: int = 16000,
        channels: int = 1,
        meeting_name: Optional[str] = None,
    ):
        self.output_dir = output_dir
        self.sample_rate = sample_rate
        self.channels = channels
        self.meeting_name = meeting_name
        self.encoder: Optional[MP3Encoder] = None
        self.filepath: Optional[Path] = None
        self.start_time: Optional[datetime] = None
        self.total_samples = 0

    def start(self) -> Path:
        """Start a new recording session."""
        self.start_time = datetime.now()

        if self.meeting_name:
            sanitized = _sanitize_filename(self.meeting_name)
            if _is_timestamp_name(self.meeting_name):
                # Default timestamp name - use as-is without extra prefix
                filename = f"{sanitized}.mp3"
            else:
                # Custom name - add timestamp prefix for uniqueness
                timestamp = self.start_time.strftime("%Y-%m-%d_%H%M%S")
                filename = f"{timestamp}_{sanitized}.mp3"
        else:
            timestamp = self.start_time.strftime("%Y-%m-%d_%H%M%S")
            filename = f"{timestamp}.mp3"
        self.filepath = self.output_dir / filename

        self.encoder = MP3Encoder(
            output_path=self.filepath,
            sample_rate=self.sample_rate,
            channels=self.channels,
        )
        self.total_samples = 0

        return self.filepath

    def write(self, audio: np.ndarray):
        """Write audio data to the recording."""
        if self.encoder is None:
            raise RuntimeError("Recording session not started")

        self.encoder.encode_chunk(audio)
        self.total_samples += len(audio)

    def stop(self) -> Tuple[Optional[Path], float]:
        """Stop the recording session.

        Returns:
            Tuple of (filepath, duration_seconds)
        """
        duration = 0.0
        filepath = self.filepath

        if self.encoder:
            # Finalize encoding
            self.encoder.finalize()
            duration = self.total_samples / self.sample_rate

            # Delete if too short (less than 5 seconds)
            if duration < 5.0 and filepath and filepath.exists():
                filepath.unlink()
                filepath = None

        self.encoder = None
        self.filepath = None
        self.start_time = None
        self.total_samples = 0

        return filepath, duration

    @property
    def is_active(self) -> bool:
        """Check if a recording is in progress."""
        return self.encoder is not None

    @property
    def duration(self) -> float:
        """Get current recording duration in seconds."""
        if self.sample_rate > 0:
            return self.total_samples / self.sample_rate
        return 0.0
