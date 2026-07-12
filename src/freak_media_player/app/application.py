"""Qt application bootstrap."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from freak_media_player.app.bootstrap import AppContext, build_app_context
from freak_media_player.config.paths import AppPathResolver
from freak_media_player.config.settings import AppSettings
from freak_media_player.plugins.base import PluginContext
from freak_media_player.plugins.manager import PluginManager
from freak_media_player.plugins.visualizer import VisualizerPlugin
from freak_media_player.services.settings_service import SettingsService
from freak_media_player.ui.main_window import MainWindow
from freak_media_player.ui.skins import SkinManager
from freak_media_player.utils.logging import configure_logging
from freak_media_player.widgets.first_start_dialog import SKIPPED, FirstStartDialog


def run_application() -> int:
    configure_logging(logs_dir=AppPathResolver().resolve().logs_dir)
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Freak Media Player")

    context = build_app_context()
    skin_manager = SkinManager(
        qt_app,
        context.app_paths.skins_dir,
        context.settings_service,
    )
    skin_manager.initialize(AppSettings(database_path=context.app_paths.database_path))
    _run_first_start(context)
    command_line_track_id = _import_command_line_files(context, sys.argv[1:])
    window = MainWindow(
        playback_service=context.playback_service,
        local_library_service=context.local_library_service,
        playlist_service=context.playlist_service,
        equalizer_service=context.equalizer_service,
        skin_manager=skin_manager,
        search_service=context.search_service,
        settings_service=context.settings_service,
        backup_service=context.backup_service,
        diagnostic_service=context.diagnostic_service,
        maintenance_service=context.maintenance_service,
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
    if command_line_track_id is not None:
        tracks = context.playlist_service.list_tracks()
        start_index = next(
            (
                index
                for index, track in enumerate(tracks)
                if track.id == command_line_track_id
            ),
            None,
        )
        if start_index is not None:
            context.playback_service.play_playlist(tracks, start_index)

    return qt_app.exec()


def _run_first_start(context: AppContext) -> None:
    settings = context.settings_service
    if settings.first_start_completed():
        return
    dialog = FirstStartDialog(context.playback_service.available_output_devices())
    result = dialog.exec()
    if result == QDialog.DialogCode.Rejected:
        return
    if result != SKIPPED:
        choices = dialog.choices()
        preferences = replace(
            settings.load_player_preferences(),
            restore_session=choices.restore_session,
            audio_device_id=choices.audio_device_id,
        )
        try:
            context.playback_service.set_output_device(choices.audio_device_id)
        except ValueError as error:
            QMessageBox.warning(dialog, "Audio output", str(error))
            preferences = replace(preferences, audio_device_id=None)
        settings.save_player_preferences(preferences)
        if choices.music_folder is not None:
            try:
                context.local_library_service.add_music_folder(choices.music_folder)
            except (OSError, ValueError) as error:
                QMessageBox.warning(dialog, "Music folder", str(error))
    settings.complete_first_start()


def _import_command_line_files(
    context: AppContext, arguments: list[str]
) -> str | None:
    paths = [Path(argument) for argument in arguments]
    supported = [
        path
        for path in paths
        if path.is_file()
        and path.suffix.casefold()
        in context.local_library_service.supported_extensions()
    ]
    if not supported:
        return None
    tracks = context.local_library_service.import_paths(supported)
    context.playlist_service.add_track_ids([track.id for track in tracks])
    return tracks[0].id if tracks else None


def _reset_window_layout(
    window: MainWindow,
    settings_service: SettingsService,
    default_layout: tuple[bytes, bytes],
) -> None:
    """Restore and immediately persist the startup layout snapshot."""
    window.restore_layout(*default_layout)
    settings_service.save_window_layout(*window.capture_layout())
