"""Ordered playback queue domain object."""

from __future__ import annotations

from collections.abc import Iterable

from freak_media_player.models.media import Track


class PlaybackQueue:
    def __init__(self, tracks: Iterable[Track] | None = None) -> None:
        self._tracks = list(tracks or ())
        self._current_index: int | None = None

    def add(self, track: Track) -> None:
        self._tracks.append(track)

    def extend(self, tracks: Iterable[Track]) -> None:
        self._tracks.extend(tracks)

    def replace(
        self,
        tracks: Iterable[Track],
        current_track_id: str | None = None,
    ) -> None:
        self._tracks = list(tracks)
        self._current_index = self._find_track_index(current_track_id)

    def select(self, index: int) -> Track | None:
        if not 0 <= index < len(self._tracks):
            return None
        self._current_index = index
        return self._tracks[index]

    def current(self) -> Track | None:
        if self._current_index is None:
            return self.select(0)
        return self._tracks[self._current_index]

    def next(self) -> Track | None:
        next_index = 0 if self._current_index is None else self._current_index + 1
        return self.select(next_index)

    def previous(self) -> Track | None:
        if self._current_index is None:
            return None
        return self.select(self._current_index - 1)

    def clear(self) -> None:
        self._tracks.clear()
        self._current_index = None

    def pending_count(self) -> int:
        if self._current_index is None:
            return len(self._tracks)
        return max(0, len(self._tracks) - self._current_index - 1)

    def _find_track_index(self, track_id: str | None) -> int | None:
        if track_id is None:
            return None
        return next(
            (index for index, track in enumerate(self._tracks) if track.id == track_id),
            None,
        )
