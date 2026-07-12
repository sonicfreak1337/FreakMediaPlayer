import sqlite3
from pathlib import Path

from freak_media_player.database.migrations import MigrationRunner
from freak_media_player.database.repositories import (
    SQLitePlaylistRepository,
    SQLiteSettingsRepository,
    SQLiteTrackRepository,
)
from freak_media_player.models.media import Artist, ProviderIdentity, Track
from freak_media_player.providers.local_files import LocalFileProvider
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.playlist_service import PlaylistService
from freak_media_player.services.settings_service import SettingsService


def make_service() -> tuple[PlaylistService, SQLiteTrackRepository]:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    MigrationRunner().run(connection)
    tracks = SQLiteTrackRepository(connection)
    service = PlaylistService(
        playlist_repository=SQLitePlaylistRepository(connection),
        track_repository=tracks,
    )
    return service, tracks


def make_track(track_id: str) -> Track:
    return Track(
        id=track_id,
        provider_identity=ProviderIdentity(provider_id="test", item_id=track_id),
        title=f"Track {track_id}",
        artist=Artist(name="Artist"),
    )


def test_playlist_adds_library_tracks_at_drop_position() -> None:
    service, repository = make_service()
    for track_id in ("1", "2", "3"):
        repository.save(make_track(track_id))
    service.add_track_ids(["1", "3"])

    tracks = service.add_track_ids(["2"], position=1)

    assert [track.id for track in tracks] == ["1", "2", "3"]


def test_playlist_moves_selected_tracks_as_a_group() -> None:
    service, repository = make_service()
    for track_id in ("1", "2", "3", "4"):
        repository.save(make_track(track_id))
    service.add_track_ids(["1", "2", "3", "4"])

    tracks = service.move_positions([1, 2], target=4)

    assert [track.id for track in tracks] == ["1", "4", "2", "3"]


def test_named_playlist_lifecycle_is_immediately_persistent() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    MigrationRunner().run(connection)
    tracks = SQLiteTrackRepository(connection)
    repository = SQLitePlaylistRepository(connection)
    settings = SettingsService(SQLiteSettingsRepository(connection))
    service = PlaylistService(repository, tracks, settings)
    track = make_track("1")
    tracks.save(track)
    service.add_track_ids([track.id])

    duplicate = service.duplicate_active_playlist("Road Trip")
    assert service.list_tracks() == [track]
    renamed = service.rename_active_playlist("Long Drive")
    created = service.create_playlist("Workout")
    service.add_track_ids([track.id])
    service.clear()
    fallback = service.delete_active_playlist()

    assert duplicate.name == "Road Trip"
    assert renamed.name == "Long Drive"
    assert created.name == "Workout"
    assert fallback.name in {"Long Drive", "Playlist"}
    assert settings.load_active_playlist_id("missing") == fallback.playlist_id

    restored = PlaylistService(repository, tracks, settings)
    assert restored.active_playlist_id() == fallback.playlist_id


def test_named_playlists_reject_empty_and_duplicate_names() -> None:
    service, _tracks = make_service()
    service.create_playlist("Workout")

    for invalid_name in ("   ", "workout"):
        try:
            service.create_playlist(invalid_name)
        except ValueError:
            pass
        else:
            raise AssertionError("Expected invalid playlist name to be rejected")


def test_m3u_import_resolves_relative_and_absolute_paths(tmp_path: Path) -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    MigrationRunner().run(connection)
    tracks = SQLiteTrackRepository(connection)
    library = LocalLibraryService(LocalFileProvider(), tracks)
    service = PlaylistService(
        SQLitePlaylistRepository(connection),
        tracks,
        local_library_service=library,
    )
    relative_track = tmp_path / "relative.mp3"
    absolute_track = tmp_path / "absolute.flac"
    relative_track.write_bytes(b"fixture")
    absolute_track.write_bytes(b"fixture")
    playlist_path = tmp_path / "Imported.m3u8"
    playlist_path.write_text(
        f"#EXTM3U\nrelative.mp3\n{absolute_track}\nmissing.mp3\n",
        encoding="utf-8",
    )

    result = service.import_m3u(playlist_path)

    assert result.playlist.name == "Imported"
    assert result.track_count == 2
    assert result.skipped_count == 1
    assert [track.title for track in service.list_tracks()] == [
        "relative",
        "absolute",
    ]
    assert len(library.list_tracks()) == 2


def test_m3u_export_supports_relative_and_absolute_paths(tmp_path: Path) -> None:
    service, repository = make_service()
    source = tmp_path / "Music" / "song.mp3"
    source.parent.mkdir()
    source.write_bytes(b"fixture")
    track = Track(
        id="song",
        provider_identity=ProviderIdentity(
            provider_id="local-files", item_id=str(source)
        ),
        title="Song",
        artist=Artist(name="Artist"),
    )
    repository.save(track)
    service.add_track_ids([track.id])

    relative_path = service.export_m3u(tmp_path / "relative.m3u8", relative=True)
    absolute_path = service.export_m3u(tmp_path / "absolute.m3u8", relative=False)

    assert relative_path.read_text(encoding="utf-8").splitlines() == [
        "#EXTM3U",
        str(Path("Music") / "song.mp3"),
    ]
    assert absolute_path.read_text(encoding="utf-8").splitlines() == [
        "#EXTM3U",
        str(source.resolve()),
    ]
