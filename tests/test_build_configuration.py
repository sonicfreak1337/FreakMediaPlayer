from pathlib import Path


def test_developer_build_keeps_scipy_runtime_modules() -> None:
    project_root = Path(__file__).resolve().parents[1]
    spec = (project_root / "FreakMediaPlayer.dev.spec").read_text(encoding="utf-8")

    assert '"scipy.' not in spec
