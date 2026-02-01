#!/usr/bin/env python3
"""
Tests for the FfufHandler.

Tests parsing accuracy and display functionality.
"""
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS, STATUS_ERROR
from souleyez.handlers.ffuf_handler import FfufHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return FfufHandler()


@pytest.fixture
def mock_managers():
    """Mock database managers."""
    host_manager = MagicMock()
    findings_manager = MagicMock()
    credentials_manager = MagicMock()

    # Default: host exists
    host_manager.get_host_by_ip.return_value = {"id": 1}
    host_manager.add_or_update_host.return_value = {"id": 1}

    return {
        "host_manager": host_manager,
        "findings_manager": findings_manager,
        "credentials_manager": credentials_manager,
    }


def create_ffuf_json_output(results, target="http://192.168.1.10/FUZZ", method="GET"):
    """Create a valid ffuf JSON output string."""
    data = {
        "commandline": f"ffuf -u {target} -w wordlist.txt",
        "time": "2024-01-15T10:00:00Z",
        "config": {
            "url": target,
            "method": method,
            "wordlist": "/usr/share/wordlists/common.txt",
        },
        "results": results,
    }
    return json.dumps(data)


class TestHandlerMetadata:
    """Test handler metadata."""

    def test_tool_name(self, handler):
        """Handler should have correct tool name."""
        assert handler.tool_name == "ffuf"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "Ffuf"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful path enumeration parsing."""

    def test_paths_detected(self, handler, mock_managers):
        """Discovered paths should be detected."""
        results = [
            {"url": "http://192.168.1.10/admin", "status": 200, "length": 1234},
            {
                "url": "http://192.168.1.10/images",
                "status": 301,
                "length": 169,
                "redirectlocation": "http://192.168.1.10/images/",
            },
            {"url": "http://192.168.1.10/robots.txt", "status": 200, "length": 128},
        ]
        log_content = create_ffuf_json_output(results)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error", return_value=None
            ):
                with patch("souleyez.storage.web_paths.WebPathsManager"):
                    job = {"target": "http://192.168.1.10/FUZZ"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_DONE
                    assert result["results_found"] == 3
        finally:
            os.unlink(log_path)

    def test_method_extracted(self, handler, mock_managers):
        """HTTP method should be extracted from config."""
        results = [{"url": "http://192.168.1.10/login", "status": 200, "length": 500}]
        log_content = create_ffuf_json_output(results, method="POST")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error", return_value=None
            ):
                with patch("souleyez.storage.web_paths.WebPathsManager"):
                    job = {"target": "http://192.168.1.10/FUZZ"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["method"] == "POST"
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_paths_returns_no_results(self, handler, mock_managers):
        """No paths found should return no_results."""
        log_content = create_ffuf_json_output([])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error", return_value=None
            ):
                with patch("souleyez.storage.web_paths.WebPathsManager"):
                    job = {"target": "http://192.168.1.10/FUZZ"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_NO_RESULTS
                    assert result["results_found"] == 0
        finally:
            os.unlink(log_path)


class TestParseJobError:
    """Test error scenario."""

    def test_invalid_json_returns_error(self, handler, mock_managers):
        """Invalid JSON should return error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json")
            log_path = f.name

        try:
            job = {"target": "http://192.168.1.10/FUZZ"}
            result = handler.parse_job(1, log_path, job, **mock_managers)

            assert "error" in result
        finally:
            os.unlink(log_path)


class TestSecurityConcerns:
    """Test security concern detection."""

    def test_sensitive_paths_detected(self, handler):
        """Sensitive paths should be identified."""
        paths = [
            {"url": "http://example.com/.git/config", "status_code": 200},
            {"url": "http://example.com/backup.sql", "status_code": 200},
            {"url": "http://example.com/.env", "status_code": 200},
            {"url": "http://example.com/admin/", "status_code": 200},
        ]
        concerns = handler._identify_security_concerns(paths)

        assert len(concerns) >= 4
        severities = [c["severity"] for c in concerns]
        assert "high" in severities
        assert "medium" in severities

    def test_high_severity_for_config_files(self, handler):
        """Config files should be high severity."""
        paths = [
            {"url": "http://example.com/.env", "status_code": 200},
        ]
        concerns = handler._identify_security_concerns(paths)

        assert len(concerns) == 1
        assert concerns[0]["severity"] == "high"
        assert "Configuration" in concerns[0]["label"]


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
        job = {"target": "http://example.com/FUZZ"}
        handler.display_no_results(job, "/fake/path")
        captured = capsys.readouterr()
        assert "No paths discovered" in captured.out
        assert "This could mean" in captured.out

    def test_display_error_shows_timeout(self, handler, capsys):
        """display_error should identify timeout errors."""
        log_content = "Command timed out after 300 seconds"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "timeout" in captured.out.lower()
        finally:
            os.unlink(log_path)

    def test_display_done_shows_paths(self, handler, capsys):
        """display_done should show discovered paths."""
        results = [
            {"url": "http://192.168.1.10/admin", "status": 200, "length": 1234},
            {"url": "http://192.168.1.10/login", "status": 200, "length": 500},
        ]
        log_content = create_ffuf_json_output(results)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {"target": "http://192.168.1.10/FUZZ"}
            handler.display_done(job, log_path)
            captured = capsys.readouterr()
            assert "FFUF DISCOVERED PATHS" in captured.out
            assert "Total found: 2" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import ffuf_handler  # noqa: F401

        handler = registry.get_handler("ffuf")
        assert handler is not None
        assert handler.tool_name == "ffuf"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import ffuf_handler  # noqa: F401

        assert registry.has_warning_handler("ffuf") is True
        assert registry.has_error_handler("ffuf") is True
        assert registry.has_no_results_handler("ffuf") is True
        assert registry.has_done_handler("ffuf") is True
