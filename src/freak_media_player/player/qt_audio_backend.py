"""Qt Multimedia audio backend."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from freak_media_player.models.equalizer import EQUALIZER_PRESETS, EqualizerPreset
from freak_media_player.models.media import AudioSource
from freak_media_player.models.playback import PlaybackStatus

MIN_VOLUME = 0.0
MAX_VOLUME = 1.0


class QtAudioBackend:
    def __init__(self) -> None:
        self._audio_output = QAudioOutput()
        self._audio_output.setVolume(1.0)
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio_output)
        self._equalizer_preset = EQUALIZER_PRESETS[0]
        self._finished_callback: Callable[[], None] | None = None
        self._player.mediaStatusChanged.connect(self._handle_media_status_changed)

    def load(self, source: AudioSource) -> None:
        self._player.setSource(QUrl.fromUserInput(source.uri))

    def play(self) -> None:
        self._player.play()

    def pause(self) -> None:
        self._player.pause()

    def stop(self) -> None:
        self._player.stop()

    def seek(self, position_ms: int) -> None:
        self._player.setPosition(max(0, position_ms))

    def position_ms(self) -> int:
        return int(self._player.position())

    def duration_ms(self) -> int:
        return int(self._player.duration())

    def set_volume(self, volume: float) -> None:
        self._audio_output.setVolume(self._clamp_volume(volume))

    def volume(self) -> float:
        return float(self._audio_output.volume())

    def set_equalizer_preset(self, preset: EqualizerPreset) -> None:
        self._equalizer_preset = preset

    def equalizer_preset(self) -> EqualizerPreset:
        return self._equalizer_preset

    def status(self) -> PlaybackStatus:
        state = self._player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            return PlaybackStatus.PLAYING
        if state == QMediaPlayer.PlaybackState.PausedState:
            return PlaybackStatus.PAUSED
        return PlaybackStatus.STOPPED

    def set_finished_callback(self, callback: Callable[[], None]) -> None:
        self._finished_callback = callback

    def _handle_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if (
            status == QMediaPlayer.MediaStatus.EndOfMedia
            and self._finished_callback is not None
        ):
            self._finished_callback()

    def _clamp_volume(self, volume: float) -> float:
        return min(MAX_VOLUME, max(MIN_VOLUME, volume))
