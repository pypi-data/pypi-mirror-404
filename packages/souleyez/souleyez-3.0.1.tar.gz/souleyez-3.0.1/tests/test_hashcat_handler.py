#!/usr/bin/env python3
"""
Tests for the HashcatHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS
from souleyez.handlers.hashcat_handler import HashcatHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return HashcatHandler()


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
        assert handler.tool_name == "hashcat"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "Hashcat"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful hashcat parsing."""

    def test_cracked_hashes_detected(self, handler, mock_managers):
        """Cracked hashes should be detected."""
        parsed_data = {
            "cracked": [
                {"hash": "5f4dcc3b5aa765d61d8327deb882cf99", "password": "password"},
                {"hash": "d8578edf8458ce06fbc5bb76a58c5ca4", "password": "qwerty"},
            ],
            "stats": {"status": "exhausted", "cracked_count": 2, "total_count": 5},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Status: Exhausted\nRecovered: 2/5\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.hashcat_parser.parse_hashcat_output",
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
            "cracked": [
                {"hash": "5f4dcc3b5aa765d61d8327deb882cf99", "password": "password"}
            ],
            "stats": {"status": "exhausted", "cracked_count": 1},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("hashcat results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.hashcat_parser.parse_hashcat_output",
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
        """No cracked hashes should return no_results status."""
        parsed_data = {
            "cracked": [],
            "stats": {"status": "exhausted", "cracked_count": 0, "total_count": 5},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Status: Exhausted\nRecovered: 0/5")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.hashcat_parser.parse_hashcat_output",
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
        log_content = "No hashes loaded"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "No hashes loaded" in captured.out
        finally:
            os.unlink(log_path)

    def test_display_error_shows_token_length_exception(self, handler, capsys):
        """display_error should identify token length exception errors."""
        log_content = "Token length exception"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "Invalid hash format" in captured.out
        finally:
            os.unlink(log_path)

    def test_display_done_shows_cracked(self, handler, capsys):
        """display_done should show cracked hashes."""
        parsed_data = {
            "cracked": [
                {"hash": "5f4dcc3b5aa765d61d8327deb882cf99", "password": "password"}
            ],
            "stats": {"status": "exhausted", "cracked_count": 1, "total_count": 5},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("hashcat results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.hashcat_parser.parse_hashcat_output",
                return_value=parsed_data,
            ):
                job = {}
                handler.display_done(job, log_path)
                captured = capsys.readouterr()
                assert "HASHCAT RESULTS" in captured.out
                assert "Cracked Hashes" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import hashcat_handler  # noqa: F401

        handler = registry.get_handler("hashcat")
        assert handler is not None
        assert handler.tool_name == "hashcat"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import hashcat_handler  # noqa: F401

        assert registry.has_warning_handler("hashcat") is True
        assert registry.has_error_handler("hashcat") is True
        assert registry.has_no_results_handler("hashcat") is True
        assert registry.has_done_handler("hashcat") is True
