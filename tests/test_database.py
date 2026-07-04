import sqlite3
from datetime import timedelta

from freak_media_player.database.migrations import MigrationRunner
from freak_media_player.database.repositories import (
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
    track = Track(
        id="track-1",
        provider_identity=ProviderIdentity(provider_id="local", item_id="file-1"),
        title="Song",
        artist=artist,
        album=Album(title="Album", artist=artist),
        duration=timedelta(seconds=123),
    )

    repository.save(track)
    loaded = repository.get_by_id("track-1")

    assert loaded is not None
    assert loaded.title == "Song"
    assert loaded.artist.name == "Artist"
    assert loaded.album is not None
    assert loaded.album.title == "Album"
    assert loaded.duration == timedelta(seconds=123)
