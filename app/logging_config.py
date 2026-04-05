"""Structured logging setup."""

from __future__ import annotations

import logging
import sys

from app.config import settings


def setup_logging() -> None:
    """Configure root logger with a clean format."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    # Quiet noisy libraries
    for name in ("httpx", "httpcore", "asyncio", "sqlalchemy.engine"):
        logging.getLogger(name).setLevel(logging.WARNING)
