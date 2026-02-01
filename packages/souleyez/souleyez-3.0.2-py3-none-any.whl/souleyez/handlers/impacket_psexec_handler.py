#!/usr/bin/env python3
"""
Impacket psexec handler.

Consolidates parsing and display logic for Impacket psexec remote execution jobs.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class ImpacketPsexecHandler(BaseToolHandler):
    """Handler for Impacket psexec remote execution jobs."""

    tool_name = "impacket-psexec"
    display_name = "PSExec"

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
        Parse psexec job results.

        Checks for successful remote shell establishment.
        """
        try:
            from souleyez.parsers.impacket_parser import parse_psexec

            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()

            target = job.get("target", "")
            parsed = parse_psexec(log_path, target)

            if "error" in parsed:
                return parsed

            # Get or create host
            host_id = None
            ip_match = re.search(r"@?(\d+\.\d+\.\d+\.\d+)", target)
            if ip_match:
                host_ip = ip_match.group(1)
                host_id = host_manager.add_or_update_host(
                    engagement_id, {"ip": host_ip, "status": "up"}
                )

            success = parsed.get("success", False)

            return {
                "tool": "impacket-psexec",
                "status": STATUS_DONE if success else STATUS_NO_RESULTS,
                "target": target,
                "success": success,
                "output_lines": parsed.get("output_lines", 0),
            }

        except Exception as e:
            logger.error(f"Error parsing psexec job: {e}")
            return {"error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful psexec results."""
        try:
            from souleyez.parsers.impacket_parser import parse_psexec

            if not log_path or not os.path.exists(log_path):
                return

            target = job.get("target", "unknown")
            parsed = parse_psexec(log_path, target)

            success = parsed.get("success", False)
            output_lines = parsed.get("output_lines", 0)

            click.echo(click.style("=" * 70, fg="green"))
            click.echo(click.style("PSEXEC RESULTS", bold=True, fg="green"))
            click.echo(click.style("=" * 70, fg="green"))
            click.echo()

            if success:
                click.echo(
                    click.style("  [SUCCESS] Remote shell established!", fg="green")
                )
                click.echo(f"  Output lines captured: {output_lines}")
                click.echo()
                click.echo("  Press 'r' to view full command output.")
            else:
                click.echo(
                    click.style(
                        "  Connection made but no shell prompt detected.", fg="yellow"
                    )
                )
                click.echo("  Press 'r' to view raw output for details.")

            click.echo()
            click.echo(click.style("=" * 70, fg="green"))
            click.echo()

        except Exception as e:
            logger.debug(f"Error in display_done: {e}")

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display warning status for psexec."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] PSEXEC", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Remote execution completed with warnings.")
        click.echo("  Check raw logs for details (press 'r').")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display error status for psexec."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] PSEXEC FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common psexec errors
        error_msg = None
        if log_content:
            if "Connection refused" in log_content:
                error_msg = "Connection refused - target SMB service may be down"
            elif (
                "Access denied" in log_content.lower()
                or "STATUS_ACCESS_DENIED" in log_content
            ):
                error_msg = "Access denied - need admin privileges on target"
            elif "STATUS_LOGON_FAILURE" in log_content:
                error_msg = "Logon failure - invalid credentials"
            elif "timed out" in log_content.lower() or "timeout" in log_content.lower():
                error_msg = "Connection timed out - target may be unreachable"
            elif (
                "Service installation" in log_content
                and "failed" in log_content.lower()
            ):
                error_msg = "Service installation failed - AV may be blocking"
            elif "ERROR_SERVICE" in log_content or (
                "service" in log_content.lower() and "error" in log_content.lower()
            ):
                error_msg = "Service error - may be blocked by endpoint protection"

        if error_msg:
            click.echo(f"  {error_msg}")
        else:
            click.echo(
                "  Remote execution failed - check raw logs for details (press 'r')"
            )

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for psexec."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("PSEXEC RESULTS", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  No command output captured.")
        click.echo()
        click.echo(click.style("Possible reasons:", dim=True))
        click.echo("  - Connection failed before shell was established")
        click.echo("  - Insufficient privileges (need local admin)")
        click.echo("  - AV/EDR blocked the service installation")
        click.echo("  - Try smbexec or wmiexec as alternatives")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
