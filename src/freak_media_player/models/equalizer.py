"""Parametric equalizer models and presets."""

from __future__ import annotations

from dataclasses import dataclass

EQUALIZER_FREQUENCIES_HZ = (31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000)
MIN_FREQUENCY_HZ = 20
MAX_FREQUENCY_HZ = 20_000
MIN_GAIN_DB = -12.0
MAX_GAIN_DB = 12.0
MIN_Q = 0.2
MAX_Q = 12.0
DEFAULT_Q = 1.0
MIN_PREAMP_DB = -18.0
MAX_PREAMP_DB = 6.0
EQUALIZER_REFERENCE_SAMPLE_RATE = 48_000


@dataclass(frozen=True)
class EqualizerBand:
    frequency_hz: int
    gain_db: float
    q: float = DEFAULT_Q
    enabled: bool = True


@dataclass(frozen=True)
class EqualizerPreset:
    preset_id: str
    name: str
    bands: tuple[EqualizerBand, ...]
    preamp_db: float = 0.0


def make_preset(
    preset_id: str,
    name: str,
    gains_db: tuple[float, ...],
    *,
    q_values: tuple[float, ...] | None = None,
    preamp_db: float = 0.0,
) -> EqualizerPreset:
    if len(gains_db) != len(EQUALIZER_FREQUENCIES_HZ):
        raise ValueError("Equalizer preset must define one gain per frequency band.")
    resolved_q_values = q_values or (DEFAULT_Q,) * len(EQUALIZER_FREQUENCIES_HZ)
    if len(resolved_q_values) != len(EQUALIZER_FREQUENCIES_HZ):
        raise ValueError("Equalizer preset must define one Q value per frequency band.")
    return EqualizerPreset(
        preset_id=preset_id,
        name=name,
        bands=tuple(
            EqualizerBand(
                frequency_hz=frequency,
                gain_db=clamp_gain(gain),
                q=clamp_q(q),
            )
            for frequency, gain, q in zip(
                EQUALIZER_FREQUENCIES_HZ,
                gains_db,
                resolved_q_values,
                strict=True,
            )
        ),
        preamp_db=clamp_preamp(preamp_db),
    )


def clamp_frequency(frequency_hz: int) -> int:
    return min(MAX_FREQUENCY_HZ, max(MIN_FREQUENCY_HZ, frequency_hz))


def clamp_gain(gain_db: float) -> float:
    return min(MAX_GAIN_DB, max(MIN_GAIN_DB, gain_db))


def clamp_q(q: float) -> float:
    return min(MAX_Q, max(MIN_Q, q))


def clamp_preamp(preamp_db: float) -> float:
    return min(MAX_PREAMP_DB, max(MIN_PREAMP_DB, preamp_db))


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
        preamp_db=-2.5,
    ),
    make_preset(
        "metalcore",
        "Metalcore",
        (2.0, 3.0, 1.0, -2.5, -2.0, 0.5, 2.5, 1.5, 1.0, 0.5),
        preamp_db=-3.0,
    ),
)
