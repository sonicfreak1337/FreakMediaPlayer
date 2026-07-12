"""Streaming decoder, DSP and native Qt audio output backend."""

from __future__ import annotations

import queue
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QIODevice, QObject, QTimer, QUrl
from PySide6.QtMultimedia import (
    QAudioFormat,
    QAudioSink,
    QMediaDevices,
    QtAudio,
)

from freak_media_player.models.equalizer import EQUALIZER_PRESETS, EqualizerPreset
from freak_media_player.models.media import AudioSource
from freak_media_player.models.playback import PlaybackStatus
from freak_media_player.player.audio_samples import AudioSampleBuffer
from freak_media_player.player.decode_worker import AudioDecodeWorker
from freak_media_player.player.dsp.parametric_equalizer import (
    ParametricEqualizerProcessor,
)
from freak_media_player.player.pipeline_messages import (
    DecodeFailed,
    DecodeFinished,
    PcmChunk,
    PipelineMessage,
)
from freak_media_player.player.streaming_decoder import (
    OUTPUT_CHANNELS,
    OUTPUT_SAMPLE_RATE,
    PyAVStreamingDecoder,
)

MIN_VOLUME = 0.0
MAX_VOLUME = 1.0
OUTPUT_PUMP_INTERVAL_MS = 10
DECODE_QUEUE_CAPACITY = 16

SinkFactory = Callable[[QAudioFormat], QAudioSink]


class DawAudioBackend(QObject):
    def __init__(
        self,
        decoder: PyAVStreamingDecoder | None = None,
        sink_factory: SinkFactory | None = None,
        audio_samples: AudioSampleBuffer | None = None,
    ) -> None:
        super().__init__()
        self._decoder = decoder or PyAVStreamingDecoder()
        self._sink_factory = sink_factory or self._default_sink_factory
        self._audio_samples = audio_samples
        self._equalizer = ParametricEqualizerProcessor(EQUALIZER_PRESETS[0])
        self._messages: queue.Queue[PipelineMessage] = queue.Queue(
            maxsize=DECODE_QUEUE_CAPACITY
        )
        self._decode_worker = AudioDecodeWorker(
            decoder=self._decoder,
            equalizer=self._equalizer,
            messages=self._messages,
        )
        self._generation = 0
        self._source_path: Path | None = None
        self._sink: QAudioSink | None = None
        self._output_device: QIODevice | None = None
        self._pending_audio = b""
        self._decode_finished = False
        self._finished_callback: Callable[[], None] | None = None
        self._status = PlaybackStatus.STOPPED
        self._duration_ms = 0
        self._base_position_ms = 0
        self._volume = 1.0
        self._pump_timer = QTimer(self)
        self._pump_timer.setInterval(OUTPUT_PUMP_INTERVAL_MS)
        self._pump_timer.timeout.connect(self._pump_output)

    def load(self, source: AudioSource) -> None:
        path = self._path_from_source(source)
        stream_info = self._decoder.probe(path)
        self._source_path = path
        self._duration_ms = stream_info.duration_ms
        self._status = PlaybackStatus.PAUSED
        self._set_sample_playback_active(False)
        self._prepare_pipeline(0)

    def play(self) -> None:
        if self._source_path is None:
            return
        if self._sink is None:
            self._restart_pipeline(self._base_position_ms, start_output=True)
        elif self._output_device is None and self._sink is not None:
            self._output_device = self._sink.start()
        elif (
            self._sink is not None
            and self._sink.state() == QtAudio.State.SuspendedState
        ):
            self._sink.resume()
        self._status = PlaybackStatus.PLAYING
        self._set_sample_playback_active(True)
        self._pump_timer.start()
        self._pump_output()

    def pause(self) -> None:
        if self._sink is not None and self._status == PlaybackStatus.PLAYING:
            self._sink.suspend()
            self._status = PlaybackStatus.PAUSED
            self._set_sample_playback_active(False)
            self._pump_timer.stop()

    def stop(self) -> None:
        self._status = PlaybackStatus.STOPPED
        self._base_position_ms = 0
        self._set_sample_playback_active(False)
        self._pump_timer.stop()
        self._stop_worker()
        self._reset_output()
        self._clear_messages()
        if self._audio_samples is not None:
            self._audio_samples.clear()

    def seek(self, position_ms: int) -> None:
        if self._source_path is None:
            return
        target_ms = min(self._duration_ms, max(0, position_ms))
        was_playing = self._status == PlaybackStatus.PLAYING
        self._status = PlaybackStatus.PAUSED
        if was_playing:
            self._restart_pipeline(target_ms, start_output=True)
            self._status = PlaybackStatus.PLAYING
            self._pump_timer.start()
        else:
            self._prepare_pipeline(target_ms)

    def position_ms(self) -> int:
        processed_ms = 0
        if self._sink is not None and self._output_device is not None:
            processed_ms = self._sink.processedUSecs() // 1000
        position_ms = self._base_position_ms + processed_ms
        if self._duration_ms > 0:
            return min(self._duration_ms, position_ms)
        return max(0, position_ms)

    def duration_ms(self) -> int:
        return self._duration_ms

    def set_volume(self, volume: float) -> None:
        self._volume = min(MAX_VOLUME, max(MIN_VOLUME, volume))
        if self._sink is not None:
            self._sink.setVolume(self._volume)

    def volume(self) -> float:
        return self._volume

    def set_equalizer_preset(self, preset: EqualizerPreset) -> None:
        self._equalizer.set_preset(preset)

    def equalizer_preset(self) -> EqualizerPreset:
        return self._equalizer.preset()

    def status(self) -> PlaybackStatus:
        return self._status

    def set_finished_callback(self, callback: Callable[[], None]) -> None:
        self._finished_callback = callback

    def _restart_pipeline(self, position_ms: int, start_output: bool) -> None:
        self._prepare_pipeline(position_ms)
        self._create_sink()
        self._start_worker(position_ms)
        if start_output and self._sink is not None:
            self._output_device = self._sink.start()

    def _prepare_pipeline(self, position_ms: int) -> None:
        self._stop_worker()
        self._reset_output()
        self._clear_messages()
        self._equalizer.reset()
        self._base_position_ms = position_ms
        self._pending_audio = b""
        self._decode_finished = False
        if self._audio_samples is not None:
            self._audio_samples.clear()

    def _start_worker(self, position_ms: int) -> None:
        if self._source_path is None:
            return
        self._generation += 1
        self._decode_worker.start(
            generation=self._generation,
            path=self._source_path,
            position_ms=position_ms,
        )

    def _pump_output(self) -> None:
        if (
            self._status != PlaybackStatus.PLAYING
            or self._sink is None
            or self._output_device is None
        ):
            return

        bytes_free = self._sink.bytesFree()
        while bytes_free > 0:
            if not self._pending_audio and not self._load_next_message():
                break
            if not self._pending_audio:
                continue
            outgoing = self._pending_audio[:bytes_free]
            written = self._output_device.write(outgoing)
            if written <= 0:
                break
            if self._audio_samples is not None:
                self._audio_samples.append_pcm16_stereo(outgoing[:written])
            self._pending_audio = self._pending_audio[written:]
            bytes_free -= written

        if (
            self._decode_finished
            and not self._pending_audio
            and self._messages.empty()
            and self._sink.state() == QtAudio.State.IdleState
        ):
            self._finish_playback()

    def _load_next_message(self) -> bool:
        try:
            message = self._messages.get_nowait()
        except queue.Empty:
            return False
        if message.generation != self._generation:
            return True
        if isinstance(message, PcmChunk):
            self._pending_audio = message.payload
        elif isinstance(message, DecodeFinished):
            self._decode_finished = True
        elif isinstance(message, DecodeFailed):
            self._status = PlaybackStatus.ERROR
            self._set_sample_playback_active(False)
            self._reset_output()
        return True

    def _finish_playback(self) -> None:
        self._status = PlaybackStatus.STOPPED
        self._base_position_ms = self._duration_ms
        self._set_sample_playback_active(False)
        self._pump_timer.stop()
        self._reset_output()
        if self._audio_samples is not None:
            self._audio_samples.clear()
        if self._finished_callback is not None:
            self._finished_callback()

    def _create_sink(self) -> None:
        audio_format = QAudioFormat()
        audio_format.setSampleRate(OUTPUT_SAMPLE_RATE)
        audio_format.setChannelCount(OUTPUT_CHANNELS)
        audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        self._sink = self._sink_factory(audio_format)
        self._sink.setVolume(self._volume)

    def _default_sink_factory(self, audio_format: QAudioFormat) -> QAudioSink:
        output = QMediaDevices.defaultAudioOutput()
        if not output.isFormatSupported(audio_format):
            raise RuntimeError("Default audio device does not support 48 kHz stereo PCM.")
        return QAudioSink(output, audio_format, self)

    def _stop_worker(self) -> None:
        self._decode_worker.stop()

    def _set_sample_playback_active(self, active: bool) -> None:
        if self._audio_samples is not None:
            self._audio_samples.set_playback_active(active)

    def _reset_output(self) -> None:
        self._pump_timer.stop()
        if self._sink is not None:
            self._sink.reset()
        self._sink = None
        self._output_device = None

    def _clear_messages(self) -> None:
        while True:
            try:
                self._messages.get_nowait()
            except queue.Empty:
                return

    def _path_from_source(self, source: AudioSource) -> Path:
        url = QUrl(source.uri)
        if not url.isLocalFile():
            raise ValueError("DAW audio backend currently supports local files only.")
        path = Path(url.toLocalFile())
        if not path.exists():
            raise FileNotFoundError(path)
        return path
