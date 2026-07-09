# Changelog

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
