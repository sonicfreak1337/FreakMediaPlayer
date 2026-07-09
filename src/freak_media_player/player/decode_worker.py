"""Background decode and DSP worker for the desktop audio pipeline."""

from __future__ import annotations

import queue
import threading
from pathlib import Path

from freak_media_player.player.dsp.parametric_equalizer import (
    ParametricEqualizerProcessor,
)
from freak_media_player.player.pcm import float_samples_to_int16_bytes
from freak_media_player.player.pipeline_messages import (
    DecodeFailed,
    DecodeFinished,
    PcmChunk,
    PipelineMessage,
)
from freak_media_player.player.streaming_decoder import (
    OUTPUT_SAMPLE_RATE,
    PyAVStreamingDecoder,
)

WORKER_JOIN_TIMEOUT_SECONDS = 0.5


class AudioDecodeWorker:
    def __init__(
        self,
        decoder: PyAVStreamingDecoder,
        equalizer: ParametricEqualizerProcessor,
        messages: queue.Queue[PipelineMessage],
    ) -> None:
        self._decoder = decoder
        self._equalizer = equalizer
        self._messages = messages
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self, generation: int, path: Path, position_ms: int) -> None:
        self.stop()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            args=(generation, path, position_ms, self._stop_event),
            daemon=True,
            name="freak-audio-decoder",
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=WORKER_JOIN_TIMEOUT_SECONDS)
        self._thread = None

    def _run(
        self,
        generation: int,
        path: Path,
        position_ms: int,
        stop_event: threading.Event,
    ) -> None:
        try:
            for samples in self._decoder.decode(path, position_ms, stop_event):
                if stop_event.is_set():
                    return
                processed = self._equalizer.process(samples, OUTPUT_SAMPLE_RATE)
                payload = float_samples_to_int16_bytes(processed)
                if not self._enqueue(PcmChunk(generation, payload), stop_event):
                    return
            self._enqueue(DecodeFinished(generation), stop_event)
        except Exception as error:
            self._enqueue(DecodeFailed(generation, str(error)), stop_event)

    def _enqueue(
        self,
        message: PipelineMessage,
        stop_event: threading.Event,
    ) -> bool:
        while not stop_event.is_set():
            try:
                self._messages.put(message, timeout=0.05)
                return True
            except queue.Full:
                continue
        return False
