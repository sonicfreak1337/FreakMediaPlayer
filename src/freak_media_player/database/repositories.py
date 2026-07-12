"""SQLite repository implementations."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from datetime import timedelta

from freak_media_player.models.media import Album, Artist, ProviderIdentity, Track
from freak_media_player.models.playlist import NamedPlaylist


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
                duration_seconds,
                album_artist,
                release_year,
                genre,
                track_number,
                disc_number
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                provider_id = excluded.provider_id,
                provider_track_id = excluded.provider_track_id,
                title = excluded.title,
                artist = excluded.artist,
                album = excluded.album,
                duration_seconds = excluded.duration_seconds,
                album_artist = excluded.album_artist,
                release_year = excluded.release_year,
                genre = excluded.genre,
                track_number = excluded.track_number,
                disc_number = excluded.disc_number
            """,
            (
                track.id,
                track.provider_identity.provider_id,
                track.provider_identity.item_id,
                track.title,
                track.artist.name,
                track.album.title if track.album else None,
                int(track.duration.total_seconds()) if track.duration else None,
                track.album.artist.name if track.album and track.album.artist else None,
                track.album.release_year if track.album else None,
                track.genre,
                track.track_number,
                track.disc_number,
            ),
        )
        self._connection.commit()

    def get_by_id(self, track_id: str) -> Track | None:
        row = self._connection.execute(
            """
            SELECT
                id, provider_id, provider_track_id, title, artist, album,
                duration_seconds, album_artist, release_year, genre,
                track_number, disc_number
            FROM tracks
            WHERE id = ?
            """,
            (track_id,),
        ).fetchone()
        if row is None:
            return None
        return _track_from_row(row)

    def get_by_provider_item(self, provider_id: str, item_id: str) -> Track | None:
        row = self._connection.execute(
            """
            SELECT
                id, provider_id, provider_track_id, title, artist, album,
                duration_seconds, album_artist, release_year, genre,
                track_number, disc_number
            FROM tracks
            WHERE provider_id = ? AND provider_track_id = ?
            """,
            (provider_id, item_id),
        ).fetchone()
        return _track_from_row(row) if row is not None else None

    def delete(self, track_id: str) -> bool:
        cursor = self._connection.execute(
            "DELETE FROM tracks WHERE id = ?",
            (track_id,),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def list_all(self) -> list[Track]:
        rows = self._connection.execute(
            """
            SELECT
                id, provider_id, provider_track_id, title, artist, album,
                duration_seconds, album_artist, release_year, genre,
                track_number, disc_number
            FROM tracks
            ORDER BY title COLLATE NOCASE, artist COLLATE NOCASE
            """
        ).fetchall()
        return [_track_from_row(row) for row in rows]

    def list_favorite_ids(self) -> set[str]:
        rows = self._connection.execute(
            "SELECT track_id FROM favorite_tracks"
        ).fetchall()
        return {str(row["track_id"]) for row in rows}

    def is_favorite(self, track_id: str) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM favorite_tracks WHERE track_id = ?", (track_id,)
        ).fetchone()
        return row is not None

    def set_favorite(self, track_id: str, favorite: bool) -> None:
        if favorite:
            self._connection.execute(
                "INSERT OR IGNORE INTO favorite_tracks (track_id) VALUES (?)",
                (track_id,),
            )
        else:
            self._connection.execute(
                "DELETE FROM favorite_tracks WHERE track_id = ?", (track_id,)
            )
        self._connection.commit()

    def update_provider_item(self, track_id: str, item_id: str) -> None:
        cursor = self._connection.execute(
            "UPDATE tracks SET provider_track_id = ? WHERE id = ?",
            (item_id, track_id),
        )
        if cursor.rowcount != 1:
            raise KeyError(track_id)
        self._connection.commit()


class SQLitePlaylistRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def ensure(self, playlist_id: str, name: str) -> None:
        self._connection.execute(
            """
            INSERT INTO playlists (id, name)
            VALUES (?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (playlist_id, name),
        )
        self._connection.commit()

    def list_tracks(self, playlist_id: str) -> list[Track]:
        rows = self._connection.execute(
            """
            SELECT
                tracks.id,
                tracks.provider_id,
                tracks.provider_track_id,
                tracks.title,
                tracks.artist,
                tracks.album,
                tracks.duration_seconds,
                tracks.album_artist,
                tracks.release_year,
                tracks.genre,
                tracks.track_number,
                tracks.disc_number
            FROM playlist_tracks
            JOIN tracks ON tracks.id = playlist_tracks.track_id
            WHERE playlist_tracks.playlist_id = ?
            ORDER BY playlist_tracks.position
            """,
            (playlist_id,),
        ).fetchall()
        return [_track_from_row(row) for row in rows]

    def replace_tracks(self, playlist_id: str, tracks: Sequence[Track]) -> None:
        with self._connection:
            self._connection.execute(
                "DELETE FROM playlist_tracks WHERE playlist_id = ?",
                (playlist_id,),
            )
            self._connection.executemany(
                """
                INSERT INTO playlist_tracks (playlist_id, track_id, position)
                VALUES (?, ?, ?)
                """,
                (
                    (playlist_id, track.id, position)
                    for position, track in enumerate(tracks)
                ),
            )
            self._connection.execute(
                "UPDATE playlists SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (playlist_id,),
            )

    def list_playlists(self) -> list[NamedPlaylist]:
        rows = self._connection.execute(
            """
            SELECT id, name, description
            FROM playlists
            ORDER BY name COLLATE NOCASE, created_at
            """
        ).fetchall()
        return [
            NamedPlaylist(
                playlist_id=str(row["id"]),
                name=str(row["name"]),
                description=str(row["description"]),
            )
            for row in rows
        ]

    def rename(self, playlist_id: str, name: str) -> None:
        cursor = self._connection.execute(
            """
            UPDATE playlists
            SET name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (name, playlist_id),
        )
        if cursor.rowcount != 1:
            raise KeyError(playlist_id)
        self._connection.commit()

    def delete(self, playlist_id: str) -> bool:
        cursor = self._connection.execute(
            "DELETE FROM playlists WHERE id = ?", (playlist_id,)
        )
        self._connection.commit()
        return cursor.rowcount > 0


def _track_from_row(row: sqlite3.Row) -> Track:
    artist = Artist(name=str(row["artist"]))
    album_title = row["album"]
    album_artist_name = row["album_artist"]
    duration_seconds = row["duration_seconds"]
    album = None
    if album_title:
        album = Album(
            title=str(album_title),
            artist=Artist(name=str(album_artist_name)) if album_artist_name else artist,
            release_year=(
                int(row["release_year"])
                if row["release_year"] is not None
                else None
            ),
        )
    return Track(
        id=str(row["id"]),
        provider_identity=ProviderIdentity(
            provider_id=str(row["provider_id"]),
            item_id=str(row["provider_track_id"]),
        ),
        title=str(row["title"]),
        artist=artist,
        album=album,
        duration=(
            timedelta(seconds=int(duration_seconds))
            if duration_seconds is not None
            else None
        ),
        genre=str(row["genre"]) if row["genre"] else None,
        track_number=(
            int(row["track_number"]) if row["track_number"] is not None else None
        ),
        disc_number=(
            int(row["disc_number"]) if row["disc_number"] is not None else None
        ),
    )
