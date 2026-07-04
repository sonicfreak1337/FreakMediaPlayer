"""Reusable content placeholder panels for early shell composition."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ContentPanel(QWidget):
    def __init__(self, title: str, subtitle: str = "") -> None:
        super().__init__()
        self._title = title
        self._subtitle = subtitle
        self._build_layout()

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)

        title_label = QLabel(self._title)
        title_label.setObjectName("panelTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        subtitle_label = QLabel(self._subtitle)
        subtitle_label.setObjectName("panelSubtitle")
        subtitle_label.setWordWrap(True)

        layout.addWidget(title_label)
        if self._subtitle:
            layout.addWidget(subtitle_label)
        layout.addStretch(1)
