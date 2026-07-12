from pathlib import Path

from freak_media_player.database.repositories import (
    SQLiteSettingsRepository,
    SQLiteTrackRepository,
)
from freak_media_player.providers.local_files import LocalFileProvider
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.maintenance_service import MaintenanceService
from freak_media_player.services.settings_service import SettingsService
from tests.test_database import make_connection
from tests.test_local_files import write_audio_file


def test_maintenance_rebuilds_metadata_and_resets_only_settings(
    tmp_path: Path,
) -> None:
    connection = make_connection()
    tracks = SQLiteTrackRepository(connection)
    connection_settings = SQLiteSettingsRepository(connection)
    settings = SettingsService(connection_settings)
    library = LocalLibraryService(LocalFileProvider(), tracks, settings)
    audio = tmp_path / "Artist - Song.mp3"
    write_audio_file(audio)
    imported = library.import_file(audio)
    settings.complete_first_start()
    maintenance = MaintenanceService(settings, library)

    assert maintenance.rebuild_library_index() == 1
    maintenance.reset_settings()

    assert tracks.get_by_id(imported.id) is not None
    assert connection_settings.get("onboarding.completed") is None
