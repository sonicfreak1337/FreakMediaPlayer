import tomllib
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from freak_media_player import __version__
from freak_media_player.models.equalizer import (
    EQUALIZER_PRESETS,
    EqualizerBand,
    EqualizerPreset,
)
from freak_media_player.player.audio_samples import AudioSampleBuffer
from freak_media_player.player.dsp.parametric_equalizer import (
    ParametricEqualizerProcessor,
)
from freak_media_player.plugins.visualizer.widget import (
    QUALITY_INTERVALS,
    VisualizerCanvas,
)

SAMPLE_RATE = 48_000
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _stereo_payload(samples: list[int]) -> bytes:
    return np.column_stack((samples, samples)).astype("<i2").tobytes()


def test_flat_equalizer_returns_the_original_sample_array() -> None:
    flat_preset = next(preset for preset in EQUALIZER_PRESETS if preset.preset_id == "flat")
    processor = ParametricEqualizerProcessor(flat_preset)
    samples = np.linspace(-0.5, 0.5, 512, dtype=np.float32).reshape(2, 256)

    processed = processor.process(samples, SAMPLE_RATE)

    assert processed is samples


def test_equalizer_bypasses_inactive_bands_but_keeps_active_processing() -> None:
    preset = EqualizerPreset(
        preset_id="mixed",
        name="Mixed",
        bands=(
            EqualizerBand(frequency_hz=250, gain_db=12.0, enabled=False),
            EqualizerBand(frequency_hz=4_000, gain_db=0.0),
            EqualizerBand(frequency_hz=1_000, gain_db=6.0),
        ),
    )
    timeline = np.arange(8_192, dtype=np.float32) / SAMPLE_RATE
    signal = np.sin(2.0 * np.pi * 1_000.0 * timeline).astype(np.float32)
    samples = np.vstack((signal, signal))
    processor = ParametricEqualizerProcessor(preset)

    processed = processor.process(samples, SAMPLE_RATE)
    input_rms = float(np.sqrt(np.mean(np.square(samples[:, 4_096:]))))
    output_rms = float(np.sqrt(np.mean(np.square(processed[:, 4_096:]))))

    assert processor._sections.shape[0] == 1
    assert output_rms > input_rms * 1.8


def test_audio_sample_capture_can_be_enabled_and_disabled() -> None:
    samples = AudioSampleBuffer(capacity=4, capture_enabled=False)
    ignored_payload = _stereo_payload([1_000, 2_000])

    samples.append_pcm16_stereo(ignored_payload)

    assert samples.sequence == 0
    np.testing.assert_array_equal(samples.snapshot(4), np.zeros(4, dtype=np.float32))

    samples.set_capture_enabled(True)
    samples.append_pcm16_stereo(_stereo_payload([3_000, 4_000]))

    assert samples.sequence == 2
    np.testing.assert_allclose(
        samples.snapshot(4),
        np.array([0, 0, 3_000, 4_000], dtype=np.float32) / 32_768,
    )

    samples.set_capture_enabled(False)
    snapshot_before_ignored_append = samples.snapshot(4)
    sequence_before_ignored_append = samples.sequence
    samples.append_pcm16_stereo(_stereo_payload([5_000, 6_000]))

    assert samples.sequence == sequence_before_ignored_append
    np.testing.assert_array_equal(samples.snapshot(4), snapshot_before_ignored_append)


def test_visualizer_only_runs_during_playback_and_tracks_application_focus(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    samples = AudioSampleBuffer(capture_enabled=False)
    canvas = VisualizerCanvas(samples)
    focused = [True]
    monkeypatch.setattr(canvas, "_is_application_focused", lambda: focused[0])

    assert canvas._timer.isActive() is False
    canvas.show()
    app.processEvents()
    assert canvas._timer.isActive() is False

    samples.set_playback_active(True)
    assert canvas._timer.isActive() is True
    assert canvas._timer.interval() == QUALITY_INTERVALS["balanced"][0]
    samples.append_pcm16_stereo(_stereo_payload([1_000, 2_000]))

    focused[0] = False
    canvas._sync_frame_interval()
    assert canvas._timer.interval() == QUALITY_INTERVALS["balanced"][1]

    samples.set_playback_active(False)
    assert canvas._timer.isActive() is False
    sequence_before_ignored_append = samples.sequence
    samples.append_pcm16_stereo(_stereo_payload([3_000, 4_000]))
    assert samples.sequence == sequence_before_ignored_append
    canvas.close()


def test_project_version_sources_are_synchronized_on_1_0_0() -> None:
    expected_version = "1.1.0"
    project_metadata = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert project_metadata["project"]["version"] == expected_version
    assert __version__ == expected_version
    assert f"Current version: `{expected_version}`" in readme
    assert f"## {expected_version} -" in changelog
    for required_document in (
        "USER_GUIDE.md",
        "THIRD_PARTY_NOTICES.md",
        "KNOWN_ISSUES.md",
        "RELEASE_CHECKLIST.md",
    ):
        assert (PROJECT_ROOT / required_document).is_file()
