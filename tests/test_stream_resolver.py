from __future__ import annotations

import pytest

from freak_media_player.player.stream_resolver import (
    InvalidStreamPlaylistError,
    NetworkStreamResolver,
)


def test_pls_resolves_first_numbered_http_stream() -> None:
    payload = b"[playlist]\nFile2=https://radio.example/backup\nFile1=https://radio.example/live\n"
    resolver = NetworkStreamResolver(fetcher=lambda _url, _timeout: (payload, "audio/x-scpls"))

    assert resolver.resolve("https://directory.example/station.pls") == (
        "https://radio.example/live"
    )


def test_m3u_resolves_relative_stream_url() -> None:
    payload = b"#EXTM3U\n#EXTINF:-1,Station\nstreams/live.mp3\n"
    resolver = NetworkStreamResolver(fetcher=lambda _url, _timeout: (payload, "audio/x-mpegurl"))

    assert resolver.resolve("https://radio.example/list.m3u") == (
        "https://radio.example/streams/live.mp3"
    )


def test_hls_playlist_is_left_for_ffmpeg() -> None:
    payload = b"#EXTM3U\n#EXT-X-VERSION:3\nsegment.ts\n"
    resolver = NetworkStreamResolver(
        fetcher=lambda _url, _timeout: (payload, "application/vnd.apple.mpegurl")
    )

    url = "https://radio.example/live.m3u8"
    assert resolver.resolve(url) == url


def test_playlist_rejects_non_http_targets() -> None:
    resolver = NetworkStreamResolver(
        fetcher=lambda _url, _timeout: (b"file:///private/audio.mp3\n", "audio/x-mpegurl")
    )

    with pytest.raises(InvalidStreamPlaylistError, match="no valid HTTP"):
        resolver.resolve("https://radio.example/list.m3u")
