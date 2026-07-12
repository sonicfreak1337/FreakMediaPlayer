"""Playback state models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum

from freak_media_player.models.media import Track


@dataclass(frozen=True)
class AudioOutputDevice:
    device_id: str
    description: str
    is_default: bool = False


class PlaybackStatus(StrEnum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    BUFFERING = "buffering"
    ERROR = "error"


class RepeatMode(StrEnum):
    OFF = "off"
    ONE = "one"
    ALL = "all"


@dataclass(frozen=True)
class PlaybackState:
    status: PlaybackStatus = PlaybackStatus.STOPPED
    current_track: Track | None = None
    position: timedelta = timedelta()
    repeat_mode: RepeatMode = RepeatMode.OFF
    shuffle_enabled: bool = False
    error_message: str | None = None
