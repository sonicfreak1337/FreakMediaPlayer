from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDockWidget

from freak_media_player.app.bootstrap import build_app_context
from freak_media_player.player.audio_backend import NullAudioBackend
from freak_media_player.ui.main_window import MainWindow


def test_main_window_registers_movable_visibility_modules(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    context = build_app_context(audio_backend=NullAudioBackend())
    window = MainWindow(
        playback_service=context.playback_service,
        local_library_service=context.local_library_service,
        playlist_service=context.playlist_service,
        equalizer_service=context.equalizer_service,
    )
    window.show()
    app.processEvents()

    player = window.module("playerModule")
    assert player is not None
    assert player.features() & QDockWidget.DockWidgetFeature.DockWidgetMovable
    assert player.features() & QDockWidget.DockWidgetFeature.DockWidgetFloatable
    assert not player.features() & QDockWidget.DockWidgetFeature.DockWidgetClosable
    player.close()
    app.processEvents()
    assert player.isVisible() is True

    module_actions = {action.text(): action for action in window.module_menu.actions()}
    for title, object_name in (
        ("Local Library", "localLibraryModule"),
        ("Playlist", "playlistModule"),
        ("Equalizer", "equalizerModule"),
    ):
        dock = window.module(object_name)
        assert dock is not None
        assert dock.features() & QDockWidget.DockWidgetFeature.DockWidgetMovable
        assert dock.features() & QDockWidget.DockWidgetFeature.DockWidgetFloatable
        assert dock.features() & QDockWidget.DockWidgetFeature.DockWidgetClosable
        assert title in module_actions
        assert window.dockWidgetArea(dock) != Qt.DockWidgetArea.NoDockWidgetArea

    for dock in window.findChildren(QDockWidget):
        dock.setFloating(True)
        app.processEvents()
        assert dock.isFloating() is True
        assert dock.isWindow() is True

    window.close()
    app.processEvents()
    context.database.connection.close()
