"""Application filesystem paths."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

APP_DIRECTORY_NAME = "FreakMediaPlayer"
LINUX_APP_DIRECTORY_NAME = "freak-media-player"
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
        data_dir = self._data_dir()
        return AppPaths(
            data_dir=data_dir,
            database_path=data_dir / DATABASE_FILE_NAME,
            skins_dir=data_dir / SKINS_DIRECTORY_NAME,
            logs_dir=data_dir / LOGS_DIRECTORY_NAME,
        )

    def _data_dir(self) -> Path:
        override = os.environ.get("FREAK_MEDIA_PLAYER_DATA_DIR")
        if override:
            return Path(override)
        executable_dir = Path(sys.executable).resolve().parent
        if getattr(sys, "frozen", False) and (executable_dir / "portable.flag").is_file():
            return executable_dir / "data"
        local_app_data = os.environ.get("LOCALAPPDATA")
        if sys.platform == "win32":
            if local_app_data:
                return Path(local_app_data) / APP_DIRECTORY_NAME
            return Path.home() / "AppData" / "Local" / APP_DIRECTORY_NAME
        xdg_data_home = os.environ.get("XDG_DATA_HOME")
        if xdg_data_home:
            return Path(xdg_data_home) / LINUX_APP_DIRECTORY_NAME
        return Path.home() / ".local" / "share" / LINUX_APP_DIRECTORY_NAME
