"""Media domain models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class ProviderIdentity:
    provider_id: str
    item_id: str


@dataclass(frozen=True)
class Artist:
    name: str
    provider_identity: ProviderIdentity | None = None


@dataclass(frozen=True)
class Album:
    title: str
    artist: Artist | None = None
    provider_identity: ProviderIdentity | None = None
    cover_url: str | None = None


@dataclass(frozen=True)
class Track:
    id: str
    provider_identity: ProviderIdentity
    title: str
    artist: Artist
    album: Album | None = None
    duration: timedelta | None = None
    cover_url: str | None = None
