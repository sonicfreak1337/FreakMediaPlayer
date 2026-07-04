# Freak Media Player

Freak Media Player is a modular native Windows media player built with Python,
PySide6 and SQLite. The current focus is local playback, a clean architecture
and a desktop UI that can grow into provider and plugin based features later.

Current version: `0.2.0`

## Current Features

- Local audio library import by file, folder and drag and drop
- Playback for common formats supported by the Windows Qt multimedia backend
- Play, pause, stop, seek, volume and mute controls
- Clickable and draggable playback and volume sliders
- Multi-select library tables with Shift-click and Ctrl-click
- Sortable library and playlist table columns
- Remove one or more selected local tracks from the library
- Equalizer screen with Flat, Metal, Metalcore and Custom curves
- SQLite storage for imported local tracks and settings
- Versioned settings and database migrations
- Build script for a Windows executable

## Architecture

The project is intentionally structured around small, replaceable modules:

- UI: PySide6 based desktop shell
- Core: UI-neutral playback, queue, playlist and event concepts
- Providers: YouTube Music, local files, radio and other media sources behind one interface
- Database: SQLite persistence with migrations
- Plugins: extension points for visualizers, lyrics, integrations and tools

See `docs/ARCHITECTURE.md` for the architecture plan.

## Equalizer

Version `0.2.0` introduces the equalizer model, service and UI. The current Qt
backend stores and exposes the selected curve. Real DSP processing is planned for
the next audio-engine milestone because Qt `QMediaPlayer` does not provide a
native equalizer stage.

## Build

Run this on Windows to create the desktop executable:

```powershell
.\build.bat
```

The generated executable is written to `dist\FreakMediaPlayer\FreakMediaPlayer.exe`.

## Development Checks

Useful local checks:

```powershell
$env:PYTHONPATH = "src"
python -m compileall src tests
```

If the development dependencies are installed:

```powershell
pytest
```

## Local Data

Runtime data is stored under the current Windows user profile:

```text
%LOCALAPPDATA%\FreakMediaPlayer\
```

The SQLite database is created there automatically on startup.

## Changelog

See `CHANGELOG.md`.
