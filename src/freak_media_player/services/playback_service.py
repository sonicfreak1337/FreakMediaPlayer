"""UI-neutral playback use cases."""

from __future__ import annotations

from freak_media_player.models.media import Track
from freak_media_player.models.playback import PlaybackState, RepeatMode
from freak_media_player.player.playback_controller import PlaybackController


class PlaybackService:
    def __init__(self, controller: PlaybackController) -> None:
        self._controller = controller

    @property
    def state(self) -> PlaybackState:
        return self._controller.state

    def enqueue_and_play(self, track: Track) -> PlaybackState:
        return self._controller.play_now(track)

    def play_playlist(self, tracks: list[Track], start_index: int) -> PlaybackState:
        return self._controller.play_playlist(tracks, start_index)

    def sync_playlist(self, tracks: list[Track]) -> PlaybackState:
        return self._controller.sync_playlist(tracks)

    def next_track(self) -> PlaybackState:
        return self._controller.next_track()

    def previous_track(self) -> PlaybackState:
        return self._controller.previous_track()

    def current_playlist_index(self) -> int | None:
        return self._controller.current_playlist_index()

    def toggle_shuffle(self) -> PlaybackState:
        return self._controller.toggle_shuffle()

    def set_shuffle_enabled(self, enabled: bool) -> PlaybackState:
        return self._controller.set_shuffle_enabled(enabled)

    def cycle_repeat_mode(self) -> PlaybackState:
        return self._controller.cycle_repeat_mode()

    def set_repeat_mode(self, repeat_mode: RepeatMode) -> PlaybackState:
        return self._controller.set_repeat_mode(repeat_mode)

    def play(self) -> PlaybackState:
        return self._controller.play()

    def pause(self) -> PlaybackState:
        return self._controller.pause()

    def toggle_play_pause(self) -> PlaybackState:
        return self._controller.toggle_play_pause()

    def stop(self) -> PlaybackState:
        return self._controller.stop()

    def seek(self, position_ms: int) -> PlaybackState:
        return self._controller.seek(position_ms)

    def seek_relative(self, offset_ms: int) -> PlaybackState:
        return self._controller.seek_relative(offset_ms)

    def position_ms(self) -> int:
        return self._controller.position_ms()

    def duration_ms(self) -> int:
        return self._controller.duration_ms()

    def set_volume(self, volume: float) -> PlaybackState:
        return self._controller.set_volume(volume)

    def volume(self) -> float:
        return self._controller.volume()
