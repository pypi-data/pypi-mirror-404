"""Main window with tab interface."""

from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout

from meeting_noter.gui.recording_tab import RecordingTab
from meeting_noter.gui.meetings_tab import MeetingsTab
from meeting_noter.gui.settings_tab import SettingsTab


class MainWindow(QMainWindow):
    """Main application window with tabbed interface."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Meeting Noter")
        self.setMinimumSize(800, 600)

        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create tabs
        self.recording_tab = RecordingTab()
        self.meetings_tab = MeetingsTab()
        self.settings_tab = SettingsTab()

        self.tabs.addTab(self.recording_tab, "Record")
        self.tabs.addTab(self.meetings_tab, "Meetings")
        self.tabs.addTab(self.settings_tab, "Settings")

        # Connect settings changes to refresh meetings list
        self.settings_tab.settings_saved.connect(self.meetings_tab.refresh)

        # Connect recording completion to refresh meetings list
        self.recording_tab.recording_saved.connect(self.meetings_tab.refresh)

    def closeEvent(self, event):
        """Handle window close - stop any active recording."""
        if self.recording_tab.is_recording:
            self.recording_tab.stop_recording()
        event.accept()
