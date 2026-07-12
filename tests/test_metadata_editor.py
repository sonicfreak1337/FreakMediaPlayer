from PySide6.QtWidgets import QApplication

from freak_media_player.models.media import Album, Artist, ProviderIdentity, Track
from freak_media_player.widgets.metadata_editor import MetadataEditorDialog


def test_metadata_editor_returns_optional_database_fields() -> None:
    QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    track = Track(
        id="track-1",
        provider_identity=ProviderIdentity(provider_id="local-files", item_id="song.mp3"),
        title="Title",
        artist=Artist(name="Artist"),
        album=Album(title="Album", release_year=2020),
        genre="Metal",
        track_number=2,
        disc_number=1,
    )
    dialog = MetadataEditorDialog(track)

    values = dialog.values()

    assert values.title == "Title"
    assert values.artist == "Artist"
    assert values.album == "Album"
    assert values.release_year == 2020
    assert values.genre == "Metal"
    assert values.track_number == 2
    assert values.disc_number == 1
    dialog.close()
