#!/usr/bin/env python3
"""
Tests for the Enum4LinuxHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS, STATUS_WARNING
from souleyez.handlers.enum4linux_handler import Enum4LinuxHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return Enum4LinuxHandler()


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
        assert handler.tool_name == "enum4linux"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "enum4linux"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful enum4linux parsing."""

    def test_users_and_shares_detected(self, handler, mock_managers):
        """Discovered users and shares should be detected."""
        parsed_data = {
            "target": "192.168.1.10",
            "workgroup": "TESTDOMAIN",
            "domain_sid": "S-1-5-21-1234567890",
            "users": ["administrator", "guest", "testuser"],
            "groups": ["Domain Admins", "Domain Users"],
            "shares": [
                {
                    "name": "C$",
                    "type": "Disk",
                    "mapping": "OK",
                    "comment": "Default share",
                }
            ],
        }
        stats_data = {
            "total_shares": 1,
            "accessible_shares": 1,
            "writable_shares": 0,
            "workgroup": "TESTDOMAIN",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("[+] enum4linux results\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.enum4linux_parser.parse_enum4linux_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.enum4linux_parser.get_smb_stats",
                    return_value=stats_data,
                ):
                    with patch(
                        "souleyez.parsers.enum4linux_parser.categorize_share",
                        return_value="readable",
                    ):
                        with patch(
                            "souleyez.engine.result_handler.detect_tool_error",
                            return_value=None,
                        ):
                            job = {"target": "192.168.1.10"}
                            result = handler.parse_job(
                                1, log_path, job, **mock_managers
                            )

                            assert result["status"] == STATUS_DONE
                            assert result["users_found"] == 3
                            assert result["shares_found"] == 1
                            assert result["credentials_added"] == 3
        finally:
            os.unlink(log_path)

    def test_credentials_stored_in_database(self, handler, mock_managers):
        """Credentials should be stored in database."""
        parsed_data = {
            "target": "192.168.1.10",
            "users": ["admin"],
            "groups": [],
            "shares": [],
        }
        stats_data = {
            "total_shares": 0,
            "accessible_shares": 0,
            "writable_shares": 0,
            "workgroup": None,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("[+] enum4linux results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.enum4linux_parser.parse_enum4linux_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.enum4linux_parser.get_smb_stats",
                    return_value=stats_data,
                ):
                    with patch(
                        "souleyez.engine.result_handler.detect_tool_error",
                        return_value=None,
                    ):
                        job = {"target": "192.168.1.10"}
                        result = handler.parse_job(1, log_path, job, **mock_managers)

                        assert result["credentials_added"] == 1
                        mock_managers[
                            "credentials_manager"
                        ].add_credential.assert_called_once()
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_data_returns_no_results(self, handler, mock_managers):
        """No data should return no_results status."""
        parsed_data = {
            "target": "192.168.1.10",
            "users": [],
            "groups": [],
            "shares": [],
        }
        stats_data = {"total_shares": 0, "accessible_shares": 0, "writable_shares": 0}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("enum4linux scan - no results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.enum4linux_parser.parse_enum4linux_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.enum4linux_parser.get_smb_stats",
                    return_value=stats_data,
                ):
                    with patch(
                        "souleyez.engine.result_handler.detect_tool_error",
                        return_value=None,
                    ):
                        job = {"target": "192.168.1.10"}
                        result = handler.parse_job(1, log_path, job, **mock_managers)

                        assert result["status"] == STATUS_NO_RESULTS
        finally:
            os.unlink(log_path)


class TestParseJobWarning:
    """Test warning scenario (partial failure)."""

    def test_partial_error_returns_warning(self, handler, mock_managers):
        """Partial error should return warning status."""
        parsed_data = {
            "target": "192.168.1.10",
            "users": [],
            "groups": [],
            "shares": [],
        }
        stats_data = {"total_shares": 0, "accessible_shares": 0, "writable_shares": 0}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Some partial results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.enum4linux_parser.parse_enum4linux_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.enum4linux_parser.get_smb_stats",
                    return_value=stats_data,
                ):
                    with patch(
                        "souleyez.engine.result_handler.detect_tool_error",
                        return_value="Partial failure",
                    ):
                        job = {"target": "192.168.1.10"}
                        result = handler.parse_job(1, log_path, job, **mock_managers)

                        assert result["status"] == STATUS_WARNING
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
        assert "No SMB/Samba information discovered" in captured.out
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
        log_content = "NT_STATUS_ACCESS_DENIED"
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

    def test_display_done_shows_users_and_shares(self, handler, capsys):
        """display_done should show discovered users and shares."""
        parsed_data = {
            "target": "192.168.1.10",
            "workgroup": "TESTDOMAIN",
            "domain_sid": "S-1-5-21-1234567890",
            "users": ["administrator", "guest"],
            "groups": ["Domain Admins"],
            "shares": [
                {"name": "C$", "type": "Disk", "mapping": "OK", "comment": "Default"}
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("enum4linux scan results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.enum4linux_parser.parse_enum4linux_output",
                return_value=parsed_data,
            ):
                job = {"target": "192.168.1.10"}
                handler.display_done(job, log_path)
                captured = capsys.readouterr()
                assert "SMB/SAMBA ENUMERATION" in captured.out
                assert "192.168.1.10" in captured.out
                assert "Users Discovered" in captured.out
                assert "Groups Discovered" in captured.out
                assert "Shares Found" in captured.out
                assert "TESTDOMAIN" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import enum4linux_handler  # noqa: F401

        handler = registry.get_handler("enum4linux")
        assert handler is not None
        assert handler.tool_name == "enum4linux"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import enum4linux_handler  # noqa: F401

        assert registry.has_warning_handler("enum4linux") is True
        assert registry.has_error_handler("enum4linux") is True
        assert registry.has_no_results_handler("enum4linux") is True
        assert registry.has_done_handler("enum4linux") is True
