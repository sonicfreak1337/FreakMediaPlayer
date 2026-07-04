from pathlib import Path
from unittest.mock import patch

from freak_media_player.app.bootstrap import build_app_context
from freak_media_player.player.audio_backend import NullAudioBackend


def test_bootstrap_initializes_database(tmp_path: Path) -> None:
    with patch.dict("os.environ", {"LOCALAPPDATA": str(tmp_path)}):
        context = build_app_context(audio_backend=NullAudioBackend())

        try:
            assert context.app_paths.database_path.exists()
            assert context.database.settings.get("settings.theme_name") == "dark"
            assert context.equalizer_service.current_preset().preset_id == "flat"
        finally:
            context.database.connection.close()
