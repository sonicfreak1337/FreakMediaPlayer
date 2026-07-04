"""UI-neutral equalizer use cases."""

from __future__ import annotations

from freak_media_player.core.ports import AudioBackend
from freak_media_player.models.equalizer import EQUALIZER_PRESETS, EqualizerPreset, make_preset

CUSTOM_PRESET_ID = "custom"
CUSTOM_PRESET_NAME = "Custom"


class EqualizerService:
    def __init__(self, audio_backend: AudioBackend) -> None:
        self._audio_backend = audio_backend
        self._presets = {preset.preset_id: preset for preset in EQUALIZER_PRESETS}

    def presets(self) -> tuple[EqualizerPreset, ...]:
        return EQUALIZER_PRESETS

    def current_preset(self) -> EqualizerPreset:
        return self._audio_backend.equalizer_preset()

    def select_preset(self, preset_id: str) -> EqualizerPreset:
        preset = self._presets[preset_id]
        self._audio_backend.set_equalizer_preset(preset)
        return preset

    def set_custom_gains(self, gains_db: tuple[float, ...]) -> EqualizerPreset:
        preset = make_preset(CUSTOM_PRESET_ID, CUSTOM_PRESET_NAME, gains_db)
        self._audio_backend.set_equalizer_preset(preset)
        return preset
