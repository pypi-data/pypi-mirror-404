#!/usr/bin/env python3
"""
Evil-WinRM handler.

Consolidates parsing and display logic for Evil-WinRM jobs.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import (
    STATUS_DONE,
    STATUS_ERROR,
    STATUS_NO_RESULTS,
    STATUS_WARNING,
)
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class EvilWinRMHandler(BaseToolHandler):
    """Handler for Evil-WinRM remote shell jobs."""

    tool_name = "evil_winrm"
    display_name = "Evil-WinRM"

    # All handlers enabled
    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    # Capability flags
    extracts_credentials = False  # Could extract creds from command output
    extracts_findings = True
    extracts_services = False
    supports_chaining = True

    # Success patterns - indicates successful authentication
    SUCCESS_PATTERNS = [
        r"Evil-WinRM shell",
        r"\*Evil-WinRM\*",
        r"PS [A-Z]:\\",
        r"Info: Establishing connection",
        r"Data: PS ",
    ]

    # Error patterns
    ERROR_PATTERNS = [
        (
            r"WinRM::WinRMAuthorizationError",
            "User not authorized for WinRM (credentials may be valid for SMB)",
        ),
        (r"Access is denied", "Access denied (insufficient privileges)"),
        (r"getaddrinfo: Name or service not known", "DNS resolution failed"),
        (r"Connection refused", "Connection refused (WinRM not running)"),
        (r"Connection timed out|Errno::ETIMEDOUT", "Connection timed out"),
        (r"No route to host", "No route to host"),
        (r"Network is unreachable", "Network unreachable"),
        (r"SSL_connect", "SSL/TLS error (try -s for SSL or check port)"),
        (r"Bad HTTP response", "Bad HTTP response (wrong port or service)"),
        (r"WinRM::WinRMHTTPTransportError", "HTTP transport error"),
        (r"WinRM::WinRMWSManFault", "WSMan fault (check WinRM config)"),
    ]

    # Warning patterns (partial success or non-critical issues)
    WARNING_PATTERNS = [
        (r"Warning:", "Warning encountered during execution"),
        (r"Access denied to", "Access denied to specific resource"),
    ]

    def parse_job(
        self,
        engagement_id: int,
        log_path: str,
        job: Dict[str, Any],
        host_manager: Optional[Any] = None,
        findings_manager: Optional[Any] = None,
        credentials_manager: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Parse Evil-WinRM job results.

        Determines if authentication succeeded and extracts command output.
        """
        try:
            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()
            if findings_manager is None:
                from souleyez.storage.findings import FindingsManager

                findings_manager = FindingsManager()

            # Read the log file
            if not os.path.exists(log_path):
                return {
                    "tool": "evil_winrm",
                    "status": STATUS_ERROR,
                    "summary": "Log file not found",
                    "error": "Log file not found",
                }

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            target = job.get("target", "")

            # Extract username and password from args if present
            args = job.get("args", [])
            username = self._extract_username(args)
            password = self._extract_password(args)

            # Check for errors first
            error_found = None
            for pattern, message in self.ERROR_PATTERNS:
                if re.search(pattern, log_content, re.IGNORECASE):
                    error_found = message
                    break

            # Check for success patterns
            success_found = False
            for pattern in self.SUCCESS_PATTERNS:
                if re.search(pattern, log_content, re.IGNORECASE):
                    success_found = True
                    break

            # Extract command output if present
            command_output = self._extract_command_output(log_content)

            # Check for warnings
            warnings = []
            for pattern, message in self.WARNING_PATTERNS:
                if re.search(pattern, log_content, re.IGNORECASE):
                    warnings.append(message)

            # Determine status
            if error_found:
                # Check if it's a connection error vs auth error
                if any(
                    x in error_found.lower()
                    for x in ["connection", "route", "network", "dns", "timed out"]
                ):
                    status = STATUS_WARNING
                    summary = f"Connection failed: {error_found}"
                else:
                    status = STATUS_ERROR
                    summary = error_found
            elif success_found:
                status = STATUS_DONE
                summary = f"WinRM shell access gained"
                if username:
                    summary += f" as {username}"

                # Add finding for successful WinRM access
                host = host_manager.get_host_by_ip(engagement_id, target)
                if not host:
                    host = host_manager.add_or_update_host(
                        engagement_id, {"ip": target, "status": "up"}
                    )

                findings_manager.add_finding(
                    engagement_id=engagement_id,
                    title=f"WinRM Shell Access - {target}",
                    finding_type="access",
                    severity="critical",
                    description=(
                        f"Evil-WinRM successfully authenticated to {target} over WinRM.\n\n"
                        f"Username: {username or 'unknown'}\n\n"
                        f"This provides remote PowerShell access to the target system, "
                        f"allowing command execution, file transfer, and potential "
                        f"privilege escalation.\n\n"
                        f"Recommendation: Review WinRM access controls and credential hygiene."
                    ),
                    host_id=host["id"] if host else None,
                    tool="evil_winrm",
                )
            elif warnings:
                status = STATUS_WARNING
                summary = warnings[0]
            else:
                status = STATUS_NO_RESULTS
                summary = "No shell access (check credentials or connectivity)"

            result = {
                "tool": "evil_winrm",
                "status": status,
                "target": target,
                "summary": summary,
                "username": username,
                "password": password,
                "success": success_found,
                "command_output": command_output,
                "warnings": warnings,
            }

            # Add credentials for UI display when shell access succeeded
            if success_found and username and password:
                result["credentials"] = [
                    {
                        "username": username,
                        "password": password,
                        "service": "winrm",
                        "access": "shell",
                    }
                ]

            if error_found:
                result["error"] = error_found

            return result

        except Exception as e:
            logger.error(f"Error parsing evil_winrm job: {e}")
            return {
                "tool": "evil_winrm",
                "status": STATUS_ERROR,
                "summary": f"Parse error: {str(e)}",
                "error": str(e),
            }

    def _extract_username(self, args) -> Optional[str]:
        """Extract username from command arguments."""
        if not args:
            return None

        # Handle list args
        if isinstance(args, list):
            for i, arg in enumerate(args):
                if arg in ["-u", "--user"] and i + 1 < len(args):
                    return args[i + 1]
            return None

        # Handle string args
        match = re.search(r"-u\s+([^\s]+)|--user\s+([^\s]+)", str(args))
        if match:
            return match.group(1) or match.group(2)
        return None

    def _extract_password(self, args) -> Optional[str]:
        """Extract password from command arguments."""
        if not args:
            return None

        # Handle list args
        if isinstance(args, list):
            for i, arg in enumerate(args):
                if arg in ["-p", "--password"] and i + 1 < len(args):
                    return args[i + 1]
            return None

        # Handle string args
        match = re.search(r"-p\s+([^\s]+)|--password\s+([^\s]+)", str(args))
        if match:
            return match.group(1) or match.group(2)
        return None

    def _extract_command_output(self, log_content: str) -> Optional[str]:
        """Extract command output from Evil-WinRM session."""
        # Look for PS prompt and capture output after it
        lines = log_content.split("\n")
        output_lines = []
        capturing = False

        for line in lines:
            # Start capturing after PS prompt
            if re.match(r"PS [A-Z]:\\", line) or "Data: PS" in line:
                capturing = True
                continue

            # Stop at completion markers
            if "Completed:" in line or "Exit Code:" in line:
                break

            if capturing and line.strip():
                # Skip Evil-WinRM internal messages
                if not any(x in line for x in ["*Evil-WinRM*", "Info:", "Data:"]):
                    output_lines.append(line)

        return "\n".join(output_lines) if output_lines else None

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful Evil-WinRM results."""
        try:
            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            target = job.get("target", "unknown")
            args = job.get("args", "")
            username = self._extract_username(args)
            command_output = self._extract_command_output(log_content)

            click.echo(click.style("=" * 70, fg="green"))
            click.echo(click.style("EVIL-WINRM SHELL ACCESS", bold=True, fg="green"))
            click.echo(click.style("=" * 70, fg="green"))
            click.echo()

            click.echo(click.style(f"Target: {target}", bold=True))
            if username:
                click.echo(f"Username: {click.style(username, fg='yellow')}")
            click.echo(f"Protocol: WinRM (Windows Remote Management)")
            click.echo()

            click.echo(click.style("Authentication successful!", fg="green", bold=True))
            click.echo("Remote PowerShell access has been established.")
            click.echo()

            if command_output:
                click.echo(click.style("Command Output:", bold=True))
                click.echo(click.style("-" * 40, dim=True))
                # Truncate long output
                if len(command_output) > 2000 and not show_all:
                    click.echo(command_output[:2000])
                    click.echo(
                        click.style(
                            f"\n... (truncated, {len(command_output)} chars total)",
                            dim=True,
                        )
                    )
                else:
                    click.echo(command_output)
                click.echo(click.style("-" * 40, dim=True))
                click.echo()

            # Extract password for reconnect command
            password = self._extract_password(args)

            click.echo(click.style("Reconnect:", fg="yellow", bold=True))
            if username and password:
                click.echo(f"  evil-winrm -i {target} -u '{username}' -p '{password}'")
            else:
                click.echo(f"  evil-winrm -i {target} -u <user> -p <pass>")
            click.echo()
            click.echo(
                click.style(
                    "  TIP: Press [s] to spawn an interactive shell", fg="green"
                )
            )
            click.echo()

            click.echo(click.style("Post-Exploitation:", fg="cyan", bold=True))
            click.echo("  - whoami /priv     (check privileges)")
            click.echo("  - systeminfo       (system enumeration)")
            click.echo("  - net user         (local users)")
            click.echo("  - net localgroup administrators")
            click.echo()

            click.echo(click.style("=" * 70, fg="green"))
            click.echo()

        except Exception as e:
            logger.error(f"Error displaying evil_winrm results: {e}")

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display Evil-WinRM error."""
        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] EVIL-WINRM FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        target = job.get("target", "unknown")
        click.echo(f"Target: {target}")
        click.echo()

        # Try to determine specific error
        error_msg = None
        if log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()

                for pattern, message in self.ERROR_PATTERNS:
                    if re.search(pattern, log_content, re.IGNORECASE):
                        error_msg = message
                        break
            except Exception:
                pass

        if error_msg:
            click.echo(f"  {error_msg}")
        else:
            click.echo(
                "  Authentication or connection failed - see raw logs for details"
            )

        click.echo()
        click.echo(click.style("Troubleshooting:", fg="yellow"))
        click.echo("  - Verify credentials are correct")
        click.echo("  - Check if WinRM is enabled on target (port 5985/5986)")
        click.echo("  - Try -s flag for SSL (port 5986)")
        click.echo("  - Ensure network connectivity to target")
        click.echo()

        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display Evil-WinRM warning."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(
            click.style("[WARNING] EVIL-WINRM CONNECTION ISSUE", bold=True, fg="yellow")
        )
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

        target = job.get("target", "unknown")
        click.echo(f"Target: {target}")
        click.echo()

        # Try to determine specific warning
        if log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()

                for pattern, message in self.ERROR_PATTERNS:
                    if re.search(pattern, log_content, re.IGNORECASE):
                        click.echo(f"  {message}")
                        break
            except Exception:
                click.echo("  Connection issue - target may be unreachable")

        click.echo()
        click.echo(click.style("Suggestions:", fg="cyan"))
        click.echo("  - Verify target is online and WinRM port is open")
        click.echo("  - Check firewall rules on target")
        click.echo("  - Try alternate port (5985 vs 5986)")
        click.echo()

        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display Evil-WinRM no results."""
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("EVIL-WINRM - NO ACCESS", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

        target = job.get("target", "unknown")
        click.echo(f"Target: {target}")
        click.echo()

        click.echo("  Could not establish WinRM shell access.")
        click.echo()

        click.echo(click.style("Common reasons:", fg="yellow"))
        click.echo("  - Invalid credentials")
        click.echo("  - WinRM not enabled on target")
        click.echo("  - Firewall blocking WinRM ports")
        click.echo("  - Account lockout or disabled")
        click.echo("  - Insufficient privileges for WinRM")
        click.echo()

        click.echo(click.style("Try:", fg="cyan"))
        click.echo("  - Verify credentials work with other tools (CME, smbclient)")
        click.echo("  - Check if WinRM is enabled: nmap -p 5985,5986 <target>")
        click.echo("  - Try psexec as alternative for shell access")
        click.echo()

        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()


# Register handler
handler = EvilWinRMHandler()
