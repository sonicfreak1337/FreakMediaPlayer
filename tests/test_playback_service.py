from freak_media_player.models.media import AudioSource, Artist, ProviderIdentity, Track
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
