"""Structured logging configuration using structlog with JSON output."""

import logging
import sys
import structlog
from typing import Any

def setup_logging(log_level: str = "INFO") -> None:
    """Configure structlog to emit JSON-formatted logs to stdout.

    Sets up the standard library logging as a backend and configures
    structlog processors for timestamping, log levels, and JSON rendering.
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> Any:
    """Return a structlog logger bound to the given name."""
    return structlog.get_logger(name)
