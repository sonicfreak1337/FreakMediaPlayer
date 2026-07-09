import numpy as np
import pytest

from freak_media_player.core.equalizer_math import response_db
from freak_media_player.models.equalizer import EqualizerBand, EqualizerPreset
from freak_media_player.player.dsp.parametric_equalizer import (
    ParametricEqualizerProcessor,
)
from freak_media_player.player.pcm import float_samples_to_int16_bytes

SAMPLE_RATE = 48_000


def make_peak_preset(gain_db: float) -> EqualizerPreset:
    return EqualizerPreset(
        preset_id="test",
        name="Test",
        bands=(EqualizerBand(frequency_hz=1000, gain_db=gain_db, q=1.0),),
    )


def test_peaking_response_matches_gain_at_center_frequency() -> None:
    preset = make_peak_preset(6.0)

    center_gain = response_db(preset, (1000.0,), SAMPLE_RATE)[0]

    assert center_gain == pytest.approx(6.0, abs=0.05)


def test_processor_preserves_state_across_audio_blocks() -> None:
    preset = make_peak_preset(4.0)
    timeline = np.arange(4096, dtype=np.float32) / SAMPLE_RATE
    signal = np.sin(2.0 * np.pi * 1000.0 * timeline).astype(np.float32)
    stereo = np.vstack((signal, signal))
    streaming = ParametricEqualizerProcessor(preset)
    single_pass = ParametricEqualizerProcessor(preset)

    streamed = np.hstack(
        (
            streaming.process(stereo[:, :2048], SAMPLE_RATE),
            streaming.process(stereo[:, 2048:], SAMPLE_RATE),
        )
    )
    complete = single_pass.process(stereo, SAMPLE_RATE)

    np.testing.assert_allclose(streamed, complete, atol=1e-6)


def test_pcm_conversion_clips_and_interleaves_stereo() -> None:
    samples = np.asarray(((1.5, -1.5), (0.5, -0.5)), dtype=np.float32)

    pcm = np.frombuffer(float_samples_to_int16_bytes(samples), dtype="<i2")

    assert pcm.tolist() == [32767, 16383, -32767, -16383]
