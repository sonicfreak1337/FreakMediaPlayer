from pathlib import Path

from freak_media_player.models.media import Album, Artist, ProviderIdentity, Track
from freak_media_player.widgets.artwork import find_track_cover


def make_local_track(path: Path, album: str = "Test Album") -> Track:
    return Track(
        id="track-1",
        provider_identity=ProviderIdentity("local-files", str(path)),
        title="Test Track",
        artist=Artist("Test Artist"),
        album=Album(album),
    )


def test_find_track_cover_prefers_conventional_file_name(tmp_path: Path) -> None:
    track_path = tmp_path / "01 - Test Track.flac"
    track_path.touch()
    (tmp_path / "random.png").touch()
    expected = tmp_path / "cover.jpg"
    expected.touch()

    assert find_track_cover(make_local_track(track_path)) == str(expected)


def test_find_track_cover_matches_album_name(tmp_path: Path) -> None:
    track_path = tmp_path / "track.mp3"
    track_path.touch()
    expected = tmp_path / "Test Album.png"
    expected.touch()

    assert find_track_cover(make_local_track(track_path)) == str(expected)


def test_find_track_cover_returns_none_without_artwork(tmp_path: Path) -> None:
    track_path = tmp_path / "track.mp3"
    track_path.touch()

    assert find_track_cover(make_local_track(track_path)) is None
