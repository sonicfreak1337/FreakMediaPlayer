# Freak Media Player User Guide

## First start and local data

The optional first-start dialog selects a music folder, audio output and session
restore behavior. Installed mode stores data below
`%LOCALAPPDATA%\FreakMediaPlayer`. Portable mode is selected by `portable.flag`
beside the executable and stores everything below its local `data` directory.

## Library and import

Use the file and folder controls in Library, or drag supported audio files into
the window. Managed folders can be rescanned or removed as sources without
deleting audio. Untagged `Artist - Title.ext` files receive an automatic artist
and title fallback. Search, filters, grouping and smart Favorites/Recent views can
be combined. Rare edit, relocation, cover and deletion actions are under `…`.

## Playlists and playback

Add selected library tracks with the arrow control or double-click. Named
playlists can be created, duplicated, renamed, imported from M3U/M3U8 and exported.
Delete removes selected playlist rows, not files. Transport supports seek, volume,
mute, Shuffle and Repeat. Unreadable titles are skipped with a bounded retry path.

## Audio output

Settings lists Windows output devices and only the Mono, Stereo, 5.1 and 7.1 modes
reported as supported. Changing mode restarts near the previous position. Surround
mapping and downmix behavior are documented in README. Use Windows speaker tests
to verify physical channel wiring before multichannel playback.

## Equalizer, Visualizer, skins and layout

The Equalizer provides presets and editable parametric bands. The Visualizer has
Eco, Balanced and Smooth performance levels and runs only during playback. Docks
can be moved, detached, hidden and restored from Module. Custom skins live in the
data folder's `skins` directory and can be reloaded from the title bar.

## Settings, backup and maintenance

Settings controls audio, session behavior, layout and Visualizer quality. Backup
exports the complete local SQLite data to `.freakbackup`; restore validates the
package and creates a safety backup first. Maintenance can reset layout, rebuild
metadata or reset settings without deleting library and playlist data.

## Diagnostics

Diagnostics shows version, database schema, paths, audio output and sanitized
recent errors. `Open log folder` opens rotating runtime logs. About lists runtime
versions and license families. See `KNOWN_ISSUES.md` before reporting a problem.

## Keyboard shortcuts

See the complete shortcut table in README. Windows media Play/Pause, Stop,
Previous and Next are supported through Qt without global keyboard hooks.

