"""Independent-window user interface for station discovery and playback."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from freak_media_player.models.playback import PlaybackStatus, StreamBufferProfile
from freak_media_player.player.stream_probe import probe_stream_url
from freak_media_player.plugins.internet_radio.directory import StationDirectory
from freak_media_player.plugins.internet_radio.errors import describe_stream_error
from freak_media_player.plugins.internet_radio.logo_cache import StationLogoCache
from freak_media_player.plugins.internet_radio.models import RadioStation, StationSearch
from freak_media_player.plugins.internet_radio.provider import PROVIDER_ID, InternetRadioProvider
from freak_media_player.plugins.internet_radio.storage import RadioStorage
from freak_media_player.plugins.internet_radio.transfer import (
    export_json,
    export_m3u,
    import_json,
    import_m3u,
)
from freak_media_player.services.playback_service import PlaybackService


class StationSearchThread(QThread):
    completed = Signal(int, object)
    failed = Signal(int, str)

    def __init__(self, generation: int, directory: StationDirectory, query: StationSearch) -> None:
        super().__init__()
        self._generation = generation
        self._directory = directory
        self._query = query

    def run(self) -> None:
        try:
            self.completed.emit(self._generation, self._directory.search(self._query))
        except Exception as error:
            self.failed.emit(self._generation, str(error) or type(error).__name__)


class LogoLoadThread(QThread):
    completed = Signal(int, str)

    def __init__(self, generation: int, cache: StationLogoCache, url: str) -> None:
        super().__init__()
        self._generation = generation
        self._cache = cache
        self._url = url

    def run(self) -> None:
        try:
            path = self._cache.get(self._url)
        except (OSError, ValueError):
            path = None
        self.completed.emit(self._generation, str(path) if path is not None else "")


class StreamProbeThread(QThread):
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, url: str) -> None:
        super().__init__()
        self._url = url

    def run(self) -> None:
        try:
            result = probe_stream_url(self._url)
        except Exception as error:
            self.failed.emit(str(error) or type(error).__name__)
            return
        self.succeeded.emit(result.content_type)


class InternetRadioPanel(QWidget):
    status_message = Signal(str)

    def __init__(
        self,
        directory: StationDirectory,
        provider: InternetRadioProvider,
        playback_service: PlaybackService,
        storage: RadioStorage,
        parent: QWidget | None = None,
        *,
        logo_cache: StationLogoCache | None = None,
    ) -> None:
        super().__init__(parent)
        self._directory = directory
        self._provider = provider
        self._playback = playback_service
        self._storage = storage
        self._logo_cache = logo_cache
        self._stations: list[RadioStation] = []
        self._threads: set[StationSearchThread] = set()
        self._logo_threads: set[LogoLoadThread] = set()
        self._probe_threads: set[StreamProbeThread] = set()
        self._logo_generation = 0
        self._generation = 0
        self._offset = 0
        self._page_size = 50
        self._active_station: RadioStation | None = None
        self._retry_attempts = 0
        self._local_view = ""
        self._play_after_search = False
        self._history_entry_ids: list[int] = []
        self._directory_offline = False
        self._directory_buttons: list[QPushButton] = []

        self._search = QLineEdit()
        self._country = QLineEdit()
        self._region = QLineEdit()
        self._language = QLineEdit()
        self._tag = QLineEdit()
        self._codec = QComboBox()
        self._bitrate_min = QSpinBox()
        self._bitrate_max = QSpinBox()
        self._reachable = QCheckBox("Only reachable")
        self._history_enabled = QCheckBox("Save listening history")
        self._logos_enabled = QCheckBox("Load station logos")
        self._sort = QComboBox()
        self._buffer_profile = QComboBox()
        self._table = QTableWidget(0, 6)
        self._status = QLabel("Ready")
        self._offline_notice = QLabel()
        self._previous = QPushButton("Previous")
        self._next = QPushButton("Next")
        self._favorite = QPushButton("♡ Favorite")
        self._logo = QLabel("No logo")
        self._details = QLabel("Select a station to see details.")
        self._playback_timer = QTimer(self)
        self._playback_timer.setInterval(500)
        self._playback_timer.timeout.connect(self._refresh_playback_status)
        self._retry_timer = QTimer(self)
        self._retry_timer.setSingleShot(True)
        self._retry_timer.timeout.connect(self._retry_stream)
        self._configure_buffer_profile()
        self._configure_privacy_options()
        self._build_ui()
        self._restore_filters()
        self._install_shortcuts()
        self._playback_timer.start()
        self.search()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(7)

        top = QHBoxLayout()
        self._search.setPlaceholderText("Station, city or keyword")
        self._search.setClearButtonEnabled(True)
        self._search.returnPressed.connect(self._new_search)
        top.addWidget(self._search, 1)
        self._search_button = QPushButton("Search")
        self._search_button.clicked.connect(self._new_search)
        top.addWidget(self._search_button)
        reset_button = QPushButton("Reset filters")
        reset_button.clicked.connect(self._reset_filters)
        top.addWidget(reset_button)
        layout.addLayout(top)
        self._offline_notice.setWordWrap(True)
        self._offline_notice.setObjectName("radioOfflineNotice")
        self._offline_notice.hide()
        layout.addWidget(self._offline_notice)

        filters = QFormLayout()
        filter_row = QHBoxLayout()
        for widget, placeholder in (
            (self._country, "Countries (comma separated)"),
            (self._region, "Regions (comma separated)"),
            (self._language, "Languages (comma separated)"),
            (self._tag, "Required tags (comma separated)"),
        ):
            widget.setPlaceholderText(placeholder)
            widget.returnPressed.connect(self._new_search)
            filter_row.addWidget(widget)
        filters.addRow("Discovery", filter_row)
        technical_row = QHBoxLayout()
        self._codec.addItems(["Any codec", "MP3", "AAC", "AAC+", "OGG", "OPUS"])
        technical_row.addWidget(self._codec)
        self._bitrate_min.setRange(0, 512)
        self._bitrate_min.setSuffix(" kbit/s min")
        technical_row.addWidget(self._bitrate_min)
        self._bitrate_max.setRange(0, 512)
        self._bitrate_max.setSpecialValueText("No maximum")
        self._bitrate_max.setSuffix(" kbit/s max")
        technical_row.addWidget(self._bitrate_max)
        self._reachable.setChecked(True)
        technical_row.addWidget(self._reachable)
        technical_row.addWidget(self._buffer_profile)
        technical_row.addStretch(1)
        filters.addRow("Technical", technical_row)
        layout.addLayout(filters)

        views = QHBoxLayout()
        for text, callback in (
            ("Popular", self._show_popular),
            ("Favorites", self._show_favorites),
            ("History", self._show_history),
            ("My streams", self._show_custom),
            ("Random", self._play_random),
            ("New / updated", self._show_new_updated),
        ):
            button = QPushButton(text)
            button.clicked.connect(callback)
            views.addWidget(button)
            if text in {"Popular", "Random", "New / updated"}:
                self._directory_buttons.append(button)
        self._sort.addItem("Popularity", "clickcount")
        self._sort.addItem("Rating", "votes")
        self._sort.addItem("Name", "name")
        self._sort.addItem("Country", "country")
        self._sort.addItem("Bitrate", "bitrate")
        self._sort.addItem("Recently changed", "lastchangetime")
        self._sort.addItem("Random", "random")
        self._sort.currentIndexChanged.connect(self._new_search)
        views.addStretch(1)
        views.addWidget(QLabel("Sort:"))
        views.addWidget(self._sort)
        layout.addLayout(views)

        management = QHBoxLayout()
        for text, callback in (
            ("Delete history entry", self._delete_history_entry),
            ("Clear history", self._clear_history),
            ("Add stream URL", self._add_custom),
            ("Edit stream", self._edit_custom),
            ("Test stream", self._test_selected_stream),
            ("Delete stream", self._delete_custom),
            ("Export", self._export_collection),
            ("Import", self._import_collection),
        ):
            button = QPushButton(text)
            button.clicked.connect(callback)
            management.addWidget(button)
        management.addStretch(1)
        layout.addLayout(management)

        privacy = QHBoxLayout()
        privacy.addWidget(QLabel("Privacy:"))
        privacy.addWidget(self._history_enabled)
        privacy.addWidget(self._logos_enabled)
        privacy.addStretch(1)
        layout.addLayout(privacy)

        self._table.setHorizontalHeaderLabels(
            ["Station", "Country / region", "Language", "Genre / tags", "Codec", "kbit/s"]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().hide()
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.doubleClicked.connect(self._play_selected)
        self._table.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(self._table, 1)

        details_row = QHBoxLayout()
        self._logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo.setFixedSize(104, 104)
        self._logo.setScaledContents(False)
        details_row.addWidget(self._logo)
        self._details.setWordWrap(True)
        self._details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        details_row.addWidget(self._details, 1)
        details_actions = QVBoxLayout()
        for text, callback in (
            ("Copy name", self._copy_name),
            ("Copy homepage", self._copy_homepage),
            ("Clear logo cache", self._clear_logo_cache),
        ):
            button = QPushButton(text)
            button.clicked.connect(callback)
            details_actions.addWidget(button)
        details_actions.addStretch(1)
        details_row.addLayout(details_actions)
        layout.addLayout(details_row)

        bottom = QHBoxLayout()
        self._previous.clicked.connect(self._previous_page)
        self._next.clicked.connect(self._next_page)
        self._favorite.clicked.connect(self._toggle_favorite)
        copy_button = QPushButton("Copy stream URL")
        copy_button.clicked.connect(self._copy_url)
        play_button = QPushButton("Play station")
        play_button.clicked.connect(self._play_selected)
        bottom.addWidget(self._previous)
        bottom.addWidget(self._next)
        bottom.addWidget(self._status, 1)
        bottom.addWidget(copy_button)
        bottom.addWidget(self._favorite)
        bottom.addWidget(play_button)
        layout.addLayout(bottom)
        self._update_paging()

    def _install_shortcuts(self) -> None:
        focus = QShortcut(QKeySequence("Ctrl+L"), self)
        focus.activated.connect(self._search.setFocus)
        play = QShortcut(QKeySequence(Qt.Key.Key_Return), self._table)
        play.activated.connect(self._play_selected)

    def _configure_buffer_profile(self) -> None:
        self._buffer_profile.setToolTip("Stream buffer used from the next connection")
        self._buffer_profile.addItem("Small buffer", StreamBufferProfile.SMALL.value)
        self._buffer_profile.addItem("Normal buffer", StreamBufferProfile.NORMAL.value)
        self._buffer_profile.addItem("Stable buffer", StreamBufferProfile.STABLE.value)
        stored = self._storage.setting(
            "buffer_profile", StreamBufferProfile.NORMAL.value
        )
        index = self._buffer_profile.findData(stored)
        self._buffer_profile.setCurrentIndex(max(0, index))
        self._apply_buffer_profile()
        self._buffer_profile.currentIndexChanged.connect(self._apply_buffer_profile)

    def _configure_privacy_options(self) -> None:
        self._history_enabled.setChecked(
            self._storage.setting("history_enabled", "true") == "true"
        )
        self._logos_enabled.setChecked(
            self._storage.setting("logos_enabled", "true") == "true"
        )
        self._history_enabled.toggled.connect(
            lambda enabled: self._storage.set_setting(
                "history_enabled", "true" if enabled else "false"
            )
        )
        self._logos_enabled.toggled.connect(self._logo_setting_changed)

    def _logo_setting_changed(self, enabled: bool) -> None:
        self._storage.set_setting("logos_enabled", "true" if enabled else "false")
        self._logo_generation += 1
        if enabled:
            if (station := self._selected()) is not None:
                self._load_logo(station.favicon_url)
        else:
            self._logo.setPixmap(QPixmap())
            self._logo.setText("Logos disabled")

    def _apply_buffer_profile(self) -> None:
        value = str(self._buffer_profile.currentData())
        try:
            profile = StreamBufferProfile(value)
        except ValueError:
            profile = StreamBufferProfile.NORMAL
        self._playback.set_stream_buffer_profile(profile)
        self._storage.set_setting("buffer_profile", profile.value)

    def _restore_filters(self) -> None:
        raw_value = self._storage.setting("search_filters")
        if not raw_value:
            return
        try:
            data = json.loads(raw_value)
            if not isinstance(data, dict):
                return
        except json.JSONDecodeError:
            return
        for widget in (self._codec, self._sort):
            widget.blockSignals(True)
        try:
            self._search.setText(str(data.get("text", "")))
            self._country.setText(str(data.get("country", "")))
            self._region.setText(str(data.get("region", "")))
            self._language.setText(str(data.get("language", "")))
            self._tag.setText(str(data.get("tag", "")))
            codec_index = self._codec.findText(str(data.get("codec", "Any codec")))
            self._codec.setCurrentIndex(max(0, codec_index))
            self._bitrate_min.setValue(max(0, int(data.get("bitrate_min", 0))))
            self._bitrate_max.setValue(max(0, int(data.get("bitrate_max", 0))))
            reachable = data.get("reachable_only", True)
            self._reachable.setChecked(reachable if isinstance(reachable, bool) else True)
            sort_index = self._sort.findData(str(data.get("order", "clickcount")))
            self._sort.setCurrentIndex(max(0, sort_index))
        except (TypeError, ValueError):
            pass
        finally:
            for widget in (self._codec, self._sort):
                widget.blockSignals(False)

    def _save_filters(self) -> None:
        data = {
            "text": self._search.text(),
            "country": self._country.text(),
            "region": self._region.text(),
            "language": self._language.text(),
            "tag": self._tag.text(),
            "codec": self._codec.currentText(),
            "bitrate_min": self._bitrate_min.value(),
            "bitrate_max": self._bitrate_max.value(),
            "reachable_only": self._reachable.isChecked(),
            "order": str(self._sort.currentData()),
        }
        self._storage.set_setting(
            "search_filters", json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        )

    def search(self) -> None:
        self._generation += 1
        generation = self._generation
        order = str(self._sort.currentData())
        query = StationSearch(
            text=self._search.text(),
            country=self._country.text(),
            region=self._region.text(),
            language=self._language.text(),
            tag=self._tag.text(),
            codec="" if self._codec.currentIndex() == 0 else self._codec.currentText(),
            bitrate_min=self._bitrate_min.value(),
            bitrate_max=self._bitrate_max.value(),
            reachable_only=self._reachable.isChecked(),
            order=order,
            reverse=order not in {"name", "country"},
            offset=self._offset,
            limit=self._page_size,
        )
        self._save_filters()
        self._status.setText("Searching station directory…")
        self._set_search_enabled(False)
        thread = StationSearchThread(generation, self._directory, query)
        thread.completed.connect(self._search_completed)
        thread.failed.connect(self._search_failed)
        thread.finished.connect(lambda: self._thread_finished(thread))
        self._threads.add(thread)
        thread.start()

    def shutdown(self) -> None:
        self._generation += 1
        self._playback_timer.stop()
        self._retry_timer.stop()
        for thread in tuple(self._threads):
            thread.requestInterruption()
            thread.wait(9_000)
        for logo_thread in tuple(self._logo_threads):
            logo_thread.requestInterruption()
            logo_thread.wait(7_000)
        for probe_thread in tuple(self._probe_threads):
            probe_thread.requestInterruption()
            probe_thread.wait(8_000)

    def _search_completed(self, generation: int, stations: object) -> None:
        if generation != self._generation or not isinstance(stations, list):
            return
        self._stations = [item for item in stations if isinstance(item, RadioStation)]
        for station in self._stations:
            if self._storage.is_favorite(station.station_id):
                self._storage.set_favorite(station, True)
        self._set_directory_offline(False)
        self._populate(self._stations)
        if self._stations:
            counts = Counter(station.country or "Unknown" for station in self._stations)
            country_summary = ", ".join(
                f"{country}: {count}" for country, count in counts.most_common(4)
            )
            self._status.setText(
                f"{len(self._stations)} stations · page "
                f"{self._offset // self._page_size + 1} · {country_summary}"
            )
        else:
            self._status.setText(
                "No stations match the active filters. Reset filters to broaden the search."
            )
        self._set_search_enabled(True)
        self._update_paging()
        if self._play_after_search and self._stations:
            self._play_after_search = False
            self._table.selectRow(0)
            self._play_selected()

    def _search_failed(self, generation: int, message: str) -> None:
        if generation != self._generation:
            return
        self._set_directory_offline(True, message)
        self._status.setText(f"Directory unavailable: {message}")
        self._play_after_search = False
        self.status_message.emit(f"Internet radio search failed: {message}")
        self._set_search_enabled(True)

    def _thread_finished(self, thread: StationSearchThread) -> None:
        self._threads.discard(thread)
        thread.deleteLater()

    def _populate(self, stations: list[RadioStation]) -> None:
        self._table.setRowCount(len(stations))
        for row, station in enumerate(stations):
            values = (
                station.name,
                " · ".join(filter(None, (station.country, station.region))),
                station.language,
                ", ".join(station.tags),
                station.codec,
                str(station.bitrate or ""),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, station.station_id)
                self._table.setItem(row, column, item)
        if stations:
            self._table.selectRow(0)
        else:
            self._selection_changed()

    def _selection_changed(self) -> None:
        self._sync_favorite_button()
        station = self._selected()
        if station is None:
            self._details.setText("Select a station to see details.")
            self._logo.setText("No logo")
            self._logo.setPixmap(QPixmap())
            return
        location = " · ".join(
            filter(None, (station.country, station.region))
        ) or "Unknown location"
        technical = " · ".join(
            filter(None, (station.codec, f"{station.bitrate} kbit/s" if station.bitrate else ""))
        ) or "Unknown stream format"
        self._details.setText(
            "\n".join(
                (
                    station.name,
                    location,
                    station.language or "Unknown language",
                    ", ".join(station.tags) or "No genre tags",
                    technical,
                    station.homepage or "No homepage",
                )
            )
        )
        self._load_logo(station.favicon_url)

    def _load_logo(self, url: str) -> None:
        self._logo_generation += 1
        generation = self._logo_generation
        self._logo.setPixmap(QPixmap())
        if not self._logos_enabled.isChecked():
            self._logo.setText("Logos disabled")
            return
        self._logo.setText("Loading logo…" if url and self._logo_cache is not None else "No logo")
        if not url or self._logo_cache is None:
            return
        thread = LogoLoadThread(generation, self._logo_cache, url)
        thread.completed.connect(self._logo_loaded)
        thread.finished.connect(lambda: self._logo_thread_finished(thread))
        self._logo_threads.add(thread)
        thread.start()

    def _logo_loaded(self, generation: int, path: str) -> None:
        if generation != self._logo_generation:
            return
        pixmap = QPixmap(path) if path else QPixmap()
        if pixmap.isNull():
            self._logo.setPixmap(QPixmap())
            self._logo.setText("No logo")
            return
        scaled = pixmap.scaled(
            96,
            96,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._logo.setText("")
        self._logo.setPixmap(scaled)

    def _logo_thread_finished(self, thread: LogoLoadThread) -> None:
        self._logo_threads.discard(thread)
        thread.deleteLater()

    def _selected(self) -> RadioStation | None:
        row = self._table.currentRow()
        return self._stations[row] if 0 <= row < len(self._stations) else None

    def _play_selected(self) -> None:
        station = self._selected()
        if station is None:
            return
        track = self._provider.register_station(station)
        self._active_station = station
        self._retry_attempts = 0
        state = self._playback.play_transient(track)
        if state.error_message:
            self._status.setText(f"Not reachable: {state.error_message}")
            return
        if self._history_enabled.isChecked():
            self._storage.add_history(station)
        self._status.setText(f"Connecting to {station.name}…")
        self.status_message.emit(f"Internet radio: connecting to {station.name}.")

    def _refresh_playback_status(self) -> None:
        state = self._playback.state
        track = state.current_track
        if track is None or track.provider_identity.provider_id != PROVIDER_ID:
            self._retry_timer.stop()
            self._active_station = None
            return
        station_name = (
            self._active_station.name if self._active_station is not None else track.title
        )
        if state.status == PlaybackStatus.BUFFERING:
            self._status.setText(f"Buffering {station_name}…")
        elif state.status == PlaybackStatus.PLAYING:
            title = self._playback.stream_title()
            self._status.setText(f"Live · {title}" if title else f"Live · {station_name}")
            self._retry_attempts = 0
        elif state.status == PlaybackStatus.PAUSED:
            self._status.setText(f"Paused · {station_name}")
        elif state.status == PlaybackStatus.ERROR and not self._retry_timer.isActive():
            if self._retry_attempts >= 3:
                self._status.setText(
                    f"Not reachable: {describe_stream_error(state.error_message)}"
                )
                return
            delay_seconds = 2**self._retry_attempts
            self._retry_attempts += 1
            self._status.setText(
                f"Reconnect {self._retry_attempts}/3 in {delay_seconds} s…"
            )
            self._retry_timer.start(delay_seconds * 1_000)

    def _retry_stream(self) -> None:
        state = self._playback.state
        track = state.current_track
        if (
            track is not None
            and track.provider_identity.provider_id == PROVIDER_ID
            and state.status == PlaybackStatus.ERROR
        ):
            self._status.setText("Reconnecting…")
            self._provider.advance_endpoint(track.provider_identity.item_id)
            self._playback.retry()

    def _play_random(self) -> None:
        self._play_after_search = True
        self._offset = 0
        self._sort.blockSignals(True)
        self._sort.setCurrentIndex(self._sort.findData("random"))
        self._sort.blockSignals(False)
        self.search()

    def _toggle_favorite(self) -> None:
        station = self._selected()
        if station is None:
            return
        favorite = not self._storage.is_favorite(station.station_id)
        self._storage.set_favorite(station, favorite)
        self._sync_favorite_button()
        self._status.setText("Station saved as favorite." if favorite else "Favorite removed.")

    def _sync_favorite_button(self) -> None:
        station = self._selected()
        favorite = station is not None and self._storage.is_favorite(station.station_id)
        self._favorite.setText("♥ Favorite" if favorite else "♡ Favorite")
        self._favorite.setEnabled(station is not None)

    def _show_favorites(self) -> None:
        self._show_local(self._storage.favorites(), "radio favorites")

    def _show_history(self) -> None:
        entries = self._storage.history()
        self._show_local([entry.station for entry in entries], "history entries")
        self._history_entry_ids = [entry.entry_id for entry in entries]

    def _show_custom(self) -> None:
        self._show_local(self._storage.custom_stations(), "custom streams")

    def _show_local(self, stations: list[RadioStation], label: str) -> None:
        self._generation += 1
        self._local_view = label
        self._history_entry_ids = []
        self._stations = stations
        self._populate(stations)
        self._status.setText(f"{len(stations)} {label} · available offline")
        self._previous.setEnabled(False)
        self._next.setEnabled(False)

    def _show_popular(self) -> None:
        self._local_view = ""
        self._sort.blockSignals(True)
        self._sort.setCurrentIndex(0)
        self._sort.blockSignals(False)
        self._new_search()

    def _show_new_updated(self) -> None:
        self._sort.blockSignals(True)
        self._sort.setCurrentIndex(self._sort.findData("lastchangetime"))
        self._sort.blockSignals(False)
        self._new_search()

    def _add_custom(self) -> None:
        name, accepted = QInputDialog.getText(self, "Add radio stream", "Station name:")
        if not accepted or not name.strip():
            return
        url, accepted = QInputDialog.getText(self, "Add radio stream", "Direct HTTP(S) stream URL:")
        if not accepted:
            return
        url = url.strip()
        if not url.casefold().startswith(("http://", "https://")):
            self._status.setText("Only HTTP(S) stream URLs are supported.")
            return
        station_id = "custom-" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        station = RadioStation(station_id, name.strip(), url)
        self._storage.save_custom(station)
        self._show_custom()

    def _clear_history(self) -> None:
        self._storage.clear_history()
        self._show_history()
        self._status.setText("Radio history cleared.")

    def _delete_history_entry(self) -> None:
        row = self._table.currentRow()
        if self._local_view != "history entries" or not 0 <= row < len(
            self._history_entry_ids
        ):
            self._status.setText("Open History and select an entry first.")
            return
        self._storage.delete_history_entry(self._history_entry_ids[row])
        self._show_history()
        self._status.setText("History entry deleted.")

    def _edit_custom(self) -> None:
        station = self._selected()
        if station is None or self._local_view != "custom streams":
            self._status.setText("Open My streams and select a custom station first.")
            return
        name, accepted = QInputDialog.getText(
            self, "Edit radio stream", "Station name:", text=station.name
        )
        if not accepted or not name.strip():
            return
        url, accepted = QInputDialog.getText(
            self, "Edit radio stream", "Direct HTTP(S) stream URL:", text=station.stream_url
        )
        if not accepted:
            return
        url = url.strip()
        if not url.casefold().startswith(("http://", "https://")):
            self._status.setText("Only HTTP(S) stream URLs are supported.")
            return
        new_id = "custom-" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        updated = RadioStation(new_id, name.strip(), url)
        if new_id != station.station_id:
            self._storage.delete_custom(station.station_id)
        self._storage.save_custom(updated)
        self._show_custom()
        self._status.setText("Custom stream updated.")

    def _test_selected_stream(self) -> None:
        station = self._selected()
        if station is None:
            self._status.setText("Select a station to test first.")
            return
        self._status.setText(f"Testing {station.name}…")
        thread = StreamProbeThread(station.stream_url)
        thread.succeeded.connect(
            lambda content_type: self._status.setText(
                f"Stream reachable · {content_type or 'unknown content type'}"
            )
        )
        thread.failed.connect(
            lambda message: self._status.setText(
                f"Stream test failed: {describe_stream_error(message)}"
            )
        )
        thread.finished.connect(lambda: self._probe_thread_finished(thread))
        self._probe_threads.add(thread)
        thread.start()

    def _probe_thread_finished(self, thread: StreamProbeThread) -> None:
        self._probe_threads.discard(thread)
        thread.deleteLater()

    def _delete_custom(self) -> None:
        station = self._selected()
        if station is None or self._local_view != "custom streams":
            self._status.setText("Open My streams and select a custom station first.")
            return
        self._storage.delete_custom(station.station_id)
        self._show_custom()
        self._status.setText("Custom stream deleted.")

    def _export_collection(self) -> None:
        file_name, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export radio collection",
            "radio-stations.json",
            "Radio JSON (*.json);;M3U playlist (*.m3u8)",
        )
        if not file_name:
            return
        try:
            if "M3U" in selected_filter:
                stations = list(
                    dict.fromkeys(
                        (*self._storage.favorites(), *self._storage.custom_stations())
                    )
                )
                destination = export_m3u(Path(file_name), stations)
            else:
                destination = export_json(
                    Path(file_name),
                    self._storage.favorites(),
                    self._storage.custom_stations(),
                )
        except (OSError, ValueError) as error:
            self._status.setText(f"Export failed: {error}")
            return
        self._status.setText(f"Radio collection exported to {destination.name}.")

    def _import_collection(self) -> None:
        file_name, selected_filter = QFileDialog.getOpenFileName(
            self,
            "Import radio collection",
            "",
            "Radio collections (*.json *.m3u *.m3u8);;All files (*)",
        )
        if not file_name:
            return
        source = Path(file_name)
        try:
            if source.suffix.casefold() == ".json" or "JSON" in selected_filter:
                favorites, custom_stations = import_json(source)
                for station in favorites:
                    self._storage.set_favorite(station, True)
                for station in custom_stations:
                    self._storage.save_custom(station)
                count = len(favorites) + len(custom_stations)
            else:
                custom_stations = import_m3u(source)
                for station in custom_stations:
                    self._storage.save_custom(station)
                count = len(custom_stations)
        except (OSError, ValueError) as error:
            self._status.setText(f"Import failed: {error}")
            return
        self._status.setText(f"Imported {count} radio stations.")

    def _copy_url(self) -> None:
        if (station := self._selected()) is not None:
            QApplication.clipboard().setText(station.stream_url)
            self._status.setText("Stream URL copied to the clipboard.")

    def _copy_name(self) -> None:
        if (station := self._selected()) is not None:
            QApplication.clipboard().setText(station.name)
            self._status.setText("Station name copied to the clipboard.")

    def _copy_homepage(self) -> None:
        station = self._selected()
        if station is None or not station.homepage:
            self._status.setText("This station does not provide a homepage.")
            return
        QApplication.clipboard().setText(station.homepage)
        self._status.setText("Station homepage copied to the clipboard.")

    def _clear_logo_cache(self) -> None:
        if self._logo_cache is None:
            self._status.setText("The station logo cache is unavailable.")
            return
        removed = self._logo_cache.clear()
        self._logo_generation += 1
        self._logo.setPixmap(QPixmap())
        self._logo.setText("No logo")
        self._status.setText(f"Cleared {removed} cached station logos.")

    def _new_search(self) -> None:
        self._local_view = ""
        self._play_after_search = False
        self._offset = 0
        self.search()

    def _next_page(self) -> None:
        self._offset += self._page_size
        self.search()

    def _previous_page(self) -> None:
        self._offset = max(0, self._offset - self._page_size)
        self.search()

    def _update_paging(self) -> None:
        self._previous.setEnabled(self._offset > 0)
        self._next.setEnabled(len(self._stations) == self._page_size)

    def _set_search_enabled(self, enabled: bool) -> None:
        self._search.setEnabled(enabled)
        self._search_button.setEnabled(enabled)

    def _set_directory_offline(self, offline: bool, detail: str = "") -> None:
        self._directory_offline = offline
        self._offline_notice.setVisible(offline)
        self._offline_notice.setText(
            "Station directory offline. Favorites, history and My streams remain "
            f"available. Use Search to retry.{f' ({detail})' if detail else ''}"
            if offline
            else ""
        )
        for button in self._directory_buttons:
            button.setEnabled(not offline)
        self._sort.setEnabled(not offline)
        self._search_button.setText("Retry search" if offline else "Search")

    def _reset_filters(self) -> None:
        for edit in (self._search, self._country, self._region, self._language, self._tag):
            edit.clear()
        self._codec.setCurrentIndex(0)
        self._bitrate_min.setValue(0)
        self._bitrate_max.setValue(0)
        self._reachable.setChecked(True)
        self._sort.setCurrentIndex(0)
        self._new_search()
