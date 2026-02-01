#!/usr/bin/env python3
"""
Tests for the SMBMapHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS, STATUS_ERROR
from souleyez.handlers.smbmap_handler import SMBMapHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return SMBMapHandler()


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
        assert handler.tool_name == "smbmap"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "SMBMap"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful SMBMap parsing."""

    def test_shares_detected(self, handler, mock_managers):
        """Discovered SMB shares should be detected."""
        parsed_data = {
            "target": "192.168.1.10",
            "status": "Authenticated",
            "shares": [
                {
                    "name": "C$",
                    "permissions": "READ, WRITE",
                    "writable": True,
                    "readable": True,
                    "comment": "Default share",
                },
                {
                    "name": "IPC$",
                    "permissions": "NO ACCESS",
                    "writable": False,
                    "readable": False,
                    "comment": "",
                },
            ],
            "files": [],
        }
        findings_data = [
            {
                "title": "Writable share found",
                "severity": "high",
                "description": "C$ is writable",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("SMBMap results\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.smbmap_parser.parse_smbmap_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.smbmap_parser.extract_findings",
                    return_value=findings_data,
                ):
                    with patch(
                        "souleyez.storage.smb_shares.SMBSharesManager"
                    ) as mock_smb:
                        mock_smb.return_value.add_share.return_value = 1
                        with patch(
                            "souleyez.engine.result_handler.detect_tool_error",
                            return_value=None,
                        ):
                            job = {"target": "192.168.1.10"}
                            result = handler.parse_job(
                                1, log_path, job, **mock_managers
                            )

                            assert result["status"] == STATUS_DONE
                            assert result["shares_added"] == 2
                            assert result["findings_added"] == 1
        finally:
            os.unlink(log_path)

    def test_shares_stored_in_database(self, handler, mock_managers):
        """Shares should be stored in database."""
        parsed_data = {
            "target": "192.168.1.10",
            "shares": [
                {
                    "name": "share1",
                    "permissions": "READ",
                    "writable": False,
                    "readable": True,
                }
            ],
            "files": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("SMBMap results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.smbmap_parser.parse_smbmap_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.smbmap_parser.extract_findings", return_value=[]
                ):
                    with patch(
                        "souleyez.storage.smb_shares.SMBSharesManager"
                    ) as mock_smb:
                        mock_smb.return_value.add_share.return_value = 1
                        with patch(
                            "souleyez.engine.result_handler.detect_tool_error",
                            return_value=None,
                        ):
                            job = {"target": "192.168.1.10"}
                            result = handler.parse_job(
                                1, log_path, job, **mock_managers
                            )

                            assert result["shares_added"] == 1
                            mock_smb.return_value.add_share.assert_called_once()
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_shares_returns_no_results(self, handler, mock_managers):
        """No shares should return no_results status."""
        parsed_data = {"target": "192.168.1.10", "shares": [], "files": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("SMBMap scan - no shares")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.smbmap_parser.parse_smbmap_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.smbmap_parser.extract_findings", return_value=[]
                ):
                    with patch("souleyez.storage.smb_shares.SMBSharesManager"):
                        with patch(
                            "souleyez.engine.result_handler.detect_tool_error",
                            return_value=None,
                        ):
                            job = {"target": "192.168.1.10"}
                            result = handler.parse_job(
                                1, log_path, job, **mock_managers
                            )

                            assert result["status"] == STATUS_NO_RESULTS
        finally:
            os.unlink(log_path)


class TestParseJobError:
    """Test error scenario."""

    def test_tool_error_returns_error_status(self, handler, mock_managers):
        """Tool error should return error status."""
        parsed_data = {"target": "192.168.1.10", "shares": [], "files": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Connection refused")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.smbmap_parser.parse_smbmap_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.smbmap_parser.extract_findings", return_value=[]
                ):
                    with patch("souleyez.storage.smb_shares.SMBSharesManager"):
                        with patch(
                            "souleyez.engine.result_handler.detect_tool_error",
                            return_value="Connection failed",
                        ):
                            job = {"target": "192.168.1.10"}
                            result = handler.parse_job(
                                1, log_path, job, **mock_managers
                            )

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
        job = {"target": "192.168.1.10"}
        handler.display_no_results(job, "/fake/path")
        captured = capsys.readouterr()
        assert "No SMB shares found" in captured.out
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

    def test_display_error_shows_auth_failure(self, handler, capsys):
        """display_error should identify authentication errors."""
        log_content = "LOGON_FAILURE"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "authentication" in captured.out.lower()
        finally:
            os.unlink(log_path)

    def test_display_error_shows_access_denied(self, handler, capsys):
        """display_error should identify access denied errors."""
        log_content = "Access denied"
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

    def test_display_done_shows_shares(self, handler, capsys):
        """display_done should show discovered shares."""
        parsed_data = {
            "target": "192.168.1.10",
            "status": "Authenticated",
            "shares": [
                {
                    "name": "C$",
                    "permissions": "READ, WRITE",
                    "writable": True,
                    "readable": True,
                    "comment": "Default",
                },
                {
                    "name": "Users",
                    "permissions": "READ",
                    "writable": False,
                    "readable": True,
                    "comment": "",
                },
                {
                    "name": "IPC$",
                    "permissions": "NO ACCESS",
                    "writable": False,
                    "readable": False,
                    "comment": "",
                },
            ],
            "files": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("SMBMap scan results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.smbmap_parser.parse_smbmap_output",
                return_value=parsed_data,
            ):
                job = {"target": "192.168.1.10"}
                handler.display_done(job, log_path)
                captured = capsys.readouterr()
                assert "SMB SHARE ENUMERATION" in captured.out
                assert "192.168.1.10" in captured.out
                assert "Writable Shares" in captured.out
                assert "Readable Shares" in captured.out
                assert "C$" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import smbmap_handler  # noqa: F401

        handler = registry.get_handler("smbmap")
        assert handler is not None
        assert handler.tool_name == "smbmap"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import smbmap_handler  # noqa: F401

        assert registry.has_warning_handler("smbmap") is True
        assert registry.has_error_handler("smbmap") is True
        assert registry.has_no_results_handler("smbmap") is True
        assert registry.has_done_handler("smbmap") is True
