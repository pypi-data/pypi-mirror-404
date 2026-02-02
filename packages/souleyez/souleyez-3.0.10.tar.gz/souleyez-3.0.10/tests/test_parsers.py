#!/usr/bin/env python3
"""
Parser regression tests.

Each test case represents a bug that was found and fixed.
When we find a new parser bug, add the sanitized log pattern here
so it never regresses.

All test data uses fake IPs (10.0.0.x) and fake credentials.
NEVER add real engagement data to this file.
"""
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def temp_log():
    """Create a temporary log file from string content."""
    created_files = []

    def _create(content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".log")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        created_files.append(path)
        return path

    yield _create

    # Cleanup
    for path in created_files:
        if os.path.exists(path):
            os.unlink(path)


# =============================================================================
# MSF PARSER (msf_parser.py) TESTS - No DB needed
# =============================================================================


class TestMsfParserModule:
    """
    Tests for souleyez/parsers/msf_parser.py functions.
    These tests don't need DB mocking - they test pure parsing logic.
    """

    def test_smb_enumshares_extracts_share_names(self):
        """
        Bug: Job #592 said '2 shares found' but didn't show share names.
        Verify share names are extracted into the description.
        """
        from souleyez.parsers.msf_parser import parse_msf_smb_enumshares

        output = """
[+] 10.0.0.50:445 - IPC$ - (IPC) Remote IPC
[+] 10.0.0.50:445 - tmp - (DISK) Temporary storage
[+] 10.0.0.50:445 - public - (DISK) Public files
[*] Auxiliary module execution completed
"""
        result = parse_msf_smb_enumshares(output, "10.0.0.50")

        assert len(result["findings"]) == 1
        finding = result["findings"][0]
        assert "3 shares" in finding["title"]
        # Share names should be in description
        assert "IPC$" in finding["description"]
        assert "tmp" in finding["description"]
        assert "public" in finding["description"]

    def test_mysql_login_extracts_credentials(self):
        """
        Bug: Job #596 said 'credentials found' but didn't show them.
        Verify MySQL credentials are extracted.
        """
        from souleyez.parsers.msf_parser import parse_msf_mysql_login

        output = """
[+] 10.0.0.50:3306 - 10.0.0.50:3306 - Found remote MySQL version 5.5.62
[+] 10.0.0.50:3306 - 10.0.0.50:3306 - Success: 'root:toor'
[*] Auxiliary module execution completed
"""
        result = parse_msf_mysql_login(output, "10.0.0.50")

        assert len(result["credentials"]) == 1
        cred = result["credentials"][0]
        assert cred["username"] == "root"
        assert cred["password"] == "toor"
        assert cred["service"] == "mysql"

    def test_ssh_login_extracts_credentials(self):
        """Verify SSH login credentials are extracted."""
        from souleyez.parsers.msf_parser import parse_msf_login_success

        output = """
[+] 10.0.0.50:22 - Success: 'admin:admin123' 'Ubuntu Linux'
[*] Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed
"""
        result = parse_msf_login_success(
            output, "10.0.0.50", "auxiliary/scanner/ssh/ssh_login"
        )

        assert len(result["credentials"]) == 1
        cred = result["credentials"][0]
        assert cred["username"] == "admin"
        assert cred["password"] == "admin123"
        assert cred["service"] == "ssh"

    def test_ftp_anonymous_detected(self):
        """Verify FTP anonymous access is detected."""
        from souleyez.parsers.msf_parser import parse_msf_ftp_anonymous

        output = """
[+] 10.0.0.50:21 - 10.0.0.50:21 - Anonymous READ (220 ProFTPD Server)
[*] Auxiliary module execution completed
"""
        result = parse_msf_ftp_anonymous(output, "10.0.0.50")

        assert len(result["findings"]) == 1
        assert "Anonymous" in result["findings"][0]["title"]
        assert len(result["credentials"]) == 1
        assert result["credentials"][0]["username"] == "anonymous"

    def test_vnc_no_auth_detected(self):
        """Verify VNC no-auth is detected as critical."""
        from souleyez.parsers.msf_parser import parse_msf_vnc_auth

        output = """
[+] 10.0.0.50:5900 - VNC server security types supported: None
[*] Auxiliary module execution completed
"""
        result = parse_msf_vnc_auth(output, "10.0.0.50")

        assert len(result["findings"]) == 1
        assert result["findings"][0]["severity"] == "critical"
        assert "No Authentication" in result["findings"][0]["title"]


# =============================================================================
# MSF EXPLOIT PARSER TESTS - With DB mocking
# =============================================================================


class TestMsfExploitParser:
    """Tests for msf_exploit result parsing."""

    def test_failed_exploit_returns_warning_not_done(self, temp_log):
        """
        Bug: Job #589 showed 'done' status when exploit failed.
        Root cause: Pattern 'Exploit completed.*session' matched
        'Exploit completed, but no session was created' as SUCCESS.
        Fixed: 2024-01 - Removed overly broad success patterns.
        """
        from souleyez.engine.result_handler import parse_msf_exploit_job

        # This log pattern caused the bug - exploit failed but was marked success
        log_content = """=== Plugin: Metasploit Exploit ===
Target: 10.0.0.50
Args: ['exploit/multi/samba/usermap_script']
Label: test
Started: 2024-01-01 00:00:00 UTC

[*] No payload configured, defaulting to cmd/unix/reverse_netcat
RHOSTS => 10.0.0.50
LHOST => 10.0.0.1
[*] Started reverse TCP handler on 10.0.0.1:4444
[-] 10.0.0.50:139 - Exploit failed [unreachable]: Rex::ConnectionTimeout The connection timed out.
[*] Exploit completed, but no session was created.

=== Completed ===
Exit Code: 0
"""
        log_path = temp_log(log_content)
        job = {"target": "10.0.0.50", "args": ["exploit/multi/samba/usermap_script"]}

        # Mock database managers
        with patch("souleyez.storage.hosts.HostManager") as mock_hm_class, patch(
            "souleyez.storage.findings.FindingsManager"
        ) as mock_fm_class:

            mock_hm = MagicMock()
            mock_hm.get_host_by_ip.return_value = {"id": 1}
            mock_hm_class.return_value = mock_hm

            mock_fm = MagicMock()
            mock_fm_class.return_value = mock_fm

            result = parse_msf_exploit_job(engagement_id=1, log_path=log_path, job=job)

        # Should be warning, NOT done
        assert (
            result["status"] == "warning"
        ), f"Expected 'warning', got '{result['status']}'"
        assert result["success"] is False, "Exploit should not be marked as success"
        assert (
            "failed" in result["summary"].lower()
        ), f"Summary should mention failure: {result['summary']}"

    def test_successful_exploit_returns_done(self, temp_log):
        """Verify successful exploits still return done status."""
        from souleyez.engine.result_handler import parse_msf_exploit_job

        log_content = """=== Plugin: Metasploit Exploit ===
Target: 10.0.0.50
Args: ['exploit/unix/ftp/vsftpd_234_backdoor']
Label: test
Started: 2024-01-01 00:00:00 UTC

[*] Started reverse TCP handler on 10.0.0.1:4444
[*] Command shell session 1 opened (10.0.0.1:4444 -> 10.0.0.50:45678)

=== Completed ===
Exit Code: 0
"""
        log_path = temp_log(log_content)
        job = {"target": "10.0.0.50", "args": ["exploit/unix/ftp/vsftpd_234_backdoor"]}

        with patch("souleyez.storage.hosts.HostManager") as mock_hm_class, patch(
            "souleyez.storage.findings.FindingsManager"
        ) as mock_fm_class:

            mock_hm = MagicMock()
            mock_hm.get_host_by_ip.return_value = {"id": 1}
            mock_hm_class.return_value = mock_hm

            mock_fm = MagicMock()
            mock_fm_class.return_value = mock_fm

            result = parse_msf_exploit_job(engagement_id=1, log_path=log_path, job=job)

        assert result["status"] == "done", f"Expected 'done', got '{result['status']}'"
        assert result["success"] is True

    def test_connection_refused_returns_warning(self, temp_log):
        """Connection refused should be warning, not error or no_results."""
        from souleyez.engine.result_handler import parse_msf_exploit_job

        log_content = """=== Plugin: Metasploit Exploit ===
Target: 10.0.0.50
Args: ['exploit/linux/http/test_exploit']
Label: test
Started: 2024-01-01 00:00:00 UTC

[-] Exploit failed: Connection refused
[*] Exploit completed, but no session was created.

=== Completed ===
Exit Code: 0
"""
        log_path = temp_log(log_content)
        job = {"target": "10.0.0.50"}

        with patch("souleyez.storage.hosts.HostManager") as mock_hm_class, patch(
            "souleyez.storage.findings.FindingsManager"
        ) as mock_fm_class:

            mock_hm = MagicMock()
            mock_hm.get_host_by_ip.return_value = {"id": 1}
            mock_hm_class.return_value = mock_hm

            mock_fm = MagicMock()
            mock_fm_class.return_value = mock_fm

            result = parse_msf_exploit_job(engagement_id=1, log_path=log_path, job=job)

        assert result["status"] == "warning"
        assert (
            "refused" in result["summary"].lower()
            or "failed" in result["summary"].lower()
        )


# =============================================================================
# MSF AUXILIARY PARSER TESTS - With DB mocking
# =============================================================================


class TestMsfAuxiliaryParser:
    """Tests for msf_auxiliary result parsing."""

    def test_connection_timeout_returns_warning(self, temp_log):
        """
        Bug: Job #598 showed 'no_results' when SSH login timed out.
        Should show 'warning' with 'target unreachable' message.
        Fixed: 2024-01 - Added connection failure detection.
        """
        from souleyez.engine.result_handler import parse_msf_auxiliary_job

        log_content = """=== Plugin: Metasploit Auxiliary ===
Target: 10.0.0.50
Args: ['auxiliary/scanner/ssh/ssh_login']
Label: test
Started: 2024-01-01 00:00:00 UTC

[*] 10.0.0.50:22 - Starting bruteforce
[-] Could not connect: The connection with (10.0.0.50:22) timed out.
[-] Could not connect: The connection with (10.0.0.50:22) timed out.
[*] Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed

=== Completed ===
Exit Code: 0
"""
        log_path = temp_log(log_content)
        job = {"target": "10.0.0.50", "args": ["auxiliary/scanner/ssh/ssh_login"]}

        with patch("souleyez.storage.hosts.HostManager") as mock_hm_class, patch(
            "souleyez.storage.findings.FindingsManager"
        ) as mock_fm_class, patch(
            "souleyez.storage.credentials.CredentialsManager"
        ) as mock_cm_class, patch(
            "souleyez.parsers.msf_parser.parse_msf_log"
        ) as mock_parse:

            mock_hm = MagicMock()
            mock_hm.get_host_by_ip.return_value = {"id": 1}
            mock_hm_class.return_value = mock_hm

            mock_fm = MagicMock()
            mock_fm_class.return_value = mock_fm

            mock_cm = MagicMock()
            mock_cm_class.return_value = mock_cm

            # Simulate parse_msf_log returning empty results (timeout = no findings)
            mock_parse.return_value = {
                "findings": [],
                "credentials": [],
                "services": [],
            }

            result = parse_msf_auxiliary_job(
                engagement_id=1, log_path=log_path, job=job
            )

        # Should be warning due to connection timeout, NOT no_results
        assert (
            result["status"] == "warning"
        ), f"Expected 'warning', got '{result['status']}'"
        assert (
            "timed out" in result["summary"].lower()
            or "unreachable" in result["summary"].lower()
        )

    def test_connection_refused_returns_warning(self, temp_log):
        """Connection refused should return warning status."""
        from souleyez.engine.result_handler import parse_msf_auxiliary_job

        log_content = """=== Plugin: Metasploit Auxiliary ===
Target: 10.0.0.50
Args: ['auxiliary/scanner/smb/smb_version']
Label: test
Started: 2024-01-01 00:00:00 UTC

[-] Connection refused
[*] Auxiliary module execution completed

=== Completed ===
Exit Code: 0
"""
        log_path = temp_log(log_content)
        job = {"target": "10.0.0.50"}

        with patch("souleyez.storage.hosts.HostManager") as mock_hm_class, patch(
            "souleyez.storage.findings.FindingsManager"
        ) as mock_fm_class, patch(
            "souleyez.storage.credentials.CredentialsManager"
        ) as mock_cm_class, patch(
            "souleyez.parsers.msf_parser.parse_msf_log"
        ) as mock_parse:

            mock_hm = MagicMock()
            mock_hm.get_host_by_ip.return_value = {"id": 1}
            mock_hm_class.return_value = mock_hm

            mock_fm = MagicMock()
            mock_fm_class.return_value = mock_fm

            mock_cm = MagicMock()
            mock_cm_class.return_value = mock_cm

            mock_parse.return_value = {
                "findings": [],
                "credentials": [],
                "services": [],
            }

            result = parse_msf_auxiliary_job(
                engagement_id=1, log_path=log_path, job=job
            )

        assert result["status"] == "warning"
        assert (
            "refused" in result["summary"].lower()
            or "unreachable" in result["summary"].lower()
        )

    def test_successful_scan_includes_finding_details(self, temp_log):
        """
        Verify parse_result includes finding summaries for UI display.
        """
        from souleyez.engine.result_handler import parse_msf_auxiliary_job

        log_content = """=== Plugin: Metasploit Auxiliary ===
Target: 10.0.0.50
Args: ['auxiliary/scanner/smb/smb_enumshares']
Label: test
Started: 2024-01-01 00:00:00 UTC

[+] 10.0.0.50:445 - IPC$ - (IPC) Remote IPC
[+] 10.0.0.50:445 - tmp - (DISK) Temporary files
[*] Auxiliary module execution completed

=== Completed ===
Exit Code: 0
"""
        log_path = temp_log(log_content)
        job = {"target": "10.0.0.50"}

        with patch("souleyez.storage.hosts.HostManager") as mock_hm_class, patch(
            "souleyez.storage.findings.FindingsManager"
        ) as mock_fm_class, patch(
            "souleyez.storage.credentials.CredentialsManager"
        ) as mock_cm_class, patch(
            "souleyez.parsers.msf_parser.parse_msf_log"
        ) as mock_parse:

            mock_hm = MagicMock()
            mock_hm.get_host_by_ip.return_value = {"id": 1}
            mock_hm_class.return_value = mock_hm

            mock_fm = MagicMock()
            mock_fm_class.return_value = mock_fm

            mock_cm = MagicMock()
            mock_cm_class.return_value = mock_cm

            # Simulate parse_msf_log returning findings with descriptions
            mock_parse.return_value = {
                "findings": [
                    {
                        "title": "SMB Shares Discovered (2 shares)",
                        "severity": "medium",
                        "description": "Found 2 SMB shares: IPC$, tmp",
                    }
                ],
                "credentials": [],
                "services": [],
            }

            result = parse_msf_auxiliary_job(
                engagement_id=1, log_path=log_path, job=job
            )

        assert result["status"] == "done"
        assert result["findings_added"] == 1
        # Check that finding details are included in parse_result
        assert "findings" in result
        assert len(result["findings"]) > 0
        assert "description" in result["findings"][0]
        assert "IPC$" in result["findings"][0]["description"]


# =============================================================================
# HYDRA PARSER TESTS
# =============================================================================


class TestHydraParser:
    """Tests for Hydra result parsing."""

    def test_connection_timeout_returns_warning(self, temp_log):
        """
        Hydra timeouts should show 'warning' not 'no_results'.
        """
        from souleyez.engine.result_handler import parse_hydra_job

        log_content = """=== Plugin: Hydra ===
Target: 10.0.0.50
Started: 2024-01-01 00:00:00 UTC

Hydra starting at 2024-01-01 00:00:00
[DATA] attacking ssh://10.0.0.50:22/
[ERROR] could not connect to ssh://10.0.0.50:22 - Connection timed out

=== Completed ===
Exit Code: 1
"""
        log_path = temp_log(log_content)
        job = {"target": "10.0.0.50", "tool": "hydra"}

        with patch("souleyez.storage.hosts.HostManager") as mock_hm_class, patch(
            "souleyez.storage.findings.FindingsManager"
        ) as mock_fm_class, patch(
            "souleyez.storage.credentials.CredentialsManager"
        ) as mock_cm_class:

            mock_hm = MagicMock()
            mock_hm.get_host_by_ip.return_value = {"id": 1}
            mock_hm_class.return_value = mock_hm

            mock_fm = MagicMock()
            mock_fm_class.return_value = mock_fm

            mock_cm = MagicMock()
            mock_cm_class.return_value = mock_cm

            result = parse_hydra_job(engagement_id=1, log_path=log_path, job=job)

        # Should be warning, not no_results
        assert (
            result["status"] == "warning"
        ), f"Expected 'warning', got '{result['status']}'"


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
