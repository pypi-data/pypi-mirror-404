"""PyQt6 application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from meeting_noter.gui.main_window import MainWindow


def _set_macos_dock_icon(icon_path: Path):
    """Set the macOS dock icon using AppKit."""
    try:
        from AppKit import NSApplication, NSImage
        ns_app = NSApplication.sharedApplication()
        icon = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
        if icon:
            ns_app.setApplicationIconImage_(icon)
    except ImportError:
        pass  # pyobjc not installed


def run_gui():
    """Launch the Meeting Noter GUI application."""
    resources = Path(__file__).parent.parent / "resources"

    app = QApplication(sys.argv)
    app.setApplicationName("Meeting Noter")
    app.setOrganizationName("Meeting Noter")

    # Set window icon
    icon_path = resources / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()

    # Set macOS dock icon AFTER window is shown
    if sys.platform == "darwin":
        icns_path = resources / "icon.icns"
        if icns_path.exists():
            _set_macos_dock_icon(icns_path)
        app.processEvents()

    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
