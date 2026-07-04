from pathlib import Path

from freak_media_player.database.migrations import MigrationRunner
from freak_media_player.database.repositories import SQLiteTrackRepository
from freak_media_player.providers.base import SearchQuery
from freak_media_player.providers.local_files import LOCAL_FILE_PROVIDER_ID, LocalFileProvider
from freak_media_player.providers.registry import ProviderNotFoundError, ProviderRegistry
from freak_media_player.services.local_library_service import LocalLibraryService
from tests.test_database import make_connection


def write_audio_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"not real audio, only a provider test fixture")


def test_local_file_provider_creates_track_from_path(tmp_path: Path) -> None:
    file_path = tmp_path / "Song.mp3"
    write_audio_file(file_path)
    provider = LocalFileProvider()

    track = provider.track_from_path(file_path)

    assert track.title == "Song"
    assert track.provider_identity.provider_id == LOCAL_FILE_PROVIDER_ID
    assert Path(track.provider_identity.item_id) == file_path.resolve()


def test_local_file_provider_searches_library_roots(tmp_path: Path) -> None:
    write_audio_file(tmp_path / "First Song.mp3")
    write_audio_file(tmp_path / "Other.wav")
    provider = LocalFileProvider([tmp_path])

    results = provider.search_tracks(SearchQuery(text="first"))

    assert len(results) == 1
    assert results[0].title == "First Song"


def test_provider_registry_resolves_audio_source(tmp_path: Path) -> None:
    file_path = tmp_path / "Song.mp3"
    write_audio_file(file_path)
    provider = LocalFileProvider()
    registry = ProviderRegistry([provider])
    track = provider.track_from_path(file_path)

    source = registry.resolve_audio_source(track)

    assert source.uri == file_path.resolve().as_uri()


def test_provider_registry_rejects_unknown_provider(tmp_path: Path) -> None:
    provider = LocalFileProvider()
    track = provider.track_from_path(tmp_path / "Song.mp3")
    registry = ProviderRegistry()

    try:
        registry.resolve_audio_source(track)
    except ProviderNotFoundError:
        assert True
    else:
        raise AssertionError("Expected ProviderNotFoundError")


def test_local_library_service_imports_folder(tmp_path: Path) -> None:
    write_audio_file(tmp_path / "One.mp3")
    write_audio_file(tmp_path / "Two.flac")
    connection = make_connection()
    MigrationRunner().run(connection)
    repository = SQLiteTrackRepository(connection)
    service = LocalLibraryService(LocalFileProvider(), repository)

    tracks = service.import_folder(tmp_path)

    assert [track.title for track in tracks] == ["One", "Two"]
    assert repository.get_by_id(tracks[0].id) is not None
