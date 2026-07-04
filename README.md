# Freak Media Player

A modular native Windows media player focused on long-term extensibility.

The project is intentionally structured around small, replaceable modules:

- UI: PySide6 based desktop shell
- Core: UI-neutral playback, queue, playlist and event concepts
- Providers: YouTube Music, local files, radio and other media sources behind one interface
- Database: SQLite persistence with migrations
- Plugins: extension points for visualizers, lyrics, integrations and tools

See docs/ARCHITECTURE.md for the initial architecture plan.

## Build

Run this on Windows to create the desktop executable:

```powershell
.\build.bat
```

The generated executable is written to `dist\FreakMediaPlayer\FreakMediaPlayer.exe`.

## Local Data

Runtime data is stored under the current Windows user profile:

```text
%LOCALAPPDATA%\FreakMediaPlayer\
```

The SQLite database is created there automatically on startup.
