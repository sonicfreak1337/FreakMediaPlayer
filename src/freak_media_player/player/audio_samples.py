"""Thread-safe rolling PCM sample buffer for visualizer plugins."""

from __future__ import annotations

import threading

import numpy as np
from numpy.typing import NDArray

DEFAULT_SAMPLE_RATE = 48_000
DEFAULT_CAPACITY = 16_384
PCM_FRAME_BYTES = 4
INT16_SCALE = 32_768.0


class AudioSampleBuffer:
    """Keeps the latest stereo output samples without blocking audio playback."""

    def __init__(
        self,
        capacity: int = DEFAULT_CAPACITY,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
    ) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._capacity = capacity
        self._sample_rate = sample_rate
        self._samples = np.zeros(capacity, dtype=np.float32)
        self._write_position = 0
        self._available = 0
        self._sequence = 0
        self._remainder = b""
        self._lock = threading.Lock()

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def sequence(self) -> int:
        """Monotonic count of complete PCM frames received."""
        with self._lock:
            return self._sequence

    def append_pcm16_stereo(self, payload: bytes) -> None:
        """Append little-endian stereo int16 PCM, preserving partial frames."""
        if not payload:
            return
        with self._lock:
            framed = self._remainder + payload
            complete_size = len(framed) - (len(framed) % PCM_FRAME_BYTES)
            self._remainder = framed[complete_size:]
            if complete_size == 0:
                return
            stereo = np.frombuffer(framed[:complete_size], dtype="<i2").reshape(-1, 2)
            mono = stereo.astype(np.float32).mean(axis=1) / INT16_SCALE
            self._append_mono(mono)
            self._sequence += int(mono.size)

    def snapshot(self, sample_count: int) -> NDArray[np.float32]:
        """Return the newest mono samples, left-padded with silence if needed."""
        if sample_count <= 0:
            return np.empty(0, dtype=np.float32)
        requested = min(sample_count, self._capacity)
        with self._lock:
            available = min(requested, self._available)
            result = np.zeros(requested, dtype=np.float32)
            if available == 0:
                return result
            start = (self._write_position - available) % self._capacity
            if start + available <= self._capacity:
                result[-available:] = self._samples[start : start + available]
            else:
                first = self._capacity - start
                result[-available : -available + first] = self._samples[start:]
                result[-available + first :] = self._samples[: available - first]
            return result

    def clear(self) -> None:
        with self._lock:
            self._samples.fill(0.0)
            self._write_position = 0
            self._available = 0
            self._remainder = b""

    def _append_mono(self, samples: NDArray[np.float32]) -> None:
        if samples.size >= self._capacity:
            samples = samples[-self._capacity :]
        count = int(samples.size)
        first = min(count, self._capacity - self._write_position)
        self._samples[self._write_position : self._write_position + first] = samples[:first]
        remaining = count - first
        if remaining:
            self._samples[:remaining] = samples[first:]
        self._write_position = (self._write_position + count) % self._capacity
        self._available = min(self._capacity, self._available + count)
