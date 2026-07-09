"""Streaming local audio decoding through PyAV."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import av
import numpy as np
from av.audio.frame import AudioFrame
from av.audio.stream import AudioStream
from av.container import InputContainer
from numpy.typing import NDArray

OUTPUT_CHANNELS = 2
OUTPUT_LAYOUT = "stereo"
OUTPUT_SAMPLE_FORMAT = "fltp"
OUTPUT_SAMPLE_RATE = 48_000


@dataclass(frozen=True)
class AudioStreamInfo:
    duration_ms: int
    sample_rate: int = OUTPUT_SAMPLE_RATE
    channels: int = OUTPUT_CHANNELS


class PyAVStreamingDecoder:
    def probe(self, path: Path) -> AudioStreamInfo:
        with av.open(str(path)) as container:
            stream = self._audio_stream(container)
            return AudioStreamInfo(duration_ms=self._duration_ms(container, stream))

    def decode(
        self,
        path: Path,
        start_ms: int,
        stop_event: threading.Event,
    ) -> Iterator[NDArray[np.float32]]:
        with av.open(str(path)) as container:
            stream = self._audio_stream(container)
            if start_ms > 0:
                time_base = stream.time_base
                if time_base is None:
                    raise ValueError("Audio stream does not provide a time base.")
                target_timestamp = int((start_ms / 1000.0) / float(time_base))
                container.seek(target_timestamp, stream=stream, backward=True)

            resampler = av.AudioResampler(
                format=OUTPUT_SAMPLE_FORMAT,
                layout=OUTPUT_LAYOUT,
                rate=OUTPUT_SAMPLE_RATE,
            )
            for frame in container.decode(stream):
                if stop_event.is_set():
                    return
                for output_frame in resampler.resample(frame):
                    samples = self._frame_samples(output_frame, start_ms)
                    if samples.shape[1] > 0:
                        yield samples

            for output_frame in resampler.resample(None):
                if stop_event.is_set():
                    return
                samples = self._frame_samples(output_frame, start_ms)
                if samples.shape[1] > 0:
                    yield samples

    def _audio_stream(self, container: InputContainer) -> AudioStream:
        if not container.streams.audio:
            raise ValueError("Audio file does not contain an audio stream.")
        return container.streams.audio[0]

    def _duration_ms(
        self,
        container: InputContainer,
        stream: AudioStream,
    ) -> int:
        if stream.duration is not None and stream.time_base is not None:
            return max(0, round(float(stream.duration * stream.time_base) * 1000))
        if container.duration is not None:
            duration_ms = float(container.duration) / float(av.time_base) * 1000.0
            return max(0, round(duration_ms))
        return 0

    def _frame_samples(
        self,
        frame: AudioFrame,
        start_ms: int,
    ) -> NDArray[np.float32]:
        samples = frame.to_ndarray().astype(np.float32, copy=False)
        if start_ms <= 0 or frame.pts is None or frame.time_base is None:
            return samples

        frame_start_seconds = float(frame.pts * frame.time_base)
        target_seconds = start_ms / 1000.0
        frame_end_seconds = frame_start_seconds + frame.samples / OUTPUT_SAMPLE_RATE
        if frame_end_seconds <= target_seconds:
            return samples[:, 0:0]
        trim_frames = max(
            0,
            round((target_seconds - frame_start_seconds) * OUTPUT_SAMPLE_RATE),
        )
        return samples[:, trim_frames:]
