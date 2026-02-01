#!/usr/bin/env python3
"""
souleyez.ai.result_parser - Parse command execution results
"""

import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ResultParser:
    """
    Parse command execution results and extract meaningful data.

    Handles different command types (SSH, MySQL, nmap, etc.)
    and extracts success status, access levels, and other metadata.
    """

    def __init__(self):
        """Initialize result parser."""
        pass

    def parse_result(
        self, command: str, stdout: str, stderr: str, exit_code: int
    ) -> Dict[str, Any]:
        """
        Parse command result based on command type.

        Args:
            command: Command that was executed
            stdout: Standard output
            stderr: Standard error
            exit_code: Exit code

        Returns:
            Dict with parsed results
        """
        cmd_lower = command.lower()

        # Detect command type and parse accordingly
        if "sshpass" in cmd_lower or ("ssh" in cmd_lower and "SSH_SUCCESS" in command):
            return self.parse_ssh_result(stdout, stderr, exit_code)
        elif "smbclient" in cmd_lower:
            return self.parse_smb_result(stdout, stderr, exit_code)
        elif "xfreerdp" in cmd_lower:
            return self.parse_rdp_result(stdout, stderr, exit_code)
        elif "lftp" in cmd_lower:
            return self.parse_ftp_result(stdout, stderr, exit_code)
        elif "psql" in cmd_lower or "PGPASSWORD" in command:
            return self.parse_postgresql_result(stdout, stderr, exit_code)
        elif "mysql" in cmd_lower:
            return self.parse_mysql_result(stdout, stderr, exit_code, command)
        elif "nmap" in cmd_lower:
            return self.parse_nmap_result(stdout, stderr, exit_code)
        elif "curl" in cmd_lower:
            return self.parse_http_result(stdout, stderr, exit_code)
        else:
            # Generic parsing
            return self.parse_generic_result(stdout, stderr, exit_code)

    def parse_ssh_result(
        self, stdout: str, stderr: str, exit_code: int
    ) -> Dict[str, Any]:
        """
        Parse SSH credential test result.

        Args:
            stdout: Command output
            stderr: Error output
            exit_code: Exit code

        Returns:
            Dict with:
                - success: bool
                - credential_valid: bool
                - access_level: str (user/root/none)
                - username: str (if found)
                - details: str
        """
        result = {
            "success": False,
            "credential_valid": False,
            "access_level": "none",
            "username": None,
            "details": "",
        }

        # Check for success marker
        if "SSH_SUCCESS" in stdout:
            result["success"] = True
            result["credential_valid"] = True

            # Extract username from whoami output
            whoami_match = re.search(r"SSH_SUCCESS\s+(\w+)", stdout)
            if whoami_match:
                result["username"] = whoami_match.group(1)

            # Check if root
            if "uid=0(root)" in stdout or result["username"] == "root":
                result["access_level"] = "root"
            else:
                result["access_level"] = "user"

            result["details"] = f"SSH login successful as {result['username']}"

        elif exit_code == 0:
            # Connection succeeded but no marker (shouldn't happen with our command)
            result["success"] = True
            result["credential_valid"] = True
            result["access_level"] = "user"
            result["details"] = "SSH connection successful"

        else:
            # Authentication failed or connection error
            result["success"] = False
            result["credential_valid"] = False

            if "Permission denied" in stderr or "Authentication failed" in stderr:
                result["details"] = "Invalid credentials"
            elif "Connection refused" in stderr:
                result["details"] = "SSH service not available"
            elif "Connection timed out" in stderr:
                result["details"] = "Connection timeout"
            else:
                result["details"] = f"SSH connection failed (exit code: {exit_code})"

        return result

    def parse_ftp_result(
        self, stdout: str, stderr: str, exit_code: int
    ) -> Dict[str, Any]:
        """
        Parse FTP credential test result.

        Returns:
            Dict with:
                - success: bool
                - credential_valid: bool
                - access_level: str (always 'user' for FTP)
                - details: str
        """
        result = {
            "success": False,
            "credential_valid": False,
            "access_level": "user",  # FTP doesn't have root concept
            "details": "",
        }

        # Check for failure marker
        if "FTP_FAILED" in stdout or "FTP_FAILED" in stderr:
            result["details"] = "FTP connection failed"
            return result

        # Check for authentication errors
        if (
            "Login incorrect" in stderr
            or "Login failed" in stderr
            or "Authentication failed" in stderr
        ):
            result["details"] = "Invalid credentials"
            return result

        # Check for connection errors
        if "Connection refused" in stderr or "Connection timed out" in stderr:
            result["details"] = "Connection failed"
            return result

        # If we got directory listing, credentials worked
        if exit_code == 0 or "drw" in stdout or "-rw" in stdout:
            result["success"] = True
            result["credential_valid"] = True
            result["details"] = "FTP login successful"

        return result

    def parse_smb_result(
        self, stdout: str, stderr: str, exit_code: int
    ) -> Dict[str, Any]:
        """
        Parse SMB credential test result.

        Returns:
            Dict with:
                - success: bool
                - credential_valid: bool
                - access_level: str (user for SMB)
                - shares: list of discovered shares (optional)
                - details: str
        """
        result = {
            "success": False,
            "credential_valid": False,
            "access_level": "user",
            "shares": [],
            "details": "",
        }

        # Check for failure marker
        if "SMB_FAILED" in stdout or "SMB_FAILED" in stderr:
            result["details"] = "SMB connection failed"
            return result

        # Check for authentication errors
        if "NT_STATUS_LOGON_FAILURE" in stderr or "NT_STATUS_ACCESS_DENIED" in stderr:
            result["details"] = "Invalid credentials"
            return result

        # Check for connection errors
        if "Connection refused" in stderr or "Connection timed out" in stderr:
            result["details"] = "Connection failed"
            return result

        if "NT_STATUS_IO_TIMEOUT" in stderr or "Unable to connect" in stderr:
            result["details"] = "Connection timeout"
            return result

        # Check for successful share listing
        if "Disk|" in stdout or "IPC$" in stdout or "Sharename" in stdout:
            result["success"] = True
            result["credential_valid"] = True
            result["details"] = "SMB login successful"

            # Extract share names (optional enhancement)
            import re

            share_matches = re.findall(r"^\s+(\S+)\s+Disk", stdout, re.MULTILINE)
            if share_matches:
                result["shares"] = share_matches
                result["details"] = (
                    f"SMB login successful, found {len(share_matches)} shares"
                )

        return result

    def parse_rdp_result(
        self, stdout: str, stderr: str, exit_code: int
    ) -> Dict[str, Any]:
        """
        Parse RDP credential test result.

        Returns:
            Dict with:
                - success: bool
                - credential_valid: bool
                - access_level: str (user for RDP)
                - details: str
        """
        result = {
            "success": False,
            "credential_valid": False,
            "access_level": "user",
            "details": "",
        }

        # Check for failure marker
        if "RDP_FAILED" in stdout or "RDP_FAILED" in stderr:
            result["details"] = "RDP connection failed"
            return result

        # Check for authentication errors
        if (
            "Authentication failure" in stderr
            or "ERRCONNECT_AUTHENTICATION_FAILED" in stderr
        ):
            result["details"] = "Invalid credentials"
            return result

        if "Account restriction" in stderr or "ERRCONNECT_ACCOUNT_DISABLED" in stderr:
            result["details"] = "Account disabled or restricted"
            return result

        # Check for connection errors
        if (
            "unable to connect" in stderr.lower()
            or "connection failed" in stderr.lower()
        ):
            result["details"] = "Connection failed"
            return result

        if "Connection timeout" in stderr or "connection timed out" in stderr.lower():
            result["details"] = "Connection timeout"
            return result

        # Check for successful authentication
        # xfreerdp with +auth-only returns 0 on successful auth
        if (
            exit_code == 0
            or "Authentication only" in stdout
            or "connected" in stdout.lower()
        ):
            result["success"] = True
            result["credential_valid"] = True
            result["details"] = "RDP authentication successful"

            # Check if admin (optional - may not be detectable in auth-only mode)
            if "administrator" in stdout.lower():
                result["access_level"] = "admin"

        return result

    def parse_postgresql_result(
        self, stdout: str, stderr: str, exit_code: int
    ) -> Dict[str, Any]:
        """
        Parse PostgreSQL credential test result.

        Returns:
            Dict with:
                - success: bool
                - credential_valid: bool
                - access_level: str
                - details: str
        """
        result = {
            "success": False,
            "credential_valid": False,
            "access_level": "user",
            "details": "",
        }

        # Check for failure marker
        if "PSQL_FAILED" in stdout:
            result["details"] = "PostgreSQL connection failed"
            return result

        # Check for authentication errors
        if (
            "authentication failed" in stderr.lower()
            or "password authentication failed" in stderr.lower()
        ):
            result["details"] = "Invalid credentials"
            return result

        # Check for connection errors
        if "could not connect" in stderr.lower() or "Connection refused" in stderr:
            result["details"] = "Connection failed"
            return result

        # Check for version output (means connection worked)
        if "PostgreSQL" in stdout or "version" in stdout.lower():
            result["success"] = True
            result["credential_valid"] = True

            # Check if superuser
            if "superuser" in stdout.lower():
                result["access_level"] = "admin"

            result["details"] = "PostgreSQL login successful"

        return result

    def parse_mysql_result(
        self, stdout: str, stderr: str, exit_code: int, command: str
    ) -> Dict[str, Any]:
        """
        Parse MySQL command result.

        Args:
            stdout: Command output
            stderr: Error output
            exit_code: Exit code
            command: Original command

        Returns:
            Dict with success status and details
        """
        result = {
            "success": False,
            "credential_valid": False,
            "details": "",
            "databases": [],
            "users": [],
        }

        # Check for version output (indicates successful connection)
        if "version()" in stdout or re.search(r"\d+\.\d+\.\d+", stdout):
            result["success"] = True
            result["credential_valid"] = True

            version_match = re.search(r"(\d+\.\d+\.\d+)", stdout)
            if version_match:
                result["details"] = (
                    f"MySQL connection successful (version: {version_match.group(1)})"
                )
            else:
                result["details"] = "MySQL connection successful"

        # Check for database enumeration
        if "SHOW DATABASES" in command.upper():
            db_matches = re.findall(r"^([a-zA-Z_]\w*)$", stdout, re.MULTILINE)
            result["databases"] = [
                db for db in db_matches if db not in ["Database", "version()"]
            ]

        # Check for user enumeration
        if "SELECT user" in command:
            user_matches = re.findall(r"(\w+)\s+(%|[\w.]+)", stdout)
            result["users"] = user_matches

        # Check for errors
        if exit_code != 0 or "ERROR" in stderr:
            result["success"] = False
            result["credential_valid"] = False

            if "Access denied" in stderr:
                result["details"] = "Invalid MySQL credentials"
            elif "Can't connect" in stderr or "Connection refused" in stderr:
                result["details"] = "MySQL service not available"
            else:
                result["details"] = f"MySQL command failed: {stderr[:100]}"

        return result

    def parse_nmap_result(
        self, stdout: str, stderr: str, exit_code: int
    ) -> Dict[str, Any]:
        """Parse nmap scan result."""
        result = {
            "success": exit_code == 0,
            "open_ports": [],
            "services": {},
            "details": "",
        }

        if exit_code == 0:
            # Extract open ports
            port_lines = re.findall(r"^(\d+)/tcp\s+open\s+(.+)$", stdout, re.MULTILINE)
            for port, service_info in port_lines:
                result["open_ports"].append(int(port))
                result["services"][port] = service_info.strip()

            result["details"] = (
                f"Scan complete: {len(result['open_ports'])} open ports found"
            )
        else:
            result["details"] = "Nmap scan failed"

        return result

    def parse_http_result(
        self, stdout: str, stderr: str, exit_code: int
    ) -> Dict[str, Any]:
        """Parse HTTP request result."""
        result = {"success": False, "status_code": None, "server": None, "details": ""}

        # Extract HTTP status code
        status_match = re.search(r"HTTP/[\d.]+\s+(\d+)", stdout)
        if status_match:
            result["success"] = True
            result["status_code"] = int(status_match.group(1))

        # Extract server header
        server_match = re.search(r"Server:\s*(.+)", stdout, re.IGNORECASE)
        if server_match:
            result["server"] = server_match.group(1).strip()

        if result["success"]:
            result["details"] = f"HTTP {result['status_code']}"
            if result["server"]:
                result["details"] += f" - {result['server']}"
        else:
            result["details"] = "HTTP request failed"

        return result

    def parse_generic_result(
        self, stdout: str, stderr: str, exit_code: int
    ) -> Dict[str, Any]:
        """Generic result parsing for unknown command types."""
        return {
            "success": exit_code == 0,
            "details": (
                "Command executed"
                if exit_code == 0
                else f"Command failed (exit {exit_code})"
            ),
        }
