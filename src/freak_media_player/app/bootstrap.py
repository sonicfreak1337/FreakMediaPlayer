"""Dependency wiring for the desktop application."""

from __future__ import annotations

from dataclasses import dataclass

from freak_media_player.player.audio_backend import NullAudioBackend
from freak_media_player.player.playback_controller import PlaybackController
from freak_media_player.player.queue import PlaybackQueue
from freak_media_player.services.playback_service import PlaybackService


@dataclass(frozen=True)
class AppContext:
    playback_service: PlaybackService


def build_app_context() -> AppContext:
    queue = PlaybackQueue()
    audio_backend = NullAudioBackend()
    controller = PlaybackController(queue=queue, audio_backend=audio_backend)
    playback_service = PlaybackService(controller=controller)
    return AppContext(playback_service=playback_service)
