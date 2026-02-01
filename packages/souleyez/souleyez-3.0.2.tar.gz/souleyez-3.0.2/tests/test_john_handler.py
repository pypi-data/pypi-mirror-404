#!/usr/bin/env python3
"""
Tests for the JohnHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS
from souleyez.handlers.john_handler import JohnHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return JohnHandler()


@pytest.fixture
def mock_managers():
    """Mock database managers."""
    host_manager = MagicMock()
    findings_manager = MagicMock()
    credentials_manager = MagicMock()

    return {
        "host_manager": host_manager,
        "findings_manager": findings_manager,
        "credentials_manager": credentials_manager,
    }


class TestHandlerMetadata:
    """Test handler metadata."""

    def test_tool_name(self, handler):
        """Handler should have correct tool name."""
        assert handler.tool_name == "john"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "John the Ripper"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful john parsing."""

    def test_cracked_passwords_detected(self, handler, mock_managers):
        """Cracked passwords should be detected."""
        parsed_data = {
            "cracked": [
                {"username": "admin", "password": "Password123"},
                {"username": "user1", "password": "test1234"},
            ],
            "total_loaded": 5,
            "total_cracked": 2,
            "session_status": "completed",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("admin:Password123\nuser1:test1234\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.john_parser.parse_john_output",
                return_value=parsed_data,
            ):
                job = {"metadata": {"hash_file": "/tmp/hashes.txt"}}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_DONE
                assert result["cracked_count"] == 2
                assert result["credentials_added"] == 2
        finally:
            os.unlink(log_path)

    def test_credentials_stored_in_database(self, handler, mock_managers):
        """Credentials should be stored in database."""
        parsed_data = {
            "cracked": [{"username": "admin", "password": "Pass123!"}],
            "total_loaded": 1,
            "session_status": "completed",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("admin:Pass123!")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.john_parser.parse_john_output",
                return_value=parsed_data,
            ):
                job = {}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["credentials_added"] == 1
                mock_managers["credentials_manager"].add_credential.assert_called_once()
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_cracked_returns_no_results(self, handler, mock_managers):
        """No cracked passwords should return no_results status."""
        parsed_data = {"cracked": [], "total_loaded": 5, "session_status": "completed"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Session completed, no passwords cracked")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.john_parser.parse_john_output",
                return_value=parsed_data,
            ):
                job = {}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_NO_RESULTS
        finally:
            os.unlink(log_path)


class TestDisplayMethods:
    """Test display method existence and basic functionality."""

    def test_display_done_exists(self, handler):
        """display_done method should exist."""
        assert hasattr(handler, "display_done")

    def test_display_warning_exists(self, handler):
        """display_warning method should exist."""
        assert hasattr(handler, "display_warning")

    def test_display_error_exists(self, handler):
        """display_error method should exist."""
        assert hasattr(handler, "display_error")

    def test_display_no_results_exists(self, handler):
        """display_no_results method should exist."""
        assert hasattr(handler, "display_no_results")

    def test_display_no_results_shows_tips(self, handler, capsys):
        """display_no_results should show helpful tips."""
        job = {}
        handler.display_no_results(job, "/fake/path")
        captured = capsys.readouterr()
        assert "No passwords cracked" in captured.out
        assert "Suggestions" in captured.out

    def test_display_error_shows_no_hashes_loaded(self, handler, capsys):
        """display_error should identify no hashes loaded errors."""
        log_content = "No password hashes loaded"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "No password hashes loaded" in captured.out
        finally:
            os.unlink(log_path)

    def test_display_error_shows_unknown_format(self, handler, capsys):
        """display_error should identify unknown format errors."""
        log_content = "Unknown ciphertext format"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "Unknown hash format" in captured.out
        finally:
            os.unlink(log_path)

    def test_display_done_shows_cracked(self, handler, capsys):
        """display_done should show cracked passwords."""
        parsed_data = {
            "cracked": [{"username": "admin", "password": "Pass123!"}],
            "total_loaded": 5,
            "total_cracked": 1,
            "session_status": "completed",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("john results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.john_parser.parse_john_output",
                return_value=parsed_data,
            ):
                job = {}
                handler.display_done(job, log_path)
                captured = capsys.readouterr()
                assert "JOHN THE RIPPER RESULTS" in captured.out
                assert "Cracked Passwords" in captured.out
                assert "admin" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import john_handler  # noqa: F401

        handler = registry.get_handler("john")
        assert handler is not None
        assert handler.tool_name == "john"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import john_handler  # noqa: F401

        assert registry.has_warning_handler("john") is True
        assert registry.has_error_handler("john") is True
        assert registry.has_no_results_handler("john") is True
        assert registry.has_done_handler("john") is True
