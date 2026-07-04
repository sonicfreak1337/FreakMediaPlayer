"""Main shell widget composition."""

from __future__ import annotations

from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from freak_media_player.ui.navigation import NavigationSection
from freak_media_player.widgets.content_panel import ContentPanel


class ShellContent(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._stack = QStackedWidget()
        self._section_indexes: dict[NavigationSection, int] = {}
        self._build_layout()

    def set_section(self, section: NavigationSection) -> None:
        index = self._section_indexes[section]
        self._stack.setCurrentIndex(index)

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)

        self._add_section(
            NavigationSection.LIBRARY,
            ContentPanel("Library", "Albums, artists and saved tracks will live here."),
        )
        self._add_section(
            NavigationSection.SEARCH,
            ContentPanel("Search", "Provider-neutral instant search will be wired here."),
        )
        self._add_section(
            NavigationSection.PLAYLISTS,
            ContentPanel("Playlists", "Local and provider playlists will share this surface."),
        )
        self._add_section(
            NavigationSection.QUEUE,
            ContentPanel("Queue", "The central queue view will mirror playback state."),
        )
        self._add_section(
            NavigationSection.HISTORY,
            ContentPanel("History", "Recently played tracks and sessions will appear here."),
        )
        self._add_section(
            NavigationSection.PLUGINS,
            ContentPanel(
                "Plugins",
                "Installed extensions and their settings will be managed here.",
            ),
        )

    def _add_section(self, section: NavigationSection, widget: QWidget) -> None:
        self._section_indexes[section] = self._stack.addWidget(widget)
