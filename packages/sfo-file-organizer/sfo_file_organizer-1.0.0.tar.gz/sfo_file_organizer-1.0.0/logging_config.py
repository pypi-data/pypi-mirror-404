"""
Logging configuration for SFO File Organizer.

Provides structured logging with console and file output support.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Default log format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Valid log levels
VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = "organizer.log",
    console_output: bool = True
) -> logging.Logger:
    """
    Configure and return the application logger.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. Set to None to disable file logging.
        console_output: Whether to output logs to console.
    
    Returns:
        Configured logger instance.
    
    Raises:
        ValueError: If an invalid log level is provided.
    """
    level = level.upper()
    if level not in VALID_LEVELS:
        raise ValueError(f"Invalid log level: {level}. Must be one of {VALID_LEVELS}")
    
    # Get or create the logger
    logger = logging.getLogger("smart_file_organizer")
    logger.setLevel(getattr(logging, level))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(getattr(logging, level))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except PermissionError:
            if console_output:
                logger.warning(f"Could not create log file: {log_file} (permission denied)")
    
    return logger


def get_logger() -> logging.Logger:
    """
    Get the application logger.
    
    Returns:
        The smart_file_organizer logger instance.
    """
    return logging.getLogger("smart_file_organizer")
