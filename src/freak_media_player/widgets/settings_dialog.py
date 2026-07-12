"""Persistent player preferences dialog."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from freak_media_player.config.settings import PlayerPreferences
from freak_media_player.models.playback import AudioOutputDevice


class SettingsDialog(QDialog):
    def __init__(
        self,
        preferences: PlayerPreferences,
        audio_devices: list[AudioOutputDevice],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Freak Media Player Settings")
        self.setModal(True)
        self.setMinimumWidth(460)
        self._audio_device = QComboBox()
        self._restore_session = QCheckBox("Restore last track and position (paused)")
        self._continue_after_track = QCheckBox("Continue with the next playlist track")
        self._restore_layout = QCheckBox("Restore window and module layout")
        self._visualizer_quality = QComboBox()
        self._notifications = QCheckBox("Enable track-change notifications")
        self._build_layout(audio_devices)
        self._load(preferences)

    def preferences(self) -> PlayerPreferences:
        device_id = self._audio_device.currentData()
        return PlayerPreferences(
            restore_session=self._restore_session.isChecked(),
            continue_after_track=self._continue_after_track.isChecked(),
            restore_layout=self._restore_layout.isChecked(),
            visualizer_quality=str(self._visualizer_quality.currentData()),
            enable_notifications=self._notifications.isChecked(),
            audio_device_id=device_id if isinstance(device_id, str) else None,
        )

    def _build_layout(self, audio_devices: list[AudioOutputDevice]) -> None:
        layout = QVBoxLayout(self)
        audio = QGroupBox("Audio output")
        audio_form = QFormLayout(audio)
        self._audio_device.addItem("Follow Windows default", None)
        for device in audio_devices:
            suffix = " (Windows default)" if device.is_default else ""
            self._audio_device.addItem(
                f"{device.description}{suffix}", device.device_id
            )
        audio_form.addRow("Output device", self._audio_device)
        layout.addWidget(audio)

        playback = QGroupBox("Playback and session")
        playback_layout = QVBoxLayout(playback)
        playback_layout.addWidget(self._restore_session)
        playback_layout.addWidget(self._continue_after_track)
        layout.addWidget(playback)

        interface = QGroupBox("Interface")
        interface_form = QFormLayout(interface)
        interface_form.addRow(self._restore_layout)
        self._visualizer_quality.addItem("Eco (lower CPU)", "eco")
        self._visualizer_quality.addItem("Balanced", "balanced")
        self._visualizer_quality.addItem("Smooth (up to 60 FPS)", "smooth")
        interface_form.addRow("Visualizer performance", self._visualizer_quality)
        interface_form.addRow(self._notifications)
        layout.addWidget(interface)

        note = QLabel("Changes apply immediately and are used on the next start.")
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self, preferences: PlayerPreferences) -> None:
        self._restore_session.setChecked(preferences.restore_session)
        self._continue_after_track.setChecked(preferences.continue_after_track)
        self._restore_layout.setChecked(preferences.restore_layout)
        self._notifications.setChecked(preferences.enable_notifications)
        quality_index = self._visualizer_quality.findData(
            preferences.visualizer_quality
        )
        self._visualizer_quality.setCurrentIndex(max(0, quality_index))
        device_index = self._audio_device.findData(preferences.audio_device_id)
        self._audio_device.setCurrentIndex(max(0, device_index))
