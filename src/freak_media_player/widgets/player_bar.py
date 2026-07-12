"""Mockup-inspired always-available player module."""

from __future__ import annotations

import math
import time
from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QHideEvent, QPainter, QShowEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from freak_media_player.models.media import Track
from freak_media_player.models.playback import PlaybackStatus, RepeatMode
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.ui.assets import clear_themed_icon, set_themed_icon
from freak_media_player.ui.skins import skin_color
from freak_media_player.widgets.artwork import ClippedArtwork, LogoArtwork, find_track_cover
from freak_media_player.widgets.clickable_slider import ClickableSlider
from freak_media_player.widgets.seek_slider import SeekSlider

POSITION_REFRESH_MS = 500
VOLUME_SCALE = 100
DEFAULT_RESTORE_VOLUME = 0.5


class MiniSpectrum(QWidget):
    """Decorative amber mini spectrum used as the track-info accent."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(25)
        self.setMinimumWidth(180)

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        count = 34
        gap = 3.0
        width = max(1.0, (self.width() - gap * (count - 1)) / count)
        phase = time.monotonic() * 1.4
        active_color = QColor(skin_color("spectrum_active"))
        inactive_color = QColor(skin_color("spectrum_inactive"))
        for index in range(count):
            envelope = max(0.12, 1.0 - index / count)
            wave = 0.35 + 0.65 * abs(math.sin(index * 0.71 + phase))
            height = max(2.0, self.height() * envelope * wave)
            color = active_color if index < 24 else inactive_color
            painter.fillRect(
                round(index * (width + gap)),
                round(self.height() - height),
                max(1, round(width)),
                round(height),
                color,
            )


class PlayerBar(QWidget):
    remove_current_requested = Signal()
    status_message = Signal(str)
    favorite_changed = Signal(str, bool)

    def __init__(
        self,
        playback_service: PlaybackService,
        local_library_service: LocalLibraryService | None = None,
    ) -> None:
        super().__init__()
        self._playback_service = playback_service
        self._local_library_service = local_library_service
        self._title_label = QLabel("Nothing playing")
        self._artist_label = QLabel("Queue is empty")
        self._album_label = QLabel("Import music into the Local Library")
        self._error_panel = QWidget()
        self._error_label = QLabel()
        self._position_label = QLabel("0:00")
        self._duration_label = QLabel("0:00")
        self._seek_slider = SeekSlider()
        self._play_pause_button = QToolButton()
        self._shuffle_button = QToolButton()
        self._repeat_button = QToolButton()
        self._volume_button = QToolButton()
        self._volume_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self._volume_label = QLabel("100%")
        self._modules_button = QToolButton()
        self._favorite_button = QToolButton()
        self._cover = ClippedArtwork(100, 5)
        self._cover_track_id: str | None = None
        self._track_display_initialized = False
        self._last_status: PlaybackStatus | None = None
        self._last_error_message: str | None = None
        self._favorite_track_id: str | None = None
        self._favorite_state = False
        self._last_repeat_mode: RepeatMode | None = None
        self._last_shuffle_enabled: bool | None = None
        self._last_volume_percent = -1
        self._last_position_seconds = -1
        self._last_duration_seconds = -1
        self._mini_spectrum = MiniSpectrum()
        self._refresh_timer = QTimer(self)
        self._volume_before_mute = 1.0
        self.setObjectName("playerPanel")
        self.setMinimumHeight(125)
        self._build_layout()
        self._configure_timer()

    def _build_layout(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setSpacing(12)

        logo = LogoArtwork(100)
        layout.addWidget(logo)
        separator = QFrame()
        separator.setObjectName("playerSeparator")
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFixedWidth(1)
        layout.addWidget(separator)
        layout.addWidget(self._cover)

        info = QVBoxLayout()
        info.setContentsMargins(4, 0, 4, 0)
        info.setSpacing(3)
        info.addWidget(self._mini_spectrum)
        self._title_label.setObjectName("playerTrackTitle")
        self._artist_label.setObjectName("playerArtist")
        self._album_label.setObjectName("playerTrackMeta")
        info.addWidget(self._title_label)
        info.addWidget(self._artist_label)
        info.addWidget(self._album_label)
        self._build_error_panel(info)
        timeline = QHBoxLayout()
        timeline.setSpacing(10)
        self._position_label.setObjectName("playerTime")
        self._duration_label.setObjectName("playerTime")
        self._seek_slider.setObjectName("seekSlider")
        self._seek_slider.seek_requested.connect(self._seek)
        self._seek_slider.sliderReleased.connect(self._seek_to_slider_position)
        timeline.addWidget(self._position_label)
        timeline.addWidget(self._seek_slider, 1)
        timeline.addWidget(self._duration_label)
        info.addLayout(timeline)
        layout.addLayout(info, 5)

        transport = QWidget()
        transport.setObjectName("transportSurface")
        transport_layout = QHBoxLayout(transport)
        transport_layout.setContentsMargins(8, 8, 8, 8)
        transport_layout.setSpacing(5)
        self._configure_mode_button(
            self._shuffle_button,
            "Shuffle: OFF",
            "Shuffle playlist",
            self._toggle_shuffle,
        )
        self._shuffle_button.setObjectName("shuffleButton")
        self._set_icon(self._shuffle_button, "shuffle_icon.png", 24)
        transport_layout.addWidget(self._shuffle_button)
        transport_layout.addWidget(
            self._icon_button(
                "previous_icon.png",
                "Previous",
                "Previous track",
                self._previous_track,
                "transportButton",
            )
        )
        self._play_pause_button.setObjectName("playPauseButton")
        self._play_pause_button.setFixedSize(72, 72)
        self._configure_button(self._play_pause_button, "▶", "Play", self._toggle_play_pause)
        transport_layout.addWidget(self._play_pause_button)
        transport_layout.addWidget(
            self._icon_button(
                "next_icon.png",
                "Next",
                "Next track",
                self._next_track,
                "transportButton",
            )
        )
        self._configure_mode_button(
            self._repeat_button,
            "Repeat Off",
            "Repeat mode",
            self._cycle_repeat_mode,
        )
        transport_layout.addWidget(self._repeat_button)
        layout.addWidget(transport, 4)

        side = QVBoxLayout()
        side.setSpacing(9)
        volume = QHBoxLayout()
        self._configure_button(self._volume_button, "◖", "Mute", self._toggle_mute)
        self._set_icon(self._volume_button, "volume_icon.png", 20)
        self._volume_button.setObjectName("flatPlayerButton")
        self._volume_slider.setObjectName("volumeSlider")
        self._volume_slider.setRange(0, VOLUME_SCALE)
        self._volume_slider.setMinimumWidth(110)
        self._sync_volume_slider(self._playback_service.volume())
        self._volume_slider.valueChanged.connect(self._set_volume_from_slider)
        self._volume_label.setObjectName("playerTime")
        self._volume_label.setMinimumWidth(38)
        volume.addWidget(self._volume_button)
        volume.addWidget(self._volume_slider, 1)
        volume.addWidget(self._volume_label)
        side.addLayout(volume)

        utility = QHBoxLayout()
        utility.setSpacing(7)
        stop = self._text_button("■", "Stop", self._stop, "utilityButton")
        utility.addWidget(stop)
        self._modules_button = self._text_button(
            "☷", "Open the Module menu", lambda: None, "utilityButton"
        )
        self._set_icon(self._modules_button, "queue_icon.png", 22)
        self._modules_button.setEnabled(False)
        utility.addWidget(self._modules_button)
        self._favorite_button = self._text_button(
            "♡",
            "Add current track to favorites",
            self._toggle_favorite,
            "utilityButton",
        )
        self._favorite_button.setCheckable(True)
        self._set_icon(self._favorite_button, "favorite_icon.png", 22)
        self._favorite_button.setEnabled(False)
        utility.addWidget(self._favorite_button)
        settings = self._icon_button(
            "settings_icon.png",
            "Settings",
            "Settings are not available yet",
            lambda: None,
            "utilityButton",
        )
        settings.setEnabled(False)
        utility.addWidget(settings)
        side.addLayout(utility)
        side.addStretch(1)
        layout.addLayout(side, 2)

    def _build_error_panel(self, layout: QVBoxLayout) -> None:
        self._error_panel.setObjectName("playbackErrorPanel")
        error_layout = QHBoxLayout(self._error_panel)
        error_layout.setContentsMargins(0, 2, 0, 2)
        error_layout.setSpacing(6)
        self._error_label.setObjectName("playbackErrorText")
        self._error_label.setWordWrap(True)
        error_layout.addWidget(self._error_label, 1)
        for text, tooltip, handler in (
            ("Retry", "Try to play this file again", self._retry),
            ("Skip", "Skip this file", self._next_track),
            ("Remove", "Remove this file from the playlist", self.remove_current_requested.emit),
        ):
            button = self._text_button(text, tooltip, handler, "playbackErrorButton")
            error_layout.addWidget(button)
        self._error_panel.hide()
        layout.addWidget(self._error_panel)

    def set_module_menu(self, menu: QMenu) -> None:
        """Attach the main module visibility menu to the mockup utility button."""
        self._modules_button.setMenu(menu)
        self._modules_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._modules_button.setEnabled(True)

    def _text_button(
        self,
        text: str,
        tooltip: str,
        handler: Callable[[], object],
        object_name: str,
    ) -> QToolButton:
        button = QToolButton()
        button.setObjectName(object_name)
        self._configure_button(button, text, tooltip, handler)
        return button

    def _icon_button(
        self,
        icon_name: str,
        text: str,
        tooltip: str,
        handler: Callable[[], object],
        object_name: str,
    ) -> QToolButton:
        button = self._text_button(text, tooltip, handler, object_name)
        self._set_icon(button, icon_name, 22)
        return button

    def _set_icon(self, button: QToolButton, icon_name: str, size: int) -> None:
        set_themed_icon(button, f"icons/{icon_name}", size)

    def _configure_button(
        self,
        button: QToolButton,
        text: str,
        tooltip: str,
        handler: Callable[[], object],
    ) -> None:
        button.setText(text)
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(handler)

    def _configure_mode_button(
        self,
        button: QToolButton,
        text: str,
        tooltip: str,
        handler: Callable[[], object],
    ) -> None:
        button.setObjectName("modeButton")
        button.setText(text)
        button.setToolTip(tooltip)
        button.setCheckable(True)
        button.setFixedSize(54, 62)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(handler)

    def _configure_timer(self) -> None:
        self._refresh_timer.setInterval(POSITION_REFRESH_MS)
        self._refresh_timer.timeout.connect(self.refresh)
        self.refresh()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.refresh()
        self._refresh_timer.start()

    def hideEvent(self, event: QHideEvent) -> None:
        self._refresh_timer.stop()
        super().hideEvent(event)

    def refresh(self) -> None:
        self._playback_service.checkpoint()
        state = self._playback_service.state
        self._update_error_panel(state.status, state.error_message)
        self._update_play_pause_button(state.status)
        self._update_playback_modes(state.repeat_mode, state.shuffle_enabled)
        self._update_volume_controls()
        track = state.current_track
        self._update_favorite_button(track)
        track_id = track.id if track is not None else None
        if not self._track_display_initialized or track_id != self._cover_track_id:
            if track is None:
                self._title_label.setText("Nothing playing")
                self._artist_label.setText("Queue is empty")
                self._album_label.setText("Import music into the Local Library")
                self._cover.set_source(None)
            else:
                self._title_label.setText(track.title)
                self._artist_label.setText(track.artist.name)
                album = track.album.title if track.album is not None else "Unknown album"
                year = track.album.release_year if track.album is not None else None
                self._album_label.setText(f"{album}{f' ({year})' if year else ''}")
                self._cover.set_source(find_track_cover(track))
            self._cover_track_id = track_id
            self._track_display_initialized = True

        position_ms = self._playback_service.position_ms()
        duration_ms = self._playback_service.duration_ms()
        position_seconds = max(0, position_ms // 1000)
        duration_seconds = max(0, duration_ms // 1000)
        if position_seconds != self._last_position_seconds:
            self._position_label.setText(self._format_time(position_ms))
            self._last_position_seconds = position_seconds
        if duration_seconds != self._last_duration_seconds:
            self._duration_label.setText(self._format_time(duration_ms))
            self._last_duration_seconds = duration_seconds
        if not self._seek_slider.isSliderDown():
            maximum = max(0, duration_ms)
            value = min(position_ms, maximum)
            if self._seek_slider.maximum() != maximum:
                self._seek_slider.setRange(0, maximum)
            if self._seek_slider.value() != value:
                self._seek_slider.setValue(value)
        if state.status == PlaybackStatus.PLAYING:
            self._mini_spectrum.update()

    def _seek_to_slider_position(self) -> None:
        self._seek(self._seek_slider.value())

    def _retry(self) -> None:
        self._playback_service.retry()
        self.refresh()

    def _update_error_panel(
        self, status: PlaybackStatus, error_message: str | None
    ) -> None:
        visible = status == PlaybackStatus.ERROR
        if visible:
            message = error_message or "The audio file could not be played."
            self._error_label.setText(message)
            if message != self._last_error_message:
                self.status_message.emit(f"Playback error: {message}")
                self._last_error_message = message
        else:
            self._last_error_message = None
        self._error_panel.setVisible(visible)

    def _seek(self, position_ms: int) -> None:
        self._playback_service.seek(position_ms)
        self.refresh()

    def _previous_track(self) -> None:
        self._playback_service.previous_track()
        self.refresh()

    def _next_track(self) -> None:
        self._playback_service.next_track()
        self.refresh()

    def _toggle_play_pause(self) -> None:
        self._playback_service.toggle_play_pause()
        self.refresh()

    def _stop(self) -> None:
        self._playback_service.stop()
        self.refresh()

    def _toggle_shuffle(self) -> None:
        self._playback_service.toggle_shuffle()
        self.refresh()

    def _cycle_repeat_mode(self) -> None:
        self._playback_service.cycle_repeat_mode()
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

    def _toggle_favorite(self) -> None:
        track = self._playback_service.state.current_track
        if track is None or self._local_library_service is None:
            return
        favorite = not self._favorite_state
        self._local_library_service.set_favorite(track.id, favorite)
        self._favorite_state = favorite
        self._sync_favorite_button()
        self.favorite_changed.emit(track.id, favorite)
        self.status_message.emit(
            "Added current track to favorites."
            if favorite
            else "Removed current track from favorites."
        )

    def _update_favorite_button(self, track: Track | None) -> None:
        track_id = track.id if track is not None else None
        if track_id != self._favorite_track_id:
            self._favorite_track_id = track_id
            self._favorite_state = bool(
                track_id is not None
                and self._local_library_service is not None
                and self._local_library_service.is_favorite(track_id)
            )
        self._sync_favorite_button()

    def _sync_favorite_button(self) -> None:
        enabled = (
            self._favorite_track_id is not None
            and self._local_library_service is not None
        )
        self._favorite_button.setEnabled(enabled)
        self._favorite_button.setChecked(self._favorite_state)
        self._favorite_button.setText("♥" if self._favorite_state else "♡")
        self._favorite_button.setToolTip(
            "Remove current track from favorites"
            if self._favorite_state
            else "Add current track to favorites"
        )

    def _set_volume_from_slider(self, value: int) -> None:
        self._playback_service.set_volume(value / VOLUME_SCALE)
        self._update_volume_controls()

    def _sync_volume_slider(self, volume: float) -> None:
        slider_value = round(volume * VOLUME_SCALE)
        if self._volume_slider.value() == slider_value:
            return
        self._volume_slider.blockSignals(True)
        self._volume_slider.setValue(slider_value)
        self._volume_slider.blockSignals(False)

    def _update_volume_controls(self) -> None:
        volume_percent = round(self._playback_service.volume() * VOLUME_SCALE)
        if volume_percent == self._last_volume_percent:
            return
        self._volume_button.setText("Muted" if volume_percent <= 0 else "Volume")
        self._set_icon(
            self._volume_button,
            "mute_icon.png" if volume_percent <= 0 else "volume_icon.png",
            20,
        )
        self._volume_button.setToolTip(
            "Restore volume" if volume_percent <= 0 else "Mute"
        )
        self._volume_label.setText(f"{volume_percent}%")
        self._last_volume_percent = volume_percent

    def _update_play_pause_button(self, status: PlaybackStatus) -> None:
        if status == self._last_status:
            return
        is_playing = status == PlaybackStatus.PLAYING
        self._play_pause_button.setText("Ⅱ" if is_playing else "▶")
        if is_playing:
            self._set_icon(self._play_pause_button, "pause_icon.png", 31)
        else:
            clear_themed_icon(self._play_pause_button)
        self._play_pause_button.setToolTip("Pause" if is_playing else "Play")
        self._last_status = status

    def _update_playback_modes(
        self,
        repeat_mode: RepeatMode,
        shuffle_enabled: bool,
    ) -> None:
        if (
            repeat_mode == self._last_repeat_mode
            and shuffle_enabled == self._last_shuffle_enabled
        ):
            return
        self._shuffle_button.blockSignals(True)
        self._shuffle_button.setChecked(shuffle_enabled)
        self._shuffle_button.blockSignals(False)
        self._shuffle_button.setText("Shuffle: ON" if shuffle_enabled else "Shuffle: OFF")
        self._shuffle_button.setToolTip(
            "Disable playlist shuffle" if shuffle_enabled else "Enable playlist shuffle"
        )
        self._set_icon(
            self._shuffle_button,
            "shuffle_icon.png" if shuffle_enabled else "shuffle_off.png",
            24,
        )
        repeat_labels = {
            RepeatMode.OFF: "Repeat Off",
            RepeatMode.ALL: "Repeat All",
            RepeatMode.ONE: "Repeat One",
        }
        label = repeat_labels[repeat_mode]
        self._repeat_button.setText(label)
        self._repeat_button.setChecked(repeat_mode != RepeatMode.OFF)
        self._repeat_button.setToolTip(label)
        repeat_icons = {
            RepeatMode.OFF: "repeat_all_off.png",
            RepeatMode.ALL: "repeat_all_on.png",
            RepeatMode.ONE: "repeat_one_on.png",
        }
        self._set_icon(self._repeat_button, repeat_icons[repeat_mode], 31)
        self._last_repeat_mode = repeat_mode
        self._last_shuffle_enabled = shuffle_enabled

    def _format_time(self, value_ms: int) -> str:
        total_seconds = max(0, value_ms // 1000)
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes}:{seconds:02d}"
