from freak_media_player.models.media import Album, Artist, ProviderIdentity, Track
from freak_media_player.services.search_service import (
    FILE_STATUS_AVAILABLE,
    FILE_STATUS_MISSING,
    LibraryFilters,
    SearchService,
)


def make_track(
    track_id: str,
    *,
    title: str,
    artist: str,
    album: str | None = None,
    year: int | None = None,
    genre: str | None = None,
    filename: str = "track.mp3",
) -> Track:
    return Track(
        id=track_id,
        provider_identity=ProviderIdentity(provider_id="local-files", item_id=filename),
        title=title,
        artist=Artist(name=artist),
        album=Album(title=album, release_year=year) if album is not None else None,
        genre=genre,
    )


def test_library_search_matches_all_supported_metadata_fields() -> None:
    tracks = [
        make_track(
            "1",
            title="Fury",
            artist="Architects",
            album="All Our Gods",
            year=2016,
            genre="Metalcore",
            filename="hidden-original-name.flac",
        ),
        make_track("2", title="Doom", artist="Other", filename="doom.mp3"),
    ]
    service = SearchService(())

    for query in (
        "fury",
        "architects",
        "all our gods",
        "2016",
        "metalcore",
        "hidden-original-name",
        "ARCHITECTS 2016",
    ):
        assert service.search_library(tracks, query) == [tracks[0]]


def test_empty_library_search_returns_complete_catalog() -> None:
    tracks = [make_track("1", title="One", artist="Artist")]

    assert SearchService(()).search_library(tracks, "   ") == tracks


def test_library_filters_are_combined(tmp_path) -> None:
    available = tmp_path / "available.mp3"
    available.touch()
    first = make_track(
        "1",
        title="One",
        artist="Artist",
        album="Album",
        year=2024,
        genre="Metal",
        filename=str(available),
    )
    second = make_track(
        "2", title="Two", artist="Other", genre="Doom", filename="missing.mp3"
    )
    service = SearchService(())

    assert service.filter_library(
        [first, second],
        LibraryFilters(
            artist="Artist",
            album="Album",
            genre="Metal",
            year=2024,
            favorite=True,
            file_status=FILE_STATUS_AVAILABLE,
        ),
        {first.id},
    ) == [first]
    assert service.file_status(second) == FILE_STATUS_MISSING
    assert service.filter_library(
        [first, second], LibraryFilters(track_ids=frozenset({second.id}))
    ) == [second]
