import random

from freak_media_player.models.media import Artist, ProviderIdentity, Track
from freak_media_player.player.queue import PlaybackQueue
from freak_media_player.player.shuffle import ShuffleCycle


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


def test_queue_moves_backward_and_forward_in_playlist_order() -> None:
    queue = PlaybackQueue([make_track("1"), make_track("2"), make_track("3")])

    assert queue.select(1).id == "2"
    assert queue.next().id == "3"
    assert queue.previous().id == "2"


def test_replace_preserves_current_track_by_id() -> None:
    queue = PlaybackQueue([make_track("1"), make_track("2")])
    queue.select(1)

    queue.replace(
        [make_track("2"), make_track("1"), make_track("3")],
        current_track_id="2",
    )

    assert queue.current().id == "2"
    assert queue.next().id == "1"


def test_queue_exposes_selected_playlist_index() -> None:
    queue = PlaybackQueue([make_track("1"), make_track("2")])

    queue.select(1)

    assert queue.current_index() == 1


def test_shuffle_plays_every_track_once_before_new_cycle() -> None:
    queue = PlaybackQueue(
        [make_track(str(index)) for index in range(5)],
        shuffle_cycle=ShuffleCycle(random.Random(7)),
    )
    queue.select(0)
    queue.set_shuffle_enabled(True)

    first_cycle = [queue.current().id]
    first_cycle.extend(queue.next().id for _ in range(4))
    last_track = first_cycle[-1]
    second_cycle = [queue.next().id for _ in range(5)]

    assert len(set(first_cycle)) == 5
    assert len(set(second_cycle)) == 5
    assert second_cycle[0] != last_track


def test_disabling_shuffle_clears_cycle_and_restores_playlist_order() -> None:
    cycle = ShuffleCycle(random.Random(11))
    queue = PlaybackQueue(
        [make_track(str(index)) for index in range(4)],
        shuffle_cycle=cycle,
    )
    queue.select(1)
    queue.set_shuffle_enabled(True)
    queue.next()

    queue.set_shuffle_enabled(False)

    assert cycle.played_indices() == frozenset()
    assert cycle.remaining_indices() == frozenset()
    current_index = queue.current_index()
    assert current_index is not None
    expected_index = current_index + 1
    next_track = queue.next()
    if expected_index < queue.track_count():
        assert next_track is not None
        assert next_track.id == str(expected_index)
    else:
        assert next_track is None


def test_shuffle_previous_and_next_follow_playback_history() -> None:
    queue = PlaybackQueue(
        [make_track(str(index)) for index in range(4)],
        shuffle_cycle=ShuffleCycle(random.Random(3)),
    )
    queue.select(0)
    queue.set_shuffle_enabled(True)
    first = queue.next()
    second = queue.next()

    assert first is not None
    assert second is not None
    assert queue.previous() == first
    assert queue.next() == second
