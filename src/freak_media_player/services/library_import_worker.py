"""Cancellable background discovery and metadata extraction for local imports."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from freak_media_player.services.local_library_service import LocalLibraryService


@dataclass(frozen=True)
class ImportScanResult:
    total: int
    processed: int
    cancelled: bool
    errors: tuple[str, ...] = ()


class LibraryImportWorker(QObject):
    track_ready = Signal(object)
    progress = Signal(int, int)
    finished = Signal(object)

    def __init__(self, service: LocalLibraryService, paths: list[Path]) -> None:
        super().__init__()
        self._service = service
        self._paths = paths
        self._cancelled = threading.Event()

    def cancel(self) -> None:
        self._cancelled.set()

    @Slot()
    def run(self) -> None:
        errors: list[str] = []
        files = self._service.discover_audio_files(self._paths)
        total = len(files)
        self.progress.emit(0, total)
        processed = 0
        for path in files:
            if self._cancelled.is_set():
                break
            try:
                self.track_ready.emit(self._service.read_track(path))
            except Exception as error:
                errors.append(f"{path.name}: {error}")
            processed += 1
            self.progress.emit(processed, total)
        self.finished.emit(
            ImportScanResult(
                total=total,
                processed=processed,
                cancelled=self._cancelled.is_set(),
                errors=tuple(errors),
            )
        )
