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

    def list_tracks(self) -> list[Track]:
        return self.tracks

    def import_paths(self, _paths: list[Path]) -> list[Track]:
        self.tracks = [make_track()]
        return self.tracks

    def list_favorite_track_ids(self) -> set[str]:
        return self.favorite_ids

    def list_music_folders(self) -> list[Path]:
        return self.music_folders

    def rescan_music_folder(self, _path: Path) -> list[Track]:
        return self.tracks

    def remove_music_folder(self, path: Path) -> bool:
        if path not in self.music_folders:
            return False
        self.music_folders.remove(path)
        return True


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
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    service = FakeLocalLibraryService()
    panel = LocalTracksPanel(
        "Local Library",
        cast(LocalLibraryService, service),
    )
    messages: list[str] = []
    panel.status_message.connect(messages.append)

    panel._import_paths([Path("track.mp3")])

    assert messages == ["Imported 1 track."]


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
