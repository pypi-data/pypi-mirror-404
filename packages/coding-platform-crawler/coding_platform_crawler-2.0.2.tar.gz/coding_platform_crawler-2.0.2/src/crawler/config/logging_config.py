"""
Logging configuration for the crawler application.

This module provides structured logging with JSON formatting for production
and human-readable formatting for development. It supports both console and
file handlers with appropriate log levels.
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Formats log records as JSON objects with consistent structure:
    - timestamp: ISO 8601 formatted timestamp
    - level: Log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - logger: Logger name
    - message: Log message
    - module: Module name where log was generated
    - function: Function name where log was generated
    - line: Line number where log was generated
    - exception: Exception information if present
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as a JSON string.

        Args:
            record: The log record to format

        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable formatter for console output.

    Provides colored output with clear formatting for development and debugging.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record with colors and human-readable structure.

        Args:
            record: The log record to format

        Returns:
            Formatted log string with colors
        """
        # Get color for log level
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Build log message
        log_parts = [
            f"{color}[{record.levelname}]{reset}",
            f"{timestamp}",
            f"{record.name}",
            f"{record.getMessage()}",
        ]

        # Add location info for DEBUG level
        if record.levelno == logging.DEBUG:
            log_parts.append(f"({record.module}.{record.funcName}:{record.lineno})")

        log_message = " - ".join(log_parts)

        # Add exception information if present
        if record.exc_info:
            log_message += "\n" + self.formatException(record.exc_info)

        return log_message


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = False,
    console_output: bool = True,
) -> logging.Logger:
    """
    Configure logging for the crawler application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If provided, logs will be written to file
        json_format: If True, use JSON formatting. If False, use human-readable format
        console_output: If True, output logs to console

    Returns:
        Configured root logger

    Example:
        >>> logger = setup_logging(level="DEBUG", log_file=Path("crawler.log"))
        >>> logger.info("Starting crawler")
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Choose formatter based on json_format flag
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = ConsoleFormatter()

    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler if log_file is provided
    if log_file:
        # Create log directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Use rotating file handler to prevent log files from growing too large
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, level.upper()))

        # Always use JSON format for file logs
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing problem", extra={"extra_fields": {"problem_id": "two-sum"}})
    """
    return logging.getLogger(name)


# Default configuration for development
def configure_default_logging() -> logging.Logger:
    """
    Configure logging with sensible defaults for development.

    - Level: INFO
    - Console output: Enabled with human-readable format
    - File output: Disabled

    Returns:
        Configured root logger
    """
    return setup_logging(
        level="INFO",
        log_file=None,
        json_format=False,
        console_output=True,
    )


# Default configuration for production
def configure_production_logging(log_dir: Path) -> logging.Logger:
    """
    Configure logging for production environment.

    - Level: INFO
    - Console output: Enabled with JSON format
    - File output: Enabled with JSON format and rotation

    Args:
        log_dir: Directory where log files should be stored

    Returns:
        Configured root logger
    """
    log_file = log_dir / f"crawler_{datetime.now().strftime('%Y%m%d')}.log"

    return setup_logging(
        level="INFO",
        log_file=log_file,
        json_format=True,
        console_output=True,
    )


# Log level constants for easy reference
DEBUG = "DEBUG"
INFO = "INFO"
WARNING = "WARNING"
ERROR = "ERROR"
CRITICAL = "CRITICAL"
