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
    QToolButton,
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
    ("spectral_mandala", "Spectral Mandala"),
    ("cyber_grid", "Cyber Grid"),
    ("liquid_orbit", "Liquid Orbit"),
    ("frequency_city", "Frequency City"),
    ("dna_helix", "DNA Helix"),
    ("solar_flare", "Solar Flare"),
)


@dataclass(frozen=True)
class VisualizerFrame:
    samples: NDArray[np.float32]
    spectrum: NDArray[np.float32]
    energy: float
    bass: float
    mids: float
    treble: float
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
            "spectral_mandala": self._paint_spectral_mandala,
            "cyber_grid": self._paint_cyber_grid,
            "liquid_orbit": self._paint_liquid_orbit,
            "frequency_city": self._paint_frequency_city,
            "dna_helix": self._paint_dna_helix,
            "solar_flare": self._paint_solar_flare,
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
        mids = min(1.0, float(np.mean(self._smoothed[10:36]) * 1.35))
        treble = min(1.0, float(np.mean(self._smoothed[36:]) * 1.3))
        return VisualizerFrame(
            samples=samples,
            spectrum=self._smoothed.copy(),
            energy=energy,
            bass=bass,
            mids=mids,
            treble=treble,
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

    def _paint_spectral_mandala(self, painter: QPainter, frame: VisualizerFrame) -> None:
        center = QPointF(self.width() / 2, self.height() / 2)
        scale = min(self.width(), self.height())
        painter.save()
        painter.translate(center)
        for ring in range(9, -1, -1):
            path = QPainterPath()
            radius = scale * (0.07 + ring * 0.035)
            rotation = frame.elapsed * (0.18 + ring * 0.025) * (-1 if ring % 2 else 1)
            points = 96
            for index in range(points + 1):
                mirrored = index if index < points // 2 else points - index
                band = (mirrored * 3 + ring * 5) % len(frame.spectrum)
                level = float(frame.spectrum[band])
                petals = math.sin(index * math.pi / 6 + ring * 0.7 + frame.elapsed)
                distance = radius + level * scale * 0.075 + petals * scale * 0.012
                angle = index * 2 * math.pi / points + rotation
                point = QPointF(math.cos(angle) * distance, math.sin(angle) * distance)
                if index == 0:
                    path.moveTo(point)
                else:
                    path.lineTo(point)
            hue = (0.68 + ring * 0.045 + frame.elapsed * 0.012) % 1.0
            color = QColor.fromHsvF(hue, 0.76, 1.0)
            color.setAlpha(54 + (9 - ring) * 15)
            painter.setPen(QPen(color, 1.0 + frame.mids * 2.2))
            painter.drawPath(path)
        core = QRadialGradient(QPointF(0, 0), scale * 0.18)
        core.setColorAt(0, QColor(255, 255, 255, 235))
        core.setColorAt(0.18, QColor(86, 193, 255, 210))
        core.setColorAt(0.55, QColor(173, 48, 255, 90))
        core.setColorAt(1, QColor(30, 0, 80, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(core)
        core_size = scale * (0.1 + frame.bass * 0.06)
        painter.drawEllipse(QPointF(0, 0), core_size, core_size)
        painter.restore()

    def _paint_cyber_grid(self, painter: QPainter, frame: VisualizerFrame) -> None:
        width, height = self.width(), self.height()
        horizon = height * 0.36
        sky = QLinearGradient(0, 0, 0, horizon)
        sky.setColorAt(0, QColor(3, 2, 22))
        sky.setColorAt(1, QColor(46, 7, 73))
        painter.fillRect(QRectF(0, 0, width, horizon), sky)
        sun = QRadialGradient(QPointF(width / 2, horizon), height * 0.34)
        sun.setColorAt(0, QColor(255, 65, 190, 155 + int(frame.bass * 80)))
        sun.setColorAt(0.35, QColor(114, 33, 220, 70))
        sun.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), sun)
        painter.setPen(QPen(QColor(29, 238, 255, 120), 1))
        vanishing = QPointF(width / 2, horizon)
        for index in range(-12, 13):
            bottom_x = width / 2 + index * width / 10
            painter.drawLine(vanishing, QPointF(bottom_x, height))
        scroll = (frame.elapsed * (0.55 + frame.energy)) % 1.0
        for row in range(19):
            depth = (row + scroll) / 19
            curved = depth * depth
            y = horizon + curved * (height - horizon)
            alpha = 35 + int(depth * 150)
            painter.setPen(QPen(QColor(40, 182, 255, alpha), 1))
            painter.drawLine(QPointF(0, y), QPointF(width, y))
        ridge = QPainterPath()
        for index, level in enumerate(frame.spectrum):
            x = index * width / (len(frame.spectrum) - 1)
            y = horizon - float(level) * height * 0.25
            if index == 0:
                ridge.moveTo(x, y)
            else:
                ridge.lineTo(x, y)
        painter.setPen(QPen(QColor(255, 60, 210, 210), 2.5))
        painter.drawPath(ridge)

    def _paint_liquid_orbit(self, painter: QPainter, frame: VisualizerFrame) -> None:
        center = QPointF(self.width() / 2, self.height() / 2)
        scale = min(self.width(), self.height())
        background = QRadialGradient(center, scale * 0.8)
        background.setColorAt(0, QColor(12, 36, 58))
        background.setColorAt(0.5, QColor(4, 12, 34))
        background.setColorAt(1, QColor(1, 2, 9))
        painter.fillRect(self.rect(), background)
        for index in range(28):
            level = float(frame.spectrum[(index * 5) % len(frame.spectrum)])
            orbit = scale * (0.12 + (index % 7) * 0.045)
            speed = 0.16 + (index % 5) * 0.035
            angle = index * 2.17 + frame.elapsed * speed * (-1 if index % 2 else 1)
            squash = 0.38 + (index % 3) * 0.1
            point = QPointF(
                center.x() + math.cos(angle) * orbit,
                center.y() + math.sin(angle) * orbit * squash,
            )
            radius = 5 + level * 20 + frame.bass * (8 if index % 4 == 0 else 2)
            blob = QRadialGradient(point, radius * 2.8)
            hue = (0.46 + index * 0.027 + frame.elapsed * 0.008) % 1.0
            color = QColor.fromHsvF(hue, 0.72, 1.0)
            blob.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 220))
            blob.setColorAt(0.28, QColor(color.red(), color.green(), color.blue(), 90))
            blob.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(blob)
            painter.drawEllipse(point, radius * 2.8, radius * 2.8)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for orbit_index in range(4):
            orbit_radius = scale * (0.16 + orbit_index * 0.08)
            color = QColor(66, 229, 255, 35 + orbit_index * 10)
            painter.setPen(QPen(color, 1))
            painter.drawEllipse(center, orbit_radius, orbit_radius * 0.42)

    def _paint_frequency_city(self, painter: QPainter, frame: VisualizerFrame) -> None:
        width, height = self.width(), self.height()
        ground = height * 0.82
        skyline_glow = QLinearGradient(0, height * 0.25, 0, ground)
        skyline_glow.setColorAt(0, QColor(2, 4, 18))
        skyline_glow.setColorAt(1, QColor(17, 20, 62))
        painter.fillRect(self.rect(), skyline_glow)
        count = 32
        building_width = width / count
        for index in range(count):
            near_level = float(frame.spectrum[index * 2])
            far_level = float(frame.spectrum[(index * 2 + 17) % len(frame.spectrum)])
            far_height = 10 + far_level * height * 0.33
            far_x = width / 2 + (index - count / 2) * building_width * 0.62
            far_rect = QRectF(far_x, ground - far_height - 24, building_width * 0.5, far_height)
            painter.fillRect(far_rect, QColor(37, 27, 91, 210))
            building_height = 18 + near_level * height * 0.58
            rect = QRectF(
                index * building_width + 1,
                ground - building_height,
                max(2.0, building_width - 3),
                building_height,
            )
            hue = (0.53 + index / count * 0.18 + frame.elapsed * 0.006) % 1.0
            color = QColor.fromHsvF(hue, 0.68, 0.68)
            painter.fillRect(rect, color)
            window_color = QColor(77, 255, 223, 80 + int(near_level * 150))
            painter.setPen(QPen(window_color, 1))
            for floor_y in range(int(rect.top()) + 7, int(rect.bottom()), 9):
                painter.drawLine(
                    QPointF(rect.left() + 3, floor_y),
                    QPointF(rect.right() - 3, floor_y),
                )
        painter.setPen(QPen(QColor(72, 129, 255, 90), 1))
        for row in range(7):
            y = ground + (row / 6) ** 2 * (height - ground)
            painter.drawLine(QPointF(0, y), QPointF(width, y))

    def _paint_dna_helix(self, painter: QPainter, frame: VisualizerFrame) -> None:
        width, height = self.width(), self.height()
        path_a = QPainterPath()
        path_b = QPainterPath()
        points_a: list[QPointF] = []
        points_b: list[QPointF] = []
        samples = 80
        for index in range(samples):
            x = index * width / (samples - 1)
            level = float(frame.spectrum[(index * len(frame.spectrum)) // samples])
            phase = index * 0.24 - frame.elapsed * (1.4 + frame.bass)
            amplitude = height * (0.18 + level * 0.18)
            center_y = height / 2 + math.sin(index * 0.055 + frame.elapsed * 0.25) * height * 0.08
            point_a = QPointF(x, center_y + math.sin(phase) * amplitude)
            point_b = QPointF(x, center_y + math.sin(phase + math.pi) * amplitude)
            points_a.append(point_a)
            points_b.append(point_b)
            if index == 0:
                path_a.moveTo(point_a)
                path_b.moveTo(point_b)
            else:
                path_a.lineTo(point_a)
                path_b.lineTo(point_b)
        for index in range(0, samples, 4):
            phase = index * 0.24 - frame.elapsed * (1.4 + frame.bass)
            depth = (math.sin(phase) + 1) / 2
            color = QColor(105, 116 + int(depth * 100), 255, 55 + int(depth * 150))
            painter.setPen(QPen(color, 1.0 + depth * 2))
            painter.drawLine(points_a[index], points_b[index])
            painter.setBrush(QColor(238, 92, 255, 170))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(points_a[index], 2.0 + depth * 2, 2.0 + depth * 2)
            painter.setBrush(QColor(70, 244, 255, 170))
            painter.drawEllipse(points_b[index], 2.0 + depth * 2, 2.0 + depth * 2)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(245, 79, 255, 215), 3))
        painter.drawPath(path_a)
        painter.setPen(QPen(QColor(57, 235, 255, 215), 3))
        painter.drawPath(path_b)

    def _paint_solar_flare(self, painter: QPainter, frame: VisualizerFrame) -> None:
        center = QPointF(self.width() / 2, self.height() / 2)
        scale = min(self.width(), self.height())
        core_radius = scale * (0.13 + frame.bass * 0.055)
        corona = QRadialGradient(center, core_radius * 3.5)
        corona.setColorAt(0, QColor(255, 255, 220, 255))
        corona.setColorAt(0.16, QColor(255, 190, 45, 245))
        corona.setColorAt(0.42, QColor(255, 53, 25, 125))
        corona.setColorAt(1, QColor(80, 0, 20, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(corona)
        painter.drawEllipse(center, core_radius * 3.5, core_radius * 3.5)
        painter.save()
        painter.translate(center)
        count = len(frame.spectrum)
        for index, level in enumerate(frame.spectrum):
            angle = index * 2 * math.pi / count + frame.elapsed * 0.07
            level_value = float(level)
            inner = core_radius * (0.85 + math.sin(index * 1.7 + frame.elapsed) * 0.05)
            outer = inner + level_value * scale * 0.27 + (index % 5) * 1.5
            start = QPointF(math.cos(angle) * inner, math.sin(angle) * inner)
            end = QPointF(math.cos(angle) * outer, math.sin(angle) * outer)
            color = QColor(
                255,
                71 + int(level_value * 150),
                22,
                65 + int(level_value * 190),
            )
            painter.setPen(QPen(color, 1.0 + level_value * 3.4))
            painter.drawLine(start, end)
        for flare in range(7):
            radius = core_radius * (1.15 + flare * 0.18)
            start_angle = frame.elapsed * (16 + flare) + flare * 53
            span = 28 + frame.mids * 95
            color = QColor(255, 126 + flare * 12, 36, 130 - flare * 10)
            painter.setPen(QPen(color, 1.5 + frame.energy * 2.5))
            painter.drawArc(
                QRectF(-radius, -radius, radius * 2, radius * 2),
                int(start_angle * 16),
                int(span * 16),
            )
        painter.restore()

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
        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 8, 9, 8)
        layout.setSpacing(9)
        modes = QWidget(self)
        modes.setObjectName("visualizerModes")
        modes.setFixedWidth(92)
        modes_layout = QVBoxLayout(modes)
        modes_layout.setContentsMargins(0, 0, 0, 0)
        modes_layout.setSpacing(7)
        controls = QWidget(self)
        controls.setObjectName("visualizerControls")
        controls.setFixedWidth(190)
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(12, 9, 12, 9)
        controls_layout.setSpacing(7)
        preset_label = QLabel("VISUAL PRESET")
        preset_label.setObjectName("compactLabel")
        controls_layout.addWidget(preset_label)
        selector = QComboBox()
        for preset_id, name in PRESETS:
            selector.addItem(name, preset_id)
        controls_layout.addWidget(selector)
        live = QLabel("● AUDIO REACTIVE")
        live.setObjectName("visualizerLive")
        controls_layout.addWidget(live)
        controls_layout.addWidget(QLabel("12 realtime presets"))
        controls_layout.addStretch(1)
        self._canvas = VisualizerCanvas(audio_samples, self)
        selector.currentIndexChanged.connect(
            lambda index: self._canvas.set_preset(str(selector.itemData(index)))
        )
        for text, preset_index in (("SPECTRUM", 0), ("WAVEFORM", 3), ("SCOPE", 4)):
            button = QToolButton(modes)
            button.setObjectName("visualizerModeButton")
            button.setText(text)
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setChecked(preset_index == 0)
            button.clicked.connect(
                lambda _checked=False, index=preset_index: selector.setCurrentIndex(index)
            )
            modes_layout.addWidget(button)
        modes_layout.addStretch(1)
        layout.addWidget(modes)
        layout.addWidget(self._canvas, 1)
        layout.addWidget(controls)
