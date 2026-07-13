"""Replaceable station directory and Radio Browser implementation."""

from __future__ import annotations

import json
import random
from collections.abc import Callable
from dataclasses import replace
from itertools import product
from typing import Any, Protocol
from urllib.parse import urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from freak_media_player.plugins.internet_radio.models import RadioStation, StationSearch

DEFAULT_API_BASE = "https://de1.api.radio-browser.info/json"
USER_AGENT = "FreakMediaPlayer/1.0 (optional internet-radio plugin)"
MAX_DIRECTORY_BYTES = 4 * 1024 * 1024
MAX_FILTER_VALUES = 4
MAX_BATCH_REQUESTS = 16


class LimitedRedirectHandler(HTTPRedirectHandler):
    max_redirections = 5
    max_repeats = 2


class StationDirectory(Protocol):
    def search(self, query: StationSearch) -> list[RadioStation]: ...


JsonLoader = Callable[[str, float], Any]


class RadioBrowserDirectory:
    def __init__(
        self,
        api_base: str = DEFAULT_API_BASE,
        loader: JsonLoader | None = None,
        timeout_seconds: float = 8.0,
    ) -> None:
        self._api_base = api_base.rstrip("/")
        self._loader = loader or self._load_json
        self._timeout_seconds = timeout_seconds

    def search(self, query: StationSearch) -> list[RadioStation]:
        countries = self._values(query.country)
        regions = self._values(query.region)
        languages = self._values(query.language)
        tags = self._values(query.tag)
        has_multiple_values = any(
            len(values) > 1 for values in (countries, regions, languages, tags)
        )
        if not has_multiple_values:
            return self._search_once(query)

        combinations = list(
            product(countries or ("",), regions or ("",), languages or ("",))
        )
        required_results = max(1, query.offset + query.limit)
        pages_per_combination = (required_results + 99) // 100
        request_count = len(combinations) * pages_per_combination
        if request_count > MAX_BATCH_REQUESTS:
            raise ValueError(
                f"Too many filter combinations; use at most {MAX_BATCH_REQUESTS}."
            )
        merged: dict[str, RadioStation] = {}
        for country, region, language in combinations:
            for page in range(pages_per_combination):
                partial = replace(
                    query,
                    country=country,
                    region=region,
                    language=language,
                    tag=tags[0] if tags else "",
                    offset=page * 100,
                    limit=min(100, required_results - page * 100),
                )
                for station in self._search_once(partial):
                    if self._matches(station, countries, regions, languages, tags):
                        merged[station.station_id] = station
        stations = list(merged.values())
        self._sort(stations, query.order, query.reverse)
        start = max(0, query.offset)
        return stations[start : start + max(1, query.limit)]

    def _search_once(self, query: StationSearch) -> list[RadioStation]:
        parameters: dict[str, str | int] = {
            "hidebroken": "true" if query.reachable_only else "false",
            "order": query.order,
            "reverse": "true" if query.reverse else "false",
            "offset": max(0, query.offset),
            "limit": min(100, max(1, query.limit)),
        }
        optional_text = {
            "name": query.text.strip(),
            "country": query.country.strip(),
            "state": query.region.strip(),
            "language": query.language.strip(),
            "tag": query.tag.strip(),
            "codec": query.codec.strip(),
        }
        parameters.update({key: value for key, value in optional_text.items() if value})
        if query.bitrate_min > 0:
            parameters["bitrateMin"] = query.bitrate_min
        if query.bitrate_max > 0:
            parameters["bitrateMax"] = query.bitrate_max
        url = f"{self._api_base}/stations/search?{urlencode(parameters)}"
        payload = self._loader(url, self._timeout_seconds)
        if not isinstance(payload, list):
            raise ValueError("The station directory returned an invalid response.")
        stations = [RadioStation.from_api(item) for item in payload if isinstance(item, dict)]
        return [station for station in stations if station.station_id and station.stream_url]

    @staticmethod
    def _values(value: str) -> tuple[str, ...]:
        normalized = value.replace(";", ",")
        values = tuple(
            dict.fromkeys(part.strip() for part in normalized.split(",") if part.strip())
        )
        if len(values) > MAX_FILTER_VALUES:
            raise ValueError(f"Use at most {MAX_FILTER_VALUES} values per filter.")
        return values

    @staticmethod
    def _matches(
        station: RadioStation,
        countries: tuple[str, ...],
        regions: tuple[str, ...],
        languages: tuple[str, ...],
        tags: tuple[str, ...],
    ) -> bool:
        country = station.country.casefold()
        region = station.region.casefold()
        station_languages = {
            item.strip().casefold() for item in station.language.split(",") if item.strip()
        }
        station_tags = {item.casefold() for item in station.tags}
        return (
            (not countries or any(item.casefold() == country for item in countries))
            and (not regions or any(item.casefold() == region for item in regions))
            and (
                not languages
                or any(item.casefold() in station_languages for item in languages)
            )
            and (not tags or all(item.casefold() in station_tags for item in tags))
        )

    @staticmethod
    def _sort(stations: list[RadioStation], order: str, reverse: bool) -> None:
        if order == "random":
            random.shuffle(stations)
            return
        key = {
            "name": lambda station: station.name.casefold(),
            "country": lambda station: station.country.casefold(),
            "votes": lambda station: station.votes,
            "bitrate": lambda station: station.bitrate,
            "lastchangetime": lambda station: station.last_changed,
            "clickcount": lambda station: station.click_count,
        }.get(order, lambda station: station.click_count)
        stations.sort(key=key, reverse=reverse)

    @staticmethod
    def _load_json(url: str, timeout_seconds: float) -> Any:
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        opener = build_opener(LimitedRedirectHandler())
        with opener.open(request, timeout=timeout_seconds) as response:
            if response.status != 200:
                raise ConnectionError(f"Station directory returned HTTP {response.status}.")
            final_url = urlparse(response.geturl())
            if final_url.scheme.casefold() != "https":
                raise ConnectionError("Station directory redirected outside HTTPS.")
            payload = response.read(MAX_DIRECTORY_BYTES + 1)
            if len(payload) > MAX_DIRECTORY_BYTES:
                raise ValueError("The station directory response is too large.")
            return json.loads(payload.decode("utf-8"))
