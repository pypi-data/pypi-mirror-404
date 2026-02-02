#!/usr/bin/env python3
"""
Tests for the MsfAuxiliaryHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS, STATUS_WARNING
from souleyez.handlers.msf_auxiliary_handler import MsfAuxiliaryHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return MsfAuxiliaryHandler()


@pytest.fixture
def mock_managers():
    """Mock database managers."""
    host_manager = MagicMock()
    findings_manager = MagicMock()
    credentials_manager = MagicMock()

    # Default: host exists
    host_manager.get_host_by_ip.return_value = {"id": 1}

    return {
        "host_manager": host_manager,
        "findings_manager": findings_manager,
        "credentials_manager": credentials_manager,
    }


class TestHandlerMetadata:
    """Test handler metadata."""

    def test_tool_name(self, handler):
        """Handler should have correct tool name."""
        assert handler.tool_name == "msf_auxiliary"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "Metasploit Auxiliary"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful auxiliary scan parsing."""

    def test_findings_detected(self, handler, mock_managers):
        """Findings from auxiliary scan should be detected."""
        log_content = """
[*] Scanning 10.0.0.5
[+] 10.0.0.5:21 - FTP Anonymous READ/WRITE (220 Welcome to FTP)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            # Mock the parser to return findings
            with patch("souleyez.parsers.msf_parser.parse_msf_log") as mock_parse:
                mock_parse.return_value = {
                    "findings": [
                        {
                            "title": "FTP Anonymous Access",
                            "severity": "high",
                            "port": 21,
                        }
                    ],
                    "credentials": [],
                    "services": [],
                }
                job = {"target": "10.0.0.5"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_DONE
                assert result["findings_added"] == 1
        finally:
            os.unlink(log_path)

    def test_credentials_detected(self, handler, mock_managers):
        """Credentials from auxiliary scan should be detected."""
        log_content = """
[+] 10.0.0.5:22 - Success: 'admin:password123'
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch("souleyez.parsers.msf_parser.parse_msf_log") as mock_parse:
                mock_parse.return_value = {
                    "findings": [],
                    "credentials": [
                        {
                            "username": "admin",
                            "password": "password123",
                            "service": "ssh",
                            "port": 22,
                        }
                    ],
                    "services": [],
                }
                job = {"target": "10.0.0.5"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_DONE
                assert result["credentials_added"] == 1
        finally:
            os.unlink(log_path)

    def test_services_detected(self, handler, mock_managers):
        """Services from auxiliary scan should be detected."""
        log_content = """
[*] 10.0.0.5:22 - SSH-2.0-OpenSSH_7.9
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch("souleyez.parsers.msf_parser.parse_msf_log") as mock_parse:
                mock_parse.return_value = {
                    "findings": [],
                    "credentials": [],
                    "services": [
                        {
                            "port": 22,
                            "service_name": "ssh",
                            "service_version": "OpenSSH_7.9",
                        }
                    ],
                }
                job = {"target": "10.0.0.5"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_DONE
                assert result["services_added"] == 1
        finally:
            os.unlink(log_path)


class TestParseJobFailure:
    """Test failed auxiliary scan parsing."""

    def test_connection_refused_returns_warning(self, handler, mock_managers):
        """Connection refused should return warning status."""
        log_content = """
[-] Connection refused
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch("souleyez.parsers.msf_parser.parse_msf_log") as mock_parse:
                mock_parse.return_value = {
                    "findings": [],
                    "credentials": [],
                    "services": [],
                }
                job = {"target": "10.0.0.5"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_WARNING
                assert "refused" in result["summary"].lower()
        finally:
            os.unlink(log_path)

    def test_connection_timeout_returns_warning(self, handler, mock_managers):
        """Connection timeout should return warning status."""
        log_content = """
[-] Rex::ConnectionTimeout: Connection timed out
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch("souleyez.parsers.msf_parser.parse_msf_log") as mock_parse:
                mock_parse.return_value = {
                    "findings": [],
                    "credentials": [],
                    "services": [],
                }
                job = {"target": "10.0.0.5"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_WARNING
                assert "timed out" in result["summary"].lower()
        finally:
            os.unlink(log_path)

    def test_no_route_returns_warning(self, handler, mock_managers):
        """No route to host should return warning status."""
        log_content = """
[-] No route to host
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch("souleyez.parsers.msf_parser.parse_msf_log") as mock_parse:
                mock_parse.return_value = {
                    "findings": [],
                    "credentials": [],
                    "services": [],
                }
                job = {"target": "10.0.0.5"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_WARNING
                assert "no route" in result["summary"].lower()
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_empty_output_returns_no_results(self, handler, mock_managers):
        """Empty or minimal output should return no_results."""
        log_content = """
[*] Scanning 10.0.0.5
[*] Scanned 1 of 1 hosts (100% complete)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch("souleyez.parsers.msf_parser.parse_msf_log") as mock_parse:
                mock_parse.return_value = {
                    "findings": [],
                    "credentials": [],
                    "services": [],
                }
                job = {"target": "10.0.0.5"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_NO_RESULTS
                assert "no results" in result["summary"].lower()
        finally:
            os.unlink(log_path)


class TestParseJobDatabaseWrites:
    """Test that database writes happen correctly."""

    def test_findings_added_to_database(self, handler, mock_managers):
        """Findings should be added to the database."""
        log_content = """
[+] Finding detected
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch("souleyez.parsers.msf_parser.parse_msf_log") as mock_parse:
                mock_parse.return_value = {
                    "findings": [
                        {
                            "title": "Anonymous FTP Access",
                            "severity": "high",
                            "description": "FTP allows anonymous login",
                            "port": 21,
                        }
                    ],
                    "credentials": [],
                    "services": [],
                }
                job = {"target": "10.0.0.5"}
                handler.parse_job(1, log_path, job, **mock_managers)

                # Verify findings_manager.add_finding was called
                mock_managers["findings_manager"].add_finding.assert_called_once()
                call_kwargs = mock_managers["findings_manager"].add_finding.call_args[1]
                assert call_kwargs["title"] == "Anonymous FTP Access"
                assert call_kwargs["severity"] == "high"
                assert call_kwargs["tool"] == "msf_auxiliary"
        finally:
            os.unlink(log_path)

    def test_credentials_added_to_database(self, handler, mock_managers):
        """Credentials should be added to the database."""
        log_content = """
[+] Credential found
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch("souleyez.parsers.msf_parser.parse_msf_log") as mock_parse:
                mock_parse.return_value = {
                    "findings": [],
                    "credentials": [
                        {
                            "username": "admin",
                            "password": "secret",
                            "service": "ssh",
                            "port": 22,
                            "status": "valid",
                        }
                    ],
                    "services": [],
                }
                job = {"target": "10.0.0.5"}
                handler.parse_job(1, log_path, job, **mock_managers)

                # Verify credentials_manager.add_credential was called
                mock_managers["credentials_manager"].add_credential.assert_called_once()
                call_kwargs = mock_managers[
                    "credentials_manager"
                ].add_credential.call_args[1]
                assert call_kwargs["username"] == "admin"
                assert call_kwargs["password"] == "secret"
                assert call_kwargs["tool"] == "msf_auxiliary"
        finally:
            os.unlink(log_path)

    def test_services_added_to_database(self, handler, mock_managers):
        """Services should be added to the database."""
        log_content = """
[*] Service detected
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch("souleyez.parsers.msf_parser.parse_msf_log") as mock_parse:
                mock_parse.return_value = {
                    "findings": [],
                    "credentials": [],
                    "services": [
                        {
                            "port": 80,
                            "service_name": "http",
                            "service_version": "Apache 2.4",
                        }
                    ],
                }
                job = {"target": "10.0.0.5"}
                handler.parse_job(1, log_path, job, **mock_managers)

                # Verify host_manager.add_service was called
                mock_managers["host_manager"].add_service.assert_called_once()
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

    def test_display_warning_uses_parse_result_summary(self, handler, capsys):
        """display_warning should use summary from parse_result."""
        job = {"parse_result": {"summary": "Target unreachable: Connection refused"}}
        handler.display_warning(job, "/fake/path")
        captured = capsys.readouterr()
        assert "connection refused" in captured.out.lower()

    def test_display_no_results_shows_reasons(self, handler, capsys):
        """display_no_results should show possible reasons."""
        job = {}
        handler.display_no_results(job, "/fake/path")
        captured = capsys.readouterr()
        assert "No results found" in captured.out
        assert "could mean" in captured.out.lower()


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()  # Clear any cached state

        # Force reimport to trigger discovery
        from souleyez.handlers import msf_auxiliary_handler  # noqa: F401

        handler = registry.get_handler("msf_auxiliary")
        assert handler is not None
        assert handler.tool_name == "msf_auxiliary"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import msf_auxiliary_handler  # noqa: F401

        assert registry.has_warning_handler("msf_auxiliary") is True
        assert registry.has_error_handler("msf_auxiliary") is True
        assert registry.has_no_results_handler("msf_auxiliary") is True
        assert registry.has_done_handler("msf_auxiliary") is True
