from freak_media_player.models.media import Artist, ProviderIdentity, Track
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


def test_enqueue_and_play_replaces_current_track() -> None:
    controller = PlaybackController(
        queue=PlaybackQueue([make_track("old")]),
        audio_backend=NullAudioBackend(),
    )
    service = PlaybackService(controller=controller)

    state = service.enqueue_and_play(make_track("new"))

    assert state.status == PlaybackStatus.PLAYING
    assert state.current_track is not None
    assert state.current_track.id == "new"
