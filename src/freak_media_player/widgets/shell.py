"""Main shell widget composition."""

from __future__ import annotations

from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.ui.navigation import NavigationSection
from freak_media_player.widgets.content_panel import ContentPanel
from freak_media_player.widgets.local_tracks_panel import LocalTracksPanel


class ShellContent(QWidget):
    def __init__(
        self,
        local_library_service: LocalLibraryService,
        playback_service: PlaybackService,
    ) -> None:
        super().__init__()
        self._local_library_service = local_library_service
        self._playback_service = playback_service
        self._stack = QStackedWidget()
        self._section_indexes: dict[NavigationSection, int] = {}
        self._build_layout()

    def set_section(self, section: NavigationSection) -> None:
        index = self._section_indexes[section]
        self._stack.setCurrentIndex(index)
        widget = self._stack.widget(index)
        if isinstance(widget, LocalTracksPanel):
            widget.refresh()

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)

        self._add_section(
            NavigationSection.LIBRARY,
            LocalTracksPanel(
                "Library",
                local_library_service=self._local_library_service,
                playback_service=self._playback_service,
            ),
        )
        self._add_section(
            NavigationSection.SEARCH,
            ContentPanel("Search", "Provider-neutral instant search will be wired here."),
        )
        self._add_section(
            NavigationSection.PLAYLISTS,
            LocalTracksPanel(
                "Playlist",
                local_library_service=self._local_library_service,
                playback_service=self._playback_service,
            ),
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
