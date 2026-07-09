from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget

from freak_media_player.widgets.collapsible_panel import (
    COLLAPSED_HORIZONTAL_EXTENT,
    CollapsiblePanel,
)


def test_collapsible_panel_hides_and_restores_content() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    content = QWidget()
    panel = CollapsiblePanel(
        "Library",
        content=content,
        collapse_orientation=Qt.Orientation.Horizontal,
    )

    panel.set_expanded(False)

    assert panel.is_expanded() is False
    assert content.isHidden() is True
    assert panel.maximumWidth() == COLLAPSED_HORIZONTAL_EXTENT

    panel.set_expanded(True)
    app.processEvents()

    assert panel.is_expanded() is True
    assert content.isHidden() is False
