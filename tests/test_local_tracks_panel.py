from pathlib import Path
from typing import cast

from PySide6.QtWidgets import QApplication

from freak_media_player.models.media import Artist, ProviderIdentity, Track
from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.widgets.local_tracks_panel import LocalTracksPanel


class FakeLocalLibraryService:
    def __init__(self) -> None:
        self.tracks: list[Track] = []

    def list_tracks(self) -> list[Track]:
        return self.tracks

    def import_paths(self, _paths: list[Path]) -> list[Track]:
        self.tracks = [make_track()]
        return self.tracks


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
