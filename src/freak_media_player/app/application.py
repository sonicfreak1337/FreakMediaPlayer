"""Qt application bootstrap."""

from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from freak_media_player.app.bootstrap import build_app_context
from freak_media_player.plugins.base import PluginContext
from freak_media_player.plugins.manager import PluginManager
from freak_media_player.plugins.visualizer import VisualizerPlugin
from freak_media_player.ui.assets import asset_path
from freak_media_player.ui.main_window import MainWindow
from freak_media_player.ui.theme import apply_dark_theme
from freak_media_player.utils.logging import configure_logging


def run_application() -> int:
    configure_logging()
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Freak Media Player")
    qt_app.setWindowIcon(QIcon(str(asset_path("app_logo.png"))))
    apply_dark_theme(qt_app)

    context = build_app_context()
    window = MainWindow(
        playback_service=context.playback_service,
        local_library_service=context.local_library_service,
        playlist_service=context.playlist_service,
        equalizer_service=context.equalizer_service,
    )
    plugin_manager = PluginManager(
        PluginContext(
            application_name=qt_app.applicationName(),
            main_window=window,
            audio_samples=context.audio_samples,
        )
    )
    plugin_manager.register(VisualizerPlugin())
    plugin_manager.activate_all()
    qt_app.aboutToQuit.connect(lambda: context.playback_service.checkpoint(force=True))
    qt_app.aboutToQuit.connect(plugin_manager.deactivate_all)
    window.show()

    return qt_app.exec()
