"""SQLite repository implementations."""

from __future__ import annotations

import sqlite3
from datetime import timedelta

from freak_media_player.models.media import Album, Artist, ProviderIdentity, Track


class SQLiteSettingsRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, key: str) -> str | None:
        row = self._connection.execute(
            "SELECT value FROM settings WHERE key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        return str(row["value"])

    def set(self, key: str, value: str) -> None:
        self._connection.execute(
            """
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        self._connection.commit()


class SQLiteTrackRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def save(self, track: Track) -> None:
        self._connection.execute(
            """
            INSERT INTO tracks (
                id,
                provider_id,
                provider_track_id,
                title,
                artist,
                album,
                duration_seconds
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                provider_id = excluded.provider_id,
                provider_track_id = excluded.provider_track_id,
                title = excluded.title,
                artist = excluded.artist,
                album = excluded.album,
                duration_seconds = excluded.duration_seconds
            """,
            (
                track.id,
                track.provider_identity.provider_id,
                track.provider_identity.item_id,
                track.title,
                track.artist.name,
                track.album.title if track.album else None,
                int(track.duration.total_seconds()) if track.duration else None,
            ),
        )
        self._connection.commit()

    def get_by_id(self, track_id: str) -> Track | None:
        row = self._connection.execute(
            """
            SELECT id, provider_id, provider_track_id, title, artist, album, duration_seconds
            FROM tracks
            WHERE id = ?
            """,
            (track_id,),
        ).fetchone()
        if row is None:
            return None
        return self._from_row(row)

    def list_all(self) -> list[Track]:
        rows = self._connection.execute(
            """
            SELECT id, provider_id, provider_track_id, title, artist, album, duration_seconds
            FROM tracks
            ORDER BY title COLLATE NOCASE, artist COLLATE NOCASE
            """
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def _from_row(self, row: sqlite3.Row) -> Track:
        artist = Artist(name=str(row["artist"]))
        album_title = row["album"]
        duration_seconds = row["duration_seconds"]
        return Track(
            id=str(row["id"]),
            provider_identity=ProviderIdentity(
                provider_id=str(row["provider_id"]),
                item_id=str(row["provider_track_id"]),
            ),
            title=str(row["title"]),
            artist=artist,
            album=Album(title=str(album_title), artist=artist) if album_title else None,
            duration=(
                timedelta(seconds=int(duration_seconds))
                if duration_seconds is not None
                else None
            ),
        )
