"""Settings tab for configuring Meeting Noter."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QFileDialog,
    QMessageBox,
    QSpinBox,
)

from meeting_noter.config import get_config
from meeting_noter.daemon import read_pid_file, is_process_running


class SettingsTab(QWidget):
    """Tab for configuring application settings."""

    settings_saved = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.config = get_config()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Directories group
        dirs_group = QGroupBox("Directories")
        dirs_layout = QFormLayout(dirs_group)

        # Recordings directory
        recordings_layout = QHBoxLayout()
        self.recordings_input = QLineEdit()
        self.recordings_input.setReadOnly(True)
        recordings_layout.addWidget(self.recordings_input)

        recordings_browse = QPushButton("Browse...")
        recordings_browse.clicked.connect(self._browse_recordings_dir)
        recordings_layout.addWidget(recordings_browse)

        dirs_layout.addRow("Recordings:", recordings_layout)

        # Transcripts directory
        transcripts_layout = QHBoxLayout()
        self.transcripts_input = QLineEdit()
        self.transcripts_input.setReadOnly(True)
        transcripts_layout.addWidget(self.transcripts_input)

        transcripts_browse = QPushButton("Browse...")
        transcripts_browse.clicked.connect(self._browse_transcripts_dir)
        transcripts_layout.addWidget(transcripts_browse)

        dirs_layout.addRow("Transcripts:", transcripts_layout)

        layout.addWidget(dirs_group)

        # Transcription group
        transcription_group = QGroupBox("Transcription")
        transcription_layout = QFormLayout(transcription_group)

        # Whisper model
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "tiny.en",
            "base.en",
            "small.en",
            "medium.en",
            "large-v3",
        ])
        transcription_layout.addRow("Whisper Model:", self.model_combo)

        # Model descriptions
        model_desc = QLabel(
            "tiny.en: Fastest, least accurate (~1GB RAM)\n"
            "base.en: Fast, decent accuracy (~1GB RAM)\n"
            "small.en: Good balance (~2GB RAM)\n"
            "medium.en: Better accuracy (~5GB RAM)\n"
            "large-v3: Best accuracy (~10GB RAM)"
        )
        model_desc.setStyleSheet("color: gray; font-size: 11px;")
        transcription_layout.addRow("", model_desc)

        # Auto-transcribe
        self.auto_transcribe_checkbox = QCheckBox("Automatically transcribe after recording stops")
        transcription_layout.addRow("", self.auto_transcribe_checkbox)

        layout.addWidget(transcription_group)

        # Recording group
        recording_group = QGroupBox("Recording")
        recording_layout = QFormLayout(recording_group)

        # Silence timeout
        silence_layout = QHBoxLayout()
        self.silence_timeout_spin = QSpinBox()
        self.silence_timeout_spin.setRange(1, 60)
        self.silence_timeout_spin.setSuffix(" minutes")
        self.silence_timeout_spin.setToolTip("Stop recording after this many minutes of silence")
        silence_layout.addWidget(self.silence_timeout_spin)
        silence_layout.addStretch()

        recording_layout.addRow("Silence timeout:", silence_layout)

        silence_desc = QLabel("Recording stops automatically after this duration of silence")
        silence_desc.setStyleSheet("color: gray; font-size: 11px;")
        recording_layout.addRow("", silence_desc)

        layout.addWidget(recording_group)

        # Appearance group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)

        self.show_menubar_checkbox = QCheckBox("Show menu bar icon (MN)")
        appearance_layout.addRow("", self.show_menubar_checkbox)

        layout.addWidget(appearance_group)

        # Save button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_button = QPushButton("Save Settings")
        self.save_button.setMinimumWidth(120)
        self.save_button.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        # Stretch to push everything up
        layout.addStretch()

    def _load_settings(self):
        """Load current settings into the UI."""
        self.recordings_input.setText(str(self.config.recordings_dir))
        self.transcripts_input.setText(str(self.config.transcripts_dir))

        # Set combo box to current model
        model = self.config.whisper_model
        index = self.model_combo.findText(model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)

        self.auto_transcribe_checkbox.setChecked(self.config.auto_transcribe)
        self.silence_timeout_spin.setValue(self.config.silence_timeout)
        self.show_menubar_checkbox.setChecked(self.config.show_menubar)

    def _browse_recordings_dir(self):
        """Browse for recordings directory."""
        current = self.recordings_input.text()
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Recordings Directory",
            current,
        )
        if directory:
            self.recordings_input.setText(directory)

    def _browse_transcripts_dir(self):
        """Browse for transcripts directory."""
        current = self.transcripts_input.text()
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Transcripts Directory",
            current,
        )
        if directory:
            self.transcripts_input.setText(directory)

    def _save_settings(self):
        """Save settings to config file."""
        recordings_dir = Path(self.recordings_input.text())
        transcripts_dir = Path(self.transcripts_input.text())

        # Validate directories
        try:
            recordings_dir.mkdir(parents=True, exist_ok=True)
            transcripts_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not create directories: {e}")
            return

        # Check if menubar setting changed
        old_show_menubar = self.config.show_menubar
        new_show_menubar = self.show_menubar_checkbox.isChecked()

        # Update config
        self.config.recordings_dir = recordings_dir
        self.config.transcripts_dir = transcripts_dir
        self.config.whisper_model = self.model_combo.currentText()
        self.config.auto_transcribe = self.auto_transcribe_checkbox.isChecked()
        self.config.silence_timeout = self.silence_timeout_spin.value()
        self.config.show_menubar = new_show_menubar

        try:
            self.config.save()

            # Handle menubar start/stop
            if new_show_menubar and not old_show_menubar:
                self._start_menubar()
            elif not new_show_menubar and old_show_menubar:
                self._stop_menubar()

            self.settings_saved.emit()
            QMessageBox.information(self, "Success", "Settings saved successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save settings: {e}")

    def _start_menubar(self):
        """Start the menu bar app in background."""
        subprocess.Popen(
            [sys.executable, "-m", "meeting_noter.menubar"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    def _stop_menubar(self):
        """Stop the menu bar app if running."""
        import os
        import signal

        menubar_pid_file = Path.home() / ".meeting-noter-menubar.pid"

        pid = read_pid_file(menubar_pid_file)
        if pid and is_process_running(pid):
            try:
                os.kill(pid, signal.SIGTERM)
            except (OSError, ProcessLookupError):
                pass
