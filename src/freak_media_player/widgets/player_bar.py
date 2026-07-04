"""Player controls."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QTimer, Qt
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
from freak_media_player.widgets.seek_slider import SeekSlider

POSITION_REFRESH_MS = 500


class PlayerBar(QWidget):
    def __init__(self, playback_service: PlaybackService) -> None:
        super().__init__()
        self._playback_service = playback_service
        self._title_label = QLabel("Nothing playing")
        self._artist_label = QLabel("Queue is empty")
        self._position_label = QLabel("0:00")
        self._duration_label = QLabel("0:00")
        self._seek_slider = SeekSlider()
        self._refresh_timer = QTimer(self)
        self.setFixedHeight(PLAYER_BAR_HEIGHT)
        self._build_layout()
        self._configure_timer()

    def _build_layout(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(14)

        track_info = QVBoxLayout()
        self._title_label.setObjectName("playerTrackTitle")
        self._artist_label.setObjectName("playerTrackMeta")
        track_info.addWidget(self._title_label)
        track_info.addWidget(self._artist_label)

        timeline = QHBoxLayout()
        self._position_label.setObjectName("playerTime")
        self._duration_label.setObjectName("playerTime")
        self._seek_slider.seek_requested.connect(self._seek)
        self._seek_slider.sliderReleased.connect(self._seek_to_slider_position)
        timeline.addWidget(self._position_label)
        timeline.addWidget(self._seek_slider, 1)
        timeline.addWidget(self._duration_label)

        center = QVBoxLayout()
        controls = QHBoxLayout()

        layout.addLayout(track_info, 1)
        controls.addWidget(
            self._build_button(
                QStyle.StandardPixmap.SP_MediaPlay,
                "Play",
                self._playback_service.play,
            )
        )
        controls.addWidget(
            self._build_button(
                QStyle.StandardPixmap.SP_MediaPause,
                "Pause",
                self._playback_service.pause,
            )
        )
        controls.addWidget(
            self._build_button(
                QStyle.StandardPixmap.SP_MediaStop,
                "Stop",
                self._playback_service.stop,
            )
        )
        center.addLayout(controls)
        center.addLayout(timeline)

        layout.addLayout(center, 3)

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

    def _configure_timer(self) -> None:
        self._refresh_timer.setInterval(POSITION_REFRESH_MS)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start()
        self.refresh()

    def refresh(self) -> None:
        state = self._playback_service.state
        track = state.current_track
        if track is None:
            self._title_label.setText("Nothing playing")
            self._artist_label.setText("Queue is empty")
        else:
            self._title_label.setText(track.title)
            self._artist_label.setText(track.artist.name)

        position_ms = self._playback_service.position_ms()
        duration_ms = self._playback_service.duration_ms()
        self._position_label.setText(self._format_time(position_ms))
        self._duration_label.setText(self._format_time(duration_ms))

        if not self._seek_slider.isSliderDown():
            self._seek_slider.setRange(0, max(0, duration_ms))
            self._seek_slider.setValue(min(position_ms, max(0, duration_ms)))

    def _seek_to_slider_position(self) -> None:
        self._seek(self._seek_slider.value())

    def _seek(self, position_ms: int) -> None:
        self._playback_service.seek(position_ms)
        self.refresh()

    def _format_time(self, value_ms: int) -> str:
        total_seconds = max(0, value_ms // 1000)
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes}:{seconds:02d}"
