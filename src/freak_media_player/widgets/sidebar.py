"""Main navigation sidebar."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from freak_media_player.ui.constants import SIDEBAR_WIDTH
from freak_media_player.ui.navigation import NavigationSection, NavigationViewModel


class Sidebar(QListWidget):
    section_selected = Signal(object)

    def __init__(self, navigation: NavigationViewModel) -> None:
        super().__init__()
        self._navigation = navigation
        self.setFixedWidth(SIDEBAR_WIDTH)
        self._populate()
        self.currentItemChanged.connect(self._handle_current_item_changed)

    def _populate(self) -> None:
        for item in self._navigation.items:
            list_item = QListWidgetItem(item.label)
            list_item.setData(Qt.ItemDataRole.UserRole, item.section)
            self.addItem(list_item)
        self.setCurrentRow(0)

    def _handle_current_item_changed(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return
        section = current.data(Qt.ItemDataRole.UserRole)
        if isinstance(section, NavigationSection):
            self._navigation.select(section)
            self.section_selected.emit(section)
