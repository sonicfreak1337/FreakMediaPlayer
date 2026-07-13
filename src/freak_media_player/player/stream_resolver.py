"""Bounded resolution of remote PLS and M3U station playlists."""

from __future__ import annotations

import re
from collections.abc import Callable
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_PLAYLIST_BYTES = 256 * 1024
MAX_PLAYLIST_DEPTH = 3
PLAYLIST_TIMEOUT_SECONDS = 6.0
USER_AGENT = "FreakMediaPlayer/1.0"

PlaylistFetcher = Callable[[str, float], tuple[bytes, str]]


class LimitedRedirectHandler(HTTPRedirectHandler):
    max_redirections = 5
    max_repeats = 2


class InvalidStreamPlaylistError(ValueError):
    pass


class NetworkStreamResolver:
    def __init__(self, fetcher: PlaylistFetcher | None = None) -> None:
        self._fetcher = fetcher or self._fetch

    def resolve(self, url: str) -> str:
        current = url
        visited: set[str] = set()
        for _depth in range(MAX_PLAYLIST_DEPTH):
            if not self._looks_like_playlist(current):
                return current
            if current in visited:
                raise InvalidStreamPlaylistError("The stream playlist contains a loop.")
            visited.add(current)
            payload, content_type = self._fetcher(current, PLAYLIST_TIMEOUT_SECONDS)
            target = self._parse(payload, current, content_type)
            if target == current:
                return current
            current = target
        if self._looks_like_playlist(current):
            raise InvalidStreamPlaylistError("The stream playlist is nested too deeply.")
        return current

    @staticmethod
    def _looks_like_playlist(url: str) -> bool:
        path = urlparse(url).path.casefold()
        return path.endswith((".pls", ".m3u", ".m3u8"))

    @staticmethod
    def _parse(payload: bytes, base_url: str, content_type: str) -> str:
        if len(payload) > MAX_PLAYLIST_BYTES:
            raise InvalidStreamPlaylistError("The stream playlist is too large.")
        text = payload.decode("utf-8-sig", errors="replace")
        if "#EXT-X-" in text.upper():
            return base_url  # HLS is decoded by FFmpeg as a playlist, not flattened here.
        suffix = urlparse(base_url).path.casefold()
        is_pls = suffix.endswith(".pls") or "scpls" in content_type.casefold()
        candidates = (
            NetworkStreamResolver._pls_entries(text)
            if is_pls
            else NetworkStreamResolver._m3u_entries(text)
        )
        for value in candidates:
            target = urljoin(base_url, value.strip())
            if urlparse(target).scheme.casefold() in {"http", "https"}:
                return target
        raise InvalidStreamPlaylistError("The playlist contains no valid HTTP(S) audio stream.")

    @staticmethod
    def _pls_entries(text: str) -> list[str]:
        entries: list[tuple[int, str]] = []
        for line in text.splitlines():
            match = re.match(r"\s*File(\d+)\s*=\s*(.+?)\s*$", line, re.IGNORECASE)
            if match is not None:
                entries.append((int(match.group(1)), match.group(2)))
        return [value for _index, value in sorted(entries)]

    @staticmethod
    def _m3u_entries(text: str) -> list[str]:
        return [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]

    @staticmethod
    def _fetch(url: str, timeout: float) -> tuple[bytes, str]:
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "audio/*,*/*"})
        opener = build_opener(LimitedRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            final_url = urlparse(response.geturl())
            if final_url.scheme.casefold() not in {"http", "https"}:
                raise InvalidStreamPlaylistError(
                    "The stream playlist redirected to an unsafe URL."
                )
            payload = response.read(MAX_PLAYLIST_BYTES + 1)
            content_type = response.headers.get_content_type()
            return payload, content_type
