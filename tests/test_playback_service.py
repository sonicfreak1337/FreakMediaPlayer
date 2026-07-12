from freak_media_player.models.media import Artist, AudioSource, ProviderIdentity, Track
from freak_media_player.models.playback import AudioOutputMode, PlaybackStatus, RepeatMode
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


class MissingFileBackend(NullAudioBackend):
    def load(self, source: AudioSource) -> None:
        raise FileNotFoundError(source.uri)


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


def test_volume_control_notifies_persistence_with_bounded_backend_value() -> None:
    saved_volumes: list[float] = []
    controller = PlaybackController(
        queue=PlaybackQueue(),
        audio_backend=NullAudioBackend(),
        source_resolver=FakeSourceResolver(),
    )
    service = PlaybackService(controller, volume_changed=saved_volumes.append)

    service.set_volume(2.0)

    assert saved_volumes == [1.0]


def test_volume_shortcuts_adjust_and_restore_muted_volume() -> None:
    saved_volumes: list[float] = []
    service = PlaybackService(
        PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=NullAudioBackend(),
            source_resolver=FakeSourceResolver(),
        ),
        volume_changed=saved_volumes.append,
    )
    service.set_volume(0.4)

    service.adjust_volume(0.05)
    service.toggle_mute()
    assert service.volume() == 0.0
    service.toggle_mute()

    assert service.volume() == 0.45
    assert saved_volumes[-3:] == [0.45, 0.0, 0.45]


def test_playback_checkpoint_persists_track_and_timestamp() -> None:
    saved_sessions: list[tuple[str, int]] = []
    service = PlaybackService(
        PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=NullAudioBackend(),
            source_resolver=FakeSourceResolver(),
        ),
        session_changed=lambda track_id, position_ms: saved_sessions.append(
            (track_id, position_ms)
        ),
    )

    service.enqueue_and_play(make_track("remember-me"))
    service.seek(54_321)

    assert saved_sessions[-1] == ("remember-me", 54_321)


def test_controller_restores_track_paused_at_saved_timestamp() -> None:
    track = make_track("remember-me")
    controller = PlaybackController(
        queue=PlaybackQueue([make_track("first"), track]),
        audio_backend=NullAudioBackend(),
        source_resolver=FakeSourceResolver(),
    )

    state = controller.restore(track, 54_321)

    assert state.status == PlaybackStatus.PAUSED
    assert state.current_track == track
    assert controller.position_ms() == 54_321
    assert controller.current_playlist_index() == 1


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


def test_finished_track_can_stop_instead_of_continuing() -> None:
    backend = NullAudioBackend()
    service = PlaybackService(
        controller=PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=backend,
            source_resolver=FakeSourceResolver(),
        )
    )
    service.play_playlist([make_track("1"), make_track("2")], 0)
    service.set_continue_after_track(False)

    backend.finish()

    assert service.state.status == PlaybackStatus.STOPPED
    assert service.state.current_track is None


def test_audio_output_devices_can_be_selected() -> None:
    service = PlaybackService(
        PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=NullAudioBackend(),
            source_resolver=FakeSourceResolver(),
        )
    )

    assert service.available_output_devices()[0].device_id == "default"
    service.set_output_device("default")

    assert service.selected_output_device_id() == "default"

    service.set_output_mode(AudioOutputMode.SURROUND_5_1)

    assert service.output_mode() == AudioOutputMode.SURROUND_5_1


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


def test_playlist_sync_reloads_current_track_after_source_relocation() -> None:
    service = PlaybackService(
        controller=PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=NullAudioBackend(),
            source_resolver=FakeSourceResolver(),
        )
    )
    original = make_track("1")
    relocated = Track(
        id=original.id,
        provider_identity=ProviderIdentity(
            provider_id="test", item_id="relocated.mp3"
        ),
        title=original.title,
        artist=original.artist,
    )
    service.play_playlist([original], 0)

    state = service.sync_playlist([relocated])

    assert state.current_track == relocated
    assert service._controller._loaded_track_id is None


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


def test_repeat_one_restarts_finished_track() -> None:
    backend = NullAudioBackend()
    service = PlaybackService(
        controller=PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=backend,
            source_resolver=FakeSourceResolver(),
        )
    )
    service.play_playlist([make_track("1"), make_track("2")], 0)
    service.set_repeat_mode(RepeatMode.ONE)

    backend.finish()

    assert service.state.status == PlaybackStatus.PLAYING
    assert service.state.current_track.id == "1"


def test_repeat_all_wraps_at_end_of_playlist() -> None:
    backend = NullAudioBackend()
    service = PlaybackService(
        controller=PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=backend,
            source_resolver=FakeSourceResolver(),
        )
    )
    service.play_playlist([make_track("1"), make_track("2")], 1)
    service.set_repeat_mode(RepeatMode.ALL)

    backend.finish()

    assert service.state.status == PlaybackStatus.PLAYING
    assert service.state.current_track.id == "1"


def test_shuffle_mode_survives_stop_and_is_cleared_when_disabled() -> None:
    service = PlaybackService(
        controller=PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=NullAudioBackend(),
            source_resolver=FakeSourceResolver(),
        )
    )
    service.play_playlist([make_track("1"), make_track("2")], 0)

    assert service.toggle_shuffle().shuffle_enabled is True
    assert service.stop().shuffle_enabled is True
    assert service.toggle_shuffle().shuffle_enabled is False


def test_playback_modes_notify_persistence_immediately() -> None:
    saved_modes: list[tuple[RepeatMode, bool]] = []
    service = PlaybackService(
        controller=PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=NullAudioBackend(),
            source_resolver=FakeSourceResolver(),
        ),
        playback_modes_changed=lambda repeat, shuffle: saved_modes.append(
            (repeat, shuffle)
        ),
    )

    service.toggle_shuffle()
    service.set_repeat_mode(RepeatMode.ONE)

    assert saved_modes == [
        (RepeatMode.OFF, True),
        (RepeatMode.ONE, True),
    ]


def test_missing_file_becomes_actionable_playback_error() -> None:
    track = make_track("missing")
    service = PlaybackService(
        PlaybackController(
            queue=PlaybackQueue([track]),
            audio_backend=MissingFileBackend(),
            source_resolver=FakeSourceResolver(),
        )
    )

    state = service.play()

    assert state.status == PlaybackStatus.ERROR
    assert state.current_track == track
    assert state.error_message is not None
    assert "not found" in state.error_message


def test_retry_and_skip_are_available_after_load_error() -> None:
    first = make_track("missing")
    second = make_track("next")
    service = PlaybackService(
        PlaybackController(
            queue=PlaybackQueue([first, second]),
            audio_backend=MissingFileBackend(),
            source_resolver=FakeSourceResolver(),
        )
    )
    service.play()

    assert service.retry().status == PlaybackStatus.ERROR
    assert service.next_track().current_track == second


def test_missing_session_file_does_not_break_restore() -> None:
    track = make_track("missing")
    controller = PlaybackController(
        queue=PlaybackQueue([track]),
        audio_backend=MissingFileBackend(),
        source_resolver=FakeSourceResolver(),
    )

    state = controller.restore(track, 12_000)

    assert state.status == PlaybackStatus.ERROR
    assert state.current_track == track
