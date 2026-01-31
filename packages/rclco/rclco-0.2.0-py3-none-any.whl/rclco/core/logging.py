"""Logging configuration for RCLCO library."""

import logging
import sys
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Create the library logger
logger = logging.getLogger("rclco")

# Default to WARNING to avoid noisy output unless explicitly configured
logger.setLevel(logging.WARNING)


def configure_logging(
    level: LogLevel = "INFO",
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream: bool = True,
) -> None:
    """Configure logging for the RCLCO library.

    Call this function to enable logging output from the library.
    By default, the library logs at WARNING level to stderr.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log message format string
        stream: If True, log to stderr; if False, only configure the level

    Example:
        from rclco.core.logging import configure_logging

        # Enable info-level logging
        configure_logging("INFO")

        # Enable debug logging for troubleshooting
        configure_logging("DEBUG")
    """
    logger.setLevel(getattr(logging, level))

    if stream and not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(format))
        logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get a child logger for a specific module.

    Args:
        name: Name of the module (will be prefixed with 'rclco.')

    Returns:
        Logger instance for the module

    Example:
        from rclco.core.logging import get_logger

        logger = get_logger("connectors.database")
        logger.debug("Connecting to database...")
    """
    return logging.getLogger(f"rclco.{name}")
