"""Visualizer plugin lifecycle and dock integration."""

from __future__ import annotations

from typing import cast

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QDockWidget, QMainWindow, QMenu

from freak_media_player.plugins.base import PluginContext, PluginManifest
from freak_media_player.plugins.visualizer.widget import VisualizerPanel


class VisualizerPlugin:
    manifest = PluginManifest(
        plugin_id="freak.visualizer",
        name="Freak Visualizer",
        version="1.0.0",
        description="Audio-reactive Winamp-inspired visualizer presets.",
    )

    def __init__(self) -> None:
        self._dock: QDockWidget | None = None
        self._view_menu: QMenu | None = None
        self._toggle_action: QAction | None = None

    def activate(self, context: PluginContext) -> None:
        if context.main_window is None or context.audio_samples is None:
            return
        dock = QDockWidget("Freak Visualizer", context.main_window)
        dock.setObjectName("freakVisualizerDock")
        dock.setAllowedAreas(
            Qt.DockWidgetArea.TopDockWidgetArea | Qt.DockWidgetArea.BottomDockWidgetArea
        )
        dock.setMinimumHeight(220)
        dock.setWidget(VisualizerPanel(context.audio_samples, dock))
        context.main_window.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)

        view_menu = self._find_or_create_view_menu(context.main_window)
        toggle_action = dock.toggleViewAction()
        toggle_action.setText("Visualizer")
        toggle_action.setShortcut("Ctrl+Shift+V")
        view_menu.addAction(toggle_action)

        self._dock = dock
        self._view_menu = view_menu
        self._toggle_action = toggle_action

    def deactivate(self) -> None:
        if self._view_menu is not None and self._toggle_action is not None:
            self._view_menu.removeAction(self._toggle_action)
        if self._dock is not None:
            self._dock.close()
            self._dock.deleteLater()
        self._dock = None
        self._view_menu = None
        self._toggle_action = None

    @staticmethod
    def _find_or_create_view_menu(main_window: QMainWindow) -> QMenu:
        menu_bar = main_window.menuBar()
        for action in menu_bar.actions():
            if action.text().replace("&", "") == "Ansicht" and action.menu() is not None:
                return cast(QMenu, action.menu())
        return menu_bar.addMenu("&Ansicht")
