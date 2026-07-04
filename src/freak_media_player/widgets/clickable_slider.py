"""Slider that jumps to the clicked position."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QSlider, QStyle


class ClickableSlider(QSlider):
    value_clicked = Signal(int)

    def __init__(self, orientation: Qt.Orientation) -> None:
        super().__init__(orientation)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            position = int(event.position().x())
            span = self.width()
            if self.orientation() == Qt.Orientation.Vertical:
                position = int(event.position().y())
                span = self.height()
            value = QStyle.sliderValueFromPosition(
                self.minimum(),
                self.maximum(),
                position,
                span,
                self.invertedAppearance(),
            )
            self.setValue(value)
            self.value_clicked.emit(value)
            event.accept()
            return
        super().mousePressEvent(event)
