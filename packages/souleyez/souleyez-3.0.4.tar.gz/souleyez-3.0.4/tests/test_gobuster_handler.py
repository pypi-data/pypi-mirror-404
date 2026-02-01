#!/usr/bin/env python3
"""
Tests for the GobusterHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS, STATUS_WARNING
from souleyez.handlers.gobuster_handler import GobusterHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return GobusterHandler()


@pytest.fixture
def mock_managers():
    """Mock database managers."""
    host_manager = MagicMock()
    findings_manager = MagicMock()
    credentials_manager = MagicMock()

    # Default: host exists
    host_manager.get_host_by_ip.return_value = {"id": 1}
    host_manager.list_hosts.return_value = [{"id": 1, "ip_address": "192.168.1.10"}]
    host_manager.add_or_update_host.return_value = {"id": 1}

    return {
        "host_manager": host_manager,
        "findings_manager": findings_manager,
        "credentials_manager": credentials_manager,
    }


class TestHandlerMetadata:
    """Test handler metadata."""

    def test_tool_name(self, handler):
        """Handler should have correct tool name."""
        assert handler.tool_name == "gobuster"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "Gobuster"

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
        log_content = """
===============================================================
Gobuster v3.8
===============================================================
[+] Url:                     http://192.168.1.10
===============================================================
/admin                (Status: 200) [Size: 1234]
/images               (Status: 301) [Size: 169] [--> http://192.168.1.10/images/]
/robots.txt           (Status: 200) [Size: 128]
===============================================================
Finished
===============================================================
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error", return_value=None
            ):
                with patch("souleyez.storage.web_paths.WebPathsManager"):
                    job = {"target": "http://192.168.1.10"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_DONE
                    assert result["total_paths"] == 3
        finally:
            os.unlink(log_path)

    def test_redirect_detected(self, handler, mock_managers):
        """Redirects should be detected and counted."""
        log_content = """
[+] Url:                     http://192.168.1.10
/images               (Status: 301) [Size: 169] [--> http://192.168.1.10/images/]
/scripts              (Status: 301) [Size: 169] [--> http://192.168.1.10/scripts/]
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error", return_value=None
            ):
                with patch("souleyez.storage.web_paths.WebPathsManager"):
                    job = {"target": "http://192.168.1.10"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_DONE
                    assert result["redirects_found"] == 2
        finally:
            os.unlink(log_path)

    def test_php_files_extracted(self, handler, mock_managers):
        """PHP files should be extracted for auto-chaining."""
        log_content = """
[+] Url:                     http://192.168.1.10
/index.php            (Status: 200) [Size: 1234]
/login.php            (Status: 200) [Size: 5678]
/config.php           (Status: 403) [Size: 276]
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error", return_value=None
            ):
                with patch("souleyez.storage.web_paths.WebPathsManager"):
                    job = {"target": "http://192.168.1.10"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert len(result["php_files"]) == 3
        finally:
            os.unlink(log_path)


class TestParseJobWarning:
    """Test warning scenarios."""

    def test_wildcard_detected_returns_warning(self, handler, mock_managers):
        """Wildcard response should return warning status."""
        log_content = """
[+] Url:                     http://192.168.1.10
the server returns a status code that matches => 403 (Length: 1434)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error", return_value=None
            ):
                with patch("souleyez.storage.web_paths.WebPathsManager"):
                    job = {"target": "http://192.168.1.10"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_WARNING
                    assert result["wildcard_detected"] is True
                    assert result["exclude_length"] == "1434"
        finally:
            os.unlink(log_path)

    def test_host_redirect_returns_warning(self, handler, mock_managers):
        """Host-level redirect should return warning status."""
        log_content = """
[+] Url:                     http://192.168.1.10
HOST_REDIRECT_TARGET: http://www.example.com
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error", return_value=None
            ):
                with patch("souleyez.storage.web_paths.WebPathsManager"):
                    job = {"target": "http://192.168.1.10"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_WARNING
                    assert result["host_redirect_detected"] is True
                    assert result["redirect_target"] == "http://www.example.com"
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_paths_returns_no_results(self, handler, mock_managers):
        """No paths found should return no_results."""
        log_content = """
===============================================================
Gobuster v3.8
===============================================================
[+] Url:                     http://192.168.1.10
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
===============================================================
Finished
===============================================================
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error", return_value=None
            ):
                with patch("souleyez.storage.web_paths.WebPathsManager"):
                    job = {"target": "http://192.168.1.10"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_NO_RESULTS
                    assert result["total_paths"] == 0
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

    def test_high_severity_for_database_files(self, handler):
        """Database files should be high severity."""
        paths = [
            {"url": "http://example.com/dump.sql", "status_code": 200},
        ]
        concerns = handler._identify_security_concerns(paths)

        assert len(concerns) == 1
        assert concerns[0]["severity"] == "high"
        assert "Database" in concerns[0]["label"]


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

    def test_display_warning_shows_wildcard(self, handler, capsys):
        """display_warning should show wildcard detection info."""
        log_content = "wildcard response detected (Length: 1234)"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {"target": "http://example.com"}
            handler.display_warning(job, log_path)
            captured = capsys.readouterr()
            assert "Wildcard" in captured.out
        finally:
            os.unlink(log_path)

    def test_display_no_results_shows_tips(self, handler, capsys):
        """display_no_results should show helpful tips."""
        job = {
            "target": "http://example.com",
            "args": ["-w", "/usr/share/wordlists/common.txt"],
        }
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


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import gobuster_handler  # noqa: F401

        handler = registry.get_handler("gobuster")
        assert handler is not None
        assert handler.tool_name == "gobuster"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import gobuster_handler  # noqa: F401

        assert registry.has_warning_handler("gobuster") is True
        assert registry.has_error_handler("gobuster") is True
        assert registry.has_no_results_handler("gobuster") is True
        assert registry.has_done_handler("gobuster") is True
