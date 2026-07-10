"""Visualizer plugin lifecycle and dock integration."""

from __future__ import annotations

from collections.abc import Callable
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
        version="1.2.0",
        description="Audio-reactive Winamp-inspired visualizer presets.",
    )

    def __init__(self) -> None:
        self._dock: QDockWidget | None = None
        self._view_menu: QMenu | None = None
        self._toggle_action: QAction | None = None
        self._main_window: QMainWindow | None = None

    def activate(self, context: PluginContext) -> None:
        if context.main_window is None or context.audio_samples is None:
            return
        panel = VisualizerPanel(context.audio_samples, context.main_window)
        add_module = getattr(context.main_window, "add_module", None)
        if callable(add_module):
            register = cast(Callable[..., QDockWidget], add_module)
            dock = register(
                "Visualizer",
                panel,
                "freakVisualizerDock",
                area=Qt.DockWidgetArea.BottomDockWidgetArea,
            )
        else:
            dock = QDockWidget("Visualizer", context.main_window)
            dock.setObjectName("freakVisualizerDock")
            dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
            dock.setWidget(panel)
            context.main_window.addDockWidget(
                Qt.DockWidgetArea.BottomDockWidgetArea, dock
            )
        dock.setMinimumHeight(220)
        stack_module = getattr(context.main_window, "stack_module_below", None)
        if callable(stack_module):
            stack_module("equalizerModule", dock, 205)

        view_menu = self._find_or_create_module_menu(context.main_window)
        toggle_action = dock.toggleViewAction()
        toggle_action.setText("Visualizer")
        toggle_action.setShortcut("Ctrl+Shift+V")
        if toggle_action not in view_menu.actions():
            view_menu.addAction(toggle_action)

        self._dock = dock
        self._view_menu = view_menu
        self._toggle_action = toggle_action
        self._main_window = context.main_window

    def deactivate(self) -> None:
        if self._view_menu is not None and self._toggle_action is not None:
            self._view_menu.removeAction(self._toggle_action)
        if self._dock is not None:
            remove_module = getattr(self._main_window, "remove_module", None)
            if callable(remove_module):
                remove_module(self._dock.objectName())
            self._dock.close()
            self._dock.deleteLater()
        self._dock = None
        self._view_menu = None
        self._toggle_action = None
        self._main_window = None

    @staticmethod
    def _find_or_create_module_menu(main_window: QMainWindow) -> QMenu:
        module_menu = getattr(main_window, "module_menu", None)
        if isinstance(module_menu, QMenu):
            return module_menu
        menu_bar = main_window.menuBar()
        for action in menu_bar.actions():
            if action.text().replace("&", "") == "Module" and action.menu() is not None:
                return cast(QMenu, action.menu())
        return menu_bar.addMenu("&Module")
