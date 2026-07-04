from pathlib import Path
from unittest.mock import patch

from freak_media_player.config.paths import AppPathResolver


def test_path_resolver_uses_local_app_data(tmp_path: Path) -> None:
    with patch.dict("os.environ", {"LOCALAPPDATA": str(tmp_path)}):
        paths = AppPathResolver().resolve()

        assert paths.data_dir == tmp_path / "FreakMediaPlayer"
        assert paths.database_path == paths.data_dir / "freak_media_player.sqlite3"
