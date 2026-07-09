"""Reusable collapsible module container."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QSizePolicy, QToolButton, QVBoxLayout, QWidget

COLLAPSED_HORIZONTAL_EXTENT = 150


class CollapsiblePanel(QWidget):
    expanded_changed = Signal(bool)

    def __init__(
        self,
        title: str,
        content: QWidget,
        collapse_orientation: Qt.Orientation,
        expanded: bool = True,
    ) -> None:
        super().__init__()
        self._content = content
        self._collapse_orientation = collapse_orientation
        self._expanded_maximum_width = self.maximumWidth()
        self._expanded_maximum_height = self.maximumHeight()
        self._header = QToolButton()
        self._build_layout(title)
        self.set_expanded(expanded)

    @property
    def content(self) -> QWidget:
        return self._content

    def is_expanded(self) -> bool:
        return self._header.isChecked()

    def set_expanded(self, expanded: bool) -> None:
        changed = self._header.isChecked() != expanded
        self._header.blockSignals(True)
        self._header.setChecked(expanded)
        self._header.blockSignals(False)
        self._content.setVisible(expanded)
        self._header.setArrowType(
            Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow
        )
        self._apply_extent(expanded)
        if changed:
            self.expanded_changed.emit(expanded)

    def _build_layout(self, title: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._header.setObjectName("collapsibleHeader")
        self._header.setText(title)
        self._header.setCheckable(True)
        self._header.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self._header.clicked.connect(self.set_expanded)

        layout.addWidget(self._header)
        layout.addWidget(self._content, 1)

    def _apply_extent(self, expanded: bool) -> None:
        if self._collapse_orientation == Qt.Orientation.Horizontal:
            maximum_width = self._expanded_maximum_width
            if not expanded:
                maximum_width = max(
                    COLLAPSED_HORIZONTAL_EXTENT,
                    self._header.sizeHint().width(),
                )
            self.setMaximumWidth(maximum_width)
        else:
            maximum_height = self._expanded_maximum_height
            if not expanded:
                maximum_height = self._header.sizeHint().height()
            self.setMaximumHeight(maximum_height)
        self.updateGeometry()
