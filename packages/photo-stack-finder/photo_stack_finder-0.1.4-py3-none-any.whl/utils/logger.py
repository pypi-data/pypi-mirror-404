"""Logging module for photo_dedup project.

Provides centralized logging configuration that reads from CONFIG.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from .config import CONFIG

# Type for logger parameters - always non-None since get_logger() always returns a valid logger
LOGGER_T = logging.Logger

# Internal module-level logger singleton - initialized lazily by get_logger()
_logger: logging.Logger | None = None


def get_logger() -> logging.Logger:
    """Get or create the global logger instance.

    The logger is configured based on CONFIG.processing.LOG_LEVEL.
    In DEBUG mode, more detailed progress information is logged.
    In parallel mode, only batch completions and stage completions are logged.

    Returns:
            Configured logger instance
    """
    global _logger  # noqa: PLW0603
    # Library configuration pattern - global state for logger

    if _logger is None:
        _logger = logging.getLogger("photo_dedup")
        _logger.setLevel(getattr(logging, CONFIG.processing.LOG_LEVEL))

        # Console handler with formatting
        handler: logging.StreamHandler[Any] = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, CONFIG.processing.LOG_LEVEL))

        # Format: [INFO] Message
        formatter: logging.Formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)

        _logger.addHandler(handler)
        _logger.propagate = False
    else:
        # Update log level if CONFIG changed
        log_level: int = getattr(logging, CONFIG.processing.LOG_LEVEL)
        _logger.setLevel(log_level)
        for h in _logger.handlers:
            h.setLevel(log_level)

    assert _logger is not None, "Logger initialization failed"
    return _logger
