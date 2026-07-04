"""Local track import and playback panel."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from freak_media_player.models.media import Track
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.playback_service import PlaybackService

TRACK_ID_ROLE = Qt.ItemDataRole.UserRole


class LocalTracksPanel(QWidget):
    def __init__(
        self,
        title: str,
        local_library_service: LocalLibraryService,
        playback_service: PlaybackService,
    ) -> None:
        super().__init__()
        self._title = title
        self._local_library_service = local_library_service
        self._playback_service = playback_service
        self._tracks: dict[str, Track] = {}
        self._table = QTableWidget()
        self.setAcceptDrops(True)
        self._build_layout()
        self.refresh()

    def refresh(self) -> None:
        tracks = self._local_library_service.list_tracks()
        self._tracks = {track.id: track for track in tracks}
        self._table.setRowCount(len(tracks))
        for row, track in enumerate(tracks):
            self._set_row(row, track)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._event_has_local_paths(event):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = self._paths_from_event(event)
        if paths:
            self._import_paths(paths)
            event.acceptProposedAction()

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel(self._title)
        title.setObjectName("panelTitle")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(
            self._build_button(
                QStyle.StandardPixmap.SP_FileIcon,
                "Import files",
                self._select_files,
            )
        )
        header.addWidget(
            self._build_button(
                QStyle.StandardPixmap.SP_DirIcon,
                "Import folder",
                self._select_folder,
            )
        )

        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Title", "Artist", "Source"])
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.itemDoubleClicked.connect(self._play_selected_item)

        layout.addLayout(header)
        layout.addWidget(self._table, 1)

    def _build_button(
        self,
        icon: QStyle.StandardPixmap,
        tooltip: str,
        handler: Callable[[], object],
    ) -> QToolButton:
        button = QToolButton()
        button.setIcon(self.style().standardIcon(icon))
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(handler)
        return button

    def _select_files(self) -> None:
        filters = "Audio files (" + " ".join(f"*{ext}" for ext in self._extensions()) + ")"
        files, _selected_filter = QFileDialog.getOpenFileNames(
            self,
            "Import files",
            str(Path.home()),
            filters,
        )
        self._import_paths([Path(file) for file in files])

    def _select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Import folder", str(Path.home()))
        if folder:
            self._import_paths([Path(folder)])

    def _import_paths(self, paths: list[Path]) -> None:
        imported = self._local_library_service.import_paths(paths)
        if imported:
            self.refresh()

    def _set_row(self, row: int, track: Track) -> None:
        title = QTableWidgetItem(track.title)
        title.setData(TRACK_ID_ROLE, track.id)
        artist = QTableWidgetItem(track.artist.name)
        source = QTableWidgetItem(track.provider_identity.item_id)
        self._table.setItem(row, 0, title)
        self._table.setItem(row, 1, artist)
        self._table.setItem(row, 2, source)

    def _play_selected_item(self, item: QTableWidgetItem) -> None:
        title_item = self._table.item(item.row(), 0)
        if title_item is None:
            return
        track_id = title_item.data(TRACK_ID_ROLE)
        if not isinstance(track_id, str):
            return
        track = self._tracks.get(track_id)
        if track is not None:
            self._playback_service.enqueue_and_play(track)

    def _extensions(self) -> tuple[str, ...]:
        return self._local_library_service.supported_extensions()

    def _event_has_local_paths(self, event: QDragEnterEvent | QDropEvent) -> bool:
        mime_data = event.mimeData()
        return mime_data.hasUrls() and bool(self._paths_from_event(event))

    def _paths_from_event(self, event: QDragEnterEvent | QDropEvent) -> list[Path]:
        paths: list[Path] = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                paths.append(Path(url.toLocalFile()))
        return paths
