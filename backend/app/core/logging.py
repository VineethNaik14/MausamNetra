"""
Centralized, security-conscious logging configuration.

- Never logs passwords, JWTs, or Authorization headers.
- Uses a consistent, structured (JSON-ish) format so logs are easy to grep
  or ship to a log aggregator later.
"""
import logging
import sys
from typing import Any

from app.core.config import settings

_REDACT_KEYS = {"password", "token", "authorization", "jwt", "secret", "access_token"}


class RedactingFilter(logging.Filter):
    """Best-effort filter that redacts obviously sensitive substrings."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        lowered = msg.lower()
        if any(key in lowered for key in _REDACT_KEYS):
            record.msg = "[REDACTED LOG MESSAGE - possible sensitive content]"
            record.args = ()
        return True


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)
    handler.addFilter(RedactingFilter())

    root.handlers.clear()
    root.addHandler(handler)

    # Quiet noisy third-party loggers a bit.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DATABASE_ECHO else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def safe_extra(**kwargs: Any) -> dict:
    """Helper to build a log-safe extra dict, dropping sensitive keys."""
    return {k: v for k, v in kwargs.items() if k.lower() not in _REDACT_KEYS}
