"""Player controls."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from freak_media_player.services.playback_service import PlaybackService


class PlayerBar(QWidget):
    def __init__(self, playback_service: PlaybackService) -> None:
        super().__init__()
        self._playback_service = playback_service
        self._build_layout()

    def _build_layout(self) -> None:
        layout = QHBoxLayout(self)
        play_button = QPushButton("Play")
        pause_button = QPushButton("Pause")
        stop_button = QPushButton("Stop")

        play_button.clicked.connect(self._playback_service.play)
        pause_button.clicked.connect(self._playback_service.pause)
        stop_button.clicked.connect(self._playback_service.stop)

        layout.addWidget(play_button)
        layout.addWidget(pause_button)
        layout.addWidget(stop_button)
        layout.addStretch(1)
