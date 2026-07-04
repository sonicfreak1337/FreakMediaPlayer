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
