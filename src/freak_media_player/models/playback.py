"""Playback state models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum

from freak_media_player.models.media import Track


class AudioOutputMode(StrEnum):
    MONO = "mono"
    STEREO = "stereo"
    SURROUND_5_1 = "5.1"
    SURROUND_7_1 = "7.1"

    @property
    def channels(self) -> int:
        return {
            self.MONO: 1,
            self.STEREO: 2,
            self.SURROUND_5_1: 6,
            self.SURROUND_7_1: 8,
        }[self]

    @property
    def av_layout(self) -> str:
        return str(self)


@dataclass(frozen=True)
class AudioOutputDevice:
    device_id: str
    description: str
    is_default: bool = False
    supported_modes: tuple[AudioOutputMode, ...] = (AudioOutputMode.STEREO,)


class PlaybackStatus(StrEnum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    BUFFERING = "buffering"
    ERROR = "error"


class StreamBufferProfile(StrEnum):
    SMALL = "small"
    NORMAL = "normal"
    STABLE = "stable"


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
