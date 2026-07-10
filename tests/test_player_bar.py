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

    player_bar._toggle_shuffle()
    app.processEvents()

    assert player_bar._shuffle_button.isChecked() is True
    assert player_bar._shuffle_button.text() == "Shuffle: ON"
    assert player_bar._shuffle_button.objectName() == "shuffleButton"
