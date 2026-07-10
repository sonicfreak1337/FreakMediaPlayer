# Changelog

## 0.6.0 - 2026-07-10

- Added the built-in Freak Visualizer plugin with a real post-DSP audio sample
  tap and six audio-reactive presets: Neon Spectrum, Radial Bloom, Star Tunnel,
  Electric Oscilloscope, Aurora Waves and Cosmic Constellation.
- Added a dockable Visualizer panel and an `Ansicht > Visualizer` toggle with
  the `Ctrl+Shift+V` shortcut.
- Added six advanced presets: Spectral Mandala, Cyber Grid, Liquid Orbit,
  Frequency City, DNA Helix and Solar Flare, bringing the preset total to twelve.
- Extended visualizer analysis with independent bass, midrange and treble
  energy values for richer multi-layer animation.
- Added automatic rendering checks for every bundled visualizer preset.

## 0.5.0 - 2026-07-10

- Added embedded metadata extraction for title, artist, album artist, album,
  release year, genre, track number, disc number and duration.
- Added a versioned, one-time metadata refresh for existing local-library rows.
- Added Album and Year columns to both the library and active playlist.
- Added non-repeating playlist shuffle with played/unplayed cycle state and
  playback history for previous/next navigation.
- Added Repeat All and Repeat One modes with automatic end-of-track handling.
- Added Death Metal, Deathcore, Black Metal, Doom Metal, Thrash Metal, Djent and
  Progressive Metal equalizer presets with preamp headroom.
- Added `fast_build.bat` with cached developer builds and optional Qt-module
  exclusions.
- Reduced release build overhead by relying on PyInstaller's PySide6 import
  analysis instead of collecting every PySide6 component.
- Added an explicit green `Shuffle: ON` indicator to the player controls.
- Kept all transitive SciPy signal dependencies in developer builds so the DAW
  equalizer cannot silently disappear through an incomplete package.

## 0.4.0 - 2026-07-10

- Replaced direct `QMediaPlayer` playback with a streaming audio pipeline.
- Added PyAV/FFmpeg decoding with bounded-memory PCM buffering and seeking.
- Added native PCM output through Qt `QAudioSink`.
- Added a real block-based parametric equalizer using cascaded biquad filters.
- Added per-band frequency, gain, Q and enabled parameters plus global preamp.
- Replaced the graphic equalizer sliders with an interactive DAW-style response
  graph and selectable band controls.
- Kept the former Qt backend as a dependency fallback.
- Added end-to-end tests for decoding, DSP continuity, PCM conversion and output
  pumping.

## 0.3.2 - 2026-07-10

- Highlighted the currently playing playlist row with a dedicated color and
  play icon.
- Kept the marker synchronized with direct playback, automatic advancement and
  previous/next controls.

## 0.3.1 - 2026-07-10

- Replaced page-style module navigation with one shared workspace.
- Showed the local library and active playlist side by side for direct drag and
  drop.
- Placed the equalizer in the same resizable window below the track workspace.
- Added independently collapsible headers for Library, Playlist and Equalizer.
- Kept the player controls permanently visible below all modules.

## 0.3.0 - 2026-07-10

- Fixed sidebar navigation so Playlist and Equalizer open reliably.
- Split the local library and active playlist into separate modules.
- Added a persistent, ordered playlist backed by SQLite.
- Added drag and drop from the library into any playlist position.
- Added playlist reordering through drag and drop and move controls.
- Added playlist removal without deleting tracks from the library.
- Changed previous and next controls to navigate playlist tracks.
- Added automatic playback of the next title when a track finishes.
- Added regression coverage for playlist persistence, ordering, navigation and
  automatic track advancement.

## 0.2.1 - 2026-07-05

- Fixed equalizer interaction by switching the bands to larger clickable sliders.
- Started the Winamp-inspired UI direction with dark panels, blue headers and
  green library/display accents.
- Hid unused future sections from the sidebar while development is paused.
- Removed placeholder docks for queue, lyrics and album information until those
  features are actually wired.
- Made library and player panels more compact.

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
