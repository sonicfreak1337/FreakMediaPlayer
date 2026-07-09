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
        self._sections = np.empty((0, 6), dtype=np.float64)
        self._state: NDArray[np.float64] | None = None
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
        if self._must_rebuild(version, channels):
            self._rebuild(preset, version, sample_rate, channels)

        preamp = math.pow(10.0, preset.preamp_db / 20.0)
        working = samples.astype(np.float64, copy=False) * preamp
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

    def _must_rebuild(self, version: int, channels: int) -> bool:
        return (
            self._active_version != version
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
        self._sections = np.asarray(
            [peaking_section(band, sample_rate) for band in preset.bands],
            dtype=np.float64,
        )
        self._state = np.zeros(
            (len(preset.bands), channels, 2),
            dtype=np.float64,
        )
        self._active_version = version
