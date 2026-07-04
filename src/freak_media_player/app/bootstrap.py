"""Dependency wiring for the desktop application."""

from __future__ import annotations

from dataclasses import dataclass

from freak_media_player.config.paths import AppPathResolver, AppPaths
from freak_media_player.config.settings import AppSettings
from freak_media_player.database.session import DatabaseSession, DatabaseSessionFactory
from freak_media_player.player.audio_backend import NullAudioBackend
from freak_media_player.player.playback_controller import PlaybackController
from freak_media_player.player.queue import PlaybackQueue
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.services.settings_service import SettingsService


@dataclass(frozen=True)
class AppContext:
    app_paths: AppPaths
    database: DatabaseSession
    playback_service: PlaybackService
    settings_service: SettingsService


def build_app_context() -> AppContext:
    app_paths = AppPathResolver().resolve()
    database = DatabaseSessionFactory(app_paths.database_path).create()
    settings_service = SettingsService(repository=database.settings)
    settings_service.load(AppSettings(database_path=app_paths.database_path))

    queue = PlaybackQueue()
    audio_backend = NullAudioBackend()
    controller = PlaybackController(queue=queue, audio_backend=audio_backend)
    playback_service = PlaybackService(controller=controller)
    return AppContext(
        app_paths=app_paths,
        database=database,
        playback_service=playback_service,
        settings_service=settings_service,
    )
