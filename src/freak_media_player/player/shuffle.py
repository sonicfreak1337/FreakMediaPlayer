"""Non-repeating shuffle cycle state."""

from __future__ import annotations

import random


class ShuffleCycle:
    def __init__(self, randomizer: random.Random | None = None) -> None:
        self._randomizer = randomizer or random.Random()
        self._size = 0
        self._remaining: list[int] = []
        self._played: set[int] = set()
        self._history: list[int] = []
        self._history_index = -1

    def reset(self, size: int, current_index: int | None = None) -> None:
        self.clear()
        self._size = max(0, size)
        self._remaining = list(range(self._size))
        if current_index is not None and 0 <= current_index < self._size:
            self._remaining.remove(current_index)
            self._played.add(current_index)
            self._history.append(current_index)
            self._history_index = 0
        self._randomizer.shuffle(self._remaining)

    def next_index(self, current_index: int | None = None) -> int | None:
        if self._size == 0:
            return None
        if self._history_index + 1 < len(self._history):
            self._history_index += 1
            return self._history[self._history_index]
        if not self._remaining:
            self._begin_next_cycle(current_index)
        next_index = self._remaining.pop()
        self._played.add(next_index)
        self._history.append(next_index)
        self._history_index = len(self._history) - 1
        return next_index

    def previous_index(self) -> int | None:
        if self._history_index <= 0:
            return None
        self._history_index -= 1
        return self._history[self._history_index]

    def clear(self) -> None:
        self._size = 0
        self._remaining.clear()
        self._played.clear()
        self._history.clear()
        self._history_index = -1

    def played_indices(self) -> frozenset[int]:
        return frozenset(self._played)

    def remaining_indices(self) -> frozenset[int]:
        return frozenset(self._remaining)

    def _begin_next_cycle(self, current_index: int | None) -> None:
        self._played.clear()
        self._remaining = list(range(self._size))
        self._randomizer.shuffle(self._remaining)
        if (
            self._size > 1
            and current_index is not None
            and self._remaining[-1] == current_index
        ):
            self._remaining[0], self._remaining[-1] = (
                self._remaining[-1],
                self._remaining[0],
            )
