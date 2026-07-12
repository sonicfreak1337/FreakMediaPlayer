"""Persistent active-playlist use cases."""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from uuid import uuid4

from freak_media_player.core.ports import PlaylistRepository, TrackRepository
from freak_media_player.models.media import Track
from freak_media_player.models.playlist import NamedPlaylist, PlaylistImportResult
from freak_media_player.providers.local_files import LOCAL_FILE_PROVIDER_ID
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.settings_service import SettingsService

DEFAULT_PLAYLIST_ID = "active-playlist"
DEFAULT_PLAYLIST_NAME = "Playlist"


class PlaylistService:
    def __init__(
        self,
        playlist_repository: PlaylistRepository,
        track_repository: TrackRepository,
        settings_service: SettingsService | None = None,
        local_library_service: LocalLibraryService | None = None,
    ) -> None:
        self._playlist_repository = playlist_repository
        self._track_repository = track_repository
        self._settings_service = settings_service
        self._local_library_service = local_library_service
        self._playlist_repository.ensure(DEFAULT_PLAYLIST_ID, DEFAULT_PLAYLIST_NAME)
        saved_id = (
            settings_service.load_active_playlist_id(DEFAULT_PLAYLIST_ID)
            if settings_service is not None
            else DEFAULT_PLAYLIST_ID
        )
        available_ids = {
            playlist.playlist_id for playlist in self._playlist_repository.list_playlists()
        }
        self._active_playlist_id = (
            saved_id if saved_id in available_ids else DEFAULT_PLAYLIST_ID
        )
        self._persist_active_playlist()

    def list_tracks(self) -> list[Track]:
        return self._playlist_repository.list_tracks(self._active_playlist_id)

    def list_playlists(self) -> list[NamedPlaylist]:
        return self._playlist_repository.list_playlists()

    def active_playlist_id(self) -> str:
        return self._active_playlist_id

    def create_playlist(self, name: str) -> NamedPlaylist:
        clean_name = self._validate_unique_name(name)
        playlist = NamedPlaylist(f"playlist-{uuid4().hex}", clean_name)
        self._playlist_repository.ensure(playlist.playlist_id, playlist.name)
        self._active_playlist_id = playlist.playlist_id
        self._persist_active_playlist()
        return playlist

    def switch_playlist(self, playlist_id: str) -> list[Track]:
        if playlist_id not in {
            playlist.playlist_id for playlist in self.list_playlists()
        }:
            raise KeyError(playlist_id)
        self._active_playlist_id = playlist_id
        self._persist_active_playlist()
        return self.list_tracks()

    def duplicate_active_playlist(self, name: str | None = None) -> NamedPlaylist:
        source = self._active_playlist()
        clean_name = self._validate_unique_name(name or f"{source.name} Copy")
        tracks = self.list_tracks()
        duplicate = self.create_playlist(clean_name)
        self._playlist_repository.replace_tracks(duplicate.playlist_id, tracks)
        return duplicate

    def rename_active_playlist(self, name: str) -> NamedPlaylist:
        clean_name = self._validate_unique_name(
            name, exclude_id=self._active_playlist_id
        )
        self._playlist_repository.rename(self._active_playlist_id, clean_name)
        return NamedPlaylist(self._active_playlist_id, clean_name)

    def delete_active_playlist(self) -> NamedPlaylist:
        deleted_id = self._active_playlist_id
        self._playlist_repository.delete(deleted_id)
        remaining = self.list_playlists()
        if not remaining:
            self._playlist_repository.ensure(
                DEFAULT_PLAYLIST_ID, DEFAULT_PLAYLIST_NAME
            )
            remaining = self.list_playlists()
        self._active_playlist_id = remaining[0].playlist_id
        self._persist_active_playlist()
        return remaining[0]

    def import_m3u(self, playlist_path: Path) -> PlaylistImportResult:
        path = playlist_path.resolve()
        if path.suffix.lower() not in {".m3u", ".m3u8"}:
            raise ValueError("Playlist must use the .m3u or .m3u8 extension.")
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        tracks: list[Track] = []
        skipped = 0
        for line in lines:
            value = line.strip()
            if not value or value.startswith("#"):
                continue
            source = Path(value)
            if not source.is_absolute():
                source = path.parent / source
            source = source.resolve()
            track = self._track_repository.get_by_provider_item(
                LOCAL_FILE_PROVIDER_ID, str(source)
            )
            if track is None and self._local_library_service is not None:
                try:
                    track = self._local_library_service.import_file(source)
                except (OSError, ValueError):
                    track = None
            if track is None:
                skipped += 1
            else:
                tracks.append(track)
        playlist = self.create_playlist(self._unique_playlist_name(path.stem))
        self._playlist_repository.replace_tracks(playlist.playlist_id, tracks)
        return PlaylistImportResult(playlist, len(tracks), skipped)

    def export_m3u(self, playlist_path: Path, *, relative: bool = True) -> Path:
        path = playlist_path
        if path.suffix.lower() not in {".m3u", ".m3u8"}:
            path = path.with_suffix(".m3u8")
        path = path.resolve()
        lines = ["#EXTM3U"]
        for track in self.list_tracks():
            source = Path(track.provider_identity.item_id).resolve()
            lines.append(
                os.path.relpath(source, path.parent) if relative else str(source)
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def add_track_ids(
        self,
        track_ids: Iterable[str],
        position: int | None = None,
    ) -> list[Track]:
        tracks: list[Track] = []
        for track_id in track_ids:
            track = self._track_repository.get_by_id(track_id)
            if track is not None:
                tracks.append(track)
        return self.add_tracks(tracks, position)

    def add_tracks(
        self,
        new_tracks: Iterable[Track],
        position: int | None = None,
    ) -> list[Track]:
        tracks = self.list_tracks()
        insert_at = self._clamp_position(position, len(tracks))
        tracks[insert_at:insert_at] = list(new_tracks)
        self._save(tracks)
        return tracks

    def remove_positions(self, positions: Iterable[int]) -> list[Track]:
        tracks = self.list_tracks()
        selected = self._valid_positions(positions, len(tracks))
        tracks = [track for index, track in enumerate(tracks) if index not in selected]
        self._save(tracks)
        return tracks

    def move_positions(self, positions: Iterable[int], target: int) -> list[Track]:
        tracks = self.list_tracks()
        selected = self._valid_positions(positions, len(tracks))
        if not selected:
            return tracks

        moving = [tracks[index] for index in sorted(selected)]
        remaining = [track for index, track in enumerate(tracks) if index not in selected]
        adjusted_target = target - sum(index < target for index in selected)
        insert_at = self._clamp_position(adjusted_target, len(remaining))
        remaining[insert_at:insert_at] = moving
        self._save(remaining)
        return remaining

    def clear(self) -> None:
        self._save([])

    def _save(self, tracks: list[Track]) -> None:
        self._playlist_repository.replace_tracks(self._active_playlist_id, tracks)

    def _active_playlist(self) -> NamedPlaylist:
        return next(
            playlist
            for playlist in self.list_playlists()
            if playlist.playlist_id == self._active_playlist_id
        )

    def _validate_unique_name(
        self, name: str, exclude_id: str | None = None
    ) -> str:
        clean_name = " ".join(name.split())
        if not clean_name:
            raise ValueError("Playlist name cannot be empty.")
        if len(clean_name) > 100:
            raise ValueError("Playlist name cannot exceed 100 characters.")
        if any(
            playlist.name.casefold() == clean_name.casefold()
            and playlist.playlist_id != exclude_id
            for playlist in self.list_playlists()
        ):
            raise ValueError("A playlist with that name already exists.")
        return clean_name

    def _unique_playlist_name(self, preferred: str) -> str:
        base = " ".join(preferred.split()) or "Imported Playlist"
        existing = {playlist.name.casefold() for playlist in self.list_playlists()}
        if base.casefold() not in existing:
            return base
        suffix = 2
        while f"{base} {suffix}".casefold() in existing:
            suffix += 1
        return f"{base} {suffix}"

    def _persist_active_playlist(self) -> None:
        if self._settings_service is not None:
            self._settings_service.save_active_playlist_id(
                self._active_playlist_id
            )

    def _clamp_position(self, position: int | None, length: int) -> int:
        if position is None:
            return length
        return min(length, max(0, position))

    def _valid_positions(self, positions: Iterable[int], length: int) -> set[int]:
        return {position for position in positions if 0 <= position < length}
