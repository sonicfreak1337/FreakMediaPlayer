from __future__ import annotations

from freak_media_player.plugins.internet_radio.models import RadioStation
from freak_media_player.plugins.internet_radio.transfer import (
    export_json,
    export_m3u,
    import_json,
    import_m3u,
)


def station(station_id: str, name: str, url: str) -> RadioStation:
    return RadioStation(
        station_id=station_id,
        name=name,
        stream_url=url,
        alternative_urls=(f"{url}?backup=1",),
        tags=("metal",),
    )


def test_json_export_import_preserves_favorites_and_custom_stations(tmp_path) -> None:
    favorite = station("favorite", "Favorite Radio", "https://radio.example/favorite")
    custom = station("custom", "Custom Radio", "https://radio.example/custom")

    destination = export_json(tmp_path / "collection", [favorite], [custom])
    favorites, custom_stations = import_json(destination)

    assert favorites == [favorite]
    assert custom_stations == [custom]


def test_m3u_export_import_preserves_names_and_urls(tmp_path) -> None:
    original = station("station", "Radio Name", "https://radio.example/live")

    destination = export_m3u(tmp_path / "stations", [original])
    imported = import_m3u(destination)

    assert destination.suffix == ".m3u8"
    assert imported[0].name == original.name
    assert imported[0].stream_url == original.stream_url
