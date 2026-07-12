"""Search use cases across providers."""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from freak_media_player.models.media import Track
from freak_media_player.providers.base import MediaProvider, SearchQuery

FILE_STATUS_AVAILABLE = "available"
FILE_STATUS_MISSING = "missing"
FILE_STATUS_UNREADABLE = "unreadable"


@dataclass(frozen=True)
class LibraryFilters:
    artist: str | None = None
    album: str | None = None
    genre: str | None = None
    year: int | None = None
    favorite: bool | None = None
    file_status: str | None = None


class SearchService:
    def __init__(self, providers: Iterable[MediaProvider]) -> None:
        self._providers = tuple(providers)

    def search_tracks(self, text: str, limit_per_provider: int = 25) -> list[Track]:
        query = SearchQuery(text=text, limit=limit_per_provider)
        results: list[Track] = []
        for provider in self._providers:
            if provider.capabilities.search:
                results.extend(provider.search_tracks(query))
        return results

    def search_library(self, tracks: Iterable[Track], text: str) -> list[Track]:
        """Filter imported tracks across user-visible metadata and filename."""
        terms = tuple(part.casefold() for part in text.split() if part.strip())
        catalog = list(tracks)
        if not terms:
            return catalog
        return [
            track
            for track in catalog
            if all(term in self._searchable_text(track) for term in terms)
        ]

    def filter_library(
        self,
        tracks: Iterable[Track],
        filters: LibraryFilters,
        favorite_ids: set[str] | None = None,
    ) -> list[Track]:
        favorites = favorite_ids or set()
        return [
            track
            for track in tracks
            if (filters.artist is None or track.artist.name == filters.artist)
            and (
                filters.album is None
                or (track.album is not None and track.album.title == filters.album)
            )
            and (filters.genre is None or track.genre == filters.genre)
            and (
                filters.year is None
                or (
                    track.album is not None
                    and track.album.release_year == filters.year
                )
            )
            and (
                filters.favorite is None
                or (track.id in favorites) is filters.favorite
            )
            and (
                filters.file_status is None
                or self.file_status(track) == filters.file_status
            )
        ]

    def file_status(self, track: Track) -> str:
        path = Path(track.provider_identity.item_id)
        if not path.is_file():
            return FILE_STATUS_MISSING
        if not os.access(path, os.R_OK):
            return FILE_STATUS_UNREADABLE
        return FILE_STATUS_AVAILABLE

    def _searchable_text(self, track: Track) -> str:
        album = track.album
        values = (
            track.title,
            track.artist.name,
            album.title if album is not None else "",
            album.artist.name if album is not None and album.artist is not None else "",
            str(album.release_year) if album is not None and album.release_year else "",
            track.genre or "",
            Path(track.provider_identity.item_id).name,
        )
        return "\n".join(values).casefold()
