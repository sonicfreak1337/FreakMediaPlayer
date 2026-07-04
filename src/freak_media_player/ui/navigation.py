"""Navigation state for the desktop shell."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NavigationSection(str, Enum):
    LIBRARY = "library"
    SEARCH = "search"
    PLAYLISTS = "playlists"
    QUEUE = "queue"
    HISTORY = "history"
    PLUGINS = "plugins"


@dataclass(frozen=True)
class NavigationItem:
    section: NavigationSection
    label: str


class NavigationViewModel:
    def __init__(self) -> None:
        self._items = (
            NavigationItem(NavigationSection.LIBRARY, "Library"),
            NavigationItem(NavigationSection.SEARCH, "Search"),
            NavigationItem(NavigationSection.PLAYLISTS, "Playlists"),
            NavigationItem(NavigationSection.QUEUE, "Queue"),
            NavigationItem(NavigationSection.HISTORY, "History"),
            NavigationItem(NavigationSection.PLUGINS, "Plugins"),
        )
        self._selected_section = NavigationSection.LIBRARY

    @property
    def items(self) -> tuple[NavigationItem, ...]:
        return self._items

    @property
    def selected_section(self) -> NavigationSection:
        return self._selected_section

    def select(self, section: NavigationSection) -> None:
        self._selected_section = section
