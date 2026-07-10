"""Runtime skin discovery, activation, persistence and semantic colors."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QApplication

from freak_media_player.config.settings import AppSettings
from freak_media_player.services.settings_service import SettingsService
from freak_media_player.ui.assets import refresh_skin_assets, set_asset_resolver
from freak_media_player.ui.theme import (
    FASTILICIOUS_COLORS,
    FREAKY_COLORS,
    build_palette,
    fastilicious_stylesheet,
    freaky_stylesheet,
)

SKIN_SCHEMA_VERSION = 1
DEFAULT_SKIN_ID = "freaky"
LEGACY_SKIN_ALIASES = {"dark": DEFAULT_SKIN_ID}
MAX_STYLESHEET_BYTES = 1_000_000

_SKIN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_COLOR_TOKEN_PATTERN = re.compile(r"\{\{\s*color:([a-z0-9_]+)\s*}}")
_ASSET_TOKEN_PATTERN = re.compile(r"\{\{\s*asset:([^{}]+?)\s*}}")
_active_colors: dict[str, str] = dict(FREAKY_COLORS)

logger = logging.getLogger(__name__)


class SkinLoadError(ValueError):
    """Raised when a custom skin manifest is unsafe or malformed."""


@dataclass(frozen=True)
class SkinDefinition:
    skin_id: str
    name: str
    description: str
    stylesheet: str
    colors: dict[str, str]
    root_dir: Path | None = None
    asset_overrides: dict[str, Path] | None = None
    built_in: bool = False

    def resolve_asset(self, logical_name: str) -> Path | None:
        """Resolve an explicit or convention-based custom asset override."""
        normalized = _normalize_logical_asset(logical_name)
        if self.asset_overrides is not None:
            explicit = self.asset_overrides.get(normalized)
            if explicit is not None:
                return explicit
        if self.root_dir is None:
            return None
        candidate = _safe_child(self.root_dir, Path("assets") / normalized)
        return candidate if candidate.is_file() else None


class SkinCatalog:
    """Discover built-in skins and valid user skin folders."""

    def __init__(self, custom_skins_dir: Path) -> None:
        self.custom_skins_dir = custom_skins_dir
        self._errors: list[str] = []

    @property
    def errors(self) -> tuple[str, ...]:
        return tuple(self._errors)

    def discover(self) -> dict[str, SkinDefinition]:
        self.custom_skins_dir.mkdir(parents=True, exist_ok=True)
        skins = _built_in_skins()
        self._errors.clear()
        for manifest_path in sorted(self.custom_skins_dir.glob("*/skin.json")):
            try:
                skin = self._load_manifest(manifest_path, skins)
                if skin.skin_id in skins:
                    raise SkinLoadError(
                        f"skin id '{skin.skin_id}' is already used; built-in ids are reserved"
                    )
                skins[skin.skin_id] = skin
            except (OSError, UnicodeError, json.JSONDecodeError, SkinLoadError) as exc:
                message = f"Could not load skin {manifest_path.parent.name!r}: {exc}"
                self._errors.append(message)
                logger.warning(message)
        return skins

    def _load_manifest(
        self,
        manifest_path: Path,
        available_bases: dict[str, SkinDefinition],
    ) -> SkinDefinition:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SkinLoadError("skin.json must contain a JSON object")
        if data.get("schema_version") != SKIN_SCHEMA_VERSION:
            raise SkinLoadError(f"schema_version must be {SKIN_SCHEMA_VERSION}")

        skin_id = str(data.get("id", "")).strip().lower()
        if _SKIN_ID_PATTERN.fullmatch(skin_id) is None:
            raise SkinLoadError("id must use 1-64 lowercase letters, digits, '.', '_' or '-'")
        name = str(data.get("name", "")).strip()
        if not name or len(name) > 80:
            raise SkinLoadError("name must contain 1-80 characters")
        description = str(data.get("description", "Custom user skin")).strip()

        base_value = data.get("extends", DEFAULT_SKIN_ID)
        base: SkinDefinition | None
        if base_value is None:
            base = None
        elif (
            isinstance(base_value, str)
            and base_value in available_bases
            and available_bases[base_value].built_in
        ):
            base = available_bases[base_value]
        else:
            raise SkinLoadError("extends must be 'freaky', 'fastilicious' or null")

        colors = dict(base.colors if base is not None else FREAKY_COLORS)
        color_data = data.get("colors", {})
        if not isinstance(color_data, dict):
            raise SkinLoadError("colors must be a JSON object")
        for role, value in color_data.items():
            if not isinstance(role, str) or role not in FREAKY_COLORS:
                raise SkinLoadError(f"unknown semantic color role: {role!r}")
            color = str(value)
            if not QColor(color).isValid():
                raise SkinLoadError(f"invalid color for {role!r}: {color!r}")
            colors[role] = color

        root_dir = manifest_path.parent.resolve()
        stylesheet = base.stylesheet if base is not None else ""
        if base is not None:
            for role, base_color in base.colors.items():
                stylesheet = stylesheet.replace(base_color, colors[role])
        stylesheet_name = data.get("stylesheet")
        if stylesheet_name is not None:
            if not isinstance(stylesheet_name, str):
                raise SkinLoadError("stylesheet must be a relative path")
            stylesheet_path = _safe_child(root_dir, stylesheet_name)
            if not stylesheet_path.is_file():
                raise SkinLoadError(f"stylesheet does not exist: {stylesheet_name}")
            if stylesheet_path.stat().st_size > MAX_STYLESHEET_BYTES:
                raise SkinLoadError("stylesheet is larger than 1 MB")
            stylesheet += "\n" + stylesheet_path.read_text(encoding="utf-8")
        if not stylesheet.strip():
            raise SkinLoadError("a standalone skin needs a stylesheet")
        for match in _COLOR_TOKEN_PATTERN.finditer(stylesheet):
            if match.group(1) not in colors:
                raise SkinLoadError(
                    f"stylesheet references unknown color role: {match.group(1)}"
                )
        for match in _ASSET_TOKEN_PATTERN.finditer(stylesheet):
            _normalize_logical_asset(match.group(1).strip())

        asset_overrides = self._load_asset_map(data.get("assets", {}), root_dir)
        return SkinDefinition(
            skin_id=skin_id,
            name=name,
            description=description,
            stylesheet=stylesheet,
            colors=colors,
            root_dir=root_dir,
            asset_overrides=asset_overrides,
        )

    def _load_asset_map(self, data: Any, root_dir: Path) -> dict[str, Path]:
        if not isinstance(data, dict):
            raise SkinLoadError("assets must be a JSON object")
        assets: dict[str, Path] = {}
        for logical_name, relative_path in data.items():
            if not isinstance(logical_name, str) or not isinstance(relative_path, str):
                raise SkinLoadError("asset names and paths must be strings")
            normalized = _normalize_logical_asset(logical_name)
            candidate = _safe_child(root_dir, relative_path)
            if not candidate.is_file():
                raise SkinLoadError(f"asset does not exist: {relative_path}")
            assets[normalized] = candidate
        return assets


class SkinManager(QObject):
    """Apply skins immediately and keep the selected skin persistent."""

    skin_changed = Signal(str)
    catalog_changed = Signal()

    def __init__(
        self,
        app: QApplication,
        custom_skins_dir: Path,
        settings_service: SettingsService,
    ) -> None:
        super().__init__()
        self._app = app
        self._settings_service = settings_service
        self._catalog = SkinCatalog(custom_skins_dir)
        self._skins: dict[str, SkinDefinition] = {}
        self._active_skin: SkinDefinition | None = None

    @property
    def custom_skins_dir(self) -> Path:
        return self._catalog.custom_skins_dir

    @property
    def active_skin_id(self) -> str:
        return self._active_skin.skin_id if self._active_skin is not None else DEFAULT_SKIN_ID

    @property
    def errors(self) -> tuple[str, ...]:
        return self._catalog.errors

    def available_skins(self) -> tuple[SkinDefinition, ...]:
        return tuple(self._skins.values())

    def initialize(self, defaults: AppSettings) -> str:
        """Discover skins and activate the persisted selection."""
        self.reload()
        saved_skin_id = self._settings_service.load(defaults).theme_name
        return self.activate(saved_skin_id)

    def reload(self) -> None:
        """Rescan custom skin folders without restarting the application."""
        active_id = self.active_skin_id
        self._skins = self._catalog.discover()
        self.catalog_changed.emit()
        if self._active_skin is not None:
            self.activate(active_id)

    def activate(self, skin_id: str, *, persist: bool = True) -> str:
        """Activate a known skin, falling back safely to Freaky."""
        normalized = LEGACY_SKIN_ALIASES.get(skin_id.strip().lower(), skin_id.strip().lower())
        skin = self._skins.get(normalized) or self._skins[DEFAULT_SKIN_ID]
        self._active_skin = skin
        _active_colors.clear()
        _active_colors.update(skin.colors)
        set_asset_resolver(self.resolve_asset)

        self._app.setPalette(build_palette(skin.colors))
        self._app.setStyleSheet(self._render_stylesheet(skin))
        self._app.setWindowIcon(QIcon(str(self.resolve_asset("app_logo.png"))))
        for widget in self._app.topLevelWidgets():
            refresh_skin_assets(widget)
        if persist:
            self._settings_service.set_theme_name(skin.skin_id)
        self.skin_changed.emit(skin.skin_id)
        return skin.skin_id

    def resolve_asset(self, logical_name: str) -> Path:
        """Resolve an active skin asset and fall back to the packaged asset."""
        if self._active_skin is not None:
            candidate = self._active_skin.resolve_asset(logical_name)
            if candidate is not None:
                return candidate
        return Path(__file__).resolve().parent.parent / "assets" / logical_name

    def _render_stylesheet(self, skin: SkinDefinition) -> str:
        def replace_color(match: re.Match[str]) -> str:
            role = match.group(1)
            if role not in skin.colors:
                raise SkinLoadError(f"stylesheet references unknown color role: {role}")
            return skin.colors[role]

        def replace_asset(match: re.Match[str]) -> str:
            return self.resolve_asset(match.group(1).strip()).as_posix()

        rendered = _COLOR_TOKEN_PATTERN.sub(replace_color, skin.stylesheet)
        return _ASSET_TOKEN_PATTERN.sub(replace_asset, rendered)


def skin_color(role: str) -> str:
    """Return a semantic color for custom-painted widgets."""
    try:
        return _active_colors[role]
    except KeyError as exc:
        raise KeyError(f"Unknown skin color role: {role}") from exc


def _built_in_skins() -> dict[str, SkinDefinition]:
    freaky = SkinDefinition(
        skin_id="freaky",
        name="Freaky",
        description="Original navy, gold and neon-blue design",
        stylesheet=freaky_stylesheet(),
        colors=dict(FREAKY_COLORS),
        built_in=True,
    )
    fastilicious = SkinDefinition(
        skin_id="fastilicious",
        name="Fastilicious",
        description="Provisional raspberry-and-aqua racing console mockup",
        stylesheet=fastilicious_stylesheet(),
        colors=dict(FASTILICIOUS_COLORS),
        built_in=True,
    )
    return {freaky.skin_id: freaky, fastilicious.skin_id: fastilicious}


def _normalize_logical_asset(value: str) -> str:
    path = Path(value.replace("\\", "/"))
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise SkinLoadError(f"unsafe logical asset path: {value!r}")
    return path.as_posix()


def _safe_child(root: Path, relative_path: str | Path) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute():
        raise SkinLoadError(f"path must be relative: {relative_path!r}")
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise SkinLoadError(f"path leaves the skin folder: {relative_path!r}")
    return candidate
