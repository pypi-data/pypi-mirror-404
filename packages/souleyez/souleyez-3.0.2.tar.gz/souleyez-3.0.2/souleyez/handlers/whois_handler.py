#!/usr/bin/env python3
"""
WHOIS handler.

Consolidates parsing and display logic for WHOIS domain lookup jobs.
"""

import logging
import os
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class WhoisHandler(BaseToolHandler):
    """Handler for WHOIS domain lookup jobs."""

    tool_name = "whois"
    display_name = "WHOIS"

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
        Parse WHOIS job results.

        Extracts domain registration information and stores as OSINT data.
        """
        try:
            from souleyez.parsers.whois_parser import (
                extract_emails,
                map_to_osint_data,
                parse_whois_output,
            )
            from souleyez.storage.osint import OsintManager

            # Read the log file
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Parse WHOIS output
            target = job.get("target", "")
            parsed = parse_whois_output(log_content, target)

            # Store OSINT data
            om = OsintManager()
            osint_record = map_to_osint_data(parsed, engagement_id)
            om.add_osint_data(
                engagement_id,
                osint_record["data_type"],
                osint_record["target"],
                source=osint_record["source"],
                target=target,
                summary=osint_record["summary"],
                content=osint_record["content"],
                metadata=osint_record["metadata"],
            )

            # Extract emails and add separately for better querying
            emails = extract_emails(parsed)
            emails_added = 0
            if emails:
                emails_added = om.bulk_add_osint_data(
                    engagement_id, "email", emails, "whois", target
                )

            return {
                "tool": "whois",
                "status": (
                    STATUS_DONE
                    if (parsed.get("registrar") or parsed.get("nameservers"))
                    else STATUS_NO_RESULTS
                ),
                "domain": parsed.get("domain", target),
                "registrar": parsed.get("registrar"),
                "created": parsed.get("dates", {}).get("created"),
                "expires": parsed.get("dates", {}).get("expires"),
                "emails_found": len(emails),
                "nameservers": len(parsed.get("nameservers", [])),
                "osint_records_added": 1,
                "emails_added": emails_added,
            }

        except Exception as e:
            logger.error(f"Error parsing whois job: {e}")
            return {"error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful WHOIS results."""
        try:
            from souleyez.parsers.whois_parser import parse_whois_output

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            parsed = parse_whois_output(log_content, job.get("target", ""))

            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo(click.style("WHOIS DOMAIN INFORMATION", bold=True, fg="cyan"))
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

            # Check if we have any data
            has_data = (
                parsed.get("domain")
                or parsed.get("registrar")
                or parsed.get("dates")
                or parsed.get("nameservers")
                or parsed.get("status")
                or parsed.get("dnssec")
            )

            if has_data:
                # Domain and registrar
                if parsed.get("domain"):
                    click.echo(click.style(f"Domain: {parsed['domain']}", bold=True))
                elif job.get("target"):
                    click.echo(click.style(f"Target: {job.get('target')}", bold=True))
                if parsed.get("registrar"):
                    click.echo(f"Registrar: {parsed['registrar']}")
                click.echo()

                # Registration dates
                dates = parsed.get("dates", {})
                if dates:
                    click.echo(click.style("Registration Information:", bold=True))
                    if dates.get("created"):
                        click.echo(f"  Created: {dates['created']}")
                    if dates.get("updated"):
                        click.echo(f"  Updated: {dates['updated']}")
                    if dates.get("expires"):
                        click.echo(f"  Expires: {dates['expires']}")
                    click.echo()

                # Nameservers
                ns = parsed.get("nameservers", [])
                if ns:
                    click.echo(click.style(f"Nameservers: {len(ns)}", bold=True))
                    for server in ns:
                        click.echo(f"  - {server}")
                    click.echo()

                # Status
                status_list = parsed.get("status", [])
                if status_list:
                    click.echo(click.style("Domain Status:", bold=True))
                    for status in status_list:
                        click.echo(f"  - {status}")
                    click.echo()

                # DNSSEC
                if parsed.get("dnssec"):
                    click.echo(f"DNSSEC: {parsed['dnssec']}")
                    click.echo()
            else:
                self.display_no_results(job, log_path)
                return

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
        """Display warning status for WHOIS."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] WHOIS LOOKUP", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  WHOIS lookup completed with warnings.")
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
        """Display error status for WHOIS."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] WHOIS LOOKUP FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common whois errors
        error_msg = None
        if log_content:
            if "No match for" in log_content or "NOT FOUND" in log_content.upper():
                error_msg = "Domain not found in WHOIS database"
            elif "timed out" in log_content.lower() or "timeout" in log_content.lower():
                error_msg = "WHOIS query timed out - server may be slow"
            elif "Connection refused" in log_content:
                error_msg = "Connection refused - WHOIS server may be down"
            elif (
                "rate limit" in log_content.lower() or "too many" in log_content.lower()
            ):
                error_msg = "Rate limited - too many WHOIS queries"

        if error_msg:
            click.echo(f"  {error_msg}")
        else:
            click.echo("  Lookup failed - see raw logs for details (press 'r')")

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for WHOIS."""
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("WHOIS DOMAIN INFORMATION", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

        if job.get("target"):
            click.echo(click.style(f"Target: {job.get('target')}", bold=True))
            click.echo()

        click.echo(
            click.style("Result: No WHOIS information found", fg="yellow", bold=True)
        )
        click.echo()
        click.echo("  The WHOIS lookup did not return any information.")
        click.echo()
        click.echo(click.style("Tips:", dim=True))
        click.echo("  - Verify the domain name is correct")
        click.echo("  - Some domains have private WHOIS")
        click.echo("  - Try a different WHOIS server")
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
