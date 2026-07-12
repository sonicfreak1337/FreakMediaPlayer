from PySide6.QtWidgets import QApplication

from freak_media_player.models.equalizer import EQUALIZER_PRESETS
from freak_media_player.player.audio_backend import NullAudioBackend
from freak_media_player.services.equalizer_service import EqualizerService
from freak_media_player.widgets.equalizer_panel import EqualizerPanel


def test_panel_initialization_preserves_restored_equalizer_preset() -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    backend = NullAudioBackend()
    restored = next(
        preset for preset in EQUALIZER_PRESETS if preset.preset_id == "metalcore"
    )
    backend.set_equalizer_preset(restored)
    persisted_changes = []
    service = EqualizerService(
        audio_backend=backend,
        preset_changed=persisted_changes.append,
    )

    panel = EqualizerPanel(equalizer_service=service)

    assert service.current_preset() == restored
    assert panel._preset_combo.currentData() == "metalcore"
    assert persisted_changes == []


def test_equalizer_change_emits_saved_status() -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    service = EqualizerService(audio_backend=NullAudioBackend())
    panel = EqualizerPanel(equalizer_service=service)
    messages: list[str] = []
    panel.status_message.connect(messages.append)

    panel._gain.setValue(2.5)

    assert messages[-1] == "Equalizer changes saved."
