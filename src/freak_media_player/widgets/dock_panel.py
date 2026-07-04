"""Dockable side panel content."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DockPanel(QWidget):
    def __init__(self, title: str, empty_text: str) -> None:
        super().__init__()
        self._title = title
        self._empty_text = empty_text
        self._build_layout()

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        title = QLabel(self._title)
        title.setObjectName("dockTitle")

        empty = QLabel(self._empty_text)
        empty.setObjectName("dockEmptyText")
        empty.setWordWrap(True)
        empty.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(title)
        layout.addWidget(empty)
        layout.addStretch(1)
