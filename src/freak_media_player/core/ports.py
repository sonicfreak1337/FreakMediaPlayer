"""Core-facing protocols implemented by outer layers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from freak_media_player.models.equalizer import EqualizerPreset
from freak_media_player.models.media import AudioSource, Track
from freak_media_player.models.playback import PlaybackStatus
from freak_media_player.models.playlist import NamedPlaylist


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

    def set_equalizer_preset(self, preset: EqualizerPreset) -> None:
        ...

    def equalizer_preset(self) -> EqualizerPreset:
        ...

    def status(self) -> PlaybackStatus:
        ...

    def error_message(self) -> str | None:
        ...

    def set_finished_callback(self, callback: Callable[[], None]) -> None:
        ...


class TrackRepository(Protocol):
    def save(self, track: Track) -> None:
        ...

    def get_by_id(self, track_id: str) -> Track | None:
        ...

    def get_by_provider_item(self, provider_id: str, item_id: str) -> Track | None:
        ...

    def delete(self, track_id: str) -> bool:
        ...

    def list_all(self) -> list[Track]:
        ...

    def list_favorite_ids(self) -> set[str]:
        ...

    def is_favorite(self, track_id: str) -> bool:
        ...

    def set_favorite(self, track_id: str, favorite: bool) -> None:
        ...

    def update_provider_item(self, track_id: str, item_id: str) -> None:
        ...

    def update_metadata(
        self,
        track_id: str,
        *,
        title: str,
        artist: str,
        album: str | None,
        release_year: int | None,
        genre: str | None,
        track_number: int | None,
        disc_number: int | None,
    ) -> None:
        ...

    def list_recently_added_ids(self, limit: int = 100) -> list[str]:
        ...


class PlaylistRepository(Protocol):
    def ensure(self, playlist_id: str, name: str) -> None:
        ...

    def list_tracks(self, playlist_id: str) -> list[Track]:
        ...

    def replace_tracks(self, playlist_id: str, tracks: Sequence[Track]) -> None:
        ...

    def list_playlists(self) -> list[NamedPlaylist]:
        ...

    def rename(self, playlist_id: str, name: str) -> None:
        ...

    def delete(self, playlist_id: str) -> bool:
        ...


class SettingsRepository(Protocol):
    def get(self, key: str) -> str | None:
        ...

    def set(self, key: str, value: str) -> None:
        ...


class AudioSourceResolver(Protocol):
    def resolve_audio_source(self, track: Track) -> AudioSource:
        ...
