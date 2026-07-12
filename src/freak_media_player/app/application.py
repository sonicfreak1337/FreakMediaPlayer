"""Qt application bootstrap."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from freak_media_player.app.bootstrap import build_app_context
from freak_media_player.config.settings import AppSettings
from freak_media_player.plugins.base import PluginContext
from freak_media_player.plugins.manager import PluginManager
from freak_media_player.plugins.visualizer import VisualizerPlugin
from freak_media_player.services.settings_service import SettingsService
from freak_media_player.ui.main_window import MainWindow
from freak_media_player.ui.skins import SkinManager
from freak_media_player.utils.logging import configure_logging


def run_application() -> int:
    configure_logging()
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Freak Media Player")

    context = build_app_context()
    skin_manager = SkinManager(
        qt_app,
        context.app_paths.skins_dir,
        context.settings_service,
    )
    skin_manager.initialize(AppSettings(database_path=context.app_paths.database_path))
    window = MainWindow(
        playback_service=context.playback_service,
        local_library_service=context.local_library_service,
        playlist_service=context.playlist_service,
        equalizer_service=context.equalizer_service,
        skin_manager=skin_manager,
        search_service=context.search_service,
        settings_service=context.settings_service,
    )
    plugin_manager = PluginManager(
        PluginContext(
            application_name=qt_app.applicationName(),
            main_window=window,
            audio_samples=context.audio_samples,
            visualizer_quality=context.settings_service.load_player_preferences().visualizer_quality,
        )
    )
    plugin_manager.register(VisualizerPlugin())
    plugin_manager.activate_all()
    default_layout = window.capture_layout()
    window.layout_reset_requested.connect(
        lambda: _reset_window_layout(window, context.settings_service, default_layout)
    )
    preferences = context.settings_service.load_player_preferences()
    if (
        preferences.restore_layout
        and (saved_layout := context.settings_service.load_window_layout()) is not None
    ):
        window.restore_layout(*saved_layout)
    qt_app.aboutToQuit.connect(lambda: context.playback_service.checkpoint(force=True))
    qt_app.aboutToQuit.connect(
        lambda: context.settings_service.save_window_layout(*window.capture_layout())
    )
    qt_app.aboutToQuit.connect(plugin_manager.deactivate_all)
    window.show()

    return qt_app.exec()


def _reset_window_layout(
    window: MainWindow,
    settings_service: SettingsService,
    default_layout: tuple[bytes, bytes],
) -> None:
    """Restore and immediately persist the startup layout snapshot."""
    window.restore_layout(*default_layout)
    settings_service.save_window_layout(*window.capture_layout())
