"""Dependency wiring for the desktop application."""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace

from freak_media_player.config.paths import AppPathResolver, AppPaths
from freak_media_player.config.settings import AppSettings, PlayerPreferences
from freak_media_player.core.ports import AudioBackend
from freak_media_player.database.session import DatabaseSession, DatabaseSessionFactory
from freak_media_player.models.playback import AudioOutputMode
from freak_media_player.player.audio_backend import create_desktop_audio_backend
from freak_media_player.player.audio_samples import AudioSampleBuffer
from freak_media_player.player.playback_controller import PlaybackController
from freak_media_player.player.queue import PlaybackQueue
from freak_media_player.providers.local_files import LocalFileProvider
from freak_media_player.providers.registry import ProviderRegistry
from freak_media_player.services.backup_service import BackupService
from freak_media_player.services.diagnostic_service import DiagnosticService
from freak_media_player.services.equalizer_service import EqualizerService
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.maintenance_service import MaintenanceService
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.services.playlist_service import PlaylistService
from freak_media_player.services.search_service import SearchService
from freak_media_player.services.settings_service import SettingsService

LOCAL_METADATA_INDEX_KEY = "library.local_metadata_index_version"
LOCAL_METADATA_INDEX_VERSION = 1
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppContext:
    app_paths: AppPaths
    audio_samples: AudioSampleBuffer
    backup_service: BackupService
    database: DatabaseSession
    diagnostic_service: DiagnosticService
    equalizer_service: EqualizerService
    local_library_service: LocalLibraryService
    maintenance_service: MaintenanceService
    playback_service: PlaybackService
    playlist_service: PlaylistService
    provider_registry: ProviderRegistry
    search_service: SearchService
    settings_service: SettingsService


def build_app_context(audio_backend: AudioBackend | None = None) -> AppContext:
    app_paths = AppPathResolver().resolve()
    database = DatabaseSessionFactory(app_paths.database_path).create()
    settings_service = SettingsService(repository=database.settings)
    backup_service = BackupService(database.connection, app_paths.data_dir)
    settings_service.load(AppSettings(database_path=app_paths.database_path))
    player_preferences = settings_service.load_player_preferences()

    local_provider = LocalFileProvider()
    provider_registry = ProviderRegistry([local_provider])
    local_library_service = LocalLibraryService(
        provider=local_provider,
        track_repository=database.tracks,
        settings_service=settings_service,
    )
    maintenance_service = MaintenanceService(settings_service, local_library_service)
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
        settings_service=settings_service,
        local_library_service=local_library_service,
    )

    queue = PlaybackQueue(playlist_service.list_tracks())
    audio_samples = AudioSampleBuffer(capture_enabled=False)
    selected_audio_backend = audio_backend or create_desktop_audio_backend(audio_samples)
    player_preferences = _configure_audio_output(
        selected_audio_backend,
        player_preferences,
    )
    settings_service.save_player_preferences(player_preferences)
    selected_audio_backend.set_volume(settings_service.load_playback_volume())
    selected_audio_backend.set_equalizer_preset(
        settings_service.load_equalizer_preset(selected_audio_backend.equalizer_preset())
    )
    controller = PlaybackController(
        queue=queue,
        audio_backend=selected_audio_backend,
        source_resolver=provider_registry,
    )
    controller.set_continue_after_track(player_preferences.continue_after_track)
    repeat_mode, shuffle_enabled = settings_service.load_playback_modes()
    controller.set_repeat_mode(repeat_mode)
    controller.set_shuffle_enabled(shuffle_enabled)
    saved_session = (
        settings_service.load_playback_session()
        if player_preferences.restore_session
        else None
    )
    if saved_session is not None:
        track_id, position_ms = saved_session
        if (track := database.tracks.get_by_id(track_id)) is not None:
            controller.restore(track, position_ms)
    playback_service = PlaybackService(
        controller=controller,
        volume_changed=settings_service.save_playback_volume,
        session_changed=settings_service.save_playback_session,
        playback_modes_changed=settings_service.save_playback_modes,
    )
    diagnostic_service = DiagnosticService(
        app_paths, database.connection, playback_service
    )
    equalizer_service = EqualizerService(
        audio_backend=selected_audio_backend,
        preset_changed=settings_service.save_equalizer_preset,
    )
    search_service = SearchService(providers=provider_registry.providers())
    return AppContext(
        app_paths=app_paths,
        audio_samples=audio_samples,
        backup_service=backup_service,
        database=database,
        diagnostic_service=diagnostic_service,
        equalizer_service=equalizer_service,
        local_library_service=local_library_service,
        maintenance_service=maintenance_service,
        playback_service=playback_service,
        playlist_service=playlist_service,
        provider_registry=provider_registry,
        search_service=search_service,
        settings_service=settings_service,
    )


def _configure_audio_output(
    audio_backend: AudioBackend,
    preferences: PlayerPreferences,
) -> PlayerPreferences:
    """Restore a usable output without letting stale device settings abort startup."""
    try:
        audio_backend.set_output_device(preferences.audio_device_id)
    except ValueError as error:
        LOGGER.warning("Stored audio output is unavailable: %s", error)
        try:
            audio_backend.set_output_device(None)
        except ValueError as fallback_error:
            # Keep the application usable even when Windows currently exposes no
            # PCM-capable device. Playback can report the device error later.
            LOGGER.warning("Default audio output is unavailable: %s", fallback_error)

    requested_mode = AudioOutputMode(preferences.audio_output_mode)
    supported_modes = _selected_output_modes(audio_backend)
    candidates = dict.fromkeys(
        (
            requested_mode,
            AudioOutputMode.STEREO,
            AudioOutputMode.MONO,
            AudioOutputMode.SURROUND_5_1,
            AudioOutputMode.SURROUND_7_1,
        )
    )
    for candidate in candidates:
        if candidate not in supported_modes:
            continue
        try:
            audio_backend.set_output_mode(candidate)
        except ValueError as error:
            # Audio devices can disappear between enumeration and selection.
            LOGGER.warning("Audio mode %s became unavailable: %s", candidate, error)
            continue
        break

    return replace(
        preferences,
        audio_device_id=audio_backend.selected_output_device_id(),
        audio_output_mode=audio_backend.output_mode().value,
    )


def _selected_output_modes(audio_backend: AudioBackend) -> tuple[AudioOutputMode, ...]:
    devices = audio_backend.available_output_devices()
    if not devices:
        return ()
    selected_id = audio_backend.selected_output_device_id()
    selected = next(
        (device for device in devices if device.device_id == selected_id),
        None,
    )
    if selected is None:
        selected = next((device for device in devices if device.is_default), devices[0])
    return selected.supported_modes
