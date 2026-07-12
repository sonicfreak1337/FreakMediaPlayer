import queue
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import numpy as np
from numpy.typing import NDArray

from freak_media_player.models.equalizer import EQUALIZER_PRESETS
from freak_media_player.player.decode_worker import AudioDecodeWorker
from freak_media_player.player.dsp.parametric_equalizer import (
    ParametricEqualizerProcessor,
)
from freak_media_player.player.pipeline_messages import PipelineMessage
from freak_media_player.player.streaming_decoder import PyAVStreamingDecoder


class CooperativeBlockingDecoder:
    def decode(
        self, _path: Path, _position_ms: int, stop_event: threading.Event
    ) -> Iterator[NDArray[np.float32]]:
        while not stop_event.wait(0.001):
            pass
        if False:
            yield np.empty((2, 0), dtype=np.float32)


def test_decoder_worker_stops_cleanly_under_repeated_restart_stress() -> None:
    messages: queue.Queue[PipelineMessage] = queue.Queue(maxsize=2)
    worker = AudioDecodeWorker(
        decoder=cast(PyAVStreamingDecoder, CooperativeBlockingDecoder()),
        equalizer=ParametricEqualizerProcessor(EQUALIZER_PRESETS[0]),
        messages=messages,
    )

    for generation in range(50):
        worker.start(generation, Path("stress.wav"), generation * 10)
        worker.stop()

    assert worker._thread is None
    assert not any(
        thread.name == "freak-audio-decoder" and thread.is_alive()
        for thread in threading.enumerate()
    )
