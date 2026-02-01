"""Centralized logging configuration for cwms.

This module provides structured logging with:
- Environment variable configuration (CWMS_LOG_LEVEL)
- Consistent formatting across all modules
- File and console handlers
- JSON formatting option for structured logging
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Default log level
DEFAULT_LOG_LEVEL = "WARNING"

# Environment variable for log level
LOG_LEVEL_ENV_VAR = "CWMS_LOG_LEVEL"

# Log file location (optional)
LOG_FILE_ENV_VAR = "CWMS_LOG_FILE"

# JSON logging flag
JSON_LOG_ENV_VAR = "CWMS_LOG_JSON"


class StructuredFormatter(logging.Formatter):
    """Formatter that produces structured log output.

    Includes timestamp, level, module, and message with optional extra fields.
    """

    def __init__(self, include_timestamp: bool = True, include_module: bool = True) -> None:
        """Initialize the formatter.

        Args:
            include_timestamp: Whether to include timestamp in output
            include_module: Whether to include module name in output
        """
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_module = include_module

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record.

        Args:
            record: The log record to format

        Returns:
            Formatted log string
        """
        parts = []

        if self.include_timestamp:
            timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            parts.append(f"[{timestamp}]")

        parts.append(f"[{record.levelname}]")

        if self.include_module:
            parts.append(f"[{record.name}]")

        parts.append(record.getMessage())

        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            parts.append(f"\n{self.formatException(record.exc_info)}")

        return " ".join(parts)


class JSONFormatter(logging.Formatter):
    """Formatter that produces JSON log output.

    Useful for log aggregation systems and structured analysis.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        for key, value in record.__dict__.items():
            if key.startswith("ctx_"):
                # Strip 'ctx_' prefix for cleaner output
                log_data[key[4:]] = value

        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)


def get_log_level() -> int:
    """Get the configured log level from environment.

    Reads from CWMS_LOG_LEVEL environment variable.
    Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL

    Returns:
        Logging level constant (e.g., logging.DEBUG)
    """
    level_str = os.environ.get(LOG_LEVEL_ENV_VAR, DEFAULT_LOG_LEVEL).upper()

    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    return level_map.get(level_str, logging.WARNING)


def setup_logging(
    level: int | None = None,
    log_file: str | Path | None = None,
    json_format: bool | None = None,
) -> None:
    """Configure logging for cwms.

    Call this early in application startup to configure logging.
    If not called, modules will use default Python logging behavior.

    Args:
        level: Log level (default: from environment or WARNING)
        log_file: Optional file to write logs to (default: from environment)
        json_format: Whether to use JSON formatting (default: from environment)
    """
    # Determine log level
    if level is None:
        level = get_log_level()

    # Determine log file
    if log_file is None:
        log_file_env = os.environ.get(LOG_FILE_ENV_VAR)
        if log_file_env:
            log_file = Path(log_file_env)

    # Determine JSON format
    if json_format is None:
        json_format = os.environ.get(JSON_LOG_ENV_VAR, "").lower() in ("1", "true", "yes")

    # Get the cwms logger
    logger = logging.getLogger("cwms")
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    if json_format:
        formatter: logging.Formatter = JSONFormatter()
    else:
        formatter = StructuredFormatter()

    # Console handler (stderr to avoid mixing with JSON output)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Don't propagate to root logger
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module.

    This is the recommended way to get a logger in cwms modules.
    It ensures consistent naming under the cwms namespace.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Processing started")
    """
    # Ensure the name is under cwms namespace
    if not name.startswith("cwms"):
        name = f"cwms.{name}"

    return logging.getLogger(name)


class LogContext:
    """Context manager for adding extra fields to log records.

    Useful for adding request-specific or operation-specific context
    to all log messages within a block.

    Example:
        with LogContext(project="my-project", operation="swap"):
            logger.info("Starting swap")  # Includes project and operation
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with context fields.

        Args:
            **kwargs: Key-value pairs to add to log records.
                      Keys will be prefixed with 'ctx_' internally.
        """
        self.context = {f"ctx_{k}": v for k, v in kwargs.items()}
        self._old_factory: Any = None

    def __enter__(self) -> LogContext:
        """Enter the context, installing the custom record factory."""
        self._old_factory = logging.getLogRecordFactory()

        context = self.context  # Capture for closure

        def record_factory(
            name: str,
            level: int,
            fn: str,
            lno: int,
            msg: object,
            args: tuple[Any, ...],
            exc_info: Any,
            func: str | None = None,
            sinfo: str | None = None,
        ) -> logging.LogRecord:
            record = logging.LogRecord(name, level, fn, lno, msg, args, exc_info, func, sinfo)
            for key, value in context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit the context, restoring the original record factory."""
        if self._old_factory is not None:
            logging.setLogRecordFactory(self._old_factory)


def log_with_timing(
    logger: logging.Logger,
    level: int,
    message: str,
    start_time: float,
    end_time: float,
    **kwargs: Any,
) -> None:
    """Log a message with timing information.

    This is a convenience function for logging operations with duration.

    Args:
        logger: Logger instance
        level: Log level (e.g., logging.INFO)
        message: Log message
        start_time: Operation start time (from time.time() or time.perf_counter())
        end_time: Operation end time
        **kwargs: Additional fields to include in the log record
    """
    duration_ms = (end_time - start_time) * 1000
    full_message = f"{message} (took {duration_ms:.2f}ms)"

    # Add timing info as extra fields for JSON logging
    extra = {f"ctx_{k}": v for k, v in kwargs.items()}
    extra["ctx_duration_ms"] = duration_ms

    logger.log(level, full_message, extra=extra)
