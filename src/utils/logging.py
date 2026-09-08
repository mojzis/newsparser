import logging
import sys
from functools import cache

from src.config.settings import get_settings


class _NspStreamHandler(logging.StreamHandler):
    """StreamHandler tagged so setup_logging can recognize its own handler."""

    _nsp_handler = True


@cache
def get_logger(name: str, level: str | None = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Optional override for log level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Resolve level from settings or the provided override
    if level is None:
        try:
            level = get_settings().log_level
        except Exception:
            level = "INFO"

    # Unknown level names fall back to INFO
    resolved_level = getattr(logging, level.upper(), logging.INFO)

    # Always apply the level (foreign handlers, e.g. pytest's log capture, must
    # not prevent reconfiguration)
    logger.setLevel(resolved_level)

    # Add our console handler once. Identify it by a marker so third-party
    # handlers don't fool the idempotency check.
    own_handlers = [h for h in logger.handlers if getattr(h, "_nsp_handler", False)]
    if not own_handlers:
        handler = _NspStreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.propagate = False
        own_handlers = [handler]

    for handler in own_handlers:
        handler.setLevel(resolved_level)

    return logger


def setup_logging(level: str | None = None) -> None:
    """
    Configure logging for the entire application.

    Args:
        level: Optional override for log level
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)  # Set root to WARNING to reduce noise

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler to root
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Configure specific loggers to reduce noise
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
