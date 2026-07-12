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
    QPixmap,
    QRadialGradient,
    QShowEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from freak_media_player.player.audio_samples import AudioSampleBuffer

FOREGROUND_FRAME_INTERVAL_MS = 17
BACKGROUND_FRAME_INTERVAL_MS = 50
FFT_SIZE = 2_048
SPECTRUM_BANDS = 64

PRESETS = (
    ("abyssal_cataclysm", "Abyssal Cataclysm"),
    ("freak_pulse", "Freak Pulse"),
    ("fire_of_chaos", "Fire of Chaos"),
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
PRESET_IDS = frozenset(preset_id for preset_id, _name in PRESETS)
SELECTIVE_ANTIALIASING_PRESETS = frozenset(
    {"abyssal_cataclysm", "fire_of_chaos", "oscilloscope"}
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
        self._fft_window = np.hanning(FFT_SIZE).astype(np.float32)
        self._band_starts = np.geomspace(
            1,
            FFT_SIZE // 2 + 1,
            SPECTRUM_BANDS + 1,
        ).astype(int)[:-1]
        self._playback_active = self._audio_samples.playback_active
        self._vignette_cache: QPixmap | None = None
        self._vignette_cache_key: tuple[int, int, float] | None = None
        self._renderers = {
            "freak_pulse": self._paint_freak_pulse,
            "abyssal_cataclysm": self._paint_abyssal_cataclysm,
            "fire_of_chaos": self._paint_fire_of_chaos,
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
        self._timer = QTimer(self)
        self._timer.setInterval(BACKGROUND_FRAME_INTERVAL_MS)
        self._timer.timeout.connect(self._advance_frame)
        self._activity_listener = self._playback_activity_changed
        application = QApplication.instance()
        if isinstance(application, QApplication):
            application.applicationStateChanged.connect(
                self._application_state_changed
            )
        self.setMinimumHeight(170)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

    def set_preset(self, preset_id: str) -> None:
        preset_id = {"fastilicious_inferno": "fire_of_chaos"}.get(
            preset_id,
            preset_id,
        )
        if preset_id in PRESET_IDS:
            self._preset = preset_id
            self.update()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._audio_samples.add_playback_activity_listener(self._activity_listener)
        self._playback_active = self._audio_samples.playback_active
        self._sync_runtime_state()

    def hideEvent(self, event: QHideEvent) -> None:
        self._timer.stop()
        self._audio_samples.set_capture_enabled(False)
        self._audio_samples.remove_playback_activity_listener(self._activity_listener)
        super().hideEvent(event)

    def _advance_frame(self) -> None:
        self.update()

    def _playback_activity_changed(self, active: bool) -> None:
        self._playback_active = active
        self._sync_runtime_state()

    def _application_state_changed(self, _state: Qt.ApplicationState) -> None:
        self._sync_frame_interval()

    def _sync_runtime_state(self) -> None:
        should_run = self._playback_active and self.isVisible()
        self._audio_samples.set_capture_enabled(should_run)
        if not should_run:
            self._timer.stop()
            self._smoothed.fill(0.0)
            self.update()
            return
        self._sync_frame_interval()
        if not self._timer.isActive():
            self._started = time.monotonic()
            self._timer.start()
        self.update()

    def _sync_frame_interval(self) -> None:
        if not self._playback_active or not self.isVisible():
            return
        interval = (
            FOREGROUND_FRAME_INTERVAL_MS
            if self._is_application_focused()
            else BACKGROUND_FRAME_INTERVAL_MS
        )
        if self._timer.interval() != interval:
            self._timer.setInterval(interval)

    @staticmethod
    def _is_application_focused() -> bool:
        return QApplication.applicationState() == Qt.ApplicationState.ApplicationActive

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            self._preset not in SELECTIVE_ANTIALIASING_PRESETS,
        )
        painter.fillRect(self.rect(), QColor("#02030a"))
        if not self._playback_active:
            self._paint_vignette(painter)
            painter.end()
            return
        frame = self._build_frame()
        self._renderers[self._preset](painter, frame)
        self._paint_vignette(painter)
        painter.end()

    def _paint_freak_pulse(self, painter: QPainter, frame: VisualizerFrame) -> None:
        """Brand-native gold/blue spectrum with an electric waveform pulse."""
        width, height = self.width(), self.height()
        horizon = height * 0.73

        background = QLinearGradient(0, 0, width, height)
        background.setColorAt(0.0, QColor("#030917"))
        background.setColorAt(0.46, QColor("#071229"))
        background.setColorAt(1.0, QColor("#010612"))
        painter.fillRect(self.rect(), background)

        ambient = QRadialGradient(QPointF(width * 0.44, horizon), width * 0.52)
        ambient.setColorAt(0.0, QColor(31, 79, 163, 95))
        ambient.setColorAt(0.48, QColor(10, 32, 79, 55))
        ambient.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), ambient)

        painter.setPen(QPen(QColor(36, 59, 91, 65), 1.0))
        for row in range(1, 5):
            y = horizon - row * height * 0.12
            painter.drawLine(QPointF(0, y), QPointF(width, y))

        band_width = width / len(frame.spectrum)
        split = max(1, len(frame.spectrum) // 3)
        for index, level in enumerate(frame.spectrum):
            level_value = float(level)
            bar_height = max(2.0, level_value * height * 0.64)
            if index < split:
                ratio = index / split
                color = QColor(
                    255,
                    round(151 + ratio * 58),
                    round(20 + ratio * 22),
                )
            else:
                ratio = (index - split) / max(1, len(frame.spectrum) - split - 1)
                color = QColor(
                    round(38 + ratio * 33),
                    round(115 + ratio * 91),
                    255,
                )
            rect = QRectF(
                index * band_width + 1.0,
                horizon - bar_height,
                max(1.0, band_width - 2.0),
                bar_height,
            )
            glow = QColor(color)
            glow.setAlpha(42 + round(level_value * 45))
            painter.fillRect(rect.adjusted(-1.5, -2.0, 1.5, 1.0), glow)
            bar_gradient = QLinearGradient(0, rect.bottom(), 0, rect.top())
            base = QColor(color)
            base.setAlpha(90)
            bar_gradient.setColorAt(0.0, base)
            bar_gradient.setColorAt(1.0, color)
            painter.fillRect(rect, bar_gradient)

            reflection = QRectF(
                rect.left(),
                horizon + 2.0,
                rect.width(),
                bar_height * 0.16,
            )
            reflection_color = QColor(color)
            reflection_color.setAlpha(22)
            painter.fillRect(reflection, reflection_color)

        baseline = QLinearGradient(0, horizon, width, horizon)
        baseline.setColorAt(0.0, QColor("#ffb21d"))
        baseline.setColorAt(0.32, QColor("#ffd33d"))
        baseline.setColorAt(0.55, QColor("#4c91ff"))
        baseline.setColorAt(1.0, QColor("#29c5ff"))
        painter.setPen(QPen(baseline, 2.0))
        painter.drawLine(QPointF(0, horizon), QPointF(width, horizon))

        samples = self._waveform_samples(frame.samples, width)
        waveform = QPainterPath()
        wave_center = height * 0.84
        for index, sample in enumerate(samples):
            x = index * width / max(1, len(samples) - 1)
            y = wave_center - float(sample) * height * 0.1
            if index == 0:
                waveform.moveTo(x, y)
            else:
                waveform.lineTo(x, y)
        painter.setPen(QPen(QColor(39, 126, 255, 48), 6.0))
        painter.drawPath(waveform)
        painter.setPen(QPen(QColor("#59a7ff"), 1.4))
        painter.drawPath(waveform)

    def _paint_abyssal_cataclysm(
        self,
        painter: QPainter,
        frame: VisualizerFrame,
    ) -> None:
        """Bombastic water apocalypse driven by bass, spectrum and transients."""
        width, height = self.width(), self.height()
        horizon = height * 0.58
        vortex_center = QPointF(width * 0.5, height * 0.69)
        scale = min(width, height)

        abyss = QLinearGradient(0, 0, 0, height)
        abyss.setColorAt(0.0, QColor("#000108"))
        abyss.setColorAt(0.34, QColor("#001128"))
        abyss.setColorAt(0.68, QColor("#002d57"))
        abyss.setColorAt(1.0, QColor("#00030b"))
        painter.fillRect(self.rect(), abyss)

        pressure = QRadialGradient(vortex_center, width * 0.62)
        pressure.setColorAt(0.0, QColor(27, 195, 255, 90 + int(frame.bass * 80)))
        pressure.setColorAt(0.22, QColor(0, 94, 210, 62))
        pressure.setColorAt(0.58, QColor(0, 24, 83, 25))
        pressure.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), pressure)

        mist = QLinearGradient(0, horizon - height * 0.18, 0, horizon + height * 0.16)
        mist.setColorAt(0.0, QColor(93, 220, 255, 0))
        mist.setColorAt(0.5, QColor(126, 231, 255, 30 + int(frame.mids * 38)))
        mist.setColorAt(1.0, QColor(8, 71, 125, 0))
        painter.fillRect(self.rect(), mist)

        rain_alpha = 20 + int(frame.treble * 88)
        painter.setPen(QPen(QColor(112, 219, 255, rain_alpha), 0.8))
        for index in range(52):
            seed = (index * 0.754877666) % 1.0
            fall = (seed + frame.elapsed * (0.21 + (index % 7) * 0.012)) % 1.0
            x = (seed * width + index * 37.0) % max(1.0, width)
            y = fall * height * 0.78
            painter.drawLine(QPointF(x, y), QPointF(x - 4.0, y + 13.0))

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
        layer_styles = (
            (0.20, 0.31, QColor(0, 25, 94, 225), QColor(0, 89, 178, 70)),
            (0.14, 0.42, QColor(0, 72, 162, 225), QColor(15, 177, 235, 88)),
            (0.08, 0.55, QColor(0, 139, 224, 225), QColor(135, 240, 255, 115)),
        )
        point_count = 72
        for layer_index, (offset, response, deep_color, crest_color) in enumerate(
            layer_styles
        ):
            points: list[QPointF] = []
            for index in range(point_count):
                ratio = index / (point_count - 1)
                spectrum_index = min(
                    len(frame.spectrum) - 1,
                    int(ratio * len(frame.spectrum)),
                )
                level = float(frame.spectrum[spectrum_index])
                cross_wave = abs(math.sin(ratio * math.pi * 3.0 - frame.elapsed * 2.8))
                chaos = math.sin(index * 1.83 + frame.elapsed * (5.1 + layer_index))
                y = (
                    horizon
                    + height * offset
                    - height * level * response
                    - height * cross_wave * (0.045 + frame.bass * 0.065)
                    + chaos * height * 0.012
                )
                points.append(QPointF(ratio * width, y))

            crest = QPainterPath(points[0])
            for point in points[1:]:
                crest.lineTo(point)
            water = QPainterPath(crest)
            water.lineTo(width, height)
            water.lineTo(0.0, height)
            water.closeSubpath()
            fill = QLinearGradient(0, min(point.y() for point in points), 0, height)
            fill.setColorAt(0.0, crest_color)
            fill.setColorAt(0.28, deep_color)
            dark = QColor(deep_color)
            dark.setAlpha(245)
            fill.setColorAt(1.0, dark)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill)
            painter.drawPath(water)

            glow = QColor(88, 221, 255, 60 + layer_index * 32)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(glow, 7.0 - layer_index * 1.7))
            painter.drawPath(crest)
            foam = QColor(202, 250, 255, 135 + layer_index * 38)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(QPen(foam, 1.0 + layer_index * 0.4))
            painter.drawPath(crest)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        core_radius = scale * (0.10 + frame.bass * 0.085)
        core = QRadialGradient(vortex_center, core_radius * 3.4)
        core.setColorAt(0.0, QColor(224, 253, 255, 245))
        core.setColorAt(0.11, QColor(72, 226, 255, 225))
        core.setColorAt(0.33, QColor(0, 96, 232, 130))
        core.setColorAt(0.64, QColor(0, 18, 84, 55))
        core.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), core)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        for ring in range(11):
            radius = scale * (0.075 + ring * 0.035 + frame.bass * 0.012)
            rotation = frame.elapsed * (78 + ring * 6) * (-1 if ring % 2 else 1)
            span = 62 + frame.mids * 120 + (ring % 3) * 24
            color = QColor(
                42 + ring * 8,
                166 + min(80, ring * 7),
                255,
                max(35, 195 - ring * 13),
            )
            painter.setPen(QPen(color, 1.1 + frame.bass * 2.6))
            painter.drawArc(
                QRectF(
                    vortex_center.x() - radius * 1.75,
                    vortex_center.y() - radius * 0.48,
                    radius * 3.5,
                    radius * 0.96,
                ),
                int((rotation + ring * 47) * 16),
                int(span * 16),
            )

        for ring in range(4):
            progress = (frame.elapsed * (0.34 + frame.bass * 0.5) + ring * 0.25) % 1.0
            radius = scale * (0.12 + progress * 0.68)
            alpha = int((1.0 - progress) * (75 + frame.bass * 120))
            painter.setPen(QPen(QColor(72, 215, 255, alpha), 1.2 + frame.bass * 2.0))
            painter.drawEllipse(vortex_center, radius * 2.1, radius * 0.48)

        lightning_alpha = 45 + int(frame.treble * 185)
        for bolt_index in range(4):
            start_x = width * (0.08 + bolt_index * 0.28)
            bolt = QPainterPath(QPointF(start_x, -4.0))
            segments = 13
            for segment in range(1, segments + 1):
                ratio = segment / segments
                target_x = start_x + (vortex_center.x() - start_x) * ratio
                jitter = math.sin(
                    bolt_index * 17.3 + segment * 9.7 + frame.elapsed * 13.0
                )
                x = target_x + jitter * width * 0.018 * (1.0 - ratio)
                y = vortex_center.y() * ratio
                bolt.lineTo(x, y)
            painter.setPen(QPen(QColor(12, 113, 255, lightning_alpha // 3), 8.0))
            painter.drawPath(bolt)
            painter.setPen(QPen(QColor(198, 247, 255, lightning_alpha), 1.25))
            painter.drawPath(bolt)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        for index in range(84):
            seed = (index * 0.61803398875) % 1.0
            travel = (seed + frame.elapsed * (0.12 + (index % 8) * 0.011)) % 1.0
            angle = math.pi * (0.08 + ((index * 0.371) % 0.84))
            distance = travel * width * (0.16 + (index % 9) * 0.022)
            x = vortex_center.x() + math.cos(angle) * distance
            y = (
                vortex_center.y()
                - math.sin(angle) * distance * 0.72
                + travel * travel * height * 0.34
            )
            level = float(frame.spectrum[(index * 5) % len(frame.spectrum)])
            radius = 0.7 + level * 2.2 + (index % 3) * 0.35
            alpha = max(18, int((1.0 - travel) * (80 + frame.treble * 170)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(148, 236, 255, alpha))
            painter.drawEllipse(QPointF(x, y), radius, radius)

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        samples = self._waveform_samples(frame.samples, width)
        pressure_line = QPainterPath()
        line_center = height * 0.82
        for index, sample in enumerate(samples):
            x = index * width / max(1, len(samples) - 1)
            y = line_center - float(sample) * height * (0.07 + frame.energy * 0.08)
            if index == 0:
                pressure_line.moveTo(x, y)
            else:
                pressure_line.lineTo(x, y)
        painter.setPen(QPen(QColor(0, 73, 255, 90), 8.0))
        painter.drawPath(pressure_line)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(184, 249, 255, 225), 1.4))
        painter.drawPath(pressure_line)

    def _paint_fire_of_chaos(
        self,
        painter: QPainter,
        frame: VisualizerFrame,
    ) -> None:
        """Brutal bass-driven flame storm for Fastilicious."""
        width, height = self.width(), self.height()
        floor = height * 0.95

        background = QLinearGradient(0, 0, 0, height)
        background.setColorAt(0.0, QColor("#010101"))
        background.setColorAt(0.42, QColor("#090100"))
        background.setColorAt(0.76, QColor("#210300"))
        background.setColorAt(1.0, QColor("#050000"))
        painter.fillRect(self.rect(), background)

        furnace = QRadialGradient(QPointF(width * 0.5, floor), width * 0.62)
        furnace.setColorAt(0.0, QColor(255, 104, 0, 135 + int(frame.bass * 90)))
        furnace.setColorAt(0.18, QColor(221, 29, 0, 90))
        furnace.setColorAt(0.55, QColor(82, 3, 0, 32))
        furnace.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), furnace)

        impact_radius = height * (0.11 + frame.bass * 0.16)
        impact = QRadialGradient(QPointF(width * 0.5, floor), impact_radius * 3.2)
        impact.setColorAt(0.0, QColor(255, 246, 168, 245))
        impact.setColorAt(0.12, QColor(255, 178, 18, 220))
        impact.setColorAt(0.36, QColor(255, 49, 0, 135))
        impact.setColorAt(1.0, QColor(62, 0, 0, 0))
        painter.fillRect(self.rect(), impact)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        for ring in range(3):
            radius = height * (
                0.18 + ring * 0.11 + (frame.elapsed * (0.42 + frame.bass)) % 0.28
            )
            alpha = max(0, 100 - ring * 24 - int(radius / max(1.0, height) * 42))
            painter.setPen(QPen(QColor(255, 54, 4, alpha), 1.3 + frame.bass * 2.2))
            painter.drawArc(
                QRectF(
                    width * 0.5 - radius * 1.8,
                    floor - radius,
                    radius * 3.6,
                    radius * 2.0,
                ),
                15 * 16,
                150 * 16,
            )

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
        flame_count = 48
        flame_width = width / flame_count
        layer_styles = (
            (0.52, QColor(116, 2, 0, 125), QColor(255, 32, 0, 28)),
            (0.72, QColor(255, 39, 0, 185), QColor(255, 111, 0, 42)),
            (0.92, QColor(255, 183, 16, 235), QColor(255, 246, 166, 58)),
        )
        for layer_index, (height_scale, base_color, tip_color) in enumerate(layer_styles):
            painter.setRenderHint(
                QPainter.RenderHint.Antialiasing,
                layer_index == len(layer_styles) - 1,
            )
            for index in range(flame_count):
                spectrum_index = min(
                    len(frame.spectrum) - 1,
                    int(index * len(frame.spectrum) / flame_count),
                )
                level = float(frame.spectrum[spectrum_index])
                chaos = (
                    0.72
                    + 0.2 * math.sin(index * 2.31 + frame.elapsed * (5.4 + layer_index))
                    + 0.08 * math.sin(index * 0.73 - frame.elapsed * 9.2)
                )
                flame_height = height * (
                    0.09
                    + level * height_scale * max(0.34, chaos)
                    + frame.bass * (0.13 if index % 5 == 0 else 0.035)
                )
                base_x = (index + 0.5) * flame_width
                lean = math.sin(index * 1.77 + frame.elapsed * 7.0) * flame_width * 0.9
                tip = QPointF(base_x + lean, floor - flame_height)
                half_width = flame_width * (0.72 + layer_index * 0.12)
                flame = QPainterPath(QPointF(base_x - half_width, floor + 3.0))
                flame.cubicTo(
                    QPointF(base_x - half_width * 0.8, floor - flame_height * 0.28),
                    QPointF(tip.x() - half_width * 0.45, tip.y() + flame_height * 0.2),
                    tip,
                )
                flame.cubicTo(
                    QPointF(tip.x() + half_width * 0.5, tip.y() + flame_height * 0.22),
                    QPointF(base_x + half_width * 0.82, floor - flame_height * 0.25),
                    QPointF(base_x + half_width, floor + 3.0),
                )
                flame.closeSubpath()
                gradient = QLinearGradient(base_x, floor, tip.x(), tip.y())
                hot = QColor(base_color)
                hot.setAlpha(min(255, hot.alpha() + int(level * 42)))
                gradient.setColorAt(0.0, hot)
                gradient.setColorAt(0.42, base_color)
                gradient.setColorAt(1.0, tip_color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(gradient)
                painter.drawPath(flame)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        for index in range(72):
            seed = (index * 0.61803398875) % 1.0
            travel = (seed + frame.elapsed * (0.08 + (index % 9) * 0.009)) % 1.0
            x = (
                seed * width
                + math.sin(frame.elapsed * (1.8 + index % 5) + index) * width * 0.035
            ) % max(1.0, width)
            y = floor - travel * height * 0.92
            intensity = float(frame.spectrum[(index * 7) % len(frame.spectrum)])
            radius = 0.7 + intensity * 2.4 + (index % 3) * 0.35
            color = QColor(
                255,
                72 + int((1.0 - travel) * 145),
                3,
                max(25, int((1.0 - travel) * (90 + frame.treble * 155))),
            )
            painter.setBrush(color)
            painter.drawEllipse(QPointF(x, y), radius, radius * 1.8)

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        samples = self._waveform_samples(frame.samples, width)
        chaos_line = QPainterPath()
        center_y = floor - height * (0.08 + frame.bass * 0.035)
        for index, sample in enumerate(samples):
            x = index * width / max(1, len(samples) - 1)
            y = center_y - float(sample) * height * (0.05 + frame.energy * 0.06)
            if index == 0:
                chaos_line.moveTo(x, y)
            else:
                chaos_line.lineTo(x, y)
        painter.setPen(QPen(QColor(255, 26, 0, 80), 8.0))
        painter.drawPath(chaos_line)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(255, 212, 46, 220), 1.35))
        painter.drawPath(chaos_line)

    def _build_frame(self) -> VisualizerFrame:
        samples = self._audio_samples.snapshot(FFT_SIZE)
        windowed = samples * self._fft_window
        magnitudes = np.abs(np.fft.rfft(windowed)) / max(1, samples.size)
        spectrum = np.maximum.reduceat(magnitudes, self._band_starts).astype(
            np.float32,
            copy=False,
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

    @staticmethod
    def _waveform_samples(
        samples: NDArray[np.float32],
        width: int,
    ) -> NDArray[np.float32]:
        max_points = max(2, width // 2)
        stride = max(1, math.ceil(samples.size / max_points))
        return samples[::stride]

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
        samples = self._waveform_samples(frame.samples, width)
        path = QPainterPath()
        for index, sample in enumerate(samples):
            x = index * width / max(1, len(samples) - 1)
            y = height / 2 - float(sample) * height * 0.42
            if index == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        for pen_width, alpha in ((9, 20), (5, 55)):
            painter.setPen(QPen(QColor(28, 255, 156, alpha), pen_width))
            painter.drawPath(path)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(28, 255, 156, 245), 2))
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
        device_ratio = self.devicePixelRatioF()
        cache_key = (self.width(), self.height(), device_ratio)
        if self._vignette_cache is None or self._vignette_cache_key != cache_key:
            cache = QPixmap(
                max(1, round(self.width() * device_ratio)),
                max(1, round(self.height() * device_ratio)),
            )
            cache.setDevicePixelRatio(device_ratio)
            cache.fill(Qt.GlobalColor.transparent)
            cache_painter = QPainter(cache)
            gradient = QRadialGradient(
                QPointF(self.width() / 2, self.height() / 2),
                max(self.width(), self.height()) * 0.7,
            )
            gradient.setColorAt(0.55, QColor(0, 0, 0, 0))
            gradient.setColorAt(1.0, QColor(0, 0, 0, 185))
            cache_painter.fillRect(self.rect(), gradient)
            cache_painter.end()
            self._vignette_cache = cache
            self._vignette_cache_key = cache_key
        painter.drawPixmap(0, 0, self._vignette_cache)


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
        selector.setObjectName("visualizerPresetSelector")
        for preset_id, name in PRESETS:
            selector.addItem(name, preset_id)
        controls_layout.addWidget(selector)
        live = QLabel("● AUDIO REACTIVE")
        live.setObjectName("visualizerLive")
        controls_layout.addWidget(live)
        controls_layout.addWidget(QLabel(f"{len(PRESETS)} realtime presets"))
        controls_layout.addStretch(1)
        self._canvas = VisualizerCanvas(audio_samples, self)
        self._selector = selector
        selector.currentIndexChanged.connect(
            lambda index: self._canvas.set_preset(str(selector.itemData(index)))
        )
        for text, preset_id in (
            ("SPECTRUM", "abyssal_cataclysm"),
            ("WAVEFORM", "aurora"),
            ("SCOPE", "oscilloscope"),
        ):
            button = QToolButton(modes)
            button.setObjectName("visualizerModeButton")
            button.setText(text)
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setChecked(preset_id == PRESETS[0][0])
            button.clicked.connect(
                lambda _checked=False, target=preset_id: selector.setCurrentIndex(
                    selector.findData(target)
                )
            )
            modes_layout.addWidget(button)
        modes_layout.addStretch(1)
        layout.addWidget(modes)
        layout.addWidget(self._canvas, 1)
        layout.addWidget(controls)

    def select_skin_preset(self, skin_id: str) -> None:
        """Select the branded preset that belongs to a built-in skin."""
        preset_id = {
            "freaky": "abyssal_cataclysm",
            "fastilicious": "fire_of_chaos",
        }.get(skin_id)
        if preset_id is None:
            return
        index = self._selector.findData(preset_id)
        if index >= 0:
            self._selector.setCurrentIndex(index)
