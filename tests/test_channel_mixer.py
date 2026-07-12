import numpy as np

from freak_media_player.player.channel_mixer import mix_channels


def test_stereo_upmix_uses_standard_channel_order_and_silent_lfe() -> None:
    stereo = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)

    surround = mix_channels(stereo, ("FL", "FR"), "5.1")

    np.testing.assert_array_equal(surround[0], stereo[0])
    np.testing.assert_array_equal(surround[1], stereo[1])
    np.testing.assert_allclose(surround[2], [0.5, 0.5])
    np.testing.assert_array_equal(surround[3], [0.0, 0.0])
    np.testing.assert_allclose(surround[4], [0.5, 0.0])
    np.testing.assert_allclose(surround[5], [0.0, 0.5])


def test_surround_downmix_is_peak_stable_and_keeps_left_right_sides() -> None:
    surround = np.ones((8, 16), dtype=np.float32)

    stereo = mix_channels(
        surround,
        ("FL", "FR", "FC", "LFE", "BL", "BR", "SL", "SR"),
        "stereo",
    )

    assert stereo.shape == (2, 16)
    assert float(np.max(np.abs(stereo))) <= 1.0


def test_mono_source_uses_center_for_surround_output() -> None:
    mono = np.array([[0.75, -0.75]], dtype=np.float32)

    surround = mix_channels(mono, ("FC",), "7.1")

    np.testing.assert_array_equal(surround[2], mono[0])
    assert np.count_nonzero(surround) == 2
