"""Readable runtime diagnostics dialog."""

from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from freak_media_player.services.diagnostic_service import DiagnosticService


class DiagnosticsDialog(QDialog):
    def __init__(self, service: DiagnosticService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Diagnostics")
        self.setMinimumSize(640, 430)
        snapshot = service.snapshot()
        layout = QVBoxLayout(self)
        details = QFormLayout()
        details.addRow("Application version", QLabel(snapshot.app_version))
        details.addRow("Database schema", QLabel(str(snapshot.database_version)))
        details.addRow("Data folder", QLabel(str(snapshot.data_dir)))
        details.addRow("Database", QLabel(str(snapshot.database_path)))
        details.addRow("Audio output", QLabel(snapshot.audio_output))
        layout.addLayout(details)
        errors = QTextEdit()
        errors.setReadOnly(True)
        errors.setPlaceholderText("No errors recorded in this session.")
        errors.setPlainText("\n\n".join(snapshot.recent_errors))
        layout.addWidget(QLabel("Recent errors (personal home path hidden)"))
        layout.addWidget(errors, 1)
        open_logs = QPushButton("Open log folder")
        open_logs.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(snapshot.logs_dir)))
        )
        layout.addWidget(open_logs)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
