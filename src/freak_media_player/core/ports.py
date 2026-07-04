"""Core-facing protocols implemented by outer layers."""

from __future__ import annotations

from typing import Protocol

from freak_media_player.models.media import AudioSource, Track
from freak_media_player.models.playback import PlaybackStatus


class AudioBackend(Protocol):
    def load(self, source: AudioSource) -> None:
        ...

    def play(self) -> None:
        ...

    def pause(self) -> None:
        ...

    def stop(self) -> None:
        ...

    def seek(self, position_ms: int) -> None:
        ...

    def position_ms(self) -> int:
        ...

    def duration_ms(self) -> int:
        ...

    def set_volume(self, volume: float) -> None:
        ...

    def volume(self) -> float:
        ...

    def status(self) -> PlaybackStatus:
        ...


class TrackRepository(Protocol):
    def save(self, track: Track) -> None:
        ...

    def get_by_id(self, track_id: str) -> Track | None:
        ...

    def list_all(self) -> list[Track]:
        ...


class SettingsRepository(Protocol):
    def get(self, key: str) -> str | None:
        ...

    def set(self, key: str, value: str) -> None:
        ...


class AudioSourceResolver(Protocol):
    def resolve_audio_source(self, track: Track) -> AudioSource:
        ...
