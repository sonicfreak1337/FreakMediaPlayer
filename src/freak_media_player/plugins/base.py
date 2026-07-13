"""Plugin contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from PySide6.QtWidgets import QMainWindow

from freak_media_player.player.audio_samples import AudioSampleBuffer
from freak_media_player.providers.registry import ProviderRegistry
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.services.settings_service import SettingsService


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
    visualizer_quality: str = "balanced"
    provider_registry: ProviderRegistry | None = None
    playback_service: PlaybackService | None = None
    settings_service: SettingsService | None = None
    plugin_data_dir: Path | None = None


class Plugin(Protocol):
    manifest: PluginManifest

    def activate(self, context: PluginContext) -> None:
        ...

    def deactivate(self) -> None:
        ...
