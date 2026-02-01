#!/usr/bin/env python3
"""
Handler for kerbrute Kerberos enumeration tool.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)

STATUS_DONE = "done"
STATUS_ERROR = "error"
STATUS_WARNING = "warning"
STATUS_NO_RESULTS = "no_results"


class KerbruteHandler(BaseToolHandler):
    """Handler for kerbrute Kerberos enumeration."""

    tool_name = "kerbrute"
    display_name = "Kerbrute"

    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    # Patterns for valid users
    VALID_USER_PATTERN = r"VALID USERNAME:\s*(\S+@\S+|\S+)"

    # Patterns for successful password spray
    VALID_CRED_PATTERN = r"VALID LOGIN:\s*(\S+):(\S+)"

    # Error patterns
    ERROR_PATTERNS = [
        (r"KDC_ERR_WRONG_REALM", "Wrong realm/domain specified"),
        (r"KDC_ERR_C_PRINCIPAL_UNKNOWN", "Principal unknown"),
        (r"error getting AS-REP", "AS-REP error"),
        (r"connection refused", "Connection refused"),
        (r"no such host", "Host not found"),
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
        """Parse kerbrute results."""
        try:
            target = job.get("target", "")

            if not log_path or not os.path.exists(log_path):
                return {
                    "tool": "kerbrute",
                    "status": STATUS_ERROR,
                    "error": "Log file not found",
                }

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Strip ANSI color codes
            log_content = re.sub(r"\x1b\[[0-9;]*m", "", log_content)

            # Check for errors first
            for pattern, error_msg in self.ERROR_PATTERNS:
                if re.search(pattern, log_content, re.IGNORECASE):
                    # Don't return error for KDC_ERR_C_PRINCIPAL_UNKNOWN - that's expected
                    if "PRINCIPAL_UNKNOWN" in pattern:
                        continue
                    return {
                        "tool": "kerbrute",
                        "status": STATUS_ERROR,
                        "target": target,
                        "error": error_msg,
                    }

            # Parse valid usernames
            valid_users = re.findall(self.VALID_USER_PATTERN, log_content)
            # Clean up usernames (remove @domain if present for consistency)
            users = []
            for user in valid_users:
                if "@" in user:
                    username = user.split("@")[0]
                else:
                    username = user
                if username and username not in users:
                    users.append(username)

            # Parse valid credentials (from password spray)
            valid_creds = re.findall(self.VALID_CRED_PATTERN, log_content)
            credentials = []
            for username, password in valid_creds:
                credentials.append(
                    {
                        "username": username,
                        "password": password,
                        "source": "kerbrute_spray",
                    }
                )

            # Store credentials and usernames if found
            if credentials_manager:
                if host_manager is None:
                    from souleyez.storage.hosts import HostManager

                    host_manager = HostManager()

                host = host_manager.get_host_by_ip(engagement_id, target)
                if host:
                    # Store valid credentials from password spray
                    for cred in credentials:
                        try:
                            credentials_manager.add_credential(
                                engagement_id=engagement_id,
                                host_id=host["id"],
                                username=cred["username"],
                                password=cred["password"],
                                service="kerberos",
                                credential_type="password",
                                tool="kerbrute",
                                status="valid",
                            )
                            logger.warning(f"CREDENTIAL FOUND: {cred['username']}")
                        except Exception:
                            pass

                    # Store enumerated usernames (without password)
                    for username in users:
                        try:
                            credentials_manager.add_credential(
                                engagement_id=engagement_id,
                                host_id=host["id"],
                                username=username,
                                password="",
                                service="kerberos",
                                credential_type="username",
                                tool="kerbrute",
                                status="untested",
                            )
                        except Exception:
                            pass  # Skip duplicates
                    if users:
                        logger.info(
                            f"kerbrute: Stored {len(users)} enumerated usernames"
                        )

            if users or credentials:
                logger.info(
                    f"kerbrute: Found {len(users)} valid user(s), {len(credentials)} credential(s)"
                )
                return {
                    "tool": "kerbrute",
                    "status": STATUS_DONE,
                    "target": target,
                    "users": users,
                    "users_found": len(users),
                    "credentials_found": credentials,
                    "credentials_added": len(credentials),
                }

            return {"tool": "kerbrute", "status": STATUS_NO_RESULTS, "target": target}

        except Exception as e:
            logger.error(f"Error parsing kerbrute job: {e}")
            return {"tool": "kerbrute", "status": STATUS_ERROR, "error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful kerbrute results."""
        click.echo()
        click.echo(click.style("=" * 70, fg="green"))
        click.echo(
            click.style("KERBRUTE ENUMERATION SUCCESSFUL", fg="green", bold=True)
        )
        click.echo(click.style("=" * 70, fg="green"))
        click.echo()

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Strip ANSI color codes
            log_content = re.sub(r"\x1b\[[0-9;]*m", "", log_content)

            # Parse and display valid users
            valid_users = re.findall(self.VALID_USER_PATTERN, log_content)
            if valid_users:
                click.echo(
                    click.style(
                        f"  VALID USERS ({len(valid_users)})", bold=True, fg="cyan"
                    )
                )
                for user in valid_users:
                    click.echo(f"    {click.style(user, fg='green')}")
                click.echo()

            # Parse and display valid credentials
            valid_creds = re.findall(self.VALID_CRED_PATTERN, log_content)
            if valid_creds:
                click.echo(
                    click.style(
                        f"  VALID CREDENTIALS ({len(valid_creds)})", bold=True, fg="red"
                    )
                )
                for username, password in valid_creds:
                    if show_passwords:
                        click.echo(
                            f"    {click.style(f'{username}:{password}', fg='red', bold=True)}"
                        )
                    else:
                        click.echo(f"    {click.style(f'{username}:***', fg='red')}")
                click.echo()

        except Exception as e:
            click.echo(f"  Error reading log: {e}")

        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display kerbrute error."""
        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("KERBRUTE FAILED", fg="red", bold=True))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            for pattern, error_msg in self.ERROR_PATTERNS:
                if re.search(pattern, log_content, re.IGNORECASE):
                    click.echo(f"  Error: {error_msg}")
                    break
            else:
                click.echo("  Kerbrute failed - check log for details")

        except Exception:
            click.echo("  Could not read error details")

        click.echo()

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display kerbrute warning."""
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("KERBRUTE - PARTIAL RESULTS", fg="yellow", bold=True))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Enumeration completed with warnings")
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display kerbrute no results."""
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(
            click.style("KERBRUTE - NO VALID USERS FOUND", fg="yellow", bold=True)
        )
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  No valid usernames were identified.")
        click.echo()
        click.echo(click.style("  Tips:", dim=True))
        click.echo("    - Try a different username wordlist")
        click.echo("    - Verify the domain name is correct")
        click.echo("    - Check if Kerberos (port 88) is accessible")
        click.echo()
