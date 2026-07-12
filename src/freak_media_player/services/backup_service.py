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
REQUIRED_TABLES = {"settings", "tracks", "playlists", "playlist_tracks"}


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
            with zipfile.ZipFile(package_path) as package:
                self._validate_package(package)
                source_path.write_bytes(package.read(DATABASE_ENTRY))
            source = sqlite3.connect(source_path)
            source.row_factory = sqlite3.Row
            try:
                try:
                    self._validate_database(source)
                    source.backup(self._connection)
                except sqlite3.DatabaseError as error:
                    raise ValueError("Backup database is invalid or damaged.") from error
            finally:
                source.close()
        MigrationRunner().run(self._connection)
        return RestoreResult(safety_backup=safety_backup)

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
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or str(integrity[0]).lower() != "ok":
            raise ValueError("Backup database failed its integrity check.")
        tables = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        if not tables >= REQUIRED_TABLES:
            raise ValueError("Backup database is missing required application data.")
