# Changelog

## 0.2.0 - 2026-07-05

- Added visible application versioning in the window title and status bar.
- Added an Equalizer section with Flat, Metal, Metalcore and Custom curves.
- Added equalizer domain models and a UI-neutral equalizer service.
- Improved playback controls with a combined play/pause button, stop, seek jumps,
  volume and mute.
- Improved playback and volume sliders for click, drag and release behavior.
- Added local library removal through the toolbar and Delete key.
- Added Shift-click and Ctrl-click multi-selection in local library and playlist
  tables.
- Added sortable library and playlist table columns.
- Added tests for equalizer presets, track removal and playback controls.

## 0.1.0 - 2026-07-04

- Created the modular PySide6 desktop application skeleton.
- Added provider, plugin, playback, settings and database boundaries.
- Added SQLite migrations and repositories.
- Added local file provider and local library import.
- Added initial playback through Qt Multimedia.
- Added Windows build script for the executable.
