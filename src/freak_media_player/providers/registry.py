"""Provider registry and source resolution."""

from __future__ import annotations

from collections.abc import Iterable

from freak_media_player.models.media import AudioSource, Track
from freak_media_player.providers.base import MediaProvider


class ProviderNotFoundError(LookupError):
    """Raised when a track references an unknown provider."""


class ProviderRegistry:
    def __init__(self, providers: Iterable[MediaProvider] | None = None) -> None:
        self._providers: dict[str, MediaProvider] = {}
        for provider in providers or ():
            self.register(provider)

    def register(self, provider: MediaProvider) -> None:
        self._providers[provider.provider_id] = provider

    def unregister(self, provider_id: str) -> None:
        self._providers.pop(provider_id, None)

    def get(self, provider_id: str) -> MediaProvider | None:
        return self._providers.get(provider_id)

    def providers(self) -> tuple[MediaProvider, ...]:
        return tuple(self._providers.values())

    def resolve_audio_source(self, track: Track) -> AudioSource:
        provider = self.get(track.provider_identity.provider_id)
        if provider is None:
            raise ProviderNotFoundError(
                f"No provider registered for '{track.provider_identity.provider_id}'."
            )
        return provider.resolve_audio_source(track)
