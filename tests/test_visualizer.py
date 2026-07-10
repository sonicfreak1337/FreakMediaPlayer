import math

import numpy as np
from PySide6.QtWidgets import QApplication

from freak_media_player.player.audio_samples import AudioSampleBuffer
from freak_media_player.plugins.visualizer.widget import PRESETS, VisualizerCanvas


def test_all_visualizer_presets_render() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    audio_samples = AudioSampleBuffer()
    timeline = np.arange(4096, dtype=np.float32) / audio_samples.sample_rate
    signal = (
        0.45 * np.sin(2 * math.pi * 55 * timeline)
        + 0.25 * np.sin(2 * math.pi * 440 * timeline)
        + 0.12 * np.sin(2 * math.pi * 4000 * timeline)
    )
    stereo = np.column_stack((signal, signal))
    audio_samples.append_pcm16_stereo((np.clip(stereo, -1.0, 1.0) * 32767).astype("<i2").tobytes())
    canvas = VisualizerCanvas(audio_samples)
    canvas.resize(900, 300)
    canvas.show()
    app.processEvents()

    preset_ids = [preset_id for preset_id, _name in PRESETS]
    assert len(preset_ids) == 13
    assert preset_ids[0] == "freak_pulse"
    assert len(set(preset_ids)) == len(preset_ids)
    for preset_id in preset_ids:
        canvas.set_preset(preset_id)
        pixmap = canvas.grab()
        assert not pixmap.isNull(), preset_id
        assert pixmap.size().width() == 900
        assert pixmap.size().height() == 300

    canvas.close()
