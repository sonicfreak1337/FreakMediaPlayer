"""Audio backend implementations."""

from __future__ import annotations

from freak_media_player.models.media import Track
from freak_media_player.models.playback import PlaybackStatus


class NullAudioBackend:
    """Backend used before a real audio engine is selected."""

    def __init__(self) -> None:
        self._status = PlaybackStatus.STOPPED
        self._track: Track | None = None

    def load(self, track: Track) -> None:
        self._track = track
        self._status = PlaybackStatus.PAUSED

    def play(self) -> None:
        if self._track is not None:
            self._status = PlaybackStatus.PLAYING

    def pause(self) -> None:
        if self._track is not None:
            self._status = PlaybackStatus.PAUSED

    def stop(self) -> None:
        self._status = PlaybackStatus.STOPPED

    def status(self) -> PlaybackStatus:
        return self._status
