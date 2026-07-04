"""Application settings use cases."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from freak_media_player.config.settings import AppSettings, SettingsMigrator
from freak_media_player.core.ports import SettingsRepository

SETTINGS_VERSION_KEY = "settings.version"
DATABASE_PATH_KEY = "settings.database_path"
THEME_NAME_KEY = "settings.theme_name"
NOTIFICATIONS_KEY = "settings.enable_notifications"


class SettingsService:
    def __init__(
        self,
        repository: SettingsRepository,
        migrator: SettingsMigrator | None = None,
    ) -> None:
        self._repository = repository
        self._migrator = migrator or SettingsMigrator()

    def load(self, defaults: AppSettings) -> AppSettings:
        data = {
            "version": self._repository.get(SETTINGS_VERSION_KEY) or defaults.version,
            "database_path": self._repository.get(DATABASE_PATH_KEY) or defaults.database_path,
            "theme_name": self._repository.get(THEME_NAME_KEY) or defaults.theme_name,
            "enable_notifications": self._repository.get(NOTIFICATIONS_KEY)
            or defaults.enable_notifications,
        }
        settings = self._migrator.from_mapping(data)
        self.save(settings)
        return settings

    def save(self, settings: AppSettings) -> None:
        values = asdict(settings)
        self._repository.set(SETTINGS_VERSION_KEY, str(values["version"]))
        self._repository.set(DATABASE_PATH_KEY, str(values["database_path"]))
        self._repository.set(THEME_NAME_KEY, str(values["theme_name"]))
        self._repository.set(NOTIFICATIONS_KEY, str(values["enable_notifications"]))

    def set_theme_name(self, theme_name: str) -> AppSettings:
        current = self.load(AppSettings())
        updated = AppSettings(
            version=current.version,
            database_path=current.database_path,
            theme_name=theme_name,
            enable_notifications=current.enable_notifications,
        )
        self.save(updated)
        return updated

    def set_database_path(self, database_path: Path) -> AppSettings:
        current = self.load(AppSettings())
        updated = AppSettings(
            version=current.version,
            database_path=database_path,
            theme_name=current.theme_name,
            enable_notifications=current.enable_notifications,
        )
        self.save(updated)
        return updated
