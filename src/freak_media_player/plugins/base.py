"""Plugin contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    description: str = ""


@dataclass(frozen=True)
class PluginContext:
    application_name: str


class Plugin(Protocol):
    manifest: PluginManifest

    def activate(self, context: PluginContext) -> None:
        ...

    def deactivate(self) -> None:
        ...
