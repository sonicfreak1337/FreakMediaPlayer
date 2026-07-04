"""Playback orchestration."""

from __future__ import annotations

from datetime import timedelta

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
        self._loaded_track_id: str | None = None

    @property
    def state(self) -> PlaybackState:
        return self._snapshot()

    def enqueue(self, track: Track) -> None:
        self._queue.add(track)

    def play_now(self, track: Track) -> PlaybackState:
        self._queue.replace([track])
        self._state = PlaybackState()
        return self.play()

    def play(self) -> PlaybackState:
        track = self._state.current_track or self._queue.current()
        if track is None:
            return self._snapshot()

        if self._loaded_track_id != track.id:
            source = self._source_resolver.resolve_audio_source(track)
            self._audio_backend.load(source)
            self._loaded_track_id = track.id
        self._audio_backend.play()
        self._state = self._snapshot(status=PlaybackStatus.PLAYING, track=track)
        return self.state

    def pause(self) -> PlaybackState:
        self._audio_backend.pause()
        self._state = PlaybackState(
            status=PlaybackStatus.PAUSED,
            current_track=self._state.current_track,
            position=self._position(),
            repeat_mode=self._state.repeat_mode,
            shuffle_enabled=self._state.shuffle_enabled,
        )
        return self.state

    def stop(self) -> PlaybackState:
        self._audio_backend.stop()
        self._loaded_track_id = None
        self._state = PlaybackState()
        return self.state

    def seek(self, position_ms: int) -> PlaybackState:
        self._audio_backend.seek(position_ms)
        self._state = self._snapshot()
        return self.state

    def position_ms(self) -> int:
        return self._audio_backend.position_ms()

    def duration_ms(self) -> int:
        return self._audio_backend.duration_ms()

    def _snapshot(
        self,
        status: PlaybackStatus | None = None,
        track: Track | None = None,
    ) -> PlaybackState:
        return PlaybackState(
            status=status or self._audio_backend.status(),
            current_track=track or self._state.current_track,
            position=self._position(),
            repeat_mode=self._state.repeat_mode,
            shuffle_enabled=self._state.shuffle_enabled,
        )

    def _position(self) -> timedelta:
        return timedelta(milliseconds=self._audio_backend.position_ms())
