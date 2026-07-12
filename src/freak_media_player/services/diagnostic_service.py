"""Privacy-conscious runtime diagnostics for support and maintenance."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from freak_media_player import __version__
from freak_media_player.config.paths import AppPaths
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.utils.logging import recent_errors


@dataclass(frozen=True)
class DiagnosticSnapshot:
    app_version: str
    database_version: int
    data_dir: Path
    database_path: Path
    logs_dir: Path
    audio_output: str
    recent_errors: tuple[str, ...]


class DiagnosticService:
    def __init__(
        self,
        paths: AppPaths,
        connection: sqlite3.Connection,
        playback_service: PlaybackService,
    ) -> None:
        self._paths = paths
        self._connection = connection
        self._playback_service = playback_service

    def snapshot(self) -> DiagnosticSnapshot:
        row = self._connection.execute(
            "SELECT COALESCE(MAX(version), 0) AS version FROM schema_migrations"
        ).fetchone()
        schema_version = int(row["version"] if row is not None else 0)
        selected = self._playback_service.selected_output_device_id()
        device = next(
            (
                item
                for item in self._playback_service.available_output_devices()
                if item.device_id == selected or (selected is None and item.is_default)
            ),
            None,
        )
        description = device.description if device is not None else "Windows default"
        audio_output = f"{description} ({self._playback_service.output_mode().value})"
        home = str(Path.home())
        errors = tuple(error.replace(home, "%USERPROFILE%") for error in recent_errors())
        return DiagnosticSnapshot(
            app_version=__version__,
            database_version=schema_version,
            data_dir=self._paths.data_dir,
            database_path=self._paths.database_path,
            logs_dir=self._paths.logs_dir,
            audio_output=audio_output,
            recent_errors=errors,
        )
