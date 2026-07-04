"""Equalizer control panel."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from freak_media_player.models.equalizer import MAX_GAIN_DB, MIN_GAIN_DB, EqualizerPreset
from freak_media_player.services.equalizer_service import (
    CUSTOM_PRESET_ID,
    EqualizerService,
)

GAIN_SCALE = 10
SLIDER_MINIMUM = round(MIN_GAIN_DB * GAIN_SCALE)
SLIDER_MAXIMUM = round(MAX_GAIN_DB * GAIN_SCALE)


class EqualizerPanel(QWidget):
    def __init__(self, equalizer_service: EqualizerService) -> None:
        super().__init__()
        self._equalizer_service = equalizer_service
        self._preset_combo = QComboBox()
        self._band_sliders: list[QSlider] = []
        self._band_value_labels: list[QLabel] = []
        self._updating_sliders = False
        self._build_layout()
        self._load_presets()

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(18)

        header = QHBoxLayout()
        title = QLabel("Equalizer")
        title.setObjectName("panelTitle")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self._preset_combo)

        bands = QGridLayout()
        bands.setHorizontalSpacing(12)
        bands.setVerticalSpacing(8)
        for column in range(10):
            slider = QSlider(Qt.Orientation.Vertical)
            slider.setRange(SLIDER_MINIMUM, SLIDER_MAXIMUM)
            slider.setTickInterval(GAIN_SCALE * 3)
            slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
            slider.setFixedHeight(220)
            value_label = QLabel("0.0 dB")
            value_label.setObjectName("playerTime")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._band_sliders.append(slider)
            self._band_value_labels.append(value_label)
            bands.addWidget(value_label, 0, column)
            bands.addWidget(slider, 1, column, Qt.AlignmentFlag.AlignHCenter)
            slider.valueChanged.connect(self._set_custom_from_sliders)

        layout.addLayout(header)
        layout.addLayout(bands)
        layout.addStretch(1)

        self._preset_combo.currentIndexChanged.connect(self._select_current_preset)

    def _load_presets(self) -> None:
        for preset in self._equalizer_service.presets():
            self._preset_combo.addItem(preset.name, preset.preset_id)
        self._preset_combo.addItem("Custom", CUSTOM_PRESET_ID)
        self._apply_preset(self._equalizer_service.current_preset())

    def _select_current_preset(self, _index: int) -> None:
        preset_id = self._preset_combo.currentData()
        if isinstance(preset_id, str) and preset_id != CUSTOM_PRESET_ID:
            self._apply_preset(self._equalizer_service.select_preset(preset_id))

    def _apply_preset(self, preset: EqualizerPreset) -> None:
        self._updating_sliders = True
        self._sync_combo(preset)
        for index, band in enumerate(preset.bands):
            self._band_sliders[index].setValue(round(band.gain_db * GAIN_SCALE))
            frequency_label = self._format_frequency(band.frequency_hz)
            gain_label = self._format_gain(band.gain_db)
            self._band_value_labels[index].setText(f"{frequency_label}\n{gain_label}")
        self._updating_sliders = False

    def _set_custom_from_sliders(self, _value: int) -> None:
        if self._updating_sliders:
            return
        gains_db = tuple(slider.value() / GAIN_SCALE for slider in self._band_sliders)
        self._apply_preset(self._equalizer_service.set_custom_gains(gains_db))

    def _sync_combo(self, preset: EqualizerPreset) -> None:
        index = self._preset_combo.findData(preset.preset_id)
        if index >= 0 and index != self._preset_combo.currentIndex():
            self._preset_combo.blockSignals(True)
            self._preset_combo.setCurrentIndex(index)
            self._preset_combo.blockSignals(False)

    def _format_frequency(self, frequency_hz: int) -> str:
        if frequency_hz >= 1000:
            return f"{frequency_hz // 1000}k"
        return f"{frequency_hz}"

    def _format_gain(self, gain_db: float) -> str:
        return f"{gain_db:+.1f} dB"
