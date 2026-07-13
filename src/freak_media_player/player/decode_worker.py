"""Background decode and DSP worker for the desktop audio pipeline."""

from __future__ import annotations

import queue
import threading

from freak_media_player.player.dsp.parametric_equalizer import (
    ParametricEqualizerProcessor,
)
from freak_media_player.player.pcm import float_samples_to_int16_bytes
from freak_media_player.player.pipeline_messages import (
    DecodeFailed,
    DecodeFinished,
    PcmChunk,
    PipelineMessage,
    StreamMetadataChanged,
)
from freak_media_player.player.streaming_decoder import (
    OUTPUT_SAMPLE_RATE,
    DecoderSource,
    PyAVStreamingDecoder,
)

WORKER_JOIN_TIMEOUT_SECONDS = 0.5
QUEUE_PUT_TIMEOUT_SECONDS = 0.2


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
        self._retired_threads: list[threading.Thread] = []
        self._stop_event = threading.Event()

    def start(self, generation: int, source: DecoderSource, position_ms: int) -> None:
        self.stop()
        self._reap_threads()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            args=(generation, source, position_ms, self._stop_event),
            daemon=True,
            name="freak-audio-decoder",
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=WORKER_JOIN_TIMEOUT_SECONDS)
            if thread.is_alive():
                self._retired_threads.append(thread)
        self._thread = None
        self._reap_threads()

    def live_thread_count(self) -> int:
        self._reap_threads()
        current = int(self._thread is not None and self._thread.is_alive())
        return current + len(self._retired_threads)

    def _reap_threads(self) -> None:
        self._retired_threads = [
            thread for thread in self._retired_threads if thread.is_alive()
        ]

    def _run(
        self,
        generation: int,
        source: DecoderSource,
        position_ms: int,
        stop_event: threading.Event,
    ) -> None:
        try:
            previous_title = ""
            for samples in self._decoder.decode(source, position_ms, stop_event):
                if stop_event.is_set():
                    return
                processed = self._equalizer.process(samples, OUTPUT_SAMPLE_RATE)
                payload = float_samples_to_int16_bytes(processed)
                if not self._enqueue(PcmChunk(generation, payload), stop_event):
                    return
                title_getter = getattr(self._decoder, "stream_title", None)
                title = title_getter() if callable(title_getter) else ""
                if title and title != previous_title:
                    if not self._enqueue(StreamMetadataChanged(generation, title), stop_event):
                        return
                    previous_title = title
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
                self._messages.put(message, timeout=QUEUE_PUT_TIMEOUT_SECONDS)
                return True
            except queue.Full:
                continue
        return False
