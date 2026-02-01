"""System audio capture using ScreenCaptureKit (macOS 12.3+).

This captures system audio by requesting Screen Recording permission,
similar to how Notion and other apps work. No special audio devices needed.
"""

from __future__ import annotations

import ctypes
import numpy as np
from collections import deque
from queue import Queue, Empty
from threading import Event, Thread
from typing import Optional
import sys


SAMPLE_RATE = 48000
CHANNELS = 2


class ScreenCaptureAudio:
    """Captures system audio using ScreenCaptureKit.

    Requires Screen Recording permission (System Settings > Privacy > Screen Recording).
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE, channels: int = CHANNELS):
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_queue: Queue[np.ndarray] = Queue()
        self._is_running = False
        self._stream = None
        self._delegate = None
        self._dispatch_queue = None

    def _check_availability(self) -> bool:
        """Check if ScreenCaptureKit is available."""
        if sys.platform != "darwin":
            return False
        try:
            import ScreenCaptureKit
            return True
        except ImportError:
            return False

    def start(self) -> bool:
        """Start capturing system audio.

        Returns True if successful, False if not available or permission denied.
        """
        if not self._check_availability():
            return False

        try:
            import ScreenCaptureKit as SCK
            import CoreMedia as CM
            from Foundation import NSObject
            import threading

            # Try to import dispatch queue creation
            dispatch_queue_create = None
            DISPATCH_QUEUE_SERIAL = None
            try:
                from libdispatch import dispatch_queue_create, DISPATCH_QUEUE_SERIAL
            except ImportError:
                try:
                    from dispatch import dispatch_queue_create, DISPATCH_QUEUE_SERIAL
                except ImportError:
                    pass  # Will use None for queue, ScreenCaptureKit uses default

            audio_queue = self.audio_queue
            parent = self

            # Create delegate class for receiving audio data
            class StreamOutput(NSObject):
                def stream_didOutputSampleBuffer_ofType_(self, stream, sampleBuffer, outputType):
                    # Only process audio (type 1), ignore video (type 0)
                    if outputType != 1:
                        return

                    try:
                        blockBuffer = CM.CMSampleBufferGetDataBuffer(sampleBuffer)
                        if blockBuffer is None:
                            return

                        length = CM.CMBlockBufferGetDataLength(blockBuffer)
                        if length == 0:
                            return

                        # Create contiguous buffer copy
                        result = CM.CMBlockBufferCreateContiguous(
                            None, blockBuffer, None, None, 0, length, 0, None
                        )

                        if result[0] == 0:  # noErr
                            contigBuffer = result[1]
                            dataResult = CM.CMBlockBufferGetDataPointer(
                                contigBuffer, 0, None, None, None
                            )

                            if dataResult[0] == 0:
                                dataPtr = dataResult[3]

                                # First element of tuple is the memory address
                                if isinstance(dataPtr, tuple) and len(dataPtr) > 0:
                                    ptr_addr = dataPtr[0]
                                    num_floats = length // 4

                                    # Cast pointer to float array
                                    float_ptr = ctypes.cast(
                                        ptr_addr, ctypes.POINTER(ctypes.c_float)
                                    )
                                    audio = np.ctypeslib.as_array(
                                        float_ptr, shape=(num_floats,)
                                    ).copy()

                                    if len(audio) > 0:
                                        audio_queue.put(audio)

                    except Exception:
                        pass

                def stream_didStopWithError_(self, stream, error):
                    parent._is_running = False

            self._delegate = StreamOutput.alloc().init()

            # Create dispatch queue if available, otherwise use None (default queue)
            if dispatch_queue_create is not None:
                self._dispatch_queue = dispatch_queue_create(
                    b"com.meetingnoter.screencapture",
                    DISPATCH_QUEUE_SERIAL
                )
            else:
                self._dispatch_queue = None

            # Get shareable content
            content_ready = threading.Event()
            content_result = [None, None]

            def on_content(content, error):
                content_result[0] = content
                content_result[1] = error
                content_ready.set()

            SCK.SCShareableContent.getShareableContentWithCompletionHandler_(on_content)

            if not content_ready.wait(timeout=5.0):
                return False

            content, error = content_result
            if error or not content:
                return False

            if not content.displays() or len(content.displays()) == 0:
                return False

            # Create filter for main display
            display = content.displays()[0]
            contentFilter = SCK.SCContentFilter.alloc().initWithDisplay_excludingWindows_(
                display, []
            )

            # Configure stream
            config = SCK.SCStreamConfiguration.alloc().init()

            # Audio settings
            config.setCapturesAudio_(True)
            config.setExcludesCurrentProcessAudio_(False)
            config.setSampleRate_(self.sample_rate)
            config.setChannelCount_(self.channels)

            # Minimal video settings (required for audio to work)
            # Note: 1x1 causes errors, need at least ~100x100
            config.setWidth_(100)
            config.setHeight_(100)
            config.setMinimumFrameInterval_(CM.CMTimeMake(1, 2))  # 0.5 fps

            # Create stream
            self._stream = SCK.SCStream.alloc().initWithFilter_configuration_delegate_(
                contentFilter, config, self._delegate
            )

            if self._stream is None:
                return False

            # Add both video and audio outputs (both required for audio to work)
            self._stream.addStreamOutput_type_sampleHandlerQueue_error_(
                self._delegate, 0, self._dispatch_queue, None  # Video
            )
            self._stream.addStreamOutput_type_sampleHandlerQueue_error_(
                self._delegate, 1, self._dispatch_queue, None  # Audio
            )

            # Start capture
            start_ready = threading.Event()
            start_error = [None]

            def on_start(error):
                start_error[0] = error
                start_ready.set()

            self._stream.startCaptureWithCompletionHandler_(on_start)

            if not start_ready.wait(timeout=5.0):
                return False

            if start_error[0]:
                error = start_error[0]
                error_code = error.code()
                if error_code == 1003:
                    print("Screen Recording permission required.")
                    print("  Go to: System Settings > Privacy & Security > Screen Recording")
                    print("  Enable permission for Terminal/your app, then restart.")
                return False

            self._is_running = True
            return True

        except Exception as e:
            print(f"ScreenCaptureKit error: {e}")
            return False

    def stop(self):
        """Stop capturing."""
        self._is_running = False

        if self._stream:
            try:
                stop_done = Event()
                self._stream.stopCaptureWithCompletionHandler_(lambda e: stop_done.set())
                stop_done.wait(timeout=2.0)
            except Exception:
                pass
            self._stream = None

    def get_audio(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Get captured audio data."""
        try:
            return self.audio_queue.get(timeout=timeout)
        except Empty:
            return None

    @property
    def is_running(self) -> bool:
        return self._is_running


class CombinedAudioCapture:
    """Captures both microphone and system audio (meeting participants).

    Uses default microphone for user's voice and ScreenCaptureKit for system audio.
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self._sample_rate = sample_rate
        self._channels = CHANNELS
        self.audio_queue: Queue[np.ndarray] = Queue()
        self.stop_event = Event()

        self._mic_capture = None
        self._system_capture = None
        self._has_system_audio = False
        self._output_thread = None

    def start(self):
        """Start capturing from microphone and system audio."""
        from meeting_noter.audio.capture import AudioCapture

        self.stop_event.clear()

        # Start microphone capture
        self._mic_capture = AudioCapture(sample_rate=self._sample_rate)
        self._mic_capture.start()
        self._channels = self._mic_capture.channels

        # Try ScreenCaptureKit for system audio
        self._system_capture = ScreenCaptureAudio(
            sample_rate=self._sample_rate,
            channels=self._channels
        )
        self._has_system_audio = self._system_capture.start()

        if self._has_system_audio:
            print("Capturing: microphone + system audio (ScreenCaptureKit)")
        else:
            print("Capturing: microphone only")
            print("  Grant Screen Recording permission to capture other participants")

        # Start output thread
        self._output_thread = Thread(target=self._process_audio, daemon=True)
        self._output_thread.start()

    def _process_audio(self):
        """Process and output audio from both sources."""
        # Ring buffers for accumulating audio
        mic_buffer = deque(maxlen=self._sample_rate)  # 1 second buffer
        sys_buffer = deque(maxlen=self._sample_rate)

        # Target chunk size (20ms at sample_rate)
        chunk_size = int(self._sample_rate * 0.02)

        while not self.stop_event.is_set():
            # Collect mic audio
            if self._mic_capture:
                mic_audio = self._mic_capture.get_audio(timeout=0.01)
                if mic_audio is not None:
                    mic_buffer.extend(mic_audio.flatten())

            # Collect system audio
            if self._system_capture and self._system_capture.is_running:
                sys_audio = self._system_capture.get_audio(timeout=0.01)
                if sys_audio is not None:
                    sys_buffer.extend(sys_audio.flatten())

            # Output when we have enough mic samples
            if len(mic_buffer) >= chunk_size:
                # Get mic chunk
                mic_chunk = np.array([mic_buffer.popleft() for _ in range(min(chunk_size, len(mic_buffer)))], dtype=np.float32)

                # Get matching system audio if available
                if self._has_system_audio and len(sys_buffer) >= chunk_size:
                    sys_chunk = np.array([sys_buffer.popleft() for _ in range(min(chunk_size, len(sys_buffer)))], dtype=np.float32)

                    # Mix: average the two sources
                    min_len = min(len(mic_chunk), len(sys_chunk))
                    if min_len > 0:
                        mixed = np.clip(mic_chunk[:min_len] * 0.7 + sys_chunk[:min_len] * 0.7, -1.0, 1.0)
                        self.audio_queue.put(mixed)
                    else:
                        self.audio_queue.put(mic_chunk)
                else:
                    # Just output mic
                    self.audio_queue.put(mic_chunk)

    def stop(self):
        """Stop all capture."""
        self.stop_event.set()

        if self._mic_capture:
            self._mic_capture.stop()
        if self._system_capture:
            self._system_capture.stop()

    def get_audio(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Get mixed audio data."""
        try:
            return self.audio_queue.get(timeout=timeout)
        except Empty:
            return None

    @property
    def channels(self) -> int:
        return self._channels

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def has_system_audio(self) -> bool:
        return self._has_system_audio
