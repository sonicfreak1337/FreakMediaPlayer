import time
from pathlib import Path
from typing import cast

from PySide6.QtWidgets import QApplication

from freak_media_player.models.media import Artist, ProviderIdentity, Track
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.widgets.local_tracks_panel import LocalTracksPanel


class FakeLocalLibraryService:
    def __init__(self) -> None:
        self.tracks: list[Track] = []
        self.favorite_ids: set[str] = set()
        self.music_folders: list[Path] = []
        self.recent_ids: list[str] = []

    def list_tracks(self) -> list[Track]:
        return self.tracks

    def import_paths(self, _paths: list[Path]) -> list[Track]:
        self.tracks = [make_track()]
        return self.tracks

    def discover_audio_files(self, paths: list[Path]) -> list[Path]:
        return paths

    def read_track(self, _path: Path) -> Track:
        return make_track()

    def save_imported_track(self, track: Track) -> bool:
        is_new = not any(item.id == track.id for item in self.tracks)
        self.tracks = [item for item in self.tracks if item.id != track.id]
        self.tracks.append(track)
        return is_new

    def save_imported_tracks(self, tracks: list[Track]) -> tuple[int, int]:
        added = 0
        updated = 0
        for track in tracks:
            if self.save_imported_track(track):
                added += 1
            else:
                updated += 1
        return added, updated

    def list_favorite_track_ids(self) -> set[str]:
        return self.favorite_ids

    def list_recently_added_track_ids(self, _limit: int = 100) -> list[str]:
        return self.recent_ids

    def list_music_folders(self) -> list[Path]:
        return self.music_folders

    def rescan_music_folder(self, _path: Path) -> list[Track]:
        return self.tracks

    def remove_music_folder(self, path: Path) -> bool:
        if path not in self.music_folders:
            return False
        self.music_folders.remove(path)
        return True

    def get_track(self, track_id: str) -> Track | None:
        return next((track for track in self.tracks if track.id == track_id), None)

    def relocate_track(self, track_id: str, path: Path) -> Track:
        track = self.get_track(track_id)
        if track is None:
            raise KeyError(track_id)
        relocated = Track(
            id=track.id,
            provider_identity=ProviderIdentity(
                provider_id=track.provider_identity.provider_id,
                item_id=str(path),
            ),
            title=track.title,
            artist=track.artist,
            genre=track.genre,
        )
        self.tracks = [relocated if item.id == track_id else item for item in self.tracks]
        return relocated


def make_track() -> Track:
    return Track(
        id="track-1",
        provider_identity=ProviderIdentity(provider_id="test", item_id="track.mp3"),
        title="Track 1",
        artist=Artist(name="Artist"),
    )


def test_library_empty_state_explains_all_import_paths() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    service = FakeLocalLibraryService()
    panel = LocalTracksPanel(
        "Local Library",
        cast(LocalLibraryService, service),
    )

    assert panel._content_stack.currentWidget() is panel._empty_state
    assert "Import audio files" in panel._empty_state.text()
    assert "folder" in panel._empty_state.text()
    assert "drag" in panel._empty_state.text()

    service.tracks = [make_track()]
    panel.refresh()
    app.processEvents()

    assert panel._content_stack.currentWidget() is panel._table


def test_library_import_emits_concise_status_message() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    service = FakeLocalLibraryService()
    panel = LocalTracksPanel(
        "Local Library",
        cast(LocalLibraryService, service),
    )
    messages: list[str] = []
    panel.status_message.connect(messages.append)

    panel._import_paths([Path("track.mp3")])

    deadline = time.monotonic() + 2.0
    while panel._import_thread is not None and time.monotonic() < deadline:
        app.processEvents()

    assert panel._last_import_result is not None
    assert messages[0] == "Import started in the background."
    assert messages[-1] == "Import finished: 1 added, 0 updated, 0 failed."


def test_library_search_filters_immediately_and_can_be_cleared() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    service = FakeLocalLibraryService()
    first = make_track()
    second = Track(
        id="track-2",
        provider_identity=ProviderIdentity(
            provider_id="test", item_id="different-file.flac"
        ),
        title="Different Song",
        artist=Artist(name="Another Artist"),
        genre="Doom",
    )
    service.tracks = [first, second]
    panel = LocalTracksPanel(
        "Local Library",
        cast(LocalLibraryService, service),
    )

    panel._search.setText("doom different-file")
    app.processEvents()

    assert panel._table.rowCount() == 1
    assert panel._table.item(0, 0).text() == "Different Song"
    assert "2 total" in panel._summary_label.text()

    panel._search.clear()
    app.processEvents()

    assert panel._table.rowCount() == 2


def test_library_filters_combine_and_reset_with_search() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    service = FakeLocalLibraryService()
    first = make_track()
    second = Track(
        id="track-2",
        provider_identity=ProviderIdentity(provider_id="test", item_id="missing.flac"),
        title="Favorite Doom",
        artist=Artist(name="Other Artist"),
        genre="Doom",
    )
    service.tracks = [first, second]
    service.favorite_ids = {second.id}
    panel = LocalTracksPanel("Local Library", cast(LocalLibraryService, service))

    favorite_row = next(
        row
        for row in range(panel._table.rowCount())
        if panel._table.item(row, 0).text() == "Favorite Doom"
    )
    assert panel._table.item(favorite_row, 6).text() == "♥"

    panel._genre_filter.setCurrentIndex(panel._genre_filter.findData("Doom"))
    panel._favorite_filter.setCurrentIndex(panel._favorite_filter.findData(True))
    panel._search.setText("favorite")
    app.processEvents()

    assert panel._table.rowCount() == 1
    assert panel._table.item(0, 0).text() == "Favorite Doom"

    panel._reset_filters()
    app.processEvents()

    assert panel._table.rowCount() == 2
    assert panel._search.text() == ""
    assert panel._genre_filter.currentData() is None
    assert panel._favorite_filter.currentData() is None


def test_managed_folder_menu_exposes_rescan_and_remove() -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    service = FakeLocalLibraryService()
    service.music_folders = [Path("C:/Music")]
    panel = LocalTracksPanel("Local Library", cast(LocalLibraryService, service))

    panel._rebuild_folder_menu()

    actions = panel._folder_menu.actions()
    assert actions[0].text() == "Add music folder…"
    submenu = next(action.menu() for action in actions if action.menu() is not None)
    assert submenu is not None
    assert [action.text() for action in submenu.actions()] == [
        "Rescan",
        "Remove source",
    ]


def test_library_marks_missing_file_status() -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    service = FakeLocalLibraryService()
    service.tracks = [make_track()]
    panel = LocalTracksPanel("Local Library", cast(LocalLibraryService, service))

    assert panel._table.item(0, 5).text() == "Missing"
    assert panel._table.item(0, 5).toolTip() == "track.mp3"


def test_group_navigation_and_smart_lists_filter_the_table() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    service = FakeLocalLibraryService()
    first = make_track()
    second = Track(
        id="track-2",
        provider_identity=ProviderIdentity(provider_id="test", item_id="two.mp3"),
        title="Two",
        artist=Artist(name="Other Artist"),
        genre="Doom",
    )
    service.tracks = [first, second]
    service.recent_ids = [second.id]
    panel = LocalTracksPanel("Local Library", cast(LocalLibraryService, service))

    panel._smart_list.setCurrentIndex(panel._smart_list.findData("recent"))
    app.processEvents()
    assert panel._table.rowCount() == 1
    assert panel._table.item(0, 0).text() == "Two"

    panel._smart_list.setCurrentIndex(0)
    panel._rebuild_group_menu()
    artists_menu = panel._group_submenus[0]
    other_artist = next(
        action for action in artists_menu.actions() if action.text() == "Other Artist"
    )
    other_artist.trigger()
    app.processEvents()

    assert panel._table.rowCount() == 1
    assert panel._table.item(0, 0).text() == "Two"
