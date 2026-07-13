from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QPushButton

from freak_media_player.config.settings import PlayerPreferences
from freak_media_player.models.playback import AudioOutputDevice, AudioOutputMode
from freak_media_player.services.backup_service import BackupService
from freak_media_player.widgets.settings_dialog import SettingsDialog
from tests.test_database import make_connection


def test_settings_dialog_round_trips_preferences() -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    preferences = PlayerPreferences(
        restore_session=False,
        continue_after_track=False,
        restore_layout=False,
        visualizer_quality="eco",
        audio_device_id="headphones",
        internet_radio_enabled=False,
    )
    dialog = SettingsDialog(
        preferences,
        [AudioOutputDevice("headphones", "USB Headphones")],
    )

    assert dialog.preferences() == preferences
    assert len(dialog.findChildren(QCheckBox)) == 4
    assert len(dialog.findChildren(QComboBox)) == 3
    dialog.close()


def test_settings_dialog_falls_back_to_windows_default_for_missing_device() -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    dialog = SettingsDialog(
        PlayerPreferences(audio_device_id="disconnected"),
        [AudioOutputDevice("speakers", "Speakers", True)],
    )

    assert dialog.preferences().audio_device_id is None
    dialog.close()


def test_settings_dialog_only_lists_device_supported_output_modes() -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    dialog = SettingsDialog(
        PlayerPreferences(audio_output_mode="5.1"),
        [
            AudioOutputDevice(
                "speakers",
                "Surround Speakers",
                True,
                (AudioOutputMode.STEREO, AudioOutputMode.SURROUND_5_1),
            )
        ],
    )

    assert dialog.preferences().audio_output_mode == "5.1"
    mode_combo = dialog.findChildren(QComboBox)[1]
    assert [mode_combo.itemData(index) for index in range(mode_combo.count())] == [
        "stereo",
        "5.1",
    ]
    dialog.close()


def test_settings_dialog_exposes_backup_and_restore_actions(tmp_path) -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    dialog = SettingsDialog(
        PlayerPreferences(),
        [],
        backup_service=BackupService(make_connection(), tmp_path),
    )

    labels = {button.text() for button in dialog.findChildren(QPushButton)}

    assert {"Export backup…", "Restore backup…"} <= labels
    dialog.close()
