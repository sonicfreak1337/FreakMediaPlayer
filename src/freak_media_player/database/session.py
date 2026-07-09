"""Database initialization helpers."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from freak_media_player.database.connection import SQLiteConnectionFactory
from freak_media_player.database.migrations import MigrationRunner
from freak_media_player.database.repositories import (
    SQLitePlaylistRepository,
    SQLiteSettingsRepository,
    SQLiteTrackRepository,
)


@dataclass(frozen=True)
class DatabaseSession:
    connection: sqlite3.Connection
    playlists: SQLitePlaylistRepository
    settings: SQLiteSettingsRepository
    tracks: SQLiteTrackRepository


class DatabaseSessionFactory:
    def __init__(
        self,
        database_path: Path,
        migration_runner: MigrationRunner | None = None,
    ) -> None:
        self._database_path = database_path
        self._migration_runner = migration_runner or MigrationRunner()

    def create(self) -> DatabaseSession:
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = SQLiteConnectionFactory(self._database_path).connect()
        self._migration_runner.run(connection)
        return DatabaseSession(
            connection=connection,
            playlists=SQLitePlaylistRepository(connection),
            settings=SQLiteSettingsRepository(connection),
            tracks=SQLiteTrackRepository(connection),
        )
