#!/usr/bin/env python3
"""Tests for Evil-WinRM handler."""
import os
import tempfile

import pytest


class TestHandlerMetadata:
    """Test handler metadata and registration."""

    @pytest.fixture
    def handler(self):
        """Get Evil-WinRM handler instance."""
        from souleyez.handlers.evil_winrm_handler import EvilWinRMHandler

        return EvilWinRMHandler()

    def test_tool_name(self, handler):
        """Handler should have correct tool name."""
        assert handler.tool_name == "evil_winrm"

    def test_display_name(self, handler):
        """Handler should have correct display name."""
        assert handler.display_name == "Evil-WinRM"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags defined."""
        assert handler.has_error_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_no_results_handler is True
        assert handler.has_done_handler is True


class TestParseJobSuccess:
    """Test successful Evil-WinRM job parsing."""

    @pytest.fixture
    def handler(self):
        from souleyez.handlers.evil_winrm_handler import EvilWinRMHandler

        return EvilWinRMHandler()

    def test_success_detected(self, handler, tmp_path, monkeypatch):
        """parse_job should detect successful authentication."""
        # Mock the managers using the storage module where they're imported from
        monkeypatch.setattr("souleyez.storage.hosts.HostManager", MockHostManager)
        monkeypatch.setattr(
            "souleyez.storage.findings.FindingsManager", MockFindingsManager
        )

        log_content = """=== Evil-WinRM Session ===
Target: 192.168.1.10
Args: -u administrator -p password123
Started: 2026-01-22 08:00:00 UTC

Evil-WinRM shell v3.5

*Evil-WinRM* PS C:\\Users\\Administrator\\Documents> whoami
domain\\administrator
"""
        log_file = tmp_path / "evil_winrm.log"
        log_file.write_text(log_content)

        result = handler.parse_job(
            engagement_id=1,
            log_path=str(log_file),
            job={"target": "192.168.1.10", "args": "-u administrator -p password123"},
        )

        assert result["status"] == "done"
        assert result["success"] is True
        assert "administrator" in result.get("username", "")

    def test_command_output_extracted(self, handler, tmp_path, monkeypatch):
        """parse_job should extract command output."""
        monkeypatch.setattr("souleyez.storage.hosts.HostManager", MockHostManager)
        monkeypatch.setattr(
            "souleyez.storage.findings.FindingsManager", MockFindingsManager
        )

        log_content = """Evil-WinRM shell v3.5

*Evil-WinRM* PS C:\\Users\\admin> systeminfo

Host Name:                 WIN-SERVER
OS Name:                   Microsoft Windows Server 2019
"""
        log_file = tmp_path / "evil_winrm.log"
        log_file.write_text(log_content)

        result = handler.parse_job(
            engagement_id=1,
            log_path=str(log_file),
            job={"target": "192.168.1.10", "args": "-u admin -p pass -c systeminfo"},
        )

        assert result["status"] == "done"


class TestParseJobFailure:
    """Test failed Evil-WinRM job parsing."""

    @pytest.fixture
    def handler(self):
        from souleyez.handlers.evil_winrm_handler import EvilWinRMHandler

        return EvilWinRMHandler()

    def test_auth_failed_returns_error(self, handler, tmp_path):
        """parse_job should return error for authentication failure."""
        log_content = """=== Evil-WinRM Session ===
Target: 192.168.1.10

WinRM::WinRMAuthorizationError: Authorization failed
"""
        log_file = tmp_path / "evil_winrm.log"
        log_file.write_text(log_content)

        result = handler.parse_job(
            engagement_id=1, log_path=str(log_file), job={"target": "192.168.1.10"}
        )

        assert result["status"] == "error"
        assert (
            "auth" in result.get("error", "").lower()
            or "credential" in result.get("error", "").lower()
        )

    def test_connection_refused_returns_warning(self, handler, tmp_path):
        """parse_job should return warning for connection issues."""
        log_content = """=== Evil-WinRM Session ===
Target: 192.168.1.10

Connection refused - connect(2) for "192.168.1.10"
"""
        log_file = tmp_path / "evil_winrm.log"
        log_file.write_text(log_content)

        result = handler.parse_job(
            engagement_id=1, log_path=str(log_file), job={"target": "192.168.1.10"}
        )

        assert result["status"] == "warning"

    def test_timeout_returns_warning(self, handler, tmp_path):
        """parse_job should return warning for timeout."""
        log_content = """=== Evil-WinRM Session ===
Target: 192.168.1.10

Errno::ETIMEDOUT: Connection timed out
"""
        log_file = tmp_path / "evil_winrm.log"
        log_file.write_text(log_content)

        result = handler.parse_job(
            engagement_id=1, log_path=str(log_file), job={"target": "192.168.1.10"}
        )

        assert result["status"] == "warning"


class TestParseJobNoResults:
    """Test Evil-WinRM job with no clear results."""

    @pytest.fixture
    def handler(self):
        from souleyez.handlers.evil_winrm_handler import EvilWinRMHandler

        return EvilWinRMHandler()

    def test_no_shell_returns_no_results(self, handler, tmp_path):
        """parse_job should return no_results when no shell established."""
        log_content = """=== Evil-WinRM Session ===
Target: 192.168.1.10
Args: -u admin -p wrongpass

Completed: 2026-01-22 08:00:05 UTC
Exit Code: 1
"""
        log_file = tmp_path / "evil_winrm.log"
        log_file.write_text(log_content)

        result = handler.parse_job(
            engagement_id=1, log_path=str(log_file), job={"target": "192.168.1.10"}
        )

        assert result["status"] == "no_results"


class TestDisplayMethods:
    """Test handler display methods."""

    @pytest.fixture
    def handler(self):
        from souleyez.handlers.evil_winrm_handler import EvilWinRMHandler

        return EvilWinRMHandler()

    def test_display_done_exists(self, handler):
        """display_done method should exist."""
        assert hasattr(handler, "display_done")
        assert callable(handler.display_done)

    def test_display_error_exists(self, handler):
        """display_error method should exist."""
        assert hasattr(handler, "display_error")
        assert callable(handler.display_error)

    def test_display_warning_exists(self, handler):
        """display_warning method should exist."""
        assert hasattr(handler, "display_warning")
        assert callable(handler.display_warning)

    def test_display_no_results_exists(self, handler):
        """display_no_results method should exist."""
        assert hasattr(handler, "display_no_results")
        assert callable(handler.display_no_results)

    def test_display_done_output(self, handler, capsys, tmp_path):
        """display_done should show success message."""
        log_content = """Evil-WinRM shell v3.5
*Evil-WinRM* PS C:\\> whoami
admin
"""
        log_file = tmp_path / "evil_winrm.log"
        log_file.write_text(log_content)

        job = {"target": "192.168.1.10", "args": "-u admin -p pass"}
        handler.display_done(job, str(log_file))
        captured = capsys.readouterr()

        assert "evil-winrm" in captured.out.lower() or "shell" in captured.out.lower()

    def test_display_error_output(self, handler, capsys, tmp_path):
        """display_error should show error message."""
        log_content = "WinRM::WinRMAuthorizationError: bad credentials"
        log_file = tmp_path / "evil_winrm.log"
        log_file.write_text(log_content)

        job = {"target": "192.168.1.10"}
        handler.display_error(job, str(log_file))
        captured = capsys.readouterr()

        assert "error" in captured.out.lower() or "failed" in captured.out.lower()


class TestRegistryIntegration:
    """Test handler registration in registry."""

    def test_handler_discovered(self):
        """Handler should be discoverable by registry."""
        from souleyez.handlers.registry import get_handler

        handler = get_handler("evil_winrm")
        assert handler is not None
        assert handler.tool_name == "evil_winrm"

    def test_registry_reports_capabilities(self):
        """Handler should report capabilities."""
        from souleyez.handlers.registry import get_handler

        handler = get_handler("evil_winrm")
        assert handler is not None
        assert handler.has_done_handler is True
        assert handler.has_error_handler is True


# Mock classes for testing
class MockHostManager:
    def get_host_by_ip(self, engagement_id, ip):
        return {"id": 1, "ip": ip}

    def add_or_update_host(self, engagement_id, host_data):
        return {"id": 1, **host_data}


class MockFindingsManager:
    def add_finding(self, **kwargs):
        return 1
