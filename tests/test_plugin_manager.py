from __future__ import annotations

from freak_media_player.app.application import _register_plugins
from freak_media_player.config.settings import PlayerPreferences
from freak_media_player.plugins.base import PluginContext, PluginManifest
from freak_media_player.plugins.manager import PluginManager


class StubPlugin:
    def __init__(self, plugin_id: str, *, fail: bool = False) -> None:
        self.manifest = PluginManifest(plugin_id, plugin_id, "1.0.0")
        self.fail = fail
        self.activated = False
        self.deactivated = False

    def activate(self, _context: PluginContext) -> None:
        if self.fail:
            raise RuntimeError("activation failed")
        self.activated = True

    def deactivate(self) -> None:
        if self.fail:
            raise RuntimeError("deactivation failed")
        self.deactivated = True


def test_plugin_failures_do_not_block_other_optional_plugins() -> None:
    manager = PluginManager(PluginContext("Test"))
    failing = StubPlugin("failing", fail=True)
    healthy = StubPlugin("healthy")
    manager.register(failing)
    manager.register(healthy)

    manager.activate_all()
    manager.deactivate_all()

    assert healthy.activated is True
    assert healthy.deactivated is True


def test_disabled_internet_radio_registers_no_radio_plugin() -> None:
    manager = PluginManager(PluginContext("Test"))

    _register_plugins(
        manager,
        PlayerPreferences(internet_radio_enabled=False),
    )

    assert "freak.visualizer" in manager._plugins
    assert "freak.internet-radio" not in manager._plugins
