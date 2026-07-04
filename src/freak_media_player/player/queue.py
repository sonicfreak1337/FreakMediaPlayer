"""Playback queue domain object."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from freak_media_player.models.media import Track


class PlaybackQueue:
    def __init__(self, tracks: Iterable[Track] | None = None) -> None:
        self._tracks: deque[Track] = deque(tracks or ())
        self._current: Track | None = None

    def add(self, track: Track) -> None:
        self._tracks.append(track)

    def extend(self, tracks: Iterable[Track]) -> None:
        self._tracks.extend(tracks)

    def replace(self, tracks: Iterable[Track]) -> None:
        self.clear()
        self.extend(tracks)

    def current(self) -> Track | None:
        if self._current is None:
            self._current = self.next()
        return self._current

    def next(self) -> Track | None:
        if not self._tracks:
            self._current = None
            return None
        self._current = self._tracks.popleft()
        return self._current

    def clear(self) -> None:
        self._tracks.clear()
        self._current = None

    def pending_count(self) -> int:
        return len(self._tracks)
