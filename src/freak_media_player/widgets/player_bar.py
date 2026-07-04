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

from freak_media_player.models.playback import PlaybackStatus
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.ui.constants import PLAYER_BAR_HEIGHT
from freak_media_player.widgets.clickable_slider import ClickableSlider
from freak_media_player.widgets.seek_slider import SeekSlider

POSITION_REFRESH_MS = 500
SEEK_JUMP_MS = 10_000
VOLUME_SCALE = 100
DEFAULT_RESTORE_VOLUME = 0.5


class PlayerBar(QWidget):
    def __init__(self, playback_service: PlaybackService) -> None:
        super().__init__()
        self._playback_service = playback_service
        self._title_label = QLabel("Nothing playing")
        self._artist_label = QLabel("Queue is empty")
        self._position_label = QLabel("0:00")
        self._duration_label = QLabel("0:00")
        self._seek_slider = SeekSlider()
        self._play_pause_button = QToolButton()
        self._volume_button = QToolButton()
        self._volume_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self._volume_label = QLabel("100%")
        self._refresh_timer = QTimer(self)
        self._volume_before_mute = 1.0
        self.setFixedHeight(PLAYER_BAR_HEIGHT)
        self._build_layout()
        self._configure_timer()

    def _build_layout(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

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
        controls.setSpacing(8)

        volume_controls = QHBoxLayout()
        volume_controls.setSpacing(8)

        layout.addLayout(track_info, 1)
        controls.addWidget(
            self._build_button(
                QStyle.StandardPixmap.SP_MediaSeekBackward,
                "Back 10 seconds",
                self._seek_backward,
            )
        )
        self._configure_button(
            self._play_pause_button,
            QStyle.StandardPixmap.SP_MediaPlay,
            "Play",
            self._toggle_play_pause,
        )
        controls.addWidget(self._play_pause_button)
        controls.addWidget(
            self._build_button(
                QStyle.StandardPixmap.SP_MediaStop,
                "Stop",
                self._stop,
            )
        )
        controls.addWidget(
            self._build_button(
                QStyle.StandardPixmap.SP_MediaSeekForward,
                "Forward 10 seconds",
                self._seek_forward,
            )
        )
        center.addLayout(controls)
        center.addLayout(timeline)

        layout.addLayout(center, 3)
        self._configure_volume_controls()
        volume_controls.addWidget(self._volume_button)
        volume_controls.addWidget(self._volume_slider)
        volume_controls.addWidget(self._volume_label)
        layout.addLayout(volume_controls, 1)

    def _build_button(
        self,
        icon: QStyle.StandardPixmap,
        tooltip: str,
        handler: Callable[[], object],
    ) -> QToolButton:
        button = QToolButton()
        self._configure_button(button, icon, tooltip, handler)
        return button

    def _configure_button(
        self,
        button: QToolButton,
        icon: QStyle.StandardPixmap,
        tooltip: str,
        handler: Callable[[], object],
    ) -> None:
        button.setIcon(self.style().standardIcon(icon))
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(handler)

    def _configure_volume_controls(self) -> None:
        self._configure_button(
            self._volume_button,
            QStyle.StandardPixmap.SP_MediaVolume,
            "Mute",
            self._toggle_mute,
        )
        self._volume_label.setObjectName("playerTime")
        self._volume_label.setMinimumWidth(36)
        self._volume_slider.setRange(0, VOLUME_SCALE)
        self._volume_slider.setFixedWidth(120)
        self._sync_volume_slider(self._playback_service.volume())
        self._volume_slider.valueChanged.connect(self._set_volume_from_slider)

    def _configure_timer(self) -> None:
        self._refresh_timer.setInterval(POSITION_REFRESH_MS)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start()
        self.refresh()

    def refresh(self) -> None:
        state = self._playback_service.state
        self._update_play_pause_button(state.status)
        self._update_volume_controls()
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

    def _seek_backward(self) -> None:
        self._playback_service.seek_relative(-SEEK_JUMP_MS)
        self.refresh()

    def _seek_forward(self) -> None:
        self._playback_service.seek_relative(SEEK_JUMP_MS)
        self.refresh()

    def _toggle_play_pause(self) -> None:
        self._playback_service.toggle_play_pause()
        self.refresh()

    def _stop(self) -> None:
        self._playback_service.stop()
        self.refresh()

    def _toggle_mute(self) -> None:
        current_volume = self._playback_service.volume()
        if current_volume > 0:
            self._volume_before_mute = current_volume
            next_volume = 0.0
        else:
            next_volume = max(DEFAULT_RESTORE_VOLUME, self._volume_before_mute)
        self._playback_service.set_volume(next_volume)
        self._sync_volume_slider(next_volume)
        self._update_volume_controls()

    def _set_volume_from_slider(self, value: int) -> None:
        self._playback_service.set_volume(value / VOLUME_SCALE)
        self._update_volume_controls()

    def _sync_volume_slider(self, volume: float) -> None:
        self._volume_slider.blockSignals(True)
        self._volume_slider.setValue(round(volume * VOLUME_SCALE))
        self._volume_slider.blockSignals(False)

    def _update_volume_controls(self) -> None:
        volume_percent = round(self._playback_service.volume() * VOLUME_SCALE)
        icon = QStyle.StandardPixmap.SP_MediaVolume
        if volume_percent <= 0:
            icon = QStyle.StandardPixmap.SP_MediaVolumeMuted
        self._volume_button.setIcon(self.style().standardIcon(icon))
        self._volume_label.setText(f"{volume_percent}%")

    def _update_play_pause_button(self, status: PlaybackStatus) -> None:
        icon = QStyle.StandardPixmap.SP_MediaPlay
        tooltip = "Play"
        if status == PlaybackStatus.PLAYING:
            icon = QStyle.StandardPixmap.SP_MediaPause
            tooltip = "Pause"
        self._play_pause_button.setIcon(self.style().standardIcon(icon))
        self._play_pause_button.setToolTip(tooltip)

    def _format_time(self, value_ms: int) -> str:
        total_seconds = max(0, value_ms // 1000)
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes}:{seconds:02d}"
