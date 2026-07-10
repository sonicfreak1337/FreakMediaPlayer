from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from freak_media_player.models.equalizer import EQUALIZER_PRESETS
from freak_media_player.widgets.equalizer_response_graph import EqualizerResponseGraph


def test_equalizer_handle_drag_changes_gain_but_keeps_frequency() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    graph = EqualizerResponseGraph()
    graph.resize(900, 220)
    preset = EQUALIZER_PRESETS[0]
    graph.set_data(preset, (20.0, 20_000.0), (0.0, 0.0))
    graph.show()
    app.processEvents()

    graph_rect = graph._graph_rect()
    handle = graph._band_point(0, graph_rect)
    edits: list[tuple[int, int, float]] = []
    graph.band_edited.connect(
        lambda index, frequency, gain: edits.append((index, frequency, gain))
    )
    graph.mousePressEvent(
        QMouseEvent(
            QEvent.Type.MouseButtonPress,
            handle,
            handle,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
    )
    moved = QPointF(handle.x() + 120.0, handle.y() + 35.0)
    graph.mouseMoveEvent(
        QMouseEvent(
            QEvent.Type.MouseMove,
            moved,
            moved,
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
    )

    assert edits
    assert edits[-1][0] == 0
    assert edits[-1][1] == preset.bands[0].frequency_hz
    assert edits[-1][2] < preset.bands[0].gain_db
    graph.close()
