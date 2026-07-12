"""Main application window and desktop-detachable module workspace."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING

from PySide6.QtCore import QByteArray, Qt, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QDockWidget,
    QLabel,
    QMainWindow,
    QMenu,
    QSizeGrip,
    QStatusBar,
    QWidget,
)

from freak_media_player import __version__
from freak_media_player.models.playback import AudioOutputMode
from freak_media_player.services.equalizer_service import EqualizerService
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.services.playlist_service import PlaylistService
from freak_media_player.services.search_service import SearchService
from freak_media_player.services.settings_service import SettingsService
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
from freak_media_player.widgets.settings_dialog import SettingsDialog

if TYPE_CHECKING:
    from freak_media_player.ui.skins import SkinManager

CORE_MODULE_HEIGHTS = [165, 325, 260]
LAYOUT_STATE_VERSION = 1


class MainWindow(QMainWindow):
    """Frameless branded shell composed from real QDockWidget modules."""

    layout_reset_requested = Signal()
    visualizer_quality_changed = Signal(str)

    def __init__(
        self,
        playback_service: PlaybackService,
        local_library_service: LocalLibraryService,
        playlist_service: PlaylistService,
        equalizer_service: EqualizerService,
        skin_manager: SkinManager | None = None,
        search_service: SearchService | None = None,
        settings_service: SettingsService | None = None,
    ) -> None:
        super().__init__()
        self._playback_service = playback_service
        self._local_library_service = local_library_service
        self._playlist_service = playlist_service
        self._equalizer_service = equalizer_service
        self._search_service = search_service
        self._skin_manager = skin_manager
        self._settings_service = settings_service
        self._module_menu = QMenu("Module", self)
        self._module_docks: dict[str, QDockWidget] = {}
        self._shortcuts: list[QShortcut] = []

        self.setObjectName("mainWindow")
        self.setWindowTitle(f"Freak Media Player {__version__}")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setMinimumSize(WINDOW_MINIMUM_WIDTH, WINDOW_MINIMUM_HEIGHT)
        self.resize(WINDOW_START_WIDTH, WINDOW_START_HEIGHT)
        self.setDockNestingEnabled(True)
        self.setDockOptions(
            QMainWindow.DockOption.AllowNestedDocks
            | QMainWindow.DockOption.AllowTabbedDocks
            | QMainWindow.DockOption.AnimatedDocks
        )
        self.setMenuWidget(AppTitleBar(self, skin_manager))
        self._build_layout()
        self._add_layout_reset_action()
        self._configure_shortcuts()

    @property
    def module_menu(self) -> QMenu:
        """Visibility menu used by built-in and plugin-provided modules."""
        return self._module_menu

    @property
    def skin_manager(self) -> SkinManager | None:
        """Expose the active skin source to skin-aware plugin modules."""
        return self._skin_manager

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

    def capture_layout(self) -> tuple[bytes, bytes]:
        """Capture main-window geometry and every registered dock's state."""
        return (
            bytes(self.saveGeometry().data()),
            bytes(self.saveState(LAYOUT_STATE_VERSION).data()),
        )

    def restore_layout(self, geometry: bytes, window_state: bytes) -> bool:
        """Restore geometry after all core and plugin docks have been registered."""
        geometry_restored = self.restoreGeometry(QByteArray(geometry))
        state_restored = self.restoreState(
            QByteArray(window_state), LAYOUT_STATE_VERSION
        )
        return geometry_restored and state_restored

    def _build_layout(self) -> None:
        player_panel = PlayerBar(
            playback_service=self._playback_service,
            local_library_service=self._local_library_service,
        )
        self._player_panel = player_panel
        player_panel.set_module_menu(self._module_menu)
        library_panel = LocalTracksPanel(
            "Local Library",
            local_library_service=self._local_library_service,
            show_title=False,
            search_service=self._search_service,
        )
        self._library_panel = library_panel
        playlist_panel = PlaylistPanel(
            playlist_service=self._playlist_service,
            playback_service=self._playback_service,
            show_title=False,
            local_library_service=self._local_library_service,
        )
        equalizer_panel = EqualizerPanel(
            equalizer_service=self._equalizer_service,
            show_title=False,
        )
        library_panel.tracks_add_requested.connect(playlist_panel.add_track_ids)
        library_panel.track_relocated.connect(lambda _track: playlist_panel.refresh())
        library_panel.track_metadata_changed.connect(
            lambda _track: playlist_panel.refresh()
        )
        library_panel.tracks_removed.connect(playlist_panel.refresh)
        player_panel.remove_current_requested.connect(playlist_panel.remove_current_track)
        player_panel.settings_requested.connect(self._open_settings)
        player_panel.favorite_changed.connect(lambda _track_id, _favorite: library_panel.refresh())
        player_panel.favorite_changed.connect(lambda _track_id, _favorite: playlist_panel.refresh())
        for panel in (player_panel, library_panel, playlist_panel, equalizer_panel):
            panel.status_message.connect(self.show_status_message)

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

    def show_status_message(self, message: str, timeout_ms: int = 4_000) -> None:
        """Show a concise transient result without interrupting the workflow."""
        self.statusBar().showMessage(message, timeout_ms)

    def _open_settings(self) -> None:
        if self._settings_service is None:
            self.show_status_message("Settings storage is unavailable.")
            return
        preferences = self._settings_service.load_player_preferences()
        dialog = SettingsDialog(
            preferences,
            self._playback_service.available_output_devices(),
            self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated = dialog.preferences()
        try:
            self._playback_service.set_output_device(updated.audio_device_id)
            self._playback_service.set_output_mode(
                AudioOutputMode(updated.audio_output_mode)
            )
        except ValueError as error:
            self.show_status_message(f"Could not select audio output: {error}")
            return
        self._playback_service.set_continue_after_track(
            updated.continue_after_track
        )
        self._settings_service.save_player_preferences(updated)
        self.visualizer_quality_changed.emit(updated.visualizer_quality)
        self.show_status_message("Settings saved and applied.")

    def _add_layout_reset_action(self) -> None:
        self._module_menu.addSeparator()
        action = QAction("Reset Layout", self)
        action.setObjectName("resetLayoutAction")
        action.setToolTip("Restore the default position and visibility of all modules")
        action.triggered.connect(self.layout_reset_requested.emit)
        self._module_menu.addAction(action)

    def _configure_shortcuts(self) -> None:
        shortcuts: tuple[tuple[QKeySequence, Callable[[], object]], ...] = (
            (QKeySequence(Qt.Key.Key_Space), self._playback_service.toggle_play_pause),
            (QKeySequence("Ctrl+."), self._playback_service.stop),
            (QKeySequence("Ctrl+Right"), self._playback_service.next_track),
            (QKeySequence("Ctrl+Left"), self._playback_service.previous_track),
            (QKeySequence("Ctrl+Up"), lambda: self._playback_service.adjust_volume(0.05)),
            (QKeySequence("Ctrl+Down"), lambda: self._playback_service.adjust_volume(-0.05)),
            (QKeySequence("M"), self._playback_service.toggle_mute),
            (QKeySequence("Ctrl+H"), self._playback_service.toggle_shuffle),
            (QKeySequence("Ctrl+R"), self._playback_service.cycle_repeat_mode),
            (QKeySequence(QKeySequence.StandardKey.Find), self._focus_library_search),
            (QKeySequence("Ctrl+1"), lambda: self._toggle_module("localLibraryModule")),
            (QKeySequence("Ctrl+2"), lambda: self._toggle_module("playlistModule")),
            (QKeySequence("Ctrl+3"), lambda: self._toggle_module("equalizerModule")),
        )
        for sequence, handler in shortcuts:
            shortcut = QShortcut(sequence, self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(handler)
            self._shortcuts.append(shortcut)

    def _focus_library_search(self) -> None:
        dock = self.module("localLibraryModule")
        if dock is not None:
            dock.show()
            dock.raise_()
        self._library_panel.focus_search()

    def _toggle_module(self, object_name: str) -> None:
        dock = self.module(object_name)
        if dock is not None:
            dock.setVisible(not dock.isVisible())

    def module(self, object_name: str) -> QDockWidget | None:
        """Return a registered module (used by plugins and tests)."""
        return self._module_docks.get(object_name)
