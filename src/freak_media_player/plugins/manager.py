"""Plugin lifecycle management."""

from __future__ import annotations

import logging

from freak_media_player.plugins.base import Plugin, PluginContext

LOGGER = logging.getLogger(__name__)


class PluginManager:
    def __init__(self, context: PluginContext) -> None:
        self._context = context
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        self._plugins[plugin.manifest.plugin_id] = plugin

    def activate_all(self) -> None:
        for plugin in self._plugins.values():
            try:
                plugin.activate(self._context)
            except Exception:
                LOGGER.exception(
                    "Optional plugin failed to activate: %s", plugin.manifest.plugin_id
                )

    def deactivate_all(self) -> None:
        for plugin in reversed(tuple(self._plugins.values())):
            try:
                plugin.deactivate()
            except Exception:
                LOGGER.exception(
                    "Optional plugin failed to deactivate: %s", plugin.manifest.plugin_id
                )
