"""Playback orchestration."""

from __future__ import annotations

from datetime import timedelta

from freak_media_player.core.ports import AudioBackend, AudioSourceResolver
from freak_media_player.models.media import Track
from freak_media_player.models.playback import PlaybackState, PlaybackStatus
from freak_media_player.player.queue import PlaybackQueue

MIN_POSITION_MS = 0


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
        self._audio_backend.set_finished_callback(self._handle_finished)

    @property
    def state(self) -> PlaybackState:
        return self._snapshot()

    def current_playlist_index(self) -> int | None:
        if self._state.current_track is None:
            return None
        return self._queue.current_index()

    def enqueue(self, track: Track) -> None:
        self._queue.add(track)

    def play_now(self, track: Track) -> PlaybackState:
        self._queue.replace([track])
        self._queue.select(0)
        self._state = PlaybackState()
        return self._start_track(track)

    def play_playlist(self, tracks: list[Track], start_index: int) -> PlaybackState:
        self._queue.replace(tracks)
        track = self._queue.select(start_index)
        if track is None:
            return self.state
        self._state = PlaybackState()
        return self._start_track(track)

    def sync_playlist(self, tracks: list[Track]) -> PlaybackState:
        current_track = self._state.current_track
        current_track_id = current_track.id if current_track is not None else None
        self._queue.replace(tracks, current_track_id=current_track_id)
        if current_track is not None and not any(
            track.id == current_track.id for track in tracks
        ):
            return self.stop()
        return self.state

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

    def next_track(self) -> PlaybackState:
        track = self._queue.next()
        if track is None:
            self._audio_backend.stop()
            self._loaded_track_id = None
            self._state = PlaybackState()
            return self.state
        return self._start_track(track)

    def previous_track(self) -> PlaybackState:
        track = self._queue.previous()
        if track is None:
            return self.state
        return self._start_track(track)

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

    def toggle_play_pause(self) -> PlaybackState:
        if self.state.status == PlaybackStatus.PLAYING:
            return self.pause()
        return self.play()

    def stop(self) -> PlaybackState:
        self._audio_backend.stop()
        self._loaded_track_id = None
        self._state = PlaybackState()
        return self.state

    def seek(self, position_ms: int) -> PlaybackState:
        self._audio_backend.seek(position_ms)
        self._state = self._snapshot()
        return self.state

    def seek_relative(self, offset_ms: int) -> PlaybackState:
        target_ms = self.position_ms() + offset_ms
        duration_ms = self.duration_ms()
        if duration_ms > MIN_POSITION_MS:
            target_ms = min(target_ms, duration_ms)
        return self.seek(max(MIN_POSITION_MS, target_ms))

    def position_ms(self) -> int:
        return self._audio_backend.position_ms()

    def duration_ms(self) -> int:
        return self._audio_backend.duration_ms()

    def set_volume(self, volume: float) -> PlaybackState:
        self._audio_backend.set_volume(volume)
        return self.state

    def volume(self) -> float:
        return self._audio_backend.volume()

    def _start_track(self, track: Track) -> PlaybackState:
        source = self._source_resolver.resolve_audio_source(track)
        self._audio_backend.load(source)
        self._loaded_track_id = track.id
        self._audio_backend.play()
        self._state = self._snapshot(status=PlaybackStatus.PLAYING, track=track)
        return self.state

    def _handle_finished(self) -> None:
        self.next_track()

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
