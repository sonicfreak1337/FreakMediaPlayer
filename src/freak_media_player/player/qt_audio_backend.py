"""Qt Multimedia audio backend."""

from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from freak_media_player.models.media import AudioSource
from freak_media_player.models.playback import PlaybackStatus


class QtAudioBackend:
    def __init__(self) -> None:
        self._audio_output = QAudioOutput()
        self._audio_output.setVolume(1.0)
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio_output)

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

    def status(self) -> PlaybackStatus:
        state = self._player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            return PlaybackStatus.PLAYING
        if state == QMediaPlayer.PlaybackState.PausedState:
            return PlaybackStatus.PAUSED
        return PlaybackStatus.STOPPED
