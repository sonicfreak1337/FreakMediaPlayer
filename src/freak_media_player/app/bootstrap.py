"""Dependency wiring for the desktop application."""

from __future__ import annotations

from dataclasses import dataclass

from freak_media_player.config.paths import AppPathResolver, AppPaths
from freak_media_player.config.settings import AppSettings
from freak_media_player.core.ports import AudioBackend
from freak_media_player.database.session import DatabaseSession, DatabaseSessionFactory
from freak_media_player.player.audio_backend import create_desktop_audio_backend
from freak_media_player.player.playback_controller import PlaybackController
from freak_media_player.player.queue import PlaybackQueue
from freak_media_player.providers.local_files import LocalFileProvider
from freak_media_player.providers.registry import ProviderRegistry
from freak_media_player.services.equalizer_service import EqualizerService
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.services.playlist_service import PlaylistService
from freak_media_player.services.search_service import SearchService
from freak_media_player.services.settings_service import SettingsService

LOCAL_METADATA_INDEX_KEY = "library.local_metadata_index_version"
LOCAL_METADATA_INDEX_VERSION = 1


@dataclass(frozen=True)
class AppContext:
    app_paths: AppPaths
    database: DatabaseSession
    equalizer_service: EqualizerService
    local_library_service: LocalLibraryService
    playback_service: PlaybackService
    playlist_service: PlaylistService
    provider_registry: ProviderRegistry
    search_service: SearchService
    settings_service: SettingsService


def build_app_context(audio_backend: AudioBackend | None = None) -> AppContext:
    app_paths = AppPathResolver().resolve()
    database = DatabaseSessionFactory(app_paths.database_path).create()
    settings_service = SettingsService(repository=database.settings)
    settings_service.load(AppSettings(database_path=app_paths.database_path))

    local_provider = LocalFileProvider()
    provider_registry = ProviderRegistry([local_provider])
    local_library_service = LocalLibraryService(
        provider=local_provider,
        track_repository=database.tracks,
    )
    indexed_version = database.settings.get(LOCAL_METADATA_INDEX_KEY)
    if indexed_version != str(LOCAL_METADATA_INDEX_VERSION):
        local_library_service.refresh_metadata()
        database.settings.set(
            LOCAL_METADATA_INDEX_KEY,
            str(LOCAL_METADATA_INDEX_VERSION),
        )
    playlist_service = PlaylistService(
        playlist_repository=database.playlists,
        track_repository=database.tracks,
    )

    queue = PlaybackQueue(playlist_service.list_tracks())
    selected_audio_backend = audio_backend or create_desktop_audio_backend()
    controller = PlaybackController(
        queue=queue,
        audio_backend=selected_audio_backend,
        source_resolver=provider_registry,
    )
    playback_service = PlaybackService(controller=controller)
    equalizer_service = EqualizerService(audio_backend=selected_audio_backend)
    search_service = SearchService(providers=provider_registry.providers())
    return AppContext(
        app_paths=app_paths,
        database=database,
        equalizer_service=equalizer_service,
        local_library_service=local_library_service,
        playback_service=playback_service,
        playlist_service=playlist_service,
        provider_registry=provider_registry,
        search_service=search_service,
        settings_service=settings_service,
    )
