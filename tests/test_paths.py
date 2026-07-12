from pathlib import Path

from freak_media_player.config.paths import AppPathResolver


def test_path_resolver_uses_isolated_explicit_data_directory(
    tmp_path: Path, monkeypatch
) -> None:
    portable_data = tmp_path / "portable-data"
    monkeypatch.setenv("FREAK_MEDIA_PLAYER_DATA_DIR", str(portable_data))

    paths = AppPathResolver().resolve()

    assert paths.data_dir == portable_data
    assert paths.database_path.parent == portable_data
    assert paths.logs_dir == portable_data / "logs"
