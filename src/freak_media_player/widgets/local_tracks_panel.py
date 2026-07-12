"""Local track import and playback panel."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import (
    QCloseEvent,
    QDragEnterEvent,
    QDropEvent,
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QProgressBar,
    QStackedWidget,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from freak_media_player.models.media import Track
from freak_media_player.services.library_import_worker import (
    ImportScanResult,
    LibraryImportWorker,
)
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.search_service import (
    FILE_STATUS_AVAILABLE,
    FILE_STATUS_MISSING,
    FILE_STATUS_UNREADABLE,
    LibraryFilters,
    SearchService,
)
from freak_media_player.ui.assets import set_themed_icon
from freak_media_player.widgets.metadata_editor import MetadataEditorDialog
from freak_media_player.widgets.track_table import TRACK_ID_ROLE, TrackTableWidget

TITLE_COLUMN = 0
ARTIST_COLUMN = 1
ALBUM_COLUMN = 2
YEAR_COLUMN = 3
LENGTH_COLUMN = 4
STATUS_COLUMN = 5
FAVORITE_COLUMN = 6
SOURCE_COLUMN = 7


class LocalTracksPanel(QWidget):
    tracks_add_requested = Signal(object)
    track_relocated = Signal(object)
    track_metadata_changed = Signal(object)
    status_message = Signal(str)

    def __init__(
        self,
        title: str,
        local_library_service: LocalLibraryService,
        show_title: bool = True,
        search_service: SearchService | None = None,
    ) -> None:
        super().__init__()
        self._title = title
        self._show_title = show_title
        self._local_library_service = local_library_service
        self._search_service = search_service or SearchService(())
        self._all_tracks: list[Track] = []
        self._search = QLineEdit()
        self._artist_filter = QComboBox()
        self._album_filter = QComboBox()
        self._genre_filter = QComboBox()
        self._year_filter = QComboBox()
        self._favorite_filter = QComboBox()
        self._status_filter = QComboBox()
        self._import_progress = QProgressBar()
        self._cancel_import_button = QToolButton()
        self._import_thread: QThread | None = None
        self._import_worker: LibraryImportWorker | None = None
        self._import_added = 0
        self._import_updated = 0
        self._last_import_result: ImportScanResult | None = None
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
        self._all_tracks = self._local_library_service.list_tracks()
        self._refresh_filter_options()
        self._apply_search()

    def _apply_search(self) -> None:
        favorite_ids = self._local_library_service.list_favorite_track_ids()
        self._favorite_ids = favorite_ids
        filtered = self._search_service.filter_library(
            self._all_tracks,
            LibraryFilters(
                artist=self._string_filter(self._artist_filter),
                album=self._string_filter(self._album_filter),
                genre=self._string_filter(self._genre_filter),
                year=self._year_filter.currentData(),
                favorite=self._favorite_filter.currentData(),
                file_status=self._status_filter.currentData(),
            ),
            favorite_ids,
        )
        tracks = self._search_service.search_library(filtered, self._search.text())
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
        summary = f"{len(tracks)} tracks, {self._format_duration(total_seconds)} total duration"
        if self._search.text().strip():
            summary += f" — {len(self._all_tracks)} total"
        self._summary_label.setText(summary)
        self._empty_state.setText(
            "No tracks match your search. Clear or change the search text."
            if self._all_tracks and not tracks
            else "Your library is empty.\nImport audio files with +, add a folder with "
            "the folder button, or drag files here."
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

    def closeEvent(self, event: QCloseEvent) -> None:
        self._cancel_import()
        if self._import_thread is not None:
            self._import_thread.quit()
            self._import_thread.wait(2_000)
        super().closeEvent(event)

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
            self._build_button(
                QStyle.StandardPixmap.SP_DialogOpenButton,
                "Relocate selected missing file",
                self._relocate_selected_track,
            ),
            self._build_button(
                QStyle.StandardPixmap.SP_FileDialogDetailedView,
                "Edit selected track metadata",
                self._edit_selected_metadata,
            ),
        ]
        folder_button = buttons[2]
        self._folder_menu = QMenu(folder_button)
        self._folder_menu.aboutToShow.connect(self._rebuild_folder_menu)
        folder_button.setMenu(self._folder_menu)
        folder_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._search.setObjectName("librarySearch")
        self._search.setPlaceholderText(
            "Search title, artist, album, genre, year or filename"
        )
        self._search.setClearButtonEnabled(True)
        self._search.setMinimumWidth(260)
        self._search.textChanged.connect(self._apply_search)
        self._header_controls.extend([self._search, *buttons])
        if self._show_title:
            header.addStretch(1)
            for button in buttons:
                header.addWidget(button)

        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            [
                "Title",
                "Artist",
                "Album",
                "Year",
                "Length",
                "Status",
                "Favorite",
                "Source",
            ]
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
        self._table.setColumnWidth(STATUS_COLUMN, 86)
        self._table.setColumnWidth(FAVORITE_COLUMN, 68)
        self._table.setColumnHidden(SOURCE_COLUMN, True)
        self._table.sortItems(TITLE_COLUMN, Qt.SortOrder.AscendingOrder)
        self._table.itemDoubleClicked.connect(self._add_item_to_playlist)

        if self._show_title:
            layout.addLayout(header)
        layout.addWidget(self._build_filter_bar())
        self._configure_empty_state()
        self._content_stack.addWidget(self._table)
        self._content_stack.addWidget(self._empty_state)
        layout.addWidget(self._content_stack, 1)
        self._summary_label.setObjectName("panelSummary")
        self._summary_label.setContentsMargins(12, 5, 12, 5)
        self._summary_label.setFixedHeight(34)
        layout.addWidget(self._summary_label)

    def _build_filter_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("libraryFilterBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        for combo, label in (
            (self._artist_filter, "All artists"),
            (self._album_filter, "All albums"),
            (self._genre_filter, "All genres"),
            (self._year_filter, "All years"),
        ):
            combo.addItem(label, None)
            combo.setMinimumWidth(105)
            combo.currentIndexChanged.connect(self._apply_search)
            layout.addWidget(combo)
        self._favorite_filter.addItem("All favorites", None)
        self._favorite_filter.addItem("Favorites", True)
        self._favorite_filter.addItem("Not favorites", False)
        self._status_filter.addItem("All file states", None)
        self._status_filter.addItem("Available", FILE_STATUS_AVAILABLE)
        self._status_filter.addItem("Missing", FILE_STATUS_MISSING)
        self._status_filter.addItem("Unreadable", FILE_STATUS_UNREADABLE)
        for combo in (self._favorite_filter, self._status_filter):
            combo.currentIndexChanged.connect(self._apply_search)
            layout.addWidget(combo)
        reset = QToolButton()
        reset.setText("Reset filters")
        reset.setToolTip("Clear search and all library filters")
        reset.clicked.connect(self._reset_filters)
        layout.addWidget(reset)
        self._import_progress.setObjectName("libraryImportProgress")
        self._import_progress.setTextVisible(True)
        self._import_progress.setMinimumWidth(150)
        self._import_progress.hide()
        layout.addWidget(self._import_progress)
        self._cancel_import_button.setText("Cancel import")
        self._cancel_import_button.clicked.connect(self._cancel_import)
        self._cancel_import_button.hide()
        layout.addWidget(self._cancel_import_button)
        layout.addStretch(1)
        return bar

    def _refresh_filter_options(self) -> None:
        artists = sorted(
            {track.artist.name for track in self._all_tracks}, key=str.casefold
        )
        albums = sorted(
            {track.album.title for track in self._all_tracks if track.album},
            key=str.casefold,
        )
        genres = sorted(
            {track.genre for track in self._all_tracks if track.genre},
            key=str.casefold,
        )
        years = sorted(
            {
                track.album.release_year
                for track in self._all_tracks
                if track.album and track.album.release_year is not None
            },
            reverse=True,
        )
        self._set_filter_options(
            self._artist_filter,
            artists,
            "All artists",
        )
        self._set_filter_options(
            self._album_filter,
            albums,
            "All albums",
        )
        self._set_filter_options(
            self._genre_filter,
            genres,
            "All genres",
        )
        self._set_filter_options(
            self._year_filter,
            years,
            "All years",
        )

    def _set_filter_options(
        self, combo: QComboBox, values: Sequence[object], all_label: str
    ) -> None:
        selected = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(all_label, None)
        for value in values:
            combo.addItem(str(value), value)
        index = combo.findData(selected)
        combo.setCurrentIndex(max(0, index))
        combo.blockSignals(False)

    def _reset_filters(self) -> None:
        self._search.clear()
        for combo in (
            self._artist_filter,
            self._album_filter,
            self._genre_filter,
            self._year_filter,
            self._favorite_filter,
            self._status_filter,
        ):
            combo.setCurrentIndex(0)
        self._apply_search()

    def _string_filter(self, combo: QComboBox) -> str | None:
        value = combo.currentData()
        return value if isinstance(value, str) else None

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
            QStyle.StandardPixmap.SP_DialogOpenButton: "↻",
            QStyle.StandardPixmap.SP_FileDialogDetailedView: "✎",
        }
        button.setText(symbols.get(icon, "+"))
        icon_files = {
            QStyle.StandardPixmap.SP_ArrowRight: "plus_icon.png",
            QStyle.StandardPixmap.SP_FileIcon: "plus_icon.png",
            QStyle.StandardPixmap.SP_DirIcon: "folder_add_icon.png",
            QStyle.StandardPixmap.SP_TrashIcon: "minus_icon.png",
            QStyle.StandardPixmap.SP_DialogOpenButton: "folder_add_icon.png",
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
            managed = self._local_library_service.register_music_folder(Path(folder))
            self._start_background_import([managed])

    def _rebuild_folder_menu(self) -> None:
        self._folder_menu.clear()
        self._folder_menu.addAction("Add music folder…", self._select_folder)
        folders = self._local_library_service.list_music_folders()
        if not folders:
            empty = self._folder_menu.addAction("No managed folders")
            empty.setEnabled(False)
            return
        self._folder_menu.addSeparator()
        for folder in folders:
            submenu = self._folder_menu.addMenu(str(folder))
            submenu.addAction(
                "Rescan",
                lambda _checked=False, path=folder: self._rescan_music_folder(path),
            )
            submenu.addAction(
                "Remove source",
                lambda _checked=False, path=folder: self._remove_music_folder(path),
            )

    def _rescan_music_folder(self, folder: Path) -> None:
        self._start_background_import([folder])

    def _remove_music_folder(self, folder: Path) -> None:
        if self._local_library_service.remove_music_folder(folder):
            self.status_message.emit(
                "Music folder source removed; imported tracks and files were kept."
            )

    def _import_paths(self, paths: list[Path]) -> None:
        self._start_background_import(paths)

    def _start_background_import(self, paths: list[Path]) -> None:
        if self._import_thread is not None and self._import_thread.isRunning():
            self.status_message.emit("An import is already running.")
            return
        self._import_added = 0
        self._import_updated = 0
        self._last_import_result = None
        self._import_progress.setRange(0, 1)
        self._import_progress.setValue(0)
        self._import_progress.show()
        self._cancel_import_button.show()
        thread = QThread(self)
        worker = LibraryImportWorker(self._local_library_service, paths)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.track_ready.connect(self._store_background_track)
        worker.progress.connect(self._update_import_progress)
        worker.finished.connect(self._finish_background_import)
        worker.finished.connect(lambda _result: thread.quit())
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_import_thread)
        self._import_thread = thread
        self._import_worker = worker
        thread.start()
        self.status_message.emit("Import started in the background.")

    def _store_background_track(self, track: object) -> None:
        if not isinstance(track, Track):
            return
        if self._local_library_service.save_imported_track(track):
            self._import_added += 1
        else:
            self._import_updated += 1

    def _update_import_progress(self, processed: int, total: int) -> None:
        self._import_progress.setRange(0, max(1, total))
        self._import_progress.setValue(processed)
        self._import_progress.setFormat(f"Importing {processed}/{total}")

    def _finish_background_import(self, result: object) -> None:
        if not isinstance(result, ImportScanResult):
            return
        self._last_import_result = result
        self._cancel_import_button.hide()
        self._import_progress.hide()
        self.refresh()
        outcome = "cancelled" if result.cancelled else "finished"
        self.status_message.emit(
            f"Import {outcome}: {self._import_added} added, "
            f"{self._import_updated} updated, {len(result.errors)} failed."
        )

    def _cancel_import(self) -> None:
        if self._import_worker is not None:
            self._import_worker.cancel()
            self._cancel_import_button.setEnabled(False)

    def _clear_import_thread(self) -> None:
        self._import_thread = None
        self._import_worker = None
        self._cancel_import_button.setEnabled(True)

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
        file_status = self._search_service.file_status(track)
        status = QTableWidgetItem(file_status.title())
        status.setToolTip(track.provider_identity.item_id)
        favorite = QTableWidgetItem("♥" if track.id in self._favorite_ids else "")
        favorite.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
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
        self._table.setItem(row, STATUS_COLUMN, status)
        self._table.setItem(row, FAVORITE_COLUMN, favorite)
        self._table.setItem(row, SOURCE_COLUMN, source)

    def _relocate_selected_track(self) -> None:
        track_ids = self._selected_track_ids()
        if len(track_ids) != 1:
            self.status_message.emit("Select exactly one library track to relocate.")
            return
        track = self._local_library_service.get_track(track_ids[0])
        if track is None:
            return
        filters = "Audio files (" + " ".join(f"*{ext}" for ext in self._extensions()) + ")"
        selected, _filter = QFileDialog.getOpenFileName(
            self,
            "Choose the new audio file location",
            str(Path(track.provider_identity.item_id).parent),
            filters,
        )
        if not selected:
            return
        try:
            relocated = self._local_library_service.relocate_track(
                track.id, Path(selected)
            )
        except (OSError, ValueError) as error:
            self.status_message.emit(f"Could not relocate track: {error}")
            return
        self.refresh()
        self.track_relocated.emit(relocated)
        self.status_message.emit("Track file location updated.")

    def _edit_selected_metadata(self) -> None:
        track_ids = self._selected_track_ids()
        if len(track_ids) != 1:
            self.status_message.emit("Select exactly one library track to edit.")
            return
        track = self._local_library_service.get_track(track_ids[0])
        if track is None:
            return
        dialog = MetadataEditorDialog(track, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        try:
            updated = self._local_library_service.update_track_metadata(
                track.id,
                title=values.title,
                artist=values.artist,
                album=values.album,
                release_year=values.release_year,
                genre=values.genre,
                track_number=values.track_number,
                disc_number=values.disc_number,
            )
        except ValueError as error:
            self.status_message.emit(f"Could not save metadata: {error}")
            return
        self.refresh()
        self.track_metadata_changed.emit(updated)
        self.status_message.emit("Library metadata saved; audio file unchanged.")

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
            self.status_message.emit(
                f"Removed {len(track_ids)} track{'s' if len(track_ids) != 1 else ''} "
                "from the library."
            )

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
