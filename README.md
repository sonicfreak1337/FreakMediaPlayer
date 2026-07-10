# Freak Media Player

A modular Winamp-inspired desktop music player focused on local playback today,
with a provider-based architecture for YouTube Music and other sources later.

Current version: `0.7.3`

## Current Features

- Import local audio by file, folder, or drag and drop
- Read embedded title, artist, album, year, genre and track metadata
- Separate local library and persistent active playlist
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
- Dockable audio-reactive visualizer with thirteen animated presets
- Live-switchable skin system with the default Freaky design and provisional
  Fastilicious racing-console mockup
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
- **Providers:** YouTube Music, local files, radio, and other media sources behind one
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
asset convention and a ready-to-copy example.

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
The thirteen included presets range from the branded gold/blue Freak Pulse view
through classic spectrum and oscilloscope views to layered mandalas, perspective
grids, particle orbits and animated solar
corona effects. The module can be toggled through `Module > Visualizer` or
`Ctrl+Shift+V`.

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
