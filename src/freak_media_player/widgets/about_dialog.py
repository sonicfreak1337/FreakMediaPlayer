"""Project and third-party component information."""

from __future__ import annotations

import platform
from importlib.metadata import PackageNotFoundError, version

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout, QWidget

from freak_media_player import __version__


class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About Freak Media Player")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        title = QLabel(f"<h2>Freak Media Player {__version__}</h2>")
        layout.addWidget(title)
        description = QLabel(
            "A native, offline-first desktop music player for local audio files."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        components = QLabel(
            "<b>Runtime components</b><br>"
            f"Python {platform.python_version()} — PSF License<br>"
            f"PySide6 {_package_version('PySide6')} — LGPLv3/GPL/commercial<br>"
            f"PyAV {_package_version('av')} — BSD-3-Clause; FFmpeg build licensing applies<br>"
            f"NumPy {_package_version('numpy')} — BSD-3-Clause<br>"
            f"SciPy {_package_version('scipy')} — BSD-3-Clause"
        )
        components.setWordWrap(True)
        layout.addWidget(components)
        note = QLabel(
            "Full bundled license notices are included with the release distribution."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


def _package_version(distribution: str) -> str:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return "not installed"
