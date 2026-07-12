"""Logo and cover-art widgets."""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from freak_media_player.models.media import Track
from freak_media_player.ui.assets import asset_path
from freak_media_player.ui.skins import skin_color

COVER_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".webp"}
COVER_STEM_PRIORITY = ("cover", "folder", "front", "album", "albumart")


def find_track_cover(track: Track) -> str | None:
    """Find conventional album artwork next to a local track."""
    if track.cover_url:
        return track.cover_url

    track_path = Path(track.provider_identity.item_id)
    album_folder = track_path.parent
    if not album_folder.is_dir():
        return None
    images = sorted(
        path
        for path in album_folder.iterdir()
        if path.is_file() and path.suffix.lower() in COVER_EXTENSIONS
    )
    by_stem = {path.stem.casefold(): path for path in images}
    for preferred_stem in COVER_STEM_PRIORITY:
        if cover := by_stem.get(preferred_stem):
            return str(cover)

    if track.album is not None:
        album_stem = re.sub(r"[^a-z0-9]+", "", track.album.title.casefold())
        for image in images:
            image_stem = re.sub(r"[^a-z0-9]+", "", image.stem.casefold())
            if image_stem == album_stem:
                return str(image)
    if len(images) == 1:
        return str(images[0])
    return None


class LogoArtwork(QWidget):
    """Transparent unframed brand mark for the left side of the Player."""

    def __init__(self, size: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap = QPixmap(str(asset_path("app_logo.png")))
        self.setFixedSize(size, size)

    def refresh_skin_asset(self) -> None:
        self._pixmap = QPixmap(str(asset_path("app_logo.png")))
        self.update()

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self._pixmap.isNull():
            return
        margin = max(3, round(min(self.width(), self.height()) * 0.045))
        scaled = self._pixmap.scaled(
            max(1, self.width() - margin * 2),
            max(1, self.height() - margin * 2),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawPixmap(
            (self.width() - scaled.width()) // 2,
            (self.height() - scaled.height()) // 2,
            scaled,
        )


class ClippedArtwork(QWidget):
    """Smooth rounded artwork surface using the branded logo as fallback."""

    def __init__(self, size: int, radius: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._radius = radius
        self._pixmap = QPixmap(str(asset_path("app_logo.png")))
        self._using_fallback = True
        self.setFixedSize(size, size)

    def sizeHint(self) -> QSize:
        return QSize(self.width(), self.height())

    def set_source(self, source: str | None) -> None:
        candidate = QPixmap(source) if source else QPixmap()
        if not candidate.isNull():
            self._pixmap = candidate
            self._using_fallback = False
        else:
            self._pixmap = QPixmap(str(asset_path("app_logo.png")))
            self._using_fallback = True
        self.update()

    def refresh_skin_asset(self) -> None:
        if self._using_fallback:
            self._pixmap = QPixmap(str(asset_path("app_logo.png")))
        self.update()

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1.0, 1.0, -1.0, -1.0)
        clip = QPainterPath()
        clip.addRoundedRect(rect, self._radius, self._radius)
        painter.setClipPath(clip)
        painter.fillRect(self.rect(), QColor(skin_color("artwork_background")))
        if not self._pixmap.isNull():
            aspect_mode = (
                Qt.AspectRatioMode.KeepAspectRatio
                if self._using_fallback
                else Qt.AspectRatioMode.KeepAspectRatioByExpanding
            )
            scaled = self._pixmap.scaled(
                self.size(),
                aspect_mode,
                Qt.TransformationMode.SmoothTransformation,
            )
            if self._using_fallback:
                painter.drawPixmap(
                    (self.width() - scaled.width()) // 2,
                    (self.height() - scaled.height()) // 2,
                    scaled,
                )
            else:
                source_x = max(0, (scaled.width() - self.width()) // 2)
                source_y = max(0, (scaled.height() - self.height()) // 2)
                painter.drawPixmap(
                    0,
                    0,
                    scaled,
                    source_x,
                    source_y,
                    self.width(),
                    self.height(),
                )
        painter.setClipping(False)
        painter.setPen(QPen(QColor(skin_color("artwork_border")), 2.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, self._radius, self._radius)
