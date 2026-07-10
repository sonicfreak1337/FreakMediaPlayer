import math
import threading
import time
import wave
from pathlib import Path
from typing import cast

import numpy as np
import pytest
from PySide6.QtCore import QIODevice
from PySide6.QtMultimedia import QAudioSink, QtAudio
from PySide6.QtWidgets import QApplication

from freak_media_player.models.media import AudioSource
from freak_media_player.models.playback import PlaybackStatus
from freak_media_player.player.audio_samples import AudioSampleBuffer
from freak_media_player.player.daw_audio_backend import DawAudioBackend
from freak_media_player.player.streaming_decoder import PyAVStreamingDecoder

SAMPLE_RATE = 48_000


class FakeOutputDevice:
    def __init__(self) -> None:
        self.payload = bytearray()

    def write(self, payload: bytes) -> int:
        self.payload.extend(payload)
        return len(payload)


class FakeAudioSink:
    def __init__(self) -> None:
        self.device = FakeOutputDevice()
        self.volume = 1.0

    def setVolume(self, volume: float) -> None:
        self.volume = volume

    def start(self) -> QIODevice:
        return cast(QIODevice, self.device)

    def reset(self) -> None:
        pass

    def suspend(self) -> None:
        pass

    def resume(self) -> None:
        pass

    def bytesFree(self) -> int:
        return 1_000_000

    def processedUSecs(self) -> int:
        return 0

    def state(self) -> QtAudio.State:
        return QtAudio.State.IdleState


def write_test_wave(path: Path, duration_seconds: float = 0.1) -> None:
    sample_count = round(SAMPLE_RATE * duration_seconds)
    timeline = np.arange(sample_count, dtype=np.float32) / SAMPLE_RATE
    signal = 0.2 * np.sin(2.0 * math.pi * 440.0 * timeline)
    pcm = (signal * 32767.0).astype("<i2")
    stereo = np.column_stack((pcm, pcm)).reshape(-1)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(stereo.tobytes())


def test_streaming_decoder_reads_real_audio_file(tmp_path: Path) -> None:
    path = tmp_path / "tone.wav"
    write_test_wave(path)
    decoder = PyAVStreamingDecoder()

    info = decoder.probe(path)
    chunks = list(decoder.decode(path, 0, threading.Event()))

    assert info.duration_ms == pytest.approx(100, abs=2)
    assert chunks
    assert chunks[0].shape[0] == 2


def test_daw_backend_streams_decoded_and_processed_pcm(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    path = tmp_path / "tone.wav"
    write_test_wave(path)
    fake_sink = FakeAudioSink()
    audio_samples = AudioSampleBuffer()
    backend = DawAudioBackend(
        sink_factory=lambda _format: cast(QAudioSink, fake_sink),
        audio_samples=audio_samples,
    )
    finished = False

    def mark_finished() -> None:
        nonlocal finished
        finished = True

    backend.set_finished_callback(mark_finished)
    backend.load(AudioSource(uri=path.as_uri()))
    backend.play()
    deadline = time.monotonic() + 2.0
    while not finished and time.monotonic() < deadline:
        app.processEvents()
        backend._pump_output()
        time.sleep(0.005)

    assert finished is True
    assert fake_sink.device.payload
    assert audio_samples.sequence > 0
    assert backend.status() == PlaybackStatus.STOPPED
