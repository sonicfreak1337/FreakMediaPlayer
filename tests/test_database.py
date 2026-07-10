import sqlite3
from datetime import timedelta

from freak_media_player.database.migrations import MigrationRunner
from freak_media_player.database.repositories import (
    SQLitePlaylistRepository,
    SQLiteSettingsRepository,
    SQLiteTrackRepository,
)
from freak_media_player.models.media import Album, Artist, ProviderIdentity, Track


def make_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    MigrationRunner().run(connection)
    return connection


def test_migrations_create_core_tables() -> None:
    connection = make_connection()

    table_names = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }

    assert "settings" in table_names
    assert "tracks" in table_names
    assert "playlists" in table_names
    assert "queue_items" in table_names
    assert "play_history" in table_names


def test_settings_repository_round_trips_values() -> None:
    repository = SQLiteSettingsRepository(make_connection())

    repository.set("theme", "dark")

    assert repository.get("theme") == "dark"
    assert repository.get("missing") is None


def test_track_repository_round_trips_track() -> None:
    repository = SQLiteTrackRepository(make_connection())
    artist = Artist(name="Artist")
    album_artist = Artist(name="Album Artist")
    track = Track(
        id="track-1",
        provider_identity=ProviderIdentity(provider_id="local", item_id="file-1"),
        title="Song",
        artist=artist,
        album=Album(
            title="Album",
            artist=album_artist,
            release_year=2024,
        ),
        duration=timedelta(seconds=123),
        genre="Metalcore",
        track_number=4,
        disc_number=2,
    )

    repository.save(track)
    loaded = repository.get_by_id("track-1")

    assert loaded is not None
    assert loaded.title == "Song"
    assert loaded.artist.name == "Artist"
    assert loaded.album is not None
    assert loaded.album.title == "Album"
    assert loaded.album.artist == album_artist
    assert loaded.album.release_year == 2024
    assert loaded.duration == timedelta(seconds=123)
    assert loaded.genre == "Metalcore"
    assert loaded.track_number == 4
    assert loaded.disc_number == 2


def test_track_repository_lists_tracks() -> None:
    repository = SQLiteTrackRepository(make_connection())
    artist = Artist(name="Artist")
    repository.save(
        Track(
            id="track-2",
            provider_identity=ProviderIdentity(provider_id="local", item_id="file-2"),
            title="Beta",
            artist=artist,
        )
    )
    repository.save(
        Track(
            id="track-1",
            provider_identity=ProviderIdentity(provider_id="local", item_id="file-1"),
            title="Alpha",
            artist=artist,
        )
    )

    tracks = repository.list_all()

    assert [track.title for track in tracks] == ["Alpha", "Beta"]


def test_track_repository_deletes_track() -> None:
    repository = SQLiteTrackRepository(make_connection())
    repository.save(
        Track(
            id="track-1",
            provider_identity=ProviderIdentity(provider_id="local", item_id="file-1"),
            title="Song",
            artist=Artist(name="Artist"),
        )
    )

    deleted = repository.delete("track-1")

    assert deleted is True
    assert repository.get_by_id("track-1") is None
    assert repository.delete("track-1") is False


def test_playlist_repository_preserves_track_order() -> None:
    connection = make_connection()
    tracks = SQLiteTrackRepository(connection)
    playlists = SQLitePlaylistRepository(connection)
    first = Track(
        id="track-1",
        provider_identity=ProviderIdentity(provider_id="local", item_id="file-1"),
        title="First",
        artist=Artist(name="Artist"),
    )
    second = Track(
        id="track-2",
        provider_identity=ProviderIdentity(provider_id="local", item_id="file-2"),
        title="Second",
        artist=Artist(name="Artist"),
    )
    tracks.save(first)
    tracks.save(second)
    playlists.ensure("active", "Playlist")

    playlists.replace_tracks("active", [second, first])

    assert [track.id for track in playlists.list_tracks("active")] == [
        "track-2",
        "track-1",
    ]
