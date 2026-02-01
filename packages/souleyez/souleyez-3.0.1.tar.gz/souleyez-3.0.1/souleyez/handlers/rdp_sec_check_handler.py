#!/usr/bin/env python3
"""
Handler for rdp-sec-check RDP security scanner.
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


class RdpSecCheckHandler(BaseToolHandler):
    """Handler for rdp-sec-check RDP security scanner."""

    tool_name = "rdp-sec-check"
    display_name = "RDP Security Check"

    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    # Protocol support patterns
    PROTOCOL_RDP_PATTERN = r"supports PROTOCOL_RDP:\s*(TRUE|FALSE)"
    PROTOCOL_SSL_PATTERN = r"supports PROTOCOL_SSL:\s*(TRUE|FALSE)"
    PROTOCOL_HYBRID_PATTERN = r"supports PROTOCOL_HYBRID:\s*(TRUE|FALSE)"

    # Encryption patterns
    ENCRYPTION_LEVEL_PATTERN = r"encryption level:\s*(\S+)"

    # Security issue patterns
    ISSUE_PATTERN = r"has issue\s+(\S+)"

    # NLA patterns
    NLA_PATTERN = r"(NLA|Network Level Authentication).*?(required|not required|supported|not supported)"

    # Error patterns
    ERROR_PATTERNS = [
        (r"connection refused", "Connection refused"),
        (r"connection timed out", "Connection timed out"),
        (r"no route to host", "No route to host"),
        (r"unable to connect", "Unable to connect"),
        (r"failed to run command", "Tool not installed"),
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
        """Parse rdp-sec-check results."""
        try:
            target = job.get("target", "")

            if not log_path or not os.path.exists(log_path):
                return {
                    "tool": "rdp-sec-check",
                    "status": STATUS_ERROR,
                    "error": "Log file not found",
                }

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Check for errors first
            for pattern, error_msg in self.ERROR_PATTERNS:
                if re.search(pattern, log_content, re.IGNORECASE):
                    return {
                        "tool": "rdp-sec-check",
                        "status": STATUS_ERROR,
                        "target": target,
                        "error": error_msg,
                    }

            # Parse protocol support
            protocols = {}
            rdp_match = re.search(self.PROTOCOL_RDP_PATTERN, log_content, re.IGNORECASE)
            if rdp_match:
                protocols["rdp"] = rdp_match.group(1).upper() == "TRUE"

            ssl_match = re.search(self.PROTOCOL_SSL_PATTERN, log_content, re.IGNORECASE)
            if ssl_match:
                protocols["tls"] = ssl_match.group(1).upper() == "TRUE"

            hybrid_match = re.search(
                self.PROTOCOL_HYBRID_PATTERN, log_content, re.IGNORECASE
            )
            if hybrid_match:
                protocols["credssp"] = hybrid_match.group(1).upper() == "TRUE"

            # Parse encryption level
            encryption_level = None
            enc_match = re.search(
                self.ENCRYPTION_LEVEL_PATTERN, log_content, re.IGNORECASE
            )
            if enc_match:
                encryption_level = enc_match.group(1)

            # Parse security issues
            issues = re.findall(self.ISSUE_PATTERN, log_content, re.IGNORECASE)

            # Check NLA status
            nla_required = None
            nla_match = re.search(self.NLA_PATTERN, log_content, re.IGNORECASE)
            if nla_match:
                nla_status = nla_match.group(2).lower()
                nla_required = "required" in nla_status or "supported" in nla_status

            # Determine security findings
            findings = []

            # Check for NLA issues
            if "NLA_SUPPORTED_BUT_NOT_MANDATED" in log_content:
                findings.append(
                    {
                        "type": "misconfiguration",
                        "severity": "medium",
                        "title": "NLA Supported But Not Mandated",
                        "description": "NLA is supported but not required - allows downgrade attacks and pre-auth DoS",
                    }
                )
            elif nla_required is False:
                findings.append(
                    {
                        "type": "misconfiguration",
                        "severity": "high",
                        "title": "NLA Not Required",
                        "description": "Network Level Authentication is not required, enabling MITM attacks",
                    }
                )

            # RDP without TLS
            if protocols.get("rdp") and not protocols.get("tls"):
                findings.append(
                    {
                        "type": "misconfiguration",
                        "severity": "medium",
                        "title": "RDP Without TLS",
                        "description": "RDP is supported without TLS encryption",
                    }
                )

            # Weak encryption
            if encryption_level and encryption_level.upper() in [
                "NONE",
                "LOW",
                "CLIENT_COMPATIBLE",
            ]:
                findings.append(
                    {
                        "type": "misconfiguration",
                        "severity": "medium",
                        "title": f"Weak RDP Encryption: {encryption_level}",
                        "description": f"RDP encryption level is set to {encryption_level}",
                    }
                )

            # Check for SSL required (good config)
            ssl_required = "SSL_REQUIRED_BY_SERVER" in log_content

            # Store findings
            if findings and findings_manager and host_manager:
                host = host_manager.get_host_by_ip(engagement_id, target)
                if host:
                    for finding in findings:
                        try:
                            findings_manager.add_finding(
                                engagement_id=engagement_id,
                                host_id=host["id"],
                                finding_type=finding["type"],
                                severity=finding["severity"],
                                title=finding["title"],
                                description=finding["description"],
                                tool="rdp-sec-check",
                                port=3389,
                                service="rdp",
                            )
                        except Exception as e:
                            logger.warning(f"Failed to store finding: {e}")

            # Determine result
            if protocols or encryption_level or issues or findings:
                # Only warn on HIGH severity findings - medium/low are informational
                has_high_severity = any(f.get("severity") == "high" for f in findings)
                status = STATUS_WARNING if has_high_severity else STATUS_DONE
                return {
                    "tool": "rdp-sec-check",
                    "status": status,
                    "target": target,
                    "protocols": protocols,
                    "encryption_level": encryption_level,
                    "nla_required": nla_required,
                    "ssl_required": "SSL_REQUIRED_BY_SERVER" in log_content,
                    "issues": issues,
                    "findings": findings,
                    "findings_added": len(findings),
                }

            return {
                "tool": "rdp-sec-check",
                "status": STATUS_NO_RESULTS,
                "target": target,
            }

        except Exception as e:
            logger.error(f"Error parsing rdp-sec-check job: {e}")
            return {"tool": "rdp-sec-check", "status": STATUS_ERROR, "error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful rdp-sec-check results."""
        click.echo()
        click.echo(click.style("=" * 70, fg="green"))
        click.echo(click.style("RDP SECURITY CHECK COMPLETE", fg="green", bold=True))
        click.echo(click.style("=" * 70, fg="green"))
        click.echo()

        parse_result = job.get("parse_result", {})

        # Protocol support
        protocols = parse_result.get("protocols", {})
        if protocols:
            click.echo(click.style("  PROTOCOL SUPPORT", bold=True, fg="cyan"))
            for proto, supported in protocols.items():
                status = (
                    click.style("YES", fg="green")
                    if supported
                    else click.style("NO", fg="red")
                )
                click.echo(f"    {proto.upper()}: {status}")
            click.echo()

        # Encryption
        enc_level = parse_result.get("encryption_level")
        if enc_level:
            color = "green" if enc_level.upper() in ["HIGH", "FIPS"] else "yellow"
            click.echo(click.style("  ENCRYPTION", bold=True, fg="cyan"))
            click.echo(f"    Level: {click.style(enc_level, fg=color)}")
            click.echo()

        # NLA Status
        nla = parse_result.get("nla_required")
        if nla is not None:
            color = "green" if nla else "red"
            status = "Required" if nla else "NOT Required"
            click.echo(
                click.style("  NETWORK LEVEL AUTHENTICATION", bold=True, fg="cyan")
            )
            click.echo(f"    Status: {click.style(status, fg=color, bold=not nla)}")
            click.echo()

        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display rdp-sec-check error."""
        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("RDP SECURITY CHECK FAILED", fg="red", bold=True))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        error = job.get("parse_result", {}).get("error") or job.get("error")
        if error:
            click.echo(f"  Error: {error}")
        else:
            click.echo("  Check log for details")

        # Installation hint
        click.echo()
        click.echo(click.style("  Installation:", dim=True))
        click.echo("    Kali: sudo apt install rdp-sec-check")
        click.echo()

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display rdp-sec-check warning (security issues found)."""
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("RDP SECURITY ISSUES FOUND", fg="yellow", bold=True))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

        parse_result = job.get("parse_result", {})

        # Show findings
        findings = parse_result.get("findings", [])
        if findings:
            click.echo(click.style("  SECURITY FINDINGS", bold=True, fg="red"))
            for finding in findings:
                severity = finding.get("severity", "info").upper()
                sev_color = (
                    "red"
                    if severity == "HIGH"
                    else "yellow" if severity == "MEDIUM" else "white"
                )
                click.echo(
                    f"    [{click.style(severity, fg=sev_color)}] {finding.get('title')}"
                )
                click.echo(f"         {finding.get('description')}")
            click.echo()

        # Also show protocol info
        self.display_done(job, log_path, show_all, False)

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display rdp-sec-check no results."""
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(
            click.style("RDP SECURITY CHECK - NO RESULTS", fg="yellow", bold=True)
        )
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Could not retrieve RDP security information.")
        click.echo()
        click.echo(click.style("  Possible causes:", dim=True))
        click.echo("    - RDP service not responding")
        click.echo("    - Port blocked by firewall")
        click.echo("    - Non-standard RDP configuration")
        click.echo()
