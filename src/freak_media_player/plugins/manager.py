"""Plugin lifecycle management."""

from __future__ import annotations

from freak_media_player.plugins.base import Plugin, PluginContext


class PluginManager:
    def __init__(self, context: PluginContext) -> None:
        self._context = context
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        self._plugins[plugin.manifest.plugin_id] = plugin

    def activate_all(self) -> None:
        for plugin in self._plugins.values():
            plugin.activate(self._context)

    def deactivate_all(self) -> None:
        for plugin in reversed(tuple(self._plugins.values())):
            plugin.deactivate()
