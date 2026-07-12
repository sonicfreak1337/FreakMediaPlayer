import numpy as np

from freak_media_player.player.audio_samples import AudioSampleBuffer


def stereo_payload(left: list[int], right: list[int]) -> bytes:
    return np.column_stack((left, right)).astype("<i2").tobytes()


def test_audio_sample_buffer_downmixes_and_returns_latest_samples() -> None:
    samples = AudioSampleBuffer(capacity=4)
    samples.append_pcm16_stereo(stereo_payload([32767, 0, -32768], [32767, 0, -32768]))

    snapshot = samples.snapshot(4)

    assert snapshot[0] == 0.0
    assert snapshot[1] == np.float32(32767 / 32768)
    assert snapshot[2] == 0.0
    assert snapshot[3] == -1.0


def test_audio_sample_buffer_preserves_split_pcm_frames_and_wraps() -> None:
    samples = AudioSampleBuffer(capacity=3)
    payload = stereo_payload([1000, 2000, 3000, 4000], [1000, 2000, 3000, 4000])
    samples.append_pcm16_stereo(payload[:5])
    samples.append_pcm16_stereo(payload[5:])

    np.testing.assert_allclose(
        samples.snapshot(3),
        np.array([2000, 3000, 4000], dtype=np.float32) / 32768,
    )


def test_audio_sample_buffer_clear_returns_silence() -> None:
    samples = AudioSampleBuffer(capacity=4)
    samples.append_pcm16_stereo(stereo_payload([100], [100]))
    samples.clear()

    np.testing.assert_array_equal(samples.snapshot(4), np.zeros(4, dtype=np.float32))


def test_audio_sample_buffer_accepts_multichannel_pcm() -> None:
    samples = AudioSampleBuffer(capacity=2)
    payload = np.array([[1000, 1000, 1000, 1000, 1000, 1000]], dtype="<i2").tobytes()

    samples.append_pcm16(payload, 6)

    np.testing.assert_allclose(samples.snapshot(2), [0.0, 1000 / 32768])
