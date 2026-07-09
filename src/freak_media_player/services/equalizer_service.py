"""UI-neutral equalizer use cases."""

from __future__ import annotations

from dataclasses import replace

from freak_media_player.core.equalizer_math import response_db
from freak_media_player.core.ports import AudioBackend
from freak_media_player.models.equalizer import (
    EQUALIZER_PRESETS,
    EqualizerBand,
    EqualizerPreset,
    clamp_frequency,
    clamp_gain,
    clamp_preamp,
    clamp_q,
)

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
        current = self.current_preset()
        if len(gains_db) != len(current.bands):
            raise ValueError("Custom equalizer gains must match the band count.")
        bands = tuple(
            replace(band, gain_db=clamp_gain(gain_db))
            for band, gain_db in zip(current.bands, gains_db, strict=True)
        )
        preset = self._custom_preset(bands, current.preamp_db)
        self._audio_backend.set_equalizer_preset(preset)
        return preset

    def update_band(
        self,
        index: int,
        *,
        frequency_hz: int,
        gain_db: float,
        q: float,
        enabled: bool,
    ) -> EqualizerPreset:
        current = self.current_preset()
        bands = list(current.bands)
        bands[index] = EqualizerBand(
            frequency_hz=clamp_frequency(frequency_hz),
            gain_db=clamp_gain(gain_db),
            q=clamp_q(q),
            enabled=enabled,
        )
        preset = self._custom_preset(tuple(bands), current.preamp_db)
        self._audio_backend.set_equalizer_preset(preset)
        return preset

    def set_preamp(self, preamp_db: float) -> EqualizerPreset:
        current = self.current_preset()
        preset = self._custom_preset(current.bands, clamp_preamp(preamp_db))
        self._audio_backend.set_equalizer_preset(preset)
        return preset

    def frequency_response_db(
        self,
        frequencies_hz: tuple[float, ...],
        sample_rate: int,
    ) -> tuple[float, ...]:
        return response_db(self.current_preset(), frequencies_hz, sample_rate)

    def _custom_preset(
        self,
        bands: tuple[EqualizerBand, ...],
        preamp_db: float,
    ) -> EqualizerPreset:
        return EqualizerPreset(
            preset_id=CUSTOM_PRESET_ID,
            name=CUSTOM_PRESET_NAME,
            bands=bands,
            preamp_db=preamp_db,
        )
