"""SQLite connection factory."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class SQLiteConnectionFactory:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
