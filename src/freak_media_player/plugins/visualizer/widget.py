"""Audio-reactive Qt canvas and controls for the visualizer plugin."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QHideEvent,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QRadialGradient,
    QShowEvent,
)
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from freak_media_player.player.audio_samples import AudioSampleBuffer

FRAME_INTERVAL_MS = 33
FFT_SIZE = 2_048
SPECTRUM_BANDS = 64

PRESETS = (
    ("neon_spectrum", "Neon Spectrum"),
    ("radial_bloom", "Radial Bloom"),
    ("star_tunnel", "Star Tunnel"),
    ("oscilloscope", "Electric Oscilloscope"),
    ("aurora", "Aurora Waves"),
    ("constellation", "Cosmic Constellation"),
)


@dataclass(frozen=True)
class VisualizerFrame:
    samples: NDArray[np.float32]
    spectrum: NDArray[np.float32]
    energy: float
    bass: float
    elapsed: float


class VisualizerCanvas(QWidget):
    def __init__(self, audio_samples: AudioSampleBuffer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._audio_samples = audio_samples
        self._preset = PRESETS[0][0]
        self._started = time.monotonic()
        self._smoothed = np.zeros(SPECTRUM_BANDS, dtype=np.float32)
        self._timer = QTimer(self)
        self._timer.setInterval(FRAME_INTERVAL_MS)
        self._timer.timeout.connect(self.update)
        self.setMinimumHeight(170)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

    def set_preset(self, preset_id: str) -> None:
        if preset_id in {item[0] for item in PRESETS}:
            self._preset = preset_id
            self.update()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._timer.start()

    def hideEvent(self, event: QHideEvent) -> None:
        self._timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#02030a"))
        frame = self._build_frame()
        renderers = {
            "neon_spectrum": self._paint_neon_spectrum,
            "radial_bloom": self._paint_radial_bloom,
            "star_tunnel": self._paint_star_tunnel,
            "oscilloscope": self._paint_oscilloscope,
            "aurora": self._paint_aurora,
            "constellation": self._paint_constellation,
        }
        renderers[self._preset](painter, frame)
        self._paint_vignette(painter)
        painter.end()

    def _build_frame(self) -> VisualizerFrame:
        samples = self._audio_samples.snapshot(FFT_SIZE)
        windowed = samples * np.hanning(samples.size).astype(np.float32)
        magnitudes = np.abs(np.fft.rfft(windowed)) / max(1, samples.size)
        edges = np.geomspace(1, magnitudes.size, SPECTRUM_BANDS + 1).astype(int)
        spectrum = np.array(
            [
                np.max(magnitudes[edges[i] : max(edges[i] + 1, edges[i + 1])])
                for i in range(SPECTRUM_BANDS)
            ],
            dtype=np.float32,
        )
        spectrum = np.clip((20.0 * np.log10(spectrum + 1e-6) + 72.0) / 72.0, 0.0, 1.0)
        self._smoothed = np.maximum(spectrum, self._smoothed * 0.88)
        energy = min(1.0, float(np.sqrt(np.mean(np.square(samples))) * 4.8))
        bass = min(1.0, float(np.mean(self._smoothed[1:10]) * 1.5))
        return VisualizerFrame(
            samples=samples,
            spectrum=self._smoothed.copy(),
            energy=energy,
            bass=bass,
            elapsed=time.monotonic() - self._started,
        )

    def _paint_neon_spectrum(self, painter: QPainter, frame: VisualizerFrame) -> None:
        width, height = self.width(), self.height()
        horizon = height * 0.72
        glow = QRadialGradient(QPointF(width / 2, horizon), width * 0.55)
        glow.setColorAt(0.0, QColor(18, 34, 100, 150))
        glow.setColorAt(1.0, QColor(1, 2, 8, 0))
        painter.fillRect(self.rect(), glow)
        band_width = width / len(frame.spectrum)
        for index, level in enumerate(frame.spectrum):
            bar_height = max(2.0, float(level) * height * 0.62)
            hue = (0.48 + index / len(frame.spectrum) * 0.36 + frame.elapsed * 0.025) % 1.0
            color = QColor.fromHsvF(hue, 0.82, 1.0)
            rect = QRectF(index * band_width + 1, horizon - bar_height, band_width - 2, bar_height)
            gradient = QLinearGradient(0, rect.bottom(), 0, rect.top())
            gradient.setColorAt(0.0, QColor(color.red(), color.green(), color.blue(), 90))
            gradient.setColorAt(1.0, color)
            painter.fillRect(rect, gradient)
            reflection = QRectF(rect.left(), horizon + 2, rect.width(), bar_height * 0.22)
            faded = QColor(color)
            faded.setAlpha(34)
            painter.fillRect(reflection, faded)
        painter.setPen(QPen(QColor(90, 220, 255, 100), 1))
        painter.drawLine(QPointF(0, horizon), QPointF(width, horizon))

    def _paint_radial_bloom(self, painter: QPainter, frame: VisualizerFrame) -> None:
        center = QPointF(self.width() / 2, self.height() / 2)
        base = min(self.width(), self.height()) * (0.13 + frame.bass * 0.05)
        painter.translate(center)
        painter.rotate(frame.elapsed * 7.0)
        for layer in range(5, -1, -1):
            path = QPainterPath()
            count = len(frame.spectrum)
            for index, level in enumerate(frame.spectrum):
                angle = 2.0 * math.pi * index / count
                pulse = float(level) * min(self.width(), self.height()) * 0.28
                radius = base + pulse + layer * 5
                point = QPointF(math.cos(angle) * radius, math.sin(angle) * radius)
                if index == 0:
                    path.moveTo(point)
                else:
                    path.lineTo(point)
            path.closeSubpath()
            color = QColor.fromHsvF((0.78 + layer * 0.045 + frame.elapsed * 0.01) % 1, 0.8, 1)
            color.setAlpha(34 + (5 - layer) * 24)
            painter.setPen(QPen(color, 1.5 + (5 - layer) * 0.35))
            painter.drawPath(path)
        core = QRadialGradient(QPointF(0, 0), base * 1.3)
        core.setColorAt(0, QColor(255, 245, 255, 230))
        core.setColorAt(0.15, QColor(123, 61, 255, 160))
        core.setColorAt(1, QColor(10, 0, 50, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(core)
        painter.drawEllipse(QPointF(0, 0), base * 1.3, base * 1.3)
        painter.resetTransform()

    def _paint_star_tunnel(self, painter: QPainter, frame: VisualizerFrame) -> None:
        center = QPointF(self.width() / 2, self.height() / 2)
        speed = 0.16 + frame.energy * 0.4
        for index in range(120):
            angle = index * 2.39996 + math.sin(index * 0.71) * 0.4
            z = (index / 120.0 - frame.elapsed * speed) % 1.0
            depth = 1.0 / (0.12 + z)
            radius = (8 + (index * 37) % 90) * depth
            x = center.x() + math.cos(angle) * radius * self.width() / 180
            y = center.y() + math.sin(angle) * radius * self.height() / 120
            if 0 <= x < self.width() and 0 <= y < self.height():
                size = min(5.0, 0.7 + depth * 0.7)
                hue = (0.52 + index / 500.0 + frame.elapsed * 0.015) % 1.0
                color = QColor.fromHsvF(hue, 0.55, 1.0)
                color.setAlphaF(min(1.0, 0.18 + (1.0 - z)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawEllipse(QPointF(x, y), size, size)
        painter.setPen(QPen(QColor(90, 190, 255, 100), 1))
        radius = 12 + frame.bass * 34
        painter.drawEllipse(center, radius, radius)

    def _paint_oscilloscope(self, painter: QPainter, frame: VisualizerFrame) -> None:
        width, height = self.width(), self.height()
        painter.setPen(QPen(QColor(20, 70, 60, 55), 1))
        for grid_x in range(0, width, 32):
            painter.drawLine(grid_x, 0, grid_x, height)
        for grid_y in range(0, height, 32):
            painter.drawLine(0, grid_y, width, grid_y)
        samples = frame.samples[:: max(1, frame.samples.size // max(2, width))]
        path = QPainterPath()
        for index, sample in enumerate(samples):
            x = index * width / max(1, len(samples) - 1)
            y = height / 2 - float(sample) * height * 0.42
            if index == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        for pen_width, alpha in ((9, 20), (5, 55), (2, 245)):
            painter.setPen(QPen(QColor(28, 255, 156, alpha), pen_width))
            painter.drawPath(path)

    def _paint_aurora(self, painter: QPainter, frame: VisualizerFrame) -> None:
        width, height = self.width(), self.height()
        for layer in range(7):
            path = QPainterPath()
            base_y = height * (0.2 + layer * 0.1)
            for x in range(0, width + 8, 8):
                band = frame.spectrum[(x // 8 + layer * 7) % len(frame.spectrum)]
                wave = math.sin(x * 0.018 + frame.elapsed * (0.7 + layer * 0.08) + layer)
                y = base_y + wave * (16 + float(band) * 42)
                if x == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            hue = (0.36 + layer * 0.055 + frame.elapsed * 0.008) % 1.0
            color = QColor.fromHsvF(hue, 0.72, 1.0)
            color.setAlpha(40 + layer * 16)
            painter.setPen(QPen(color, 3 + frame.energy * 3))
            painter.drawPath(path)

    def _paint_constellation(self, painter: QPainter, frame: VisualizerFrame) -> None:
        width, height = self.width(), self.height()
        points: list[QPointF] = []
        for index in range(34):
            level = float(frame.spectrum[(index * 7) % len(frame.spectrum)])
            x = ((index * 73.17) % width + math.sin(frame.elapsed * 0.22 + index) * 18) % width
            y = ((index * 41.31) % height + math.cos(frame.elapsed * 0.17 + index) * 14) % height
            points.append(QPointF(x, y))
            color = QColor(125, 235, 255, 120 + int(level * 135))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(points[-1], 1.4 + level * 3.2, 1.4 + level * 3.2)
        painter.setPen(QPen(QColor(91, 135, 255, 45 + int(frame.energy * 60)), 1))
        for index, point in enumerate(points):
            for other in points[index + 1 : index + 6]:
                dx, dy = point.x() - other.x(), point.y() - other.y()
                if dx * dx + dy * dy < 9_000:
                    painter.drawLine(point, other)

    def _paint_vignette(self, painter: QPainter) -> None:
        gradient = QRadialGradient(
            QPointF(self.width() / 2, self.height() / 2),
            max(self.width(), self.height()) * 0.7,
        )
        gradient.setColorAt(0.55, QColor(0, 0, 0, 0))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 185))
        painter.fillRect(self.rect(), gradient)


class VisualizerPanel(QWidget):
    def __init__(self, audio_samples: AudioSampleBuffer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        controls = QWidget(self)
        controls.setObjectName("visualizerControls")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(10, 5, 10, 5)
        controls_layout.addWidget(QLabel("PRESET"))
        selector = QComboBox()
        for preset_id, name in PRESETS:
            selector.addItem(name, preset_id)
        controls_layout.addWidget(selector)
        controls_layout.addStretch(1)
        live = QLabel("● AUDIO REACTIVE")
        live.setObjectName("visualizerLive")
        controls_layout.addWidget(live)
        self._canvas = VisualizerCanvas(audio_samples, self)
        selector.currentIndexChanged.connect(
            lambda index: self._canvas.set_preset(str(selector.itemData(index)))
        )
        layout.addWidget(controls)
        layout.addWidget(self._canvas, 1)
