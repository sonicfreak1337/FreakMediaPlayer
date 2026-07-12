# Freak Media Player

A modular Winamp-inspired desktop music player focused on local playback through
version 1.0, with a provider-based architecture for external sources after 1.0.

Current version: `0.9.0`

## Current Features

- Import local audio by file, folder, or drag and drop
- Manage persistent music folders with targeted background rescans and cancellation
- Read embedded title, artist, album, year, genre and track metadata
- Search and combine artist, album, genre, year, favorite and file-status filters
- Browse grouped artists, albums and genres plus Favorites and Recently Added views
- Separate local library and persistent active playlist
- Create, open, duplicate, rename, clear and delete multiple named playlists
- Import and export local M3U/M3U8 playlists with relative or absolute paths
- Mark favorites from the Player and see them in library and playlist tables
- Detect missing or unreadable files, relocate moved tracks and safely edit
  database-only metadata without modifying audio files
- Desktop-detachable dock modules for Library, Playlist, Equalizer, Player, and
  Visualizer (use the title-bar undock button or double-click the title bar)
- Close and restore optional modules through the `Module` menu; Player stays open
- Drag and drop from the library into a chosen playlist position
- Manual playlist ordering through drag and drop or move controls
- Playback for common local formats supported by the bundled FFmpeg libraries
- Streaming local decoding through PyAV/FFmpeg with bounded memory usage
- Native PCM output through Qt AudioSink
- Play, pause, stop, previous, next, seek, volume, and mute controls
- Non-repeating playlist shuffle with previous/next history
- Repeat All and Repeat One playback modes
- Automatic playback of the next playlist title
- Highlighted currently playing playlist row
- Clickable and draggable playback and volume sliders
- Multi-select library tables with Shift-click and Ctrl-click
- Sortable library columns and explicit playlist ordering
- Remove one or more selected local tracks from the library
- Remove playlist entries without deleting library tracks
- Audible parametric equalizer with metal-subgenre presets and Custom mode
- DAW-style response graph with frequency, gain, Q, enable, and preamp controls
- Dockable audio-reactive visualizer with fifteen animated presets
- Live-switchable skin system with the default Freaky design and the black-metal,
  red/orange Fastilicious console skin
- User skins with inherited or standalone QSS, semantic colors and custom assets
- Branded application/taskbar icon and logo-based fallback artwork
- Automatic album-cover discovery from conventional images beside local tracks
- Gold playing-row emphasis and restrained outlined table selection
- SQLite storage for imported tracks and settings
- Versioned settings and database migrations
- Windows executable build script

## Architecture

The project is built around small, replaceable modules:

- **UI:** PySide6 desktop shell
- **Core:** UI-neutral playback, queue, playlist, and event concepts
- **Providers:** Local files through 1.0; external sources later behind the same
  shared interface
- **Database:** SQLite persistence with migrations
- **Plugins:** Extension points for visualizers, lyrics, integrations, and tools

See `docs/ARCHITECTURE.md` for the architecture plan.

## Modular desktop interface

Version `0.7.0` introduces the fully redesigned mockup-driven interface. Player,
Library, Playlist, Equalizer and Visualizer use a consistent dock module chrome.
Use the `↗` control or drag a module title to detach it into its own desktop
window; double-clicking its title docks it again. Optional modules can be closed
and restored from the `Module` button in the Player. The Player remains available.

## Skins

Use the `SKIN` dropdown in the title bar to switch immediately between Freaky,
Fastilicious and installed user skins. The selection persists across launches.
Custom skin folders live below `%LOCALAPPDATA%\FreakMediaPlayer\skins` and can
override the complete QSS, semantic colors and any packaged image or icon while
retaining safe fallbacks. See [`docs/SKINS.md`](docs/SKINS.md) for the manifest,
asset convention and a ready-to-copy example. The built-in Visualizer follows
skin changes by selecting Abyssal Cataclysm or Fire of Chaos automatically.

## Equalizer

Since version `0.5.0`, decoded PCM audio passes through a real parametric equalizer
before it reaches the Windows output device. Each band is a stateful peaking
filter with frequency, gain and Q controls. The displayed response curve uses
the same coefficients as the audio processor.

PyAV handles local decoding, SciPy applies cascaded second-order filters, and Qt
`QAudioSink` writes the final stereo PCM stream to the native audio device.

## Visualizer

Version `0.6.0` adds the built-in Freak Visualizer plugin. It receives the
actual post-DSP PCM stream through a bounded, thread-safe sample tap and derives
waveform, spectrum, bass, midrange and treble energy without delaying playback.
The fifteen included presets range from Freaky's bombastic water apocalypse
Abyssal Cataclysm and the bass-driven Fastilicious firestorm Fire of Chaos to
the legacy Freak Pulse, classic spectrum and oscilloscope views, layered
mandalas, perspective grids, particle orbits and animated solar corona effects.
Rendering stays inactive without playback, targets 60 FPS while the application
is focused and automatically reduces its refresh rate in the background.
The module can be toggled through `Module > Visualizer` or `Ctrl+Shift+V`.

## Build

Run this on Windows to create the desktop executable:

```powershell
.\build.bat
```

The generated executable is written to `dist\FreakMediaPlayer\FreakMediaPlayer.exe`.

For fast development iterations, run:

```powershell
.\fast_build.bat
```

This reuses the build environment and PyInstaller cache, skips dependency
synchronization when the required packages are already installed, and excludes
unused optional Qt modules. Its executable is written to
`dist-dev\FreakMediaPlayer\FreakMediaPlayer.exe`. Run `build.bat` after changing
dependencies and for release builds.

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

## Roadmap

The release plan through the stable local-player milestone 1.0 is documented in
[`ROADMAP.md`](ROADMAP.md). External audio sources are explicitly scheduled only
after version 1.0.
