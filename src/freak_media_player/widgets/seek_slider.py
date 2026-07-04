"""Clickable playback seek slider."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal

from freak_media_player.widgets.clickable_slider import ClickableSlider


class SeekSlider(ClickableSlider):
    seek_requested = Signal(int)

    def __init__(self) -> None:
        super().__init__(Qt.Orientation.Horizontal)
        self.setRange(0, 0)
        self.setSingleStep(1000)
        self.setPageStep(10000)
        self.value_clicked.connect(self.seek_requested.emit)
