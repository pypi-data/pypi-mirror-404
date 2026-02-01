#!/usr/bin/env python3
"""
SmbPasswd handler.

Handles parsing and display for smbpasswd password change jobs.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_ERROR, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class SmbpasswdHandler(BaseToolHandler):
    """Handler for smbpasswd password change jobs."""

    tool_name = "smbpasswd"
    display_name = "SMB Password Change"

    has_error_handler = True
    has_warning_handler = False
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
        """Parse smbpasswd job results."""
        try:
            if not log_path or not os.path.exists(log_path):
                return {"error": "Log file not found"}

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            target = job.get("target", "")
            # Check for success - either our custom message or smbpasswd native output
            password_changed = (
                "PASSWORD CHANGED SUCCESSFULLY" in content
                or "Password changed for user" in content
            )

            # Extract username and new password from log or job args
            username = None
            new_password = None

            # Try to extract from log first
            username_match = re.search(r"Username:\s*(\S+)", content)
            if username_match:
                username = username_match.group(1)

            # Also try to extract from smbpasswd native output
            if not username:
                native_match = re.search(r"Password changed for user (\S+)", content)
                if native_match:
                    username = native_match.group(1)

            # Try to extract from job args if not in log
            job_args = job.get("args", [])
            if isinstance(job_args, str):
                job_args = job_args.split()

            for i, arg in enumerate(job_args):
                if arg in ["-U", "--user"] and i + 1 < len(job_args):
                    if not username:
                        username = job_args[i + 1]
                elif arg == "--new-pass" and i + 1 < len(job_args):
                    if not new_password:
                        new_password = job_args[i + 1]

            # Only extract new password from the success section in log
            if password_changed and not new_password:
                newpass_match = re.search(
                    r"New Password:\s*(.+?)$", content, re.MULTILINE
                )
                if newpass_match:
                    new_password = newpass_match.group(1).strip()

            # Store the new credential if successful
            if password_changed and username and new_password and credentials_manager:
                if host_manager is None:
                    from souleyez.storage.hosts import HostManager

                    host_manager = HostManager()

                host = host_manager.get_host_by_ip(engagement_id, target)
                if host:
                    credentials_manager.add_credential(
                        engagement_id=engagement_id,
                        host_id=host["id"],
                        username=username,
                        password=new_password,
                        service="smb",
                        credential_type="password",
                        tool="smbpasswd",
                        status="valid",
                    )

            status = STATUS_DONE if password_changed else STATUS_ERROR

            # Build credentials list for display and chaining
            creds_list = []
            if password_changed and username and new_password:
                creds_list = [
                    {"username": username, "password": new_password, "service": "smb"}
                ]

            return {
                "tool": "smbpasswd",
                "status": status,
                "target": target,
                "password_changed": password_changed,
                "username": username,
                "new_password": new_password,
                # Standard field for generic display
                "credentials": creds_list,
                # For chaining to evil-winrm
                "valid_credentials": creds_list,
                "has_valid_credentials": password_changed,
            }

        except Exception as e:
            logger.error(f"Error parsing smbpasswd job: {e}")
            return {"error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful smbpasswd results."""
        try:
            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Check for success - either our custom message or smbpasswd native output
            password_changed = (
                "PASSWORD CHANGED SUCCESSFULLY" in content
                or "Password changed for user" in content
            )

            # Extract info
            username = None
            new_password = None
            target = job.get("target", "")

            # Try to extract from log first
            username_match = re.search(r"Username:\s*(\S+)", content)
            if username_match:
                username = username_match.group(1)

            # Also try to extract from smbpasswd native output
            if not username:
                native_match = re.search(r"Password changed for user (\S+)", content)
                if native_match:
                    username = native_match.group(1)

            # Try to extract from job args if not in log
            job_args = job.get("args", [])
            if isinstance(job_args, str):
                job_args = job_args.split()

            for i, arg in enumerate(job_args):
                if arg in ["-U", "--user"] and i + 1 < len(job_args):
                    if not username:
                        username = job_args[i + 1]
                elif arg == "--new-pass" and i + 1 < len(job_args):
                    if not new_password:
                        new_password = job_args[i + 1]

            if password_changed and not new_password:
                newpass_match = re.search(
                    r"New Password:\s*(.+?)$", content, re.MULTILINE
                )
                if newpass_match:
                    new_password = newpass_match.group(1).strip()

            click.echo(click.style("=" * 70, fg="green", bold=True))
            click.echo(
                click.style("PASSWORD CHANGED SUCCESSFULLY!", bold=True, fg="green")
            )
            click.echo(click.style("=" * 70, fg="green", bold=True))
            click.echo()

            click.echo(click.style(f"  Target:   {target}", fg="white"))
            click.echo(click.style(f"  Username: {username}", fg="white"))
            if show_passwords and new_password:
                click.echo(
                    click.style(f"  Password: {new_password}", fg="yellow", bold=True)
                )
            else:
                click.echo(click.style(f"  Password: ***", fg="yellow"))
            click.echo()

            click.echo(
                click.style(
                    "  NEXT STEP: Connect with evil-winrm", fg="cyan", bold=True
                )
            )
            if show_passwords and new_password:
                click.echo(
                    click.style(
                        f"  evil-winrm -i {target} -u {username} -p '{new_password}'",
                        fg="cyan",
                    )
                )
            else:
                click.echo(
                    click.style(
                        f"  evil-winrm -i {target} -u {username} -p '<password>'",
                        fg="cyan",
                    )
                )
            click.echo()
            click.echo(click.style("=" * 70, fg="green", bold=True))
            click.echo()

        except Exception as e:
            logger.debug(f"Error in display_done: {e}")

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display error status for smbpasswd."""
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] PASSWORD CHANGE FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        error_msg = None
        if log_content:
            if "NT_STATUS_WRONG_PASSWORD" in log_content:
                error_msg = "Wrong current password provided"
            elif "NT_STATUS_PASSWORD_RESTRICTION" in log_content:
                error_msg = "New password doesn't meet complexity requirements"
            elif "NT_STATUS_ACCESS_DENIED" in log_content:
                error_msg = "Access denied - check permissions"
            elif "NT_STATUS_NO_SUCH_USER" in log_content:
                error_msg = "User not found"
            elif "Connection refused" in log_content:
                error_msg = "Connection refused - SMB service may be down"

        if error_msg:
            click.echo(f"  {error_msg}")
        else:
            click.echo(
                "  Password change failed - see raw logs for details (press 'r')"
            )

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for smbpasswd."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("PASSWORD CHANGE - NO RESULT", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  The password change operation did not complete.")
        click.echo("  Check raw logs for details (press 'r').")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
