"""Small, fully skippable first-start setup."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from freak_media_player.models.playback import AudioOutputDevice

SKIPPED = 2


@dataclass(frozen=True)
class FirstStartChoices:
    music_folder: Path | None
    audio_device_id: str | None
    restore_session: bool


class FirstStartDialog(QDialog):
    def __init__(
        self,
        audio_devices: list[AudioOutputDevice],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Welcome to Freak Media Player")
        self.setMinimumWidth(520)
        self._folder = QLineEdit()
        self._audio_device = QComboBox()
        self._restore_session = QCheckBox("Restore the last track on future starts")
        self._restore_session.setChecked(True)
        layout = QVBoxLayout(self)
        intro = QLabel(
            "Choose initial local-player defaults. Every item is optional and can "
            "be changed later in Settings."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        form = QFormLayout()
        folder_row = QHBoxLayout()
        folder_row.addWidget(self._folder, 1)
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse_folder)
        folder_row.addWidget(browse)
        form.addRow("Music folder", folder_row)
        self._audio_device.addItem("Follow Windows default", None)
        for device in audio_devices:
            self._audio_device.addItem(device.description, device.device_id)
        form.addRow("Audio output", self._audio_device)
        form.addRow(self._restore_session)
        layout.addLayout(form)
        actions = QHBoxLayout()
        actions.addStretch(1)
        skip = QPushButton("Skip")
        finish = QPushButton("Finish setup")
        skip.clicked.connect(lambda: self.done(SKIPPED))
        finish.clicked.connect(self.accept)
        actions.addWidget(skip)
        actions.addWidget(finish)
        layout.addLayout(actions)

    def choices(self) -> FirstStartChoices:
        folder_text = self._folder.text().strip()
        device_id = self._audio_device.currentData()
        return FirstStartChoices(
            music_folder=Path(folder_text) if folder_text else None,
            audio_device_id=device_id if isinstance(device_id, str) else None,
            restore_session=self._restore_session.isChecked(),
        )

    def _browse_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Choose music folder")
        if selected:
            self._folder.setText(selected)
