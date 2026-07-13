"""Private local persistence for radio favorites, history and custom streams."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from freak_media_player.plugins.internet_radio.models import HistoryEntry, RadioStation

CURRENT_RADIO_SCHEMA_VERSION = 1


class RadioStorage:
    def __init__(self, database_path: Path) -> None:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(database_path)
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS favorites "
            "(station_id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
        )
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, station_id TEXT NOT NULL, "
            "played_at TEXT NOT NULL, payload TEXT NOT NULL)"
        )
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS custom_stations "
            "(station_id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
        )
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS plugin_settings "
            "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self._migrate()
        self._connection.commit()

    def _migrate(self) -> None:
        row = self._connection.execute(
            "SELECT value FROM plugin_settings WHERE key = 'schema_version'"
        ).fetchone()
        version = int(row[0]) if row is not None else 0
        if version > CURRENT_RADIO_SCHEMA_VERSION:
            raise ValueError("Radio database schema is newer than this plugin.")
        if version < 1:
            self._connection.execute(
                "INSERT OR REPLACE INTO plugin_settings(key, value) VALUES (?, ?)",
                ("schema_version", str(CURRENT_RADIO_SCHEMA_VERSION)),
            )

    def close(self) -> None:
        self._connection.close()

    def set_favorite(self, station: RadioStation, favorite: bool) -> None:
        if favorite:
            self._connection.execute(
                "INSERT OR REPLACE INTO favorites(station_id, payload) VALUES (?, ?)",
                (station.station_id, self._encode(station)),
            )
        else:
            self._connection.execute(
                "DELETE FROM favorites WHERE station_id = ?", (station.station_id,)
            )
        self._connection.commit()

    def is_favorite(self, station_id: str) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM favorites WHERE station_id = ?", (station_id,)
        ).fetchone()
        return row is not None

    def favorites(self) -> list[RadioStation]:
        rows = self._connection.execute(
            "SELECT payload FROM favorites ORDER BY station_id"
        ).fetchall()
        return [self._decode(row[0]) for row in rows]

    def add_history(self, station: RadioStation) -> None:
        self._connection.execute(
            "INSERT INTO history(station_id, played_at, payload) VALUES (?, ?, ?)",
            (
                station.station_id,
                datetime.now().isoformat(timespec="seconds"),
                self._encode(station),
            ),
        )
        self._connection.execute(
            "DELETE FROM history WHERE id NOT IN "
            "(SELECT id FROM history ORDER BY id DESC LIMIT 200)"
        )
        self._connection.commit()

    def history(self) -> list[HistoryEntry]:
        rows = self._connection.execute(
            "SELECT id, payload, played_at FROM history ORDER BY id DESC LIMIT 200"
        ).fetchall()
        return [
            HistoryEntry(
                self._decode(payload), datetime.fromisoformat(played_at), int(entry_id)
            )
            for entry_id, payload, played_at in rows
        ]

    def delete_history_entry(self, entry_id: int) -> bool:
        cursor = self._connection.execute(
            "DELETE FROM history WHERE id = ?", (entry_id,)
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def clear_history(self) -> None:
        self._connection.execute("DELETE FROM history")
        self._connection.commit()

    def save_custom(self, station: RadioStation) -> None:
        self._connection.execute(
            "INSERT OR REPLACE INTO custom_stations(station_id, payload) VALUES (?, ?)",
            (station.station_id, self._encode(station)),
        )
        self._connection.commit()

    def custom_stations(self) -> list[RadioStation]:
        rows = self._connection.execute(
            "SELECT payload FROM custom_stations ORDER BY station_id"
        ).fetchall()
        return [self._decode(row[0]) for row in rows]

    def delete_custom(self, station_id: str) -> bool:
        cursor = self._connection.execute(
            "DELETE FROM custom_stations WHERE station_id = ?", (station_id,)
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def setting(self, key: str, default: str = "") -> str:
        row = self._connection.execute(
            "SELECT value FROM plugin_settings WHERE key = ?", (key,)
        ).fetchone()
        return str(row[0]) if row is not None else default

    def set_setting(self, key: str, value: str) -> None:
        self._connection.execute(
            "INSERT OR REPLACE INTO plugin_settings(key, value) VALUES (?, ?)",
            (key, value),
        )
        self._connection.commit()

    @staticmethod
    def _encode(station: RadioStation) -> str:
        data = asdict(station)
        data["tags"] = list(station.tags)
        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _decode(payload: str) -> RadioStation:
        data = json.loads(payload)
        data["tags"] = tuple(data.get("tags", ()))
        data["alternative_urls"] = tuple(data.get("alternative_urls", ()))
        return RadioStation(**data)
