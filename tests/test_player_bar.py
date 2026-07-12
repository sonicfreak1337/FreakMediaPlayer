from typing import cast

from PySide6.QtWidgets import QApplication

from freak_media_player.models.media import Artist, ProviderIdentity, Track
from freak_media_player.models.playback import PlaybackState, PlaybackStatus
from freak_media_player.player.audio_backend import NullAudioBackend
from freak_media_player.player.playback_controller import PlaybackController
from freak_media_player.player.queue import PlaybackQueue
from freak_media_player.providers.registry import ProviderRegistry
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.widgets.player_bar import PlayerBar


def test_shuffle_button_exposes_enabled_state() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    service = PlaybackService(
        PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=NullAudioBackend(),
            source_resolver=ProviderRegistry(),
        )
    )
    player_bar = PlayerBar(service)
    player_bar._refresh_timer.stop()

    assert player_bar._shuffle_button.isChecked() is False
    assert player_bar._shuffle_button.text() == "Shuffle: OFF"
    off_icon = player_bar._shuffle_button.icon().cacheKey()

    player_bar._toggle_shuffle()
    app.processEvents()

    assert player_bar._shuffle_button.isChecked() is True
    assert player_bar._shuffle_button.text() == "Shuffle: ON"
    assert player_bar._shuffle_button.objectName() == "shuffleButton"
    assert player_bar._shuffle_button.icon().cacheKey() != off_icon


def test_repeat_button_uses_distinct_assets_for_each_mode() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    service = PlaybackService(
        PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=NullAudioBackend(),
            source_resolver=ProviderRegistry(),
        )
    )
    player_bar = PlayerBar(service)
    player_bar._refresh_timer.stop()

    off_icon = player_bar._repeat_button.icon().cacheKey()
    player_bar._cycle_repeat_mode()
    all_icon = player_bar._repeat_button.icon().cacheKey()
    player_bar._cycle_repeat_mode()
    one_icon = player_bar._repeat_button.icon().cacheKey()

    assert len({off_icon, all_icon, one_icon}) == 3
    app.processEvents()


def test_mute_button_uses_a_distinct_muted_icon() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    service = PlaybackService(
        PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=NullAudioBackend(),
            source_resolver=ProviderRegistry(),
        )
    )
    player_bar = PlayerBar(service)
    player_bar._refresh_timer.stop()
    volume_icon = player_bar._volume_button.icon().cacheKey()

    player_bar._toggle_mute()
    app.processEvents()

    assert player_bar._volume_button.text() == "Muted"
    assert player_bar._volume_button.toolTip() == "Restore volume"
    assert player_bar._volume_button.icon().cacheKey() != volume_icon


def test_playback_error_shows_message_and_direct_actions() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    service = PlaybackService(
        PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=NullAudioBackend(),
            source_resolver=ProviderRegistry(),
        )
    )
    player_bar = PlayerBar(service)
    player_bar._refresh_timer.stop()
    service._controller._state = PlaybackState(
        status=PlaybackStatus.ERROR,
        error_message="The audio file is damaged or unsupported.",
    )
    messages: list[str] = []
    player_bar.status_message.connect(messages.append)

    player_bar.refresh()
    app.processEvents()

    assert player_bar._error_panel.isHidden() is False
    assert "damaged or unsupported" in player_bar._error_label.text()
    labels = {
        button.text()
        for button in player_bar._error_panel.findChildren(type(player_bar._play_pause_button))
    }
    assert labels == {"Retry", "Skip", "Remove"}
    assert messages == [
        "Playback error: The audio file is damaged or unsupported."
    ]


class FakeFavoriteService:
    def __init__(self) -> None:
        self.favorite_ids: set[str] = set()

    def is_favorite(self, track_id: str) -> bool:
        return track_id in self.favorite_ids

    def set_favorite(self, track_id: str, favorite: bool) -> None:
        if favorite:
            self.favorite_ids.add(track_id)
        else:
            self.favorite_ids.discard(track_id)


def test_favorite_button_toggles_current_track_immediately() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    service = PlaybackService(
        PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=NullAudioBackend(),
            source_resolver=ProviderRegistry(),
        )
    )
    favorites = FakeFavoriteService()
    player_bar = PlayerBar(service, cast(LocalLibraryService, favorites))
    player_bar._refresh_timer.stop()
    track = Track(
        id="favorite",
        provider_identity=ProviderIdentity(provider_id="test", item_id="favorite.mp3"),
        title="Favorite",
        artist=Artist(name="Artist"),
    )
    service.enqueue_and_play(track)
    player_bar.refresh()

    player_bar._favorite_button.click()
    app.processEvents()

    assert favorites.favorite_ids == {track.id}
    assert player_bar._favorite_button.isChecked() is True
    assert player_bar._favorite_button.toolTip() == (
        "Remove current track from favorites"
    )
