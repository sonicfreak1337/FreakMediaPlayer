from PySide6.QtWidgets import QApplication

from freak_media_player.player.audio_backend import NullAudioBackend
from freak_media_player.player.playback_controller import PlaybackController
from freak_media_player.player.queue import PlaybackQueue
from freak_media_player.providers.registry import ProviderRegistry
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
