"""Search use cases across providers."""

from __future__ import annotations

from collections.abc import Iterable

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
