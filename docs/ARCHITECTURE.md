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

`LocalMetadataReader` is the provider-side adapter for embedded audio tags. The
provider maps extracted values into immutable media models, while SQLite
repositories persist those models without exposing tag-library details. A
versioned startup index refresh upgrades existing local rows exactly once.

## Playback Policies

`PlaybackQueue` owns playlist position and delegates randomized traversal to
`ShuffleCycle`. The cycle tracks played and remaining positions, avoids repeats
until every current playlist entry has played, and keeps navigation history for
previous/next. Disabling shuffle destroys that transient state.

`PlaybackController` owns end-of-track policy. Repeat One restarts the current
track, Repeat All wraps ordered playback, and shuffle starts a fresh randomized
cycle after exhausting the previous one. Qt controls only issue service
commands and render the resulting immutable `PlaybackState`.

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

The desktop backend introduced in `0.4.0` is a streaming pipeline:

1. PyAV/FFmpeg decodes local media into normalized stereo float blocks.
2. Stateful DSP processors transform those blocks without loading entire files.
3. A bounded queue separates decoding and DSP work from the Qt event loop.
4. Qt `QAudioSink` writes interleaved 48 kHz, 16-bit PCM to the native device.

The parametric equalizer uses cascaded second-order sections and preserves filter
state across blocks. Its coefficients follow the W3C/RBJ Audio EQ Cookbook. The
response graph obtains its values through `EqualizerService` and therefore uses
the same coefficient calculation as the processor.

`DawAudioBackend` remains behind the existing `AudioBackend` protocol. Playback,
playlist, provider and UI layers do not know which decoder or output device is
used. The former `QtAudioBackend` remains available as an import fallback.

The visualizer sample tap observes the final PCM bytes accepted by the native
output device and stores only a bounded rolling mono window. Plugins consume
snapshots without holding up the output pump. Crossfade, gapless scheduling and
ReplayGain remain future processors or scheduling policies in this pipeline.
