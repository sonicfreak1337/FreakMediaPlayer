"""Persistent player preferences dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from freak_media_player.config.settings import PlayerPreferences
from freak_media_player.models.playback import AudioOutputDevice, AudioOutputMode
from freak_media_player.services.backup_service import BackupService


class SettingsDialog(QDialog):
    def __init__(
        self,
        preferences: PlayerPreferences,
        audio_devices: list[AudioOutputDevice],
        parent: QWidget | None = None,
        backup_service: BackupService | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Freak Media Player Settings")
        self.setModal(True)
        self.setMinimumWidth(460)
        self._audio_device = QComboBox()
        self._audio_mode = QComboBox()
        self._audio_devices = audio_devices
        self._backup_service = backup_service
        self._restore_session = QCheckBox("Restore last track and position (paused)")
        self._continue_after_track = QCheckBox("Continue with the next playlist track")
        self._restore_layout = QCheckBox("Restore window and module layout")
        self._visualizer_quality = QComboBox()
        self._build_layout(audio_devices)
        self._load(preferences)

    def preferences(self) -> PlayerPreferences:
        device_id = self._audio_device.currentData()
        return PlayerPreferences(
            restore_session=self._restore_session.isChecked(),
            continue_after_track=self._continue_after_track.isChecked(),
            restore_layout=self._restore_layout.isChecked(),
            visualizer_quality=str(self._visualizer_quality.currentData()),
            audio_device_id=device_id if isinstance(device_id, str) else None,
            audio_output_mode=str(self._audio_mode.currentData()),
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
        self._audio_device.currentIndexChanged.connect(self._refresh_output_modes)
        audio_form.addRow("Speaker configuration", self._audio_mode)
        explanation = QLabel(
            "Only configurations supported by the selected Windows device are shown."
        )
        explanation.setWordWrap(True)
        audio_form.addRow(explanation)
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
        layout.addWidget(interface)

        if self._backup_service is not None:
            data = QGroupBox("Local data")
            data_layout = QHBoxLayout(data)
            export_button = QPushButton("Export backup…")
            restore_button = QPushButton("Restore backup…")
            export_button.clicked.connect(self._export_backup)
            restore_button.clicked.connect(self._restore_backup)
            data_layout.addWidget(export_button)
            data_layout.addWidget(restore_button)
            layout.addWidget(data)

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
        quality_index = self._visualizer_quality.findData(
            preferences.visualizer_quality
        )
        self._visualizer_quality.setCurrentIndex(max(0, quality_index))
        device_index = self._audio_device.findData(preferences.audio_device_id)
        self._audio_device.setCurrentIndex(max(0, device_index))
        self._refresh_output_modes()
        mode_index = self._audio_mode.findData(preferences.audio_output_mode)
        self._audio_mode.setCurrentIndex(max(0, mode_index))

    def _refresh_output_modes(self) -> None:
        selected_id = self._audio_device.currentData()
        device = next(
            (
                item
                for item in self._audio_devices
                if item.device_id == selected_id
                or (selected_id is None and item.is_default)
            ),
            None,
        )
        modes = device.supported_modes if device else (AudioOutputMode.STEREO,)
        previous = self._audio_mode.currentData()
        self._audio_mode.clear()
        labels = {
            AudioOutputMode.MONO: "Mono",
            AudioOutputMode.STEREO: "Stereo",
            AudioOutputMode.SURROUND_5_1: "5.1 Surround",
            AudioOutputMode.SURROUND_7_1: "7.1 Surround",
        }
        for mode in modes:
            self._audio_mode.addItem(labels[mode], mode.value)
        index = self._audio_mode.findData(previous)
        if index < 0:
            index = self._audio_mode.findData(AudioOutputMode.STEREO.value)
        self._audio_mode.setCurrentIndex(max(0, index))

    def _export_backup(self) -> None:
        if self._backup_service is None:
            return
        selected, _filter = QFileDialog.getSaveFileName(
            self,
            "Export Freak Media Player backup",
            "freak-media-player-backup.freakbackup",
            "Freak backups (*.freakbackup)",
        )
        if not selected:
            return
        try:
            path = self._backup_service.export_backup(Path(selected))
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Backup failed", str(error))
            return
        QMessageBox.information(self, "Backup complete", f"Saved to:\n{path}")

    def _restore_backup(self) -> None:
        if self._backup_service is None:
            return
        selected, _filter = QFileDialog.getOpenFileName(
            self,
            "Restore Freak Media Player backup",
            "",
            "Freak backups (*.freakbackup)",
        )
        if not selected:
            return
        answer = QMessageBox.question(
            self,
            "Restore backup?",
            "Current local data will be replaced after a safety backup is created.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            result = self._backup_service.restore_backup(Path(selected))
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Restore failed", str(error))
            return
        QMessageBox.information(
            self,
            "Restore complete",
            f"Data restored. Safety backup:\n{result.safety_backup}\n\n"
            "Restart Freak Media Player before continuing.",
        )
        self.reject()
