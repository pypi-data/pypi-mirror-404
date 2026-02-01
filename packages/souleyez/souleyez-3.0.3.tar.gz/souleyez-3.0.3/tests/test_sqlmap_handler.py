#!/usr/bin/env python3
"""
Tests for the SQLMapHandler.

Tests parsing accuracy and display functionality.
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS, STATUS_ERROR
from souleyez.handlers.sqlmap_handler import SQLMapHandler


@pytest.fixture
def handler():
    """Provide a fresh handler instance."""
    return SQLMapHandler()


@pytest.fixture
def mock_managers():
    """Mock database managers."""
    host_manager = MagicMock()
    findings_manager = MagicMock()
    credentials_manager = MagicMock()

    # Default: host exists
    host_manager.get_host_by_ip.return_value = {"id": 1}
    host_manager.add_or_update_host.return_value = 1
    host_manager.list_hosts.return_value = []
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
        assert handler.tool_name == "sqlmap"

    def test_display_name(self, handler):
        """Handler should have human-readable display name."""
        assert handler.display_name == "SQLMap"

    def test_capability_flags(self, handler):
        """Handler should have all capability flags enabled."""
        assert handler.has_done_handler is True
        assert handler.has_warning_handler is True
        assert handler.has_error_handler is True
        assert handler.has_no_results_handler is True


class TestParseJobSuccess:
    """Test successful SQLMap parsing."""

    def test_sqli_detected(self, handler, mock_managers):
        """Discovered SQL injection should be detected."""
        parsed_data = {
            "target_url": "http://example.com/page.php?id=1",
            "dbms": "MySQL",
            "vulnerabilities": [
                {
                    "parameter": "id",
                    "vuln_type": "sqli",
                    "injectable": True,
                    "description": "SQL injection in id parameter",
                    "technique": "boolean-based blind",
                }
            ],
            "databases": ["mysql", "information_schema", "testdb"],
            "tables": {"testdb": ["users", "orders"]},
            "injection_techniques": [],
        }
        stats_data = {
            "total_vulns": 1,
            "sqli_confirmed": 1,
            "databases_found": 3,
            "xss_possible": 0,
            "fi_possible": 0,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("SQLMap results\n")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.sqlmap_parser.parse_sqlmap_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.sqlmap_parser.get_sqli_stats",
                    return_value=stats_data,
                ):
                    with patch("souleyez.storage.sqlmap_data.SQLMapDataManager"):
                        with patch(
                            "souleyez.engine.result_handler.detect_tool_error",
                            return_value=None,
                        ):
                            job = {"target": "http://example.com/page.php?id=1"}
                            result = handler.parse_job(
                                1, log_path, job, **mock_managers
                            )

                            assert result["status"] == STATUS_DONE
                            assert result["sqli_confirmed"] == 1
                            assert result["databases_found"] == 3
        finally:
            os.unlink(log_path)

    def test_findings_stored_in_database(self, handler, mock_managers):
        """Findings should be stored in database."""
        parsed_data = {
            "target_url": "http://example.com/page.php?id=1",
            "vulnerabilities": [
                {
                    "parameter": "id",
                    "vuln_type": "sqli",
                    "injectable": True,
                    "description": "SQL injection",
                }
            ],
            "databases": [],
            "tables": {},
        }
        stats_data = {
            "total_vulns": 1,
            "sqli_confirmed": 1,
            "databases_found": 0,
            "xss_possible": 0,
            "fi_possible": 0,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("SQLMap results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.sqlmap_parser.parse_sqlmap_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.sqlmap_parser.get_sqli_stats",
                    return_value=stats_data,
                ):
                    with patch("souleyez.storage.sqlmap_data.SQLMapDataManager"):
                        with patch(
                            "souleyez.engine.result_handler.detect_tool_error",
                            return_value=None,
                        ):
                            job = {"target": "http://example.com/page.php?id=1"}
                            result = handler.parse_job(
                                1, log_path, job, **mock_managers
                            )

                            assert result["findings_added"] >= 1
                            mock_managers[
                                "findings_manager"
                            ].add_finding.assert_called()
        finally:
            os.unlink(log_path)


class TestParseJobNoResults:
    """Test no results scenario."""

    def test_no_sqli_returns_no_results(self, handler, mock_managers):
        """No SQL injection should return no_results status."""
        parsed_data = {
            "target_url": "http://example.com/page.php?id=1",
            "vulnerabilities": [],
            "databases": [],
            "tables": {},
        }
        stats_data = {
            "total_vulns": 0,
            "sqli_confirmed": 0,
            "databases_found": 0,
            "xss_possible": 0,
            "fi_possible": 0,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("SQLMap scan - no findings")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.sqlmap_parser.parse_sqlmap_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.sqlmap_parser.get_sqli_stats",
                    return_value=stats_data,
                ):
                    with patch("souleyez.storage.sqlmap_data.SQLMapDataManager"):
                        with patch(
                            "souleyez.engine.result_handler.detect_tool_error",
                            return_value=None,
                        ):
                            job = {"target": "http://example.com/page.php?id=1"}
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
        parsed_data = {
            "target_url": "http://example.com/page.php?id=1",
            "vulnerabilities": [],
            "databases": [],
            "tables": {},
        }
        stats_data = {"total_vulns": 0, "sqli_confirmed": 0, "databases_found": 0}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("Connection timed out")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.sqlmap_parser.parse_sqlmap_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.sqlmap_parser.get_sqli_stats",
                    return_value=stats_data,
                ):
                    with patch("souleyez.storage.sqlmap_data.SQLMapDataManager"):
                        with patch(
                            "souleyez.engine.result_handler.detect_tool_error",
                            return_value="Connection failed",
                        ):
                            job = {"target": "http://example.com/page.php?id=1"}
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
        job = {"target": "http://example.com/page.php?id=1"}
        handler.display_no_results(job, "/fake/path")
        captured = capsys.readouterr()
        assert "No SQL injection vulnerabilities found" in captured.out
        assert "Tips" in captured.out

    def test_display_error_shows_timeout(self, handler, capsys):
        """display_error should identify timeout errors."""
        log_content = "connection timed out"
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

    def test_display_error_shows_waf(self, handler, capsys):
        """display_error should identify actual WAF blocks, not heuristic checks."""
        log_content = "blocked by WAF/IPS"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "waf" in captured.out.lower()
        finally:
            os.unlink(log_path)

    def test_display_error_shows_404(self, handler, capsys):
        """display_error should identify 404 errors."""
        log_content = "page not found 404"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            log_path = f.name

        try:
            job = {}
            handler.display_error(job, log_path)
            captured = capsys.readouterr()
            assert "404" in captured.out
        finally:
            os.unlink(log_path)

    def test_display_done_shows_sqli(self, handler, capsys):
        """display_done should show discovered SQL injection."""
        parsed_data = {
            "target_url": "http://example.com/page.php?id=1",
            "dbms": "MySQL",
            "web_server_os": "Linux",
            "web_app_technology": ["PHP", "Apache"],
            "injection_techniques": [
                {
                    "parameter": "id",
                    "method": "GET",
                    "techniques": [
                        {
                            "type": "boolean-based blind",
                            "title": "Test",
                            "payload": "id=1 AND 1=1",
                        }
                    ],
                }
            ],
            "databases": ["mysql", "testdb"],
            "tables": {"testdb": ["users"]},
            "dumped_data": {},
        }
        stats_data = {
            "total_vulns": 1,
            "sqli_confirmed": 1,
            "databases_found": 2,
            "xss_possible": 0,
            "fi_possible": 0,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("SQLMap scan results")
            log_path = f.name

        try:
            with patch(
                "souleyez.parsers.sqlmap_parser.parse_sqlmap_output",
                return_value=parsed_data,
            ):
                with patch(
                    "souleyez.parsers.sqlmap_parser.get_sqli_stats",
                    return_value=stats_data,
                ):
                    job = {"target": "http://example.com/page.php?id=1"}
                    handler.display_done(job, log_path)
                    captured = capsys.readouterr()
                    assert "SQL INJECTION SCAN" in captured.out
                    assert "vulnerability" in captured.out.lower()
                    assert "MySQL" in captured.out
                    assert "Databases Enumerated" in captured.out
        finally:
            os.unlink(log_path)


class TestRegistryIntegration:
    """Test that handler is discovered by registry."""

    def test_handler_discovered(self):
        """Handler should be discovered by registry."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import sqlmap_handler  # noqa: F401

        handler = registry.get_handler("sqlmap")
        assert handler is not None
        assert handler.tool_name == "sqlmap"

    def test_registry_reports_capabilities(self):
        """Registry should report handler capabilities correctly."""
        from souleyez.handlers.registry import get_registry

        registry = get_registry()
        registry.reset()

        from souleyez.handlers import sqlmap_handler  # noqa: F401

        assert registry.has_warning_handler("sqlmap") is True
        assert registry.has_error_handler("sqlmap") is True
        assert registry.has_no_results_handler("sqlmap") is True
        assert registry.has_done_handler("sqlmap") is True


class TestUsernameValidation:
    """Test username validation to filter scanner garbage."""

    def test_valid_usernames_accepted(self, handler):
        """Legitimate usernames should be accepted."""
        valid_usernames = [
            "admin",
            "john.doe",
            "user123",
            "jane_doe",
            "test",
            "blade",
            "tibi",
            "user@example.com",
            "first.last@company.org",
        ]
        for username in valid_usernames:
            assert (
                handler._is_valid_username(username) is True
            ), f"Should accept: {username}"

    def test_scanner_artifacts_rejected(self, handler):
        """Scanner tool signatures should be rejected."""
        scanner_artifacts = [
            '"+netsparker(0x001DF8)+"',
            "acunetix_test",
            "burpsuite_probe",
        ]
        for artifact in scanner_artifacts:
            assert (
                handler._is_valid_username(artifact) is False
            ), f"Should reject: {artifact}"

    def test_injection_payloads_rejected(self, handler):
        """Injection payloads should be rejected."""
        payloads = [
            "{{ 268409241- 16102 }}",
            "${7*7}",
            "<%=7*7%>",
            "' OR 1=1 --",
            "1'='1",
            "' UNION SELECT",
        ]
        for payload in payloads:
            assert (
                handler._is_valid_username(payload) is False
            ), f"Should reject: {payload}"

    def test_path_patterns_rejected(self, handler):
        """Path traversal patterns should be rejected."""
        paths = [
            "/etc/passwd",
            "..\\..\\etc\\passwd",
            "file:///etc/passwd",
            "test.asp",
            "page.axd",
        ]
        for path in paths:
            assert handler._is_valid_username(path) is False, f"Should reject: {path}"

    def test_command_injection_rejected(self, handler):
        """Command injection attempts should be rejected."""
        commands = [
            "& ping -n 25 127.0.0.1 &",
            "| whoami",
            "$(whoami)",
            "`id`",
        ]
        for cmd in commands:
            assert handler._is_valid_username(cmd) is False, f"Should reject: {cmd}"

    def test_url_encoded_payloads_rejected(self, handler):
        """URL-encoded payloads should be rejected."""
        encoded = [
            "%27",  # Single quote
            "%22",  # Double quote
            "%3cscript%3e",  # XSS
        ]
        for enc in encoded:
            assert handler._is_valid_username(enc) is False, f"Should reject: {enc}"

    def test_special_char_boundaries_rejected(self, handler):
        """Values starting/ending with injection chars should be rejected."""
        boundary_cases = [
            '"admin',
            "admin'",
            "(select)",
            "admin;",
        ]
        for case in boundary_cases:
            assert handler._is_valid_username(case) is False, f"Should reject: {case}"

    def test_long_usernames_rejected(self, handler):
        """Excessively long usernames should be rejected."""
        long_username = "a" * 101
        assert handler._is_valid_username(long_username) is False

    def test_empty_rejected(self, handler):
        """Empty usernames should be rejected."""
        assert handler._is_valid_username("") is False
        assert handler._is_valid_username(None) is False
