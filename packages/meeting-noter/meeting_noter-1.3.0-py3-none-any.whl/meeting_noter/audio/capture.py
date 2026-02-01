"""Audio capture from default microphone."""

from __future__ import annotations

import numpy as np
import sounddevice as sd
from queue import Queue
from threading import Event
from typing import Optional, Union


SAMPLE_RATE = 48000  # Native sample rate for macOS devices
CHANNELS = 2  # Capture stereo for better quality
BLOCK_SIZE = 1024


def find_capture_device() -> tuple[Optional[int], bool]:
    """Find the default microphone for capture.

    Returns:
        Tuple of (device_index, has_system_audio)
        has_system_audio is always False - system audio comes from ScreenCaptureKit
    """
    # Use default input device (microphone)
    try:
        default_input = sd.default.device[0]
        if default_input is not None and default_input >= 0:
            device_info = sd.query_devices(default_input)
            if device_info["max_input_channels"] > 0:
                return default_input, False
    except Exception:
        pass

    # Fallback: find any real input device (skip virtual devices)
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device["max_input_channels"] > 0:
            name = device["name"].lower()
            # Skip virtual audio devices
            if "blackhole" in name or "virtual" in name or "aggregate" in name:
                continue
            return i, False

    # Last resort: any input device
    for i, device in enumerate(devices):
        if device["max_input_channels"] > 0:
            return i, False

    return None, False


def find_capture_device_simple() -> Optional[int]:
    """Simple wrapper for backward compatibility."""
    device_idx, _ = find_capture_device()
    return device_idx


def find_default_microphone() -> Optional[int]:
    """Find the default microphone device."""
    try:
        default_input = sd.default.device[0]
        if default_input is not None and default_input >= 0:
            return default_input
    except Exception:
        pass
    return None


# Backward compatibility alias
find_capture_device_legacy = find_capture_device_simple


def find_device_by_name(name: str) -> Optional[int]:
    """Find a device by name (partial match)."""
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if name.lower() in device["name"].lower():
            return i
    return None


class AudioCapture:
    """Captures audio from default microphone."""

    def __init__(
        self,
        device: Union[int, str, None] = None,
        sample_rate: int = SAMPLE_RATE,
        channels: Optional[int] = None,
        block_size: int = BLOCK_SIZE,
    ):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.audio_queue: Queue[np.ndarray] = Queue()
        self.stop_event = Event()
        self.stream: Optional[sd.InputStream] = None

        # Find device
        self.has_system_audio = False  # System audio comes from ScreenCaptureKit
        if device is None:
            self.device_index, _ = find_capture_device()
            if self.device_index is None:
                raise RuntimeError(
                    "No audio input device found. Please check your microphone."
                )
        elif isinstance(device, str):
            self.device_index = find_device_by_name(device)
            if self.device_index is None:
                raise RuntimeError(f"Device '{device}' not found.")
        else:
            self.device_index = device

        # Get actual channel count from device (use up to 2 channels)
        device_info = sd.query_devices(self.device_index)
        max_channels = device_info["max_input_channels"]
        self.channels = channels if channels is not None else min(max_channels, CHANNELS)

        print(f"Using microphone: {device_info['name']}")

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags,
    ):
        """Callback for audio stream."""
        if status:
            print(f"Audio status: {status}")
        # Copy data to queue
        self.audio_queue.put(indata.copy())

    def start(self):
        """Start capturing audio."""
        self.stop_event.clear()
        self.stream = sd.InputStream(
            device=self.device_index,
            channels=self.channels,
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            dtype=np.float32,
            callback=self._audio_callback,
        )
        self.stream.start()

    def stop(self):
        """Stop capturing audio."""
        self.stop_event.set()
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def get_audio(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Get audio data from queue."""
        try:
            return self.audio_queue.get(timeout=timeout)
        except:
            return None

    def get_all_audio(self) -> np.ndarray:
        """Get all accumulated audio from queue."""
        chunks = []
        while not self.audio_queue.empty():
            try:
                chunks.append(self.audio_queue.get_nowait())
            except:
                break
        if chunks:
            return np.concatenate(chunks)
        return np.array([], dtype=np.float32)


class SilenceDetector:
    """Detects extended silence in audio stream."""

    def __init__(
        self,
        threshold: float = 0.01,
        silence_duration: float = 60.0,
        sample_rate: int = SAMPLE_RATE,
    ):
        self.threshold = threshold
        self.silence_samples = int(silence_duration * sample_rate)
        self.current_silence = 0
        self.sample_rate = sample_rate

    def update(self, audio: np.ndarray) -> bool:
        """Update with new audio data.

        Returns True if extended silence is detected (meeting likely ended).
        """
        rms = np.sqrt(np.mean(audio ** 2))

        if rms < self.threshold:
            self.current_silence += len(audio)
        else:
            self.current_silence = 0

        return self.current_silence >= self.silence_samples

    def reset(self):
        """Reset silence counter."""
        self.current_silence = 0

    def is_audio_present(self, audio: np.ndarray) -> bool:
        """Check if there's meaningful audio (not just silence)."""
        rms = np.sqrt(np.mean(audio ** 2))
        return rms >= self.threshold
