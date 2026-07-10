"""Metadata extraction for local audio files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import av
from av.audio.stream import AudioStream
from av.container import InputContainer

YEAR_PATTERN = re.compile(r"(?:19|20)\d{2}")


@dataclass(frozen=True)
class LocalTrackMetadata:
    title: str | None = None
    artist: str | None = None
    album_title: str | None = None
    album_artist: str | None = None
    release_year: int | None = None
    genre: str | None = None
    track_number: int | None = None
    disc_number: int | None = None
    duration_seconds: float | None = None


class LocalMetadataReader:
    def read(self, path: Path) -> LocalTrackMetadata:
        try:
            with av.open(str(path)) as container:
                stream = self._audio_stream(container)
                tags = self._normalized_tags(container, stream)
                return self.from_tags(
                    tags,
                    duration_seconds=self._duration_seconds(container, stream),
                )
        except (av.FFmpegError, ValueError):
            return LocalTrackMetadata()

    def from_tags(
        self,
        tags: dict[str, str],
        duration_seconds: float | None = None,
    ) -> LocalTrackMetadata:
        normalized = {
            self._normalize_key(key): value.strip()
            for key, value in tags.items()
            if value.strip()
        }
        return LocalTrackMetadata(
            title=self._first(normalized, "title"),
            artist=self._first(normalized, "artist", "performer", "author"),
            album_title=self._first(normalized, "album"),
            album_artist=self._first(normalized, "album_artist", "albumartist"),
            release_year=self._parse_year(
                self._first(normalized, "date", "year", "originaldate")
            ),
            genre=self._first(normalized, "genre"),
            track_number=self._parse_position(
                self._first(normalized, "track", "tracknumber")
            ),
            disc_number=self._parse_position(
                self._first(normalized, "disc", "discnumber")
            ),
            duration_seconds=duration_seconds,
        )

    def _normalized_tags(
        self,
        container: InputContainer,
        stream: AudioStream,
    ) -> dict[str, str]:
        tags = dict(container.metadata)
        tags.update(stream.metadata)
        return {str(key): str(value) for key, value in tags.items()}

    def _audio_stream(self, container: InputContainer) -> AudioStream:
        if not container.streams.audio:
            raise ValueError("Audio file does not contain an audio stream.")
        return container.streams.audio[0]

    def _duration_seconds(
        self,
        container: InputContainer,
        stream: AudioStream,
    ) -> float | None:
        if stream.duration is not None and stream.time_base is not None:
            return float(stream.duration * stream.time_base)
        if container.duration is not None:
            return float(container.duration) / float(av.time_base)
        return None

    def _normalize_key(self, key: str) -> str:
        return key.strip().lower().replace("-", "_").replace(" ", "_")

    def _first(self, tags: dict[str, str], *keys: str) -> str | None:
        return next((tags[key] for key in keys if tags.get(key)), None)

    def _parse_year(self, value: str | None) -> int | None:
        if value is None:
            return None
        match = YEAR_PATTERN.search(value)
        return int(match.group(0)) if match is not None else None

    def _parse_position(self, value: str | None) -> int | None:
        if value is None:
            return None
        first_part = value.split("/", maxsplit=1)[0].strip()
        return int(first_part) if first_part.isdigit() else None
