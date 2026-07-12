import json
from pathlib import Path

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QComboBox, QMainWindow

from freak_media_player.app.bootstrap import build_app_context
from freak_media_player.config.settings import AppSettings
from freak_media_player.player.audio_backend import NullAudioBackend
from freak_media_player.services.settings_service import SettingsService
from freak_media_player.ui.main_window import MainWindow
from freak_media_player.ui.skins import SkinCatalog, SkinManager
from freak_media_player.widgets.app_title_bar import AppTitleBar


class InMemorySettingsRepository:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def set(self, key: str, value: str) -> None:
        self.values[key] = value


def test_catalog_exposes_built_in_skins_and_rejects_unsafe_assets(tmp_path: Path) -> None:
    bad_skin = tmp_path / "bad"
    bad_skin.mkdir()
    (tmp_path / "outside.png").write_bytes(b"image")
    (bad_skin / "skin.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "bad",
                "name": "Bad",
                "assets": {"app_logo.png": "../outside.png"},
            }
        ),
        encoding="utf-8",
    )

    catalog = SkinCatalog(tmp_path)
    skins = catalog.discover()

    assert [skin.name for skin in skins.values()] == ["Freaky", "Fastilicious"]
    fastilicious = skins["fastilicious"]
    assert fastilicious.resolve_asset("app_logo.png").is_file()
    shuffle_icon = fastilicious.resolve_asset("icons/shuffle_icon.png")
    repeat_icon = fastilicious.resolve_asset("icons/repeat_all_on.png")
    assert shuffle_icon.is_file()
    assert repeat_icon.is_file()
    assert QImage(str(shuffle_icon)) != QImage(str(repeat_icon))
    logo = QImage(str(fastilicious.resolve_asset("app_logo.png")))
    assert logo.hasAlphaChannel()
    assert logo.pixelColor(0, 0).alpha() == 0
    assert fastilicious.colors["accent"] == "#ff2a12"
    assert len(catalog.errors) == 1
    assert "leaves the skin folder" in catalog.errors[0]


def test_custom_skin_can_override_styles_colors_and_assets(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    custom_skin = tmp_path / "my-skin"
    assets = custom_skin / "assets"
    assets.mkdir(parents=True)
    custom_logo = assets / "my-logo.png"
    custom_logo.write_bytes(b"custom image placeholder")
    (custom_skin / "style.qss").write_text(
        '#appTitleBar { color: {{color:accent}}; image: url("{{asset:app_logo.png}}"); }',
        encoding="utf-8",
    )
    (custom_skin / "skin.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "my-skin",
                "name": "My Skin",
                "extends": "freaky",
                "stylesheet": "style.qss",
                "colors": {"accent": "#abcdef"},
                "assets": {"app_logo.png": "assets/my-logo.png"},
            }
        ),
        encoding="utf-8",
    )
    repository = InMemorySettingsRepository()
    manager = SkinManager(app, tmp_path, SettingsService(repository))
    manager.initialize(AppSettings())

    selected = manager.activate("my-skin")

    assert selected == "my-skin"
    assert manager.resolve_asset("app_logo.png") == custom_logo
    assert "#abcdef" in app.styleSheet()
    assert custom_logo.as_posix() in app.styleSheet()
    assert repository.values["settings.theme_name"] == "my-skin"
    manager.activate("freaky")


def test_title_bar_dropdown_switches_and_persists_skin(tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    repository = InMemorySettingsRepository()
    manager = SkinManager(app, tmp_path, SettingsService(repository))
    assert manager.initialize(AppSettings(theme_name="dark")) == "freaky"
    window = QMainWindow()
    title_bar = AppTitleBar(window, manager)
    selector = title_bar.findChild(QComboBox, "skinSelector")

    assert selector is not None
    assert [selector.itemText(index) for index in range(selector.count())] == [
        "Freaky",
        "Fastilicious",
    ]

    selector.setCurrentIndex(selector.findData("fastilicious"))
    app.processEvents()

    assert manager.active_skin_id == "fastilicious"
    assert repository.values["settings.theme_name"] == "fastilicious"
    title_bar.close()
    window.close()
    manager.activate("freaky")


def test_main_window_applies_fastilicious_live(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = QApplication.instance() or QApplication(["", "-platform", "offscreen"])
    context = build_app_context(audio_backend=NullAudioBackend())
    manager = SkinManager(app, context.app_paths.skins_dir, context.settings_service)
    manager.initialize(AppSettings(database_path=context.app_paths.database_path))
    window = MainWindow(
        playback_service=context.playback_service,
        local_library_service=context.local_library_service,
        playlist_service=context.playlist_service,
        equalizer_service=context.equalizer_service,
        skin_manager=manager,
    )
    try:
        window.show()
        app.processEvents()
        selector = window.findChild(QComboBox, "skinSelector")
        assert selector is not None

        selector.setCurrentIndex(selector.findData("fastilicious"))
        app.processEvents()

        assert manager.active_skin_id == "fastilicious"
        assert "#ff8700" in app.styleSheet()
        assert manager.resolve_asset("app_logo.png").parent.name == "fastilicious"
        for fallback_icon in (
            "folder_add_icon.png",
            "minus_icon.png",
            "next_icon.png",
            "plus_icon.png",
            "previous_icon.png",
            "settings_icon.png",
            "volume_icon.png",
        ):
            assert "skins" not in manager.resolve_asset(f"icons/{fallback_icon}").parts
        assert context.database.settings.get("settings.theme_name") == "fastilicious"
    finally:
        window.close()
        context.database.connection.close()
        manager.activate("freaky", persist=False)
