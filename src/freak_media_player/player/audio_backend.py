"""Audio backend implementations."""

from __future__ import annotations

import logging
from collections.abc import Callable

from freak_media_player.core.ports import AudioBackend
from freak_media_player.models.equalizer import EQUALIZER_PRESETS, EqualizerPreset
from freak_media_player.models.media import AudioSource
from freak_media_player.models.playback import (
    AudioOutputDevice,
    AudioOutputMode,
    PlaybackStatus,
)
from freak_media_player.player.audio_samples import AudioSampleBuffer

DEFAULT_VOLUME = 1.0
MIN_VOLUME = 0.0
MAX_VOLUME = 1.0
LOGGER = logging.getLogger(__name__)


class NullAudioBackend:
    """Backend used before a real audio engine is selected."""

    def __init__(self) -> None:
        self._status = PlaybackStatus.STOPPED
        self._source: AudioSource | None = None
        self._position_ms = 0
        self._duration_ms = 0
        self._volume = DEFAULT_VOLUME
        self._equalizer_preset = EQUALIZER_PRESETS[0]
        self._finished_callback: Callable[[], None] | None = None
        self._output_device_id: str | None = None
        self._output_mode = AudioOutputMode.STEREO

    def load(self, source: AudioSource) -> None:
        self._source = source
        self._status = PlaybackStatus.PAUSED

    def play(self) -> None:
        if self._source is not None:
            self._status = PlaybackStatus.PLAYING

    def pause(self) -> None:
        if self._source is not None:
            self._status = PlaybackStatus.PAUSED

    def stop(self) -> None:
        self._position_ms = 0
        self._status = PlaybackStatus.STOPPED

    def seek(self, position_ms: int) -> None:
        self._position_ms = max(0, position_ms)

    def position_ms(self) -> int:
        return self._position_ms

    def duration_ms(self) -> int:
        return self._duration_ms

    def set_volume(self, volume: float) -> None:
        self._volume = min(MAX_VOLUME, max(MIN_VOLUME, volume))

    def volume(self) -> float:
        return self._volume

    def set_equalizer_preset(self, preset: EqualizerPreset) -> None:
        self._equalizer_preset = preset

    def equalizer_preset(self) -> EqualizerPreset:
        return self._equalizer_preset

    def status(self) -> PlaybackStatus:
        return self._status

    def error_message(self) -> str | None:
        return None

    def available_output_devices(self) -> list[AudioOutputDevice]:
        return [
            AudioOutputDevice(
                "default", "Default audio output", True, tuple(AudioOutputMode)
            )
        ]

    def selected_output_device_id(self) -> str | None:
        return self._output_device_id

    def set_output_device(self, device_id: str | None) -> None:
        if device_id not in {None, "default"}:
            raise ValueError(f"Unknown audio output device: {device_id}")
        self._output_device_id = device_id

    def output_mode(self) -> AudioOutputMode:
        return self._output_mode

    def set_output_mode(self, mode: AudioOutputMode) -> None:
        self._output_mode = mode

    def set_finished_callback(self, callback: Callable[[], None]) -> None:
        self._finished_callback = callback

    def finish(self) -> None:
        self._status = PlaybackStatus.STOPPED
        if self._finished_callback is not None:
            self._finished_callback()


def create_desktop_audio_backend(
    audio_samples: AudioSampleBuffer | None = None,
) -> AudioBackend:
    try:
        from freak_media_player.player.daw_audio_backend import DawAudioBackend
    except ImportError:
        LOGGER.exception("DAW audio backend unavailable; using Qt audio fallback")
        try:
            from freak_media_player.player.qt_audio_backend import QtAudioBackend
        except ImportError:
            return NullAudioBackend()
        return QtAudioBackend()
    return DawAudioBackend(audio_samples=audio_samples)
