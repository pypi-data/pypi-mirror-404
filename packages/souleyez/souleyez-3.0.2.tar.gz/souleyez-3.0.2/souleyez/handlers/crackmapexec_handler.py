#!/usr/bin/env python3
"""
CrackMapExec handler.

Consolidates parsing and display logic for CrackMapExec Windows/AD enumeration jobs.
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


class CrackMapExecHandler(BaseToolHandler):
    """Handler for CrackMapExec Windows/AD enumeration jobs."""

    tool_name = "crackmapexec"
    display_name = "CrackMapExec"

    # All handlers enabled
    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

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
        Parse CrackMapExec job results.

        Extracts hosts, credentials, and SMB information.
        """
        try:
            from souleyez.parsers.crackmapexec_parser import parse_crackmapexec

            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()
            if credentials_manager is None:
                from souleyez.storage.credentials import CredentialsManager

                credentials_manager = CredentialsManager()

            target = job.get("target", "")
            parsed = parse_crackmapexec(log_path, target)

            if "error" in parsed:
                return parsed

            # Store hosts
            for host in parsed.get("findings", {}).get("hosts", []):
                host_manager.add_or_update_host(
                    engagement_id,
                    {
                        "ip": host["ip"],
                        "hostname": host.get("hostname"),
                        "domain": host.get("domain"),
                        "os": host.get("os"),
                        "status": "up",
                    },
                )

            # Store credentials
            creds_added = 0
            for cred in parsed.get("findings", {}).get("credentials", []):
                host = host_manager.get_host_by_ip(engagement_id, target)
                if host:
                    credentials_manager.add_credential(
                        engagement_id=engagement_id,
                        host_id=host["id"],
                        username=cred["username"],
                        password=cred["password"],
                        service="smb",
                        credential_type="password",
                        tool="crackmapexec",
                        status="valid",
                    )
                    creds_added += 1

            # Determine status - check all finding types
            hosts_found = len(parsed.get("findings", {}).get("hosts", []))
            shares_found = len(parsed.get("findings", {}).get("shares", []))
            users_found = len(parsed.get("findings", {}).get("users", []))
            vulns_found = len(parsed.get("findings", {}).get("vulnerabilities", []))
            pw_must_change = parsed.get("password_must_change", [])

            # Determine status based on results found
            # Retry logic is handled by background.py before parsing
            if (
                hosts_found > 0
                or shares_found > 0
                or users_found > 0
                or creds_added > 0
                or vulns_found > 0
                or len(pw_must_change) > 0
            ):
                status = STATUS_DONE
            else:
                status = STATUS_NO_RESULTS

            # Extract readable shares for chaining (AD attack paths)
            all_shares = parsed.get("findings", {}).get("shares", [])
            readable_shares = [
                s
                for s in all_shares
                if s.get("permissions") and "READ" in s.get("permissions", "").upper()
            ]

            # Extract admin credentials for post-exploitation chaining
            admin_creds = parsed.get("valid_admin_credentials", [])

            return {
                "tool": "crackmapexec",
                "status": status,
                "target": target,
                "hosts_found": parsed.get("hosts_found", 0),
                "shares_found": parsed.get("shares_found", 0),
                "users_found": parsed.get("users_found", 0),
                "credentials_added": creds_added,
                "vulnerabilities_found": parsed.get("vulnerabilities_found", 0),
                "domains": parsed.get("domains", []),
                # For chaining - AD attack paths
                "readable_shares": readable_shares,
                "shares": all_shares,
                # For post-exploitation chaining
                "valid_admin_credentials": admin_creds,
                "has_admin_access": len(admin_creds) > 0,
                # For password change chaining (STATUS_PASSWORD_MUST_CHANGE)
                "password_must_change": pw_must_change,
                "has_password_must_change": len(pw_must_change) > 0,
            }

        except Exception as e:
            logger.error(f"Error parsing crackmapexec job: {e}")
            return {"error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful CrackMapExec results."""
        try:
            from souleyez.parsers.crackmapexec_parser import parse_crackmapexec_output

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            parsed = parse_crackmapexec_output(log_content, job.get("target", ""))

            findings = parsed.get("findings", {})
            hosts = findings.get("hosts", [])
            shares = findings.get("shares", [])
            users = findings.get("users", [])
            vulns = findings.get("vulnerabilities", [])
            creds = findings.get("credentials", [])
            auth_info = findings.get("auth_info", {})
            pw_must_change = findings.get("password_must_change", [])

            # Only show summary if there's meaningful data
            has_results = (
                hosts
                or shares
                or users
                or vulns
                or creds
                or auth_info
                or pw_must_change
            )
            if not has_results:
                self.display_no_results(job, log_path)
                return

            # Header
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo(click.style("SMB ENUMERATION RESULTS", bold=True, fg="cyan"))
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

            # Host information
            if hosts:
                for host in hosts:
                    click.echo(
                        click.style(
                            f"Target: {host.get('hostname', 'Unknown')} ({host['ip']}:{host.get('port', 445)})",
                            bold=True,
                            fg="green",
                        )
                    )
                    if host.get("os"):
                        click.echo(click.style(f"  OS: {host['os']}", fg="white"))
                    if host.get("domain"):
                        click.echo(
                            click.style(f"  Domain: {host['domain']}", fg="white")
                        )

                    # Security info
                    if host.get("signing") or host.get("smbv1"):
                        click.echo()
                        click.echo(click.style("  Security Status:", bold=True))
                        if host.get("signing"):
                            signing_color = (
                                "red" if host["signing"].lower() == "false" else "green"
                            )
                            click.echo(
                                click.style(
                                    f"    SMB Signing: {host['signing']}",
                                    fg=signing_color,
                                )
                            )
                        if host.get("smbv1"):
                            smbv1_color = (
                                "red" if host["smbv1"].lower() == "true" else "green"
                            )
                            smbv1_status = (
                                "Enabled (VULNERABLE)"
                                if host["smbv1"].lower() == "true"
                                else "Disabled"
                            )
                            click.echo(
                                click.style(
                                    f"    SMBv1: {smbv1_status}", fg=smbv1_color
                                )
                            )
                    click.echo()

            # Shares
            if shares:
                click.echo(
                    click.style(
                        f"Shares Found ({len(shares)}):", bold=True, fg="yellow"
                    )
                )
                for share in shares:
                    name = share.get("name", "Unknown")
                    perms = share.get("permissions", "")
                    click.echo(f"  - {name} ({perms})")
                click.echo()

            # Users
            if users:
                click.echo(
                    click.style(f"Users Found ({len(users)}):", bold=True, fg="green")
                )
                max_users = None if show_all else 15
                display_users = users if max_users is None else users[:max_users]
                for user in display_users:
                    click.echo(f"  - {user}")
                if max_users and len(users) > max_users:
                    click.echo(f"  ... and {len(users) - max_users} more")
                click.echo()

            # Credentials
            if creds:
                click.echo(
                    click.style(
                        f"Credentials Found ({len(creds)}):", bold=True, fg="red"
                    )
                )
                for cred in creds:
                    username = cred.get("username", "Unknown")
                    if show_passwords and cred.get("password"):
                        click.echo(f"  - {username}:{cred['password']}")
                    else:
                        click.echo(f"  - {username}:***")
                click.echo()

            # Password Must Change - HIGH VALUE FINDING
            if pw_must_change:
                click.echo(click.style("=" * 70, fg="red", bold=True))
                click.echo(
                    click.style(
                        f"PASSWORD MUST CHANGE ({len(pw_must_change)}):",
                        bold=True,
                        fg="red",
                    )
                )
                click.echo(
                    click.style(
                        "  These users can authenticate but MUST change their password!",
                        fg="yellow",
                    )
                )
                click.echo()
                for entry in pw_must_change:
                    domain = entry.get("domain", "")
                    username = entry.get("username", "")
                    password = entry.get("password", "")
                    if show_passwords:
                        click.echo(
                            click.style(
                                f"  {domain}\\{username}:{password}",
                                fg="red",
                                bold=True,
                            )
                        )
                    else:
                        click.echo(
                            click.style(
                                f"  {domain}\\{username}:***",
                                fg="red",
                                bold=True,
                            )
                        )
                click.echo()
                click.echo(
                    click.style(
                        "  NEXT STEP: Use smbpasswd to change password, then login",
                        fg="green",
                        bold=True,
                    )
                )
                click.echo(
                    click.style(
                        f"  Example: smbpasswd -r <target> -U {pw_must_change[0].get('username', 'USER')}",
                        fg="cyan",
                    )
                )
                click.echo(click.style("=" * 70, fg="red", bold=True))
                click.echo()

            # Vulnerabilities
            if vulns:
                click.echo(
                    click.style(f"Vulnerabilities ({len(vulns)}):", bold=True, fg="red")
                )
                for vuln in vulns:
                    click.echo(f"  - {vuln}")
                click.echo()

            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

        except Exception as e:
            logger.debug(f"Error in display_done: {e}")

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display warning status for CrackMapExec."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] CRACKMAPEXEC", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Scan completed with warnings. Check raw logs for details.")
        click.echo("  Press [r] to view raw logs.")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display error status for CrackMapExec."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] CRACKMAPEXEC FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common CME errors
        error_msg = None
        if log_content:
            if "Connection refused" in log_content or "Connection reset" in log_content:
                error_msg = "Connection refused - SMB service may be down"
            elif "timed out" in log_content.lower() or "timeout" in log_content.lower():
                error_msg = "Connection timed out - target may be slow or filtering"
            elif "STATUS_LOGON_FAILURE" in log_content:
                error_msg = "Authentication failed - invalid credentials"
            elif "STATUS_ACCESS_DENIED" in log_content:
                error_msg = "Access denied - insufficient privileges"
            elif "Errno 113" in log_content or "No route to host" in log_content:
                error_msg = "No route to host - network unreachable"
            elif "[-]" in log_content:
                match = re.search(r"\[-\]\s*(.+?)(?:\n|$)", log_content)
                if match:
                    error_msg = match.group(1).strip()[:100]

        if error_msg:
            click.echo(f"  {error_msg}")
        else:
            click.echo("  Scan failed - see raw logs for details (press 'r')")

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for CrackMapExec."""
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("SMB ENUMERATION RESULTS", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

        if job.get("target"):
            click.echo(click.style(f"Target: {job.get('target')}", bold=True))
            click.echo()

        # Show summary counts (all zeros for no_results)
        click.echo(click.style("Summary:", bold=True))
        click.echo(f"  Hosts:           0")
        click.echo(f"  Shares:          0")
        click.echo(f"  Users:           0")
        click.echo(f"  Credentials:     0")
        click.echo(f"  Vulnerabilities: 0")
        click.echo()

        click.echo(
            click.style("Result: No SMB information discovered", fg="yellow", bold=True)
        )
        click.echo()
        click.echo("  The scan did not find any hosts, shares, or users.")
        click.echo()
        click.echo(click.style("Possible reasons:", dim=True))
        click.echo("  - Target does not have SMB enabled (port 445)")
        click.echo("  - Firewall blocking SMB traffic")
        click.echo("  - Host is offline or unreachable")
        click.echo("  - Authentication required (try: -u user -p password)")
        click.echo()
        click.echo(click.style("Tips:", dim=True))
        click.echo("  - Verify connectivity: nmap -p 445 <target>")
        click.echo("  - Try null session: --shares")
        click.echo("  - Try different protocols: smb, winrm, ldap, ssh")
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
