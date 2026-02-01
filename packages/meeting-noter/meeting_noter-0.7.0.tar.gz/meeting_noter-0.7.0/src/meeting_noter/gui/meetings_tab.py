"""Meetings list tab for browsing and managing recordings."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QDialog,
    QTextEdit,
    QLineEdit,
    QLabel,
    QMessageBox,
    QDialogButtonBox,
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from meeting_noter.config import get_config


class TranscriptDialog(QDialog):
    """Dialog for viewing a transcript."""

    def __init__(self, title: str, content: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Transcript: {title}")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(content)
        layout.addWidget(self.text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)


class RenameDialog(QDialog):
    """Dialog for renaming a meeting."""

    def __init__(self, current_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rename Meeting")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("New name:"))

        self.name_input = QLineEdit()
        self.name_input.setText(current_name)
        self.name_input.selectAll()
        layout.addWidget(self.name_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_name(self) -> str:
        """Get the entered name."""
        return self.name_input.text().strip()


class MeetingsTab(QWidget):
    """Tab for browsing and managing meeting recordings."""

    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.player: Optional[QMediaPlayer] = None
        self.audio_output: Optional[QAudioOutput] = None
        self.current_playing: Optional[Path] = None

        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Table for meetings
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "Name", "Duration", "Transcript", "Actions"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        # Bottom buttons
        button_layout = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        button_layout.addWidget(self.refresh_button)

        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self._open_folder)
        button_layout.addWidget(self.open_folder_button)

        button_layout.addStretch()

        layout.addLayout(button_layout)

    def refresh(self):
        """Refresh the meetings list."""
        self.table.setRowCount(0)

        recordings_dir = self.config.recordings_dir
        if not recordings_dir.exists():
            return

        # Find all MP3 files
        mp3_files = sorted(recordings_dir.glob("*.mp3"), reverse=True)

        for mp3_path in mp3_files:
            self._add_meeting_row(mp3_path)

    def _get_transcript_path(self, mp3_path: Path) -> Path:
        """Get the transcript path for an audio file."""
        transcripts_dir = self.config.transcripts_dir
        return transcripts_dir / mp3_path.with_suffix(".txt").name

    def _add_meeting_row(self, mp3_path: Path):
        """Add a row for a meeting recording."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Parse filename
        name = mp3_path.stem
        parts = name.split("_", 2)

        if len(parts) >= 2:
            # Format: YYYY-MM-DD_HHMMSS or YYYY-MM-DD_HHMMSS_name
            try:
                date_str = parts[0]
                time_str = parts[1]
                date_obj = datetime.strptime(f"{date_str}_{time_str}", "%Y-%m-%d_%H%M%S")
                display_date = date_obj.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                display_date = name
            meeting_name = parts[2] if len(parts) > 2 else ""
        else:
            display_date = name
            meeting_name = ""

        # Date column
        date_item = QTableWidgetItem(display_date)
        date_item.setData(Qt.ItemDataRole.UserRole, str(mp3_path))
        self.table.setItem(row, 0, date_item)

        # Name column
        name_item = QTableWidgetItem(meeting_name)
        self.table.setItem(row, 1, name_item)

        # Duration column
        duration = self._get_duration(mp3_path)
        duration_item = QTableWidgetItem(duration)
        self.table.setItem(row, 2, duration_item)

        # Transcript column
        transcript_path = self._get_transcript_path(mp3_path)
        has_transcript = transcript_path.exists()
        transcript_item = QTableWidgetItem("Yes" if has_transcript else "No")
        self.table.setItem(row, 3, transcript_item)

        # Actions column - widget with buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(4, 2, 4, 2)
        actions_layout.setSpacing(4)

        play_btn = QPushButton("Play")
        play_btn.setFixedWidth(50)
        play_btn.clicked.connect(lambda checked, p=mp3_path: self._play_audio(p))
        actions_layout.addWidget(play_btn)

        if has_transcript:
            view_btn = QPushButton("View")
            view_btn.setFixedWidth(50)
            tp = transcript_path  # Capture for lambda
            view_btn.clicked.connect(lambda checked, p=tp: self._view_transcript(p))
            actions_layout.addWidget(view_btn)
        else:
            transcribe_btn = QPushButton("Transcribe")
            transcribe_btn.setFixedWidth(70)
            transcribe_btn.clicked.connect(lambda checked, p=mp3_path: self._transcribe_recording(p))
            actions_layout.addWidget(transcribe_btn)

        rename_btn = QPushButton("Rename")
        rename_btn.setFixedWidth(60)
        rename_btn.clicked.connect(lambda checked, p=mp3_path, r=row: self._rename_meeting(p, r))
        actions_layout.addWidget(rename_btn)

        self.table.setCellWidget(row, 4, actions_widget)

    def _get_duration(self, mp3_path: Path) -> str:
        """Get the duration of an MP3 file."""
        try:
            # Use file size as rough estimate (128kbps = 16KB/s)
            size_bytes = mp3_path.stat().st_size
            duration_secs = size_bytes / (128 * 1000 / 8)
            mins, secs = divmod(int(duration_secs), 60)
            return f"{mins:02d}:{secs:02d}"
        except Exception:
            return "--:--"

    def _play_audio(self, mp3_path: Path):
        """Play or stop audio playback."""
        # Stop current playback if any
        if self.player and self.current_playing == mp3_path:
            self.player.stop()
            self.player = None
            self.audio_output = None
            self.current_playing = None
            return

        # Stop any existing playback
        if self.player:
            self.player.stop()

        # Create new player
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(QUrl.fromLocalFile(str(mp3_path)))
        self.player.play()
        self.current_playing = mp3_path

    def _view_transcript(self, transcript_path: Path):
        """View a transcript in a dialog."""
        try:
            content = transcript_path.read_text()
            dialog = TranscriptDialog(transcript_path.stem, content, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not read transcript: {e}")

    def _rename_meeting(self, mp3_path: Path, row: int):
        """Rename a meeting (both MP3 and transcript files)."""
        # Extract current name
        name = mp3_path.stem
        parts = name.split("_", 2)
        current_name = parts[2] if len(parts) > 2 else ""

        dialog = RenameDialog(current_name, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        new_name = dialog.get_name()
        if not new_name:
            return

        # Sanitize new name
        import re
        sanitized = new_name.replace(" ", "_")
        sanitized = re.sub(r"[^\w\-]", "", sanitized)
        if len(sanitized) > 50:
            sanitized = sanitized[:50].rstrip("_-")

        # Build new filename
        if len(parts) >= 2:
            new_stem = f"{parts[0]}_{parts[1]}_{sanitized}"
        else:
            new_stem = f"{name}_{sanitized}"

        new_mp3_path = mp3_path.with_stem(new_stem)
        transcript_path = self._get_transcript_path(mp3_path)
        new_transcript_path = self._get_transcript_path(new_mp3_path)

        try:
            # Rename MP3
            mp3_path.rename(new_mp3_path)

            # Rename transcript if exists
            if transcript_path.exists():
                transcript_path.rename(new_transcript_path)

            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not rename files: {e}")

    def _transcribe_recording(self, mp3_path: Path):
        """Transcribe a recording that doesn't have a transcript."""
        from PyQt6.QtCore import QThread, pyqtSignal

        class TranscribeWorker(QThread):
            finished = pyqtSignal(bool, str)

            def __init__(self, audio_path, config):
                super().__init__()
                self.audio_path = audio_path
                self.config = config

            def run(self):
                try:
                    from meeting_noter.transcription.engine import transcribe_file
                    transcribe_file(
                        str(self.audio_path),
                        self.config.recordings_dir,
                        self.config.whisper_model,
                        self.config.transcripts_dir,
                    )
                    self.finished.emit(True, "")
                except Exception as e:
                    self.finished.emit(False, str(e))

        def on_finished(success, error):
            self._transcribe_worker = None
            if success:
                QMessageBox.information(self, "Success", f"Transcription complete: {mp3_path.name}")
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", f"Transcription failed: {error}")

        # Show progress
        QMessageBox.information(self, "Transcribing", f"Transcribing {mp3_path.name}...\nThis may take a while.")

        self._transcribe_worker = TranscribeWorker(mp3_path, self.config)
        self._transcribe_worker.finished.connect(on_finished)
        self._transcribe_worker.start()

    def _open_folder(self):
        """Open the recordings folder in Finder."""
        recordings_dir = self.config.recordings_dir
        recordings_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["open", str(recordings_dir)])
