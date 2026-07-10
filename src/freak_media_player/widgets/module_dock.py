"""Custom dock chrome for movable, desktop-detachable player modules."""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from freak_media_player.ui.assets import asset_path

MODULE_ICONS = {
    "Local Library": "library_note_icon.png",
    "Playlist": "playlist_icon.png",
    "Equalizer": "equalizer_icon.png",
    "Visualizer": "visualizer_icon.png",
}


class ModuleTitleBar(QWidget):
    """Styled title bar that keeps native dock dragging and adds clear actions."""

    def __init__(
        self,
        dock: QDockWidget,
        title: str,
        closable: bool,
        controls: Iterable[QWidget] = (),
    ) -> None:
        super().__init__(dock)
        self._dock = dock
        self.setObjectName("moduleTitleBar")
        self.setFixedHeight(38)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 3, 8, 3)
        layout.setSpacing(7)

        icon = QLabel()
        icon.setObjectName("moduleIcon")
        icon_name = MODULE_ICONS.get(title)
        if icon_name is not None:
            icon.setPixmap(
                QPixmap(str(asset_path(f"icons/{icon_name}"))).scaled(
                    18,
                    18,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            icon.setText("▶" if title == "Player" else "◆")
        icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        label = QLabel(title.upper())
        label.setObjectName("moduleTitle")
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(icon)
        layout.addWidget(label)
        layout.addStretch(1)

        for control in controls:
            layout.addWidget(control)

        float_button = QToolButton(self)
        float_button.setObjectName("moduleChromeButton")
        float_button.setText("↗")
        float_button.setToolTip("Detach module / dock module")
        float_button.setFixedSize(31, 27)
        float_button.clicked.connect(self._toggle_floating)
        layout.addWidget(float_button)

        if closable:
            close_button = QToolButton(self)
            close_button.setObjectName("moduleChromeButton")
            close_button.setText("—")
            close_button.setToolTip("Close module")
            close_button.setFixedSize(31, 27)
            close_button.clicked.connect(dock.close)
            layout.addWidget(close_button)

    def _toggle_floating(self) -> None:
        self._dock.setFloating(not self._dock.isFloating())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # QDockWidget needs the unhandled event for native drag-to-float behavior.
        event.ignore()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        event.ignore()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        event.ignore()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self._toggle_floating()
        event.accept()


class ModuleDockWidget(QDockWidget):
    """QDockWidget with consistent mockup-inspired title chrome."""

    def __init__(
        self,
        title: str,
        parent: QWidget,
        *,
        closable: bool,
        controls: Iterable[QWidget] = (),
    ) -> None:
        super().__init__(title, parent)
        self._closable = closable
        self.setTitleBarWidget(ModuleTitleBar(self, title, closable, controls))

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._closable:
            event.ignore()
            self.show()
            return
        super().closeEvent(event)
