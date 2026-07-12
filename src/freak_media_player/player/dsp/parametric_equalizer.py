"""Stateful block-based parametric equalizer processor."""

from __future__ import annotations

import math
import threading
from typing import cast

import numpy as np
from numpy.typing import NDArray
from scipy.signal import sosfilt  # type: ignore[import-untyped]

from freak_media_player.core.equalizer_math import peaking_section
from freak_media_player.models.equalizer import EqualizerPreset


class ParametricEqualizerProcessor:
    def __init__(self, preset: EqualizerPreset) -> None:
        self._preset = preset
        self._preset_version = 0
        self._active_version = -1
        self._active_sample_rate = 0
        self._sections = np.empty((0, 6), dtype=np.float64)
        self._state: NDArray[np.float64] | None = None
        self._preamp = 1.0
        self._lock = threading.Lock()

    def set_preset(self, preset: EqualizerPreset) -> None:
        with self._lock:
            self._preset = preset
            self._preset_version += 1

    def preset(self) -> EqualizerPreset:
        with self._lock:
            return self._preset

    def reset(self) -> None:
        self._active_version = -1
        self._state = None

    def process(
        self,
        samples: NDArray[np.float32],
        sample_rate: int,
    ) -> NDArray[np.float32]:
        preset, version = self._preset_snapshot()
        channels = samples.shape[0]
        if self._must_rebuild(version, sample_rate, channels):
            self._rebuild(preset, version, sample_rate, channels)

        if not self._sections.size:
            if self._preamp == 1.0:
                return samples
            return np.multiply(samples, self._preamp, dtype=np.float32)

        working = samples.astype(np.float64, copy=False) * self._preamp
        filtered, state = sosfilt(
            self._sections,
            working,
            axis=1,
            zi=self._state,
        )
        self._state = state
        return cast(
            NDArray[np.float32],
            filtered.astype(np.float32, copy=False),
        )

    def _preset_snapshot(self) -> tuple[EqualizerPreset, int]:
        with self._lock:
            return self._preset, self._preset_version

    def _must_rebuild(self, version: int, sample_rate: int, channels: int) -> bool:
        return (
            self._active_version != version
            or self._active_sample_rate != sample_rate
            or self._state is None
            or self._state.shape[1] != channels
        )

    def _rebuild(
        self,
        preset: EqualizerPreset,
        version: int,
        sample_rate: int,
        channels: int,
    ) -> None:
        active_bands = tuple(
            band
            for band in preset.bands
            if band.enabled and not math.isclose(band.gain_db, 0.0, abs_tol=1e-9)
        )
        if active_bands:
            self._sections = np.asarray(
                [peaking_section(band, sample_rate) for band in active_bands],
                dtype=np.float64,
            )
        else:
            self._sections = np.empty((0, 6), dtype=np.float64)
        self._state = np.zeros(
            (len(active_bands), channels, 2),
            dtype=np.float64,
        )
        self._preamp = math.pow(10.0, preset.preamp_db / 20.0)
        self._active_version = version
        self._active_sample_rate = sample_rate
