"""Frameless main-window title bar matching the player chrome."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QMouseEvent
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from freak_media_player import __version__
from freak_media_player.ui.assets import set_themed_pixmap

if TYPE_CHECKING:
    from freak_media_player.ui.skins import SkinManager


class AppTitleBar(QWidget):
    """Compact branded title bar with window controls and drag handling."""

    def __init__(
        self,
        window: QMainWindow,
        skin_manager: SkinManager | None = None,
    ) -> None:
        super().__init__(window)
        self._window = window
        self._skin_manager = skin_manager
        self._skin_selector: QComboBox | None = None
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
        set_themed_pixmap(logo, "app_logo.png", 28, 28)
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
        if self._skin_manager is not None:
            self._build_skin_controls(layout)
        layout.addWidget(self._window_button("—", "Minimize", self._window.showMinimized))
        layout.addWidget(self._window_button("□", "Maximize", self._toggle_maximized))
        close = self._window_button("×", "Close", self._window.close)
        close.setObjectName("windowCloseButton")
        layout.addWidget(close)

    def _build_skin_controls(self, layout: QHBoxLayout) -> None:
        if self._skin_manager is None:
            return
        label = QLabel("SKIN")
        label.setObjectName("skinSelectorLabel")
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        selector = QComboBox(self)
        selector.setObjectName("skinSelector")
        selector.setMinimumWidth(145)
        selector.setToolTip("Choose the active player skin")
        self._skin_selector = selector
        self._populate_skin_selector()
        selector.currentIndexChanged.connect(self._activate_selected_skin)
        self._skin_manager.skin_changed.connect(self._sync_active_skin)
        self._skin_manager.catalog_changed.connect(self._populate_skin_selector)

        reload_button = self._skin_button("↻", "Reload custom skins", self._reload_skins)
        folder_button = self._skin_button(
            "…",
            "Open the custom skins folder",
            self._open_skins_folder,
        )
        layout.addWidget(label)
        layout.addWidget(selector)
        layout.addWidget(reload_button)
        layout.addWidget(folder_button)

    def _skin_button(
        self,
        text: str,
        tooltip: str,
        handler: Callable[[], object],
    ) -> QToolButton:
        button = QToolButton(self)
        button.setObjectName("skinUtilityButton")
        button.setText(text)
        button.setToolTip(tooltip)
        button.setFixedSize(28, 28)
        button.clicked.connect(handler)
        return button

    def _populate_skin_selector(self) -> None:
        if self._skin_manager is None or self._skin_selector is None:
            return
        selector = self._skin_selector
        selector.blockSignals(True)
        selector.clear()
        for skin in self._skin_manager.available_skins():
            selector.addItem(skin.name, skin.skin_id)
            selector.setItemData(
                selector.count() - 1,
                skin.description,
                Qt.ItemDataRole.ToolTipRole,
            )
        selector.blockSignals(False)
        self._sync_active_skin(self._skin_manager.active_skin_id)

    def _activate_selected_skin(self, index: int) -> None:
        if self._skin_manager is None or self._skin_selector is None or index < 0:
            return
        skin_id = self._skin_selector.itemData(index)
        if isinstance(skin_id, str):
            self._skin_manager.activate(skin_id)

    def _sync_active_skin(self, skin_id: str) -> None:
        if self._skin_selector is None:
            return
        index = self._skin_selector.findData(skin_id)
        if index >= 0 and index != self._skin_selector.currentIndex():
            self._skin_selector.blockSignals(True)
            self._skin_selector.setCurrentIndex(index)
            self._skin_selector.blockSignals(False)

    def _reload_skins(self) -> None:
        if self._skin_manager is not None:
            self._skin_manager.reload()

    def _open_skins_folder(self) -> None:
        if self._skin_manager is not None:
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(self._skin_manager.custom_skins_dir))
            )

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
