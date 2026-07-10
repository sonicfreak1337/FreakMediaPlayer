"""Logo and cover-art widgets."""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from freak_media_player.ui.assets import asset_path


class ClippedArtwork(QWidget):
    """Smooth rounded artwork surface using the branded logo as fallback."""

    def __init__(self, size: int, radius: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._radius = radius
        self._pixmap = QPixmap(str(asset_path("app_logo.png")))
        self.setFixedSize(size, size)

    def sizeHint(self) -> QSize:
        return QSize(self.width(), self.height())

    def set_source(self, source: str | None) -> None:
        candidate = QPixmap(source) if source else QPixmap()
        if not candidate.isNull():
            self._pixmap = candidate
        else:
            self._pixmap = QPixmap(str(asset_path("app_logo.png")))
        self.update()

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1.0, 1.0, -1.0, -1.0)
        clip = QPainterPath()
        clip.addRoundedRect(rect, self._radius, self._radius)
        painter.setClipPath(clip)
        painter.fillRect(self.rect(), QColor("#020714"))
        if not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            source_x = max(0, (scaled.width() - self.width()) // 2)
            source_y = max(0, (scaled.height() - self.height()) // 2)
            painter.drawPixmap(0, 0, scaled, source_x, source_y, self.width(), self.height())
        painter.setClipping(False)
        painter.setPen(QPen(QColor("#1f4b91"), 2.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, self._radius, self._radius)
