"""Player controls."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.ui.constants import PLAYER_BAR_HEIGHT


class PlayerBar(QWidget):
    def __init__(self, playback_service: PlaybackService) -> None:
        super().__init__()
        self._playback_service = playback_service
        self.setFixedHeight(PLAYER_BAR_HEIGHT)
        self._build_layout()

    def _build_layout(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(14)

        track_info = QVBoxLayout()
        title = QLabel("Nothing playing")
        title.setObjectName("playerTrackTitle")
        artist = QLabel("Queue is empty")
        artist.setObjectName("playerTrackMeta")
        track_info.addWidget(title)
        track_info.addWidget(artist)

        layout.addLayout(track_info, 1)
        layout.addWidget(
            self._build_button(
                QStyle.StandardPixmap.SP_MediaPlay,
                "Play",
                self._playback_service.play,
            )
        )
        layout.addWidget(
            self._build_button(
                QStyle.StandardPixmap.SP_MediaPause,
                "Pause",
                self._playback_service.pause,
            )
        )
        layout.addWidget(
            self._build_button(
                QStyle.StandardPixmap.SP_MediaStop,
                "Stop",
                self._playback_service.stop,
            )
        )
        layout.addStretch(1)

    def _build_button(
        self,
        icon: QStyle.StandardPixmap,
        tooltip: str,
        handler: Callable[[], object],
    ) -> QToolButton:
        button = QToolButton()
        button.setIcon(self.style().standardIcon(icon))
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(handler)
        return button
