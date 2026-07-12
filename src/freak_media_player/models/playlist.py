"""Named playlist domain models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NamedPlaylist:
    playlist_id: str
    name: str
    description: str = ""


@dataclass(frozen=True)
class PlaylistImportResult:
    playlist: NamedPlaylist
    track_count: int
    skipped_count: int
