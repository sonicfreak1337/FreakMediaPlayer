"""PCM output conversion helpers."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

INT16_SCALE = 32_767.0


def float_samples_to_int16_bytes(samples: NDArray[np.float32]) -> bytes:
    interleaved = np.array(samples.T, dtype=np.float32, order="C", copy=True)
    np.clip(interleaved, -1.0, 1.0, out=interleaved)
    np.multiply(interleaved, INT16_SCALE, out=interleaved)
    return interleaved.astype("<i2").tobytes()
