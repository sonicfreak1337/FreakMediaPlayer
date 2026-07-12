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
    "background": "#050505",
    "panel_background": "#0b0b0b",
    "panel_sunken": "#030303",
    "panel_border": "#2b2b2b",
    "header_background": "#090909",
    "header_highlight": "#67140b",
    "text_primary": "#dddddd",
    "text_secondary": "#999999",
    "display": "#ff9a00",
    "accent": "#ff2a12",
    "highlight": "#ff8700",
    "playing_row_background": "#54140b",
    "playing_row_text": "#ffd6cb",
    "artwork_background": "#050505",
    "artwork_border": "#d52615",
    "spectrum_active": "#ff8700",
    "spectrum_inactive": "#571208",
    "graph_background": "#080808",
    "graph_band": "#ff4a12",
    "graph_band_disabled": "#4a241c",
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
    """Return the black-metal Fastilicious skin from the supplied mockup."""
    replacements = {
        # Semantic Freaky colors.
        "#01081a": "#050505",
        "#050d20": "#0b0b0b",
        "#000410": "#030303",
        "#29384f": "#2b2b2b",
        "#071127": "#090909",
        "#123a88": "#67140b",
        "#e6e8f3": "#dddddd",
        "#8e9ab1": "#999999",
        "#4d91ff": "#ff9a00",
        "#2b83ff": "#ff2a12",
        "#ffc126": "#ff8700",
        "#503900": "#54140b",
        "#ffd45c": "#ffd6cb",
        # Navy surfaces become layered graphite; blue chrome becomes hot metal.
        "#061026": "#111111",
        "#020818": "#050505",
        "#173e78": "#3a0d08",
        "#1d2e4c": "#292929",
        "#14213a": "#1b1b1b",
        "#07142d": "#111111",
        "#3d8dff": "#ff4b1a",
        "#1155c0": "#a91c0d",
        "#4b89ee": "#ff7a00",
        "#397bd5": "#e83a16",
        "#5a8fe8": "#ff9a00",
        "#afc8fa": "#ffc065",
        "#263650": "#292929",
        "#071126": "#101010",
        "#030919": "#050505",
        "#030916": "#050505",
        "#030a18": "#070707",
        "#081329": "#121212",
        "#030b1c": "#060606",
        "#09152b": "#151515",
        "#071123": "#090909",
        "#24344e": "#353535",
        "#202f48": "#303030",
        "#2a3a55": "#353535",
        "#25334a": "#292929",
        "#0c1930": "#181818",
        "#0a162b": "#151515",
        "#020714": "#040404",
        "#030918": "#050505",
        "#040c1c": "#080808",
        "#07142a": "#0b0b0b",
        "#071022": "#0c0c0c",
        "#274263": "#3a3a3a",
        "#3c5275": "#464646",
        "#638aca": "#ff5b22",
        "#74a0ff": "#ff5b22",
        "#9cb8ec": "#b8b8b8",
        "#75a6ff": "#ff4a18",
    }
    stylesheet = freaky_stylesheet()
    for source, target in replacements.items():
        stylesheet = stylesheet.replace(source, target)
    return stylesheet + """
        QMainWindow#mainWindow {
            background: #050505;
            border: 1px solid #343434;
        }
        QDockWidget {
            background: #090909;
            border: 1px solid #292929;
            border-radius: 7px;
        }
        #appTitleBar, #moduleTitleBar, QStatusBar#appStatusBar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #171717, stop:0.16 #0d0d0d, stop:1 #050505);
        }
        #appTitleBar {
            border-top: 1px solid #353535;
            border-bottom: 1px solid #292929;
        }
        #moduleTitleBar {
            border-bottom: 1px solid #272727;
        }
        #playerPanel {
            background: qradialgradient(cx:0.52, cy:0.35, radius:0.9,
                stop:0 #151515, stop:0.58 #090909, stop:1 #030303);
        }
        #transportSurface {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1b1b1b, stop:0.18 #0c0c0c, stop:0.8 #050505, stop:1 #151515);
            border: 1px solid #3c3c3c;
            border-radius: 14px;
        }
        QToolButton#transportButton, QToolButton#modeButton,
        QToolButton#shuffleButton, QToolButton#utilityButton,
        QToolButton#flatPlayerButton, QToolButton#moduleChromeButton,
        QToolButton#skinUtilityButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1e1e1e, stop:0.14 #111111, stop:1 #050505);
            border: 1px solid #343434;
            color: #c8c8c8;
        }
        QToolButton#transportButton:hover, QToolButton#modeButton:hover,
        QToolButton#shuffleButton:hover, QToolButton#utilityButton:hover,
        QToolButton#flatPlayerButton:hover, QToolButton#moduleChromeButton:hover,
        QToolButton#skinUtilityButton:hover {
            border-color: #ff4a19;
            color: #ff9200;
        }
        QToolButton#playPauseButton {
            background: qradialgradient(cx:0.5, cy:0.42, radius:0.62,
                stop:0 #b32612, stop:0.48 #4d0903, stop:0.7 #140100, stop:1 #050505);
            border: 2px solid #ff3c18;
            border-radius: 36px;
            color: #ff9a00;
            font-size: 31px;
        }
        QToolButton#playPauseButton:hover {
            background: qradialgradient(cx:0.5, cy:0.42, radius:0.62,
                stop:0 #e94017, stop:0.5 #6a1006, stop:1 #080808);
            border-color: #ff7a22;
        }
        QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
            background: #070707;
            border: 1px solid #353535;
            color: #d8d8d8;
            selection-background-color: #6b170b;
        }
        QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QLineEdit:hover {
            border-color: #c72b16;
        }
        QHeaderView::section {
            background: #0d0d0d;
            border-color: #292929;
            color: #bdbdbd;
        }
        QTableView {
            background: #070707;
            alternate-background-color: #0d0d0d;
            border-color: #292929;
            gridline-color: #252525;
        }
        QTableView::item:selected {
            background: #5b140a;
            color: #f1f1f1;
        }
        #panelSummary {
            background: #090909;
            border-top-color: #292929;
        }
        #appBrandFreak, #moduleTitle, #panelTitle, #visualizerLive,
        #playerArtist, #readyStatus {
            color: #ff3217;
        }
        #playerTime, #skinSelectorLabel, #compactLabel {
            color: #a3a3a3;
        }
        QSlider::groove:horizontal {
            background: #111111;
            border-color: #292929;
        }
        QSlider::sub-page:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #a91609, stop:0.58 #ff3515, stop:1 #ff9100);
        }
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #eeeeee, stop:0.45 #a8a8a8, stop:1 #555555);
            border: 1px solid #f0f0f0;
        }
        QSlider::groove:vertical {
            background: #080808;
            border-color: #303030;
        }
        QSlider::sub-page:vertical, QSlider::add-page:vertical {
            background: #ff3216;
        }
        QSlider::handle:vertical {
            background: #111111;
            border: 1px solid #ff5b21;
        }
        QCheckBox::indicator:checked {
            background: #ff8700;
            border-color: #ffb14c;
        }
        #visualizerControls {
            background: #080808;
            border-color: #2c2c2c;
        }
        QToolButton#visualizerModeButton {
            background: #080808;
            border-color: #303030;
            color: #bcbcbc;
        }
        QToolButton#visualizerModeButton:checked {
            background: #150503;
            border-color: #ff3216;
            color: #ff4a19;
        }
        QStatusBar#appStatusBar {
            border: 1px solid #292929;
            border-radius: 6px;
        }
        QToolButton#windowButton:hover {
            background: #222222;
        }
        QToolButton#windowCloseButton:hover {
            background: #8f160b;
        }
        QComboBox#skinSelector:hover {
            border-color: #ff3c19;
        }
        QMainWindow::separator {
            background: #121212;
            width: 6px;
            height: 6px;
        }
        QMainWindow::separator:hover {
            background: #4d120a;
        }
        QDockWidget {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #121212, stop:0.08 #090909, stop:1 #050505);
            border: 1px solid #3b3b3b;
            border-radius: 7px;
        }
        #moduleTitleBar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1d1d1d, stop:0.18 #101010, stop:1 #060606);
            border-top: 1px solid #424242;
            border-bottom: 1px solid #323232;
        }
        #appBrandFreak {
            color: #ff8700;
        }
        #moduleTitle, #panelTitle, #visualizerLive, #playerArtist, #readyStatus {
            color: #ff3217;
        }
        QToolButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #202020, stop:0.14 #131313, stop:1 #070707);
            border: 1px solid #3b3b3b;
            border-radius: 5px;
            color: #c6c6c6;
        }
        QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2a211e, stop:0.18 #1d100c, stop:1 #090706);
            border-color: #d43a1c;
            color: #ff9200;
        }
        QToolButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #5e180d, stop:0.3 #2d0904, stop:1 #100302);
            border-color: #ff421c;
            color: #ff9400;
        }
        QToolButton:disabled {
            background: #0a0a0a;
            border-color: #242424;
            color: #595959;
        }
        QToolButton#modeButton:checked, QToolButton#shuffleButton:checked {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #64180d, stop:0.32 #300904, stop:1 #0e0201);
            border-color: #ff471d;
            color: #ff9400;
        }
        QToolButton#utilityButton:disabled {
            background: #090909;
            border-color: #252525;
            color: #555555;
        }
        QMenu {
            background: #0b0b0b;
            border: 1px solid #3b3b3b;
            color: #dddddd;
        }
        QMenu::item:selected {
            background: #5c150b;
            color: #ffffff;
        }
        QComboBox QAbstractItemView {
            background: #080808;
            border: 1px solid #3b3b3b;
            color: #dddddd;
            selection-background-color: #5c150b;
        }
        QTableWidget {
            background: #060606;
            alternate-background-color: #0b0b0b;
            border: 0;
            color: #d7d7d7;
            gridline-color: #292929;
            selection-background-color: #4b1008;
            selection-color: #f2f2f2;
        }
        QTableWidget::item {
            border-bottom: 1px solid #272727;
            padding: 4px 7px;
        }
        QTableWidget::item:selected {
            background: #4b1008;
            border-top: 1px solid #b52c15;
            border-bottom: 1px solid #b52c15;
            color: #f2f2f2;
        }
        QHeaderView::section {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #171717, stop:1 #090909);
            border: 0;
            border-right: 1px solid #303030;
            border-bottom: 1px solid #3a3a3a;
            color: #c8c8c8;
        }
        #panelSummary {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #111111, stop:1 #070707);
            border-top: 1px solid #303030;
            color: #a8a8a8;
        }
        QScrollBar:vertical {
            background: #080808;
            border-left: 1px solid #242424;
            width: 11px;
            margin: 0;
        }
        QScrollBar::handle:vertical {
            background: #555555;
            border: 1px solid #777777;
            border-radius: 4px;
            min-height: 24px;
        }
        QScrollBar::handle:vertical:hover {
            background: #c9361a;
            border-color: #ff5a25;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: transparent;
            border: 0;
            height: 0;
        }
        QToolTip {
            background: #141414;
            border: 1px solid #d43a1c;
            color: #f0f0f0;
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
