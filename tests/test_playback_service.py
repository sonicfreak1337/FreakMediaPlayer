from freak_media_player.models.media import Artist, AudioSource, ProviderIdentity, Track
from freak_media_player.models.playback import PlaybackStatus
from freak_media_player.player.audio_backend import NullAudioBackend
from freak_media_player.player.playback_controller import PlaybackController
from freak_media_player.player.queue import PlaybackQueue
from freak_media_player.services.playback_service import PlaybackService


def make_track(track_id: str) -> Track:
    return Track(
        id=track_id,
        provider_identity=ProviderIdentity(provider_id="test", item_id=track_id),
        title=f"Track {track_id}",
        artist=Artist(name="Artist"),
    )


class FakeSourceResolver:
    def resolve_audio_source(self, track: Track) -> AudioSource:
        return AudioSource(uri=f"file:///{track.id}.mp3")


def test_enqueue_and_play_replaces_current_track() -> None:
    controller = PlaybackController(
        queue=PlaybackQueue([make_track("old")]),
        audio_backend=NullAudioBackend(),
        source_resolver=FakeSourceResolver(),
    )
    service = PlaybackService(controller=controller)

    state = service.enqueue_and_play(make_track("new"))

    assert state.status == PlaybackStatus.PLAYING
    assert state.current_track is not None
    assert state.current_track.id == "new"


def test_seek_updates_playback_position() -> None:
    controller = PlaybackController(
        queue=PlaybackQueue([make_track("track")]),
        audio_backend=NullAudioBackend(),
        source_resolver=FakeSourceResolver(),
    )
    service = PlaybackService(controller=controller)

    service.play()
    service.seek(42_000)

    assert service.position_ms() == 42_000


def test_toggle_play_pause_keeps_current_position() -> None:
    controller = PlaybackController(
        queue=PlaybackQueue([make_track("track")]),
        audio_backend=NullAudioBackend(),
        source_resolver=FakeSourceResolver(),
    )
    service = PlaybackService(controller=controller)

    service.play()
    service.seek(42_000)
    paused_state = service.toggle_play_pause()
    playing_state = service.toggle_play_pause()

    assert paused_state.status == PlaybackStatus.PAUSED
    assert playing_state.status == PlaybackStatus.PLAYING
    assert service.position_ms() == 42_000


def test_seek_relative_clamps_to_zero() -> None:
    controller = PlaybackController(
        queue=PlaybackQueue([make_track("track")]),
        audio_backend=NullAudioBackend(),
        source_resolver=FakeSourceResolver(),
    )
    service = PlaybackService(controller=controller)

    service.play()
    service.seek(1_000)
    service.seek_relative(-10_000)

    assert service.position_ms() == 0


def test_volume_control_updates_backend() -> None:
    controller = PlaybackController(
        queue=PlaybackQueue([make_track("track")]),
        audio_backend=NullAudioBackend(),
        source_resolver=FakeSourceResolver(),
    )
    service = PlaybackService(controller=controller)

    service.set_volume(0.35)

    assert service.volume() == 0.35


def test_playlist_navigation_uses_selected_order() -> None:
    service = PlaybackService(
        controller=PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=NullAudioBackend(),
            source_resolver=FakeSourceResolver(),
        )
    )
    tracks = [make_track("1"), make_track("2"), make_track("3")]

    service.play_playlist(tracks, 1)
    next_state = service.next_track()
    previous_state = service.previous_track()

    assert next_state.current_track.id == "3"
    assert previous_state.current_track.id == "2"
    assert service.current_playlist_index() == 1


def test_finished_track_automatically_starts_next_playlist_track() -> None:
    backend = NullAudioBackend()
    service = PlaybackService(
        controller=PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=backend,
            source_resolver=FakeSourceResolver(),
        )
    )
    service.play_playlist([make_track("1"), make_track("2")], 0)

    backend.finish()

    assert service.state.status == PlaybackStatus.PLAYING
    assert service.state.current_track.id == "2"


def test_playlist_reorder_updates_the_next_track_without_interrupting_playback() -> None:
    service = PlaybackService(
        controller=PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=NullAudioBackend(),
            source_resolver=FakeSourceResolver(),
        )
    )
    first = make_track("1")
    second = make_track("2")
    third = make_track("3")
    service.play_playlist([first, second, third], 0)

    service.sync_playlist([first, third, second])
    state = service.next_track()

    assert state.current_track.id == "3"


def test_finished_last_playlist_track_stops_playback() -> None:
    backend = NullAudioBackend()
    service = PlaybackService(
        controller=PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=backend,
            source_resolver=FakeSourceResolver(),
        )
    )
    service.play_playlist([make_track("1")], 0)

    backend.finish()

    assert service.state.status == PlaybackStatus.STOPPED
    assert service.state.current_track is None
