"""Plugin contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from PySide6.QtWidgets import QMainWindow

from freak_media_player.player.audio_samples import AudioSampleBuffer


@dataclass(frozen=True)
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    description: str = ""


@dataclass(frozen=True)
class PluginContext:
    application_name: str
    main_window: QMainWindow | None = None
    audio_samples: AudioSampleBuffer | None = None


class Plugin(Protocol):
    manifest: PluginManifest

    def activate(self, context: PluginContext) -> None:
        ...

    def deactivate(self) -> None:
        ...
