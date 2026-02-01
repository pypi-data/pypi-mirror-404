#!/usr/bin/env python3
"""
Tests for the ResponderHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS
from souleyez.handlers.responder_handler import ResponderHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return ResponderHandler()


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
        assert handler.tool_name == "responder"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "Responder"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful responder parsing."""

    def test_credentials_captured_detected(self, handler, mock_managers):
        """Captured credentials should be detected."""
        parsed_data = {
            "credentials": [
                {"domain": "CORP", "username": "jsmith", "protocol": "NTLMv2"}
            ],
            "credentials_captured": 1,
            "summary": "Captured 1 NTLMv2 hash",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("[NTLMv2] NTLMv2 Hash: CORP\\jsmith\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.responder_parser.parse_responder",
                return_value=parsed_data,
            ):
                with patch("souleyez.parsers.responder_parser.store_responder_results"):
                    job = {"target": "eth0"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_DONE
                    assert result["credentials_captured"] == 1
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_credentials_returns_no_results(self, handler, mock_managers):
        """No captured credentials should return no_results status."""
        parsed_data = {
            "credentials": [],
            "credentials_captured": 0,
            "summary": "No credentials captured",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Responder listening...")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.responder_parser.parse_responder",
                return_value=parsed_data,
            ):
                with patch("souleyez.parsers.responder_parser.store_responder_results"):
                    job = {"target": "eth0"}
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
        assert "No credentials captured" in captured.out
        assert "Possible reasons" in captured.out

    def test_display_error_shows_permission_denied(self, handler, capsys):
        """display_error should identify permission denied errors."""
        log_content = "Permission denied"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "Permission denied" in captured.out
        finally:
            os.unlink(log_path)

    def test_display_error_shows_port_in_use(self, handler, capsys):
        """display_error should identify port in use errors."""
        log_content = "Address already in use"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "Port already in use" in captured.out
        finally:
            os.unlink(log_path)

    def test_display_done_shows_credentials(self, handler, capsys):
        """display_done should show captured credentials."""
        parsed_data = {
            "credentials": [
                {"domain": "CORP", "username": "jsmith", "protocol": "NTLMv2"}
            ],
            "credentials_captured": 1,
            "summary": "Captured 1 NTLMv2 hash",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("responder results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.responder_parser.parse_responder",
                return_value=parsed_data,
            ):
                job = {"target": "eth0"}
                handler.display_done(job, log_path)
                captured = capsys.readouterr()
                assert "RESPONDER RESULTS" in captured.out
                assert "NTLMv2" in captured.out
                assert "jsmith" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import responder_handler  # noqa: F401

        handler = registry.get_handler("responder")
        assert handler is not None
        assert handler.tool_name == "responder"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import responder_handler  # noqa: F401

        assert registry.has_warning_handler("responder") is True
        assert registry.has_error_handler("responder") is True
        assert registry.has_no_results_handler("responder") is True
        assert registry.has_done_handler("responder") is True
