"""Deterministic, peak-stable channel mapping for supported speaker layouts."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

TARGET_CHANNELS = {
    "mono": ("FC",),
    "stereo": ("FL", "FR"),
    "5.1": ("FL", "FR", "FC", "LFE", "BL", "BR"),
    "7.1": ("FL", "FR", "FC", "LFE", "BL", "BR", "SL", "SR"),
}


def mix_channels(
    samples: NDArray[np.float32],
    source_channels: tuple[str, ...],
    target_layout: str,
) -> NDArray[np.float32]:
    """Map standard FFmpeg channel names with rows normalized against clipping."""
    targets = TARGET_CHANNELS[target_layout]
    if samples.shape[0] != len(source_channels):
        raise ValueError("Channel metadata does not match decoded samples.")
    if source_channels == targets:
        return samples

    matrix = np.zeros((len(targets), len(source_channels)), dtype=np.float32)
    source_index = {name: index for index, name in enumerate(source_channels)}

    if len(source_channels) == 1:
        destination = "FC" if "FC" in targets else targets[0]
        matrix[targets.index(destination), 0] = 1.0
        if targets == TARGET_CHANNELS["stereo"]:
            matrix[:, 0] = 1.0
        return matrix @ samples

    for target_index, name in enumerate(targets):
        if name in source_index:
            matrix[target_index, source_index[name]] = 1.0

    if target_layout == "mono":
        matrix[0].fill(0.0)
        _add(matrix[0], source_index, "FL", 0.5)
        _add(matrix[0], source_index, "FR", 0.5)
        _add(matrix[0], source_index, "FC", 0.707)
        for name in ("BL", "BR", "SL", "SR"):
            _add(matrix[0], source_index, name, 0.354)
        _add(matrix[0], source_index, "LFE", 0.25)
    elif target_layout == "stereo":
        left, right = matrix
        _add(left, source_index, "FC", 0.707)
        _add(right, source_index, "FC", 0.707)
        for name in ("BL", "SL"):
            _add(left, source_index, name, 0.5)
        for name in ("BR", "SR"):
            _add(right, source_index, name, 0.5)
        _add(left, source_index, "LFE", 0.25)
        _add(right, source_index, "LFE", 0.25)
    elif {"FL", "FR"}.issubset(source_index):
        left_index = source_index["FL"]
        right_index = source_index["FR"]
        if "FC" in targets and "FC" not in source_index:
            matrix[targets.index("FC"), (left_index, right_index)] = 0.5
        for channel, source in (
            ("BL", left_index),
            ("BR", right_index),
            ("SL", left_index),
            ("SR", right_index),
        ):
            if channel in targets and channel not in source_index:
                matrix[targets.index(channel), source] = 0.5

    for row in matrix:
        total = float(np.sum(np.abs(row)))
        if total > 1.0:
            row /= total
    return matrix @ samples


def _add(
    row: NDArray[np.float32], source_index: dict[str, int], name: str, gain: float
) -> None:
    index = source_index.get(name)
    if index is not None:
        row[index] += gain
