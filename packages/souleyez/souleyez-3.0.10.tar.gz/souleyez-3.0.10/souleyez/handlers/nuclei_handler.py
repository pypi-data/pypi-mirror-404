#!/usr/bin/env python3
"""
Nuclei handler.

Consolidates parsing and display logic for nuclei vulnerability scanning jobs.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_ERROR, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class NucleiHandler(BaseToolHandler):
    """Handler for nuclei vulnerability scanning jobs."""

    tool_name = "nuclei"
    display_name = "Nuclei"

    # All handlers enabled
    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    # Severity mapping for database storage
    SEVERITY_MAP = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}

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
        Parse nuclei job results.

        Extracts vulnerabilities and stores them as findings.
        """
        try:
            from souleyez.engine.result_handler import detect_tool_error
            from souleyez.parsers.nuclei_parser import parse_nuclei

            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()
            if findings_manager is None:
                from souleyez.storage.findings import FindingsManager

                findings_manager = FindingsManager()

            target = job.get("target", "")
            parsed = parse_nuclei(log_path, target)

            if "error" in parsed:
                return parsed

            # Get or create host
            host_id = None
            parsed_url = urlparse(target)
            target_host = parsed_url.hostname or target

            if target_host:
                host_id = host_manager.add_or_update_host(
                    engagement_id, {"ip": target_host, "status": "up"}
                )

            # Store findings
            findings_added = 0
            for finding in parsed.get("findings", []):
                findings_added += self._store_finding(
                    finding, engagement_id, host_id, job, findings_manager
                )

            # Check for nuclei errors
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            nuclei_error = detect_tool_error(log_content, "nuclei")

            # Determine status based on results
            if nuclei_error:
                status = STATUS_ERROR
            elif parsed.get("findings_count", 0) > 0:
                status = STATUS_DONE
            else:
                status = STATUS_NO_RESULTS

            return {
                "tool": "nuclei",
                "status": status,
                "target": target,
                "findings_count": parsed.get("findings_count", 0),
                "findings_added": findings_added,
                "critical": parsed.get("critical", 0),
                "high": parsed.get("high", 0),
                "medium": parsed.get("medium", 0),
                "low": parsed.get("low", 0),
                "info": parsed.get("info", 0),
            }

        except Exception as e:
            logger.error(f"Error parsing nuclei job: {e}")
            return {"error": str(e)}

    def _store_finding(
        self,
        finding: Dict,
        engagement_id: int,
        host_id: Optional[int],
        job: Dict,
        findings_manager: Any,
    ) -> int:
        """Store a single nuclei finding."""
        severity = finding.get("severity", "info")
        title = finding.get("name", "Unknown Vulnerability")
        description = finding.get("description", "")

        # Add CVE and reference info to description
        if finding.get("cve_id"):
            description += f"\n\nCVE: {finding['cve_id']}"
        if finding.get("cvss_score"):
            description += f"\nCVSS Score: {finding['cvss_score']}"
        if finding.get("references"):
            description += f"\n\nReferences:\n" + "\n".join(finding["references"])

        # Add deduplication attribution if this scan covered multiple IPs
        metadata = job.get("metadata", {})
        associated_ips = metadata.get("associated_ips", [])
        if associated_ips and len(associated_ips) > 1:
            target_host = job.get("target", "")
            representative_ip = metadata.get("representative_ip", target_host)
            domain = metadata.get("domain_context", "")
            description += f"\n\n[Web Target Deduplication] This finding was discovered on {representative_ip}"
            description += f" (representative IP for {len(associated_ips)} IPs serving"
            if domain:
                description += f" {domain}"
            description += f"). All affected IPs: {', '.join(associated_ips)}"

        # Build evidence with matched_at, cve_id, and template_id
        evidence = f"Template: {finding.get('template_id', 'unknown')}"
        if finding.get("matched_at"):
            evidence += f"\nMatched at: {finding.get('matched_at')}"
        if finding.get("cve_id"):
            evidence += f"\nCVE: {finding.get('cve_id')}"

        findings_manager.add_finding(
            engagement_id=engagement_id,
            host_id=host_id,
            title=title,
            description=description,
            severity=severity,
            finding_type="vulnerability",
            tool="nuclei",
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
        """Display successful nuclei scan results."""
        try:
            from souleyez.parsers.nuclei_parser import parse_nuclei_output

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            parsed = parse_nuclei_output(log_content, job.get("target", ""))

            findings = parsed.get("findings", [])

            # Always show summary header
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo(click.style("VULNERABILITY SCAN", bold=True, fg="cyan"))
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

            click.echo(
                click.style(f"Target: {job.get('target', 'unknown')}", bold=True)
            )

            if findings:
                click.echo(
                    click.style(
                        f"Result: {len(findings)} vulnerability(ies) found",
                        fg="red",
                        bold=True,
                    )
                )
                click.echo()

                # Group by severity
                by_severity = {}
                for finding in findings:
                    severity = finding.get("severity", "info").lower()
                    if severity not in by_severity:
                        by_severity[severity] = []
                    by_severity[severity].append(finding)

                # Display in order: critical, high, medium, low, info
                max_per_severity = None if show_all else 5
                for severity in ["critical", "high", "medium", "low", "info"]:
                    if severity in by_severity:
                        items = by_severity[severity]
                        self._display_severity_section(
                            severity, items, max_per_severity
                        )

                click.echo(click.style("=" * 70, fg="cyan"))
                click.echo()
            else:
                self.display_no_results(job, log_path)

        except Exception as e:
            logger.debug(f"Error in display_done: {e}")

    def _display_severity_section(
        self, severity: str, items: List[Dict], max_items: Optional[int]
    ) -> None:
        """Display a severity section with findings."""
        # Color code severity
        if severity == "critical":
            sev_display = click.style(severity.upper(), fg="red", bold=True)
        elif severity == "high":
            sev_display = click.style(severity.upper(), fg="red")
        elif severity == "medium":
            sev_display = click.style(severity.upper(), fg="yellow")
        elif severity == "low":
            sev_display = click.style(severity.upper(), fg="blue")
        else:
            sev_display = click.style(severity.upper(), dim=True)

        click.echo(f"{sev_display}: {len(items)} finding(s)")

        display_items = items if max_items is None else items[:max_items]
        for finding in display_items:
            template = finding.get("template_id", "unknown")
            url = finding.get("matched_at", "")
            click.echo(f"  - [{template}] {url}")

        if max_items and len(items) > max_items:
            click.echo(f"    ... and {len(items) - max_items} more")
        click.echo()

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display warning status for nuclei scan."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] NUCLEI SCAN", bold=True, fg="yellow"))
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
        """Display error status for nuclei scan."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] NUCLEI SCAN FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common nuclei errors
        error_msg = None
        if log_content:
            if (
                "Could not run nuclei" in log_content
                or "not found" in log_content.lower()
            ):
                error_msg = "Nuclei binary not found - check installation"
            elif "no templates" in log_content.lower():
                error_msg = "No templates found - update nuclei templates"
            elif "rate limit" in log_content.lower():
                error_msg = "Rate limited by target - try with -rl flag"
            elif "timed out" in log_content.lower() or "timeout" in log_content.lower():
                error_msg = "Scan timed out - target may be slow or filtering"
            elif "Connection refused" in log_content:
                error_msg = "Connection refused - target may be down"
            elif "could not connect" in log_content.lower():
                error_msg = "Could not connect to target"
            elif "[ERR]" in log_content or "[FTL]" in log_content:
                match = re.search(r"\[(ERR|FTL)\]\s*(.+?)(?:\n|$)", log_content)
                if match:
                    error_msg = match.group(2).strip()[:100]

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
        """Display no_results status for nuclei scan."""
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("VULNERABILITY SCAN", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

        click.echo(click.style(f"Target: {job.get('target', 'unknown')}", bold=True))
        click.echo(
            click.style("Result: No vulnerabilities detected", fg="green", bold=True)
        )
        click.echo()
        click.echo("  The scan completed without finding any vulnerabilities.")
        click.echo("  This could mean the target is secure or templates didn't match.")
        click.echo()
        click.echo(click.style("Tips:", dim=True))
        click.echo(
            "  - Try different severity levels: -severity critical,high,medium,low"
        )
        click.echo("  - Try specific tags: -tags cve,exposure,misconfiguration")
        click.echo("  - Update templates: nuclei -update-templates")
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
