"""Logging configuration for service healthcheck."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_file: str = "./healthcheck.log",
    log_level: int = logging.INFO,
    console_level: int = logging.INFO
) -> logging.Logger:
    """Configure logging with file and console handlers.

    Args:
        log_file: Path to log file (default: ./healthcheck.log)
        log_level: Logging level for file handler
        console_level: Logging level for console handler

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("service_healthcheck")
    logger.setLevel(logging.DEBUG)  # Capture all levels, handlers will filter

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_formatter = logging.Formatter(
        fmt="%(levelname)s: %(message)s"
    )

    # File handler - detailed logging
    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # If file logging fails, log to stderr but continue
        print(f"Warning: Could not set up file logging: {e}", file=sys.stderr)

    # Console handler - INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger
