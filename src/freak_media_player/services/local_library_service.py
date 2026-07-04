"""Local library import use cases."""

from __future__ import annotations

from pathlib import Path

from freak_media_player.core.ports import TrackRepository
from freak_media_player.models.media import Track
from freak_media_player.providers.local_files import LocalFileProvider


class LocalLibraryService:
    def __init__(
        self,
        provider: LocalFileProvider,
        track_repository: TrackRepository,
    ) -> None:
        self._provider = provider
        self._track_repository = track_repository

    def import_file(self, path: Path) -> Track:
        track = self._provider.track_from_path(path)
        self._track_repository.save(track)
        return track

    def import_folder(self, path: Path) -> list[Track]:
        tracks = self._provider.scan(path)
        for track in tracks:
            self._track_repository.save(track)
        return tracks
