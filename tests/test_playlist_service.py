import sqlite3

from freak_media_player.database.migrations import MigrationRunner
from freak_media_player.database.repositories import (
    SQLitePlaylistRepository,
    SQLiteTrackRepository,
)
from freak_media_player.models.media import Artist, ProviderIdentity, Track
from freak_media_player.services.playlist_service import PlaylistService


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
