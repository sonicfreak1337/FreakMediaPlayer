"""Streaming local audio decoding through PyAV."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

import av
import numpy as np
from av.audio.frame import AudioFrame
from av.audio.stream import AudioStream
from av.container import InputContainer
from numpy.typing import NDArray

from freak_media_player.models.playback import StreamBufferProfile
from freak_media_player.player.channel_mixer import mix_channels
from freak_media_player.player.stream_resolver import NetworkStreamResolver

OUTPUT_SAMPLE_FORMAT = "fltp"
OUTPUT_SAMPLE_RATE = 48_000
DecoderSource: TypeAlias = str | Path
NETWORK_TIMEOUT_SECONDS = (5.0, 3.0)
NETWORK_BUFFER_BYTES = {
    StreamBufferProfile.SMALL: 64 * 1024,
    StreamBufferProfile.NORMAL: 256 * 1024,
    StreamBufferProfile.STABLE: 1024 * 1024,
}


@dataclass(frozen=True)
class AudioStreamInfo:
    duration_ms: int
    sample_rate: int = OUTPUT_SAMPLE_RATE
    channels: int = 2


class PyAVStreamingDecoder:
    def __init__(
        self,
        output_layout: str = "stereo",
        stream_resolver: NetworkStreamResolver | None = None,
    ) -> None:
        self._output_layout = output_layout
        self._stream_resolver = stream_resolver or NetworkStreamResolver()
        self._stream_title = ""
        self._buffer_profile = StreamBufferProfile.NORMAL

    def set_output_layout(self, output_layout: str) -> None:
        if output_layout not in {"mono", "stereo", "5.1", "7.1"}:
            raise ValueError(f"Unsupported output layout: {output_layout}")
        self._output_layout = output_layout

    def set_stream_buffer_profile(self, profile: StreamBufferProfile) -> None:
        self._buffer_profile = profile

    def probe(self, source: DecoderSource) -> AudioStreamInfo:
        with self._open(source) as container:
            stream = self._audio_stream(container)
            self._update_stream_title(container, stream)
            return AudioStreamInfo(duration_ms=self._duration_ms(container, stream))

    def decode(
        self,
        source: DecoderSource,
        start_ms: int,
        stop_event: threading.Event,
    ) -> Iterator[NDArray[np.float32]]:
        with self._open(source) as container:
            stream = self._audio_stream(container)
            if start_ms > 0:
                time_base = stream.time_base
                if time_base is None:
                    raise ValueError("Audio stream does not provide a time base.")
                target_timestamp = int((start_ms / 1000.0) / float(time_base))
                container.seek(target_timestamp, stream=stream, backward=True)

            resampler: av.AudioResampler | None = None
            for frame in container.decode(stream):
                if stop_event.is_set():
                    return
                self._update_stream_title(container, stream)
                if resampler is None:
                    resampler = av.AudioResampler(
                        format=OUTPUT_SAMPLE_FORMAT,
                        layout=frame.layout.name,
                        rate=OUTPUT_SAMPLE_RATE,
                    )
                for output_frame in resampler.resample(frame):
                    samples = self._frame_samples(output_frame, start_ms)
                    if samples.shape[1] > 0:
                        channels = tuple(
                            channel.name for channel in output_frame.layout.channels
                        )
                        yield mix_channels(samples, channels, self._output_layout)

            if resampler is None:
                return
            for output_frame in resampler.resample(None):
                if stop_event.is_set():
                    return
                samples = self._frame_samples(output_frame, start_ms)
                if samples.shape[1] > 0:
                    channels = tuple(
                        channel.name for channel in output_frame.layout.channels
                    )
                    yield mix_channels(samples, channels, self._output_layout)

    def _open(self, source: DecoderSource) -> InputContainer:
        value = str(source)
        if value.casefold().startswith(("http://", "https://")):
            resolved = self._stream_resolver.resolve(value)
            return av.open(
                resolved,
                timeout=NETWORK_TIMEOUT_SECONDS,
                options={
                    "buffer_size": str(NETWORK_BUFFER_BYTES[self._buffer_profile]),
                    "icy": "1",
                },
            )
        return av.open(value)

    def stream_title(self) -> str:
        return self._stream_title

    def _update_stream_title(self, container: InputContainer, stream: AudioStream) -> None:
        combined = dict(container.metadata)
        combined.update(stream.metadata)
        metadata = {str(key).casefold(): str(value) for key, value in combined.items()}
        self._stream_title = (
            metadata.get("streamtitle")
            or metadata.get("icy-title")
            or metadata.get("title")
            or ""
        ).strip()

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
