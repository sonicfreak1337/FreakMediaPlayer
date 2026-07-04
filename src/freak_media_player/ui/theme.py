"""Application theme setup."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def apply_dark_theme(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(24, 25, 28))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(235, 236, 240))
    palette.setColor(QPalette.ColorRole.Base, QColor(18, 19, 22))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(34, 36, 42))
    palette.setColor(QPalette.ColorRole.Text, QColor(235, 236, 240))
    palette.setColor(QPalette.ColorRole.Button, QColor(40, 42, 48))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(235, 236, 240))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(80, 140, 220))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
