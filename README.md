# Freak Media Player

A modular Winamp-inspired desktop music player focused on local playback today,
with a provider-based architecture for YouTube Music and other sources later.

Current version: `0.3.0`

## Current Features

- Import local audio by file, folder, or drag and drop
- Separate local library and persistent active playlist
- Drag and drop from the library into a chosen playlist position
- Manual playlist ordering through drag and drop or move controls
- Playback for common formats supported by the Windows Qt multimedia backend
- Play, pause, stop, previous, next, seek, volume, and mute controls
- Automatic playback of the next playlist title
- Clickable and draggable playback and volume sliders
- Multi-select library tables with Shift-click and Ctrl-click
- Sortable library columns and explicit playlist ordering
- Remove one or more selected local tracks from the library
- Remove playlist entries without deleting library tracks
- Equalizer screen with Flat, Metal, Metalcore, and Custom curves
- Compact Winamp-inspired dark UI with green library/display accents
- Sidebar only shows sections that are currently implemented
- SQLite storage for imported tracks and settings
- Versioned settings and database migrations
- Windows executable build script

## Architecture

The project is built around small, replaceable modules:

- **UI:** PySide6 desktop shell
- **Core:** UI-neutral playback, queue, playlist, and event concepts
- **Providers:** YouTube Music, local files, radio, and other media sources behind one
  shared interface
- **Database:** SQLite persistence with migrations
- **Plugins:** Extension points for visualizers, lyrics, integrations, and tools

See `docs/ARCHITECTURE.md` for the architecture plan.

## Equalizer

Version `0.3.0` keeps the equalizer visible and clickable through the app UI. The
current Qt backend stores and exposes the selected curve. Real DSP processing is
planned for the next audio-engine milestone because Qt `QMediaPlayer` does not
provide a native equalizer stage.

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
