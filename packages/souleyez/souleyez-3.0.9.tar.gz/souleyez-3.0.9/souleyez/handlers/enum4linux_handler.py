#!/usr/bin/env python3
"""
enum4linux handler.

Consolidates parsing and display logic for enum4linux SMB/Samba enumeration jobs.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS, STATUS_WARNING
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class Enum4LinuxHandler(BaseToolHandler):
    """Handler for enum4linux SMB/Samba enumeration jobs."""

    tool_name = "enum4linux"
    display_name = "enum4linux"

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
        Parse enum4linux job results.

        Extracts SMB users, groups, shares and stores them.
        """
        try:
            from souleyez.engine.result_handler import detect_tool_error
            from souleyez.parsers.enum4linux_parser import (
                categorize_share,
                get_smb_stats,
                parse_enum4linux_output,
            )

            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()
            if findings_manager is None:
                from souleyez.storage.findings import FindingsManager

                findings_manager = FindingsManager()
            if credentials_manager is None:
                from souleyez.storage.credentials import CredentialsManager

                credentials_manager = CredentialsManager()

            target = job.get("target", "")

            # Read log file
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                output = f.read()

            parsed = parse_enum4linux_output(output, target)

            # Get or create host
            host_id = None
            if parsed.get("target"):
                is_ip = re.match(
                    r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", parsed["target"]
                )
                if is_ip:
                    host = host_manager.get_host_by_ip(engagement_id, parsed["target"])
                    if host:
                        host_id = host["id"]
                    else:
                        host_id = host_manager.add_or_update_host(
                            engagement_id, {"ip": parsed["target"], "status": "up"}
                        )

            # Store discovered usernames as credentials
            credentials_added = 0
            for username in parsed.get("users", []):
                credentials_manager.add_credential(
                    engagement_id=engagement_id,
                    host_id=host_id,
                    username=username,
                    password="",
                    credential_type="smb",
                    service="smb",
                    port=445,
                    tool="enum4linux",
                )
                credentials_added += 1

            # Store shares in smb_shares table (proper storage)
            from souleyez.storage.smb_shares import SMBSharesManager

            smb_mgr = SMBSharesManager()
            shares_added = 0
            findings_added = 0

            for share in parsed.get("shares", []):
                category = categorize_share(share)
                share_name = share["name"]
                share_type = share.get("type", "Unknown")
                mapping = share.get("mapping", "N/A")
                listing = share.get("listing", "N/A")
                writing = share.get("writing", "N/A")

                # Determine readable/writable status
                readable = mapping == "OK" and listing in ("OK", "N/A")
                writable = mapping == "OK" and writing == "OK"

                # Store in smb_shares table
                if host_id:
                    try:
                        smb_mgr.add_share(
                            host_id=host_id,
                            share_data={
                                "name": share_name,
                                "type": share_type,
                                "permissions": f"{mapping}/{listing}/{writing}",
                                "comment": share.get("comment", ""),
                                "readable": readable,
                                "writable": writable,
                            },
                        )
                        shares_added += 1
                    except Exception as e:
                        logger.debug(f"Could not store share in smb_shares: {e}")

                # Also add a finding for high-risk shares (writable or open)
                if category == "open" or writable:
                    if category == "open":
                        severity = "high"
                    elif writable:
                        severity = "medium"
                    else:
                        severity = "low"

                    title = f"Writable SMB Share: {share_name}"
                    description = (
                        f"Share: {share_name}\n"
                        f"Type: {share_type}\n"
                        f"Comment: {share.get('comment', 'N/A')}\n"
                        f"Readable: {readable}, Writable: {writable}"
                    )

                    findings_manager.add_finding(
                        engagement_id=engagement_id,
                        host_id=host_id,
                        title=title,
                        finding_type="smb_share",
                        severity=severity,
                        description=description,
                        tool="enum4linux",
                        port=445,
                    )
                    findings_added += 1

            stats = get_smb_stats(parsed)

            # Extract domains for auto-chaining
            domains = []
            workgroup = stats.get("workgroup")
            common_workgroups = {"WORKGROUP", "MYGROUP", "MSHOME", "HOME"}
            if workgroup and workgroup.upper() not in common_workgroups:
                domains.append({"domain": workgroup, "ip": parsed.get("target")})

            # Check for errors
            enum4linux_error = detect_tool_error(output, "enum4linux")

            # Determine status
            has_results = (
                shares_added > 0
                or findings_added > 0
                or credentials_added > 0
                or len(parsed.get("users", [])) > 0
                or stats["total_shares"] > 0
            )
            has_positive_output = "[+]" in output

            if has_results:
                status = STATUS_DONE
            elif has_positive_output:
                status = STATUS_DONE
            elif enum4linux_error:
                status = STATUS_WARNING
            else:
                status = STATUS_NO_RESULTS

            return {
                "tool": "enum4linux",
                "status": status,
                "shares_added": shares_added,
                "findings_added": findings_added,
                "credentials_added": credentials_added,
                "users_found": len(parsed.get("users", [])),
                "shares_found": stats["total_shares"],
                "accessible_shares": stats["accessible_shares"],
                "writable_shares": stats["writable_shares"],
                "workgroup": stats.get("workgroup"),
                "domains": domains,
            }

        except Exception as e:
            logger.error(f"Error parsing enum4linux job: {e}")
            return {"error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful enum4linux results."""
        try:
            from souleyez.parsers.enum4linux_parser import parse_enum4linux_output

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            parsed = parse_enum4linux_output(log_content, job.get("target", ""))

            # Header
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo(click.style("SMB/SAMBA ENUMERATION", bold=True, fg="cyan"))
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

            if parsed.get("target"):
                click.echo(click.style(f"Target: {parsed['target']}", bold=True))
            elif job.get("target"):
                click.echo(click.style(f"Target: {job.get('target')}", bold=True))
            if parsed.get("workgroup"):
                click.echo(f"Workgroup/Domain: {parsed['workgroup']}")
            if parsed.get("domain_sid"):
                click.echo(f"Domain SID: {parsed['domain_sid']}")
            click.echo()

            # Collect all results
            users = parsed.get("users", [])
            groups = parsed.get("groups", [])
            shares = parsed.get("shares", [])

            has_results = (
                users
                or groups
                or shares
                or parsed.get("workgroup")
                or parsed.get("domain_sid")
            )

            if not has_results:
                self.display_no_results(job, log_path)
                return

            # Users
            if users:
                click.echo(
                    click.style(
                        f"Users Discovered ({len(users)}):", bold=True, fg="green"
                    )
                )
                max_users = None if show_all else 15
                display_users = users if max_users is None else users[:max_users]
                for user in display_users:
                    click.echo(f"  - {user}")
                if max_users and len(users) > max_users:
                    click.echo(f"  ... and {len(users) - max_users} more")
                click.echo()

            # Groups
            if groups:
                click.echo(
                    click.style(
                        f"Groups Discovered ({len(groups)}):", bold=True, fg="cyan"
                    )
                )
                max_groups = None if show_all else 10
                display_groups = groups if max_groups is None else groups[:max_groups]
                for group in display_groups:
                    click.echo(f"  - {group}")
                if max_groups and len(groups) > max_groups:
                    click.echo(f"  ... and {len(groups) - max_groups} more")
                click.echo()

            # Shares
            if shares:
                click.echo(
                    click.style(
                        f"Shares Found ({len(shares)}):", bold=True, fg="yellow"
                    )
                )
                for share in shares:
                    name = share.get("name", "")
                    share_type = share.get("type", "")
                    comment = share.get("comment", "")
                    mapping = share.get("mapping", "N/A")

                    # Color code by access
                    if mapping == "OK":
                        access_display = click.style("Accessible", fg="green")
                    elif mapping == "DENIED":
                        access_display = click.style("Denied", fg="red")
                    else:
                        access_display = click.style("Unknown", dim=True)

                    comment_str = f" - {comment}" if comment else ""
                    click.echo(
                        f"  - {name} ({share_type}) [{access_display}]{comment_str}"
                    )
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
        """Display warning status for enum4linux."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] ENUM4LINUX", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Scan completed with partial results or warnings.")
        click.echo("  Some queries may have failed. Check raw logs for details.")
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
        """Display error status for enum4linux."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] ENUM4LINUX FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common enum4linux errors
        error_msg = None
        if log_content:
            if "Connection refused" in log_content:
                error_msg = "Connection refused - SMB/NetBIOS service may be down"
            elif "timed out" in log_content.lower() or "timeout" in log_content.lower():
                error_msg = "Connection timed out - target may be slow or filtering"
            elif "NT_STATUS_ACCESS_DENIED" in log_content:
                error_msg = "Access denied - null session may be blocked"
            elif "NT_STATUS_LOGON_FAILURE" in log_content:
                error_msg = "Logon failure - authentication failed"
            elif "Errno 113" in log_content or "No route to host" in log_content:
                error_msg = "No route to host - network unreachable"
            elif "Could not initialise" in log_content:
                error_msg = "Could not initialize - target may not support SMB"

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
        """Display no_results status for enum4linux."""
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("SMB/SAMBA ENUMERATION", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

        if job.get("target"):
            click.echo(click.style(f"Target: {job.get('target')}", bold=True))
            click.echo()

        click.echo(
            click.style(
                "Result: No SMB/Samba information discovered", fg="yellow", bold=True
            )
        )
        click.echo()
        click.echo("  The scan did not find any users, groups, or shares.")
        click.echo()
        click.echo(click.style("Tips:", dim=True))
        click.echo("  - Check if SMB is enabled on the target")
        click.echo("  - Try with credentials for authenticated enumeration")
        click.echo("  - Verify the target IP is correct")
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
