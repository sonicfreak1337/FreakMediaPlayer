"""Main application window and desktop-detachable module workspace."""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QLabel,
    QMainWindow,
    QMenu,
    QSizeGrip,
    QStatusBar,
    QWidget,
)

from freak_media_player import __version__
from freak_media_player.services.equalizer_service import EqualizerService
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.services.playlist_service import PlaylistService
from freak_media_player.ui.constants import (
    WINDOW_MINIMUM_HEIGHT,
    WINDOW_MINIMUM_WIDTH,
    WINDOW_START_HEIGHT,
    WINDOW_START_WIDTH,
)
from freak_media_player.widgets.app_title_bar import AppTitleBar
from freak_media_player.widgets.equalizer_panel import EqualizerPanel
from freak_media_player.widgets.local_tracks_panel import LocalTracksPanel
from freak_media_player.widgets.module_dock import ModuleDockWidget
from freak_media_player.widgets.player_bar import PlayerBar
from freak_media_player.widgets.playlist_panel import PlaylistPanel

CORE_MODULE_HEIGHTS = [165, 325, 260]


class MainWindow(QMainWindow):
    """Frameless branded shell composed from real QDockWidget modules."""

    def __init__(
        self,
        playback_service: PlaybackService,
        local_library_service: LocalLibraryService,
        playlist_service: PlaylistService,
        equalizer_service: EqualizerService,
    ) -> None:
        super().__init__()
        self._playback_service = playback_service
        self._local_library_service = local_library_service
        self._playlist_service = playlist_service
        self._equalizer_service = equalizer_service
        self._module_menu = QMenu("Module", self)
        self._module_docks: dict[str, QDockWidget] = {}

        self.setObjectName("mainWindow")
        self.setWindowTitle(f"Freak Media Player {__version__}")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(WINDOW_MINIMUM_WIDTH, WINDOW_MINIMUM_HEIGHT)
        self.resize(WINDOW_START_WIDTH, WINDOW_START_HEIGHT)
        self.setDockNestingEnabled(True)
        self.setDockOptions(
            QMainWindow.DockOption.AllowNestedDocks
            | QMainWindow.DockOption.AllowTabbedDocks
            | QMainWindow.DockOption.AnimatedDocks
        )
        self.setMenuWidget(AppTitleBar(self))
        self._build_layout()

    @property
    def module_menu(self) -> QMenu:
        """Visibility menu used by built-in and plugin-provided modules."""
        return self._module_menu

    def add_module(
        self,
        title: str,
        widget: QWidget,
        object_name: str,
        *,
        closable: bool = True,
        area: Qt.DockWidgetArea = Qt.DockWidgetArea.TopDockWidgetArea,
        header_controls: Iterable[QWidget] = (),
    ) -> QDockWidget:
        """Register a movable module that can become a desktop window."""
        dock = ModuleDockWidget(
            title,
            self,
            closable=closable,
            controls=header_controls,
        )
        dock.setObjectName(object_name)
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        features = (
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        if closable:
            features |= QDockWidget.DockWidgetFeature.DockWidgetClosable
        dock.setFeatures(features)
        dock.setWidget(widget)
        self.addDockWidget(area, dock)
        self._module_docks[object_name] = dock

        if closable:
            action = dock.toggleViewAction()
            action.setText(title)
            self._module_menu.addAction(action)
        return dock

    def stack_module_below(
        self,
        reference_name: str,
        dock: QDockWidget,
        preferred_height: int,
    ) -> None:
        """Place a late plugin module as a full-width row below a core module."""
        reference = self.module(reference_name)
        if reference is None:
            return
        self.splitDockWidget(reference, dock, Qt.Orientation.Vertical)
        rows = [
            item
            for name in (
                "playerModule",
                "localLibraryModule",
                "equalizerModule",
                dock.objectName(),
            )
            if (item := self.module(name)) is not None
        ]
        heights = [165, 325, 260, preferred_height][: len(rows)]
        self.resizeDocks(rows, heights, Qt.Orientation.Vertical)

    def remove_module(self, object_name: str) -> None:
        """Forget a plugin module after its dock has been deactivated."""
        self._module_docks.pop(object_name, None)

    def _build_layout(self) -> None:
        player_panel = PlayerBar(playback_service=self._playback_service)
        player_panel.set_module_menu(self._module_menu)
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

        player_dock = self.add_module(
            "Player", player_panel, "playerModule", closable=False
        )
        library_dock = self.add_module(
            "Local Library",
            library_panel,
            "localLibraryModule",
            header_controls=library_panel.header_controls,
        )
        equalizer_dock = self.add_module(
            "Equalizer",
            equalizer_panel,
            "equalizerModule",
            header_controls=equalizer_panel.header_controls,
        )

        # Build the same split tree as the mockup: a full-width player, a two-column
        # library row, then full-width EQ and plugin rows underneath.
        self.splitDockWidget(player_dock, library_dock, Qt.Orientation.Vertical)
        self.splitDockWidget(library_dock, equalizer_dock, Qt.Orientation.Vertical)
        playlist_dock = self.add_module(
            "Playlist",
            playlist_panel,
            "playlistModule",
            header_controls=playlist_panel.header_controls,
        )
        self.splitDockWidget(library_dock, playlist_dock, Qt.Orientation.Horizontal)
        self.resizeDocks(
            [player_dock, library_dock, equalizer_dock],
            CORE_MODULE_HEIGHTS,
            Qt.Orientation.Vertical,
        )
        self.resizeDocks(
            [library_dock, playlist_dock],
            [52, 48],
            Qt.Orientation.Horizontal,
        )
        self._build_status_bar()

    def _build_status_bar(self) -> None:
        status_bar = QStatusBar(self)
        status_bar.setObjectName("appStatusBar")
        status_bar.setSizeGripEnabled(False)
        ready = QLabel("●  Ready")
        ready.setObjectName("readyStatus")
        queue = QLabel("●  Queue is ready")
        queue.setObjectName("queueStatus")
        status_bar.addWidget(ready)
        status_bar.addWidget(queue, 1)
        status_bar.addPermanentWidget(QLabel(f"Freak Media Player {__version__}"))
        status_bar.addPermanentWidget(QSizeGrip(self))
        self.setStatusBar(status_bar)

    def module(self, object_name: str) -> QDockWidget | None:
        """Return a registered module (used by plugins and tests)."""
        return self._module_docks.get(object_name)
