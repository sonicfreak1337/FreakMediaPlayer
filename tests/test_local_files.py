from pathlib import Path

from freak_media_player.database.migrations import MigrationRunner
from freak_media_player.database.repositories import (
    SQLiteSettingsRepository,
    SQLiteTrackRepository,
)
from freak_media_player.models.media import Artist, ProviderIdentity, Track
from freak_media_player.providers.base import SearchQuery
from freak_media_player.providers.local_files import LOCAL_FILE_PROVIDER_ID, LocalFileProvider
from freak_media_player.providers.local_metadata import (
    LocalMetadataReader,
    LocalTrackMetadata,
)
from freak_media_player.providers.registry import ProviderNotFoundError, ProviderRegistry
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.settings_service import SettingsService
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


def test_metadata_reader_normalizes_common_audio_tags() -> None:
    metadata = LocalMetadataReader().from_tags(
        {
            "TITLE": " The Song ",
            "ARTIST": "The Artist",
            "ALBUM": "The Album",
            "album artist": "Various Artists",
            "DATE": "2025-03-14",
            "GENRE": "Deathcore",
            "TRACKNUMBER": "07/12",
            "DISCNUMBER": "2/2",
        },
        duration_seconds=123.5,
    )

    assert metadata.title == "The Song"
    assert metadata.artist == "The Artist"
    assert metadata.album_title == "The Album"
    assert metadata.album_artist == "Various Artists"
    assert metadata.release_year == 2025
    assert metadata.genre == "Deathcore"
    assert metadata.track_number == 7
    assert metadata.disc_number == 2
    assert metadata.duration_seconds == 123.5


class StubMetadataReader(LocalMetadataReader):
    def read(self, _path: Path) -> LocalTrackMetadata:
        return LocalTrackMetadata(
            title="Tagged Song",
            artist="Tagged Artist",
            album_title="Tagged Album",
            album_artist="Album Artist",
            release_year=2026,
            genre="Metal",
            track_number=3,
            disc_number=1,
            duration_seconds=180.0,
        )


def test_local_file_provider_uses_embedded_metadata(tmp_path: Path) -> None:
    file_path = tmp_path / "fallback-name.flac"
    write_audio_file(file_path)
    provider = LocalFileProvider(metadata_reader=StubMetadataReader())

    track = provider.track_from_path(file_path)

    assert track.title == "Tagged Song"
    assert track.artist.name == "Tagged Artist"
    assert track.album is not None
    assert track.album.title == "Tagged Album"
    assert track.album.artist is not None
    assert track.album.artist.name == "Album Artist"
    assert track.album.release_year == 2026
    assert track.genre == "Metal"
    assert track.track_number == 3
    assert track.disc_number == 1


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
    file_path = tmp_path / "Song.mp3"
    write_audio_file(file_path)
    provider = LocalFileProvider()
    track = provider.track_from_path(file_path)
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


def test_local_library_service_imports_supported_paths_only(tmp_path: Path) -> None:
    audio_file = tmp_path / "One.mp3"
    text_file = tmp_path / "notes.txt"
    write_audio_file(audio_file)
    text_file.write_text("ignored", encoding="utf-8")
    repository = SQLiteTrackRepository(make_connection())
    service = LocalLibraryService(LocalFileProvider(), repository)

    tracks = service.import_paths([audio_file, text_file])

    assert len(tracks) == 1
    assert tracks[0].title == "One"


def test_local_library_service_removes_track(tmp_path: Path) -> None:
    audio_file = tmp_path / "One.mp3"
    write_audio_file(audio_file)
    repository = SQLiteTrackRepository(make_connection())
    service = LocalLibraryService(LocalFileProvider(), repository)
    track = service.import_file(audio_file)

    removed = service.remove_track(track.id)

    assert removed is True
    assert service.list_tracks() == []


def test_local_library_service_refreshes_existing_metadata(tmp_path: Path) -> None:
    audio_file = tmp_path / "old-title.mp3"
    write_audio_file(audio_file)
    repository = SQLiteTrackRepository(make_connection())
    original_provider = LocalFileProvider()
    original_track = original_provider.track_from_path(audio_file)
    repository.save(original_track)
    service = LocalLibraryService(
        LocalFileProvider(metadata_reader=StubMetadataReader()),
        repository,
    )

    refreshed_count = service.refresh_metadata()
    refreshed_track = repository.get_by_id(original_track.id)

    assert refreshed_count == 1
    assert refreshed_track is not None
    assert refreshed_track.title == "Tagged Song"
    assert refreshed_track.artist.name == "Tagged Artist"


def test_managed_music_folders_add_rescan_and_remove_source(tmp_path: Path) -> None:
    music = tmp_path / "Music"
    write_audio_file(music / "One.mp3")
    connection = make_connection()
    repository = SQLiteTrackRepository(connection)
    settings = SettingsService(SQLiteSettingsRepository(connection))
    service = LocalLibraryService(LocalFileProvider(), repository, settings)

    imported = service.add_music_folder(music)
    write_audio_file(music / "Two.flac")
    rescanned = service.rescan_music_folder(music)
    removed = service.remove_music_folder(music)

    assert [track.title for track in imported] == ["One"]
    assert [track.title for track in rescanned] == ["One", "Two"]
    assert service.list_music_folders() == []
    assert removed is True
    assert [track.title for track in service.list_tracks()] == ["One", "Two"]


def test_relocate_track_preserves_id_and_manually_stored_metadata(tmp_path: Path) -> None:
    old_path = tmp_path / "missing.mp3"
    new_path = tmp_path / "moved.mp3"
    write_audio_file(new_path)
    repository = SQLiteTrackRepository(make_connection())
    original = Track(
        id="stable-id",
        provider_identity=ProviderIdentity(
            provider_id=LOCAL_FILE_PROVIDER_ID, item_id=str(old_path)
        ),
        title="Manual Title",
        artist=Artist(name="Manual Artist"),
        genre="Manual Genre",
    )
    repository.save(original)
    service = LocalLibraryService(LocalFileProvider(), repository)

    relocated = service.relocate_track(original.id, new_path)

    assert relocated.id == original.id
    assert relocated.title == "Manual Title"
    assert relocated.artist.name == "Manual Artist"
    assert relocated.genre == "Manual Genre"
    assert Path(relocated.provider_identity.item_id) == new_path.resolve()


def test_update_track_metadata_validates_and_stores_database_override(
    tmp_path: Path,
) -> None:
    audio = tmp_path / "song.mp3"
    write_audio_file(audio)
    repository = SQLiteTrackRepository(make_connection())
    service = LocalLibraryService(LocalFileProvider(), repository)
    track = service.import_file(audio)

    updated = service.update_track_metadata(
        track.id,
        title="  Manual   Title ",
        artist=" Manual Artist ",
        album=" Manual Album ",
        release_year=2024,
        genre=" Doom ",
        track_number=4,
        disc_number=1,
    )

    assert updated.title == "Manual Title"
    assert updated.artist.name == "Manual Artist"
    assert updated.album is not None
    assert updated.album.title == "Manual Album"
    assert updated.album.release_year == 2024
    assert updated.genre == "Doom"
    assert updated.track_number == 4
    assert updated.disc_number == 1

    try:
        service.update_track_metadata(
            track.id,
            title="",
            artist="Artist",
            album=None,
            release_year=None,
            genre=None,
            track_number=None,
            disc_number=None,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected empty title to be rejected")
