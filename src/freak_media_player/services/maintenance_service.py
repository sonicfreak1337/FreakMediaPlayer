"""Safe maintenance operations that keep library files untouched."""

from __future__ import annotations

from freak_media_player.services.local_library_service import LocalLibraryService
from freak_media_player.services.settings_service import SettingsService


class MaintenanceService:
    def __init__(
        self,
        settings_service: SettingsService,
        library_service: LocalLibraryService,
    ) -> None:
        self._settings_service = settings_service
        self._library_service = library_service

    def rebuild_library_index(self) -> int:
        return self._library_service.refresh_metadata()

    def reset_settings(self) -> None:
        self._settings_service.reset_all()
