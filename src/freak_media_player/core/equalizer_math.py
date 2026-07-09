"""Pure parametric equalizer coefficient and response calculations."""

from __future__ import annotations

import cmath
import math
from collections.abc import Iterable

from freak_media_player.models.equalizer import EqualizerBand, EqualizerPreset

MIN_MAGNITUDE = 1e-12

SecondOrderSection = tuple[float, float, float, float, float, float]


def peaking_section(
    band: EqualizerBand,
    sample_rate: int,
) -> SecondOrderSection:
    if not band.enabled or abs(band.gain_db) < 1e-9:
        return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

    nyquist_limit = sample_rate * 0.5 * 0.999
    frequency_hz = min(float(band.frequency_hz), nyquist_limit)
    amplitude = math.pow(10.0, band.gain_db / 40.0)
    omega = 2.0 * math.pi * frequency_hz / sample_rate
    alpha = math.sin(omega) / (2.0 * band.q)
    cosine = math.cos(omega)

    b0 = 1.0 + alpha * amplitude
    b1 = -2.0 * cosine
    b2 = 1.0 - alpha * amplitude
    a0 = 1.0 + alpha / amplitude
    a1 = -2.0 * cosine
    a2 = 1.0 - alpha / amplitude
    return (
        b0 / a0,
        b1 / a0,
        b2 / a0,
        1.0,
        a1 / a0,
        a2 / a0,
    )


def response_db(
    preset: EqualizerPreset,
    frequencies_hz: Iterable[float],
    sample_rate: int,
) -> tuple[float, ...]:
    sections = tuple(peaking_section(band, sample_rate) for band in preset.bands)
    return tuple(
        preset.preamp_db + _sections_response_db(sections, frequency, sample_rate)
        for frequency in frequencies_hz
    )


def _sections_response_db(
    sections: tuple[SecondOrderSection, ...],
    frequency_hz: float,
    sample_rate: int,
) -> float:
    omega = 2.0 * math.pi * frequency_hz / sample_rate
    z1 = cmath.exp(complex(0.0, -omega))
    z2 = z1 * z1
    magnitude = 1.0
    for b0, b1, b2, _a0, a1, a2 in sections:
        numerator = b0 + b1 * z1 + b2 * z2
        denominator = 1.0 + a1 * z1 + a2 * z2
        magnitude *= abs(numerator / denominator)
    return 20.0 * math.log10(max(MIN_MAGNITUDE, magnitude))
