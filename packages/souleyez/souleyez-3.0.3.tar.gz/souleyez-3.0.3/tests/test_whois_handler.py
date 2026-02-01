#!/usr/bin/env python3
"""
Tests for the WhoisHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS
from souleyez.handlers.whois_handler import WhoisHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return WhoisHandler()


@pytest.fixture
def mock_managers():
    """Mock database managers."""
    host_manager = MagicMock()
    findings_manager = MagicMock()
    credentials_manager = MagicMock()

    return {
        "host_manager": host_manager,
        "findings_manager": findings_manager,
        "credentials_manager": credentials_manager,
    }


class TestHandlerMetadata:
    """Test handler metadata."""

    def test_tool_name(self, handler):
        """Handler should have correct tool name."""
        assert handler.tool_name == "whois"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "WHOIS"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful whois parsing."""

    def test_domain_info_detected(self, handler, mock_managers):
        """Domain registration info should be detected."""
        parsed_data = {
            "domain": "example.com",
            "registrar": "Example Registrar Inc.",
            "dates": {"created": "2000-01-01", "expires": "2025-01-01"},
            "nameservers": ["ns1.example.com", "ns2.example.com"],
        }
        osint_record = {
            "data_type": "domain",
            "target": "example.com",
            "source": "whois",
            "summary": "Domain info",
            "content": "test",
            "metadata": {},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Domain Name: example.com\nRegistrar: Example Registrar Inc.\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.whois_parser.parse_whois_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.whois_parser.map_to_osint_data",
                    return_value=osint_record,
                ):
                    with patch(
                        "souleyez.parsers.whois_parser.extract_emails",
                        return_value=["admin@example.com"],
                    ):
                        with patch("souleyez.storage.osint.OsintManager") as mock_osint:
                            mock_osint_instance = MagicMock()
                            mock_osint.return_value = mock_osint_instance
                            mock_osint_instance.bulk_add_osint_data.return_value = 1

                            job = {"target": "example.com"}
                            result = handler.parse_job(
                                1, log_path, job, **mock_managers
                            )

                            assert result["status"] == STATUS_DONE
                            assert result["registrar"] == "Example Registrar Inc."
                            assert result["nameservers"] == 2
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_domain_info_returns_no_results(self, handler, mock_managers):
        """No domain info should return no_results status."""
        parsed_data = {
            "domain": None,
            "registrar": None,
            "dates": {},
            "nameservers": [],
        }
        osint_record = {
            "data_type": "domain",
            "target": "unknown.tld",
            "source": "whois",
            "summary": "",
            "content": "",
            "metadata": {},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("No match for domain")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.whois_parser.parse_whois_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.whois_parser.map_to_osint_data",
                    return_value=osint_record,
                ):
                    with patch(
                        "souleyez.parsers.whois_parser.extract_emails", return_value=[]
                    ):
                        with patch("souleyez.storage.osint.OsintManager"):
                            job = {"target": "unknown.tld"}
                            result = handler.parse_job(
                                1, log_path, job, **mock_managers
                            )

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
        job = {"target": "example.com"}
        handler.display_no_results(job, "/fake/path")
        captured = capsys.readouterr()
        assert "No WHOIS information found" in captured.out
        assert "Tips" in captured.out

    def test_display_error_shows_not_found(self, handler, capsys):
        """display_error should identify not found errors."""
        log_content = "No match for domain"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "Domain not found" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import whois_handler  # noqa: F401

        handler = registry.get_handler("whois")
        assert handler is not None
        assert handler.tool_name == "whois"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import whois_handler  # noqa: F401

        assert registry.has_warning_handler("whois") is True
        assert registry.has_error_handler("whois") is True
        assert registry.has_no_results_handler("whois") is True
        assert registry.has_done_handler("whois") is True
