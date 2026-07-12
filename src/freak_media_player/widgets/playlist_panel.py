"""Ordered active-playlist panel."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QHideEvent,
    QIcon,
    QKeySequence,
    QShortcut,
    QShowEvent,
)
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
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
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.services.playlist_service import PlaylistService
from freak_media_player.ui.assets import set_themed_icon
from freak_media_player.ui.skins import skin_color
from freak_media_player.widgets.track_table import (
    PLAYING_ROLE,
    TRACK_ID_ROLE,
    PlaylistTrackTable,
)

ORDER_COLUMN = 0
TITLE_COLUMN = 1
ARTIST_COLUMN = 2
LENGTH_COLUMN = 3
ALBUM_COLUMN = 4
YEAR_COLUMN = 5
FAVORITE_COLUMN = 6
SOURCE_COLUMN = 7
PLAYING_HIGHLIGHT_REFRESH_MS = 250


class PlaylistPanel(QWidget):
    status_message = Signal(str)

    def __init__(
        self,
        playlist_service: PlaylistService,
        playback_service: PlaybackService,
        show_title: bool = True,
        local_library_service: LocalLibraryService | None = None,
    ) -> None:
        super().__init__()
        self._playlist_service = playlist_service
        self._playback_service = playback_service
        self._show_title = show_title
        self._local_library_service = local_library_service
        self._tracks: list[Track] = []
        self._playing_row: int | None = None
        self._table = PlaylistTrackTable()
        self._playlist_selector = QComboBox()
        self._playlist_actions = QToolButton()
        self._content_stack = QStackedWidget()
        self._empty_state = QLabel(
            "Your playlist is empty.\nSelect tracks in the Local Library and use "
            "the add button, double-click a track, or drag it here."
        )
        self._summary_label = QLabel()
        self._header_controls: list[QWidget] = []
        self._delete_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Delete), self._table
        )
        self._delete_shortcut.setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self._highlight_timer = QTimer(self)
        self._build_layout()
        self._connect_interactions()
        self._configure_highlight_timer()
        self._refresh_playlist_selector()
        self.refresh()

    @property
    def header_controls(self) -> tuple[QWidget, ...]:
        return tuple(self._header_controls)

    def refresh(self) -> None:
        self._show_tracks(self._playlist_service.list_tracks())

    def refresh_skin_asset(self) -> None:
        """Repaint stored item brushes after a live skin change."""
        if self._playing_row is not None:
            self._set_playing_highlight(self._playing_row, highlighted=True)
        self._table.viewport().update()

    def add_track_ids(
        self,
        track_ids: Iterable[str],
        position: int | None = None,
    ) -> None:
        previous_count = len(self._tracks)
        tracks = self._playlist_service.add_track_ids(track_ids, position)
        self._show_tracks(tracks)
        added_count = len(tracks) - previous_count
        if added_count:
            self.status_message.emit(
                f"Playlist saved — added {added_count} "
                f"track{'s' if added_count != 1 else ''}."
            )

    def remove_current_track(self) -> None:
        position = self._playback_service.current_playlist_index()
        if position is not None:
            self._show_tracks(self._playlist_service.remove_positions([position]))
            self.status_message.emit("Playlist saved — removed the current track.")

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(10, 4, 10, 4)
        header.setSpacing(6)
        if self._show_title:
            title = QLabel("Playlist")
            title.setObjectName("panelTitle")
            header.addWidget(title)
        buttons = [
            self._build_button(
                QStyle.StandardPixmap.SP_ArrowUp,
                "Move selected up",
                self._move_selected_up,
            ),
            self._build_button(
                QStyle.StandardPixmap.SP_ArrowDown,
                "Move selected down",
                self._move_selected_down,
            ),
            self._build_button(
                QStyle.StandardPixmap.SP_TrashIcon,
                "Remove selected from playlist",
                self._remove_selected,
            ),
        ]
        self._playlist_selector.setObjectName("playlistSelector")
        self._playlist_selector.setMinimumWidth(170)
        self._playlist_actions.setText("Playlist actions")
        self._playlist_actions.setObjectName("playlistActionsButton")
        actions_menu = QMenu(self._playlist_actions)
        actions_menu.addAction("New playlist…", self._create_playlist)
        actions_menu.addAction("Duplicate playlist…", self._duplicate_playlist)
        actions_menu.addAction("Rename playlist…", self._rename_playlist)
        actions_menu.addSeparator()
        actions_menu.addAction("Clear playlist…", self._clear_playlist)
        actions_menu.addAction("Delete playlist…", self._delete_playlist)
        self._playlist_actions.setMenu(actions_menu)
        self._playlist_actions.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        self._header_controls.extend(
            [self._playlist_selector, self._playlist_actions, *buttons]
        )
        if self._show_title:
            header.addStretch(1)
            for button in buttons:
                header.addWidget(button)

        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            ["#", "Title", "Artist", "Length", "Album", "Year", "Favorite", "Source"]
        )
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setColumnWidth(ORDER_COLUMN, 44)
        self._table.setColumnWidth(TITLE_COLUMN, 310)
        self._table.setColumnWidth(ARTIST_COLUMN, 220)
        self._table.setColumnWidth(LENGTH_COLUMN, 66)
        self._table.setColumnHidden(ALBUM_COLUMN, True)
        self._table.setColumnHidden(YEAR_COLUMN, True)
        self._table.setColumnWidth(FAVORITE_COLUMN, 68)
        self._table.setColumnHidden(SOURCE_COLUMN, True)
        self._table.horizontalHeader().setMinimumHeight(34)
        self._table.verticalHeader().setDefaultSectionSize(35)

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

    def _connect_interactions(self) -> None:
        self._playlist_selector.currentIndexChanged.connect(
            self._switch_selected_playlist
        )
        self._delete_shortcut.activated.connect(self._remove_selected)
        self._table.itemDoubleClicked.connect(self._play_item)
        self._table.track_ids_dropped.connect(self.add_track_ids)
        self._table.rows_move_requested.connect(self._move_rows)

    def _refresh_playlist_selector(self) -> None:
        self._playlist_selector.blockSignals(True)
        self._playlist_selector.clear()
        for playlist in self._playlist_service.list_playlists():
            self._playlist_selector.addItem(playlist.name, playlist.playlist_id)
        index = self._playlist_selector.findData(
            self._playlist_service.active_playlist_id()
        )
        self._playlist_selector.setCurrentIndex(max(0, index))
        self._playlist_selector.blockSignals(False)

    def _switch_selected_playlist(self, index: int) -> None:
        playlist_id = self._playlist_selector.itemData(index)
        if not isinstance(playlist_id, str):
            return
        self._show_tracks(self._playlist_service.switch_playlist(playlist_id))
        self.status_message.emit(
            f"Opened playlist “{self._playlist_selector.itemText(index)}”."
        )

    def _create_playlist(self) -> None:
        name, accepted = QInputDialog.getText(self, "New playlist", "Playlist name")
        if not accepted:
            return
        try:
            playlist = self._playlist_service.create_playlist(name)
        except ValueError as error:
            self.status_message.emit(str(error))
            return
        self._refresh_playlist_selector()
        self._show_tracks([])
        self.status_message.emit(f"Created playlist “{playlist.name}”.")

    def _duplicate_playlist(self) -> None:
        current_name = self._playlist_selector.currentText()
        name, accepted = QInputDialog.getText(
            self, "Duplicate playlist", "New playlist name", text=f"{current_name} Copy"
        )
        if not accepted:
            return
        try:
            playlist = self._playlist_service.duplicate_active_playlist(name)
        except ValueError as error:
            self.status_message.emit(str(error))
            return
        self._refresh_playlist_selector()
        self.refresh()
        self.status_message.emit(f"Duplicated playlist as “{playlist.name}”.")

    def _rename_playlist(self) -> None:
        name, accepted = QInputDialog.getText(
            self,
            "Rename playlist",
            "Playlist name",
            text=self._playlist_selector.currentText(),
        )
        if not accepted:
            return
        try:
            playlist = self._playlist_service.rename_active_playlist(name)
        except ValueError as error:
            self.status_message.emit(str(error))
            return
        self._refresh_playlist_selector()
        self.status_message.emit(f"Renamed playlist to “{playlist.name}”.")

    def _clear_playlist(self) -> None:
        answer = QMessageBox.question(
            self,
            "Clear playlist",
            "Remove every track from this playlist? Library files are kept.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._playlist_service.clear()
        self._show_tracks([])
        self.status_message.emit("Playlist cleared and saved.")

    def _delete_playlist(self) -> None:
        answer = QMessageBox.question(
            self,
            "Delete playlist",
            "Delete this playlist? Library files are kept.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        deleted_name = self._playlist_selector.currentText()
        self._playlist_service.delete_active_playlist()
        self._refresh_playlist_selector()
        self.refresh()
        self.status_message.emit(f"Deleted playlist “{deleted_name}”.")

    def _configure_highlight_timer(self) -> None:
        self._highlight_timer.setInterval(PLAYING_HIGHLIGHT_REFRESH_MS)
        self._highlight_timer.timeout.connect(self._sync_playing_highlight)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._sync_playing_highlight()
        self._highlight_timer.start()

    def hideEvent(self, event: QHideEvent) -> None:
        self._highlight_timer.stop()
        super().hideEvent(event)

    def _build_button(
        self,
        icon: QStyle.StandardPixmap,
        tooltip: str,
        handler: Callable[[], object],
    ) -> QToolButton:
        button = QToolButton()
        symbols = {
            QStyle.StandardPixmap.SP_ArrowUp: "↑",
            QStyle.StandardPixmap.SP_ArrowDown: "↓",
            QStyle.StandardPixmap.SP_TrashIcon: "−",
        }
        button.setText(symbols.get(icon, "•"))
        if icon == QStyle.StandardPixmap.SP_TrashIcon:
            set_themed_icon(button, "icons/minus_icon.png", 18)
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(handler)
        return button

    def _show_tracks(self, tracks: list[Track]) -> None:
        self._tracks = tracks
        favorite_ids = (
            self._local_library_service.list_favorite_track_ids()
            if self._local_library_service is not None
            else set()
        )
        self._playing_row = None
        self._table.setRowCount(len(tracks))
        for row, track in enumerate(tracks):
            self._set_row(row, track, favorite_ids)
        self._playback_service.sync_playlist(tracks)
        self._sync_playing_highlight()
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

    def _set_row(self, row: int, track: Track, favorite_ids: set[str]) -> None:
        order = QTableWidgetItem(str(row + 1))
        order.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QTableWidgetItem(track.title)
        title.setData(TRACK_ID_ROLE, track.id)
        artist = QTableWidgetItem(track.artist.name)
        length = QTableWidgetItem(
            self._format_duration(int(track.duration.total_seconds()))
            if track.duration is not None
            else ""
        )
        album = QTableWidgetItem(track.album.title if track.album else "")
        year = QTableWidgetItem(
            str(track.album.release_year)
            if track.album and track.album.release_year is not None
            else ""
        )
        source = QTableWidgetItem(track.provider_identity.item_id)
        favorite = QTableWidgetItem("♥" if track.id in favorite_ids else "")
        favorite.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._table.setItem(row, ORDER_COLUMN, order)
        self._table.setItem(row, TITLE_COLUMN, title)
        self._table.setItem(row, ARTIST_COLUMN, artist)
        self._table.setItem(row, LENGTH_COLUMN, length)
        self._table.setItem(row, ALBUM_COLUMN, album)
        self._table.setItem(row, YEAR_COLUMN, year)
        self._table.setItem(row, FAVORITE_COLUMN, favorite)
        self._table.setItem(row, SOURCE_COLUMN, source)

    def _play_item(self, item: QTableWidgetItem) -> None:
        if 0 <= item.row() < len(self._tracks):
            self._playback_service.play_playlist(self._tracks, item.row())
            self._sync_playing_highlight()

    def _remove_selected(self) -> None:
        rows = self._selected_rows()
        if rows:
            self._show_tracks(self._playlist_service.remove_positions(rows))
            self.status_message.emit(
                f"Playlist saved — removed {len(rows)} "
                f"track{'s' if len(rows) != 1 else ''}."
            )

    def _move_selected_up(self) -> None:
        rows = self._selected_rows()
        if rows and rows[0] > 0:
            self._move_rows(rows, rows[0] - 1)

    def _move_selected_down(self) -> None:
        rows = self._selected_rows()
        if rows and rows[-1] < len(self._tracks) - 1:
            self._move_rows(rows, rows[-1] + 2)

    def _move_rows(self, rows: Iterable[int], target: int) -> None:
        selected = list(rows)
        self._show_tracks(self._playlist_service.move_positions(selected, target))
        if selected:
            self.status_message.emit("Playlist order saved.")

    def _selected_rows(self) -> list[int]:
        return sorted({item.row() for item in self._table.selectedItems()})

    def _sync_playing_highlight(self) -> None:
        playing_row = self._playback_service.current_playlist_index()
        if playing_row is not None and not 0 <= playing_row < self._table.rowCount():
            playing_row = None
        if playing_row == self._playing_row:
            return
        if self._playing_row is not None:
            self._set_playing_highlight(self._playing_row, highlighted=False)
        if playing_row is not None:
            self._set_playing_highlight(playing_row, highlighted=True)
        self._playing_row = playing_row

    def _set_playing_highlight(self, row: int, highlighted: bool) -> None:
        background = (
            QBrush(QColor(skin_color("playing_row_background")))
            if highlighted
            else QBrush()
        )
        foreground = (
            QBrush(QColor(skin_color("playing_row_text")))
            if highlighted
            else QBrush()
        )
        for column in range(self._table.columnCount()):
            item = self._table.item(row, column)
            if item is not None:
                item.setBackground(background)
                item.setForeground(foreground)
                item.setData(PLAYING_ROLE, highlighted)
        order_item = self._table.item(row, ORDER_COLUMN)
        if order_item is not None:
            icon = QIcon()
            if highlighted:
                icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
            order_item.setIcon(icon)

    def _format_duration(self, seconds: int) -> str:
        minutes, remaining_seconds = divmod(max(0, seconds), 60)
        return f"{minutes}:{remaining_seconds:02d}"
