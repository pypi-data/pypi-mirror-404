#!/usr/bin/env python3
"""
Nikto handler.

Consolidates parsing and display logic for nikto web scanner jobs.
"""

import logging
import os
import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_ERROR, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class NiktoHandler(BaseToolHandler):
    """Handler for nikto web scanner jobs."""

    tool_name = "nikto"
    display_name = "Nikto"

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
        Parse nikto job results.

        Extracts web server issues and stores them as findings.
        """
        try:
            from souleyez.engine.result_handler import detect_tool_error
            from souleyez.parsers.nikto_parser import parse_nikto_output

            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()
            if findings_manager is None:
                from souleyez.storage.findings import FindingsManager

                findings_manager = FindingsManager()

            target = job.get("target", "")

            # Read log file
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                output = f.read()

            parsed = parse_nikto_output(output, target)

            # Get or create host
            host_id = None
            target_ip = parsed.get("target_ip") or parsed.get("target_hostname")
            if not target_ip:
                parsed_url = urlparse(target)
                target_ip = parsed_url.hostname or target

            if target_ip:
                host_id = host_manager.add_or_update_host(
                    engagement_id,
                    {
                        "ip": target_ip,
                        "hostname": parsed.get("target_hostname", ""),
                        "status": "up",
                    },
                )

            # Store findings
            findings_added = 0
            for finding in parsed.get("findings", []):
                findings_added += self._store_finding(
                    finding, parsed, engagement_id, host_id, findings_manager
                )

            # Check for nikto errors
            nikto_error = detect_tool_error(output, "nikto")

            # Determine status based on results
            if nikto_error:
                status = STATUS_ERROR
            elif findings_added > 0:
                status = STATUS_DONE
            else:
                status = STATUS_NO_RESULTS

            # Build summary for job queue display
            summary_parts = []
            total_findings = parsed["stats"]["total"]
            if total_findings > 0:
                summary_parts.append(f"{total_findings} finding(s)")
            by_sev = parsed["stats"]["by_severity"]
            high_count = by_sev.get("critical", 0) + by_sev.get("high", 0)
            if high_count > 0:
                summary_parts.append(f"{high_count} high/critical")
            server = parsed.get("server", "")
            if server:
                summary_parts.append(server[:30])
            summary = " | ".join(summary_parts) if summary_parts else "No findings"

            return {
                "tool": "nikto",
                "status": status,
                "summary": summary,
                "target": target,
                "target_ip": parsed.get("target_ip", ""),
                "server": parsed.get("server", ""),
                "findings_count": parsed["stats"]["total"],
                "findings_added": findings_added,
                "by_severity": parsed["stats"]["by_severity"],
            }

        except Exception as e:
            logger.error(f"Error parsing nikto job: {e}")
            return {"error": str(e)}

    def _store_finding(
        self,
        finding: Dict,
        parsed: Dict,
        engagement_id: int,
        host_id: Optional[int],
        findings_manager: Any,
    ) -> int:
        """Store a single nikto finding."""
        severity = finding.get("severity", "info")

        # Build title from OSVDB or path + description
        osvdb = finding.get("osvdb")
        path = finding.get("path", "/")
        desc = finding.get("description", "")

        if osvdb:
            title = f"Nikto: {osvdb} - {path}"
        elif path:
            title = f"Nikto: {path} - {desc[:50]}{'...' if len(desc) > 50 else ''}"
        else:
            title = f"Nikto Finding: {desc[:60]}{'...' if len(desc) > 60 else ''}"

        # Build description with server info
        description = desc
        if parsed.get("server"):
            description += f"\n\nServer: {parsed['server']}"
        if osvdb:
            description += f"\n\nReference: {osvdb}"
        if path:
            description += f"\nPath: {path}"

        # Build evidence
        evidence = f"Detected by Nikto web scanner"
        if path:
            evidence += f"\nPath: {path}"
        if osvdb:
            evidence += f"\nOSVDB: {osvdb}"

        findings_manager.add_finding(
            engagement_id=engagement_id,
            host_id=host_id,
            title=title,
            description=description,
            severity=severity,
            finding_type="misconfiguration",
            tool="nikto",
            evidence=evidence,
        )
        return 1

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful nikto scan results."""
        try:
            from souleyez.parsers.nikto_parser import parse_nikto_output

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            parsed = parse_nikto_output(log_content, job.get("target", ""))

            findings = parsed.get("findings", [])

            # Always show header
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo(click.style("NIKTO SCAN RESULTS", bold=True, fg="cyan"))
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

            # Target info
            if parsed.get("target_ip"):
                click.echo(click.style(f"Target: {parsed['target_ip']}", bold=True))
            elif job.get("target"):
                click.echo(click.style(f"Target: {job.get('target')}", bold=True))
            if parsed.get("server"):
                click.echo(f"Server: {parsed['server']}")
            if parsed.get("target_port"):
                click.echo(f"Port: {parsed['target_port']}")
            click.echo()

            if findings:
                # Stats
                stats = parsed.get("stats", {})
                by_severity = stats.get("by_severity", {})
                click.echo(
                    click.style(
                        f"Findings: {stats.get('total', len(findings))}", bold=True
                    )
                )
                severity_parts = []
                if by_severity.get("high", 0) > 0:
                    severity_parts.append(
                        click.style(f"{by_severity['high']} High", fg="red")
                    )
                if by_severity.get("medium", 0) > 0:
                    severity_parts.append(
                        click.style(f"{by_severity['medium']} Medium", fg="yellow")
                    )
                if by_severity.get("low", 0) > 0:
                    severity_parts.append(
                        click.style(f"{by_severity['low']} Low", fg="cyan")
                    )
                if by_severity.get("info", 0) > 0:
                    severity_parts.append(f"{by_severity['info']} Info")
                if severity_parts:
                    click.echo("  " + " | ".join(severity_parts))
                click.echo()

                # List findings
                max_findings = None if show_all else 15
                click.echo(click.style("Issues Found:", bold=True))
                display_findings = (
                    findings if max_findings is None else findings[:max_findings]
                )

                for i, finding in enumerate(display_findings, 1):
                    severity = finding.get("severity", "info")
                    desc = finding.get("description", "")[:60]
                    path = finding.get("path", "")

                    # Color by severity
                    if severity == "high":
                        sev_color = "red"
                    elif severity == "medium":
                        sev_color = "yellow"
                    elif severity == "low":
                        sev_color = "cyan"
                    else:
                        sev_color = "white"

                    sev_badge = click.style(f"[{severity.upper()}]", fg=sev_color)
                    if path:
                        click.echo(f"  {i}. {sev_badge} {path}: {desc}")
                    else:
                        click.echo(f"  {i}. {sev_badge} {desc}")

                if max_findings and len(findings) > max_findings:
                    click.echo(
                        f"  ... and {len(findings) - max_findings} more findings"
                    )
                click.echo()

                # Display next steps suggestions
                try:
                    from souleyez.parsers.nikto_parser import generate_next_steps

                    next_steps = generate_next_steps(parsed, job.get("target", ""))
                    if next_steps:
                        click.echo(click.style("=" * 70, fg="green"))
                        click.echo(
                            click.style("SUGGESTED NEXT STEPS", bold=True, fg="green")
                        )
                        click.echo(click.style("=" * 70, fg="green"))
                        click.echo()
                        for i, step in enumerate(next_steps[:5], 1):
                            click.echo(click.style(f"{i}. {step['title']}", bold=True))
                            click.echo(
                                click.style(f"   Why: {step['reason']}", fg="white")
                            )
                            for cmd in step.get("commands", [])[:2]:
                                click.echo(click.style(f"   $ {cmd}", fg="cyan"))
                            click.echo()
                        if len(next_steps) > 5:
                            click.echo(
                                f"   ... and {len(next_steps) - 5} more suggestions"
                            )
                            click.echo()
                except Exception as e:
                    logger.debug(f"Next steps display failed: {e}")
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
        """Display warning status for nikto scan."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] NIKTO SCAN", bold=True, fg="yellow"))
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
        """Display error status for nikto scan."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] NIKTO SCAN FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common nikto errors
        error_msg = None
        if log_content:
            if (
                "Unable to connect" in log_content
                or "Connection refused" in log_content
            ):
                error_msg = (
                    "Unable to connect to target - check if web server is running"
                )
            elif "timed out" in log_content.lower() or "timeout" in log_content.lower():
                error_msg = "Connection timed out - target may be slow or filtering"
            elif "No web server found" in log_content:
                error_msg = "No web server found on target port"
            elif "ssl handshake" in log_content.lower():
                error_msg = "SSL handshake failed - try with/without -ssl flag"
            elif "ERROR:" in log_content:
                match = re.search(r"ERROR:\s*(.+?)(?:\n|$)", log_content)
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
        """Display no_results status for nikto scan."""
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("NIKTO SCAN RESULTS", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

        if job.get("target"):
            click.echo(click.style(f"Target: {job.get('target')}", bold=True))
            click.echo()

        click.echo(click.style("Result: No issues detected", fg="green", bold=True))
        click.echo()
        click.echo("  The scan completed without finding any web server issues.")
        click.echo()
        click.echo(click.style("Tips:", dim=True))
        click.echo("  - Try with different tuning: -T 1-9 for specific test types")
        click.echo("  - Check if the target web server is running")
        click.echo("  - Use -Cgidirs to specify CGI directories")
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
