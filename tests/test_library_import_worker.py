from pathlib import Path
from typing import cast

from freak_media_player.models.media import Artist, ProviderIdentity, Track
from freak_media_player.services.library_import_worker import (
    ImportScanResult,
    LibraryImportWorker,
)
from freak_media_player.services.local_library_service import LocalLibraryService


class FakeImportService:
    def discover_audio_files(self, paths: list[Path]) -> list[Path]:
        return paths

    def read_track(self, path: Path) -> Track:
        if path.name == "broken.mp3":
            raise ValueError("broken metadata")
        return Track(
            id=path.stem,
            provider_identity=ProviderIdentity(
                provider_id="local-files", item_id=str(path)
            ),
            title=path.stem,
            artist=Artist(name="Artist"),
        )


def test_background_import_worker_reports_progress_tracks_and_errors() -> None:
    worker = LibraryImportWorker(
        cast(LocalLibraryService, FakeImportService()),
        [Path("one.mp3"), Path("broken.mp3"), Path("two.flac")],
    )
    tracks: list[Track] = []
    progress: list[tuple[int, int]] = []
    results: list[ImportScanResult] = []
    worker.track_ready.connect(tracks.append)
    worker.progress.connect(lambda current, total: progress.append((current, total)))
    worker.finished.connect(results.append)

    worker.run()

    assert [track.id for track in tracks] == ["one", "two"]
    assert progress == [(0, 3), (1, 3), (2, 3), (3, 3)]
    assert results == [
        ImportScanResult(
            total=3,
            processed=3,
            cancelled=False,
            errors=("broken.mp3: broken metadata",),
        )
    ]


def test_background_import_worker_can_be_cancelled_before_scan_processing() -> None:
    worker = LibraryImportWorker(
        cast(LocalLibraryService, FakeImportService()), [Path("one.mp3")]
    )
    results: list[ImportScanResult] = []
    worker.finished.connect(results.append)

    worker.cancel()
    worker.run()

    assert results[0].processed == 0
    assert results[0].cancelled is True
