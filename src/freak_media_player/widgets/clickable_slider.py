"""Slider that jumps to the clicked position."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QSlider, QStyle

HORIZONTAL_MINIMUM_HEIGHT = 24
MINIMUM_SLIDER_SPAN = 1


class ClickableSlider(QSlider):
    value_clicked = Signal(int)

    def __init__(self, orientation: Qt.Orientation) -> None:
        super().__init__(orientation)
        if orientation == Qt.Orientation.Horizontal:
            self.setMinimumHeight(HORIZONTAL_MINIMUM_HEIGHT)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setSliderDown(True)
            self._apply_mouse_position(event)
            self.value_clicked.emit(self.value())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton and self.isSliderDown():
            self._apply_mouse_position(event)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.isSliderDown():
            self._apply_mouse_position(event)
            self.setSliderDown(False)
            self.sliderReleased.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _apply_mouse_position(self, event: QMouseEvent) -> None:
        position = int(event.position().x())
        span = max(MINIMUM_SLIDER_SPAN, self.width())
        if self.orientation() == Qt.Orientation.Vertical:
            position = int(event.position().y())
            span = max(MINIMUM_SLIDER_SPAN, self.height())
        self.setValue(
            QStyle.sliderValueFromPosition(
                self.minimum(),
                self.maximum(),
                position,
                span,
                self._is_upside_down(),
            )
        )

    def _is_upside_down(self) -> bool:
        if self.orientation() == Qt.Orientation.Vertical:
            return not self.invertedAppearance()
        return self.invertedAppearance()
