import logging
import sys
from functools import cache


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

    # Only configure if logger has no handlers (avoid duplicate configuration)
    if not logger.handlers:
        # Get level from settings or use provided level
        if level is None:
            try:
                from src.config.settings import get_settings

                settings = get_settings()
                level = settings.log_level
            except Exception:
                level = "INFO"

        # Configure logger
        logger.setLevel(getattr(logging, level.upper()))

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper()))

        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

        # Prevent propagation to root logger
        logger.propagate = False

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
