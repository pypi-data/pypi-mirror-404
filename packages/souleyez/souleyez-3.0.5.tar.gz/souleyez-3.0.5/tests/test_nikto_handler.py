#!/usr/bin/env python3
"""
Tests for the NiktoHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS, STATUS_ERROR
from souleyez.handlers.nikto_handler import NiktoHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return NiktoHandler()


@pytest.fixture
def mock_managers():
    """Mock database managers."""
    host_manager = MagicMock()
    findings_manager = MagicMock()
    credentials_manager = MagicMock()

    # Default: host exists
    host_manager.get_host_by_ip.return_value = {"id": 1}
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
        assert handler.tool_name == "nikto"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "Nikto"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful nikto parsing."""

    def test_findings_detected(self, handler, mock_managers):
        """Discovered web issues should be detected."""
        parsed_data = {
            "target_ip": "192.168.1.10",
            "target_hostname": "www.example.com",
            "target_port": "80",
            "server": "Apache/2.4",
            "findings": [
                {
                    "path": "/admin/",
                    "description": "Admin directory found",
                    "severity": "medium",
                    "osvdb": "OSVDB-12345",
                },
                {
                    "path": "/phpinfo.php",
                    "description": "PHP info page exposed",
                    "severity": "high",
                },
            ],
            "stats": {
                "total": 2,
                "by_severity": {"high": 1, "medium": 1, "low": 0, "info": 0},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Nikto scan results\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nikto_parser.parse_nikto_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value=None,
                ):
                    job = {"target": "http://192.168.1.10"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_DONE
                    assert result["findings_count"] == 2
                    assert result["findings_added"] == 2
        finally:
            os.unlink(log_path)

    def test_findings_stored_in_database(self, handler, mock_managers):
        """Findings should be stored in database."""
        parsed_data = {
            "target_ip": "192.168.1.10",
            "server": "nginx",
            "findings": [
                {"path": "/backup/", "description": "Backup dir", "severity": "high"}
            ],
            "stats": {
                "total": 1,
                "by_severity": {"high": 1, "medium": 0, "low": 0, "info": 0},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Nikto scan results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nikto_parser.parse_nikto_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value=None,
                ):
                    job = {"target": "http://192.168.1.10"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["findings_added"] == 1
                    mock_managers["findings_manager"].add_finding.assert_called_once()
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_findings_returns_no_results(self, handler, mock_managers):
        """No findings should return no_results status."""
        parsed_data = {
            "target_ip": "192.168.1.10",
            "server": "Apache",
            "findings": [],
            "stats": {
                "total": 0,
                "by_severity": {"high": 0, "medium": 0, "low": 0, "info": 0},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Nikto scan - no findings")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nikto_parser.parse_nikto_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value=None,
                ):
                    job = {"target": "http://192.168.1.10"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_NO_RESULTS
                    assert result["findings_added"] == 0
        finally:
            os.unlink(log_path)


class TestParseJobError:
    """Test error scenario."""

    def test_tool_error_returns_error_status(self, handler, mock_managers):
        """Tool error should return error status."""
        parsed_data = {
            "target_ip": "192.168.1.10",
            "findings": [],
            "stats": {"total": 0, "by_severity": {}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Connection refused")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nikto_parser.parse_nikto_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value="Connection failed",
                ):
                    job = {"target": "http://192.168.1.10"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_ERROR
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
        job = {"target": "http://example.com"}
        handler.display_no_results(job, "/fake/path")
        captured = capsys.readouterr()
        assert "No issues detected" in captured.out
        assert "Tips" in captured.out

    def test_display_error_shows_connection_refused(self, handler, capsys):
        """display_error should identify connection refused errors."""
        log_content = "Connection refused"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "connect" in captured.out.lower()
        finally:
            os.unlink(log_path)

    def test_display_error_shows_ssl_error(self, handler, capsys):
        """display_error should identify SSL errors."""
        log_content = "SSL handshake failed"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "ssl" in captured.out.lower()
        finally:
            os.unlink(log_path)

    def test_display_done_shows_findings(self, handler, capsys):
        """display_done should show discovered findings."""
        parsed_data = {
            "target_ip": "192.168.1.10",
            "server": "Apache/2.4",
            "target_port": "80",
            "findings": [
                {"path": "/admin/", "description": "Admin found", "severity": "high"},
                {
                    "path": "/backup/",
                    "description": "Backup found",
                    "severity": "medium",
                },
            ],
            "stats": {
                "total": 2,
                "by_severity": {"high": 1, "medium": 1, "low": 0, "info": 0},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Nikto scan results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nikto_parser.parse_nikto_output",
                return_value=parsed_data,
            ):
                job = {"target": "http://192.168.1.10"}
                handler.display_done(job, log_path)
                captured = capsys.readouterr()
                assert "NIKTO SCAN RESULTS" in captured.out
                assert "192.168.1.10" in captured.out
                assert "Apache/2.4" in captured.out
                assert "Issues Found" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import nikto_handler  # noqa: F401

        handler = registry.get_handler("nikto")
        assert handler is not None
        assert handler.tool_name == "nikto"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import nikto_handler  # noqa: F401

        assert registry.has_warning_handler("nikto") is True
        assert registry.has_error_handler("nikto") is True
        assert registry.has_no_results_handler("nikto") is True
        assert registry.has_done_handler("nikto") is True
