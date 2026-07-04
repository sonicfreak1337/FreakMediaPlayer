"""Qt application bootstrap."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from freak_media_player.app.bootstrap import build_app_context
from freak_media_player.ui.main_window import MainWindow
from freak_media_player.ui.theme import apply_dark_theme


def run_application() -> int:
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Freak Media Player")
    apply_dark_theme(qt_app)

    context = build_app_context()
    window = MainWindow(
        playback_service=context.playback_service,
        local_library_service=context.local_library_service,
        equalizer_service=context.equalizer_service,
    )
    window.show()

    return qt_app.exec()
