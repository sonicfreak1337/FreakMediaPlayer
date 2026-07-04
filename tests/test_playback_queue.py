from freak_media_player.models.media import Artist, ProviderIdentity, Track
from freak_media_player.player.queue import PlaybackQueue


def make_track(track_id: str) -> Track:
    return Track(
        id=track_id,
        provider_identity=ProviderIdentity(provider_id="test", item_id=track_id),
        title=f"Track {track_id}",
        artist=Artist(name="Artist"),
    )


def test_queue_returns_tracks_in_order() -> None:
    queue = PlaybackQueue([make_track("1"), make_track("2")])

    assert queue.next().id == "1"
    assert queue.next().id == "2"
    assert queue.next() is None


def test_clear_resets_current_track() -> None:
    queue = PlaybackQueue([make_track("1")])

    assert queue.current() is not None
    queue.clear()

    assert queue.current() is None
    assert queue.pending_count() == 0
