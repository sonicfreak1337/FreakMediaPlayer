from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDockWidget, QWidget

from freak_media_player.app.application import _reset_window_layout
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

    assert window.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert window.windowFlags() & Qt.WindowType.WindowMinimizeButtonHint
    assert window.windowFlags() & Qt.WindowType.WindowMaximizeButtonHint

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


def test_space_toggles_play_pause_from_main_window(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    context = build_app_context(audio_backend=NullAudioBackend())
    calls = 0
    original_toggle = context.playback_service.toggle_play_pause

    def record_toggle():
        nonlocal calls
        calls += 1
        return original_toggle()

    context.playback_service.toggle_play_pause = record_toggle
    window = MainWindow(
        playback_service=context.playback_service,
        local_library_service=context.local_library_service,
        playlist_service=context.playlist_service,
        equalizer_service=context.equalizer_service,
    )
    window.show()
    window.activateWindow()
    app.processEvents()

    shortcuts = window.findChildren(QShortcut)
    assert any(shortcut.key() == QKeySequence(Qt.Key.Key_Space) for shortcut in shortcuts)
    QTest.keyClick(window, Qt.Key.Key_Space)
    app.processEvents()

    assert calls == 1
    window.close()
    context.database.connection.close()


def test_window_layout_restores_core_and_plugin_modules(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    context = build_app_context(audio_backend=NullAudioBackend())

    first = MainWindow(
        playback_service=context.playback_service,
        local_library_service=context.local_library_service,
        playlist_service=context.playlist_service,
        equalizer_service=context.equalizer_service,
    )
    first_plugin = first.add_module("Test Plugin", QWidget(), "testPluginDock")
    first.resize(1_120, 774)
    first.show()
    app.processEvents()
    library = first.module("localLibraryModule")
    equalizer = first.module("equalizerModule")
    assert library is not None
    assert equalizer is not None
    library.hide()
    equalizer.setFloating(True)
    first_plugin.hide()
    app.processEvents()
    geometry, window_state = first.capture_layout()

    second = MainWindow(
        playback_service=context.playback_service,
        local_library_service=context.local_library_service,
        playlist_service=context.playlist_service,
        equalizer_service=context.equalizer_service,
    )
    second_plugin = second.add_module("Test Plugin", QWidget(), "testPluginDock")
    assert second.restore_layout(geometry, window_state) is True
    second.show()
    app.processEvents()

    restored_library = second.module("localLibraryModule")
    restored_equalizer = second.module("equalizerModule")
    assert restored_library is not None
    assert restored_equalizer is not None
    assert second.size() == first.size()
    assert restored_library.isVisible() is False
    assert restored_equalizer.isFloating() is True
    assert second_plugin.isVisible() is False

    first.close()
    second.close()
    app.processEvents()
    context.database.connection.close()


def test_reset_layout_action_restores_and_persists_startup_layout(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    context = build_app_context(audio_backend=NullAudioBackend())
    window = MainWindow(
        playback_service=context.playback_service,
        local_library_service=context.local_library_service,
        playlist_service=context.playlist_service,
        equalizer_service=context.equalizer_service,
    )
    plugin = window.add_module("Test Plugin", QWidget(), "testPluginDock")
    window.show()
    app.processEvents()
    default_layout = window.capture_layout()
    window.layout_reset_requested.connect(
        lambda: _reset_window_layout(
            window, context.settings_service, default_layout
        )
    )
    library = window.module("localLibraryModule")
    equalizer = window.module("equalizerModule")
    assert library is not None
    assert equalizer is not None
    library.hide()
    equalizer.setFloating(True)
    plugin.hide()
    app.processEvents()

    action = window.findChild(QAction, "resetLayoutAction")
    assert action is not None
    assert action.text() == "Reset Layout"
    action.trigger()
    app.processEvents()

    assert library.isVisible() is True
    assert equalizer.isFloating() is False
    assert plugin.isVisible() is True
    assert context.settings_service.load_window_layout() == window.capture_layout()

    window.close()
    app.processEvents()
    context.database.connection.close()
