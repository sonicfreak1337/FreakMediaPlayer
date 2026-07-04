"""SQLite schema migrations."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Migration:
    version: int
    sql: str


INITIAL_MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version=1,
        sql="""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tracks (
            id TEXT PRIMARY KEY,
            provider_id TEXT NOT NULL,
            provider_track_id TEXT NOT NULL,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            album TEXT,
            duration_seconds INTEGER
        );
        """,
    ),
)


class MigrationRunner:
    def __init__(self, migrations: Iterable[Migration] = INITIAL_MIGRATIONS) -> None:
        self._migrations = tuple(sorted(migrations, key=lambda item: item.version))

    def run(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)"
        )
        applied = {
            row["version"]
            for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
        }

        for migration in self._migrations:
            if migration.version in applied:
                continue
            connection.executescript(migration.sql)
            connection.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)",
                (migration.version,),
            )
        connection.commit()
