#!/usr/bin/env python3
"""
Tests for the NucleiHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS, STATUS_ERROR
from souleyez.handlers.nuclei_handler import NucleiHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return NucleiHandler()


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
        assert handler.tool_name == "nuclei"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "Nuclei"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful nuclei parsing."""

    def test_findings_detected(self, handler, mock_managers):
        """Discovered vulnerabilities should be detected."""
        parsed_data = {
            "findings": [
                {
                    "name": "SQL Injection",
                    "severity": "high",
                    "template_id": "sqli-detector",
                    "matched_at": "http://example.com/login?id=1",
                    "cve_id": "CVE-2021-12345",
                },
                {
                    "name": "XSS Vulnerability",
                    "severity": "medium",
                    "template_id": "xss-detector",
                    "matched_at": "http://example.com/search",
                },
            ],
            "findings_count": 2,
            "critical": 0,
            "high": 1,
            "medium": 1,
            "low": 0,
            "info": 0,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("[sqli-detector] http://example.com/login?id=1\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nuclei_parser.parse_nuclei", return_value=parsed_data
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value=None,
                ):
                    job = {"target": "http://example.com"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_DONE
                    assert result["findings_count"] == 2
                    assert result["high"] == 1
                    assert result["medium"] == 1
        finally:
            os.unlink(log_path)

    def test_findings_stored_in_database(self, handler, mock_managers):
        """Findings should be stored in database."""
        parsed_data = {
            "findings": [
                {
                    "name": "SQL Injection",
                    "severity": "high",
                    "template_id": "sqli-detector",
                    "matched_at": "http://example.com/login",
                }
            ],
            "findings_count": 1,
            "critical": 0,
            "high": 1,
            "medium": 0,
            "low": 0,
            "info": 0,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("[sqli-detector] http://example.com/login\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nuclei_parser.parse_nuclei", return_value=parsed_data
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

    def test_no_findings_returns_no_results(self, handler, mock_managers):
        """No findings should return no_results status."""
        parsed_data = {
            "findings": [],
            "findings_count": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Nuclei scan completed\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nuclei_parser.parse_nuclei", return_value=parsed_data
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value=None,
                ):
                    job = {"target": "http://example.com"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_NO_RESULTS
                    assert result["findings_count"] == 0
        finally:
            os.unlink(log_path)


class TestParseJobError:
    """Test error scenario."""

    def test_parse_error_returns_error(self, handler, mock_managers):
        """Parse error should return error dict."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Connection refused")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nuclei_parser.parse_nuclei",
                return_value={"error": "Parse failed"},
            ):
                job = {"target": "http://example.com"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert "error" in result
        finally:
            os.unlink(log_path)

    def test_tool_error_detected(self, handler, mock_managers):
        """Tool error should return error status."""
        parsed_data = {
            "findings": [],
            "findings_count": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("[ERR] Could not connect to target")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nuclei_parser.parse_nuclei", return_value=parsed_data
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value="Connection failed",
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
        assert "No vulnerabilities detected" in captured.out
        assert "Tips" in captured.out

    def test_display_error_shows_binary_not_found(self, handler, capsys):
        """display_error should identify binary not found errors."""
        log_content = "Could not run nuclei"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "binary not found" in captured.out.lower()
        finally:
            os.unlink(log_path)

    def test_display_error_shows_rate_limit(self, handler, capsys):
        """display_error should identify rate limit errors."""
        log_content = "rate limit exceeded"
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

    def test_display_done_shows_findings(self, handler, capsys):
        """display_done should show discovered vulnerabilities."""
        parsed_data = {
            "findings": [
                {
                    "name": "SQL Injection",
                    "severity": "high",
                    "template_id": "sqli-detector",
                    "matched_at": "http://example.com/login",
                },
                {
                    "name": "Info Disclosure",
                    "severity": "info",
                    "template_id": "info-detector",
                    "matched_at": "http://example.com/",
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Nuclei scan results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nuclei_parser.parse_nuclei_output",
                return_value=parsed_data,
            ):
                job = {"target": "http://example.com"}
                handler.display_done(job, log_path)
                captured = capsys.readouterr()
                assert "VULNERABILITY SCAN" in captured.out
                assert "2 vulnerability" in captured.out
                assert "HIGH" in captured.out
        finally:
            os.unlink(log_path)

    def test_display_done_shows_severity_counts(self, handler, capsys):
        """display_done should show findings grouped by severity."""
        parsed_data = {
            "findings": [
                {
                    "severity": "critical",
                    "template_id": "crit-1",
                    "matched_at": "http://x.com/1",
                },
                {
                    "severity": "high",
                    "template_id": "high-1",
                    "matched_at": "http://x.com/2",
                },
                {
                    "severity": "high",
                    "template_id": "high-2",
                    "matched_at": "http://x.com/3",
                },
                {
                    "severity": "medium",
                    "template_id": "med-1",
                    "matched_at": "http://x.com/4",
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Nuclei scan results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nuclei_parser.parse_nuclei_output",
                return_value=parsed_data,
            ):
                job = {"target": "http://example.com"}
                handler.display_done(job, log_path)
                captured = capsys.readouterr()
                assert "CRITICAL: 1" in captured.out
                assert "HIGH: 2" in captured.out
                assert "MEDIUM: 1" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import nuclei_handler  # noqa: F401

        handler = registry.get_handler("nuclei")
        assert handler is not None
        assert handler.tool_name == "nuclei"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import nuclei_handler  # noqa: F401

        assert registry.has_warning_handler("nuclei") is True
        assert registry.has_error_handler("nuclei") is True
        assert registry.has_no_results_handler("nuclei") is True
        assert registry.has_done_handler("nuclei") is True
