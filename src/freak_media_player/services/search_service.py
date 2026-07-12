"""Search use cases across providers."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from freak_media_player.models.media import Track
from freak_media_player.providers.base import MediaProvider, SearchQuery


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
