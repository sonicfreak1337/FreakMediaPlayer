"""Versioned application settings."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

CURRENT_SETTINGS_VERSION = 1


@dataclass(frozen=True)
class AppSettings:
    version: int = CURRENT_SETTINGS_VERSION
    database_path: Path = Path("freak_media_player.sqlite3")
    theme_name: str = "freaky"
    enable_notifications: bool = True


@dataclass(frozen=True)
class PlayerPreferences:
    restore_session: bool = True
    continue_after_track: bool = True
    restore_layout: bool = True
    visualizer_quality: str = "balanced"
    enable_notifications: bool = True
    audio_device_id: str | None = None


class SettingsMigrationError(RuntimeError):
    """Raised when settings cannot be migrated safely."""


class SettingsMigrator:
    def migrate(self, settings: AppSettings) -> AppSettings:
        if settings.version > CURRENT_SETTINGS_VERSION:
            raise SettingsMigrationError("Settings version is newer than this application.")

        migrated = settings
        while migrated.version < CURRENT_SETTINGS_VERSION:
            migrated = self._migrate_one_version(migrated)
        return migrated

    def from_mapping(self, data: dict[str, Any]) -> AppSettings:
        settings = AppSettings(
            version=int(data.get("version", 0)),
            database_path=Path(str(data.get("database_path", "freak_media_player.sqlite3"))),
            theme_name=str(data.get("theme_name", "dark")),
            enable_notifications=self._to_bool(data.get("enable_notifications", True)),
        )
        return self.migrate(settings)

    def _migrate_one_version(self, settings: AppSettings) -> AppSettings:
        if settings.version == 0:
            return replace(settings, version=1)
        raise SettingsMigrationError(f"No migration from version {settings.version}.")

    def _to_bool(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)
