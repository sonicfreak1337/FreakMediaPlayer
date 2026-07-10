"""Ordered active-playlist panel."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
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
SOURCE_COLUMN = 6
PLAYING_HIGHLIGHT_REFRESH_MS = 250


class PlaylistPanel(QWidget):
    def __init__(
        self,
        playlist_service: PlaylistService,
        playback_service: PlaybackService,
        show_title: bool = True,
    ) -> None:
        super().__init__()
        self._playlist_service = playlist_service
        self._playback_service = playback_service
        self._show_title = show_title
        self._tracks: list[Track] = []
        self._playing_row: int | None = None
        self._table = PlaylistTrackTable()
        self._summary_label = QLabel()
        self._header_controls: list[QWidget] = []
        self._delete_shortcut = QShortcut(QKeySequence.StandardKey.Delete, self._table)
        self._highlight_timer = QTimer(self)
        self._build_layout()
        self._connect_interactions()
        self._configure_highlight_timer()
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
        tracks = self._playlist_service.add_track_ids(track_ids, position)
        self._show_tracks(tracks)

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
        self._header_controls.extend(buttons)
        if self._show_title:
            header.addStretch(1)
            for button in buttons:
                header.addWidget(button)

        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["#", "Title", "Artist", "Length", "Album", "Year", "Source"]
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
        self._table.setColumnHidden(SOURCE_COLUMN, True)
        self._table.horizontalHeader().setMinimumHeight(34)
        self._table.verticalHeader().setDefaultSectionSize(35)

        if self._show_title:
            layout.addLayout(header)
        layout.addWidget(self._table, 1)
        self._summary_label.setObjectName("panelSummary")
        self._summary_label.setContentsMargins(12, 5, 12, 5)
        self._summary_label.setFixedHeight(34)
        layout.addWidget(self._summary_label)

    def _connect_interactions(self) -> None:
        self._delete_shortcut.activated.connect(self._remove_selected)
        self._table.itemDoubleClicked.connect(self._play_item)
        self._table.track_ids_dropped.connect(self.add_track_ids)
        self._table.rows_move_requested.connect(self._move_rows)

    def _configure_highlight_timer(self) -> None:
        self._highlight_timer.setInterval(PLAYING_HIGHLIGHT_REFRESH_MS)
        self._highlight_timer.timeout.connect(self._sync_playing_highlight)
        self._highlight_timer.start()

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
        self._playing_row = None
        self._table.setRowCount(len(tracks))
        for row, track in enumerate(tracks):
            self._set_row(row, track)
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

    def _set_row(self, row: int, track: Track) -> None:
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
        self._table.setItem(row, ORDER_COLUMN, order)
        self._table.setItem(row, TITLE_COLUMN, title)
        self._table.setItem(row, ARTIST_COLUMN, artist)
        self._table.setItem(row, LENGTH_COLUMN, length)
        self._table.setItem(row, ALBUM_COLUMN, album)
        self._table.setItem(row, YEAR_COLUMN, year)
        self._table.setItem(row, SOURCE_COLUMN, source)

    def _play_item(self, item: QTableWidgetItem) -> None:
        if 0 <= item.row() < len(self._tracks):
            self._playback_service.play_playlist(self._tracks, item.row())
            self._sync_playing_highlight()

    def _remove_selected(self) -> None:
        rows = self._selected_rows()
        if rows:
            self._show_tracks(self._playlist_service.remove_positions(rows))

    def _move_selected_up(self) -> None:
        rows = self._selected_rows()
        if rows and rows[0] > 0:
            self._move_rows(rows, rows[0] - 1)

    def _move_selected_down(self) -> None:
        rows = self._selected_rows()
        if rows and rows[-1] < len(self._tracks) - 1:
            self._move_rows(rows, rows[-1] + 2)

    def _move_rows(self, rows: Iterable[int], target: int) -> None:
        self._show_tracks(self._playlist_service.move_positions(rows, target))

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
