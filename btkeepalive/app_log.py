"""Application logging (rotating files under the config directory)."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

from btkeepalive.config import config_dir

_CONFIGURED = False
_LOGGER: logging.Logger | None = None


def _level_from_env() -> int:
    name = os.environ.get("BTKEEPALIVE_LOG_LEVEL", "INFO").upper()
    return getattr(logging, name, logging.INFO)


def get_logger() -> logging.Logger:
    global _CONFIGURED, _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger("btkeepalive")
    logger.setLevel(_level_from_env())
    if not _CONFIGURED:
        log_dir = config_dir()
        log_dir.mkdir(parents=True, exist_ok=True)

        fmt = logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        app_handler = RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=512_000,
            backupCount=3,
            encoding="utf-8",
        )
        app_handler.setFormatter(fmt)
        logger.addHandler(app_handler)

        audio_handler = RotatingFileHandler(
            log_dir / "audio-errors.log",
            maxBytes=512_000,
            backupCount=3,
            encoding="utf-8",
        )
        audio_handler.setFormatter(fmt)
        audio_handler.setLevel(logging.WARNING)
        logger.addHandler(audio_handler)

        _CONFIGURED = True
    _LOGGER = logger
    return logger


def log_audio_error(message: str) -> None:
    get_logger().warning("audio: %s", message)


def log_info(message: str, *args: object) -> None:
    get_logger().info(message, *args)


def log_error(message: str, *args: object) -> None:
    get_logger().error(message, *args)
