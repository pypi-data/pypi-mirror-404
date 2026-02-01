"""
Logging configuration for AntiAI.

Provides structured logging with different levels and outputs.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Default format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"


def setup_logger(
    name: str = "antiai",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    detailed: bool = False,
) -> logging.Logger:
    """
    Configure and return a logger instance.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging
        detailed: If True, use detailed format with function names

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger("antiai.encoder", level=logging.DEBUG)
        >>> logger.info("Processing image")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Choose format
    fmt = DETAILED_FORMAT if detailed else DEFAULT_FORMAT
    formatter = logging.Formatter(fmt)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Module-level logger
logger = setup_logger()
