#!/usr/bin/env python3
"""
Responder handler.

Consolidates parsing and display logic for Responder credential capture jobs.
"""

import logging
import os
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class ResponderHandler(BaseToolHandler):
    """Handler for Responder credential capture jobs."""

    tool_name = "responder"
    display_name = "Responder"

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
        Parse Responder job results.

        Extracts captured NTLMv2 hashes and stores them.
        """
        try:
            from souleyez.parsers.responder_parser import (
                parse_responder,
                store_responder_results,
            )

            target = job.get("target", "")
            parsed = parse_responder(log_path, target)

            job_id = job.get("id")
            store_responder_results(parsed, engagement_id, job_id)

            return {
                "tool": "responder",
                "status": (
                    STATUS_DONE
                    if parsed.get("credentials_captured", 0) > 0
                    else STATUS_NO_RESULTS
                ),
                "interface": target,
                "credentials_captured": parsed.get("credentials_captured", 0),
                "hash_files": parsed.get("hash_files", []),  # For chaining to hashcat
                "summary": parsed.get("summary", "No results"),
            }

        except Exception as e:
            logger.error(f"Error parsing responder job: {e}")
            return {"error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful Responder results."""
        try:
            from souleyez.parsers.responder_parser import parse_responder

            if not log_path or not os.path.exists(log_path):
                return

            interface = job.get("args", {}).get(
                "interface", job.get("target", "unknown")
            )
            parsed = parse_responder(log_path, interface)

            credentials = parsed.get("credentials", [])
            summary = parsed.get("summary", "")

            click.echo(click.style("=" * 70, fg="green"))
            click.echo(click.style("RESPONDER RESULTS", bold=True, fg="green"))
            click.echo(click.style("=" * 70, fg="green"))
            click.echo()

            # Summary
            click.echo(click.style("Summary:", bold=True))
            click.echo(f"  {summary}")
            click.echo()

            # Show captured credentials
            if credentials:
                click.echo(
                    click.style(
                        f"Captured NTLMv2 Hashes ({len(credentials)}):",
                        bold=True,
                        fg="green",
                    )
                )
                max_show = None if show_all else 10
                display_creds = (
                    credentials if max_show is None else credentials[:max_show]
                )
                for c in display_creds:
                    domain = c.get("domain", "")
                    username = c.get("username", "?")
                    protocol = c.get("protocol", "?")
                    if domain:
                        click.echo(
                            click.style(
                                f"  [{protocol}] {domain}\\{username}", fg="green"
                            )
                        )
                    else:
                        click.echo(
                            click.style(f"  [{protocol}] {username}", fg="green")
                        )
                if max_show and len(credentials) > max_show:
                    click.echo(
                        click.style(
                            f"  ... and {len(credentials) - max_show} more", dim=True
                        )
                    )
                click.echo()
                click.echo(
                    click.style(
                        "  Tip: Crack these hashes with hashcat -m 5600", fg="cyan"
                    )
                )
            else:
                click.echo(click.style("  No credentials captured.", fg="yellow"))

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
        """Display warning status for Responder."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] RESPONDER", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Responder completed with warnings.")
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
        """Display error status for Responder."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] RESPONDER FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common responder errors
        error_msg = None
        if log_content:
            if "Permission denied" in log_content or "root" in log_content.lower():
                error_msg = "Permission denied - Responder requires root privileges"
            elif "Address already in use" in log_content:
                error_msg = "Port already in use - another service may be running"
            elif "No such device" in log_content or "Interface" in log_content:
                error_msg = "Invalid network interface - check interface name"
            elif "cannot bind" in log_content.lower():
                error_msg = "Cannot bind to port - check if ports are available"

        if error_msg:
            click.echo(f"  {error_msg}")
        else:
            click.echo("  Responder failed - check raw logs for details (press 'r')")

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for Responder."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("RESPONDER RESULTS", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  No credentials captured.")
        click.echo()
        click.echo(click.style("Possible reasons:", dim=True))
        click.echo("  - No LLMNR/NBT-NS/mDNS traffic on network")
        click.echo("  - Network is using proper DNS infrastructure")
        click.echo("  - Firewall blocking broadcast traffic")
        click.echo("  - Try running for longer or during peak hours")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
