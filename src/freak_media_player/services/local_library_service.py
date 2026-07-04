"""Local library import use cases."""

from __future__ import annotations

from pathlib import Path

from freak_media_player.core.ports import TrackRepository
from freak_media_player.models.media import Track
from freak_media_player.providers.local_files import (
    SUPPORTED_AUDIO_EXTENSIONS,
    LocalFileProvider,
)


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

    def import_paths(self, paths: list[Path]) -> list[Track]:
        imported: list[Track] = []
        for path in paths:
            if path.is_dir():
                imported.extend(self.import_folder(path))
            elif self._provider.is_supported_file(path):
                imported.append(self.import_file(path))
        return imported

    def import_folder(self, path: Path) -> list[Track]:
        tracks = self._provider.scan(path)
        for track in tracks:
            self._track_repository.save(track)
        return tracks

    def list_tracks(self) -> list[Track]:
        return self._track_repository.list_all()

    def remove_track(self, track_id: str) -> bool:
        return self._track_repository.delete(track_id)

    def supported_extensions(self) -> tuple[str, ...]:
        return tuple(sorted(SUPPORTED_AUDIO_EXTENSIONS))
