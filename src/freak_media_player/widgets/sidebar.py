"""Main navigation sidebar."""

from __future__ import annotations

from PySide6.QtWidgets import QListWidget


class Sidebar(QListWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedWidth(220)
        self.addItems(["Library", "Search", "Playlists", "Queue", "History", "Plugins"])
