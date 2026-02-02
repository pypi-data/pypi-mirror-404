#!/usr/bin/env python3
"""
Tests for the KatanaHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS, STATUS_ERROR
from souleyez.handlers.katana_handler import KatanaHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return KatanaHandler()


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
        assert handler.tool_name == "katana"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "Katana"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful Katana parsing."""

    def test_urls_with_params_detected(self, handler, mock_managers):
        """URLs with parameters should be detected."""
        parsed_data = {
            "urls": [
                "http://example.com/search?q=test",
                "http://example.com/api/users",
                "http://example.com/login",
            ],
            "urls_with_params": ["http://example.com/search?q=test"],
            "forms_found": ["http://example.com/login"],
            "js_endpoints": ["http://example.com/api/users"],
            "unique_parameters": ["q"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(
                '{"request":{"endpoint":"http://example.com/search?q=test","method":"GET"}}\n'
            )
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.katana_parser.parse_katana_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value=None,
                ):
                    job = {"target": "http://example.com"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_DONE
                    assert result["urls_found"] == 3
                    assert (
                        len(result["urls_with_params"]) == 1
                    )  # Now a list for chaining
                    assert result["forms_found_count"] == 1
        finally:
            os.unlink(log_path)

    def test_injectable_urls_extracted(self, handler, mock_managers):
        """Injectable URLs should be extracted for chaining."""
        parsed_data = {
            "urls": [
                "http://example.com/search?q=test",
                "http://example.com/products?id=1",
            ],
            "urls_with_params": [
                "http://example.com/search?q=test",
                "http://example.com/products?id=1",
            ],
            "forms_found": [],
            "js_endpoints": [],
            "unique_parameters": ["q", "id"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("katana results\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.katana_parser.parse_katana_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.katana_parser.extract_injectable_urls",
                    return_value=[
                        "http://example.com/search?q=test",
                        "http://example.com/products?id=1",
                    ],
                ):
                    with patch(
                        "souleyez.engine.result_handler.detect_tool_error",
                        return_value=None,
                    ):
                        job = {"target": "http://example.com"}
                        result = handler.parse_job(1, log_path, job, **mock_managers)

                        assert "injectable_urls" in result
                        assert len(result["injectable_urls"]) == 2
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_urls_returns_no_results(self, handler, mock_managers):
        """No URLs discovered should return no_results status."""
        parsed_data = {
            "urls": [],
            "urls_with_params": [],
            "forms_found": [],
            "js_endpoints": [],
            "unique_parameters": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("katana crawl - no results\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.katana_parser.parse_katana_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value=None,
                ):
                    job = {"target": "http://example.com"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_NO_RESULTS
                    assert result["urls_found"] == 0
        finally:
            os.unlink(log_path)


class TestParseJobError:
    """Test error scenario."""

    def test_tool_error_returns_error_status(self, handler, mock_managers):
        """Tool error should return error status."""
        parsed_data = {
            "urls": [],
            "urls_with_params": [],
            "forms_found": [],
            "js_endpoints": [],
            "unique_parameters": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("failed to run command 'katana': No such file or directory\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.katana_parser.parse_katana_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value="No such file or directory",
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
        assert "No URLs" in captured.out or "no results" in captured.out.lower()
        assert "Tips" in captured.out

    def test_display_error_shows_not_installed(self, handler, capsys):
        """display_error should identify katana-not-installed errors."""
        log_content = "failed to run command 'katana': No such file or directory"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert (
                "not installed" in captured.out.lower()
                or "install" in captured.out.lower()
            )
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import katana_handler  # noqa: F401

        handler = registry.get_handler("katana")
        assert handler is not None
        assert handler.tool_name == "katana"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import katana_handler  # noqa: F401

        assert registry.has_warning_handler("katana") is True
        assert registry.has_error_handler("katana") is True
        assert registry.has_no_results_handler("katana") is True
        assert registry.has_done_handler("katana") is True
