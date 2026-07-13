"""Bounded connection probe for manually entered radio streams."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import Request, build_opener

from freak_media_player.player.stream_resolver import (
    LimitedRedirectHandler,
    NetworkStreamResolver,
)

PROBE_BYTES = 1024
PROBE_TIMEOUT_SECONDS = 7.0


@dataclass(frozen=True)
class StreamProbeResult:
    resolved_url: str
    content_type: str


def probe_stream_url(url: str) -> StreamProbeResult:
    resolved = NetworkStreamResolver().resolve(url)
    request = Request(
        resolved,
        headers={
            "User-Agent": "FreakMediaPlayer/1.0",
            "Accept": "audio/*,*/*",
            "Icy-MetaData": "1",
            "Range": f"bytes=0-{PROBE_BYTES - 1}",
        },
    )
    opener = build_opener(LimitedRedirectHandler())
    with opener.open(request, timeout=PROBE_TIMEOUT_SECONDS) as response:
        final_url = response.geturl()
        parsed = urlparse(final_url)
        if parsed.scheme.casefold() not in {"http", "https"}:
            raise ValueError("The stream redirected to an unsafe URL.")
        payload = response.read(PROBE_BYTES)
        if not payload:
            raise ValueError("The stream returned no audio data.")
        content_type = response.headers.get_content_type()
        return StreamProbeResult(final_url, content_type)
