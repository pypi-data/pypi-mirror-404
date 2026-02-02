#!/usr/bin/env python3
"""
Tests for the HydraHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS, STATUS_WARNING
from souleyez.handlers.hydra_handler import HydraHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return HydraHandler()


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


class TestHandlerMetadata:
    """Test handler metadata."""

    def test_tool_name(self, handler):
        """Handler should have correct tool name."""
        assert handler.tool_name == "hydra"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "Hydra"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful credential parsing."""

    def test_credentials_detected(self, handler, mock_managers):
        """Valid credentials should be detected and stored."""
        log_content = """
Hydra v9.5 (c) 2023 by van Hauser/THC
[DATA] attacking ssh://192.168.1.10:22/
[22][ssh] host: 192.168.1.10   login: admin   password: password123
[STATUS] attack finished for 192.168.1.10 (valid pair found)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error", return_value=None
            ):
                job = {"target": "192.168.1.10"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_DONE
                assert result["credentials_found"] == 1
                assert "valid credential" in result["summary"].lower()
        finally:
            os.unlink(log_path)

    def test_multiple_credentials(self, handler, mock_managers):
        """Multiple credentials should all be detected."""
        log_content = """
[22][ssh] host: 192.168.1.10   login: admin   password: password123
[22][ssh] host: 192.168.1.10   login: root   password: toor
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error", return_value=None
            ):
                job = {"target": "192.168.1.10"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_DONE
                assert result["credentials_found"] == 2
        finally:
            os.unlink(log_path)

    def test_usernames_detected(self, handler, mock_managers):
        """Username enumeration should be detected."""
        log_content = """
[DATA] attacking http-post-form://192.168.1.10:80/wp-login.php
[80][http-post-form] host: 192.168.1.10   login: admin   password: wrongpass
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error", return_value=None
            ):
                job = {"target": "192.168.1.10"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                # The parser detects this as WordPress without wp-admin redirect
                # so it's username enumeration, not full creds
                assert result["status"] in [STATUS_DONE, STATUS_NO_RESULTS]
        finally:
            os.unlink(log_path)


class TestParseJobFailure:
    """Test failed attack parsing."""

    def test_connection_refused_returns_warning(self, handler, mock_managers):
        """Connection refused should return warning status."""
        log_content = """
[ERROR] Can not connect to 192.168.1.10 (Connection refused)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error",
                return_value="Connection refused",
            ):
                job = {"target": "192.168.1.10"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_WARNING
                assert "refused" in result["summary"].lower()
        finally:
            os.unlink(log_path)

    def test_connection_timeout_returns_warning(self, handler, mock_managers):
        """Connection timeout should return warning status."""
        log_content = """
[ERROR] Connection timed out
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error",
                return_value="Connection timed out",
            ):
                job = {"target": "192.168.1.10"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_WARNING
                assert "timed out" in result["summary"].lower()
        finally:
            os.unlink(log_path)

    def test_no_route_returns_warning(self, handler, mock_managers):
        """No route to host should return warning status."""
        log_content = """
[ERROR] No route to host
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error",
                return_value="No route to host",
            ):
                job = {"target": "192.168.1.10"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_WARNING
                assert "no route" in result["summary"].lower()
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_credentials_returns_no_results(self, handler, mock_managers):
        """No credentials found should return no_results."""
        log_content = """
Hydra v9.5 (c) 2023 by van Hauser/THC
[DATA] attacking ssh://192.168.1.10:22/
[STATUS] attack finished for 192.168.1.10 (0 valid passwords found)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error", return_value=None
            ):
                job = {"target": "192.168.1.10"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert result["status"] == STATUS_NO_RESULTS
                assert "no valid" in result["summary"].lower()
        finally:
            os.unlink(log_path)


class TestParseJobDatabaseWrites:
    """Test that database writes happen correctly."""

    def test_credentials_added_to_database(self, handler, mock_managers):
        """Credentials should be added to the database."""
        log_content = """
[22][ssh] host: 192.168.1.10   login: admin   password: secret123
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error", return_value=None
            ):
                job = {"target": "192.168.1.10"}
                handler.parse_job(1, log_path, job, **mock_managers)

                # Verify credentials_manager.add_credential was called
                mock_managers["credentials_manager"].add_credential.assert_called()
                call_kwargs = mock_managers[
                    "credentials_manager"
                ].add_credential.call_args[1]
                assert call_kwargs["username"] == "admin"
                assert call_kwargs["password"] == "secret123"
                assert call_kwargs["tool"] == "hydra"
        finally:
            os.unlink(log_path)

    def test_findings_created_for_credentials(self, handler, mock_managers):
        """Findings should be created when credentials are found."""
        log_content = """
[22][ssh] host: 192.168.1.10   login: admin   password: secret123
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            with patch(
                "souleyez.engine.result_handler.detect_tool_error", return_value=None
            ):
                job = {"target": "192.168.1.10"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                # Verify findings_manager.add_finding was called
                mock_managers["findings_manager"].add_finding.assert_called()
                assert result["findings_added"] >= 1
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
        job = {"parse_result": {"summary": "Target unreachable (connection refused)"}}
        handler.display_warning(job, "/fake/path")
        captured = capsys.readouterr()
        assert "connection refused" in captured.out.lower()

    def test_display_no_results_shows_tips(self, handler, capsys):
        """display_no_results should show helpful tips."""
        job = {"target": "192.168.1.10"}
        handler.display_no_results(job, "/fake/path")
        captured = capsys.readouterr()
        assert "No valid credentials found" in captured.out
        assert "Tips" in captured.out

    def test_display_error_shows_common_errors(self, handler, capsys):
        """display_error should identify common error messages."""
        log_content = "Connection refused"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "Connection refused" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()  # Clear any cached state

        # Force reimport to trigger discovery
        from souleyez.handlers import hydra_handler  # noqa: F401

        handler = registry.get_handler("hydra")
        assert handler is not None
        assert handler.tool_name == "hydra"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import hydra_handler  # noqa: F401

        assert registry.has_warning_handler("hydra") is True
        assert registry.has_error_handler("hydra") is True
        assert registry.has_no_results_handler("hydra") is True
        assert registry.has_done_handler("hydra") is True
