#!/bin/sh
set -eu

APP_NAME="freak-media-player"
SOURCE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MODE="system"

if [ "${1:-}" = "--user" ]; then
    MODE="user"
elif [ -n "${1:-}" ]; then
    echo "Usage: ./install.sh [--user]" >&2
    exit 2
fi

if [ ! -x "$SOURCE_DIR/FreakMediaPlayer/FreakMediaPlayer" ]; then
    echo "FreakMediaPlayer executable not found next to install.sh." >&2
    exit 1
fi

if [ "$MODE" = "user" ]; then
    PREFIX="${XDG_DATA_HOME:-$HOME/.local/share}"
    APP_DIR="$HOME/.local/opt/$APP_NAME"
    BIN_DIR="$HOME/.local/bin"
    DESKTOP_DIR="$PREFIX/applications"
    ICON_DIR="$PREFIX/icons/hicolor/256x256/apps"
    RUN=""
else
    APP_DIR="/opt/$APP_NAME"
    BIN_DIR="/usr/local/bin"
    DESKTOP_DIR="/usr/local/share/applications"
    ICON_DIR="/usr/local/share/icons/hicolor/256x256/apps"
    if [ "$(id -u)" -eq 0 ]; then
        RUN=""
    elif command -v sudo >/dev/null 2>&1; then
        RUN="sudo"
    else
        echo "System installation requires root or sudo. Use ./install.sh --user instead." >&2
        exit 1
    fi
fi

$RUN mkdir -p "$APP_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$ICON_DIR"
$RUN cp -R "$SOURCE_DIR/FreakMediaPlayer/." "$APP_DIR/"
$RUN install -m 0755 "$SOURCE_DIR/freak-media-player" "$BIN_DIR/freak-media-player"
$RUN install -m 0644 "$SOURCE_DIR/freak-media-player.desktop" "$DESKTOP_DIR/freak-media-player.desktop"
$RUN install -m 0644 "$SOURCE_DIR/freak-media-player.png" "$ICON_DIR/freak-media-player.png"

if command -v update-desktop-database >/dev/null 2>&1; then
    $RUN update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    $RUN gtk-update-icon-cache -q -t "$(dirname "$(dirname "$ICON_DIR")")" >/dev/null 2>&1 || true
fi

echo "Freak Media Player 1.1 installed ($MODE). Run: freak-media-player"
if [ "$MODE" = "user" ]; then
    case ":$PATH:" in
        *":$HOME/.local/bin:"*) ;;
        *) echo "Add $HOME/.local/bin to PATH if the command is not found." ;;
    esac
fi
