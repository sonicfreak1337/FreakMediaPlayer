"""Validated backup and restore packages for all local application data."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from freak_media_player import __version__
from freak_media_player.database.migrations import MigrationRunner

BACKUP_FORMAT_VERSION = 1
DATABASE_ENTRY = "freak_media_player.sqlite3"
MANIFEST_ENTRY = "manifest.json"
RADIO_DATABASE_ENTRY = "plugins/internet-radio.sqlite3"
RADIO_DATABASE_RELATIVE_PATH = Path("plugins/internet-radio.sqlite3")
REQUIRED_TABLES = {"settings", "tracks", "playlists", "playlist_tracks"}
REQUIRED_RADIO_TABLES = {"favorites", "history", "custom_stations", "plugin_settings"}


@dataclass(frozen=True)
class RestoreResult:
    safety_backup: Path


class BackupService:
    def __init__(self, connection: sqlite3.Connection, data_dir: Path) -> None:
        self._connection = connection
        self._data_dir = data_dir

    def export_backup(self, destination: Path) -> Path:
        destination = destination.with_suffix(".freakbackup")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
            temporary_dir = Path(temporary)
            snapshot = temporary_dir / DATABASE_ENTRY
            snapshot_connection = sqlite3.connect(snapshot)
            try:
                self._connection.backup(snapshot_connection)
            finally:
                snapshot_connection.close()
            archive = temporary_dir / destination.name
            manifest = {
                "format_version": BACKUP_FORMAT_VERSION,
                "app_version": __version__,
                "created_at": datetime.now(UTC).isoformat(),
            }
            with zipfile.ZipFile(
                archive, "w", compression=zipfile.ZIP_DEFLATED
            ) as package:
                package.writestr(MANIFEST_ENTRY, json.dumps(manifest, indent=2))
                package.write(snapshot, DATABASE_ENTRY)
                radio_database = self._data_dir / RADIO_DATABASE_RELATIVE_PATH
                if radio_database.is_file():
                    radio_snapshot = temporary_dir / "internet-radio.sqlite3"
                    self._snapshot_database(radio_database, radio_snapshot)
                    package.write(radio_snapshot, RADIO_DATABASE_ENTRY)
            os.replace(archive, destination)
        return destination

    def restore_backup(self, package_path: Path) -> RestoreResult:
        if not package_path.is_file():
            raise ValueError("Backup package does not exist.")
        safety_dir = self._data_dir / "backups"
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safety_backup = self.export_backup(safety_dir / f"before-restore-{stamp}")
        with tempfile.TemporaryDirectory(dir=self._data_dir) as temporary:
            source_path = Path(temporary) / DATABASE_ENTRY
            radio_source_path = Path(temporary) / "internet-radio.sqlite3"
            with zipfile.ZipFile(package_path) as package:
                self._validate_package(package)
                source_path.write_bytes(package.read(DATABASE_ENTRY))
                has_radio_database = RADIO_DATABASE_ENTRY in package.namelist()
                if has_radio_database:
                    radio_source_path.write_bytes(package.read(RADIO_DATABASE_ENTRY))
            source = sqlite3.connect(source_path)
            source.row_factory = sqlite3.Row
            try:
                try:
                    self._validate_database(source)
                    if has_radio_database:
                        radio_validation = sqlite3.connect(radio_source_path)
                        radio_validation.row_factory = sqlite3.Row
                        try:
                            self._validate_tables(
                                radio_validation, REQUIRED_RADIO_TABLES
                            )
                        finally:
                            radio_validation.close()
                    source.backup(self._connection)
                except sqlite3.DatabaseError as error:
                    raise ValueError("Backup database is invalid or damaged.") from error
            finally:
                source.close()
            if has_radio_database:
                self._restore_plugin_database(
                    radio_source_path,
                    self._data_dir / RADIO_DATABASE_RELATIVE_PATH,
                    REQUIRED_RADIO_TABLES,
                )
        MigrationRunner().run(self._connection)
        return RestoreResult(safety_backup=safety_backup)

    @staticmethod
    def _snapshot_database(source_path: Path, destination_path: Path) -> None:
        source = sqlite3.connect(source_path)
        destination = sqlite3.connect(destination_path)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()

    @staticmethod
    def _restore_plugin_database(
        source_path: Path,
        destination_path: Path,
        required_tables: set[str],
    ) -> None:
        source = sqlite3.connect(source_path)
        source.row_factory = sqlite3.Row
        try:
            BackupService._validate_tables(source, required_tables)
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            destination = sqlite3.connect(destination_path)
            try:
                source.backup(destination)
            finally:
                destination.close()
        finally:
            source.close()

    def _validate_package(self, package: zipfile.ZipFile) -> None:
        names = set(package.namelist())
        if not {MANIFEST_ENTRY, DATABASE_ENTRY} <= names:
            raise ValueError("Backup package is incomplete.")
        try:
            manifest = json.loads(package.read(MANIFEST_ENTRY))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Backup manifest is invalid.") from error
        if manifest.get("format_version") != BACKUP_FORMAT_VERSION:
            raise ValueError("Backup format is not supported.")

    def _validate_database(self, connection: sqlite3.Connection) -> None:
        self._validate_tables(connection, REQUIRED_TABLES)

    @staticmethod
    def _validate_tables(connection: sqlite3.Connection, required_tables: set[str]) -> None:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or str(integrity[0]).lower() != "ok":
            raise ValueError("Backup database failed its integrity check.")
        tables = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        if not tables >= required_tables:
            raise ValueError("Backup database is missing required application data.")
