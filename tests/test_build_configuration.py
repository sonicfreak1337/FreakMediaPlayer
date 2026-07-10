from pathlib import Path


def test_developer_build_keeps_scipy_runtime_modules() -> None:
    project_root = Path(__file__).resolve().parents[1]
    spec = (project_root / "FreakMediaPlayer.dev.spec").read_text(encoding="utf-8")

    assert '"scipy.' not in spec


def test_builds_bundle_brand_assets_and_windows_icon() -> None:
    project_root = Path(__file__).resolve().parents[1]
    spec = (project_root / "FreakMediaPlayer.dev.spec").read_text(encoding="utf-8")
    release_script = (project_root / "build.bat").read_text(encoding="utf-8")

    assert '"freak_media_player/assets"' in spec
    assert 'icon=str(app_assets / "app_logo.ico")' in spec
    assert "--add-data" in release_script
    assert "app_logo.ico" in release_script
    assert (project_root / "src/freak_media_player/assets/icons/pause_icon.png").exists()
    assert (project_root / "src/freak_media_player/assets/icons/repeat_all_off.png").exists()
    assert (project_root / "src/freak_media_player/assets/icons/repeat_all_on.png").exists()
    assert (project_root / "src/freak_media_player/assets/icons/repeat_one_on.png").exists()
    assert (project_root / "src/freak_media_player/assets/icons/shuffle_off.png").exists()
