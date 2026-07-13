"""Portable JSON and M3U transfer for local radio collections."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from freak_media_player.plugins.internet_radio.models import RadioStation

FORMAT_VERSION = 1
MAX_IMPORT_BYTES = 2 * 1024 * 1024


def export_json(
    destination: Path,
    favorites: list[RadioStation],
    custom_stations: list[RadioStation],
) -> Path:
    payload = {
        "format_version": FORMAT_VERSION,
        "favorites": [_station_data(station) for station in favorites],
        "custom_stations": [_station_data(station) for station in custom_stations],
    }
    destination = destination.with_suffix(".json")
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


def import_json(source: Path) -> tuple[list[RadioStation], list[RadioStation]]:
    payload = _read_bounded(source)
    try:
        data = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("The radio JSON file is invalid.") from error
    if not isinstance(data, dict) or data.get("format_version") != FORMAT_VERSION:
        raise ValueError("The radio JSON format is not supported.")
    return (
        _station_list(data.get("favorites")),
        _station_list(data.get("custom_stations")),
    )


def export_m3u(destination: Path, stations: list[RadioStation]) -> Path:
    destination = destination.with_suffix(".m3u8")
    lines = ["#EXTM3U"]
    for station in stations:
        lines.extend((f"#EXTINF:-1,{station.name}", station.stream_url))
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def import_m3u(source: Path) -> list[RadioStation]:
    text = _read_bounded(source).decode("utf-8-sig", errors="replace")
    stations: list[RadioStation] = []
    pending_name = ""
    for line in text.splitlines():
        value = line.strip()
        if value.casefold().startswith("#extinf:"):
            _prefix, _separator, pending_name = value.partition(",")
        elif value and not value.startswith("#"):
            if not value.casefold().startswith(("http://", "https://")):
                continue
            digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
            stations.append(
                RadioStation(
                    station_id=f"custom-{digest}",
                    name=pending_name.strip() or "Imported station",
                    stream_url=value,
                )
            )
            pending_name = ""
    if not stations:
        raise ValueError("The M3U file contains no HTTP(S) radio streams.")
    return stations


def _station_data(station: RadioStation) -> dict[str, Any]:
    data = asdict(station)
    data["tags"] = list(station.tags)
    data["alternative_urls"] = list(station.alternative_urls)
    return data


def _station_list(value: Any) -> list[RadioStation]:
    if not isinstance(value, list):
        raise ValueError("The radio JSON collection is incomplete.")
    stations: list[RadioStation] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("The radio JSON contains an invalid station.")
        station_data = dict(item)
        station_data["tags"] = tuple(station_data.get("tags", ()))
        station_data["alternative_urls"] = tuple(
            station_data.get("alternative_urls", ())
        )
        try:
            station = RadioStation(**station_data)
        except (TypeError, ValueError) as error:
            raise ValueError("The radio JSON contains an invalid station.") from error
        if not station.station_id or not station.stream_url.casefold().startswith(
            ("http://", "https://")
        ):
            raise ValueError("The radio JSON contains an unsafe station URL.")
        stations.append(station)
    return stations


def _read_bounded(source: Path) -> bytes:
    if not source.is_file() or source.stat().st_size > MAX_IMPORT_BYTES:
        raise ValueError("The radio collection is missing or too large.")
    return source.read_bytes()
