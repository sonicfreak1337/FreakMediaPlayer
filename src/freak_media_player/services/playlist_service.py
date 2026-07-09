"""Persistent active-playlist use cases."""

from __future__ import annotations

from collections.abc import Iterable

from freak_media_player.core.ports import PlaylistRepository, TrackRepository
from freak_media_player.models.media import Track

DEFAULT_PLAYLIST_ID = "active-playlist"
DEFAULT_PLAYLIST_NAME = "Playlist"


class PlaylistService:
    def __init__(
        self,
        playlist_repository: PlaylistRepository,
        track_repository: TrackRepository,
    ) -> None:
        self._playlist_repository = playlist_repository
        self._track_repository = track_repository
        self._playlist_repository.ensure(DEFAULT_PLAYLIST_ID, DEFAULT_PLAYLIST_NAME)

    def list_tracks(self) -> list[Track]:
        return self._playlist_repository.list_tracks(DEFAULT_PLAYLIST_ID)

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
        self._playlist_repository.replace_tracks(DEFAULT_PLAYLIST_ID, tracks)

    def _clamp_position(self, position: int | None, length: int) -> int:
        if position is None:
            return length
        return min(length, max(0, position))

    def _valid_positions(self, positions: Iterable[int], length: int) -> set[int]:
        return {position for position in positions if 0 <= position < length}
