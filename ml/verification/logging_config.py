"""Structured logging setup.

Design rules (see project security requirements):
    * Never log secrets, API keys, or raw uploaded image bytes.
    * Log report IDs, not full report payloads (which may contain
      user-submitted free text / PII in edge cases).
    * One shared configuration function so every module logs consistently.
"""
from __future__ import annotations

import logging
import sys

from .config import get_settings

_CONFIGURED = False


def configure_logging() -> None:
    """Idempotently configure root logging for the verification module."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger("mausamnetra.verification")
    root.setLevel(settings.log_level.upper())
    root.handlers.clear()
    root.addHandler(handler)
    root.propagate = False

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger under the verification module's root."""
    configure_logging()
    return logging.getLogger(f"mausamnetra.verification.{name}")
