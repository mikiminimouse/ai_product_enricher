"""Structured logging configuration using structlog."""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from .config import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    # Determine log level
    log_level = getattr(logging, settings.log_level, logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Shared processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    # Environment-specific processors
    if settings.is_development or settings.app_debug:
        # Development: colored console output
        processors: list[Processor] = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # Production: JSON output
        processors = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None, **initial_context: Any) -> structlog.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Optional logger name (module name recommended)
        **initial_context: Initial context values to bind to the logger

    Returns:
        Configured structlog BoundLogger instance
    """
    logger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger


class RequestContextLogger:
    """Logger with request context management."""

    def __init__(self, logger: structlog.BoundLogger) -> None:
        self._logger = logger

    def bind(self, **context: Any) -> "RequestContextLogger":
        """Bind additional context to the logger."""
        return RequestContextLogger(self._logger.bind(**context))

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info level message."""
        self._logger.info(message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug level message."""
        self._logger.debug(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning level message."""
        self._logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error level message."""
        self._logger.error(message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        self._logger.exception(message, **kwargs)
