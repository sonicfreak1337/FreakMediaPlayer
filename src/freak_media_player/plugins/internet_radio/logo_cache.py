"""Bounded local cache for untrusted station logos."""

from __future__ import annotations

import hashlib
import os
import time
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_LOGO_BYTES = 2 * 1024 * 1024
MAX_CACHE_BYTES = 24 * 1024 * 1024
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60
DOWNLOAD_TIMEOUT_SECONDS = 6.0
USER_AGENT = "FreakMediaPlayer/1.0"

LogoLoader = Callable[[str, float], tuple[bytes, str]]


class LimitedRedirectHandler(HTTPRedirectHandler):
    max_redirections = 5
    max_repeats = 2


class StationLogoCache:
    def __init__(self, directory: Path, loader: LogoLoader | None = None) -> None:
        self._directory = directory
        self._loader = loader or self._download

    def get(self, url: str) -> Path | None:
        parsed = urlparse(url)
        if parsed.scheme.casefold() not in {"http", "https"} or not parsed.netloc:
            return None
        self._directory.mkdir(parents=True, exist_ok=True)
        destination = self._path_for(url)
        now = time.time()
        if destination.is_file() and now - destination.stat().st_mtime <= CACHE_TTL_SECONDS:
            return destination
        payload, content_type = self._loader(url, DOWNLOAD_TIMEOUT_SECONDS)
        if not content_type.casefold().startswith("image/"):
            raise ValueError("Station logo response is not an image.")
        if not payload or len(payload) > MAX_LOGO_BYTES:
            raise ValueError("Station logo is empty or too large.")
        temporary = destination.with_suffix(".tmp")
        temporary.write_bytes(payload)
        os.replace(temporary, destination)
        self.prune()
        return destination

    def clear(self) -> int:
        if not self._directory.is_dir():
            return 0
        removed = 0
        for path in self._directory.glob("*.img"):
            path.unlink(missing_ok=True)
            removed += 1
        return removed

    def prune(self) -> None:
        files = sorted(
            self._directory.glob("*.img"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        total = 0
        for path in files:
            size = path.stat().st_size
            if total + size <= MAX_CACHE_BYTES:
                total += size
            else:
                path.unlink(missing_ok=True)

    def _path_for(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self._directory / f"{digest}.img"

    @staticmethod
    def _download(url: str, timeout: float) -> tuple[bytes, str]:
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "image/*"})
        opener = build_opener(LimitedRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            final_url = urlparse(response.geturl())
            if final_url.scheme.casefold() not in {"http", "https"}:
                raise ValueError("Station logo redirected to an unsafe URL.")
            payload = response.read(MAX_LOGO_BYTES + 1)
            return payload, response.headers.get_content_type()
