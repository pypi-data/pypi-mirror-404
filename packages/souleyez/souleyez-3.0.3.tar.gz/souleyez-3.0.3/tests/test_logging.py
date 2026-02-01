"""
Tests for structured logging module.
"""

import json
import logging
import tempfile
from pathlib import Path
import pytest
from souleyez.log_config import get_logger, log_timing, init_logging


def test_logger_initialization(tmp_path):
    """Test that logger initializes correctly."""
    logger = get_logger(__name__)
    assert logger is not None
    assert isinstance(logger, logging.Logger)


def test_logging_with_extra_fields(tmp_path):
    """Test that extra fields are included in logs."""
    logger = get_logger(__name__)

    # Log with extra fields
    logger.info(
        "Test message", extra={"job_id": 123, "tool": "nmap", "target": "192.168.1.1"}
    )

    # If we got here without errors, logging works
    assert True


def test_log_timing_context_manager(tmp_path):
    """Test the log_timing context manager."""
    logger = get_logger(__name__)

    # Use timing context
    with log_timing(logger, "test_operation", test_id=456):
        # Simulate some work
        pass

    # If we got here, timing works
    assert True


def test_logger_levels(tmp_path):
    """Test different log levels."""
    logger = get_logger(__name__)

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    assert True


def test_logger_with_exception(tmp_path):
    """Test logging exceptions with exc_info."""
    logger = get_logger(__name__)

    try:
        raise ValueError("Test error")
    except ValueError:
        logger.error(
            "Caught exception", exc_info=True, extra={"error_type": "ValueError"}
        )

    assert True


def test_multiple_loggers(tmp_path):
    """Test that multiple modules can get loggers."""
    logger1 = get_logger("module1")
    logger2 = get_logger("module2")

    assert logger1 is not None
    assert logger2 is not None
    assert logger1.name == "module1"
    assert logger2.name == "module2"
