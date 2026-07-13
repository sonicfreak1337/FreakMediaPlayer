import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTextEdit

from freak_media_player.config.paths import AppPaths
from freak_media_player.player.audio_backend import NullAudioBackend
from freak_media_player.player.playback_controller import PlaybackController
from freak_media_player.player.queue import PlaybackQueue
from freak_media_player.services.diagnostic_service import DiagnosticService
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.utils.logging import configure_logging
from freak_media_player.widgets.about_dialog import AboutDialog
from freak_media_player.widgets.diagnostics_dialog import DiagnosticsDialog
from tests.test_database import make_connection
from tests.test_playback_service import FakeSourceResolver


def make_service(tmp_path: Path) -> DiagnosticService:
    paths = AppPaths(
        data_dir=tmp_path,
        database_path=tmp_path / "player.sqlite3",
        skins_dir=tmp_path / "skins",
        logs_dir=tmp_path / "logs",
    )
    playback = PlaybackService(
        PlaybackController(
            PlaybackQueue(), NullAudioBackend(), FakeSourceResolver()
        )
    )
    return DiagnosticService(paths, make_connection(), playback)


def test_diagnostic_snapshot_contains_runtime_and_sanitized_errors(
    tmp_path: Path,
) -> None:
    service = make_service(tmp_path)
    configure_logging()
    logging.getLogger("diagnostic-test").error("Failed below %s", Path.home())

    snapshot = service.snapshot()

    assert snapshot.app_version
    assert snapshot.database_version == 7
    assert snapshot.audio_output == "Default audio output (stereo)"
    assert snapshot.recent_errors
    assert str(Path.home()) not in snapshot.recent_errors[-1]
    assert "~" in snapshot.recent_errors[-1]


def test_diagnostics_and_about_dialogs_expose_support_information(
    tmp_path: Path,
) -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    diagnostics = DiagnosticsDialog(make_service(tmp_path))
    about = AboutDialog()

    assert diagnostics.findChild(QTextEdit) is not None
    assert any(
        button.text() == "Open log folder"
        for button in diagnostics.findChildren(QPushButton)
    )
    assert any(
        "Runtime components" in label.text() for label in about.findChildren(QLabel)
    )
    diagnostics.close()
    about.close()
