"""Structured logging configuration using structlog."""

import logging
import sys

import orjson
import structlog
from structlog.types import Processor

from identity_plan_kit.config import Environment


def _orjson_dumps(obj: object, **_kwargs: object) -> str:
    """Serialize to JSON using orjson for better performance."""
    return orjson.dumps(obj, option=orjson.OPT_UTC_Z).decode("utf-8")


def _get_shared_processors() -> list[Processor]:
    """Get processors shared between dev and prod configurations."""
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]


def configure_logging(
    environment: Environment = Environment.DEVELOPMENT,
    log_level: str = "INFO",
) -> None:
    """
    Configure structlog for the application.

    In development: Pretty, colorful console output
    In production: JSON output for log aggregation

    Args:
        environment: The application environment
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Example:
        >>> from identity_plan_kit.config import Environment
        >>> configure_logging(Environment.PRODUCTION, "INFO")
    """
    shared_processors = _get_shared_processors()

    if environment == Environment.DEVELOPMENT:
        # Development: Pretty console output with colors
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.dev.ConsoleRenderer(
                colors=sys.stderr.isatty(),
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]
    else:
        # Production: JSON output for log aggregation
        processors = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(serializer=_orjson_dumps),
        ]

    # Configure structlog
    # Note: cache_logger_on_first_use=False ensures that loggers created before
    # configure_logging() is called will pick up the correct log level.
    # This fixes the issue where module-level loggers bypass level filtering.
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )

    # Also configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structlog logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        A bound structlog logger

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("user_authenticated", user_id="123", provider="google")
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: object) -> None:
    """
    Bind context variables to all subsequent log calls in this context.

    Useful for adding request_id, user_id, etc. to all logs in a request.

    Args:
        **kwargs: Key-value pairs to bind

    Example:
        >>> bind_context(request_id="abc-123", user_id="user-456")
        >>> logger.info("processing_request")  # Will include request_id and user_id
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()
