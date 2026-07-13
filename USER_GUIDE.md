# Freak Media Player User Guide

## First start and local data

The optional first-start dialog selects a music folder, audio output and session
restore behavior. Installed mode stores data below
`%LOCALAPPDATA%\FreakMediaPlayer` on Windows or
`${XDG_DATA_HOME:-$HOME/.local/share}/freak-media-player` on Linux. Portable mode is selected by `portable.flag`
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

Settings lists system output devices and only the Mono, Stereo, 5.1 and 7.1 modes
reported as supported. Changing mode restarts near the previous position. Surround
mapping and downmix behavior are documented in README. Use the operating system's speaker tests
to verify physical channel wiring before multichannel playback.

## Equalizer, Visualizer, skins and layout

Choose an Equalizer **Genre** first and then a **Subgenre**. The catalog contains
more than 100 tonal starting points across 12 broad groups. Editing frequency,
gain, Q, enable or preamp switches the selection to Custom while preserving the
current curve. The Visualizer has Eco, Balanced and Smooth performance levels and
runs only during playback. Docks
are position-locked to prevent accidental dragging; they can still be detached with
the explicit `↗` button, hidden and restored from Module. Custom skins live in the
data folder's `skins` directory and can be reloaded from the title bar.

## Optional Internet Radio

Choose `Module > Internet Radio…` or press `Ctrl+Shift+R` to open the independent
radio window on demand. It never docks into or rearranges the main player layout.
Search and filters run without blocking the interface. Double-click a station to
play it through the main Player; this does not replace the local playlist.
Favorites, recent stations and manually added HTTP(S) stream URLs remain
available locally when the public station directory is offline. A zero-duration
stream is shown as `LIVE`, with seeking disabled.

Disable the complete optional module in Player Settings and restart to remove its
provider and Module action. Existing radio data is retained for a later re-enable.

Direct MP3/AAC streams and ordinary PLS/M3U forwarding playlists are supported;
HLS/M3U8 is passed to FFmpeg. When available, the station's live title appears in
the radio status and main Player. Song and artist are shown in addition to the
permanently visible station name. Interrupted connections retry at most three
times with increasing delays and can always be cancelled with Stop.

Choose Small, Normal or Stable buffering before connecting. Export/Import stores
favorites and own streams either as complete JSON or as an M3U8 list. Normal app
backup and restore also includes the separate radio database if it has been
created.

The last search and filters are restored when the radio window is reopened. The
detail area shows all available location, language, genre, codec, bitrate and
homepage information. Station logos are downloaded in the background into a
size- and age-limited cache that can be cleared from the same window.
Saving listening history and loading logos can each be switched off; disabling
logos prevents those image network requests entirely.

Separate multiple countries, regions or languages with commas. Multiple tags mean
that every listed tag is required. History entries can be removed one at a time.
Use Test stream before relying on a manually entered URL; the background test reads
only a small bounded prefix and reports whether the endpoint is reachable.

Opening the module contacts Radio Browser for directory searches and the selected
station for audio. The plugin uses no account, location access or telemetry and
does not record audio. Its separate database is stored below `data/plugins`.

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

See the complete shortcut table in README. Media Play/Pause, Stop,
Previous and Next are supported through Qt without global keyboard hooks.
