"""Provider contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from freak_media_player.models.media import AudioSource, Track


@dataclass(frozen=True)
class SearchQuery:
    text: str
    limit: int = 25


@dataclass(frozen=True)
class ProviderCapabilities:
    search: bool = False
    streaming: bool = False
    library: bool = False
    playlists: bool = False


class MediaProvider(Protocol):
    provider_id: str
    display_name: str
    capabilities: ProviderCapabilities

    def search_tracks(self, query: SearchQuery) -> list[Track]:
        ...

    def resolve_audio_source(self, track: Track) -> AudioSource:
        ...
