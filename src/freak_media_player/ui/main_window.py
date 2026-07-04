"""Main application window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from freak_media_player import __version__
from freak_media_player.services.equalizer_service import EqualizerService
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.ui.constants import (
    WINDOW_MINIMUM_HEIGHT,
    WINDOW_MINIMUM_WIDTH,
    WINDOW_START_HEIGHT,
    WINDOW_START_WIDTH,
)
from freak_media_player.ui.navigation import NavigationViewModel
from freak_media_player.widgets.player_bar import PlayerBar
from freak_media_player.widgets.shell import ShellContent
from freak_media_player.widgets.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(
        self,
        playback_service: PlaybackService,
        local_library_service: LocalLibraryService,
        equalizer_service: EqualizerService,
    ) -> None:
        super().__init__()
        self._playback_service = playback_service
        self._local_library_service = local_library_service
        self._equalizer_service = equalizer_service
        self._navigation = NavigationViewModel()
        self._content = ShellContent(
            local_library_service=self._local_library_service,
            playback_service=self._playback_service,
            equalizer_service=self._equalizer_service,
        )
        self.setWindowTitle(f"Freak Media Player {__version__}")
        self.setMinimumSize(WINDOW_MINIMUM_WIDTH, WINDOW_MINIMUM_HEIGHT)
        self.resize(WINDOW_START_WIDTH, WINDOW_START_HEIGHT)
        self._build_layout()

    def _build_layout(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        sidebar = Sidebar(navigation=self._navigation)
        sidebar.section_selected.connect(self._content.set_section)
        splitter.addWidget(sidebar)
        splitter.addWidget(self._content)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        root_layout.addWidget(splitter, 1)
        root_layout.addWidget(PlayerBar(playback_service=self._playback_service))

        self.setCentralWidget(root)
        status_bar = QStatusBar()
        status_bar.showMessage(f"Freak Media Player {__version__}")
        self.setStatusBar(status_bar)
