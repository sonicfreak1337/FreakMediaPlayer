# Changelog

## 0.9.2 - Unreleased

- Added validated local backup packages for library data, playlists, favorites and
  settings, plus integrity-checked restore with an automatic pre-restore backup.

## 0.9.1 - 2026-07-12

- Activated a persistent Settings dialog for audio output, paused session restore,
  end-of-track behavior, layout restore and Visualizer performance.
- Added live enumeration and selection of Windows audio output devices with an
  explicit follow-default option and safe fallback for unavailable saved devices.
- Added device-validated Mono, Stereo, 5.1 and 7.1 output with deterministic,
  peak-stable upmix/downmix matrices and multichannel Visualizer sample capture.
- Added internal temporary next-track scheduling ahead of saved playlist order.
- Added bounded automatic continuation after load, decoder or backend errors,
  preferring Up Next entries and retaining a visible final error if all fail.
- Added application-wide Qt media-key handling for Windows transport controls
  without global keyboard hooks.
- Added persistent per-track local cover overrides with reset to automatic folder
  artwork discovery.
- Added metadata fallback for untagged files named `Artist - Title`, while embedded
  tags continue to take priority.
- Added documented window-wide shortcuts for transport, volume, mute, Shuffle,
  Repeat, library search and core module visibility.

## 0.9.0 - 2026-07-12

- Added transactional batch upserts and automated 10,000-track acceptance coverage
  for import, search, rescan, ordering, multi-row moves and every schema upgrade.
- Clarified playlist removal, library-only removal and irreversible disk deletion,
  with a separate confirmation-gated file deletion workflow and result report.
- Added grouped artist/album/genre browsing alongside the fast table plus dynamic
  Favorites and Recently Added library views.
- Added safe database-only editing for title, artist, album, year, genre and
  track/disc numbers, with manual overrides protected from metadata rescans.
- Added M3U/M3U8 import and export with UTF-8, relative and absolute local paths,
  automatic library import and skipped-entry result reporting.
- Activated the Player heart button with immediate SQLite persistence and favorite
  markers in both library and playlist, integrated with the favorite filter.
- Added multiple named persistent playlists with active-list restoration and
  create, open, duplicate, rename, clear and delete workflows.
- Added visible Available/Missing/Unreadable library status, a unique source-path
  constraint and manual file relocation that preserves track IDs and playlists.
- Moved file discovery and metadata extraction into a cancellable background
  importer with live progress and an added/updated/failed result summary.
- Added persistent managed music folders with add, remove-source and targeted
  rescan actions directly from the library folder menu.
- Added combinable library filters for artist, album, genre, year, favorites and
  live local-file status with a one-click search-and-filter reset.
- Added an instant imported-library search for title, artist, album, genre, year
  and filename, including multi-term matching and a clear no-results state.
- Expanded stability coverage for empty and changed playlists, stale sessions,
  repeated decoder restarts and clean worker-thread shutdown.
- Added concise transient status-bar feedback for imports, playback errors,
  library changes, playlist persistence and saved equalizer changes.
- Added explanatory first-run empty states to the library and playlist with the
  available import, add, double-click and drag-and-drop paths.
- Added a visible `Reset Layout` command to the Module menu that restores and
  immediately persists the complete startup layout, including plugin modules.
- Persisted and restored the main-window geometry plus every core and plugin
  module's size, position, visibility and docked or floating state.
- Completed session restoration for volume, equalizer, skin, active playlist,
  paused track position, Shuffle and Repeat without automatic playback.
- Added explicit Delete-key removal for selected active-playlist rows.
- Added an in-player playback error panel for missing, unreadable, damaged or
  unsupported files with direct retry, skip and playlist-removal actions.
- Prevented missing files from crashing session restore and retained decoder
  failure details in the visible playback state.
## 0.8.0 - 2026-07-12

- Reduced visualizer CPU usage with cached FFT and vignette data, pixel-bounded
  waveforms and selective antialiasing that retains smooth foreground contours.
- Kept the visualizer completely inactive until playback starts, renders at 60 FPS
  while the application is focused and falls back to an efficient background rate.
- Bypassed no-op equalizer stages, including the default Flat preset, while keeping
  active bands and preamp processing unchanged.
- Suspended audio, player and playlist timers whenever their work is inactive or
  hidden, and deferred decoding until playback actually starts.
- Disabled PCM sample conversion while the visualizer is hidden and reduced
  temporary allocations in sample downmixing and PCM output conversion.
- Avoided redundant player text, slider, icon and artwork updates while preserving
  live playback state, controls, skins and all visualizer presets.

## 0.7.3 - 2026-07-11

- Added a live, persistent skin system with the original interface as the default
  Freaky skin and the black-metal, red/orange Fastilicious console skin.
- Added a title-bar skin dropdown plus custom-skin reload and folder controls.
- Added safe external JSON/QSS skin discovery, semantic color overrides, custom
  asset mappings, convention-based asset replacement and packaged fallbacks.
- Bundled the supplied Fastilicious character and control assets plus the brutal,
  audio-reactive Fire of Chaos flame visualizer.
- Refined the Fastilicious panel chrome, removed remaining blue control states,
  corrected the invalid supplied Shuffle On icon and made Fire of Chaos activate with
  the skin automatically.
- Replaced broken screenshot-crop controls with the reliable Freaky transport,
  library, playlist, volume and settings icons, added a distinct muted speaker
  state and rebuilt the supplied logo master with a real transparent background.
- Reworked logo rendering to preserve the full character silhouette with a safe
  margin instead of cropping the hair and replaced the former segmented spectrum
  with layered flames, embers, bass shockwaves and a white-hot chaos core.
- Added Abyssal Cataclysm as Freaky's new default visualizer: a bombastic water
  apocalypse with spectrum-driven tsunami walls, a rotating maelstrom, bass
  pressure waves, underwater lightning, rain and treble-reactive spray.

## 0.7.2 - 2026-07-10

- Restored native Windows taskbar minimization behavior for the frameless player
  window.
- Persisted playback volume and the complete equalizer state across launches,
  including custom band parameters and preamp gain.
- Restored the last played track and timestamp in a paused state without automatic
  playback, with periodic and shutdown checkpoints.
- Added the Space key as a window-wide Play/Pause shortcut.

## 0.7.1 - 2026-07-10

- Replaced the original logo, Pause and Repeat graphics with the newly supplied
  transparent assets, including distinct Repeat Off, All and One states.
- Added the supplied dark inactive Shuffle artwork while retaining the gold icon
  for the enabled state.
- Removed the circular frame around the Player logo and regenerated the packaged
  Windows icon from the new transparent brand asset.
- Added automatic album-cover lookup for conventional image names and album-title
  matches in each local track's folder.
- Simplified the equalizer to handle-only vertical gain dragging and removed the
  blue points that obscured its slider handles.
- Changed table selection to a restrained outlined state and highlighted the
  currently playing playlist row in gold, even while it remains selected.
- Added Freak Pulse, a new audio-reactive gold and electric-blue Visualizer preset,
  bringing the plugin to thirteen presets.

## 0.7.0 - 2026-07-10

- Rebuilt the complete interface from the supplied high-fidelity mockup with a
  frameless branded window, navy panel chrome, gold accents and neon-blue controls.
- Reworked Player, Library, Playlist, Equalizer and Visualizer into consistent
  movable dock modules that can be reordered or detached into independent desktop
  windows via visible title-bar controls.
- Added a shared `Module` menu for closing and restoring Library, Playlist,
  Equalizer and Visualizer while keeping the Player permanently available.
- Redesigned the Player around branded artwork, track metadata, a mini spectrum,
  a central transport surface and dedicated volume and utility controls.
- Added mockup-style table headers, duration columns, row sizing and summary
  footers while retaining import, sorting, selection and drag-and-drop behavior.
- Reworked the equalizer visualization into ten illuminated gain lanes with an
  amber response curve while keeping frequency, gain, Q, enable and preset editing.
- Added a three-mode Visualizer launcher and retained all twelve realtime presets.
- Bundled the supplied logo for in-app artwork, package data and a multi-resolution
  Windows executable icon.

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
