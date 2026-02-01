#!/usr/bin/env python3
"""
Tests for the ImpacketPsexecHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS
from souleyez.handlers.impacket_psexec_handler import ImpacketPsexecHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return ImpacketPsexecHandler()


@pytest.fixture
def mock_managers():
    """Mock database managers."""
    host_manager = MagicMock()
    findings_manager = MagicMock()
    credentials_manager = MagicMock()

    host_manager.add_or_update_host.return_value = 1

    return {
        "host_manager": host_manager,
        "findings_manager": findings_manager,
        "credentials_manager": credentials_manager,
    }


class TestHandlerMetadata:
    """Test handler metadata."""

    def test_tool_name(self, handler):
        """Handler should have correct tool name."""
        assert handler.tool_name == "impacket-psexec"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "PSExec"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful psexec parsing."""

    def test_success_detected(self, handler, mock_managers):
        """Successful shell should be detected."""
        parsed_data = {"success": True, "output_lines": 15}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("C:\\Windows\\system32>\nwhoami\nnt authority\\system\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.impacket_parser.parse_psexec",
                return_value=parsed_data,
            ):
                job = {"target": "admin:Pass123!@192.168.1.10"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_DONE
                assert result["success"] is True
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_shell_returns_no_results(self, handler, mock_managers):
        """No shell output should return no_results status."""
        parsed_data = {"success": False, "output_lines": 0}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Connection failed")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.impacket_parser.parse_psexec",
                return_value=parsed_data,
            ):
                job = {"target": "192.168.1.10"}
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
        job = {"target": "192.168.1.10"}
        handler.display_no_results(job, "/fake/path")
        captured = capsys.readouterr()
        assert "No command output captured" in captured.out
        assert "Possible reasons" in captured.out

    def test_display_error_shows_access_denied(self, handler, capsys):
        """display_error should identify access denied errors."""
        log_content = "STATUS_ACCESS_DENIED"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "Access denied" in captured.out
        finally:
            os.unlink(log_path)

    def test_display_error_shows_service_error(self, handler, capsys):
        """display_error should identify service errors."""
        log_content = "Service installation failed"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "Service installation failed" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import impacket_psexec_handler  # noqa: F401

        handler = registry.get_handler("impacket-psexec")
        assert handler is not None
        assert handler.tool_name == "impacket-psexec"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import impacket_psexec_handler  # noqa: F401

        assert registry.has_warning_handler("impacket-psexec") is True
        assert registry.has_error_handler("impacket-psexec") is True
        assert registry.has_no_results_handler("impacket-psexec") is True
        assert registry.has_done_handler("impacket-psexec") is True
