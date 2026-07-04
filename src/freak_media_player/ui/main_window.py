"""Main application window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QSplitter, QStatusBar, QWidget

from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.widgets.player_bar import PlayerBar
from freak_media_player.widgets.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(self, playback_service: PlaybackService) -> None:
        super().__init__()
        self._playback_service = playback_service
        self.setWindowTitle("Freak Media Player")
        self.resize(1280, 800)
        self._build_layout()

    def _build_layout(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(Sidebar())
        splitter.addWidget(self._build_library_placeholder())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)
        self.setStatusBar(QStatusBar())
        self.setMenuWidget(PlayerBar(playback_service=self._playback_service))

    def _build_library_placeholder(self) -> QWidget:
        label = QLabel("Library")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label
