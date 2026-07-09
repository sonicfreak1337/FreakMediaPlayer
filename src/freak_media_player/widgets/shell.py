"""Main workspace composition."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from freak_media_player.services.equalizer_service import EqualizerService
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.services.playlist_service import PlaylistService
from freak_media_player.widgets.collapsible_panel import CollapsiblePanel
from freak_media_player.widgets.equalizer_panel import EqualizerPanel
from freak_media_player.widgets.local_tracks_panel import LocalTracksPanel
from freak_media_player.widgets.playlist_panel import PlaylistPanel

WORKSPACE_INITIAL_SIZE = 360
EQUALIZER_INITIAL_SIZE = 280


class ShellContent(QWidget):
    _library_section: CollapsiblePanel
    _playlist_section: CollapsiblePanel
    _equalizer_section: CollapsiblePanel

    def __init__(
        self,
        local_library_service: LocalLibraryService,
        playback_service: PlaybackService,
        playlist_service: PlaylistService,
        equalizer_service: EqualizerService,
    ) -> None:
        super().__init__()
        self._local_library_service = local_library_service
        self._playback_service = playback_service
        self._playlist_service = playlist_service
        self._equalizer_service = equalizer_service
        self._workspace = QSplitter(Qt.Orientation.Horizontal)
        self._modules = QSplitter(Qt.Orientation.Vertical)
        self._build_layout()

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        library_panel = LocalTracksPanel(
            "Local Library",
            local_library_service=self._local_library_service,
            show_title=False,
        )
        playlist_panel = PlaylistPanel(
            playlist_service=self._playlist_service,
            playback_service=self._playback_service,
            show_title=False,
        )
        equalizer_panel = EqualizerPanel(
            equalizer_service=self._equalizer_service,
            show_title=False,
        )
        library_panel.tracks_add_requested.connect(playlist_panel.add_track_ids)

        self._library_section = CollapsiblePanel(
            "Local Library",
            content=library_panel,
            collapse_orientation=Qt.Orientation.Horizontal,
        )
        self._playlist_section = CollapsiblePanel(
            "Playlist",
            content=playlist_panel,
            collapse_orientation=Qt.Orientation.Horizontal,
        )
        self._equalizer_section = CollapsiblePanel(
            "Equalizer",
            content=equalizer_panel,
            collapse_orientation=Qt.Orientation.Vertical,
        )

        self._workspace.setChildrenCollapsible(False)
        self._workspace.addWidget(self._library_section)
        self._workspace.addWidget(self._playlist_section)
        self._workspace.setStretchFactor(0, 1)
        self._workspace.setStretchFactor(1, 1)
        self._workspace.setSizes([WORKSPACE_INITIAL_SIZE, WORKSPACE_INITIAL_SIZE])

        self._modules.setChildrenCollapsible(False)
        self._modules.addWidget(self._workspace)
        self._modules.addWidget(self._equalizer_section)
        self._modules.setStretchFactor(0, 3)
        self._modules.setStretchFactor(1, 2)
        self._modules.setSizes([WORKSPACE_INITIAL_SIZE, EQUALIZER_INITIAL_SIZE])

        self._library_section.expanded_changed.connect(self._balance_workspace)
        self._playlist_section.expanded_changed.connect(self._balance_workspace)
        self._equalizer_section.expanded_changed.connect(self._balance_modules)

        layout.addWidget(self._modules)

    def _balance_workspace(self, _expanded: bool) -> None:
        library_size = (
            WORKSPACE_INITIAL_SIZE if self._library_section.is_expanded() else 0
        )
        playlist_size = (
            WORKSPACE_INITIAL_SIZE if self._playlist_section.is_expanded() else 0
        )
        self._workspace.setSizes([library_size, playlist_size])

    def _balance_modules(self, expanded: bool) -> None:
        equalizer_size = EQUALIZER_INITIAL_SIZE if expanded else 0
        self._modules.setSizes([WORKSPACE_INITIAL_SIZE, equalizer_size])
