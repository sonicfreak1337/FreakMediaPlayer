from __future__ import annotations

import pytest

from freak_media_player.plugins.internet_radio.logo_cache import StationLogoCache


def test_logo_cache_downloads_once_and_can_be_cleared(tmp_path) -> None:
    calls = 0

    def loader(_url: str, _timeout: float) -> tuple[bytes, str]:
        nonlocal calls
        calls += 1
        return b"fake-png-payload", "image/png"

    cache = StationLogoCache(tmp_path / "logos", loader=loader)

    first = cache.get("https://radio.example/logo.png")
    second = cache.get("https://radio.example/logo.png")

    assert first == second
    assert first is not None and first.read_bytes() == b"fake-png-payload"
    assert calls == 1
    assert cache.clear() == 1
    assert not first.exists()


def test_logo_cache_rejects_non_image_and_unsafe_url(tmp_path) -> None:
    cache = StationLogoCache(
        tmp_path / "logos",
        loader=lambda _url, _timeout: (b"html", "text/html"),
    )

    assert cache.get("file:///private/logo.png") is None
    with pytest.raises(ValueError, match="not an image"):
        cache.get("https://radio.example/logo.png")
