"""Local track import and playback panel."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QKeySequence, QShortcut
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
from freak_media_player.widgets.track_table import TRACK_ID_ROLE, TrackTableWidget

TITLE_COLUMN = 0
ARTIST_COLUMN = 1
SOURCE_COLUMN = 2


class LocalTracksPanel(QWidget):
    tracks_add_requested = Signal(object)

    def __init__(
        self,
        title: str,
        local_library_service: LocalLibraryService,
    ) -> None:
        super().__init__()
        self._title = title
        self._local_library_service = local_library_service
        self._table = TrackTableWidget()
        self._delete_shortcut = QShortcut(QKeySequence.StandardKey.Delete, self._table)
        self.setAcceptDrops(True)
        self._build_layout()
        self._delete_shortcut.activated.connect(self._remove_selected_track)
        self.refresh()

    def refresh(self) -> None:
        tracks = self._local_library_service.list_tracks()
        sort_column = self._table.horizontalHeader().sortIndicatorSection()
        sort_order = self._table.horizontalHeader().sortIndicatorOrder()
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(tracks))
        for row, track in enumerate(tracks):
            self._set_row(row, track)
        self._table.setSortingEnabled(True)
        if sort_column >= 0:
            self._table.sortItems(sort_column, sort_order)

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
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel(self._title)
        title.setObjectName("panelTitle")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(
            self._build_button(
                QStyle.StandardPixmap.SP_ArrowRight,
                "Add selected to playlist",
                self._add_selected_to_playlist,
            )
        )
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
        header.addWidget(
            self._build_button(
                QStyle.StandardPixmap.SP_TrashIcon,
                "Remove selected",
                self._remove_selected_track,
            )
        )

        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Title", "Artist", "Source"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSortIndicatorShown(True)
        self._table.setSortingEnabled(True)
        self._table.sortItems(TITLE_COLUMN, Qt.SortOrder.AscendingOrder)
        self._table.itemDoubleClicked.connect(self._add_item_to_playlist)

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
        self._table.setItem(row, TITLE_COLUMN, title)
        self._table.setItem(row, ARTIST_COLUMN, artist)
        self._table.setItem(row, SOURCE_COLUMN, source)

    def _add_item_to_playlist(self, item: QTableWidgetItem) -> None:
        title_item = self._table.item(item.row(), 0)
        if title_item is None:
            return
        track_id = title_item.data(TRACK_ID_ROLE)
        if isinstance(track_id, str):
            self.tracks_add_requested.emit([track_id])

    def _add_selected_to_playlist(self) -> None:
        track_ids = self._selected_track_ids()
        if track_ids:
            self.tracks_add_requested.emit(track_ids)

    def _remove_selected_track(self) -> None:
        track_ids = self._selected_track_ids()
        if not track_ids:
            return
        removed = False
        for track_id in track_ids:
            removed = self._local_library_service.remove_track(track_id) or removed
        if removed:
            self.refresh()

    def _selected_track_ids(self) -> list[str]:
        track_ids_by_row: dict[int, str] = {}
        for item in self._table.selectedItems():
            if item.column() != TITLE_COLUMN:
                continue
            track_id = item.data(TRACK_ID_ROLE)
            if isinstance(track_id, str):
                track_ids_by_row[item.row()] = track_id
        return [track_ids_by_row[row] for row in sorted(track_ids_by_row)]

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
