"""Skin-aware UI asset lookup and live widget refresh helpers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QAbstractButton, QLabel, QWidget

AssetResolver = Callable[[str], Path]

_asset_resolver: AssetResolver | None = None
_SKIN_ASSET_PROPERTY = "skinAssetPath"
_SKIN_ASSET_WIDTH_PROPERTY = "skinAssetWidth"
_SKIN_ASSET_HEIGHT_PROPERTY = "skinAssetHeight"


def set_asset_resolver(resolver: AssetResolver | None) -> None:
    """Set the active skin's resolver; ``None`` restores packaged assets."""
    global _asset_resolver
    _asset_resolver = resolver


def asset_path(file_name: str) -> Path:
    """Return an active-skin asset with a packaged fallback."""
    if _asset_resolver is not None:
        return _asset_resolver(file_name)
    return Path(__file__).resolve().parent.parent / "assets" / file_name


def set_themed_icon(button: QAbstractButton, file_name: str, size: int) -> None:
    """Apply an icon and remember its logical path for live skin changes."""
    button.setProperty(_SKIN_ASSET_PROPERTY, file_name)
    button.setProperty(_SKIN_ASSET_WIDTH_PROPERTY, size)
    button.setProperty(_SKIN_ASSET_HEIGHT_PROPERTY, size)
    button.setIcon(QIcon(str(asset_path(file_name))))
    button.setIconSize(QSize(size, size))


def clear_themed_icon(button: QAbstractButton) -> None:
    """Clear an icon and prevent a stale skin asset from being restored."""
    button.setProperty(_SKIN_ASSET_PROPERTY, None)
    button.setIcon(QIcon())


def set_themed_pixmap(label: QLabel, file_name: str, width: int, height: int) -> None:
    """Apply a pixmap and remember its logical path for live skin changes."""
    label.setProperty(_SKIN_ASSET_PROPERTY, file_name)
    label.setProperty(_SKIN_ASSET_WIDTH_PROPERTY, width)
    label.setProperty(_SKIN_ASSET_HEIGHT_PROPERTY, height)
    _refresh_label_pixmap(label)


def refresh_skin_assets(root: QWidget) -> None:
    """Reload all marked icons, pixmaps and custom painted skin assets."""
    widgets = [root, *root.findChildren(QWidget)]
    for widget in widgets:
        file_name = widget.property(_SKIN_ASSET_PROPERTY)
        if isinstance(file_name, str) and file_name:
            if isinstance(widget, QAbstractButton):
                size = int(widget.property(_SKIN_ASSET_WIDTH_PROPERTY) or 16)
                widget.setIcon(QIcon(str(asset_path(file_name))))
                widget.setIconSize(QSize(size, size))
            elif isinstance(widget, QLabel):
                _refresh_label_pixmap(widget)

        refresh = getattr(widget, "refresh_skin_asset", None)
        if callable(refresh):
            refresh()
        widget.update()


def _refresh_label_pixmap(label: QLabel) -> None:
    file_name = label.property(_SKIN_ASSET_PROPERTY)
    if not isinstance(file_name, str) or not file_name:
        return
    width = int(label.property(_SKIN_ASSET_WIDTH_PROPERTY) or label.width())
    height = int(label.property(_SKIN_ASSET_HEIGHT_PROPERTY) or label.height())
    label.setPixmap(
        QPixmap(str(asset_path(file_name))).scaled(
            width,
            height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    )
