"""Audio backend implementations."""

from __future__ import annotations

from freak_media_player.core.ports import AudioBackend
from freak_media_player.models.media import AudioSource
from freak_media_player.models.playback import PlaybackStatus

DEFAULT_VOLUME = 1.0
MIN_VOLUME = 0.0
MAX_VOLUME = 1.0


class NullAudioBackend:
    """Backend used before a real audio engine is selected."""

    def __init__(self) -> None:
        self._status = PlaybackStatus.STOPPED
        self._source: AudioSource | None = None
        self._position_ms = 0
        self._duration_ms = 0
        self._volume = DEFAULT_VOLUME

    def load(self, source: AudioSource) -> None:
        self._source = source
        self._status = PlaybackStatus.PAUSED

    def play(self) -> None:
        if self._source is not None:
            self._status = PlaybackStatus.PLAYING

    def pause(self) -> None:
        if self._source is not None:
            self._status = PlaybackStatus.PAUSED

    def stop(self) -> None:
        self._position_ms = 0
        self._status = PlaybackStatus.STOPPED

    def seek(self, position_ms: int) -> None:
        self._position_ms = max(0, position_ms)

    def position_ms(self) -> int:
        return self._position_ms

    def duration_ms(self) -> int:
        return self._duration_ms

    def set_volume(self, volume: float) -> None:
        self._volume = min(MAX_VOLUME, max(MIN_VOLUME, volume))

    def volume(self) -> float:
        return self._volume

    def status(self) -> PlaybackStatus:
        return self._status


def create_desktop_audio_backend() -> AudioBackend:
    try:
        from freak_media_player.player.qt_audio_backend import QtAudioBackend
    except ImportError:
        return NullAudioBackend()
    return QtAudioBackend()
