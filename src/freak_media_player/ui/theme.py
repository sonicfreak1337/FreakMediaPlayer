"""Built-in Freaky and Fastilicious skin stylesheets."""

from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

BACKGROUND = "#01081a"
PANEL_BACKGROUND = "#050d20"
PANEL_SUNKEN = "#000410"
PANEL_BORDER = "#29384f"
HEADER_BACKGROUND = "#071127"
HEADER_HIGHLIGHT = "#123a88"
TEXT_PRIMARY = "#e6e8f3"
TEXT_SECONDARY = "#8e9ab1"
DISPLAY_GREEN = "#4d91ff"
ACCENT = "#2b83ff"
AMBER = "#ffc126"
PLAYING_ROW_BACKGROUND = "#503900"
PLAYING_ROW_TEXT = "#ffd45c"

FREAKY_COLORS = {
    "background": BACKGROUND,
    "panel_background": PANEL_BACKGROUND,
    "panel_sunken": PANEL_SUNKEN,
    "panel_border": PANEL_BORDER,
    "header_background": HEADER_BACKGROUND,
    "header_highlight": HEADER_HIGHLIGHT,
    "text_primary": TEXT_PRIMARY,
    "text_secondary": TEXT_SECONDARY,
    "display": DISPLAY_GREEN,
    "accent": ACCENT,
    "highlight": AMBER,
    "playing_row_background": PLAYING_ROW_BACKGROUND,
    "playing_row_text": PLAYING_ROW_TEXT,
    "artwork_background": "#020714",
    "artwork_border": "#1f4b91",
    "spectrum_active": "#f6b91d",
    "spectrum_inactive": "#16233f",
    "graph_background": "#030b1b",
    "graph_band": "#287cff",
    "graph_band_disabled": "#29364b",
}

FASTILICIOUS_COLORS = {
    "background": "#100b17",
    "panel_background": "#19111f",
    "panel_sunken": "#09070d",
    "panel_border": "#56364f",
    "header_background": "#25152d",
    "header_highlight": "#7d244e",
    "text_primary": "#fff4f8",
    "text_secondary": "#c5a9b8",
    "display": "#2ee0cf",
    "accent": "#ff3864",
    "highlight": "#ff5a7d",
    "playing_row_background": "#561b36",
    "playing_row_text": "#ffb2c4",
    "artwork_background": "#0d0712",
    "artwork_border": "#ff3864",
    "spectrum_active": "#2ee0cf",
    "spectrum_inactive": "#402038",
    "graph_background": "#150c1b",
    "graph_band": "#2ee0cf",
    "graph_band_disabled": "#503044",
}


def freaky_stylesheet() -> str:
    """Return the original 0.7 design, now named Freaky."""
    return f"""
        * {{
            font-family: "Segoe UI";
            font-size: 11px;
            color: {TEXT_PRIMARY};
        }}
        QMainWindow#mainWindow {{
            background: {BACKGROUND};
            border: 1px solid #1a2b49;
        }}
        QMainWindow::separator {{
            background: {BACKGROUND};
            width: 8px;
            height: 8px;
        }}
        QMainWindow::separator:hover {{
            background: #173e78;
        }}
        #appTitleBar {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #061026, stop:1 #020818);
            border-bottom: 1px solid #1d2e4c;
        }}
        #appBrand {{
            color: #e8eaf2;
            font-size: 17px;
        }}
        #appBrandFreak {{
            color: {AMBER};
            font-size: 17px;
            font-weight: 700;
        }}
        #appVersion {{
            color: #b6bdce;
            font-size: 16px;
        }}
        #skinSelectorLabel {{
            color: {TEXT_SECONDARY};
            font-size: 9px;
            font-weight: 700;
        }}
        QComboBox#skinSelector {{
            background: #020818;
            border: 1px solid #2b3c57;
            border-radius: 4px;
            color: {TEXT_PRIMARY};
            min-height: 24px;
            padding: 2px 8px;
        }}
        QComboBox#skinSelector:hover {{
            border-color: {AMBER};
        }}
        QToolButton#skinUtilityButton {{
            background: transparent;
            border: 1px solid #2b3b56;
            border-radius: 4px;
            color: #9cb8ec;
            min-width: 0;
            min-height: 0;
            padding: 0;
        }}
        QToolButton#skinUtilityButton:hover {{
            border-color: {AMBER};
            color: {AMBER};
        }}
        QToolButton#windowButton {{
            background: transparent;
            border: 0;
            color: #aeb7ca;
            font-size: 18px;
        }}
        QToolButton#windowButton:hover {{
            background: #14213a;
            color: white;
        }}
        QToolButton#windowCloseButton:hover {{
            background: #a52a3a;
        }}
        QDockWidget {{
            background: {PANEL_BACKGROUND};
            border: 1px solid {PANEL_BORDER};
            border-radius: 8px;
            color: {TEXT_PRIMARY};
        }}
        #moduleTitleBar {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #081329, stop:1 #030b1c);
            border-bottom: 1px solid #25334a;
        }}
        #moduleIcon {{
            color: #74a0ff;
            font-size: 18px;
            font-weight: 700;
        }}
        #moduleTitle {{
            color: {AMBER};
            font-size: 13px;
            font-weight: 700;
        }}
        QToolButton#moduleChromeButton {{
            min-width: 0;
            min-height: 0;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0c1930, stop:1 #030916);
            border: 1px solid #2a3a55;
            border-radius: 4px;
            color: #9cb8ec;
            font-size: 15px;
        }}
        QToolButton#moduleChromeButton:hover {{
            border-color: #4c8cf5;
            color: {AMBER};
        }}
        #playerPanel {{
            background: qradialgradient(cx:0.44, cy:0.38, radius:0.85,
                stop:0 #07142d, stop:0.65 #020a1b, stop:1 #010612);
        }}
        #playerSeparator {{
            background: #1d2f4d;
            border: 0;
        }}
        #playerTrackTitle {{
            color: #f0f1f6;
            font-size: 17px;
            font-weight: 600;
        }}
        #playerArtist {{
            color: {AMBER};
            font-size: 13px;
            font-weight: 600;
        }}
        #playerTrackMeta, #playerTime {{
            color: {TEXT_SECONDARY};
            font-size: 11px;
        }}
        #transportSurface {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #09152b, stop:0.52 #030a18, stop:1 #071123);
            border: 1px solid #24344e;
            border-radius: 10px;
        }}
        QToolButton#transportButton, QToolButton#modeButton, QToolButton#shuffleButton,
        QToolButton#utilityButton, QToolButton#flatPlayerButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0a162b, stop:1 #020714);
            border: 1px solid #202f48;
            border-radius: 7px;
            color: #d8deeb;
            min-width: 42px;
            min-height: 38px;
            padding: 3px;
            font-size: 14px;
        }}
        QToolButton#transportButton:hover, QToolButton#modeButton:hover,
        QToolButton#shuffleButton:hover,
        QToolButton#utilityButton:hover, QToolButton#flatPlayerButton:hover {{
            border-color: #397bd5;
            color: {AMBER};
        }}
        QToolButton#modeButton, QToolButton#shuffleButton {{
            color: {AMBER};
            font-size: 9px;
        }}
        QToolButton#modeButton:checked, QToolButton#shuffleButton:checked {{
            background: #0d2551;
            border-color: {AMBER};
            color: {AMBER};
        }}
        QToolButton#playPauseButton {{
            background: qradialgradient(cx:0.5, cy:0.45, radius:0.6,
                stop:0 #3d8dff, stop:0.48 #1155c0,
                stop:0.55 #06152d, stop:0.72 #101a2b, stop:1 #020713);
            border: 2px solid #8aaef0;
            border-radius: 36px;
            color: white;
            font-size: 25px;
            font-weight: 700;
        }}
        QToolButton#playPauseButton:hover {{
            border-color: {AMBER};
        }}
        QToolButton#utilityButton:disabled {{
            color: #55627a;
            border-color: #17243a;
        }}
        QMenu {{
            background: #071126;
            border: 1px solid #344765;
            padding: 5px;
        }}
        QMenu::item {{
            padding: 7px 28px 7px 10px;
        }}
        QMenu::item:selected {{
            background: #153b7b;
            color: white;
        }}
        QToolButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0b172d, stop:1 #030916);
            border: 1px solid #2b3b56;
            border-radius: 4px;
            color: #86a9ed;
            min-width: 28px;
            min-height: 25px;
            padding: 2px 5px;
        }}
        QToolButton:hover {{
            border-color: #4b89ee;
            color: {AMBER};
        }}
        QToolButton:checked {{
            background: #123b83;
            border-color: #6ea6ff;
            color: white;
        }}
        QComboBox, QSpinBox, QDoubleSpinBox {{
            background: #020818;
            border: 1px solid #2b3c57;
            border-radius: 4px;
            color: #d8deec;
            padding: 3px 8px;
            min-height: 23px;
        }}
        QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
            border-color: #4b86e8;
        }}
        QComboBox QAbstractItemView {{
            background: #050d20;
            border: 1px solid #344867;
            color: #dce2ef;
            selection-background-color: #123b83;
        }}
        QTableWidget {{
            background: {PANEL_SUNKEN};
            alternate-background-color: #020817;
            border: 0;
            color: #d7dbe6;
            gridline-color: #0d1c33;
            selection-background-color: #071225;
            selection-color: #e1e5ef;
            font-size: 11px;
            outline: 0;
        }}
        QTableWidget::item {{
            border-bottom: 1px solid #09162a;
            padding: 4px 7px;
        }}
        QTableWidget::item:selected {{
            background: #071225;
            border-top: 1px solid #3b4a65;
            border-bottom: 1px solid #3b4a65;
            color: #e1e5ef;
        }}
        QHeaderView::section {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #081227, stop:1 #030a18);
            border: 0;
            border-right: 1px solid #16243a;
            border-bottom: 1px solid #263650;
            color: #c8ceda;
            padding: 5px 7px;
            font-size: 11px;
            font-weight: 500;
        }}
        QSlider::groove:horizontal {{
            background: #111a29;
            border: 1px solid #25334a;
            border-radius: 3px;
            height: 6px;
        }}
        QSlider::sub-page:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {AMBER}, stop:1 #f4cf48);
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: #5a8fe8;
            border: 1px solid #afc8fa;
            border-radius: 7px;
            margin: -5px 0;
            width: 14px;
        }}
        QSlider::groove:vertical {{
            background: #07142a;
            border: 1px solid #274263;
            border-radius: 2px;
            width: 7px;
        }}
        QSlider::handle:vertical {{
            background: #071022;
            border: 1px solid #638aca;
            border-radius: 3px;
            height: 15px;
            margin: 0 -8px;
        }}
        QCheckBox {{
            color: #cbd2df;
            spacing: 6px;
        }}
        QCheckBox::indicator {{
            width: 15px;
            height: 15px;
            background: #020818;
            border: 1px solid #3c5275;
            border-radius: 3px;
        }}
        QCheckBox::indicator:checked {{
            background: {AMBER};
            border-color: #ffe08a;
        }}
        #panelTitle {{
            color: {AMBER};
            font-size: 13px;
            font-weight: 700;
        }}
        #panelSubtitle, #dockEmptyText {{
            color: {TEXT_SECONDARY};
        }}
        #panelSummary {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #071126, stop:1 #030919);
            border-top: 1px solid #263650;
            color: #aab2c1;
        }}
        #compactLabel {{
            color: #8e9bb5;
            font-size: 9px;
            font-weight: 600;
        }}
        #visualizerControls {{
            background: #040c1c;
            border: 1px solid #263650;
            border-radius: 6px;
        }}
        #visualizerModes {{
            background: transparent;
        }}
        QToolButton#visualizerModeButton {{
            background: #030918;
            border: 1px solid #263650;
            border-radius: 4px;
            color: #aeb9cf;
            min-height: 26px;
            font-size: 10px;
        }}
        QToolButton#visualizerModeButton:checked {{
            border-color: {AMBER};
            color: {AMBER};
            background: #0a1427;
        }}
        #visualizerLive {{
            color: {AMBER};
            font-size: 10px;
            font-weight: 700;
        }}
        QStatusBar#appStatusBar {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #071126, stop:1 #020817);
            border: 1px solid #263650;
            border-radius: 6px;
            color: #aab3c4;
            min-height: 34px;
            padding: 0 10px;
        }}
        QStatusBar#appStatusBar::item {{
            border: 0;
        }}
        #readyStatus {{ color: #75a6ff; }}
        #queueStatus {{ color: #8b95a9; padding-left: 360px; }}
        """


def fastilicious_stylesheet() -> str:
    """Return the provisional Fastilicious racing-console mockup."""
    replacements = {
        "#01081a": "#100b17",
        "#050d20": "#19111f",
        "#000410": "#09070d",
        "#29384f": "#56364f",
        "#071127": "#25152d",
        "#123a88": "#7d244e",
        "#e6e8f3": "#fff4f8",
        "#8e9ab1": "#c5a9b8",
        "#4d91ff": "#2ee0cf",
        "#2b83ff": "#ff3864",
        "#ffc126": "#ff5a7d",
        "#503900": "#561b36",
        "#ffd45c": "#ffb2c4",
        "#061026": "#32152e",
        "#020818": "#0d0712",
        "#173e78": "#8d2857",
        "#1d2e4c": "#63364f",
        "#14213a": "#402038",
        "#07142d": "#2a1227",
        "#3d8dff": "#ff5578",
        "#1155c0": "#b62055",
        "#4b89ee": "#2ee0cf",
        "#397bd5": "#ff7893",
        "#5a8fe8": "#2ee0cf",
        "#afc8fa": "#b7fff8",
    }
    stylesheet = freaky_stylesheet()
    for source, target in replacements.items():
        stylesheet = stylesheet.replace(source, target)
    return stylesheet + """
        QDockWidget, #transportSurface, QStatusBar#appStatusBar {
            border-radius: 2px;
        }
        #appTitleBar {
            border-bottom: 2px solid #ff3864;
        }
        #appBrandFreak, #moduleTitle, #panelTitle, #visualizerLive {
            color: #2ee0cf;
        }
        QToolButton#playPauseButton {
            border-color: #ff7893;
        }
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ff3864, stop:1 #2ee0cf);
        }
    """


def build_palette(colors: Mapping[str, str]) -> QPalette:
    """Build a Qt palette from a skin's semantic color roles."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(colors["background"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["text_primary"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(colors["panel_sunken"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors["panel_background"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(colors["text_primary"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(colors["panel_background"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["text_primary"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["header_highlight"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors["text_primary"]))
    return palette


def apply_dark_theme(app: QApplication) -> None:
    """Compatibility wrapper for callers that still request the old dark theme."""
    app.setPalette(build_palette(FREAKY_COLORS))
    app.setStyleSheet(freaky_stylesheet())
