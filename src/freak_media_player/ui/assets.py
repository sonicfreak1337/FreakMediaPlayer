"""Packaged UI asset lookup."""

from __future__ import annotations

from pathlib import Path


def asset_path(file_name: str) -> Path:
    """Return an asset path that works from source and bundled installations."""
    return Path(__file__).resolve().parent.parent / "assets" / file_name
