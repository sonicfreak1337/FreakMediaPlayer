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


def test_bootstrap_restores_last_volume_and_equalizer(tmp_path: Path) -> None:
    with patch.dict("os.environ", {"LOCALAPPDATA": str(tmp_path)}):
        first = build_app_context(audio_backend=NullAudioBackend())
        first.playback_service.set_volume(0.42)
        expected_preset = first.equalizer_service.update_band(
            2,
            frequency_hz=140,
            gain_db=4.5,
            q=1.8,
            enabled=False,
        )
        first.database.connection.close()

        second = build_app_context(audio_backend=NullAudioBackend())
        try:
            assert second.playback_service.volume() == 0.42
            assert second.equalizer_service.current_preset() == expected_preset
        finally:
            second.database.connection.close()
