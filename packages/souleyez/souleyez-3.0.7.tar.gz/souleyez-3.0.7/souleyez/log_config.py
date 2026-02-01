"""
Structured logging module for SoulEyez.
Provides JSON-formatted logs with rotation and configuration support.
"""

import json
import logging
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Try different import paths for python-json-logger (version compatibility)
try:
    # pythonjsonlogger 3.x / 4.x
    from pythonjsonlogger.json import JsonFormatter
except ImportError:
    try:
        # pythonjsonlogger 2.x
        from pythonjsonlogger import jsonlogger

        JsonFormatter = jsonlogger.JsonFormatter
    except ImportError:
        # Fallback: simple JSON formatter if python-json-logger not installed
        class JsonFormatter(logging.Formatter):
            """Simple JSON formatter fallback."""

            def format(self, record):
                log_obj = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "name": record.name,
                    "levelname": record.levelname,
                    "message": record.getMessage(),
                }
                if hasattr(record, "exc_info") and record.exc_info:
                    log_obj["exc_info"] = self.formatException(record.exc_info)
                # Include extra fields
                for key, value in record.__dict__.items():
                    if key not in (
                        "name",
                        "msg",
                        "args",
                        "created",
                        "filename",
                        "funcName",
                        "levelname",
                        "levelno",
                        "lineno",
                        "module",
                        "msecs",
                        "pathname",
                        "process",
                        "processName",
                        "relativeCreated",
                        "stack_info",
                        "thread",
                        "threadName",
                        "exc_info",
                        "exc_text",
                        "message",
                        "taskName",
                    ):
                        log_obj[key] = value
                return json.dumps(log_obj)


_initialized = False


def init_logging():
    """
    Initialize logging system from config.
    Should be called once at app startup.
    """
    global _initialized
    if _initialized:
        return

    # Prevent Python's logging.basicConfig from adding default handlers
    # This must happen BEFORE any logging occurs
    logging.root.handlers.clear()

    try:
        from souleyez import config

        # Get config values
        log_level = config.get("logging.level", "INFO")
        log_file = config.get("logging.file", "~/.souleyez/souleyez.log")
        log_format = config.get("logging.format", "json")
        max_bytes = config.get("logging.max_bytes", 10485760)  # 10MB
        backup_count = config.get("logging.backup_count", 5)

        # Expand path
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create root logger
        root_logger = logging.getLogger("souleyez")
        root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Remove existing handlers
        root_logger.handlers.clear()

        # File handler with rotation
        file_handler = RotatingFileHandler(
            log_path, maxBytes=max_bytes, backupCount=backup_count
        )

        # Set secure permissions on log file
        import os

        if log_path.exists():
            os.chmod(log_path, 0o600)

        # JSON formatter
        if log_format == "json":
            formatter = JsonFormatter(
                "%(timestamp)s %(name)s %(levelname)s %(message)s", timestamp=True
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Console handler for critical errors only (suppress INFO/WARNING/ERROR)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.CRITICAL)  # Only CRITICAL, not ERROR
        console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        root_logger.addHandler(console_handler)

        _initialized = True
        root_logger.info(
            "Logging initialized",
            extra={
                "log_file": str(log_path),
                "log_level": log_level,
                "log_format": log_format,
            },
        )

    except Exception as e:
        # Fallback to console logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stderr,
        )
        logging.warning(
            f"Failed to initialize file logging: {e}. Using console fallback."
        )
        _initialized = True


def get_logger(name):
    """
    Get a logger instance for a module.

    Args:
        name: Module name (use __name__)

    Returns:
        logging.Logger instance
    """
    if not _initialized:
        init_logging()

    return logging.getLogger(name)


@contextmanager
def log_timing(logger, operation, **extra_fields):
    """
    Context manager to automatically log operation duration.

    Usage:
        with log_timing(logger, "parse_nmap", job_id=job_id):
            # ... do work ...

    Args:
        logger: Logger instance
        operation: Operation name
        **extra_fields: Additional fields to include in log
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"{operation} completed",
            extra={
                "operation": operation,
                "duration_ms": round(duration_ms, 2),
                **extra_fields,
            },
        )
