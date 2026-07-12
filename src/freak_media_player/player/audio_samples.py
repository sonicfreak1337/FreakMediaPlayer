"""Thread-safe rolling PCM sample buffer for visualizer plugins."""

from __future__ import annotations

import threading
from collections.abc import Callable

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
        *,
        capture_enabled: bool = True,
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
        self._capture_enabled = capture_enabled
        self._playback_active = False
        self._activity_listeners: list[Callable[[bool], None]] = []
        self._lock = threading.Lock()

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def sequence(self) -> int:
        """Monotonic count of complete PCM frames received."""
        with self._lock:
            return self._sequence

    @property
    def playback_active(self) -> bool:
        """Whether audio is currently expected to produce visualizer samples."""
        with self._lock:
            return self._playback_active

    def append_pcm16_stereo(self, payload: bytes) -> None:
        """Append little-endian stereo int16 PCM, preserving partial frames."""
        self.append_pcm16(payload, 2)

    def append_pcm16(self, payload: bytes, channels: int) -> None:
        """Append interleaved PCM and downmix all channels for visualization."""
        if not payload or not self._capture_enabled:
            return
        if channels <= 0:
            raise ValueError("channels must be positive")
        with self._lock:
            framed = self._remainder + payload
            frame_bytes = channels * 2
            complete_size = len(framed) - (len(framed) % frame_bytes)
            self._remainder = framed[complete_size:]
            if complete_size == 0:
                return
            interleaved = np.frombuffer(framed[:complete_size], dtype="<i2").reshape(
                -1, channels
            )
            mono = np.asarray(
                np.mean(interleaved, axis=1, dtype=np.float32), dtype=np.float32
            )
            mono /= INT16_SCALE
            self._append_mono(mono)
            self._sequence += int(mono.size)

    def set_capture_enabled(self, enabled: bool) -> None:
        """Enable sample capture only while at least one visualizer is visible."""
        with self._lock:
            self._capture_enabled = enabled
            if not enabled:
                self._samples.fill(0.0)
                self._write_position = 0
                self._available = 0
                self._remainder = b""

    def set_playback_active(self, active: bool) -> None:
        """Publish playback activity so visualizers can run without polling."""
        with self._lock:
            if active == self._playback_active:
                return
            self._playback_active = active
            listeners = tuple(self._activity_listeners)
        for listener in listeners:
            listener(active)

    def add_playback_activity_listener(
        self,
        listener: Callable[[bool], None],
    ) -> None:
        with self._lock:
            if listener not in self._activity_listeners:
                self._activity_listeners.append(listener)

    def remove_playback_activity_listener(
        self,
        listener: Callable[[bool], None],
    ) -> None:
        with self._lock:
            if listener in self._activity_listeners:
                self._activity_listeners.remove(listener)

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
