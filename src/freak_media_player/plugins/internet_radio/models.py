"""Domain models for the optional internet-radio plugin."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RadioStation:
    station_id: str
    name: str
    stream_url: str
    alternative_urls: tuple[str, ...] = ()
    homepage: str = ""
    favicon_url: str = ""
    country: str = ""
    country_code: str = ""
    region: str = ""
    language: str = ""
    tags: tuple[str, ...] = ()
    codec: str = ""
    bitrate: int = 0
    votes: int = 0
    click_count: int = 0
    last_changed: str = ""
    reachable: bool = True

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> RadioStation:
        tags = tuple(
            dict.fromkeys(
                part.strip() for part in str(data.get("tags", "")).split(",") if part.strip()
            )
        )
        station_id = str(data.get("stationuuid", "")).strip()
        stream_url = str(data.get("url_resolved") or data.get("url") or "").strip()
        known_urls = tuple(
            dict.fromkeys(
                value
                for value in (
                    str(data.get("url_resolved") or "").strip(),
                    str(data.get("url") or "").strip(),
                )
                if value and value != stream_url
            )
        )
        return cls(
            station_id=station_id,
            name=str(data.get("name", "")).strip() or "Unnamed station",
            stream_url=stream_url,
            alternative_urls=known_urls,
            homepage=str(data.get("homepage", "")).strip(),
            favicon_url=str(data.get("favicon", "")).strip(),
            country=str(data.get("country", "")).strip(),
            country_code=str(data.get("countrycode", "")).strip(),
            region=str(data.get("state", "")).strip(),
            language=str(data.get("language", "")).strip(),
            tags=tags,
            codec=str(data.get("codec", "")).strip(),
            bitrate=max(0, int(data.get("bitrate") or 0)),
            votes=max(0, int(data.get("votes") or 0)),
            click_count=max(0, int(data.get("clickcount") or 0)),
            last_changed=str(data.get("lastchangetime_iso8601", "")).strip(),
            reachable=bool(data.get("lastcheckok", 1)),
        )


@dataclass(frozen=True)
class StationSearch:
    text: str = ""
    country: str = ""
    region: str = ""
    language: str = ""
    tag: str = ""
    codec: str = ""
    bitrate_min: int = 0
    bitrate_max: int = 0
    reachable_only: bool = True
    order: str = "clickcount"
    reverse: bool = True
    offset: int = 0
    limit: int = 50


@dataclass(frozen=True)
class HistoryEntry:
    station: RadioStation
    played_at: datetime = field(default_factory=datetime.now)
    entry_id: int = 0
