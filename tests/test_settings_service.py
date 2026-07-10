from pathlib import Path

from freak_media_player.config.settings import AppSettings
from freak_media_player.models.equalizer import EQUALIZER_PRESETS, EqualizerBand, EqualizerPreset
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


def test_settings_service_round_trips_volume_and_complete_equalizer_state() -> None:
    repository = InMemorySettingsRepository()
    service = SettingsService(repository=repository)
    custom = EqualizerPreset(
        preset_id="custom",
        name="Custom",
        bands=tuple(
            EqualizerBand(
                frequency_hz=band.frequency_hz,
                gain_db=index - 4.5,
                q=band.q + 0.1,
                enabled=index != 3,
            )
            for index, band in enumerate(EQUALIZER_PRESETS[0].bands)
        ),
        preamp_db=-3.5,
    )

    service.save_playback_volume(0.37)
    service.save_equalizer_preset(custom)

    assert service.load_playback_volume() == 0.37
    assert service.load_equalizer_preset(EQUALIZER_PRESETS[0]) == custom


def test_settings_service_repairs_invalid_runtime_settings() -> None:
    repository = InMemorySettingsRepository()
    repository.values["player.volume"] = "not-a-number"
    repository.values["equalizer.current_preset"] = "{broken"
    service = SettingsService(repository=repository)

    assert service.load_playback_volume(0.8) == 0.8
    assert service.load_equalizer_preset(EQUALIZER_PRESETS[0]) == EQUALIZER_PRESETS[0]


def test_settings_service_round_trips_last_track_and_position() -> None:
    repository = InMemorySettingsRepository()
    service = SettingsService(repository=repository)

    service.save_playback_session("track-42", 123_456)

    assert service.load_playback_session() == ("track-42", 123_456)
