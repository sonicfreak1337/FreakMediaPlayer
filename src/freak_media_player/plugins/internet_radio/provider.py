"""Media provider exposing radio stations to the central player."""

from __future__ import annotations

from freak_media_player.models.media import Album, Artist, AudioSource, ProviderIdentity, Track
from freak_media_player.plugins.internet_radio.models import RadioStation
from freak_media_player.providers.base import ProviderCapabilities, SearchQuery

PROVIDER_ID = "internet-radio"


class InternetRadioProvider:
    provider_id = PROVIDER_ID
    display_name = "Internet Radio"
    capabilities = ProviderCapabilities(search=False, streaming=True)

    def __init__(self) -> None:
        self._stations: dict[str, RadioStation] = {}
        self._endpoint_indices: dict[str, int] = {}

    def register_station(self, station: RadioStation) -> Track:
        self._stations[station.station_id] = station
        self._endpoint_indices[station.station_id] = 0
        return self.track_for(station)

    def advance_endpoint(self, station_id: str) -> bool:
        station = self._stations.get(station_id)
        if station is None:
            return False
        endpoints = (station.stream_url, *station.alternative_urls)
        current = self._endpoint_indices.get(station_id, 0)
        if current + 1 >= len(endpoints):
            return False
        self._endpoint_indices[station_id] = current + 1
        return True

    def search_tracks(self, query: SearchQuery) -> list[Track]:
        needle = query.text.casefold().strip()
        stations = (
            station
            for station in self._stations.values()
            if not needle or needle in station.name.casefold()
        )
        return [self.track_for(station) for station in list(stations)[: query.limit]]

    def resolve_audio_source(self, track: Track) -> AudioSource:
        station = self._stations.get(track.provider_identity.item_id)
        if station is None:
            raise LookupError("The radio station is no longer available in this session.")
        endpoints = (station.stream_url, *station.alternative_urls)
        index = min(self._endpoint_indices.get(station.station_id, 0), len(endpoints) - 1)
        return AudioSource(uri=endpoints[index], mime_type="audio/*")

    @staticmethod
    def track_for(station: RadioStation) -> Track:
        return Track(
            id=f"radio:{station.station_id}",
            provider_identity=ProviderIdentity(PROVIDER_ID, station.station_id),
            title=station.name,
            artist=Artist("Live Radio"),
            album=Album(station.country or "Internet Radio"),
            duration=None,
            cover_url=station.favicon_url or None,
            genre=", ".join(station.tags) or None,
        )
