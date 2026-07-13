from __future__ import annotations

import json
import sqlite3
import time
from urllib.parse import parse_qs, urlparse

from PySide6.QtWidgets import QApplication, QDockWidget, QMainWindow, QMenu, QTableWidget

import freak_media_player.plugins.internet_radio.plugin as radio_plugin_module
from freak_media_player.models.media import Artist, AudioSource, ProviderIdentity, Track
from freak_media_player.models.playback import PlaybackStatus
from freak_media_player.player.audio_backend import NullAudioBackend
from freak_media_player.player.playback_controller import PlaybackController
from freak_media_player.player.queue import PlaybackQueue
from freak_media_player.plugins.base import PluginContext
from freak_media_player.plugins.internet_radio.directory import RadioBrowserDirectory
from freak_media_player.plugins.internet_radio.errors import describe_stream_error
from freak_media_player.plugins.internet_radio.models import RadioStation, StationSearch
from freak_media_player.plugins.internet_radio.plugin import InternetRadioPlugin
from freak_media_player.plugins.internet_radio.provider import InternetRadioProvider
from freak_media_player.plugins.internet_radio.storage import RadioStorage
from freak_media_player.plugins.internet_radio.widget import InternetRadioPanel
from freak_media_player.providers.base import ProviderCapabilities, SearchQuery
from freak_media_player.providers.registry import ProviderRegistry
from freak_media_player.services.playback_service import PlaybackService


def make_station(station_id: str = "station-1") -> RadioStation:
    return RadioStation(
        station_id=station_id,
        name="Test Radio",
        stream_url="https://radio.example/live.mp3",
        country="Germany",
        language="German",
        tags=("metal", "rock"),
        codec="MP3",
        bitrate=192,
    )


class LocalTestProvider:
    provider_id = "test-local"
    display_name = "Test local"
    capabilities = ProviderCapabilities()

    def search_tracks(self, query: SearchQuery) -> list[Track]:
        return []

    def resolve_audio_source(self, track: Track) -> AudioSource:
        return AudioSource("file:///test.mp3")


def test_radio_browser_search_maps_filters_and_station_data() -> None:
    requested: list[str] = []

    def loader(url: str, _timeout: float) -> object:
        requested.append(url)
        return [
            {
                "stationuuid": "abc",
                "name": "Metal Radio",
                "url_resolved": "https://radio.example/stream",
                "country": "Germany",
                "language": "German",
                "tags": "metal,rock,metal",
                "codec": "MP3",
                "bitrate": 192,
                "lastcheckok": 1,
            }
        ]

    directory = RadioBrowserDirectory(loader=loader)
    result = directory.search(
        StationSearch(
            text="Metal",
            country="Germany",
            language="German",
            tag="metal",
            codec="MP3",
            bitrate_min=128,
            bitrate_max=256,
            offset=50,
        )
    )

    parameters = parse_qs(urlparse(requested[0]).query)
    assert parameters["name"] == ["Metal"]
    assert parameters["country"] == ["Germany"]
    assert parameters["bitrateMin"] == ["128"]
    assert parameters["bitrateMax"] == ["256"]
    assert parameters["offset"] == ["50"]
    assert result[0].tags == ("metal", "rock")
    assert result[0].bitrate == 192


def test_radio_browser_combines_multiple_country_language_and_tag_filters() -> None:
    requested: list[dict[str, list[str]]] = []

    def loader(url: str, _timeout: float) -> object:
        parameters = parse_qs(urlparse(url).query)
        requested.append(parameters)
        country = parameters.get("country", [""])[0]
        language = parameters.get("language", [""])[0]
        valid = {("Germany", "German"), ("Japan", "Japanese")}
        if (country, language) not in valid:
            return []
        return [
            {
                "stationuuid": country.casefold(),
                "name": f"{country} Metal",
                "url_resolved": f"https://radio.example/{country.casefold()}",
                "country": country,
                "language": language,
                "tags": "metal,rock",
                "lastcheckok": 1,
            }
        ]

    result = RadioBrowserDirectory(loader=loader).search(
        StationSearch(
            country="Germany, Japan",
            language="German, Japanese",
            tag="metal, rock",
            order="name",
            reverse=False,
        )
    )

    assert [station.country for station in result] == ["Germany", "Japan"]
    assert len(requested) == 4
    assert all(parameters["tag"] == ["metal"] for parameters in requested)


def test_radio_storage_keeps_favorites_and_history_offline(tmp_path) -> None:
    station = make_station()
    storage = RadioStorage(tmp_path / "radio.sqlite3")

    storage.set_favorite(station, True)
    storage.add_history(station)
    storage.close()

    reopened = RadioStorage(tmp_path / "radio.sqlite3")
    assert reopened.favorites() == [station]
    history = reopened.history()
    assert history[0].station == station
    assert reopened.delete_history_entry(history[0].entry_id) is True
    assert reopened.history() == []
    reopened.close()


def test_radio_storage_migrates_legacy_station_payload(tmp_path) -> None:
    path = tmp_path / "radio-legacy.sqlite3"
    storage = RadioStorage(path)
    storage.close()
    legacy = {
        "station_id": "legacy",
        "name": "Legacy Radio",
        "stream_url": "https://radio.example/legacy",
    }
    connection = sqlite3.connect(path)
    connection.execute(
        "INSERT INTO favorites(station_id, payload) VALUES (?, ?)",
        ("legacy", json.dumps(legacy)),
    )
    connection.commit()
    connection.close()

    migrated = RadioStorage(path)
    assert migrated.favorites()[0].alternative_urls == ()
    assert migrated.setting("schema_version") == "1"
    migrated.close()


def test_custom_station_can_be_deleted_and_errors_are_classified(tmp_path) -> None:
    station = make_station("custom-station")
    storage = RadioStorage(tmp_path / "radio-custom.sqlite3")
    storage.save_custom(station)

    assert storage.delete_custom(station.station_id) is True
    assert storage.custom_stations() == []
    assert describe_stream_error("Connection timed out") == "Connection timed out."
    assert "TLS" in describe_stream_error("SSL certificate verify failed")
    storage.set_setting("buffer_profile", "stable")
    assert storage.setting("buffer_profile") == "stable"
    storage.close()


def test_provider_advances_to_alternative_stream_endpoint() -> None:
    provider = InternetRadioProvider()
    station = RadioStation(
        "station-with-backup",
        "Backup Radio",
        "https://primary.example/live",
        alternative_urls=("https://backup.example/live",),
    )
    track = provider.register_station(station)

    assert provider.resolve_audio_source(track).uri == station.stream_url
    assert provider.advance_endpoint(station.station_id) is True
    assert provider.resolve_audio_source(track).uri == station.alternative_urls[0]
    assert provider.advance_endpoint(station.station_id) is False


def test_transient_radio_playback_preserves_local_queue() -> None:
    radio_provider = InternetRadioProvider()
    local_provider = LocalTestProvider()
    registry = ProviderRegistry([local_provider, radio_provider])
    station = make_station()
    radio_track = radio_provider.register_station(station)
    local_track = Track(
        id="local-1",
        provider_identity=ProviderIdentity(local_provider.provider_id, "local-1"),
        title="Local track",
        artist=Artist("Artist"),
    )
    backend = NullAudioBackend()
    controller = PlaybackController(
        queue=PlaybackQueue([local_track]),
        audio_backend=backend,
        source_resolver=registry,
    )
    service = PlaybackService(controller)

    state = service.play_transient(radio_track)
    backend.fail()
    failed = service.state
    service.stop()
    resumed = service.play()

    assert state.current_track == radio_track
    assert failed.current_track == radio_track
    assert failed.status == PlaybackStatus.ERROR
    assert resumed.current_track == local_track
    assert registry.resolve_audio_source(radio_track).uri == station.stream_url


def test_radio_panel_loads_directory_results_without_blocking_ui(tmp_path) -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    provider = InternetRadioProvider()
    service = PlaybackService(
        PlaybackController(
            queue=PlaybackQueue(),
            audio_backend=NullAudioBackend(),
            source_resolver=ProviderRegistry([provider]),
        )
    )

    class FakeDirectory:
        def search(self, query: StationSearch) -> list[RadioStation]:
            return [make_station()]

    storage = RadioStorage(tmp_path / "radio-ui.sqlite3")
    panel = InternetRadioPanel(FakeDirectory(), provider, service, storage)
    table = panel.findChild(QTableWidget)
    assert table is not None
    for _attempt in range(100):
        app.processEvents()
        if table.rowCount() == 1:
            break
        time.sleep(0.005)
    assert table.rowCount() == 1
    panel.shutdown()
    panel.close()
    storage.close()


def test_radio_panel_restores_saved_search_filters(tmp_path) -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    storage = RadioStorage(tmp_path / "radio-filters.sqlite3")
    storage.set_setting(
        "search_filters",
        '{"text":"jazz","country":"Japan","region":"Tokyo",'
        '"language":"Japanese","tag":"jazz","codec":"AAC",'
        '"bitrate_min":128,"bitrate_max":256,"reachable_only":false,'
        '"order":"name"}',
    )
    provider = InternetRadioProvider()
    playback = PlaybackService(
        PlaybackController(
            PlaybackQueue(), NullAudioBackend(), ProviderRegistry([provider])
        )
    )

    class EmptyDirectory:
        def search(self, _query: StationSearch) -> list[RadioStation]:
            return []

    panel = InternetRadioPanel(EmptyDirectory(), provider, playback, storage)
    panel.shutdown()
    app.processEvents()

    assert panel._search.text() == "jazz"
    assert panel._country.text() == "Japan"
    assert panel._bitrate_min.value() == 128
    assert panel._bitrate_max.value() == 256
    assert panel._reachable.isChecked() is False
    assert panel._sort.currentData() == "name"
    panel.close()
    storage.close()


def test_radio_panel_can_disable_history_and_logo_network_access(tmp_path) -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    station = make_station()
    storage = RadioStorage(tmp_path / "radio-privacy.sqlite3")
    provider = InternetRadioProvider()
    playback = PlaybackService(
        PlaybackController(
            PlaybackQueue(), NullAudioBackend(), ProviderRegistry([provider])
        )
    )

    class EmptyDirectory:
        def search(self, _query: StationSearch) -> list[RadioStation]:
            return []

    panel = InternetRadioPanel(EmptyDirectory(), provider, playback, storage)
    panel.shutdown()
    panel._stations = [station]
    panel._populate([station])
    panel._history_enabled.setChecked(False)
    panel._logos_enabled.setChecked(False)
    panel._play_selected()

    assert storage.history() == []
    assert storage.setting("history_enabled") == "false"
    assert storage.setting("logos_enabled") == "false"
    panel.close()
    storage.close()


def test_radio_panel_keeps_local_views_available_when_directory_is_offline(
    tmp_path,
) -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    favorite = make_station()
    storage = RadioStorage(tmp_path / "radio-offline.sqlite3")
    storage.set_favorite(favorite, True)
    provider = InternetRadioProvider()
    playback = PlaybackService(
        PlaybackController(
            PlaybackQueue(), NullAudioBackend(), ProviderRegistry([provider])
        )
    )

    class EmptyDirectory:
        def search(self, _query: StationSearch) -> list[RadioStation]:
            return []

    panel = InternetRadioPanel(EmptyDirectory(), provider, playback, storage)
    panel.shutdown()
    panel._search_failed(panel._generation, "DNS unavailable")

    assert panel._offline_notice.isHidden() is False
    assert panel._search_button.text() == "Retry search"
    assert all(button.isEnabled() is False for button in panel._directory_buttons)
    panel._show_favorites()
    assert panel._stations == [favorite]
    panel.close()
    storage.close()


def test_directory_result_refreshes_favorite_by_stable_station_id(tmp_path) -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    old = make_station("stable-id")
    updated = RadioStation(
        "stable-id",
        "Updated Radio",
        "https://radio.example/new-stream",
        country="Germany",
    )
    storage = RadioStorage(tmp_path / "radio-refresh.sqlite3")
    storage.set_favorite(old, True)
    provider = InternetRadioProvider()
    playback = PlaybackService(
        PlaybackController(
            PlaybackQueue(), NullAudioBackend(), ProviderRegistry([provider])
        )
    )

    class EmptyDirectory:
        def search(self, _query: StationSearch) -> list[RadioStation]:
            return []

    panel = InternetRadioPanel(EmptyDirectory(), provider, playback, storage)
    panel.shutdown()
    panel._search_completed(panel._generation, [updated])

    assert storage.favorites() == [updated]
    panel.close()
    storage.close()


def test_radio_reconnect_is_cancelled_by_stop(tmp_path) -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    station = make_station()
    storage = RadioStorage(tmp_path / "radio-retry.sqlite3")
    provider = InternetRadioProvider()
    backend = NullAudioBackend()
    playback = PlaybackService(
        PlaybackController(PlaybackQueue(), backend, ProviderRegistry([provider]))
    )

    class EmptyDirectory:
        def search(self, _query: StationSearch) -> list[RadioStation]:
            return []

    panel = InternetRadioPanel(EmptyDirectory(), provider, playback, storage)
    panel.shutdown()
    panel._stations = [station]
    panel._populate([station])
    panel._play_selected()
    backend.fail()
    panel._refresh_playback_status()
    assert panel._retry_timer.isActive() is True

    playback.stop()
    panel._refresh_playback_status()
    assert panel._retry_timer.isActive() is False
    panel.close()
    storage.close()


def test_radio_plugin_opens_separate_window_without_player_dock(
    tmp_path, monkeypatch
) -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])

    class HostWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self._module_menu = QMenu("Module", self)

        @property
        def module_menu(self) -> QMenu:
            return self._module_menu

        def show_status_message(self, _message: str) -> None:
            pass

    class EmptyDirectory:
        def search(self, _query: StationSearch) -> list[RadioStation]:
            return []

    monkeypatch.setattr(radio_plugin_module, "RadioBrowserDirectory", EmptyDirectory)
    host = HostWindow()
    provider_registry = ProviderRegistry()
    playback = PlaybackService(
        PlaybackController(
            PlaybackQueue(), NullAudioBackend(), provider_registry
        )
    )
    plugin = InternetRadioPlugin()
    plugin.activate(
        PluginContext(
            application_name="Test",
            main_window=host,
            provider_registry=provider_registry,
            playback_service=playback,
            plugin_data_dir=tmp_path,
        )
    )

    plugin._open_module()
    app.processEvents()

    assert plugin._window is not None
    assert plugin._window.isWindow()
    assert plugin._window.parent() is host
    assert plugin._window.centralWidget() is plugin._panel
    assert host.findChildren(QDockWidget) == []
    station = make_station("deactivate-radio")
    playback.play_transient(plugin._provider.register_station(station))
    plugin.deactivate()
    app.processEvents()
    assert playback.state.current_track is None
    assert provider_registry.get("internet-radio") is None
