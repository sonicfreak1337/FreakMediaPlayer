"""Track-table drag and drop primitives."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import (
    QByteArray,
    QMimeData,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QDrag,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QPainter,
    QPalette,
    QPen,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
)

from freak_media_player.ui.skins import skin_color

TRACK_ID_ROLE = Qt.ItemDataRole.UserRole
PLAYING_ROLE = Qt.ItemDataRole.UserRole + 1
TRACK_IDS_MIME_TYPE = "application/x-freak-media-player-track-ids"
PLAYLIST_ROWS_MIME_TYPE = "application/x-freak-media-player-playlist-rows"


class TrackRowDelegate(QStyledItemDelegate):
    """Keep the gold playing state dominant over the subtle selection state."""

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        playing = bool(index.data(PLAYING_ROLE))
        styled_option = QStyleOptionViewItem(option)
        if playing:
            styled_option.state &= ~QStyle.StateFlag.State_Selected
            styled_option.palette.setColor(
                QPalette.ColorRole.Text,
                QColor(skin_color("playing_row_text")),
            )
        super().paint(painter, styled_option, index)
        if playing:
            painter.save()
            painter.setPen(QPen(QColor(skin_color("highlight")), 1.0))
            painter.drawLine(option.rect.topLeft(), option.rect.topRight())
            painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
            painter.restore()


class TrackTableWidget(QTableWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setDragEnabled(True)
        self.setItemDelegate(TrackRowDelegate(self))
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)

    def mimeTypes(self) -> list[str]:
        return [TRACK_IDS_MIME_TYPE]

    def mimeData(self, items: Sequence[QTableWidgetItem]) -> QMimeData:
        mime_data = QMimeData()
        track_ids = self._track_ids(items)
        mime_data.setData(TRACK_IDS_MIME_TYPE, _encode_values(track_ids))
        return mime_data

    def _track_ids(self, items: Sequence[QTableWidgetItem]) -> list[str]:
        track_ids_by_row: dict[int, str] = {}
        for item in items:
            track_id = item.data(TRACK_ID_ROLE)
            if isinstance(track_id, str):
                track_ids_by_row[item.row()] = track_id
        return [track_ids_by_row[row] for row in sorted(track_ids_by_row)]


class PlaylistTrackTable(TrackTableWidget):
    track_ids_dropped = Signal(object, int)
    rows_move_requested = Signal(object, int)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDropIndicatorShown(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._supports_drop(event.mimeData()):
            event.acceptProposedAction()
            return
        event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if self._supports_drop(event.mimeData()):
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        target_row = self._drop_row(event)
        mime_data = event.mimeData()
        if event.source() is self and mime_data.hasFormat(PLAYLIST_ROWS_MIME_TYPE):
            rows = _decode_integers(mime_data.data(PLAYLIST_ROWS_MIME_TYPE))
            self.rows_move_requested.emit(rows, target_row)
            drop_action = Qt.DropAction.MoveAction
        elif mime_data.hasFormat(TRACK_IDS_MIME_TYPE):
            track_ids = _decode_values(mime_data.data(TRACK_IDS_MIME_TYPE))
            self.track_ids_dropped.emit(track_ids, target_row)
            drop_action = Qt.DropAction.CopyAction
        else:
            event.ignore()
            return
        event.setDropAction(drop_action)
        event.accept()

    def startDrag(self, supported_actions: Qt.DropAction) -> None:
        rows = sorted({item.row() for item in self.selectedItems()})
        if not rows:
            return
        mime_data = self.mimeData(self.selectedItems())
        mime_data.setData(
            PLAYLIST_ROWS_MIME_TYPE,
            _encode_values([str(row) for row in rows]),
        )
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.MoveAction)

    def _supports_drop(self, mime_data: QMimeData) -> bool:
        return mime_data.hasFormat(TRACK_IDS_MIME_TYPE)

    def _drop_row(self, event: QDropEvent) -> int:
        point = event.position().toPoint()
        index = self.indexAt(point)
        if not index.isValid():
            return self.rowCount()
        row = index.row()
        if point.y() > self.visualRect(index).center().y():
            return row + 1
        return row


def _encode_values(values: list[str]) -> QByteArray:
    return QByteArray("\n".join(values).encode("utf-8"))


def _decode_values(data: QByteArray) -> list[str]:
    return [value for value in bytes(data.data()).decode("utf-8").splitlines() if value]


def _decode_integers(data: QByteArray) -> list[int]:
    return [int(value) for value in _decode_values(data)]
