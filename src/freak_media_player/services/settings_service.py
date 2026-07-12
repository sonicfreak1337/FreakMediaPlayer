"""Application settings use cases."""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any

from freak_media_player.config.settings import AppSettings, SettingsMigrator
from freak_media_player.core.ports import SettingsRepository
from freak_media_player.models.equalizer import (
    EqualizerBand,
    EqualizerPreset,
    clamp_frequency,
    clamp_gain,
    clamp_preamp,
    clamp_q,
)
from freak_media_player.models.playback import RepeatMode

SETTINGS_VERSION_KEY = "settings.version"
DATABASE_PATH_KEY = "settings.database_path"
THEME_NAME_KEY = "settings.theme_name"
NOTIFICATIONS_KEY = "settings.enable_notifications"
PLAYBACK_VOLUME_KEY = "player.volume"
EQUALIZER_PRESET_KEY = "equalizer.current_preset"
PLAYBACK_SESSION_KEY = "player.last_session"
PLAYBACK_MODES_KEY = "player.playback_modes"


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

    def load_playback_volume(self, default: float = 1.0) -> float:
        """Load a finite, bounded playback volume and repair invalid storage."""
        raw_value = self._repository.get(PLAYBACK_VOLUME_KEY)
        try:
            volume = float(raw_value) if raw_value is not None else float(default)
        except (TypeError, ValueError):
            volume = float(default)
        if not math.isfinite(volume):
            volume = float(default)
        volume = min(1.0, max(0.0, volume))
        self.save_playback_volume(volume)
        return volume

    def save_playback_volume(self, volume: float) -> None:
        bounded = min(1.0, max(0.0, float(volume)))
        self._repository.set(PLAYBACK_VOLUME_KEY, repr(bounded))

    def load_playback_session(self) -> tuple[str, int] | None:
        raw_session = self._repository.get(PLAYBACK_SESSION_KEY)
        if raw_session is None:
            return None
        try:
            data = json.loads(raw_session)
            track_id = str(data["track_id"])
            position_ms = max(0, int(data["position_ms"]))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None
        if not track_id.strip():
            return None
        return track_id, position_ms

    def save_playback_session(self, track_id: str, position_ms: int) -> None:
        data = {"track_id": track_id, "position_ms": max(0, position_ms)}
        self._repository.set(
            PLAYBACK_SESSION_KEY,
            json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        )

    def load_playback_modes(self) -> tuple[RepeatMode, bool]:
        raw_modes = self._repository.get(PLAYBACK_MODES_KEY)
        if raw_modes is None:
            return RepeatMode.OFF, False
        try:
            data = json.loads(raw_modes)
            repeat_mode = RepeatMode(str(data["repeat_mode"]))
            shuffle_enabled = data["shuffle_enabled"]
            if not isinstance(shuffle_enabled, bool):
                raise TypeError("shuffle_enabled must be a boolean")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return RepeatMode.OFF, False
        return repeat_mode, shuffle_enabled

    def save_playback_modes(
        self, repeat_mode: RepeatMode, shuffle_enabled: bool
    ) -> None:
        data = {
            "repeat_mode": repeat_mode.value,
            "shuffle_enabled": bool(shuffle_enabled),
        }
        self._repository.set(
            PLAYBACK_MODES_KEY,
            json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        )

    def load_equalizer_preset(self, default: EqualizerPreset) -> EqualizerPreset:
        """Load the last complete EQ state, falling back if storage is malformed."""
        raw_value = self._repository.get(EQUALIZER_PRESET_KEY)
        if raw_value is None:
            preset = default
        else:
            try:
                preset = self._equalizer_from_data(json.loads(raw_value), default)
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                preset = default
        self.save_equalizer_preset(preset)
        return preset

    def save_equalizer_preset(self, preset: EqualizerPreset) -> None:
        data = {
            "preset_id": preset.preset_id,
            "name": preset.name,
            "preamp_db": preset.preamp_db,
            "bands": [asdict(band) for band in preset.bands],
        }
        self._repository.set(
            EQUALIZER_PRESET_KEY,
            json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        )

    def _equalizer_from_data(
        self,
        data: Any,
        default: EqualizerPreset,
    ) -> EqualizerPreset:
        if not isinstance(data, dict) or not isinstance(data.get("bands"), list):
            raise ValueError("Invalid equalizer settings")
        if len(data["bands"]) != len(default.bands):
            raise ValueError("Unexpected equalizer band count")
        bands = tuple(self._equalizer_band_from_data(item) for item in data["bands"])
        preamp_db = float(data["preamp_db"])
        if not math.isfinite(preamp_db):
            raise ValueError("Invalid equalizer preamp")
        return EqualizerPreset(
            preset_id=str(data["preset_id"]),
            name=str(data["name"]),
            bands=bands,
            preamp_db=clamp_preamp(preamp_db),
        )

    def _equalizer_band_from_data(self, data: Any) -> EqualizerBand:
        if not isinstance(data, dict) or not isinstance(data.get("enabled"), bool):
            raise ValueError("Invalid equalizer band")
        frequency_hz = int(data["frequency_hz"])
        gain_db = float(data["gain_db"])
        q = float(data["q"])
        if not all(math.isfinite(value) for value in (frequency_hz, gain_db, q)):
            raise ValueError("Invalid equalizer band value")
        return EqualizerBand(
            frequency_hz=clamp_frequency(frequency_hz),
            gain_db=clamp_gain(gain_db),
            q=clamp_q(q),
            enabled=data["enabled"],
        )
