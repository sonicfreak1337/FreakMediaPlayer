"""Local library import use cases."""

from __future__ import annotations

from pathlib import Path

from freak_media_player.core.ports import TrackRepository
from freak_media_player.models.media import Track
from freak_media_player.providers.local_files import (
    LOCAL_FILE_PROVIDER_ID,
    SUPPORTED_AUDIO_EXTENSIONS,
    LocalFileProvider,
)
from freak_media_player.services.settings_service import SettingsService


class LocalLibraryService:
    def __init__(
        self,
        provider: LocalFileProvider,
        track_repository: TrackRepository,
        settings_service: SettingsService | None = None,
    ) -> None:
        self._provider = provider
        self._track_repository = track_repository
        self._settings_service = settings_service

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

    def list_music_folders(self) -> list[Path]:
        if self._settings_service is None:
            return []
        return self._settings_service.load_music_folders()

    def add_music_folder(self, path: Path) -> list[Track]:
        folder = path.resolve()
        if not folder.is_dir():
            raise NotADirectoryError(folder)
        folders = self.list_music_folders()
        if str(folder).casefold() not in {str(item).casefold() for item in folders}:
            folders.append(folder)
            if self._settings_service is not None:
                self._settings_service.save_music_folders(folders)
        return self.import_folder(folder)

    def remove_music_folder(self, path: Path) -> bool:
        target = str(path.resolve()).casefold()
        folders = self.list_music_folders()
        remaining = [
            folder for folder in folders if str(folder.resolve()).casefold() != target
        ]
        if len(remaining) == len(folders):
            return False
        if self._settings_service is not None:
            self._settings_service.save_music_folders(remaining)
        return True

    def rescan_music_folder(self, path: Path) -> list[Track]:
        target = str(path.resolve()).casefold()
        folder = next(
            (
                item
                for item in self.list_music_folders()
                if str(item.resolve()).casefold() == target
            ),
            None,
        )
        if folder is None:
            raise ValueError(f"Not a managed music folder: {path}")
        return self.import_folder(folder)

    def list_tracks(self) -> list[Track]:
        return self._track_repository.list_all()

    def remove_track(self, track_id: str) -> bool:
        return self._track_repository.delete(track_id)

    def list_favorite_track_ids(self) -> set[str]:
        return self._track_repository.list_favorite_ids()

    def set_favorite(self, track_id: str, favorite: bool) -> None:
        self._track_repository.set_favorite(track_id, favorite)

    def refresh_metadata(self) -> int:
        refreshed_count = 0
        for track in self._track_repository.list_all():
            if track.provider_identity.provider_id != LOCAL_FILE_PROVIDER_ID:
                continue
            path = Path(track.provider_identity.item_id)
            if not path.is_file() or not self._provider.is_supported_file(path):
                continue
            self._track_repository.save(self._provider.track_from_path(path))
            refreshed_count += 1
        return refreshed_count

    def supported_extensions(self) -> tuple[str, ...]:
        return tuple(sorted(SUPPORTED_AUDIO_EXTENSIONS))
