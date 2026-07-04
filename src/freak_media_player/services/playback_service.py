"""UI-neutral playback use cases."""

from __future__ import annotations

from freak_media_player.models.media import Track
from freak_media_player.models.playback import PlaybackState
from freak_media_player.player.playback_controller import PlaybackController


class PlaybackService:
    def __init__(self, controller: PlaybackController) -> None:
        self._controller = controller

    @property
    def state(self) -> PlaybackState:
        return self._controller.state

    def enqueue_and_play(self, track: Track) -> PlaybackState:
        return self._controller.play_now(track)

    def play(self) -> PlaybackState:
        return self._controller.play()

    def pause(self) -> PlaybackState:
        return self._controller.pause()

    def stop(self) -> PlaybackState:
        return self._controller.stop()
