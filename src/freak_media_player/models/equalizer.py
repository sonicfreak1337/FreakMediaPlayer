"""Equalizer models and presets."""

from __future__ import annotations

from dataclasses import dataclass

EQUALIZER_FREQUENCIES_HZ = (31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000)
MIN_GAIN_DB = -12.0
MAX_GAIN_DB = 12.0


@dataclass(frozen=True)
class EqualizerBand:
    frequency_hz: int
    gain_db: float


@dataclass(frozen=True)
class EqualizerPreset:
    preset_id: str
    name: str
    bands: tuple[EqualizerBand, ...]


def make_preset(preset_id: str, name: str, gains_db: tuple[float, ...]) -> EqualizerPreset:
    if len(gains_db) != len(EQUALIZER_FREQUENCIES_HZ):
        raise ValueError("Equalizer preset must define one gain per frequency band.")
    return EqualizerPreset(
        preset_id=preset_id,
        name=name,
        bands=tuple(
            EqualizerBand(frequency_hz=frequency, gain_db=_clamp_gain(gain))
            for frequency, gain in zip(EQUALIZER_FREQUENCIES_HZ, gains_db, strict=True)
        ),
    )


def _clamp_gain(gain_db: float) -> float:
    return min(MAX_GAIN_DB, max(MIN_GAIN_DB, gain_db))


EQUALIZER_PRESETS = (
    make_preset(
        "flat",
        "Flat",
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    ),
    make_preset(
        "metal",
        "Metal",
        (1.5, 2.5, 1.5, -2.0, -1.5, 0.5, 1.5, 1.0, 2.0, 1.0),
    ),
    make_preset(
        "metalcore",
        "Metalcore",
        (2.0, 3.0, 1.0, -2.5, -2.0, 0.5, 2.5, 1.5, 1.0, 0.5),
    ),
)
