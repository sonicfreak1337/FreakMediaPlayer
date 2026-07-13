import sqlite3
import zipfile
from pathlib import Path

import pytest

from freak_media_player.database.repositories import SQLiteSettingsRepository
from freak_media_player.plugins.internet_radio.models import RadioStation
from freak_media_player.plugins.internet_radio.storage import RadioStorage
from freak_media_player.services.backup_service import BackupService
from tests.test_database import make_connection


def test_backup_round_trip_restores_database_and_creates_safety_copy(
    tmp_path: Path,
) -> None:
    connection = make_connection()
    settings = SQLiteSettingsRepository(connection)
    service = BackupService(connection, tmp_path / "data")
    settings.set("example", "before")
    package = service.export_backup(tmp_path / "my-library")
    settings.set("example", "after")

    result = service.restore_backup(package)

    assert settings.get("example") == "before"
    assert package.suffix == ".freakbackup"
    assert result.safety_backup.is_file()


def test_backup_package_contains_manifest_and_consistent_database(
    tmp_path: Path,
) -> None:
    service = BackupService(make_connection(), tmp_path / "data")

    package = service.export_backup(tmp_path / "library.freakbackup")

    with zipfile.ZipFile(package) as archive:
        assert set(archive.namelist()) == {
            "manifest.json",
            "freak_media_player.sqlite3",
        }


def test_restore_rejects_invalid_package_without_replacing_database(
    tmp_path: Path,
) -> None:
    connection = make_connection()
    settings = SQLiteSettingsRepository(connection)
    settings.set("example", "preserved")
    invalid = tmp_path / "invalid.freakbackup"
    with zipfile.ZipFile(invalid, "w") as archive:
        archive.writestr("manifest.json", '{"format_version":1}')
        archive.writestr("freak_media_player.sqlite3", b"not sqlite")

    with pytest.raises((ValueError, sqlite3.DatabaseError)):
        BackupService(connection, tmp_path / "data").restore_backup(invalid)

    assert settings.get("example") == "preserved"


def test_backup_round_trip_includes_optional_radio_database(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    radio_path = data_dir / "plugins" / "internet-radio.sqlite3"
    favorite = RadioStation(
        "radio-id", "Backup Radio", "https://radio.example/live"
    )
    radio = RadioStorage(radio_path)
    radio.set_favorite(favorite, True)
    radio.close()
    service = BackupService(make_connection(), data_dir)

    package = service.export_backup(tmp_path / "with-radio")
    radio = RadioStorage(radio_path)
    radio.set_favorite(favorite, False)
    radio.close()
    service.restore_backup(package)

    restored = RadioStorage(radio_path)
    assert restored.favorites() == [favorite]
    restored.close()
    with zipfile.ZipFile(package) as archive:
        assert "plugins/internet-radio.sqlite3" in archive.namelist()
