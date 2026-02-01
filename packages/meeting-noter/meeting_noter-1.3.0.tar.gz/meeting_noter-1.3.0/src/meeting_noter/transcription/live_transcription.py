"""Live transcription during recording.

Buffers audio chunks and transcribes them in a background thread,
writing segments to a .live.txt file that can be tailed by the CLI.

Uses overlapping windows for lower latency: keeps a 5-second context window
but transcribes every 1 second, only outputting new content.
"""

from __future__ import annotations

import sys
import numpy as np
from collections import deque
from pathlib import Path
from queue import Queue, Empty
from threading import Thread, Event
from typing import Optional
from datetime import datetime


class LiveTranscriber:
    """Transcribes audio in real-time during recording.

    Uses overlapping windows approach:
    - Maintains a rolling window of audio (default 5 seconds)
    - Transcribes every `slide_seconds` (default 1 second)
    - Only outputs new segments to avoid duplicates
    """

    def __init__(
        self,
        output_path: Path,
        sample_rate: int = 48000,
        channels: int = 2,
        window_seconds: float = 5.0,
        slide_seconds: float = 1.0,
        model_size: str = "tiny.en",
    ):
        """Initialize the live transcriber.

        Args:
            output_path: Path to write live transcript (will use .live.txt suffix in live/ subfolder)
            sample_rate: Audio sample rate
            channels: Number of audio channels
            window_seconds: Size of the context window for transcription
            slide_seconds: How often to transcribe (lower = more responsive, higher CPU)
            model_size: Whisper model to use (tiny.en recommended for speed)
        """
        # Put live transcripts in a 'live/' subfolder to keep recordings folder clean
        live_dir = output_path.parent / "live"
        live_dir.mkdir(exist_ok=True)
        self.output_path = live_dir / (output_path.stem + ".live.txt")
        self.sample_rate = sample_rate
        self.channels = channels
        self.window_seconds = window_seconds
        self.slide_seconds = slide_seconds
        self.model_size = model_size

        self._audio_queue: Queue[np.ndarray] = Queue()
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        self._model = None
        self._start_time: Optional[datetime] = None
        self._recording_offset = 0.0  # Current position in recording (seconds)
        self._last_output_end = 0.0  # End time of last outputted segment

    def start(self):
        """Start the live transcription thread."""
        self._stop_event.clear()
        self._start_time = datetime.now()
        self._recording_offset = 0.0
        self._last_output_end = 0.0

        # Create/clear the output file
        with open(self.output_path, "w") as f:
            f.write(f"Live Transcription - {self._start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 40 + "\n\n")

        self._thread = Thread(target=self._transcribe_loop, daemon=True)
        self._thread.start()

    def write(self, audio: np.ndarray):
        """Add audio chunk to the transcription queue.

        Args:
            audio: Audio data (float32, -1 to 1)
        """
        if not self._stop_event.is_set():
            self._audio_queue.put(audio.copy())

    def stop(self):
        """Stop the live transcription thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=10.0)
            self._thread = None
        self._model = None

    def _load_model(self):
        """Load the Whisper model (lazy loading)."""
        if self._model is not None:
            return

        try:
            from faster_whisper import WhisperModel

            # Check for bundled model
            bundled_path = None
            try:
                from meeting_noter_models import get_model_path
                bundled_path = get_model_path()
                if not (bundled_path.exists() and (bundled_path / "model.bin").exists()):
                    bundled_path = None
            except ImportError:
                pass

            # Try GPU acceleration first, fall back to CPU if not supported
            model_path = str(bundled_path) if (bundled_path and self.model_size == "tiny.en") else self.model_size

            try:
                # Try GPU with float16 first
                self._model = WhisperModel(
                    model_path,
                    device="cuda",
                    compute_type="float16",
                )
            except Exception:
                # Fall back to CPU with int8 (fastest CPU option)
                self._model = WhisperModel(
                    model_path,
                    device="cpu",
                    compute_type="int8",
                )
        except Exception as e:
            print(f"Failed to load Whisper model: {e}", file=sys.stderr)
            self._model = None

    def _transcribe_loop(self):
        """Main transcription loop with overlapping windows."""
        # Rolling buffer using deque for efficient sliding
        window_samples = int(self.window_seconds * self.sample_rate)
        slide_samples = int(self.slide_seconds * self.sample_rate)

        # Buffer holds raw audio samples
        rolling_buffer: deque[float] = deque(maxlen=window_samples)
        samples_since_last_transcribe = 0

        # Load model on first use
        self._load_model()
        if self._model is None:
            return

        while not self._stop_event.is_set():
            try:
                # Collect audio chunks
                try:
                    chunk = self._audio_queue.get(timeout=0.1)

                    # Add samples to rolling buffer (batch extend is faster than per-sample append)
                    rolling_buffer.extend(chunk)

                    samples_since_last_transcribe += len(chunk)
                    self._recording_offset += len(chunk) / self.sample_rate

                except Empty:
                    if self._stop_event.is_set():
                        break
                    continue

                # Transcribe every slide_seconds
                if samples_since_last_transcribe >= slide_samples and len(rolling_buffer) >= slide_samples:
                    self._transcribe_window(rolling_buffer)
                    samples_since_last_transcribe = 0

            except Exception as e:
                print(f"Live transcription error: {e}", file=sys.stderr)

        # Final transcription on stop
        if len(rolling_buffer) > 0:
            self._transcribe_window(rolling_buffer)

    def _transcribe_window(self, rolling_buffer: deque):
        """Transcribe the current window and output new segments."""
        if not rolling_buffer or self._model is None:
            return

        try:
            # Convert deque to numpy array (ensure float32 for Whisper)
            audio = np.array(list(rolling_buffer), dtype=np.float32)

            # Convert stereo to mono if needed
            if self.channels == 2 and len(audio) % 2 == 0:
                audio = audio.reshape(-1, 2).mean(axis=1).astype(np.float32)

            # Resample to 16kHz if needed (Whisper expects 16kHz)
            if self.sample_rate != 16000:
                audio = self._resample(audio, self.sample_rate, 16000).astype(np.float32)

            # Calculate window timing
            window_duration = len(rolling_buffer) / self.sample_rate
            window_start = self._recording_offset - window_duration

            # Transcribe using faster-whisper
            segments, _ = self._model.transcribe(
                audio,
                beam_size=1,  # Fastest
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=200),
            )

            # Write only NEW segments to file
            with open(self.output_path, "a") as f:
                for segment in segments:
                    # Calculate absolute timestamp
                    abs_start = window_start + segment.start
                    abs_end = window_start + segment.end

                    # Only output if this segment is new (starts after last output)
                    if abs_start >= self._last_output_end - 0.5:  # 0.5s tolerance for overlap
                        text = segment.text.strip()
                        if text:
                            timestamp = self._format_timestamp(abs_start)
                            f.write(f"{timestamp} {text}\n")
                            f.flush()
                            self._last_output_end = abs_end

        except Exception as e:
            print(f"Transcription error: {e}", file=sys.stderr)

    @staticmethod
    def _resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Simple resampling using linear interpolation."""
        if orig_sr == target_sr:
            return audio

        duration = len(audio) / orig_sr
        target_length = int(duration * target_sr)

        # Use numpy interpolation (returns float64, so cast back)
        indices = np.linspace(0, len(audio) - 1, target_length)
        return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds as [MM:SS]."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"[{minutes:02d}:{secs:02d}]"

    @property
    def live_file_path(self) -> Path:
        """Get the path to the live transcript file."""
        return self.output_path
