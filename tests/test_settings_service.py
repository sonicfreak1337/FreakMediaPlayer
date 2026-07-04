from pathlib import Path

from freak_media_player.config.settings import AppSettings
from freak_media_player.services.settings_service import SettingsService


class InMemorySettingsRepository:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def set(self, key: str, value: str) -> None:
        self.values[key] = value


def test_settings_service_persists_defaults() -> None:
    repository = InMemorySettingsRepository()
    service = SettingsService(repository=repository)
    defaults = AppSettings(database_path=Path("app.sqlite3"))

    settings = service.load(defaults)

    assert settings.database_path == Path("app.sqlite3")
    assert repository.values["settings.theme_name"] == "dark"


def test_settings_service_reads_saved_values() -> None:
    repository = InMemorySettingsRepository()
    service = SettingsService(repository=repository)
    service.save(
        AppSettings(
            database_path=Path("custom.sqlite3"),
            theme_name="midnight",
            enable_notifications=False,
        )
    )

    settings = service.load(AppSettings())

    assert settings.database_path == Path("custom.sqlite3")
    assert settings.theme_name == "midnight"
    assert settings.enable_notifications is False
