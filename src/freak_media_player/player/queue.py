"""Ordered playback queue domain object."""

from __future__ import annotations

from collections.abc import Iterable

from freak_media_player.models.media import Track
from freak_media_player.player.shuffle import ShuffleCycle


class PlaybackQueue:
    def __init__(
        self,
        tracks: Iterable[Track] | None = None,
        shuffle_cycle: ShuffleCycle | None = None,
    ) -> None:
        self._tracks = list(tracks or ())
        self._current_index: int | None = None
        self._shuffle_enabled = False
        self._shuffle_cycle = shuffle_cycle or ShuffleCycle()
        self._play_next: list[Track] = []

    def add(self, track: Track) -> None:
        self._tracks.append(track)
        self._reset_shuffle_cycle()

    def extend(self, tracks: Iterable[Track]) -> None:
        self._tracks.extend(tracks)
        self._reset_shuffle_cycle()

    def replace(
        self,
        tracks: Iterable[Track],
        current_track_id: str | None = None,
    ) -> None:
        self._tracks = list(tracks)
        self._current_index = self._find_track_index(current_track_id)
        self._reset_shuffle_cycle()

    def select(self, index: int) -> Track | None:
        track = self._select(index)
        if track is not None:
            self._reset_shuffle_cycle()
        return track

    def select_track(self, track_id: str) -> Track | None:
        """Select a queued track by its stable library identifier."""
        index = self._find_track_index(track_id)
        return self.select(index) if index is not None else None

    def _select(self, index: int) -> Track | None:
        if not 0 <= index < len(self._tracks):
            return None
        self._current_index = index
        return self._tracks[index]

    def current(self) -> Track | None:
        if self._current_index is None:
            if self._shuffle_enabled:
                return self.next()
            return self.select(0)
        return self._tracks[self._current_index]

    def current_index(self) -> int | None:
        return self._current_index

    def current_playlist_track(self) -> Track | None:
        if self._current_index is None:
            return None
        return self._tracks[self._current_index]

    def next(self) -> Track | None:
        if self._play_next:
            return self._play_next.pop(0)
        if self._shuffle_enabled:
            next_index = self._shuffle_cycle.next_index(self._current_index)
            return self._select(next_index) if next_index is not None else None
        next_index = 0 if self._current_index is None else self._current_index + 1
        return self.select(next_index)

    def previous(self) -> Track | None:
        if self._shuffle_enabled:
            previous_index = self._shuffle_cycle.previous_index()
            return self._select(previous_index) if previous_index is not None else None
        if self._current_index is None:
            return None
        return self.select(self._current_index - 1)

    def set_shuffle_enabled(self, enabled: bool) -> None:
        if enabled == self._shuffle_enabled:
            return
        self._shuffle_enabled = enabled
        if enabled:
            self._shuffle_cycle.reset(len(self._tracks), self._current_index)
        else:
            self._shuffle_cycle.clear()

    def shuffle_enabled(self) -> bool:
        return self._shuffle_enabled

    def clear(self) -> None:
        self._tracks.clear()
        self._play_next.clear()
        self._current_index = None
        self._shuffle_cycle.clear()

    def pending_count(self) -> int:
        if self._current_index is None:
            return len(self._tracks)
        return max(0, len(self._tracks) - self._current_index - 1)

    def track_count(self) -> int:
        return len(self._tracks)

    def enqueue_next(self, tracks: Iterable[Track]) -> None:
        self._play_next.extend(tracks)

    def play_next_tracks(self) -> list[Track]:
        return list(self._play_next)

    def remove_play_next(self, positions: Iterable[int]) -> list[Track]:
        for position in sorted(set(positions), reverse=True):
            if 0 <= position < len(self._play_next):
                self._play_next.pop(position)
        return self.play_next_tracks()

    def move_play_next(self, positions: Iterable[int], target: int) -> list[Track]:
        selected = sorted(
            {
                position
                for position in positions
                if 0 <= position < len(self._play_next)
            }
        )
        if not selected:
            return self.play_next_tracks()
        moving = [self._play_next[position] for position in selected]
        for position in reversed(selected):
            self._play_next.pop(position)
        adjusted_target = max(
            0,
            min(
                target - sum(position < target for position in selected),
                len(self._play_next),
            ),
        )
        self._play_next[adjusted_target:adjusted_target] = moving
        return self.play_next_tracks()

    def _find_track_index(self, track_id: str | None) -> int | None:
        if track_id is None:
            return None
        return next(
            (index for index, track in enumerate(self._tracks) if track.id == track_id),
            None,
        )

    def _reset_shuffle_cycle(self) -> None:
        if self._shuffle_enabled:
            self._shuffle_cycle.reset(len(self._tracks), self._current_index)
