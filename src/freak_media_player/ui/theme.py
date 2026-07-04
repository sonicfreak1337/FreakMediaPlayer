"""Application theme setup."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

BACKGROUND = "#18191c"
PANEL_BACKGROUND = "#22242a"
PANEL_BORDER = "#343741"
TEXT_PRIMARY = "#ebecf0"
TEXT_SECONDARY = "#aeb4c0"
ACCENT = "#508cdc"


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
    app.setStyleSheet(
        f"""
        QMainWindow {{
            background: {BACKGROUND};
        }}
        QListWidget {{
            background: {PANEL_BACKGROUND};
            border: 0;
            color: {TEXT_PRIMARY};
            padding: 10px 6px;
        }}
        QListWidget::item {{
            min-height: 34px;
            padding: 6px 12px;
            border-radius: 6px;
        }}
        QListWidget::item:selected {{
            background: {ACCENT};
            color: white;
        }}
        QStackedWidget, QWidget {{
            background: {BACKGROUND};
            color: {TEXT_PRIMARY};
        }}
        QDockWidget {{
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
            color: {TEXT_PRIMARY};
        }}
        QDockWidget::title {{
            background: {PANEL_BACKGROUND};
            border: 1px solid {PANEL_BORDER};
            padding: 7px 10px;
        }}
        QToolButton {{
            background: {PANEL_BACKGROUND};
            border: 1px solid {PANEL_BORDER};
            border-radius: 6px;
            min-width: 34px;
            min-height: 34px;
        }}
        QToolButton:hover {{
            border-color: {ACCENT};
        }}
        QSlider::groove:horizontal {{
            background: {PANEL_BORDER};
            border-radius: 3px;
            height: 6px;
        }}
        QSlider::sub-page:horizontal {{
            background: {ACCENT};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {TEXT_PRIMARY};
            border: 1px solid {PANEL_BORDER};
            border-radius: 6px;
            margin: -4px 0;
            width: 12px;
        }}
        #panelTitle {{
            font-size: 26px;
            font-weight: 600;
        }}
        #panelSubtitle, #dockEmptyText, #playerTrackMeta, #playerTime {{
            color: {TEXT_SECONDARY};
        }}
        #dockTitle, #playerTrackTitle {{
            font-weight: 600;
        }}
        """
    )
