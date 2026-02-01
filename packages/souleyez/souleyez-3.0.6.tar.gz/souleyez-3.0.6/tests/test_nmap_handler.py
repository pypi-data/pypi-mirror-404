#!/usr/bin/env python3
"""
Tests for the NmapHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS, STATUS_ERROR
from souleyez.handlers.nmap_handler import NmapHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return NmapHandler()


@pytest.fixture
def mock_managers():
    """Mock database managers."""
    host_manager = MagicMock()
    findings_manager = MagicMock()
    credentials_manager = MagicMock()

    # Default: host exists and import succeeds
    host_manager.get_host_by_ip.return_value = {"id": 1}
    host_manager.add_or_update_host.return_value = {"id": 1}
    host_manager.import_nmap_results.return_value = {
        "hosts_added": 1,
        "services_added": 3,
    }
    host_manager.get_host_services.return_value = []

    return {
        "host_manager": host_manager,
        "findings_manager": findings_manager,
        "credentials_manager": credentials_manager,
    }


class TestHandlerMetadata:
    """Test handler metadata."""

    def test_tool_name(self, handler):
        """Handler should have correct tool name."""
        assert handler.tool_name == "nmap"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "Nmap"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful nmap parsing."""

    def test_hosts_detected(self, handler, mock_managers):
        """Discovered hosts should be detected."""
        parsed_data = {
            "hosts": [
                {
                    "ip": "192.168.1.10",
                    "status": "up",
                    "hostname": "target.local",
                    "services": [
                        {
                            "port": 22,
                            "protocol": "tcp",
                            "state": "open",
                            "service": "ssh",
                            "version": "OpenSSH 8.2",
                        },
                        {
                            "port": 80,
                            "protocol": "tcp",
                            "state": "open",
                            "service": "http",
                            "version": "Apache 2.4",
                        },
                        {
                            "port": 443,
                            "protocol": "tcp",
                            "state": "open",
                            "service": "https",
                        },
                    ],
                }
            ],
            "vulnerabilities": [],
            "info_scripts": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(
                "Nmap scan report for 192.168.1.10\n22/tcp open ssh\n80/tcp open http\n443/tcp open https"
            )
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nmap_parser.parse_nmap_log", return_value=parsed_data
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value=None,
                ):
                    with patch("souleyez.core.cve_matcher.CVEMatcher") as mock_cve:
                        mock_cve.return_value.parse_nmap_service.return_value = []
                        mock_cve.return_value.scan_for_common_issues.return_value = []

                        job = {"target": "192.168.1.10"}
                        result = handler.parse_job(1, log_path, job, **mock_managers)

                        assert result["status"] == STATUS_DONE
                        assert result["hosts_added"] == 1
                        assert result["services_added"] == 3
        finally:
            os.unlink(log_path)

    def test_services_collected_for_chaining(self, handler, mock_managers):
        """Services should be collected for tool chaining."""
        parsed_data = {
            "hosts": [
                {
                    "ip": "192.168.1.10",
                    "status": "up",
                    "services": [
                        {
                            "port": 22,
                            "protocol": "tcp",
                            "state": "open",
                            "service": "ssh",
                        },
                        {
                            "port": 445,
                            "protocol": "tcp",
                            "state": "open",
                            "service": "microsoft-ds",
                        },
                    ],
                }
            ],
            "vulnerabilities": [],
            "info_scripts": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Nmap scan report")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nmap_parser.parse_nmap_log", return_value=parsed_data
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value=None,
                ):
                    with patch("souleyez.core.cve_matcher.CVEMatcher") as mock_cve:
                        mock_cve.return_value.parse_nmap_service.return_value = []
                        mock_cve.return_value.scan_for_common_issues.return_value = []

                        job = {"target": "192.168.1.10"}
                        result = handler.parse_job(1, log_path, job, **mock_managers)

                        assert len(result["services"]) == 2
                        assert result["services"][0]["port"] == 22
                        assert result["services"][1]["port"] == 445
        finally:
            os.unlink(log_path)

    def test_discovery_scan_detected(self, handler, mock_managers):
        """Discovery scan flag should be set based on args."""
        parsed_data = {
            "hosts": [{"ip": "192.168.1.10", "status": "up", "services": []}],
            "vulnerabilities": [],
            "info_scripts": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Nmap ping sweep")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nmap_parser.parse_nmap_log", return_value=parsed_data
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value=None,
                ):
                    with patch("souleyez.core.cve_matcher.CVEMatcher") as mock_cve:
                        mock_cve.return_value.parse_nmap_service.return_value = []
                        mock_cve.return_value.scan_for_common_issues.return_value = []

                        job = {"target": "192.168.1.0/24", "args": ["-sn"]}
                        result = handler.parse_job(1, log_path, job, **mock_managers)

                        assert result["is_discovery"] is True
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_hosts_returns_no_results(self, handler, mock_managers):
        """No hosts up should return no_results."""
        parsed_data = {"hosts": [], "vulnerabilities": [], "info_scripts": []}
        mock_managers["host_manager"].import_nmap_results.return_value = {
            "hosts_added": 0,
            "services_added": 0,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("All 1000 scanned ports are closed")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nmap_parser.parse_nmap_log", return_value=parsed_data
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value=None,
                ):
                    job = {"target": "192.168.1.10"}
                    result = handler.parse_job(1, log_path, job, **mock_managers)

                    assert result["status"] == STATUS_NO_RESULTS
                    assert result["hosts_added"] == 0
        finally:
            os.unlink(log_path)


class TestParseJobError:
    """Test error scenario."""

    def test_parse_error_returns_error(self, handler, mock_managers):
        """Parse error should return error dict."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Failed to resolve")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nmap_parser.parse_nmap_log",
                return_value={"error": "Parse failed"},
            ):
                job = {"target": "192.168.1.10"}
                result = handler.parse_job(1, log_path, job, **mock_managers)

                assert "error" in result
        finally:
            os.unlink(log_path)

    def test_tool_error_detected(self, handler, mock_managers):
        """Tool error should return error status."""
        parsed_data = {
            "hosts": [{"ip": "192.168.1.10", "status": "up", "services": []}],
            "vulnerabilities": [],
            "info_scripts": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("requires root privileges")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nmap_parser.parse_nmap_log", return_value=parsed_data
            ):
                with patch(
                    "souleyez.engine.result_handler.detect_tool_error",
                    return_value="Permission denied",
                ):
                    with patch("souleyez.core.cve_matcher.CVEMatcher") as mock_cve:
                        mock_cve.return_value.parse_nmap_service.return_value = []
                        mock_cve.return_value.scan_for_common_issues.return_value = []

                        job = {"target": "192.168.1.10"}
                        result = handler.parse_job(1, log_path, job, **mock_managers)

                        assert result["status"] == STATUS_ERROR
        finally:
            os.unlink(log_path)


class TestSecurityConcerns:
    """Test security concern detection."""

    def test_risky_ports_detected(self, handler):
        """Risky ports should be identified as security concerns."""
        hosts = [
            {
                "ip": "192.168.1.10",
                "services": [
                    {"port": 23, "state": "open", "service": "telnet"},
                    {"port": 445, "state": "open", "service": "microsoft-ds"},
                    {"port": 3389, "state": "open", "service": "ms-wbt-server"},
                ],
            }
        ]
        concerns = handler._identify_security_concerns(hosts)

        assert len(concerns) == 3
        services = [c["service"] for c in concerns]
        assert "Telnet" in services
        assert "SMB" in services
        assert "RDP" in services

    def test_vnc_on_nonstandard_port_detected(self, handler):
        """VNC on non-standard port should be detected."""
        hosts = [
            {
                "ip": "192.168.1.10",
                "services": [
                    {"port": 5910, "state": "open", "service": "vnc"},
                ],
            }
        ]
        concerns = handler._identify_security_concerns(hosts)

        assert len(concerns) == 1
        assert concerns[0]["service"] == "VNC"

    def test_closed_ports_not_flagged(self, handler):
        """Closed ports should not be flagged as concerns."""
        hosts = [
            {
                "ip": "192.168.1.10",
                "services": [
                    {"port": 23, "state": "closed", "service": "telnet"},
                    {"port": 445, "state": "filtered", "service": "microsoft-ds"},
                ],
            }
        ]
        concerns = handler._identify_security_concerns(hosts)

        assert len(concerns) == 0


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
        assert "No open ports" in captured.out
        assert "This could mean" in captured.out

    def test_display_error_shows_permission_error(self, handler, capsys):
        """display_error should identify permission errors."""
        log_content = "requires root privileges"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "root privileges" in captured.out.lower()
        finally:
            os.unlink(log_path)

    def test_display_error_shows_timeout(self, handler, capsys):
        """display_error should identify timeout errors."""
        log_content = "Scan timed out"
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

    def test_display_done_shows_services(self, handler, capsys):
        """display_done should show discovered services."""
        parsed_data = {
            "hosts": [
                {
                    "ip": "192.168.1.10",
                    "status": "up",
                    "services": [
                        {
                            "port": 22,
                            "protocol": "tcp",
                            "state": "open",
                            "service": "ssh",
                        },
                        {
                            "port": 80,
                            "protocol": "tcp",
                            "state": "open",
                            "service": "http",
                        },
                    ],
                }
            ],
            "vulnerabilities": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Nmap scan report")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nmap_parser.parse_nmap_output",
                return_value=parsed_data,
            ):
                job = {"target": "192.168.1.10"}
                handler.display_done(job, log_path)
                captured = capsys.readouterr()
                assert "DISCOVERED SERVICES" in captured.out
                assert "192.168.1.10" in captured.out
        finally:
            os.unlink(log_path)

    def test_display_done_shows_vulnerabilities(self, handler, capsys):
        """display_done should show vulnerabilities when found."""
        parsed_data = {
            "hosts": [],
            "vulnerabilities": [
                {
                    "host_ip": "192.168.1.10",
                    "port": 445,
                    "title": "MS17-010 EternalBlue",
                    "state": "VULNERABLE",
                    "cvss_score": 9.8,
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Nmap scan report with vulns")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.nmap_parser.parse_nmap_output",
                return_value=parsed_data,
            ):
                job = {"target": "192.168.1.10"}
                handler.display_done(job, log_path, show_all=True)
                captured = capsys.readouterr()
                assert "VULNERABILITY SCAN RESULTS" in captured.out
                assert "CRITICAL" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import nmap_handler  # noqa: F401

        handler = registry.get_handler("nmap")
        assert handler is not None
        assert handler.tool_name == "nmap"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import nmap_handler  # noqa: F401

        assert registry.has_warning_handler("nmap") is True
        assert registry.has_error_handler("nmap") is True
        assert registry.has_no_results_handler("nmap") is True
        assert registry.has_done_handler("nmap") is True
