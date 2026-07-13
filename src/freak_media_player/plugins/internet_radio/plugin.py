"""Lazy lifecycle integration for the optional internet-radio module."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMenu

from freak_media_player.plugins.base import PluginContext, PluginManifest
from freak_media_player.plugins.internet_radio.directory import RadioBrowserDirectory
from freak_media_player.plugins.internet_radio.logo_cache import StationLogoCache
from freak_media_player.plugins.internet_radio.provider import PROVIDER_ID, InternetRadioProvider
from freak_media_player.plugins.internet_radio.storage import RadioStorage
from freak_media_player.plugins.internet_radio.widget import InternetRadioPanel


class InternetRadioPlugin:
    manifest = PluginManifest(
        plugin_id="freak.internet-radio",
        name="Internet Radio",
        version="1.0.0",
        description="Optional live-radio directory, favorites and playback module.",
    )

    def __init__(self) -> None:
        self._context: PluginContext | None = None
        self._provider = InternetRadioProvider()
        self._launcher: QAction | None = None
        self._menu: QMenu | None = None
        self._window: QMainWindow | None = None
        self._panel: InternetRadioPanel | None = None
        self._storage: RadioStorage | None = None

    def activate(self, context: PluginContext) -> None:
        if (
            context.main_window is None
            or context.provider_registry is None
            or context.playback_service is None
        ):
            return
        self._context = context
        context.provider_registry.register(self._provider)
        self._menu = self._module_menu(context.main_window)
        self._launcher = QAction("Internet Radio…", context.main_window)
        self._launcher.setShortcut("Ctrl+Shift+R")
        self._launcher.setToolTip("Open the optional Internet Radio module")
        self._launcher.triggered.connect(self._open_module)
        self._menu.addAction(self._launcher)

    def deactivate(self) -> None:
        if self._context is not None and self._context.playback_service is not None:
            track = self._context.playback_service.state.current_track
            if track is not None and track.provider_identity.provider_id == PROVIDER_ID:
                self._context.playback_service.stop()
        if self._panel is not None:
            self._panel.shutdown()
        if self._menu is not None and self._launcher is not None:
            self._menu.removeAction(self._launcher)
        if self._window is not None:
            self._window.close()
            self._window.deleteLater()
        if self._storage is not None:
            self._storage.close()
        if self._context is not None and self._context.provider_registry is not None:
            self._context.provider_registry.unregister(PROVIDER_ID)
        self._context = None
        self._launcher = None
        self._menu = None
        self._window = None
        self._panel = None
        self._storage = None

    def _open_module(self) -> None:
        if self._window is not None:
            self._window.show()
            self._window.raise_()
            self._window.activateWindow()
            return
        context = self._context
        if context is None or context.main_window is None or context.playback_service is None:
            return
        data_dir = context.plugin_data_dir or Path.cwd() / ".freak-plugins"
        self._storage = RadioStorage(data_dir / "internet-radio.sqlite3")
        self._window = QMainWindow(context.main_window, Qt.WindowType.Window)
        self._window.setObjectName("internetRadioWindow")
        self._window.setWindowTitle("Freak Internet Radio")
        self._window.setMinimumSize(760, 420)
        self._window.resize(1100, 680)
        self._panel = InternetRadioPanel(
            RadioBrowserDirectory(),
            self._provider,
            context.playback_service,
            self._storage,
            self._window,
            logo_cache=StationLogoCache(data_dir / "internet-radio-cache" / "logos"),
        )
        status = getattr(context.main_window, "show_status_message", None)
        if callable(status):
            self._panel.status_message.connect(status)
        self._window.setCentralWidget(self._panel)
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    @staticmethod
    def _module_menu(main_window: QMainWindow) -> QMenu:
        menu = getattr(main_window, "module_menu", None)
        return menu if isinstance(menu, QMenu) else main_window.menuBar().addMenu("&Module")
