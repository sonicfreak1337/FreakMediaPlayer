"""Frameless main-window title bar matching the player chrome."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from freak_media_player import __version__
from freak_media_player.ui.assets import asset_path


class AppTitleBar(QWidget):
    """Compact branded title bar with window controls and drag handling."""

    def __init__(self, window: QMainWindow) -> None:
        super().__init__(window)
        self._window = window
        self._drag_offset: QPoint | None = None
        self.setObjectName("appTitleBar")
        self.setFixedHeight(42)
        self._build_layout()

    def _build_layout(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 8, 4)
        layout.setSpacing(8)

        logo = QLabel()
        logo.setObjectName("titleLogo")
        logo.setPixmap(
            QPixmap(str(asset_path("app_logo.png"))).scaled(
                28,
                28,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        logo.setFixedSize(30, 30)
        logo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        freak = QLabel("Freak")
        freak.setObjectName("appBrandFreak")
        freak.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        brand = QLabel("Media Player")
        brand.setObjectName("appBrand")
        brand.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        version = QLabel(__version__)
        version.setObjectName("appVersion")
        version.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout.addWidget(logo)
        layout.addWidget(freak)
        layout.addWidget(brand)
        layout.addWidget(version)
        layout.addStretch(1)
        layout.addWidget(self._window_button("—", "Minimize", self._window.showMinimized))
        layout.addWidget(self._window_button("□", "Maximize", self._toggle_maximized))
        close = self._window_button("×", "Close", self._window.close)
        close.setObjectName("windowCloseButton")
        layout.addWidget(close)

    def _window_button(
        self,
        text: str,
        tooltip: str,
        handler: Callable[[], object],
    ) -> QToolButton:
        button = QToolButton(self)
        button.setObjectName("windowButton")
        button.setText(text)
        button.setToolTip(tooltip)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        button.setFixedSize(42, 30)
        button.clicked.connect(handler)
        return button

    def _toggle_maximized(self) -> None:
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self._window.pos()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if (
            self._drag_offset is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            if self._window.isMaximized():
                self._window.showNormal()
                self._drag_offset = QPoint(self._window.width() // 2, 20)
            self._window.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximized()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
