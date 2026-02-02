#!/usr/bin/env python3
"""
Tests for the TheHarvesterHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS
from souleyez.handlers.theharvester_handler import TheHarvesterHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return TheHarvesterHandler()


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
        assert handler.tool_name == "theharvester"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "TheHarvester"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful theHarvester parsing."""

    def test_osint_data_detected(self, handler, mock_managers):
        """Discovered OSINT data should be detected."""
        parsed_data = {
            "emails": ["user@example.com", "admin@example.com"],
            "hosts": ["www.example.com", "mail.example.com"],
            "ips": ["192.168.1.10", "192.168.1.20"],
            "urls": ["https://example.com/admin"],
            "asns": ["AS12345"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("theHarvester scan results\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.theharvester_parser.parse_theharvester_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.theharvester_parser.get_osint_stats",
                    return_value={},
                ):
                    with patch("souleyez.storage.osint.OsintManager") as mock_osint:
                        mock_osint.return_value.bulk_add_osint_data.return_value = 1

                        job = {"target": "example.com"}
                        result = handler.parse_job(1, log_path, job, **mock_managers)

                        assert result["status"] == STATUS_DONE
                        assert "osint_added" in result
        finally:
            os.unlink(log_path)

    def test_ips_added_to_hosts(self, handler, mock_managers):
        """Discovered IPs should be added to hosts table."""
        parsed_data = {
            "emails": [],
            "hosts": [],
            "ips": ["192.168.1.10", "192.168.1.20"],
            "urls": [],
            "asns": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("theHarvester scan results\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.theharvester_parser.parse_theharvester_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.theharvester_parser.get_osint_stats",
                    return_value={},
                ):
                    with patch("souleyez.storage.osint.OsintManager") as mock_osint:
                        mock_osint.return_value.bulk_add_osint_data.return_value = 1

                        job = {"target": "example.com"}
                        result = handler.parse_job(1, log_path, job, **mock_managers)

                        assert result["hosts_added"] == 2
                        assert (
                            mock_managers["host_manager"].add_or_update_host.call_count
                            == 2
                        )
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_osint_returns_no_results(self, handler, mock_managers):
        """No OSINT data should return no_results status."""
        parsed_data = {"emails": [], "hosts": [], "ips": [], "urls": [], "asns": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("theHarvester scan - no results\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.theharvester_parser.parse_theharvester_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.theharvester_parser.get_osint_stats",
                    return_value={},
                ):
                    with patch("souleyez.storage.osint.OsintManager") as mock_osint:
                        mock_osint.return_value.bulk_add_osint_data.return_value = 0

                        job = {"target": "example.com"}
                        result = handler.parse_job(1, log_path, job, **mock_managers)

                        assert result["status"] == STATUS_NO_RESULTS
        finally:
            os.unlink(log_path)


class TestSecurityConcerns:
    """Test security concern detection."""

    def test_admin_url_detected(self, handler):
        """Admin URLs should be flagged as high severity."""
        urls = ["https://example.com/admin/dashboard"]
        subdomains = []
        concerns = handler._identify_security_concerns(urls, subdomains)

        assert len(concerns) == 1
        assert concerns[0]["severity"] == "high"
        assert "Admin" in concerns[0]["label"]

    def test_dev_subdomain_detected(self, handler):
        """Dev/staging subdomains should be flagged."""
        urls = []
        subdomains = ["dev.example.com", "staging.example.com"]
        concerns = handler._identify_security_concerns(urls, subdomains)

        assert len(concerns) == 2
        assert all(c["severity"] == "high" for c in concerns)
        assert all(
            "Development" in c["label"] or "staging" in c["label"].lower()
            for c in concerns
        )

    def test_api_endpoint_detected(self, handler):
        """API endpoints should be flagged."""
        urls = ["https://example.com/api/v1/users"]
        subdomains = []
        concerns = handler._identify_security_concerns(urls, subdomains)

        assert len(concerns) == 1
        assert concerns[0]["severity"] == "medium"
        assert "API" in concerns[0]["label"]

    def test_database_subdomain_detected(self, handler):
        """Database subdomains should be flagged as high severity."""
        urls = []
        subdomains = ["db.example.com", "mysql.example.com"]
        concerns = handler._identify_security_concerns(urls, subdomains)

        assert len(concerns) == 2
        assert all(c["severity"] == "high" for c in concerns)


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
        assert "No assets discovered" in captured.out
        assert "Tips" in captured.out

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

    def test_display_error_shows_api_error(self, handler, capsys):
        """display_error should identify API key errors."""
        log_content = "API key error"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "api" in captured.out.lower()
        finally:
            os.unlink(log_path)

    def test_display_done_shows_assets(self, handler, capsys):
        """display_done should show discovered assets."""
        parsed_data = {
            "emails": ["user@example.com"],
            "ips": ["192.168.1.10"],
            "asns": [],
            "urls": [],
            "subdomains": ["www.example.com"],
            "base_urls": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("theHarvester scan results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.theharvester_parser.parse_theharvester_output",
                return_value=parsed_data,
            ):
                job = {"target": "example.com"}
                handler.display_done(job, log_path)
                captured = capsys.readouterr()
                assert "DISCOVERED ASSETS" in captured.out
                assert "Emails" in captured.out
                assert "IP Addresses" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import theharvester_handler  # noqa: F401

        handler = registry.get_handler("theharvester")
        assert handler is not None
        assert handler.tool_name == "theharvester"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import theharvester_handler  # noqa: F401

        assert registry.has_warning_handler("theharvester") is True
        assert registry.has_error_handler("theharvester") is True
        assert registry.has_no_results_handler("theharvester") is True
        assert registry.has_done_handler("theharvester") is True
