#!/usr/bin/env python3
"""
Tests for the DNSReconHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS, STATUS_ERROR
from souleyez.handlers.dnsrecon_handler import DNSReconHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return DNSReconHandler()


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
        assert handler.tool_name == "dnsrecon"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "DNSRecon"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful DNSRecon parsing."""

    def test_dns_records_detected(self, handler, mock_managers):
        """Discovered DNS records should be detected."""
        parsed_data = {
            "target_domain": "example.com",
            "hosts": [
                {"hostname": "www.example.com", "ip": "192.168.1.10"},
                {"hostname": "mail.example.com", "ip": "192.168.1.20"},
            ],
            "nameservers": ["ns1.example.com", "ns2.example.com"],
            "mail_servers": ["mx1.example.com"],
            "txt_records": ["v=spf1 include:_spf.google.com ~all"],
            "subdomains": ["www.example.com", "mail.example.com"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("DNSRecon results\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.dnsrecon_parser.parse_dnsrecon_output",
                return_value=parsed_data,
            ):
                with patch("souleyez.storage.osint.OsintManager") as mock_osint:
                    mock_osint.return_value.bulk_add_osint_data.return_value = 1
                    with patch(
                        "souleyez.engine.result_handler.detect_tool_error",
                        return_value=None,
                    ):
                        job = {"target": "example.com"}
                        result = handler.parse_job(1, log_path, job, **mock_managers)

                        assert result["status"] == STATUS_DONE
                        assert result["hosts_found"] == 2
                        assert result["nameservers"] == 2
                        assert result["mail_servers"] == 1
        finally:
            os.unlink(log_path)

    def test_hosts_added_to_database(self, handler, mock_managers):
        """Hosts should be added to database."""
        parsed_data = {
            "hosts": [{"hostname": "www.example.com", "ip": "192.168.1.10"}],
            "nameservers": [],
            "mail_servers": [],
            "txt_records": [],
            "subdomains": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("DNSRecon results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.dnsrecon_parser.parse_dnsrecon_output",
                return_value=parsed_data,
            ):
                with patch("souleyez.storage.osint.OsintManager") as mock_osint:
                    mock_osint.return_value.bulk_add_osint_data.return_value = 0
                    with patch(
                        "souleyez.engine.result_handler.detect_tool_error",
                        return_value=None,
                    ):
                        job = {"target": "example.com"}
                        result = handler.parse_job(1, log_path, job, **mock_managers)

                        assert result["hosts_added"] == 1
                        mock_managers[
                            "host_manager"
                        ].add_or_update_host.assert_called_once()
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_records_returns_no_results(self, handler, mock_managers):
        """No DNS records should return no_results status."""
        parsed_data = {
            "hosts": [],
            "nameservers": [],
            "mail_servers": [],
            "txt_records": [],
            "subdomains": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("DNSRecon scan - no results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.dnsrecon_parser.parse_dnsrecon_output",
                return_value=parsed_data,
            ):
                with patch("souleyez.storage.osint.OsintManager") as mock_osint:
                    mock_osint.return_value.bulk_add_osint_data.return_value = 0
                    with patch(
                        "souleyez.engine.result_handler.detect_tool_error",
                        return_value=None,
                    ):
                        job = {"target": "example.com"}
                        result = handler.parse_job(1, log_path, job, **mock_managers)

                        assert result["status"] == STATUS_NO_RESULTS
        finally:
            os.unlink(log_path)


class TestParseJobError:
    """Test error scenario."""

    def test_tool_error_returns_error_status(self, handler, mock_managers):
        """Tool error should return error status."""
        parsed_data = {
            "hosts": [],
            "nameservers": [],
            "mail_servers": [],
            "txt_records": [],
            "subdomains": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Could not resolve domain")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.dnsrecon_parser.parse_dnsrecon_output",
                return_value=parsed_data,
            ):
                with patch("souleyez.storage.osint.OsintManager") as mock_osint:
                    mock_osint.return_value.bulk_add_osint_data.return_value = 0
                    with patch(
                        "souleyez.engine.result_handler.detect_tool_error",
                        return_value="DNS failure",
                    ):
                        job = {"target": "example.com"}
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
        job = {"target": "example.com"}
        handler.display_no_results(job, "/fake/path")
        captured = capsys.readouterr()
        assert "No DNS records discovered" in captured.out
        assert "Tips" in captured.out

    def test_display_error_shows_nxdomain(self, handler, capsys):
        """display_error should identify NXDOMAIN errors."""
        log_content = "NXDOMAIN"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "resolve" in captured.out.lower()
        finally:
            os.unlink(log_path)

    def test_display_error_shows_servfail(self, handler, capsys):
        """display_error should identify SERVFAIL errors."""
        log_content = "SERVFAIL"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "servfail" in captured.out.lower()
        finally:
            os.unlink(log_path)

    def test_display_error_shows_refused(self, handler, capsys):
        """display_error should identify REFUSED errors."""
        log_content = "REFUSED"
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

    def test_display_done_shows_records(self, handler, capsys):
        """display_done should show discovered DNS records."""
        parsed_data = {
            "hosts": [{"hostname": "www.example.com", "ip": "192.168.1.10"}],
            "nameservers": ["ns1.example.com"],
            "mail_servers": ["mx1.example.com"],
            "txt_records": ["v=spf1 include:_spf.google.com"],
            "subdomains": ["www.example.com"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("DNSRecon results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.dnsrecon_parser.parse_dnsrecon_output",
                return_value=parsed_data,
            ):
                job = {"target": "example.com"}
                handler.display_done(job, log_path)
                captured = capsys.readouterr()
                assert "DISCOVERED DNS RECORDS" in captured.out
                assert "Hosts (A Records)" in captured.out
                assert "Nameservers" in captured.out
                assert "Mail Servers" in captured.out
                assert "TXT Records" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import dnsrecon_handler  # noqa: F401

        handler = registry.get_handler("dnsrecon")
        assert handler is not None
        assert handler.tool_name == "dnsrecon"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import dnsrecon_handler  # noqa: F401

        assert registry.has_warning_handler("dnsrecon") is True
        assert registry.has_error_handler("dnsrecon") is True
        assert registry.has_no_results_handler("dnsrecon") is True
        assert registry.has_done_handler("dnsrecon") is True
