from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox

from freak_media_player.config.settings import PlayerPreferences
from freak_media_player.models.playback import AudioOutputDevice
from freak_media_player.widgets.settings_dialog import SettingsDialog


def test_settings_dialog_round_trips_preferences() -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    preferences = PlayerPreferences(
        restore_session=False,
        continue_after_track=False,
        restore_layout=False,
        visualizer_quality="eco",
        enable_notifications=False,
        audio_device_id="headphones",
    )
    dialog = SettingsDialog(
        preferences,
        [AudioOutputDevice("headphones", "USB Headphones")],
    )

    assert dialog.preferences() == preferences
    assert len(dialog.findChildren(QCheckBox)) == 4
    assert len(dialog.findChildren(QComboBox)) == 2
    dialog.close()


def test_settings_dialog_falls_back_to_windows_default_for_missing_device() -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    dialog = SettingsDialog(
        PlayerPreferences(audio_device_id="disconnected"),
        [AudioOutputDevice("speakers", "Speakers", True)],
    )

    assert dialog.preferences().audio_device_id is None
    dialog.close()
