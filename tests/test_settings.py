from freak_media_player.config.settings import AppSettings, SettingsMigrator


def test_migrates_version_zero_settings() -> None:
    migrator = SettingsMigrator()

    migrated = migrator.migrate(AppSettings(version=0))

    assert migrated.version == 1


def test_loads_settings_from_mapping() -> None:
    migrator = SettingsMigrator()

    settings = migrator.from_mapping({"version": 1, "theme_name": "dark"})

    assert settings.theme_name == "dark"
