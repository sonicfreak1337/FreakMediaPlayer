from pathlib import Path
from unittest.mock import patch

from freak_media_player.app.bootstrap import build_app_context


def test_bootstrap_initializes_database(tmp_path: Path) -> None:
    with patch.dict("os.environ", {"LOCALAPPDATA": str(tmp_path)}):
        context = build_app_context()

        try:
            assert context.app_paths.database_path.exists()
            assert context.database.settings.get("settings.theme_name") == "dark"
        finally:
            context.database.connection.close()
