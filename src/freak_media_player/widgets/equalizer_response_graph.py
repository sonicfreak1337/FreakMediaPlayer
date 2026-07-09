"""Interactive DAW-style equalizer response graph."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from freak_media_player.models.equalizer import (
    MAX_FREQUENCY_HZ,
    MAX_GAIN_DB,
    MIN_FREQUENCY_HZ,
    MIN_GAIN_DB,
    EqualizerPreset,
)
from freak_media_player.ui.theme import (
    AMBER,
    DISPLAY_GREEN,
    HEADER_HIGHLIGHT,
    PANEL_BORDER,
    PANEL_SUNKEN,
    TEXT_SECONDARY,
)

GRAPH_MARGIN_LEFT = 44.0
GRAPH_MARGIN_RIGHT = 16.0
GRAPH_MARGIN_TOP = 12.0
GRAPH_MARGIN_BOTTOM = 24.0
NODE_RADIUS = 6.0
NODE_HIT_RADIUS = 14.0
FREQUENCY_TICKS = (20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000)
GAIN_TICKS = (-12, -6, 0, 6, 12)


class EqualizerResponseGraph(QWidget):
    band_selected = Signal(int)
    band_edited = Signal(int, int, float)

    def __init__(self) -> None:
        super().__init__()
        self._preset: EqualizerPreset | None = None
        self._response_frequencies: tuple[float, ...] = ()
        self._response_values: tuple[float, ...] = ()
        self._selected_band = 0
        self._dragging_band: int | None = None
        self.setMinimumHeight(170)
        self.setMouseTracking(True)

    def sizeHint(self) -> QSize:
        return QSize(720, 220)

    def set_data(
        self,
        preset: EqualizerPreset,
        response_frequencies: tuple[float, ...],
        response_values: tuple[float, ...],
    ) -> None:
        self._preset = preset
        self._response_frequencies = response_frequencies
        self._response_values = response_values
        self.update()

    def select_band(self, index: int) -> None:
        self._selected_band = index
        self.update()

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(PANEL_SUNKEN))
        graph_rect = self._graph_rect()
        self._draw_grid(painter, graph_rect)
        self._draw_response(painter, graph_rect)
        self._draw_nodes(painter, graph_rect)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        band_index = self._band_at(event.position())
        if band_index is None:
            return
        self._selected_band = band_index
        self._dragging_band = band_index
        self.band_selected.emit(band_index)
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging_band is None:
            return
        frequency_hz, gain_db = self._values_from_point(event.position())
        self.band_edited.emit(self._dragging_band, frequency_hz, gain_db)

    def mouseReleaseEvent(self, _event: QMouseEvent) -> None:
        self._dragging_band = None

    def _draw_grid(self, painter: QPainter, graph_rect: QRectF) -> None:
        painter.setFont(self.font())
        for gain_db in GAIN_TICKS:
            y = self._gain_to_y(float(gain_db), graph_rect)
            color = HEADER_HIGHLIGHT if gain_db == 0 else PANEL_BORDER
            painter.setPen(QPen(QColor(color), 1.0))
            painter.drawLine(QPointF(graph_rect.left(), y), QPointF(graph_rect.right(), y))
            painter.setPen(QColor(TEXT_SECONDARY))
            painter.drawText(
                QRectF(0.0, y - 8.0, GRAPH_MARGIN_LEFT - 6.0, 16.0),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{gain_db:+d}",
            )

        for frequency_hz in FREQUENCY_TICKS:
            x = self._frequency_to_x(float(frequency_hz), graph_rect)
            painter.setPen(QPen(QColor(PANEL_BORDER), 1.0))
            painter.drawLine(QPointF(x, graph_rect.top()), QPointF(x, graph_rect.bottom()))
            painter.setPen(QColor(TEXT_SECONDARY))
            painter.drawText(
                QRectF(x - 24.0, graph_rect.bottom() + 3.0, 48.0, 18.0),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                self._frequency_label(frequency_hz),
            )

    def _draw_response(self, painter: QPainter, graph_rect: QRectF) -> None:
        if not self._response_values:
            return
        path = QPainterPath()
        for index, (frequency_hz, gain_db) in enumerate(
            zip(self._response_frequencies, self._response_values, strict=True)
        ):
            point = QPointF(
                self._frequency_to_x(frequency_hz, graph_rect),
                self._gain_to_y(gain_db, graph_rect),
            )
            if index == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)
        painter.setPen(QPen(QColor(DISPLAY_GREEN), 2.0))
        painter.drawPath(path)

    def _draw_nodes(self, painter: QPainter, graph_rect: QRectF) -> None:
        if self._preset is None:
            return
        for index, band in enumerate(self._preset.bands):
            point = self._band_point(index, graph_rect)
            color = TEXT_SECONDARY
            if band.enabled:
                color = AMBER if index == self._selected_band else DISPLAY_GREEN
            painter.setPen(QPen(QColor(PANEL_SUNKEN), 2.0))
            painter.setBrush(QColor(color))
            painter.drawEllipse(point, NODE_RADIUS, NODE_RADIUS)

    def _band_at(self, point: QPointF) -> int | None:
        if self._preset is None:
            return None
        graph_rect = self._graph_rect()
        nearest: tuple[float, int] | None = None
        for index, _band in enumerate(self._preset.bands):
            band_point = self._band_point(index, graph_rect)
            distance = math.hypot(point.x() - band_point.x(), point.y() - band_point.y())
            if distance <= NODE_HIT_RADIUS and (nearest is None or distance < nearest[0]):
                nearest = (distance, index)
        return nearest[1] if nearest is not None else None

    def _band_point(self, index: int, graph_rect: QRectF) -> QPointF:
        if self._preset is None:
            return QPointF()
        band = self._preset.bands[index]
        return QPointF(
            self._frequency_to_x(float(band.frequency_hz), graph_rect),
            self._gain_to_y(band.gain_db, graph_rect),
        )

    def _values_from_point(self, point: QPointF) -> tuple[int, float]:
        graph_rect = self._graph_rect()
        normalized_x = min(1.0, max(0.0, (point.x() - graph_rect.left()) / graph_rect.width()))
        frequency_ratio = MAX_FREQUENCY_HZ / MIN_FREQUENCY_HZ
        frequency_hz = round(MIN_FREQUENCY_HZ * math.pow(frequency_ratio, normalized_x))
        normalized_y = min(1.0, max(0.0, (point.y() - graph_rect.top()) / graph_rect.height()))
        gain_db = MAX_GAIN_DB - normalized_y * (MAX_GAIN_DB - MIN_GAIN_DB)
        return frequency_hz, round(gain_db, 1)

    def _frequency_to_x(self, frequency_hz: float, graph_rect: QRectF) -> float:
        frequency_hz = min(MAX_FREQUENCY_HZ, max(MIN_FREQUENCY_HZ, frequency_hz))
        normalized = math.log(frequency_hz / MIN_FREQUENCY_HZ) / math.log(
            MAX_FREQUENCY_HZ / MIN_FREQUENCY_HZ
        )
        return graph_rect.left() + normalized * graph_rect.width()

    def _gain_to_y(self, gain_db: float, graph_rect: QRectF) -> float:
        gain_db = min(MAX_GAIN_DB, max(MIN_GAIN_DB, gain_db))
        normalized = (MAX_GAIN_DB - gain_db) / (MAX_GAIN_DB - MIN_GAIN_DB)
        return graph_rect.top() + normalized * graph_rect.height()

    def _graph_rect(self) -> QRectF:
        return QRectF(
            GRAPH_MARGIN_LEFT,
            GRAPH_MARGIN_TOP,
            max(1.0, self.width() - GRAPH_MARGIN_LEFT - GRAPH_MARGIN_RIGHT),
            max(1.0, self.height() - GRAPH_MARGIN_TOP - GRAPH_MARGIN_BOTTOM),
        )

    def _frequency_label(self, frequency_hz: int) -> str:
        if frequency_hz >= 1000:
            return f"{frequency_hz // 1000}k"
        return str(frequency_hz)
