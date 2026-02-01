"""Recording tab for starting/stopping meeting recordings."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QGroupBox,
)

from meeting_noter.config import get_config, generate_meeting_name, is_default_meeting_name


class RecordingWorker(QThread):
    """Background worker thread for audio recording."""

    log_message = pyqtSignal(str)
    recording_started = pyqtSignal(str)  # filepath
    recording_stopped = pyqtSignal(str, float)  # filepath, duration
    silence_stopped = pyqtSignal()  # stopped due to silence
    error = pyqtSignal(str)

    def __init__(self, output_dir: Path, meeting_name: str, silence_timeout_minutes: int = 5):
        super().__init__()
        self.output_dir = output_dir
        self.meeting_name = meeting_name
        self.silence_timeout_minutes = silence_timeout_minutes
        self._stop_requested = False
        self.saved_filepath: Optional[Path] = None

    def run(self):
        """Run the recording in background thread."""
        # Import audio modules in thread
        try:
            from meeting_noter.audio.capture import SilenceDetector
            from meeting_noter.audio.system_audio import CombinedAudioCapture
            from meeting_noter.audio.encoder import RecordingSession
        except ImportError as e:
            self.error.emit(f"Import error: {e}")
            return

        from meeting_noter.daemon import check_audio_available
        if not check_audio_available():
            self.error.emit("No audio input device found. Please check your microphone.")
            return

        try:
            # Use CombinedAudioCapture for mic + system audio
            capture = CombinedAudioCapture()
            capture.start()
        except Exception as e:
            self.error.emit(f"Audio capture error: {e}")
            return

        session = RecordingSession(
            self.output_dir,
            sample_rate=capture.sample_rate,
            channels=capture.channels,
            meeting_name=self.meeting_name,
        )

        # Silence detection
        silence_detector = SilenceDetector(
            threshold=0.01,
            silence_duration=self.silence_timeout_minutes * 60.0,
            sample_rate=capture.sample_rate,
        )
        stopped_by_silence = False

        # Log capture mode
        if capture.has_system_audio:
            self.log_message.emit("Capturing: microphone + system audio")
        else:
            self.log_message.emit("Capturing: microphone only")

        try:
            filepath = session.start()
            self.recording_started.emit(str(filepath))
            self.log_message.emit(f"Will stop after {self.silence_timeout_minutes} min of silence")

            while not self._stop_requested:
                audio = capture.get_audio(timeout=0.5)
                if audio is None:
                    continue

                if audio.ndim > 1:
                    audio = audio.flatten()

                session.write(audio)

                # Check for extended silence
                if silence_detector.update(audio):
                    self.log_message.emit("Stopped: silence timeout reached")
                    stopped_by_silence = True
                    break

        except Exception as e:
            self.error.emit(f"Recording error: {e}")
        finally:
            capture.stop()

            if session.is_active:
                filepath, duration = session.stop()
                if filepath:
                    self.saved_filepath = filepath
                    self.recording_stopped.emit(str(filepath), duration)
                    if stopped_by_silence:
                        self.silence_stopped.emit()
                else:
                    self.log_message.emit("Recording discarded (too short)")

    def stop(self):
        """Request the recording to stop."""
        self._stop_requested = True


class RecordingTab(QWidget):
    """Tab for recording meetings."""

    recording_saved = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.worker: Optional[RecordingWorker] = None
        self.is_recording = False

        self._setup_ui()
        self._setup_meeting_detection()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Meeting name input
        name_group = QGroupBox("Meeting Name")
        name_layout = QHBoxLayout(name_group)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter meeting name or leave blank to auto-detect")
        self.name_input.returnPressed.connect(self._on_start_clicked)
        name_layout.addWidget(self.name_input)

        self.detect_button = QPushButton("Detect")
        self.detect_button.setMaximumWidth(80)
        self.detect_button.clicked.connect(self._detect_meeting)
        name_layout.addWidget(self.detect_button)

        layout.addWidget(name_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Start Recording")
        self.start_button.setMinimumHeight(50)
        self.start_button.clicked.connect(self._on_start_clicked)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Recording")
        self.stop_button.setMinimumHeight(50)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        button_layout.addWidget(self.stop_button)

        layout.addLayout(button_layout)

        # Status
        self.status_label = QLabel("Ready to record")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(self.status_label)

        # Log output
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(200)
        log_layout.addWidget(self.log_output)

        layout.addWidget(log_group)

        # Stretch to push everything up
        layout.addStretch()

    def _setup_meeting_detection(self):
        """Set up periodic meeting detection."""
        self._detection_timer = QTimer()
        self._detection_timer.timeout.connect(self._check_for_meeting)
        self._detection_timer.start(3000)  # Check every 3 seconds

        # Initial check
        self._detect_meeting()

    def _check_for_meeting(self):
        """Check for active meeting and update UI if not recording."""
        if self.is_recording:
            return

        # Only auto-update if field is empty or has default timestamp
        current = self.name_input.text().strip()
        if current and not is_default_meeting_name(current):
            return

        try:
            from meeting_noter.meeting_detector import detect_active_meeting
            meeting = detect_active_meeting()
            if meeting and meeting.meeting_name:
                self.name_input.setText(meeting.meeting_name)
                self.status_label.setText(f"Meeting detected: {meeting.app_name}")
        except Exception:
            pass

    def _detect_meeting(self):
        """Manually detect current meeting."""
        try:
            from meeting_noter.meeting_detector import detect_active_meeting
            meeting = detect_active_meeting()
            if meeting:
                name = meeting.meeting_name or meeting.app_name
                self.name_input.setText(name)
                self._log(f"Detected: {meeting.app_name} - {name}")
            else:
                self.name_input.setText(generate_meeting_name())
                self._log("No meeting detected, using timestamp")
        except Exception as e:
            self._log(f"Detection error: {e}")
            self.name_input.setText(generate_meeting_name())

    def _on_start_clicked(self):
        """Handle start button click."""
        meeting_name = self.name_input.text().strip()

        # Auto-detect or generate name if empty
        if not meeting_name:
            try:
                from meeting_noter.meeting_detector import detect_active_meeting
                meeting = detect_active_meeting()
                if meeting and meeting.meeting_name:
                    meeting_name = meeting.meeting_name
                else:
                    meeting_name = generate_meeting_name()
            except Exception:
                meeting_name = generate_meeting_name()
            self.name_input.setText(meeting_name)

        self.start_recording(meeting_name)

    def _on_stop_clicked(self):
        """Handle stop button click."""
        self.stop_recording()

    def start_recording(self, meeting_name: str):
        """Start a new recording."""
        if self.is_recording:
            return

        self.is_recording = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.name_input.setEnabled(False)
        self.detect_button.setEnabled(False)

        self.status_label.setText(f"Recording: {meeting_name}")
        self.status_label.setStyleSheet(
            "font-size: 14px; padding: 10px; color: white; background-color: #c0392b;"
        )

        self.log_output.clear()
        self._log(f"Starting recording: {meeting_name}")

        # Start worker thread
        output_dir = self.config.recordings_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        self.worker = RecordingWorker(
            output_dir,
            meeting_name,
            silence_timeout_minutes=self.config.silence_timeout,
        )
        self.worker.log_message.connect(self._log)
        self.worker.recording_started.connect(self._on_recording_started)
        self.worker.recording_stopped.connect(self._on_recording_stopped)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def stop_recording(self):
        """Stop the current recording."""
        if not self.is_recording or not self.worker:
            return

        self._log("Stopping recording...")
        self.worker.stop()
        self.worker.wait(5000)  # Wait up to 5 seconds

    def _on_recording_started(self, filepath: str):
        """Handle recording started."""
        self._log(f"Recording to: {Path(filepath).name}")

    def _on_recording_stopped(self, filepath: str, duration: float):
        """Handle recording stopped."""
        mins, secs = divmod(int(duration), 60)
        self._log(f"Saved: {Path(filepath).name} ({mins:02d}:{secs:02d})")

        # Auto-transcribe if enabled
        if self.config.auto_transcribe:
            self._log("Auto-transcribing...")
            try:
                from meeting_noter.transcription.engine import transcribe_file
                transcribe_file(
                    filepath,
                    self.config.recordings_dir,
                    self.config.whisper_model,
                    self.config.transcripts_dir,
                )
                self._log("Transcription complete")
            except Exception as e:
                self._log(f"Transcription error: {e}")

        self.recording_saved.emit()

    def _on_error(self, message: str):
        """Handle error from worker."""
        self._log(f"Error: {message}")
        self.status_label.setText(f"Error: {message}")
        self.status_label.setStyleSheet("font-size: 14px; padding: 10px; color: red;")

    def _on_worker_finished(self):
        """Handle worker thread finished."""
        self.is_recording = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.name_input.setEnabled(True)
        self.detect_button.setEnabled(True)

        # Clear the name field for next recording
        self.name_input.clear()

        self.status_label.setText("Ready to record")
        self.status_label.setStyleSheet("font-size: 14px; padding: 10px;")

        self.worker = None

    def _log(self, message: str):
        """Add a message to the log output."""
        self.log_output.append(message)
