"""Structured logging configuration for runner"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from decimal import Decimal

import sentry_sdk
import structlog
from structlog.stdlib import LOG_KWARG_NAMES
from structlog.typing import EventDict


def record_metric_distribution(
    metric_name: str, value: float, unit: str | None = None
) -> None:
    """Record a distribution metric in Sentry."""
    try:
        sentry_sdk.metrics.distribution(metric_name, value=value, unit=unit)
    except Exception:
        # Silently fail - don't break the application if metrics fail
        pass


def record_metric_counter(
    metric_name: str, value: int = 1, tags: dict[str, str] | None = None
) -> None:
    """Record a counter metric in Sentry."""
    try:
        sentry_sdk.metrics.count(metric_name, value=value)
    except Exception:
        # Silently fail - don't break the application if metrics fail
        pass


def record_metric_gauge(metric_name: str, value: float) -> None:
    """Record a gauge metric in Sentry."""
    try:
        sentry_sdk.metrics.gauge(metric_name, value=value)
    except Exception:
        # Silently fail - don't break the application if metrics fail
        pass


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles non-serializable types."""

    def default(self, o):
        """Convert non-JSON-serializable objects to strings."""
        if isinstance(o, (Decimal, uuid.UUID)):
            return str(o)
        # Handle Mock objects from unittest.mock
        if hasattr(o, "_mock_name"):
            return str(o)
        return super().default(o)


class RenderToLog:
    """Structlog processor that renders event dict to log format."""

    def __init__(self, is_simple: bool = False) -> None:
        """
        Initialize the processor.

        Args:
            is_simple: If True, omit custom fields from log output
        """
        self.is_simple = is_simple

    def __call__(self, _: logging.Logger, __: str, event_dict: EventDict) -> EventDict:
        """Process and render the event dict."""
        custom_fields = {
            k: v
            for k, v in event_dict.items()
            if k not in ("level", "timestamp", "event")
        }
        msg = json.dumps(event_dict, cls=JSONEncoder)
        if custom_fields and not self.is_simple:
            msg = (
                event_dict.get("event")
                + " "
                + json.dumps(custom_fields, cls=JSONEncoder)
            )
        new_event_dict = {
            "msg": msg,
            "extra": custom_fields,
            **{kw: event_dict.pop(kw) for kw in LOG_KWARG_NAMES if kw in event_dict},
        }

        return new_event_dict


custom_formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

simple_formatter = logging.Formatter(fmt="%(message)s")


def configure_logging(is_simple: bool = False, log_level: str = "INFO") -> None:
    """
    Configure structured JSON logging with context support

    Can be called multiple times (e.g., to change log level).

    Sets up:
    - JSON formatting for all logs
    - Context variables support (test_id, workspace_id, etc.)
    - Disabled external library logs

    Args:
        is_simple: If True, omit custom fields from log output
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    if is_simple:
        formatter = simple_formatter
    else:
        formatter = custom_formatter

    # Disable logs from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aioboto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("stripe").setLevel(logging.WARNING)

    # Apply formatter to all existing handlers (including uvicorn's)
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", ""]:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers:
            handler.setFormatter(formatter)

    # Configure structlog
    structlog.configure(
        processors=[
            # Add log level
            structlog.stdlib.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.contextvars.merge_contextvars,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            RenderToLog(is_simple=is_simple),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Create handler with formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logging.basicConfig(handlers=[handler], level=getattr(logging, log_level.upper()))


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get configured structlog logger

    Note: If configure_logging() hasn't been called yet, this will return
    a logger with default structlog configuration. Call configure_logging()
    early in your application startup.
    """
    return structlog.get_logger(name)
