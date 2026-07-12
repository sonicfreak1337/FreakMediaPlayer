"""Database-only track metadata editor dialog."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from freak_media_player.models.media import Track


@dataclass(frozen=True)
class EditedTrackMetadata:
    title: str
    artist: str
    album: str | None
    release_year: int | None
    genre: str | None
    track_number: int | None
    disc_number: int | None


class MetadataEditorDialog(QDialog):
    def __init__(self, track: Track, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit library metadata")
        self.setModal(True)
        self._title = QLineEdit(track.title)
        self._artist = QLineEdit(track.artist.name)
        self._album = QLineEdit(track.album.title if track.album else "")
        self._year = self._optional_spin(9999)
        self._genre = QLineEdit(track.genre or "")
        self._track_number = self._optional_spin(999)
        self._disc_number = self._optional_spin(99)
        if track.album and track.album.release_year:
            self._year.setValue(track.album.release_year)
        if track.track_number:
            self._track_number.setValue(track.track_number)
        if track.disc_number:
            self._disc_number.setValue(track.disc_number)
        self._build_layout()

    def values(self) -> EditedTrackMetadata:
        return EditedTrackMetadata(
            title=self._title.text(),
            artist=self._artist.text(),
            album=self._optional_text(self._album),
            release_year=self._optional_value(self._year),
            genre=self._optional_text(self._genre),
            track_number=self._optional_value(self._track_number),
            disc_number=self._optional_value(self._disc_number),
        )

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        note = QLabel(
            "Changes are stored safely in the library database. The audio file "
            "itself is not modified."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        form = QFormLayout()
        form.addRow("Title", self._title)
        form.addRow("Artist", self._artist)
        form.addRow("Album", self._album)
        form.addRow("Year", self._year)
        form.addRow("Genre", self._genre)
        form.addRow("Track number", self._track_number)
        form.addRow("Disc number", self._disc_number)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _optional_spin(self, maximum: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(0, maximum)
        spin.setSpecialValueText("Not set")
        spin.setMinimum(0)
        return spin

    def _optional_value(self, spin: QSpinBox) -> int | None:
        value = spin.value()
        if value == 0:
            return None
        return value

    def _optional_text(self, field: QLineEdit) -> str | None:
        value = field.text().strip()
        return value or None
