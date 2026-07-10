"""Local filesystem media provider."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from datetime import timedelta
from pathlib import Path

from freak_media_player.models.media import Album, Artist, AudioSource, ProviderIdentity, Track
from freak_media_player.providers.base import ProviderCapabilities, SearchQuery
from freak_media_player.providers.local_metadata import LocalMetadataReader

LOCAL_FILE_PROVIDER_ID = "local-files"
UNKNOWN_ARTIST = "Unknown Artist"

SUPPORTED_AUDIO_EXTENSIONS = frozenset(
    {
        ".aac",
        ".aiff",
        ".alac",
        ".flac",
        ".m4a",
        ".mp3",
        ".ogg",
        ".opus",
        ".wav",
        ".wma",
    }
)


class LocalFileProvider:
    provider_id = LOCAL_FILE_PROVIDER_ID
    display_name = "Local Files"
    capabilities = ProviderCapabilities(search=True, streaming=True, library=True)

    def __init__(
        self,
        library_roots: Iterable[Path] | None = None,
        metadata_reader: LocalMetadataReader | None = None,
    ) -> None:
        self._library_roots = tuple(Path(root) for root in library_roots or ())
        self._metadata_reader = metadata_reader or LocalMetadataReader()

    def search_tracks(self, query: SearchQuery) -> list[Track]:
        text = query.text.strip().lower()
        if not text:
            return []

        matches: list[Track] = []
        for path in self._iter_audio_files():
            if text in path.stem.lower():
                matches.append(self.track_from_path(path))
            if len(matches) >= query.limit:
                break
        return matches

    def scan(self, root: Path) -> list[Track]:
        return [self.track_from_path(path) for path in self._iter_audio_files((Path(root),))]

    def resolve_audio_source(self, track: Track) -> AudioSource:
        self._validate_track(track)
        path = Path(track.provider_identity.item_id)
        if not path.exists():
            raise FileNotFoundError(path)
        return AudioSource(uri=path.resolve().as_uri())

    def track_from_path(self, path: Path) -> Track:
        resolved = path.resolve()
        if not self.is_supported_file(resolved):
            raise ValueError(f"Unsupported audio file: {resolved}")
        metadata = self._metadata_reader.read(resolved)
        artist = Artist(name=metadata.artist or UNKNOWN_ARTIST)
        album_artist = Artist(name=metadata.album_artist or artist.name)
        album = None
        if metadata.album_title:
            album = Album(
                title=metadata.album_title,
                artist=album_artist,
                release_year=metadata.release_year,
            )
        return Track(
            id=self._track_id(resolved),
            provider_identity=ProviderIdentity(
                provider_id=self.provider_id,
                item_id=str(resolved),
            ),
            title=metadata.title or resolved.stem,
            artist=artist,
            album=album,
            duration=(
                timedelta(seconds=metadata.duration_seconds)
                if metadata.duration_seconds is not None
                else None
            ),
            genre=metadata.genre,
            track_number=metadata.track_number,
            disc_number=metadata.disc_number,
        )

    def is_supported_file(self, path: Path) -> bool:
        return path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS

    def _iter_audio_files(self, roots: Iterable[Path] | None = None) -> Iterable[Path]:
        for root in roots or self._library_roots:
            if not root.exists():
                continue
            for path in sorted(root.rglob("*")):
                if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS:
                    yield path

    def _track_id(self, path: Path) -> str:
        digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()
        return f"{self.provider_id}:{digest}"

    def _validate_track(self, track: Track) -> None:
        if track.provider_identity.provider_id != self.provider_id:
            raise ValueError("Track does not belong to the local file provider.")
