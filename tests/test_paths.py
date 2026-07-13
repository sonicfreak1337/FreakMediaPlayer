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


def test_path_resolver_uses_xdg_data_home_on_linux(tmp_path: Path, monkeypatch) -> None:
    xdg_data_home = tmp_path / "xdg-data"
    monkeypatch.delenv("FREAK_MEDIA_PLAYER_DATA_DIR", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(xdg_data_home))
    monkeypatch.setattr("sys.platform", "linux")

    paths = AppPathResolver().resolve()

    assert paths.data_dir == xdg_data_home / "freak-media-player"


def test_path_resolver_uses_linux_freedesktop_default(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("FREAK_MEDIA_PLAYER_DATA_DIR", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    paths = AppPathResolver().resolve()

    assert paths.data_dir == tmp_path / ".local" / "share" / "freak-media-player"
