#!/usr/bin/env python3
"""
Tests for the WPScanHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS, STATUS_ERROR
from souleyez.handlers.wpscan_handler import WPScanHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return WPScanHandler()


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
        assert handler.tool_name == "wpscan"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "WPScan"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful WPScan parsing."""

    def test_vulnerabilities_detected(self, handler, mock_managers):
        """Discovered vulnerabilities should be detected."""
        parsed_data = {
            "wordpress_version": "5.8.1",
            "findings": [
                {
                    "title": "WP Core XSS",
                    "severity": "high",
                    "description": "Cross-site scripting vulnerability",
                    "references": ["https://example.com/cve"],
                }
            ],
            "plugins": [
                {
                    "name": "contact-form-7",
                    "vulnerabilities": [
                        {
                            "title": "CF7 SQL Injection",
                            "severity": "critical",
                            "description": "SQL injection in form handler",
                            "references": [],
                        }
                    ],
                }
            ],
            "themes": [],
            "users": ["admin", "editor"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("WPScan results\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.wpscan_parser.parse_wpscan_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value=None,
                ):
                    job = {"target": "http://example.com"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_DONE
                    assert result["findings_added"] == 2  # 1 core + 1 plugin
                    assert result["wp_version"] == "5.8.1"
                    assert result["users"] == ["admin", "editor"]
        finally:
            os.unlink(log_path)

    def test_findings_stored_in_database(self, handler, mock_managers):
        """Findings should be stored in database."""
        parsed_data = {
            "findings": [
                {
                    "title": "Vuln 1",
                    "severity": "high",
                    "description": "Test",
                    "references": [],
                }
            ],
            "plugins": [],
            "themes": [],
            "users": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("WPScan results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.wpscan_parser.parse_wpscan_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value=None,
                ):
                    job = {"target": "http://example.com"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["findings_added"] == 1
                    mock_managers["findings_manager"].add_finding.assert_called_once()
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_vulnerabilities_returns_no_results(self, handler, mock_managers):
        """No vulnerabilities and no WordPress info should return no_results status."""
        parsed_data = {
            "wordpress_version": None,  # No version detected = no results
            "findings": [],
            "plugins": [],
            "themes": [],
            "users": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("WPScan scan - no findings")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.wpscan_parser.parse_wpscan_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value=None,
                ):
                    job = {"target": "http://example.com"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_NO_RESULTS
                    assert result["findings_added"] == 0
        finally:
            os.unlink(log_path)


class TestParseJobError:
    """Test error scenario."""

    def test_tool_error_returns_error_status(self, handler, mock_managers):
        """Tool error should return error status."""
        parsed_data = {"vulnerabilities": [], "plugins": {}, "themes": {}, "users": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Target is NOT running WordPress")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.wpscan_parser.parse_wpscan_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value="Not WordPress",
                ):
                    job = {"target": "http://example.com"}
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
        assert "No WordPress detected" in captured.out
        assert "Tips" in captured.out

    def test_display_error_shows_not_wordpress(self, handler, capsys):
        """display_error should identify not-wordpress errors."""
        log_content = "The target is NOT running WordPress"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "not running WordPress" in captured.out
        finally:
            os.unlink(log_path)

    def test_display_error_shows_ssl_error(self, handler, capsys):
        """display_error should identify SSL errors."""
        log_content = "SSL error occurred"
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

    def test_display_error_shows_rate_limit(self, handler, capsys):
        """display_error should identify rate limit errors."""
        log_content = "API limit reached"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "rate limit" in captured.out.lower()
        finally:
            os.unlink(log_path)

    def test_display_done_shows_vulnerabilities(self, handler, capsys):
        """display_done should show discovered vulnerabilities."""
        parsed_data = {
            "wordpress_version": "5.8.1",
            "version_status": "Insecure",
            "findings": [
                {"title": "XSS Vulnerability", "severity": "high"},
                {"title": "SQL Injection", "severity": "critical"},
            ],
            "plugins": [
                {"name": "contact-form-7", "version": "5.4", "vulnerable": True}
            ],
            "themes": [{"name": "twentytwenty", "version": "1.8", "vulnerable": False}],
            "users": ["admin", "editor"],
            "info": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("WPScan scan results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.wpscan_parser.parse_wpscan_output",
                return_value=parsed_data,
            ):
                job = {"target": "http://example.com"}
                handler.display_done(job, log_path)
                captured = capsys.readouterr()
                assert "WPSCAN WORDPRESS SECURITY SCAN" in captured.out
                assert "5.8.1" in captured.out
                assert "Insecure" in captured.out
                assert "Vulnerabilities Found" in captured.out
                assert "Plugins Detected" in captured.out
                assert "Users Enumerated" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import wpscan_handler  # noqa: F401

        handler = registry.get_handler("wpscan")
        assert handler is not None
        assert handler.tool_name == "wpscan"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import wpscan_handler  # noqa: F401

        assert registry.has_warning_handler("wpscan") is True
        assert registry.has_error_handler("wpscan") is True
        assert registry.has_no_results_handler("wpscan") is True
        assert registry.has_done_handler("wpscan") is True
