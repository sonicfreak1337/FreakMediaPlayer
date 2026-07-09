"""DAW-style parametric equalizer controls."""

from __future__ import annotations

import math

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from freak_media_player.models.equalizer import (
    EQUALIZER_FREQUENCIES_HZ,
    EQUALIZER_REFERENCE_SAMPLE_RATE,
    MAX_FREQUENCY_HZ,
    MAX_GAIN_DB,
    MAX_PREAMP_DB,
    MAX_Q,
    MIN_FREQUENCY_HZ,
    MIN_GAIN_DB,
    MIN_PREAMP_DB,
    MIN_Q,
    EqualizerPreset,
)
from freak_media_player.services.equalizer_service import (
    CUSTOM_PRESET_ID,
    EqualizerService,
)
from freak_media_player.widgets.equalizer_response_graph import EqualizerResponseGraph

RESPONSE_POINT_COUNT = 180


class EqualizerPanel(QWidget):
    def __init__(
        self,
        equalizer_service: EqualizerService,
        show_title: bool = True,
    ) -> None:
        super().__init__()
        self._equalizer_service = equalizer_service
        self._show_title = show_title
        self._preset_combo = QComboBox()
        self._graph = EqualizerResponseGraph()
        self._band_group = QButtonGroup(self)
        self._band_buttons: list[QToolButton] = []
        self._enabled = QCheckBox("Enabled")
        self._frequency = QSpinBox()
        self._gain = QDoubleSpinBox()
        self._q = QDoubleSpinBox()
        self._preamp = QDoubleSpinBox()
        self._selected_band = 0
        self._updating_controls = False
        self._response_frequencies = self._make_response_frequencies()
        self._build_layout()
        self._configure_controls()
        self._load_presets()

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()
        if self._show_title:
            title = QLabel("Equalizer")
            title.setObjectName("panelTitle")
            header.addWidget(title)
        header.addStretch(1)
        header.addWidget(QLabel("Preamp"))
        header.addWidget(self._preamp)
        header.addWidget(self._preset_combo)

        band_selector = QHBoxLayout()
        band_selector.setSpacing(4)
        for index in range(len(EQUALIZER_FREQUENCIES_HZ)):
            button = QToolButton()
            button.setText(str(index + 1))
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            self._band_group.addButton(button, index)
            self._band_buttons.append(button)
            band_selector.addWidget(button)
        band_selector.addStretch(1)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        controls.addWidget(self._enabled)
        controls.addWidget(QLabel("Frequency"))
        controls.addWidget(self._frequency)
        controls.addWidget(QLabel("Gain"))
        controls.addWidget(self._gain)
        controls.addWidget(QLabel("Q"))
        controls.addWidget(self._q)
        controls.addStretch(1)

        layout.addLayout(header)
        layout.addWidget(self._graph, 1)
        layout.addLayout(band_selector)
        layout.addLayout(controls)

    def _configure_controls(self) -> None:
        self._frequency.setRange(MIN_FREQUENCY_HZ, MAX_FREQUENCY_HZ)
        self._frequency.setSuffix(" Hz")
        self._gain.setRange(MIN_GAIN_DB, MAX_GAIN_DB)
        self._gain.setDecimals(1)
        self._gain.setSingleStep(0.1)
        self._gain.setSuffix(" dB")
        self._q.setRange(MIN_Q, MAX_Q)
        self._q.setDecimals(2)
        self._q.setSingleStep(0.05)
        self._preamp.setRange(MIN_PREAMP_DB, MAX_PREAMP_DB)
        self._preamp.setDecimals(1)
        self._preamp.setSingleStep(0.5)
        self._preamp.setSuffix(" dB")

        self._preset_combo.currentIndexChanged.connect(self._select_current_preset)
        self._band_group.idClicked.connect(self._select_band)
        self._enabled.toggled.connect(self._update_selected_band)
        self._frequency.valueChanged.connect(self._update_selected_band)
        self._gain.valueChanged.connect(self._update_selected_band)
        self._q.valueChanged.connect(self._update_selected_band)
        self._preamp.valueChanged.connect(self._update_preamp)
        self._graph.band_selected.connect(self._select_band)
        self._graph.band_edited.connect(self._edit_band_from_graph)

    def _load_presets(self) -> None:
        for preset in self._equalizer_service.presets():
            self._preset_combo.addItem(preset.name, preset.preset_id)
        self._preset_combo.addItem("Custom", CUSTOM_PRESET_ID)
        self._band_buttons[0].setChecked(True)
        self._apply_preset(self._equalizer_service.current_preset())

    def _select_current_preset(self, _index: int) -> None:
        preset_id = self._preset_combo.currentData()
        if isinstance(preset_id, str) and preset_id != CUSTOM_PRESET_ID:
            self._apply_preset(self._equalizer_service.select_preset(preset_id))

    def _select_band(self, index: int) -> None:
        self._selected_band = index
        self._band_buttons[index].setChecked(True)
        self._graph.select_band(index)
        self._sync_selected_band_controls(self._equalizer_service.current_preset())

    def _update_selected_band(self, _value: object = None) -> None:
        if self._updating_controls:
            return
        preset = self._equalizer_service.update_band(
            self._selected_band,
            frequency_hz=self._frequency.value(),
            gain_db=self._gain.value(),
            q=self._q.value(),
            enabled=self._enabled.isChecked(),
        )
        self._apply_preset(preset)

    def _edit_band_from_graph(
        self,
        index: int,
        frequency_hz: int,
        gain_db: float,
    ) -> None:
        self._selected_band = index
        current = self._equalizer_service.current_preset().bands[index]
        preset = self._equalizer_service.update_band(
            index,
            frequency_hz=frequency_hz,
            gain_db=gain_db,
            q=current.q,
            enabled=current.enabled,
        )
        self._apply_preset(preset)

    def _update_preamp(self, preamp_db: float) -> None:
        if not self._updating_controls:
            self._apply_preset(self._equalizer_service.set_preamp(preamp_db))

    def _apply_preset(self, preset: EqualizerPreset) -> None:
        self._updating_controls = True
        self._sync_combo(preset)
        self._preamp.setValue(preset.preamp_db)
        self._sync_selected_band_controls(preset)
        response = self._equalizer_service.frequency_response_db(
            self._response_frequencies,
            EQUALIZER_REFERENCE_SAMPLE_RATE,
        )
        self._graph.set_data(preset, self._response_frequencies, response)
        self._graph.select_band(self._selected_band)
        self._band_buttons[self._selected_band].setChecked(True)
        self._updating_controls = False

    def _sync_selected_band_controls(self, preset: EqualizerPreset) -> None:
        previous_state = self._updating_controls
        self._updating_controls = True
        band = preset.bands[self._selected_band]
        self._enabled.setChecked(band.enabled)
        self._frequency.setValue(band.frequency_hz)
        self._gain.setValue(band.gain_db)
        self._q.setValue(band.q)
        self._updating_controls = previous_state

    def _sync_combo(self, preset: EqualizerPreset) -> None:
        index = self._preset_combo.findData(preset.preset_id)
        if index >= 0 and index != self._preset_combo.currentIndex():
            self._preset_combo.blockSignals(True)
            self._preset_combo.setCurrentIndex(index)
            self._preset_combo.blockSignals(False)

    def _make_response_frequencies(self) -> tuple[float, ...]:
        ratio = MAX_FREQUENCY_HZ / MIN_FREQUENCY_HZ
        return tuple(
            MIN_FREQUENCY_HZ * math.pow(ratio, index / (RESPONSE_POINT_COUNT - 1))
            for index in range(RESPONSE_POINT_COUNT)
        )
