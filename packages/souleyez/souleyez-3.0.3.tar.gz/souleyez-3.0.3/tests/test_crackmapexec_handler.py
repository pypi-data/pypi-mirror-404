#!/usr/bin/env python3
"""
Tests for the CrackMapExecHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS
from souleyez.handlers.crackmapexec_handler import CrackMapExecHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return CrackMapExecHandler()


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
        assert handler.tool_name == "crackmapexec"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "CrackMapExec"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful crackmapexec parsing."""

    def test_hosts_and_credentials_detected(self, handler, mock_managers):
        """Discovered hosts and credentials should be detected."""
        parsed_data = {
            "findings": {
                "hosts": [
                    {
                        "ip": "192.168.1.10",
                        "hostname": "DC01",
                        "domain": "TESTDOMAIN.LOCAL",
                        "os": "Windows Server 2019",
                    }
                ],
                "credentials": [{"username": "admin", "password": "Pass123!"}],
            },
            "hosts_found": 1,
            "shares_found": 0,
            "users_found": 0,
            "vulnerabilities_found": 0,
            "domains": ["TESTDOMAIN.LOCAL"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("[+] crackmapexec results\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.crackmapexec_parser.parse_crackmapexec",
                return_value=parsed_data,
            ):
                job = {"target": "192.168.1.10"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_DONE
                assert result["hosts_found"] == 1
                assert result["credentials_added"] == 1
        finally:
            os.unlink(log_path)

    def test_credentials_stored_in_database(self, handler, mock_managers):
        """Credentials should be stored in database."""
        parsed_data = {
            "findings": {
                "hosts": [],
                "credentials": [{"username": "admin", "password": "Pass123!"}],
            },
            "hosts_found": 0,
            "shares_found": 0,
            "users_found": 0,
            "vulnerabilities_found": 0,
            "domains": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("[+] crackmapexec results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.crackmapexec_parser.parse_crackmapexec",
                return_value=parsed_data,
            ):
                job = {"target": "192.168.1.10"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["credentials_added"] == 1
                mock_managers["credentials_manager"].add_credential.assert_called_once()
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_data_returns_no_results(self, handler, mock_managers):
        """No data should return no_results status."""
        parsed_data = {
            "findings": {"hosts": [], "credentials": []},
            "hosts_found": 0,
            "shares_found": 0,
            "users_found": 0,
            "vulnerabilities_found": 0,
            "domains": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("crackmapexec scan - no results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.crackmapexec_parser.parse_crackmapexec",
                return_value=parsed_data,
            ):
                job = {"target": "192.168.1.10"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_NO_RESULTS
        finally:
            os.unlink(log_path)


class TestParseJobError:
    """Test error scenario."""

    def test_parser_error_returns_error_dict(self, handler, mock_managers):
        """Parser error should return error dict."""
        parsed_data = {"error": "Connection refused"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Connection refused")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.crackmapexec_parser.parse_crackmapexec",
                return_value=parsed_data,
            ):
                job = {"target": "192.168.1.10"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert "error" in result
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
        assert "No SMB information discovered" in captured.out
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
            assert "refused" in captured.out.lower()
        finally:
            os.unlink(log_path)

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
            assert "access denied" in captured.out.lower()
        finally:
            os.unlink(log_path)

    def test_display_error_shows_timeout(self, handler, capsys):
        """display_error should identify timeout errors."""
        log_content = "Connection timed out"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "timed out" in captured.out.lower()
        finally:
            os.unlink(log_path)

    def test_display_done_shows_hosts_and_shares(self, handler, capsys):
        """display_done should show discovered hosts and shares."""
        parsed_data = {
            "findings": {
                "hosts": [
                    {
                        "ip": "192.168.1.10",
                        "hostname": "DC01",
                        "domain": "TESTDOMAIN.LOCAL",
                        "os": "Windows Server 2019",
                        "port": 445,
                    }
                ],
                "shares": [{"name": "C$", "permissions": "READ"}],
                "users": [],
                "vulnerabilities": [],
                "credentials": [],
                "auth_info": {},
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("crackmapexec scan results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.crackmapexec_parser.parse_crackmapexec_output",
                return_value=parsed_data,
            ):
                job = {"target": "192.168.1.10"}
                handler.display_done(job, log_path)
                captured = capsys.readouterr()
                assert "SMB ENUMERATION RESULTS" in captured.out
                assert "192.168.1.10" in captured.out
                assert "DC01" in captured.out
                assert "Shares Found" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import crackmapexec_handler  # noqa: F401

        handler = registry.get_handler("crackmapexec")
        assert handler is not None
        assert handler.tool_name == "crackmapexec"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import crackmapexec_handler  # noqa: F401

        assert registry.has_warning_handler("crackmapexec") is True
        assert registry.has_error_handler("crackmapexec") is True
        assert registry.has_no_results_handler("crackmapexec") is True
        assert registry.has_done_handler("crackmapexec") is True
