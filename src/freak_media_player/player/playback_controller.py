"""Playback orchestration."""

from __future__ import annotations

from freak_media_player.core.ports import AudioBackend, AudioSourceResolver
from freak_media_player.models.media import Track
from freak_media_player.models.playback import PlaybackState, PlaybackStatus
from freak_media_player.player.queue import PlaybackQueue


class PlaybackController:
    def __init__(
        self,
        queue: PlaybackQueue,
        audio_backend: AudioBackend,
        source_resolver: AudioSourceResolver,
    ) -> None:
        self._queue = queue
        self._audio_backend = audio_backend
        self._source_resolver = source_resolver
        self._state = PlaybackState()

    @property
    def state(self) -> PlaybackState:
        return self._state

    def enqueue(self, track: Track) -> None:
        self._queue.add(track)

    def play_now(self, track: Track) -> PlaybackState:
        self._queue.replace([track])
        self._state = PlaybackState()
        return self.play()

    def play(self) -> PlaybackState:
        track = self._state.current_track or self._queue.current()
        if track is None:
            return self._state

        source = self._source_resolver.resolve_audio_source(track)
        self._audio_backend.load(source)
        self._audio_backend.play()
        self._state = PlaybackState(status=PlaybackStatus.PLAYING, current_track=track)
        return self._state

    def pause(self) -> PlaybackState:
        self._audio_backend.pause()
        self._state = PlaybackState(
            status=PlaybackStatus.PAUSED,
            current_track=self._state.current_track,
            position=self._state.position,
            repeat_mode=self._state.repeat_mode,
            shuffle_enabled=self._state.shuffle_enabled,
        )
        return self._state

    def stop(self) -> PlaybackState:
        self._audio_backend.stop()
        self._state = PlaybackState()
        return self._state
