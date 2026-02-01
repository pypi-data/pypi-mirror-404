#!/usr/bin/env python3
"""
Handler for BloodHound - Active Directory attack path mapping.
Parses bloodhound-python collection results.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

import click

from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)

STATUS_DONE = "done"
STATUS_ERROR = "error"
STATUS_WARNING = "warning"
STATUS_NO_RESULTS = "no_results"


class BloodhoundHandler(BaseToolHandler):
    """Handler for BloodHound AD collection."""

    tool_name = "bloodhound"
    display_name = "BloodHound"

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
        """Parse bloodhound-python results."""
        try:
            target = job.get("target", "")

            if not log_path or not os.path.exists(log_path):
                return {
                    "tool": "bloodhound",
                    "status": STATUS_ERROR,
                    "error": "Log file not found",
                }

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Check for errors
            if "ERROR" in log_content and "bloodhound-python not found" in log_content:
                return {
                    "tool": "bloodhound",
                    "status": STATUS_ERROR,
                    "error": "bloodhound-python not installed",
                }

            if "ERROR: Missing required arguments" in log_content:
                return {
                    "tool": "bloodhound",
                    "status": STATUS_ERROR,
                    "error": "Missing credentials",
                }

            # Check for authentication errors
            auth_errors = [
                "Authentication failed",
                "Invalid credentials",
                "Logon failure",
                "KDC_ERR_PREAUTH_FAILED",
                "KDC_ERR_C_PRINCIPAL_UNKNOWN",
            ]
            for err in auth_errors:
                if err.lower() in log_content.lower():
                    return {
                        "tool": "bloodhound",
                        "status": STATUS_ERROR,
                        "error": f"Authentication failed: {err}",
                    }

            # Parse collection statistics
            stats = {
                "users": 0,
                "groups": 0,
                "computers": 0,
                "domains": 0,
                "gpos": 0,
                "ous": 0,
                "containers": 0,
            }

            # Pattern: "Done in 00m 05s" or object counts
            patterns = [
                (r"(\d+)\s+user", "users"),
                (r"(\d+)\s+group", "groups"),
                (r"(\d+)\s+computer", "computers"),
                (r"(\d+)\s+domain", "domains"),
                (r"(\d+)\s+gpo", "gpos"),
                (r"(\d+)\s+ou", "ous"),
                (r"(\d+)\s+container", "containers"),
            ]

            for pattern, key in patterns:
                match = re.search(pattern, log_content, re.IGNORECASE)
                if match:
                    stats[key] = int(match.group(1))

            # Check for output files
            output_path = ""
            output_match = re.search(r"Output saved to:\s*(.+)", log_content)
            if output_match:
                output_path = output_match.group(1).strip()

            # Check for success indicators
            success = (
                "Data collection complete" in log_content
                or "Done in" in log_content
                or any(v > 0 for v in stats.values())
            )

            if success:
                status = STATUS_DONE
                total_objects = sum(stats.values())
                if total_objects == 0:
                    # Collected but no stats parsed - still success
                    status = STATUS_DONE
            elif "timeout" in log_content.lower():
                status = STATUS_ERROR
            else:
                status = STATUS_NO_RESULTS

            result = {
                "tool": "bloodhound",
                "status": status,
                "target": target,
                "stats": stats,
                "total_objects": sum(stats.values()),
                "output_path": output_path,
            }

            if sum(stats.values()) > 0:
                logger.info(f"bloodhound: Collected {sum(stats.values())} AD objects")

            return result

        except Exception as e:
            logger.error(f"Error parsing bloodhound job: {e}")
            return {"tool": "bloodhound", "status": STATUS_ERROR, "error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful bloodhound results."""
        click.echo()
        click.echo(click.style("=" * 70, fg="green"))
        click.echo(click.style("BLOODHOUND AD COLLECTION", fg="green", bold=True))
        click.echo(click.style("=" * 70, fg="green"))
        click.echo()

        parse_result = job.get("parse_result", {})
        stats = parse_result.get("stats", {})
        output_path = parse_result.get("output_path", "")
        total = parse_result.get("total_objects", 0)

        if total > 0:
            click.echo(click.style("  Objects Collected:", bold=True))
            for key, value in stats.items():
                if value > 0:
                    click.echo(f"    {key.capitalize()}: {value}")
            click.echo()

        if output_path:
            click.echo(f"  Output: {output_path}")
            click.echo()

        click.echo(click.style("  Next Steps:", fg="cyan"))
        click.echo("    1. Start BloodHound GUI: bloodhound")
        click.echo("    2. Import the ZIP file(s)")
        click.echo("    3. Run query: 'Shortest Path to Domain Admins'")
        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display bloodhound error."""
        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("BLOODHOUND COLLECTION FAILED", fg="red", bold=True))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        error = job.get("parse_result", {}).get("error") or job.get("error")
        if error:
            click.echo(f"  Error: {error}")
        else:
            click.echo("  Check log for details")
        click.echo()

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display bloodhound warning."""
        self.display_done(job, log_path, show_all, False)

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display bloodhound no results."""
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("BLOODHOUND NO DATA COLLECTED", fg="yellow", bold=True))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  No AD objects were collected.")
        click.echo("  Possible causes:")
        click.echo("    - Invalid credentials")
        click.echo("    - Network connectivity issues")
        click.echo("    - Domain controller not reachable")
        click.echo()


# Register handler
handler = BloodhoundHandler()
