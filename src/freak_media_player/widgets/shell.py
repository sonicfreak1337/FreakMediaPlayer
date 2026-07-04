"""Main shell widget composition."""

from __future__ import annotations

from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from freak_media_player.services.equalizer_service import EqualizerService
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.ui.navigation import NavigationSection
from freak_media_player.widgets.equalizer_panel import EqualizerPanel
from freak_media_player.widgets.local_tracks_panel import LocalTracksPanel


class ShellContent(QWidget):
    def __init__(
        self,
        local_library_service: LocalLibraryService,
        playback_service: PlaybackService,
        equalizer_service: EqualizerService,
    ) -> None:
        super().__init__()
        self._local_library_service = local_library_service
        self._playback_service = playback_service
        self._equalizer_service = equalizer_service
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
                "Local Library",
                local_library_service=self._local_library_service,
                playback_service=self._playback_service,
            ),
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
            NavigationSection.EQUALIZER,
            EqualizerPanel(equalizer_service=self._equalizer_service),
        )

    def _add_section(self, section: NavigationSection, widget: QWidget) -> None:
        self._section_indexes[section] = self._stack.addWidget(widget)
