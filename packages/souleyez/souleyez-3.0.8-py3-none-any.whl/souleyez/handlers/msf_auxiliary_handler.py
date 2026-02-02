#!/usr/bin/env python3
"""
Metasploit auxiliary handler.

Consolidates parsing and display logic for msf_auxiliary jobs.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS, STATUS_WARNING
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class MsfAuxiliaryHandler(BaseToolHandler):
    """Handler for Metasploit auxiliary module jobs."""

    tool_name = "msf_auxiliary"
    display_name = "Metasploit Auxiliary"

    # All handlers enabled
    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    # Connection failure patterns
    CONNECTION_FAILURE_PATTERNS = [
        (r"Could not connect.*timed?\s*out", "Connection timed out"),
        (r"Connection refused", "Connection refused"),
        (r"Rex::ConnectionTimeout", "Connection timed out"),
        (r"Rex::ConnectionRefused", "Connection refused"),
        (r"No route to host", "No route to host"),
        (r"Network is unreachable", "Network unreachable"),
        (r"Login Failed.*Session Request failed", "SMB session request failed"),
        (r"SMB Login Error", "SMB login error"),
        (r"Connection reset by peer", "Connection reset"),
        (r"Called name not present", "NetBIOS name not found"),
        (r"DCERPC FAULT.*nca_s_fault_access_denied", "RPC access denied"),
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
        Parse MSF auxiliary job results.

        Extracts findings, credentials, and services from the output.
        """
        try:
            from souleyez.parsers.msf_parser import parse_msf_log

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

            # Read raw log for connection failure detection
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                raw_content = f.read()

            # Check for connection failures BEFORE parsing
            connection_failure = False
            failure_reason = None
            for pattern, reason in self.CONNECTION_FAILURE_PATTERNS:
                if re.search(pattern, raw_content, re.IGNORECASE):
                    connection_failure = True
                    failure_reason = reason
                    break

            # Parse the log
            parsed = parse_msf_log(log_path)

            if "error" in parsed:
                return {"error": parsed["error"]}

            target = job.get("target", "")

            services_added = 0
            findings_added = 0
            credentials_added = 0
            finding_summaries = []
            credential_summaries = []

            # Get or create host
            host = host_manager.get_host_by_ip(engagement_id, target)
            if not host:
                host_id = host_manager.add_host(engagement_id, target)
            else:
                host_id = host["id"]

            # Add services if any
            for svc in parsed.get("services", []):
                host_manager.add_service(
                    host_id,
                    {
                        "port": svc.get("port"),
                        "protocol": svc.get("protocol", "tcp"),
                        "state": svc.get("state", "open"),
                        "service": svc.get("service_name"),
                        "version": svc.get("service_version"),
                    },
                )
                services_added += 1

            # Add findings
            for finding in parsed.get("findings", []):
                findings_manager.add_finding(
                    engagement_id=engagement_id,
                    host_id=host_id,
                    title=finding.get("title"),
                    finding_type=(
                        "credential"
                        if "credential" in finding.get("title", "").lower()
                        else "security_issue"
                    ),
                    severity=finding.get("severity", "info"),
                    description=finding.get("description"),
                    tool="msf_auxiliary",
                    port=finding.get("port"),
                )
                findings_added += 1
                finding_summaries.append(
                    {
                        "title": finding.get("title"),
                        "severity": finding.get("severity", "info"),
                        "description": finding.get("description", "")[:200],
                    }
                )

            # Add credentials if any
            for cred in parsed.get("credentials", []):
                credentials_manager.add_credential(
                    engagement_id=engagement_id,
                    host_id=host_id,
                    service=cred.get("service", "unknown"),
                    username=cred.get("username", ""),
                    password=cred.get("password", ""),
                    credential_type="password",
                    tool="msf_auxiliary",
                    port=cred.get("port"),
                    status=cred.get("status", "valid"),
                )
                credentials_added += 1
                credential_summaries.append(
                    {
                        "username": cred.get("username", ""),
                        "password": cred.get("password", ""),
                        "service": cred.get("service", "unknown"),
                        "port": cred.get("port"),
                    }
                )

            # Determine status and summary
            has_results = (
                services_added > 0 or findings_added > 0 or credentials_added > 0
            )

            if has_results:
                final_status = STATUS_DONE
                summary = (
                    f"Found {findings_added} findings, {credentials_added} credentials"
                )
            elif connection_failure:
                final_status = STATUS_WARNING
                summary = f"Target unreachable: {failure_reason}"
            else:
                final_status = STATUS_NO_RESULTS
                summary = "No results found (target responded but nothing discovered)"

            return {
                "tool": "msf_auxiliary",
                "status": final_status,
                "summary": summary,
                "host": target,
                "services_added": services_added,
                "findings_added": findings_added,
                "credentials_added": credentials_added,
                "findings": finding_summaries,
                "credentials": credential_summaries,
            }
        except Exception as e:
            logger.error(f"Error parsing msf_auxiliary job: {e}")
            return {"error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful auxiliary scan results."""
        try:
            from souleyez.parsers.msf_parser import parse_msf_log

            if not log_path or not os.path.exists(log_path):
                return

            parsed = parse_msf_log(log_path)
            findings = parsed.get("findings", [])
            credentials = parsed.get("credentials", [])
            services = parsed.get("services", [])

            if not findings and not credentials and not services:
                return

            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo(click.style("PARSED RESULTS", bold=True, fg="cyan"))
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

            # Show findings
            if findings:
                severity_colors = {
                    "critical": "red",
                    "high": "red",
                    "medium": "yellow",
                    "low": "blue",
                    "info": "cyan",
                }
                click.echo(click.style(f"Findings ({len(findings)}):", bold=True))
                for f in findings[:10]:
                    sev = f.get("severity", "info")
                    color = severity_colors.get(sev, "white")
                    title = f.get("title", "Unknown")
                    click.echo(click.style(f"  [{sev.upper()}] ", fg=color) + title)
                    # Show description if it has useful details
                    desc = f.get("description", "")
                    if desc and desc != title and len(desc) > len(title):
                        if len(desc) > 120:
                            desc = desc[:117] + "..."
                        click.echo(click.style(f"           {desc}", fg="bright_black"))
                if len(findings) > 10:
                    click.echo(f"  ... and {len(findings) - 10} more findings")
                click.echo()

            # Show credentials
            if credentials:
                click.echo(click.style(f"Credentials ({len(credentials)}):", bold=True))
                creds_to_show = credentials if show_all else credentials[:5]
                for c in creds_to_show:
                    user = c.get("username", "")
                    pwd = c.get("password", "")
                    svc = c.get("service", "unknown")
                    if pwd and show_passwords:
                        click.echo(click.style(f"  {svc}: {user}:{pwd}", fg="green"))
                    elif pwd:
                        click.echo(click.style(f"  {svc}: {user}:******", fg="green"))
                    else:
                        click.echo(f"  {svc}: {user} (username only)")
                if not show_all and len(credentials) > 5:
                    click.echo(
                        click.style(
                            f"  ... and {len(credentials) - 5} more (press [x] to expand)",
                            fg="bright_black",
                        )
                    )
                click.echo()

            # Show services
            if services:
                click.echo(click.style(f"Services ({len(services)}):", bold=True))
                for s in services[:5]:
                    port = s.get("port", "?")
                    name = s.get("service_name", "unknown")
                    ver = s.get("service_version", "")
                    click.echo(f"  {port}/{name}: {ver}" if ver else f"  {port}/{name}")
                if len(services) > 5:
                    click.echo(f"  ... and {len(services) - 5} more services")
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
        """Display warning status for auxiliary scan."""
        parse_result = job.get("parse_result", {})
        summary = "Auxiliary scan failed"
        if isinstance(parse_result, dict):
            summary = parse_result.get("summary", "Auxiliary scan failed")

        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(
            click.style("[WARNING] METASPLOIT AUXILIARY", bold=True, fg="yellow")
        )
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo(f"  {summary}")
        click.echo()
        click.echo(click.style("  Common causes:", fg="bright_black"))
        click.echo(
            click.style(
                "    - Target unreachable (firewall, network issue)", fg="bright_black"
            )
        )
        click.echo(
            click.style("    - Service not running on expected port", fg="bright_black")
        )
        click.echo(click.style("    - Connection timed out", fg="bright_black"))
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display error status for auxiliary scan."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(
            click.style("[ERROR] METASPLOIT AUXILIARY FAILED", bold=True, fg="red")
        )
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common MSF errors
        error_msg = None
        if log_content:
            if "Connection refused" in log_content:
                error_msg = "Connection refused - target service may be down"
            elif "timed out" in log_content.lower() or "timeout" in log_content.lower():
                error_msg = "Connection timed out - target may be slow or filtering"
            elif "Exploit failed" in log_content:
                error_msg = "Exploit failed - target may not be vulnerable"
            elif "Module not found" in log_content or "Unknown module" in log_content:
                error_msg = "Module not found - check module name"
            elif "Required option" in log_content:
                match = re.search(
                    r'Required option\s*[\'"]?(\w+)[\'"]?\s*is missing', log_content
                )
                if match:
                    error_msg = f"Required option '{match.group(1)}' is missing"
            elif "[-]" in log_content:
                match = re.search(r"\[-\]\s*(.+?)(?:\n|$)", log_content)
                if match:
                    error_msg = match.group(1).strip()[:100]

        if error_msg:
            click.echo(f"  {error_msg}")
        else:
            click.echo("  Module failed - see raw logs for details (press 'r')")

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for auxiliary scan."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("METASPLOIT AUXILIARY RESULTS", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  No results found.")
        click.echo()
        click.echo(
            click.style(
                "  The target responded but the module found nothing.",
                fg="bright_black",
            )
        )
        click.echo(click.style("  This could mean:", fg="bright_black"))
        click.echo(click.style("    - Service is not vulnerable", fg="bright_black"))
        click.echo(click.style("    - No valid credentials found", fg="bright_black"))
        click.echo(click.style("    - No matching configuration", fg="bright_black"))
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
