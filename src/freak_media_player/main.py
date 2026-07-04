"""Application entry point."""

from freak_media_player.app.application import run_application


def main() -> int:
    return run_application()


if __name__ == "__main__":
    raise SystemExit(main())
