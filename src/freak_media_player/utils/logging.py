"""Logging setup."""

from __future__ import annotations

import logging
from collections import deque
from logging.handlers import RotatingFileHandler
from pathlib import Path

DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
LOG_FILE_NAME = "freak-media-player.log"
_RECENT_ERRORS: deque[str] = deque(maxlen=20)


class _RecentErrorHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR:
            _RECENT_ERRORS.append(self.format(record))


def configure_logging(level: int = logging.INFO, logs_dir: Path | None = None) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    if not any(isinstance(handler, _RecentErrorHandler) for handler in root.handlers):
        recent = _RecentErrorHandler()
        recent.setFormatter(formatter)
        root.addHandler(recent)
    if not root.handlers or all(isinstance(item, _RecentErrorHandler) for item in root.handlers):
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        root.addHandler(console)
    if logs_dir is not None:
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = (logs_dir / LOG_FILE_NAME).resolve()
        existing = {
            Path(handler.baseFilename).resolve()
            for handler in root.handlers
            if isinstance(handler, RotatingFileHandler)
        }
        if log_path not in existing:
            rotating = RotatingFileHandler(
                log_path,
                maxBytes=1_000_000,
                backupCount=3,
                encoding="utf-8",
            )
            rotating.setFormatter(formatter)
            root.addHandler(rotating)


def recent_errors() -> tuple[str, ...]:
    return tuple(_RECENT_ERRORS)
