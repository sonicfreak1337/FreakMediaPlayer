from pathlib import Path

from PySide6.QtWidgets import QApplication

from freak_media_player.app.application import _import_command_line_files
from freak_media_player.app.bootstrap import build_app_context
from freak_media_player.models.playback import AudioOutputDevice
from freak_media_player.player.audio_backend import NullAudioBackend
from freak_media_player.widgets.first_start_dialog import FirstStartDialog
from tests.test_local_files import write_audio_file


def test_first_start_dialog_collects_optional_choices(tmp_path: Path) -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    dialog = FirstStartDialog(
        [AudioOutputDevice("headphones", "USB Headphones")]
    )
    dialog._folder.setText(str(tmp_path))
    dialog._audio_device.setCurrentIndex(1)
    dialog._restore_session.setChecked(False)

    choices = dialog.choices()

    assert choices.music_folder == tmp_path
    assert choices.audio_device_id == "headphones"
    assert choices.restore_session is False
    dialog.close()


def test_command_line_audio_is_imported_and_added_to_active_playlist(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "appdata"))
    audio = tmp_path / "Artist - Opened Song.mp3"
    ignored = tmp_path / "notes.txt"
    write_audio_file(audio)
    ignored.write_text("ignore", encoding="utf-8")
    context = build_app_context(NullAudioBackend())

    selected_id = _import_command_line_files(
        context, [str(ignored), str(audio)]
    )

    assert selected_id is not None
    tracks = context.playlist_service.list_tracks()
    assert [track.id for track in tracks] == [selected_id]
    assert tracks[0].artist.name == "Artist"
    assert tracks[0].title == "Opened Song"
    context.database.connection.close()
