"""Application theme setup."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

BACKGROUND = "#0a0b0f"
PANEL_BACKGROUND = "#161826"
PANEL_SUNKEN = "#030407"
PANEL_BORDER = "#50536b"
HEADER_BACKGROUND = "#232456"
HEADER_HIGHLIGHT = "#3135a4"
TEXT_PRIMARY = "#d7d8e8"
TEXT_SECONDARY = "#8f94b2"
DISPLAY_GREEN = "#19ff54"
ACCENT = "#4d54d8"
AMBER = "#e6c34c"
PLAYING_ROW_BACKGROUND = "#173d27"
PLAYING_ROW_TEXT = "#f1d85a"


def apply_dark_theme(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(10, 11, 15))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(215, 216, 232))
    palette.setColor(QPalette.ColorRole.Base, QColor(3, 4, 7))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 22, 32))
    palette.setColor(QPalette.ColorRole.Text, QColor(25, 255, 84))
    palette.setColor(QPalette.ColorRole.Button, QColor(22, 24, 38))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(215, 216, 232))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(49, 53, 164))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    app.setStyleSheet(
        f"""
        QMainWindow {{
            background: {BACKGROUND};
        }}
        QListWidget {{
            background: {PANEL_BACKGROUND};
            border-right: 1px solid {PANEL_BORDER};
            color: {DISPLAY_GREEN};
            font-size: 12px;
            padding: 6px 4px;
        }}
        QListWidget::item {{
            min-height: 24px;
            padding: 4px 8px;
            border: 1px solid transparent;
        }}
        QListWidget::item:selected {{
            background: {HEADER_HIGHLIGHT};
            border-color: {PANEL_BORDER};
            color: white;
        }}
        QStackedWidget, QWidget {{
            background: {BACKGROUND};
            color: {TEXT_PRIMARY};
        }}
        QStatusBar {{
            background: {PANEL_BACKGROUND};
            border-top: 1px solid {PANEL_BORDER};
            color: {DISPLAY_GREEN};
            font-size: 11px;
        }}
        QSplitter::handle {{
            background: {PANEL_BORDER};
            width: 2px;
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
            color: {TEXT_PRIMARY};
            min-width: 26px;
            min-height: 24px;
            padding: 2px;
        }}
        QToolButton:hover {{
            border-color: {DISPLAY_GREEN};
            color: {DISPLAY_GREEN};
        }}
        QToolButton#shuffleButton:checked {{
            background: {DISPLAY_GREEN};
            border-color: {AMBER};
            color: {PANEL_SUNKEN};
            font-weight: 600;
        }}
        #collapsibleHeader {{
            background: {HEADER_BACKGROUND};
            border: 1px solid {PANEL_BORDER};
            color: white;
            font-size: 13px;
            font-weight: 600;
            min-height: 26px;
            padding: 2px 8px;
            text-align: left;
        }}
        #collapsibleHeader:hover,
        #collapsibleHeader:checked {{
            background: {HEADER_HIGHLIGHT};
            border-color: {DISPLAY_GREEN};
        }}
        QComboBox {{
            background: {PANEL_SUNKEN};
            border: 1px solid {PANEL_BORDER};
            color: {DISPLAY_GREEN};
            padding: 3px 8px;
            min-height: 22px;
        }}
        QComboBox QAbstractItemView {{
            background: {PANEL_SUNKEN};
            border: 1px solid {PANEL_BORDER};
            color: {DISPLAY_GREEN};
            selection-background-color: {HEADER_HIGHLIGHT};
        }}
        QTableWidget {{
            background: {PANEL_SUNKEN};
            alternate-background-color: #07090f;
            border: 1px solid {PANEL_BORDER};
            color: {DISPLAY_GREEN};
            gridline-color: #24283e;
            selection-background-color: {HEADER_HIGHLIGHT};
            selection-color: white;
            font-size: 12px;
        }}
        QHeaderView::section {{
            background: {HEADER_BACKGROUND};
            border: 0;
            border-right: 1px solid {PANEL_BORDER};
            color: {TEXT_PRIMARY};
            padding: 4px 6px;
            font-size: 12px;
            font-weight: 600;
        }}
        QSlider::groove:horizontal {{
            background: {PANEL_BORDER};
            border: 1px solid #202234;
            border-radius: 2px;
            height: 8px;
        }}
        QSlider::sub-page:horizontal {{
            background: {AMBER};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background: {DISPLAY_GREEN};
            border: 1px solid #07140a;
            margin: -6px 0;
            width: 14px;
        }}
        QSlider::groove:vertical {{
            background: {PANEL_SUNKEN};
            border: 1px solid {PANEL_BORDER};
            border-radius: 2px;
            width: 10px;
        }}
        QSlider::sub-page:vertical {{
            background: {AMBER};
            border-radius: 2px;
        }}
        QSlider::add-page:vertical {{
            background: #222537;
            border-radius: 2px;
        }}
        QSlider::handle:vertical {{
            background: {DISPLAY_GREEN};
            border: 1px solid #07140a;
            height: 12px;
            margin: 0 -8px;
        }}
        #panelTitle {{
            background: {HEADER_BACKGROUND};
            border: 1px solid {PANEL_BORDER};
            color: white;
            font-size: 16px;
            font-weight: 600;
            padding: 4px 8px;
        }}
        #panelSubtitle, #dockEmptyText, #playerTrackMeta, #playerTime {{
            color: {TEXT_SECONDARY};
        }}
        #dockTitle, #playerTrackTitle {{
            font-weight: 600;
        }}
        #playerTrackTitle {{
            color: {DISPLAY_GREEN};
        }}
        """
    )
