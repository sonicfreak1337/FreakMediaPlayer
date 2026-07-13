# Freak Media Player

A modular Winamp-inspired desktop music player focused on local playback through
version 1.0, with a provider-based architecture for external sources after 1.0.

Current version: `1.1.0`

## Current Features

- Import local audio by file, folder, or drag and drop
- Manage persistent music folders with targeted background rescans and cancellation
- Read embedded title, artist, album, year, genre and track metadata
- Infer artist and title from `Artist - Title` filenames when tags are missing
- Search and combine artist, album, genre, year, favorite and file-status filters
- Browse grouped artists, albums and genres plus Favorites and Recently Added views
- Separate local library and persistent active playlist
- Create, open, duplicate, rename, clear and delete multiple named playlists
- Import and export local M3U/M3U8 playlists with relative or absolute paths
- Mark favorites from the Player and see them in library and playlist tables
- Detect missing or unreadable files, relocate moved tracks and safely edit
  database-only metadata without modifying audio files
- Position-locked, desktop-detachable modules for Library, Playlist, Equalizer,
  Player and Visualizer (use the explicit title-bar undock button)
- Close and restore optional modules through the `Module` menu; Player stays open
- Open the fully optional Internet Radio module only when needed; it supports
  paginated station search, filters, favorites, history and custom HTTP(S) streams
- Resolve bounded PLS/M3U station playlists, preserve HLS for FFmpeg, display
  available live stream titles and retry interrupted radio connections up to three times
- Drag and drop from the library into a chosen playlist position
- Manual playlist ordering through drag and drop or move controls
- Playback for common local formats supported by the bundled FFmpeg libraries
- Streaming local decoding through PyAV/FFmpeg with bounded memory usage
- Selectable system audio device and Mono, Stereo, 5.1 or 7.1 PCM output through
  Qt AudioSink when supported by the device
- Play, pause, stop, previous, next, seek, volume, and mute controls
- Hook-free Qt handling for play/pause, stop, previous and next media keys
- Non-repeating playlist shuffle with previous/next history
- Repeat All and Repeat One playback modes
- Automatic playback of the next playlist title
- Automatic bounded skip over unreadable Up Next and playlist entries, including
  asynchronous decoder failures
- Highlighted currently playing playlist row
- Clickable and draggable playback and volume sliders
- Multi-select library tables with Shift-click and Ctrl-click
- Sortable library columns and explicit playlist ordering
- Remove one or more selected local tracks from the library
- Remove playlist entries without deleting library tracks
- Audible parametric equalizer with a two-stage genre/subgenre catalog and Custom mode
- DAW-style response graph with frequency, gain, Q, enable, and preamp controls
- Dockable audio-reactive visualizer with fifteen animated presets
- Live-switchable skin system with the default Freaky design and the black-metal,
  red/orange Fastilicious console skin
- User skins with inherited or standalone QSS, semantic colors and custom assets
- Branded application/taskbar icon and logo-based fallback artwork
- Automatic album-cover discovery from conventional images beside local tracks
- Per-track local cover overrides with one-click return to automatic discovery
- Gold playing-row emphasis and restrained outlined table selection
- SQLite storage for imported tracks and settings
- Versioned settings and database migrations
- Validated `.freakbackup` export and restore for the complete local database,
  with an automatic safety backup before replacement
- Windows builds plus `.deb`, `.rpm` and portable `.tar.gz` Linux packages

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
Use the `↗` control to detach or dock a module. Module positions cannot be changed
by dragging or double-clicking, avoiding accidental layout edits. Optional modules
can be closed and restored from the `Module` button in the Player. The Player
remains available.

## Skins

Use the `SKIN` dropdown in the title bar to switch immediately between Freaky,
Fastilicious and installed user skins. The selection persists across launches.
Custom skin folders live below the platform data directory (`%LOCALAPPDATA%\FreakMediaPlayer\skins`
on Windows or `~/.local/share/freak-media-player/skins` on Linux) and can
override the complete QSS, semantic colors and any packaged image or icon while
retaining safe fallbacks. See [`docs/SKINS.md`](docs/SKINS.md) for the manifest,
asset convention and a ready-to-copy example. The built-in Visualizer follows
skin changes by selecting Abyssal Cataclysm or Fire of Chaos automatically.

## Equalizer

Since version `0.5.0`, decoded PCM audio passes through a real parametric equalizer
before it reaches the native output device. Each band is a stateful peaking
filter with frequency, gain and Q controls. The displayed response curve uses
the same coefficients as the audio processor.

Preset selection is split into **Genre** and **Subgenre**. The bundled catalog
covers 12 broad groups and more than 100 style-specific starting curves, from Pop,
Rock, Metal and Electronic through Jazz, Classical, Country, Reggae, Latin and
soundtracks. Manual edits move the selection to Custom without losing the curve.
All musical presets use broad bands and automatic preamp headroom; their curves
are tonal starting points rather than corrective rules for every recording.

PyAV handles local decoding, SciPy applies cascaded second-order filters, and Qt
`QAudioSink` writes the final configured PCM stream to the native audio device.

## Audio output and channel mapping

The Settings dialog lists only the Mono, Stereo, 5.1 and 7.1 configurations that
the selected audio device reports as supported. Changing device or speaker mode
restarts the stream near its previous position; an unavailable saved mode safely
falls back to Stereo.

Channel conversion happens once, after PyAV has decoded the source at 48 kHz and
before equalizer processing. Native channels keep FFmpeg's standard order. Mono is
routed to Center for surround output and duplicated to Left/Right for Stereo.
Stereo keeps its original Left/Right channels, adds a -6 dB Center and -6 dB rear
feed for surround, and leaves LFE silent. Surround downmixes use Center at -3 dB,
surround channels at -6/-9 dB and LFE at -12 dB; each output row is normalized so
a full-scale correlated input cannot exceed full scale before DSP.

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

## Optional Internet Radio

Open `Module > Internet Radio…` or press `Ctrl+Shift+R`. The plugin is lazy: its
separate window, private database and network search are not opened until this
command is used. The window never joins or changes the player's dock layout.
Radio playback is transient and leaves the active local playlist unchanged.
The main Player controls play/pause, stop, volume, mute and audio output; decoded
radio PCM also uses the selected channel mode, equalizer and Visualizer.

Station discovery queries the public Radio Browser directory over HTTPS. Playing
a station connects directly to the station's HTTP(S) stream. The plugin requests
no account or device location and sends no telemetry. Radio favorites, the latest
200 history entries and manually entered stream URLs are stored locally in
`data/plugins/internet-radio.sqlite3`; no audio is recorded. Closing the window keeps
the launcher available in the Module menu, while never opening it leaves local-player
data and workflows unchanged.

PLS and ordinary M3U links are resolved with bounded size and nesting limits;
HLS/M3U8 remains in FFmpeg's streaming pipeline. When supplied by a station, live
stream titles replace the static station title. Failed radio connections are
classified (timeout, DNS, TLS, playlist, codec and common HTTP failures) and use
three cancellable retries with increasing delays. Stop or switching away from
radio cancels pending retries immediately.

The automated local-server matrix decodes real generated MP3, AAC, Ogg Vorbis,
Opus and HLS streams over HTTP in addition to testing ICY metadata changes,
playlist redirects, bounded probing, stalled-stream cleanup and logo delivery;
public stations remain excluded from automated tests. AAC+ uses the same bundled
FFmpeg AAC decoder and remains part of the public-network release smoke test.

When a station publishes ICY/stream song information, the main Player shows the
current title and artist while keeping `Station: <name>` visible underneath. If
metadata stops or is unavailable, it falls back to the station name and country.

Small, Normal and Stable buffer profiles are persisted by the plugin and apply
from the next connection. When Radio Browser supplies a distinct fallback URL,
retries advance to it before reusing the previous endpoint. Favorites and custom
stations can be transferred as a lossless JSON collection or a standard UTF-8
M3U8 playlist. The normal `.freakbackup` package includes and validates the
optional radio database whenever it exists.

The separate radio window restores its last search, country, region, language,
tag, codec, minimum/maximum bitrate, reachability and sorting filters. Selecting
a result shows its complete available station details and provides separate copy
actions for name, homepage and stream URL. Station logos use an asynchronous local
cache limited to HTTPS/HTTP image responses, 2 MiB per image, seven days and
24 MiB total; the cache can be cleared directly from the radio window.
Listening-history writes and all station-logo network requests can be disabled
independently in the radio window; existing history remains explicitly clearable.
The complete plugin can be disabled in Player Settings for the next start; when
disabled it registers no provider, menu action, window, database or network work.

Country, region and language fields accept up to four comma-separated alternatives;
tag values are combined as required tags. Batched searches are capped at sixteen
directory requests, deduplicate stable station IDs and apply global sorting and
pagination afterward. The result status includes per-country counts for the loaded
page, while Random requests a fresh result from the active server-side filter set.
History entries can be removed individually. Custom streams can be added, edited,
deleted and tested asynchronously with a bounded 1 KiB connection probe that never
stores the received audio bytes.

## Build

### Linux 1.1

Build on a current x86-64 or ARM64 Linux host with Python 3.11+, the project build
dependencies and the packaging tools available on that distribution:

```bash
python3 -m venv .venv-build
. .venv-build/bin/activate
python -m pip install --upgrade pip
python -m pip install '.[build]'
./build_linux.sh
```

The script always creates a portable `.tar.gz` below `dist/linux`. It additionally
creates a `.deb` when `dpkg-deb` is installed and an `.rpm` when `rpmbuild` is
installed. PyInstaller must run natively on Linux; a Windows build cannot be
cross-compiled into a Linux executable.

Install the resulting package with the normal command for the distribution:

```bash
# Debian, Ubuntu, Linux Mint, Pop!_OS
sudo apt install ./dist/linux/freak-media-player_1.1.0_amd64.deb

# Fedora, RHEL, Rocky Linux, AlmaLinux
sudo dnf install ./dist/linux/freak-media-player-1.1.0-1.*.rpm

# openSUSE
sudo zypper install ./dist/linux/freak-media-player-1.1.0-1.*.rpm

# Distribution-neutral archive (system-wide)
tar -xzf dist/linux/FreakMediaPlayer-1.1.0-linux-x86_64.tar.gz
cd FreakMediaPlayer-1.1.0-linux-x86_64
./install.sh

# Or install the archive only for the current user
./install.sh --user
```

After installation, start it from the desktop application menu or with
`freak-media-player`. Package-manager installs can be removed with
`apt remove freak-media-player` or `dnf remove freak-media-player`.

### Windows

Run this on Windows to create the desktop executable:

```powershell
.\build.bat
```

The generated executable is written to `dist\FreakMediaPlayer\FreakMediaPlayer.exe`.

Run `build_portable.bat` for an isolated portable package below
`release\FreakMediaPlayer-Portable`. Its `portable.flag` keeps database, settings,
logs and skins inside the package's `data` folder.

The executable accepts supported audio paths as command-line arguments. For a
per-user Windows `Open with` registration without administrator rights, run:

```powershell
.\scripts\register_file_associations.ps1 -ExecutablePath .\FreakMediaPlayer.exe
```

Use `scripts\unregister_file_associations.ps1` before removing that registration.

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

## Keyboard shortcuts

- `Space`: Play/Pause
- `Ctrl+.`: Stop
- `Ctrl+Left` / `Ctrl+Right`: Previous/Next track
- `Ctrl+Up` / `Ctrl+Down`: Volume up/down
- `M`: Mute/restore volume
- `Ctrl+H`: Toggle Shuffle
- `Ctrl+R`: Cycle Repeat Off/All/One
- `Ctrl+F`: Show the library and focus search
- `Ctrl+1`, `Ctrl+2`, `Ctrl+3`: Toggle Library, Playlist and Equalizer
- `Ctrl+Shift+V`: Toggle Visualizer
- `Ctrl+Shift+R`: Open Internet Radio
- `Delete`: Remove selected active-playlist rows

## Diagnostics and support

Open Player Settings and choose `Diagnostics…` to inspect the application version,
database schema, local data paths, active audio output and recent errors. Runtime
logs rotate below the platform data directory; personal home paths are
masked in the on-screen error summary. `About…` lists the core runtime components
and their license families.

On first start, a skippable setup asks for a music folder, audio output and
session-restore preference. Settings also contains safe maintenance actions for
restoring the default layout, rebuilding local metadata and resetting settings
without deleting library or playlist data.

## Local Data

Runtime data is stored per user:

```text
Windows: %LOCALAPPDATA%\FreakMediaPlayer\
Linux:   ${XDG_DATA_HOME:-$HOME/.local/share}/freak-media-player/
```

The SQLite database is created there automatically on startup.

## Changelog

See `CHANGELOG.md`.

## Roadmap

The completed release plan through the stable local-player milestone 1.0 is
documented in [`ROADMAP.md`](ROADMAP.md). Development after 1.0 starts with the
directly integrated internet-radio plugin described in
[`docs/INTERNET_RADIO_ROADMAP.md`](docs/INTERNET_RADIO_ROADMAP.md).
