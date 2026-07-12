from typing import cast

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QKeySequence
from PySide6.QtWidgets import QApplication

from freak_media_player.models.media import Artist, ProviderIdentity, Track
from freak_media_player.models.playback import PlaybackState
from freak_media_player.services.playback_service import PlaybackService
from freak_media_player.services.playlist_service import PlaylistService
from freak_media_player.ui.theme import PLAYING_ROW_BACKGROUND
from freak_media_player.widgets.playlist_panel import PlaylistPanel
from freak_media_player.widgets.track_table import PLAYING_ROLE


class FakePlaylistService:
    def __init__(self, tracks: list[Track]) -> None:
        self._tracks = tracks

    def list_tracks(self) -> list[Track]:
        return self._tracks

    def remove_positions(self, positions: list[int]) -> list[Track]:
        selected = set(positions)
        self._tracks = [
            track for index, track in enumerate(self._tracks) if index not in selected
        ]
        return self._tracks


class FakePlaybackService:
    def __init__(self, playing_index: int | None) -> None:
        self.playing_index = playing_index

    def sync_playlist(self, _tracks: list[Track]) -> PlaybackState:
        return PlaybackState()

    def current_playlist_index(self) -> int | None:
        return self.playing_index


def make_track(track_id: str) -> Track:
    return Track(
        id=track_id,
        provider_identity=ProviderIdentity(provider_id="test", item_id=track_id),
        title=f"Track {track_id}",
        artist=Artist(name="Artist"),
    )


def test_playlist_highlight_follows_playing_index() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    playlist_service = FakePlaylistService([make_track("1"), make_track("2")])
    playback_service = FakePlaybackService(playing_index=1)
    panel = PlaylistPanel(
        playlist_service=cast(PlaylistService, playlist_service),
        playback_service=cast(PlaybackService, playback_service),
    )
    panel._highlight_timer.stop()

    expected_color = QColor(PLAYING_ROW_BACKGROUND).name()
    assert panel._table.item(1, 0).background().color().name() == expected_color
    assert panel._table.item(1, 0).icon().isNull() is False
    assert panel._table.item(1, 0).data(PLAYING_ROLE) is True

    playback_service.playing_index = 0
    panel._sync_playing_highlight()
    app.processEvents()

    assert panel._table.item(0, 0).background().color().name() == expected_color
    assert panel._table.item(0, 0).icon().isNull() is False
    assert panel._table.item(1, 0).background().style() == Qt.BrushStyle.NoBrush
    assert panel._table.item(1, 0).icon().isNull() is True
    assert panel._table.item(1, 0).data(PLAYING_ROLE) is False


def test_delete_key_removes_selected_playlist_rows() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    playlist_service = FakePlaylistService(
        [make_track("1"), make_track("2"), make_track("3")]
    )
    panel = PlaylistPanel(
        playlist_service=cast(PlaylistService, playlist_service),
        playback_service=cast(PlaybackService, FakePlaybackService(None)),
    )
    panel._highlight_timer.stop()
    panel._table.selectRow(1)

    panel._delete_shortcut.activated.emit()
    app.processEvents()

    assert [track.id for track in playlist_service.list_tracks()] == ["1", "3"]
    assert panel._table.rowCount() == 2
    assert panel._delete_shortcut.key() == QKeySequence(Qt.Key.Key_Delete)


def test_playlist_empty_state_explains_how_to_add_tracks() -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    playlist_service = FakePlaylistService([])
    panel = PlaylistPanel(
        playlist_service=cast(PlaylistService, playlist_service),
        playback_service=cast(PlaybackService, FakePlaybackService(None)),
    )
    panel._highlight_timer.stop()

    assert panel._content_stack.currentWidget() is panel._empty_state
    assert "Local Library" in panel._empty_state.text()
    assert "drag" in panel._empty_state.text()

    playlist_service._tracks = [make_track("1")]
    panel.refresh()
    app.processEvents()

    assert panel._content_stack.currentWidget() is panel._table
