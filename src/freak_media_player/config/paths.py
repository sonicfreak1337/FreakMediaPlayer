"""Application filesystem paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

APP_DIRECTORY_NAME = "FreakMediaPlayer"
DATABASE_FILE_NAME = "freak_media_player.sqlite3"
SKINS_DIRECTORY_NAME = "skins"
LOGS_DIRECTORY_NAME = "logs"


@dataclass(frozen=True)
class AppPaths:
    data_dir: Path
    database_path: Path
    skins_dir: Path
    logs_dir: Path


class AppPathResolver:
    def resolve(self) -> AppPaths:
        data_dir = self._data_root() / APP_DIRECTORY_NAME
        return AppPaths(
            data_dir=data_dir,
            database_path=data_dir / DATABASE_FILE_NAME,
            skins_dir=data_dir / SKINS_DIRECTORY_NAME,
            logs_dir=data_dir / LOGS_DIRECTORY_NAME,
        )

    def _data_root(self) -> Path:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data)
        return Path.home() / "AppData" / "Local"
