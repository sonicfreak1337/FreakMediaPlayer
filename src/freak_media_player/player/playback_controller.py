"""Playback orchestration."""

from __future__ import annotations

import logging
from datetime import timedelta

from freak_media_player.core.ports import AudioBackend, AudioSourceResolver
from freak_media_player.models.media import Track
from freak_media_player.models.playback import (
    AudioOutputDevice,
    PlaybackState,
    PlaybackStatus,
    RepeatMode,
)
from freak_media_player.player.queue import PlaybackQueue

MIN_POSITION_MS = 0
LOGGER = logging.getLogger(__name__)


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
        self._continue_after_track = True
        self._audio_backend.set_finished_callback(self._handle_finished)

    @property
    def state(self) -> PlaybackState:
        backend_status = self._audio_backend.status()
        if backend_status == PlaybackStatus.ERROR:
            return self._snapshot(status=PlaybackStatus.ERROR)
        return self._snapshot(
            status=self._state.status,
            error_message=self._state.error_message,
        )

    def current_playlist_index(self) -> int | None:
        if self._state.current_track is None:
            return None
        return self._queue.current_index()

    def enqueue(self, track: Track) -> None:
        self._queue.add(track)

    def restore(self, track: Track, position_ms: int) -> PlaybackState:
        """Load a previous session without automatically starting playback."""
        self._queue.select_track(track.id)
        try:
            source = self._source_resolver.resolve_audio_source(track)
            self._audio_backend.load(source)
            self._loaded_track_id = track.id
            self._audio_backend.seek(max(MIN_POSITION_MS, position_ms))
            self._state = self._snapshot(status=PlaybackStatus.PAUSED, track=track)
        except Exception as error:
            LOGGER.exception("Could not restore track %s", track.id)
            self._loaded_track_id = None
            self._state = self._snapshot(
                status=PlaybackStatus.ERROR,
                track=track,
                error_message=self._friendly_error(error),
            )
        return self.state

    def play_now(self, track: Track) -> PlaybackState:
        self._queue.replace([track])
        self._queue.select(0)
        self._state = self._idle_state()
        return self._start_track(track)

    def play_playlist(self, tracks: list[Track], start_index: int) -> PlaybackState:
        self._queue.replace(tracks)
        track = self._queue.select(start_index)
        if track is None:
            return self.state
        self._state = self._idle_state()
        return self._start_track(track)

    def sync_playlist(self, tracks: list[Track]) -> PlaybackState:
        current_track = self._state.current_track
        current_track_id = current_track.id if current_track is not None else None
        self._queue.replace(tracks, current_track_id=current_track_id)
        if current_track is not None and not any(
            track.id == current_track.id for track in tracks
        ):
            return self.stop()
        replacement = next(
            (
                track
                for track in tracks
                if current_track is not None and track.id == current_track.id
            ),
            None,
        )
        if (
            current_track is not None
            and replacement is not None
            and replacement != current_track
        ):
            if replacement.provider_identity != current_track.provider_identity:
                self._loaded_track_id = None
            self._state = self._snapshot(track=replacement)
        return self.state

    def play(self) -> PlaybackState:
        track = self._state.current_track or self._queue.current()
        if track is None:
            return self._snapshot()

        return self._start_track(track)

    def retry(self) -> PlaybackState:
        track = self._state.current_track
        if track is None:
            return self.state
        self._loaded_track_id = None
        return self._start_track(track)

    def next_track(self) -> PlaybackState:
        track = self._queue.next()
        if track is None and self._state.repeat_mode == RepeatMode.ALL:
            track = self._queue.select(0)
        if track is None:
            return self.stop()
        return self._start_track(track)

    def previous_track(self) -> PlaybackState:
        track = self._queue.previous()
        if track is None and self._state.repeat_mode == RepeatMode.ALL:
            track = self._queue.select(self._queue.track_count() - 1)
        if track is None:
            return self.state
        return self._start_track(track)

    def set_shuffle_enabled(self, enabled: bool) -> PlaybackState:
        self._queue.set_shuffle_enabled(enabled)
        self._state = self._snapshot(shuffle_enabled=enabled)
        return self.state

    def toggle_shuffle(self) -> PlaybackState:
        return self.set_shuffle_enabled(not self._state.shuffle_enabled)

    def set_repeat_mode(self, repeat_mode: RepeatMode) -> PlaybackState:
        self._state = self._snapshot(repeat_mode=repeat_mode)
        return self.state

    def cycle_repeat_mode(self) -> PlaybackState:
        next_mode = {
            RepeatMode.OFF: RepeatMode.ALL,
            RepeatMode.ALL: RepeatMode.ONE,
            RepeatMode.ONE: RepeatMode.OFF,
        }[self._state.repeat_mode]
        return self.set_repeat_mode(next_mode)

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
        self._state = self._idle_state()
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

    def available_output_devices(self) -> list[AudioOutputDevice]:
        return self._audio_backend.available_output_devices()

    def selected_output_device_id(self) -> str | None:
        return self._audio_backend.selected_output_device_id()

    def set_output_device(self, device_id: str | None) -> PlaybackState:
        self._audio_backend.set_output_device(device_id)
        self._state = self._snapshot()
        return self.state

    def set_continue_after_track(self, enabled: bool) -> None:
        self._continue_after_track = enabled

    def _start_track(self, track: Track) -> PlaybackState:
        try:
            if self._loaded_track_id != track.id:
                source = self._source_resolver.resolve_audio_source(track)
                self._audio_backend.load(source)
                self._loaded_track_id = track.id
            self._audio_backend.play()
            self._state = self._snapshot(status=PlaybackStatus.PLAYING, track=track)
        except Exception as error:
            LOGGER.exception("Could not start track %s", track.id)
            self._loaded_track_id = None
            self._state = self._snapshot(
                status=PlaybackStatus.ERROR,
                track=track,
                error_message=self._friendly_error(error),
            )
        return self.state

    def _handle_finished(self) -> None:
        if (
            self._state.repeat_mode == RepeatMode.ONE
            and self._state.current_track is not None
        ):
            self._start_track(self._state.current_track)
            return
        if not self._continue_after_track:
            self.stop()
            return
        self.next_track()

    def _snapshot(
        self,
        status: PlaybackStatus | None = None,
        track: Track | None = None,
        repeat_mode: RepeatMode | None = None,
        shuffle_enabled: bool | None = None,
        error_message: str | None = None,
    ) -> PlaybackState:
        resolved_status = status or self._audio_backend.status()
        return PlaybackState(
            status=resolved_status,
            current_track=track or self._state.current_track,
            position=self._position(),
            repeat_mode=repeat_mode or self._state.repeat_mode,
            shuffle_enabled=(
                self._state.shuffle_enabled
                if shuffle_enabled is None
                else shuffle_enabled
            ),
            error_message=(
                error_message
                if error_message is not None
                else self._audio_backend.error_message()
                if resolved_status == PlaybackStatus.ERROR
                else None
            ),
        )

    def _idle_state(self) -> PlaybackState:
        return PlaybackState(
            repeat_mode=self._state.repeat_mode,
            shuffle_enabled=self._state.shuffle_enabled,
        )

    def _friendly_error(self, error: Exception) -> str:
        if isinstance(error, FileNotFoundError):
            return "The audio file was not found. It may have been moved or deleted."
        if isinstance(error, PermissionError):
            return "The audio file cannot be read. Check its permissions."
        detail = str(error).strip()
        return detail or "The audio file is damaged or unsupported."

    def _position(self) -> timedelta:
        return timedelta(milliseconds=self._audio_backend.position_ms())
