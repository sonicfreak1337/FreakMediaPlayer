"""UI-neutral playback use cases."""

from __future__ import annotations

import time
from collections.abc import Callable

from freak_media_player.models.media import Track
from freak_media_player.models.playback import PlaybackState, RepeatMode
from freak_media_player.player.playback_controller import PlaybackController

SESSION_CHECKPOINT_SECONDS = 5.0


class PlaybackService:
    def __init__(
        self,
        controller: PlaybackController,
        volume_changed: Callable[[float], None] | None = None,
        session_changed: Callable[[str, int], None] | None = None,
        playback_modes_changed: Callable[[RepeatMode, bool], None] | None = None,
    ) -> None:
        self._controller = controller
        self._volume_changed = volume_changed
        self._session_changed = session_changed
        self._playback_modes_changed = playback_modes_changed
        self._last_checkpoint_at = 0.0
        self._volume_before_mute = 0.5

    @property
    def state(self) -> PlaybackState:
        return self._controller.state

    def enqueue_and_play(self, track: Track) -> PlaybackState:
        return self._checkpoint_after(self._controller.play_now(track))

    def play_playlist(self, tracks: list[Track], start_index: int) -> PlaybackState:
        return self._checkpoint_after(self._controller.play_playlist(tracks, start_index))

    def sync_playlist(self, tracks: list[Track]) -> PlaybackState:
        return self._controller.sync_playlist(tracks)

    def next_track(self) -> PlaybackState:
        return self._checkpoint_after(self._controller.next_track())

    def previous_track(self) -> PlaybackState:
        return self._checkpoint_after(self._controller.previous_track())

    def current_playlist_index(self) -> int | None:
        return self._controller.current_playlist_index()

    def toggle_shuffle(self) -> PlaybackState:
        return self._notify_playback_modes(self._controller.toggle_shuffle())

    def set_shuffle_enabled(self, enabled: bool) -> PlaybackState:
        return self._notify_playback_modes(
            self._controller.set_shuffle_enabled(enabled)
        )

    def cycle_repeat_mode(self) -> PlaybackState:
        return self._notify_playback_modes(self._controller.cycle_repeat_mode())

    def set_repeat_mode(self, repeat_mode: RepeatMode) -> PlaybackState:
        return self._notify_playback_modes(
            self._controller.set_repeat_mode(repeat_mode)
        )

    def play(self) -> PlaybackState:
        return self._checkpoint_after(self._controller.play())

    def retry(self) -> PlaybackState:
        return self._checkpoint_after(self._controller.retry())

    def pause(self) -> PlaybackState:
        return self._checkpoint_after(self._controller.pause())

    def toggle_play_pause(self) -> PlaybackState:
        return self._checkpoint_after(self._controller.toggle_play_pause())

    def stop(self) -> PlaybackState:
        self.checkpoint(force=True)
        return self._controller.stop()

    def seek(self, position_ms: int) -> PlaybackState:
        return self._checkpoint_after(self._controller.seek(position_ms))

    def seek_relative(self, offset_ms: int) -> PlaybackState:
        return self._checkpoint_after(self._controller.seek_relative(offset_ms))

    def position_ms(self) -> int:
        return self._controller.position_ms()

    def duration_ms(self) -> int:
        return self._controller.duration_ms()

    def set_volume(self, volume: float) -> PlaybackState:
        state = self._controller.set_volume(volume)
        if self._volume_changed is not None:
            self._volume_changed(self._controller.volume())
        return state

    def volume(self) -> float:
        return self._controller.volume()

    def adjust_volume(self, delta: float) -> PlaybackState:
        return self.set_volume(self.volume() + delta)

    def toggle_mute(self) -> PlaybackState:
        current = self.volume()
        if current > 0:
            self._volume_before_mute = current
            return self.set_volume(0.0)
        return self.set_volume(max(0.05, self._volume_before_mute))

    def checkpoint(self, *, force: bool = False) -> None:
        """Persist the current track and position at a bounded write frequency."""
        if self._session_changed is None:
            return
        now = time.monotonic()
        if not force and now - self._last_checkpoint_at < SESSION_CHECKPOINT_SECONDS:
            return
        track = self.state.current_track
        if track is None:
            return
        self._session_changed(track.id, self.position_ms())
        self._last_checkpoint_at = now

    def _checkpoint_after(self, state: PlaybackState) -> PlaybackState:
        self.checkpoint(force=True)
        return state

    def _notify_playback_modes(self, state: PlaybackState) -> PlaybackState:
        if self._playback_modes_changed is not None:
            self._playback_modes_changed(state.repeat_mode, state.shuffle_enabled)
        return state
