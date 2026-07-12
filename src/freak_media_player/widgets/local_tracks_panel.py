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
    QStackedWidget,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from freak_media_player.models.media import Track
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.ui.assets import set_themed_icon
from freak_media_player.widgets.track_table import TRACK_ID_ROLE, TrackTableWidget

TITLE_COLUMN = 0
ARTIST_COLUMN = 1
ALBUM_COLUMN = 2
YEAR_COLUMN = 3
LENGTH_COLUMN = 4
SOURCE_COLUMN = 5


class LocalTracksPanel(QWidget):
    tracks_add_requested = Signal(object)

    def __init__(
        self,
        title: str,
        local_library_service: LocalLibraryService,
        show_title: bool = True,
    ) -> None:
        super().__init__()
        self._title = title
        self._show_title = show_title
        self._local_library_service = local_library_service
        self._table = TrackTableWidget()
        self._content_stack = QStackedWidget()
        self._empty_state = QLabel(
            "Your library is empty.\nImport audio files with +, add a folder with "
            "the folder button, or drag files here."
        )
        self._summary_label = QLabel()
        self._header_controls: list[QWidget] = []
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
        total_seconds = sum(
            int(track.duration.total_seconds())
            for track in tracks
            if track.duration is not None
        )
        self._summary_label.setText(
            f"{len(tracks)} tracks, {self._format_duration(total_seconds)} total duration"
        )
        self._content_stack.setCurrentWidget(
            self._table if tracks else self._empty_state
        )

    @property
    def header_controls(self) -> tuple[QWidget, ...]:
        return tuple(self._header_controls)

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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(10, 4, 10, 4)
        header.setSpacing(6)
        if self._show_title:
            title = QLabel(self._title)
            title.setObjectName("panelTitle")
            header.addWidget(title)
        buttons = [
            self._build_button(
                QStyle.StandardPixmap.SP_ArrowRight,
                "Add selected to playlist",
                self._add_selected_to_playlist,
            ),
            self._build_button(
                QStyle.StandardPixmap.SP_FileIcon,
                "Import files",
                self._select_files,
            ),
            self._build_button(
                QStyle.StandardPixmap.SP_DirIcon,
                "Import folder",
                self._select_folder,
            ),
            self._build_button(
                QStyle.StandardPixmap.SP_TrashIcon,
                "Remove selected",
                self._remove_selected_track,
            ),
        ]
        self._header_controls.extend(buttons)
        if self._show_title:
            header.addStretch(1)
            for button in buttons:
                header.addWidget(button)

        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["Title", "Artist", "Album", "Year", "Length", "Source"]
        )
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSortIndicatorShown(True)
        self._table.horizontalHeader().setMinimumHeight(34)
        self._table.verticalHeader().setDefaultSectionSize(35)
        self._table.setSortingEnabled(True)
        self._table.setColumnWidth(TITLE_COLUMN, 235)
        self._table.setColumnWidth(ARTIST_COLUMN, 165)
        self._table.setColumnWidth(ALBUM_COLUMN, 150)
        self._table.setColumnWidth(YEAR_COLUMN, 52)
        self._table.setColumnWidth(LENGTH_COLUMN, 60)
        self._table.setColumnHidden(SOURCE_COLUMN, True)
        self._table.sortItems(TITLE_COLUMN, Qt.SortOrder.AscendingOrder)
        self._table.itemDoubleClicked.connect(self._add_item_to_playlist)

        if self._show_title:
            layout.addLayout(header)
        self._configure_empty_state()
        self._content_stack.addWidget(self._table)
        self._content_stack.addWidget(self._empty_state)
        layout.addWidget(self._content_stack, 1)
        self._summary_label.setObjectName("panelSummary")
        self._summary_label.setContentsMargins(12, 5, 12, 5)
        self._summary_label.setFixedHeight(34)
        layout.addWidget(self._summary_label)

    def _configure_empty_state(self) -> None:
        self._empty_state.setObjectName("panelEmptyState")
        self._empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state.setWordWrap(True)
        self._empty_state.setContentsMargins(36, 24, 36, 24)
        self._empty_state.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )

    def _build_button(
        self,
        icon: QStyle.StandardPixmap,
        tooltip: str,
        handler: Callable[[], object],
    ) -> QToolButton:
        button = QToolButton()
        symbols = {
            QStyle.StandardPixmap.SP_ArrowRight: "→",
            QStyle.StandardPixmap.SP_FileIcon: "+",
            QStyle.StandardPixmap.SP_DirIcon: "▣+",
            QStyle.StandardPixmap.SP_TrashIcon: "−",
        }
        button.setText(symbols.get(icon, "+"))
        icon_files = {
            QStyle.StandardPixmap.SP_ArrowRight: "plus_icon.png",
            QStyle.StandardPixmap.SP_FileIcon: "plus_icon.png",
            QStyle.StandardPixmap.SP_DirIcon: "folder_add_icon.png",
            QStyle.StandardPixmap.SP_TrashIcon: "minus_icon.png",
        }
        icon_file = icon_files.get(icon)
        if icon_file is not None:
            set_themed_icon(button, f"icons/{icon_file}", 18)
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
        album = QTableWidgetItem(track.album.title if track.album else "")
        year = QTableWidgetItem(
            str(track.album.release_year)
            if track.album and track.album.release_year is not None
            else ""
        )
        source = QTableWidgetItem(track.provider_identity.item_id)
        length = QTableWidgetItem(
            self._format_duration(int(track.duration.total_seconds()))
            if track.duration is not None
            else ""
        )
        self._table.setItem(row, TITLE_COLUMN, title)
        self._table.setItem(row, ARTIST_COLUMN, artist)
        self._table.setItem(row, ALBUM_COLUMN, album)
        self._table.setItem(row, YEAR_COLUMN, year)
        self._table.setItem(row, LENGTH_COLUMN, length)
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

    def _format_duration(self, seconds: int) -> str:
        minutes, remaining_seconds = divmod(max(0, seconds), 60)
        return f"{minutes}:{remaining_seconds:02d}"

    def _event_has_local_paths(self, event: QDragEnterEvent | QDropEvent) -> bool:
        mime_data = event.mimeData()
        return mime_data.hasUrls() and bool(self._paths_from_event(event))

    def _paths_from_event(self, event: QDragEnterEvent | QDropEvent) -> list[Path]:
        paths: list[Path] = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                paths.append(Path(url.toLocalFile()))
        return paths
