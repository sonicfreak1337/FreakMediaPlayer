import sqlite3
import time

from freak_media_player.database.migrations import MigrationRunner
from freak_media_player.database.repositories import (
    SQLitePlaylistRepository,
    SQLiteTrackRepository,
)
from freak_media_player.models.media import Album, Artist, ProviderIdentity, Track
from freak_media_player.services.playlist_service import PlaylistService
from freak_media_player.services.search_service import LibraryFilters, SearchService

TRACK_COUNT = 10_000
MAX_OPERATION_SECONDS = 5.0


def make_tracks() -> list[Track]:
    return [
        Track(
            id=f"track-{index:05d}",
            provider_identity=ProviderIdentity(
                provider_id="local-files", item_id=f"C:/Music/{index:05d}.mp3"
            ),
            title=f"Song {index:05d}",
            artist=Artist(name=f"Artist {index % 100:03d}"),
            album=Album(title=f"Album {index % 500:03d}", release_year=2000 + index % 25),
            genre=f"Genre {index % 10}",
        )
        for index in range(TRACK_COUNT)
    ]


def test_ten_thousand_track_import_search_rescan_and_playlist_order() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    MigrationRunner().run(connection)
    repository = SQLiteTrackRepository(connection)
    tracks = make_tracks()

    started = time.perf_counter()
    assert repository.save_many(tracks) == (TRACK_COUNT, 0)
    assert time.perf_counter() - started < MAX_OPERATION_SECONDS

    search = SearchService(())
    started = time.perf_counter()
    results = search.search_library(
        search.filter_library(tracks, LibraryFilters(genre="Genre 7")),
        "Artist 042",
    )
    assert time.perf_counter() - started < MAX_OPERATION_SECONDS
    assert results

    playlist_repository = SQLitePlaylistRepository(connection)
    playlist = PlaylistService(playlist_repository, repository)
    playlist.add_tracks(tracks)
    original_order = [track.id for track in playlist.list_tracks()]

    started = time.perf_counter()
    assert repository.save_many(tracks) == (0, TRACK_COUNT)
    assert time.perf_counter() - started < MAX_OPERATION_SECONDS
    assert [track.id for track in playlist.list_tracks()] == original_order

    moved = playlist.move_positions(range(100, 200), TRACK_COUNT)
    assert len(moved) == TRACK_COUNT
    assert [track.id for track in moved[-100:]] == original_order[100:200]
