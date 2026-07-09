# Architecture

## Direction

Freak Media Player is built as a native desktop application with a UI-neutral core.
The core owns rules and contracts. Outer layers adapt those contracts to Qt, SQLite,
audio backends, providers and plugins.

## Dependency Rule

Dependencies point inward:

- `ui` depends on `services`
- `services` depends on `core`, `models` and ports
- `database`, `providers`, `player` and `plugins` implement or consume ports
- `core` and `models` do not import Qt, SQLite, provider implementations or plugins

## Packages

- `app`: application assembly and startup wiring
- `config`: versioned settings and migrations
- `core`: domain events, ports and pure playback concepts
- `database`: SQLite connection handling, migrations and repositories
- `models`: immutable domain dataclasses and enums
- `player`: playback controller, queue and audio backend abstractions
- `providers`: media provider contracts and implementations
- `plugins`: plugin manifests, lifecycle and extension points
- `services`: UI-neutral use cases
- `ui`: PySide6 windows, view models and themes
- `widgets`: reusable Qt widgets
- `utils`: small cross-cutting helpers

## Library And Playlist

The local library is the durable catalog of known tracks. It does not define
playback order. The active playlist is stored separately through a playlist
repository and owns the ordered sequence used by the playback controller.

Qt widgets exchange track identities through drag and drop, while playlist
mutation remains in `PlaylistService`. The player receives an ordered snapshot
through `PlaybackService`; neither the library widget nor the playlist widget
talks to the audio backend directly.

Library and playlist are presented simultaneously in a horizontal splitter so
drag and drop never depends on navigation state. The equalizer shares the same
workspace in a vertical splitter. `CollapsiblePanel` owns only presentation
state and does not introduce dependencies between the contained modules.

## First Milestone

The first milestone is a runnable shell with:

- stable package layout
- typed domain models
- provider contract
- plugin contract
- queue and playback controller skeleton
- settings migration pipeline
- SQLite migration runner
- basic PySide6 main window

Feature implementation starts only after these boundaries are in place.

## Audio Engine Direction

The current desktop playback backend uses Qt Multimedia for fast, native local
file playback. Qt `QMediaPlayer` does not expose a real equalizer/DSP pipeline,
so the equalizer introduced in `0.2.0` is deliberately modeled as a clean
service and backend contract first.

The next audio-engine milestone should replace or extend the Qt player backend
with a decoder plus audio sink pipeline. That is where ReplayGain, real
equalizer processing, crossfade, gapless playback and visualizer sample taps
belong. The UI should continue to talk only to services, never to the backend
implementation directly.
