#!/usr/bin/env python3
"""
Handler for Certipy - Active Directory Certificate Services (ADCS) enumeration.
Parses vulnerable certificate templates (ESC1-ESC8).
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)

STATUS_DONE = "done"
STATUS_ERROR = "error"
STATUS_WARNING = "warning"
STATUS_NO_RESULTS = "no_results"


class CertipyHandler(BaseToolHandler):
    """Handler for Certipy ADCS enumeration."""

    tool_name = "certipy"
    display_name = "Certipy"

    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    # ESC vulnerability patterns
    ESC_PATTERNS = {
        "ESC1": r"ESC1\s*:.*Enrollee Supplies Subject",
        "ESC2": r"ESC2\s*:.*Any Purpose",
        "ESC3": r"ESC3\s*:.*Certificate Request Agent",
        "ESC4": r"ESC4\s*:.*Vulnerable Access Control",
        "ESC5": r"ESC5\s*:.*PKI Object Access Control",
        "ESC6": r"ESC6\s*:.*EDITF_ATTRIBUTESUBJECTALTNAME2",
        "ESC7": r"ESC7\s*:.*CA Access Control",
        "ESC8": r"ESC8\s*:.*NTLM Relay.*AD CS",
        "ESC9": r"ESC9\s*:.*No Security Extension",
        "ESC10": r"ESC10\s*:.*Weak Certificate Mappings",
    }

    def parse_job(
        self,
        engagement_id: int,
        log_path: str,
        job: Dict[str, Any],
        host_manager: Optional[Any] = None,
        findings_manager: Optional[Any] = None,
        credentials_manager: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Parse certipy results."""
        try:
            target = job.get("target", "")
            if not log_path or not os.path.exists(log_path):
                return {
                    "tool": "certipy",
                    "status": STATUS_ERROR,
                    "error": "Log file not found",
                }

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Strip ANSI codes
            log_content = re.sub(r"\x1b\[[0-9;]*m", "", log_content)

            vulnerabilities = []
            templates = []
            cas = []  # Certificate Authorities
            domain = ""

            # Parse domain
            domain_match = re.search(r"Domain\s*:\s*(\S+)", log_content, re.IGNORECASE)
            if domain_match:
                domain = domain_match.group(1)

            # Track counts from summary output (certipy v5.x stdout format)
            template_count = 0
            ca_count = 0
            enabled_count = 0

            # Parse counts from stdout summary lines
            template_count_match = re.search(
                r"Found (\d+) certificate templates", log_content
            )
            if template_count_match:
                template_count = int(template_count_match.group(1))

            ca_count_match = re.search(r"Found (\d+) certificate authorit", log_content)
            if ca_count_match:
                ca_count = int(ca_count_match.group(1))

            enabled_count_match = re.search(
                r"Found (\d+) enabled certificate templates", log_content
            )
            if enabled_count_match:
                enabled_count = int(enabled_count_match.group(1))

            # Parse Certificate Authorities (from detailed output if available)
            ca_pattern = r"CA Name\s*:\s*(.+?)(?:\n|$)"
            for match in re.finditer(ca_pattern, log_content):
                ca_name = match.group(1).strip()
                if ca_name and ca_name not in cas:
                    cas.append(ca_name)

            # Also extract CA name from "CA configuration for 'name'" pattern
            ca_config_match = re.search(r"CA configuration for '([^']+)'", log_content)
            if ca_config_match:
                ca_name = ca_config_match.group(1)
                if ca_name and ca_name not in cas:
                    cas.append(ca_name)

            # Parse vulnerable templates (from detailed output if available)
            template_pattern = r"Template Name\s*:\s*(.+?)(?:\n|$)"
            for match in re.finditer(template_pattern, log_content):
                template_name = match.group(1).strip()
                if template_name and template_name not in templates:
                    templates.append(template_name)

            # Check for ESC vulnerabilities
            for esc_name, pattern in self.ESC_PATTERNS.items():
                if re.search(pattern, log_content, re.IGNORECASE):
                    # Extract the template name associated with this vulnerability
                    # Look for template name before the ESC finding
                    vuln = {
                        "type": esc_name,
                        "severity": (
                            "high"
                            if esc_name in ["ESC1", "ESC4", "ESC7", "ESC8"]
                            else "medium"
                        ),
                        "description": self._get_esc_description(esc_name),
                    }
                    vulnerabilities.append(vuln)

                    # Store as finding
                    if findings_manager and host_manager:
                        try:
                            host = host_manager.get_host_by_ip(engagement_id, target)
                            if host:
                                findings_manager.add_finding(
                                    host_id=host["id"],
                                    title=f"ADCS {esc_name} Vulnerability",
                                    severity=vuln["severity"],
                                    description=vuln["description"],
                                    tool="certipy",
                                    port=0,
                                    service="adcs",
                                )
                        except Exception as e:
                            logger.debug(f"Could not store finding: {e}")

            # Check for "[!] Vulnerabilities" section
            vuln_section = re.search(
                r"\[\!\]\s*Vulnerabilities", log_content, re.IGNORECASE
            )

            # Check for real errors (not just timeout warnings)
            has_real_error = False
            if "error" in log_content.lower() or "failed" in log_content.lower():
                # Exclude known non-fatal warnings
                non_fatal_patterns = [
                    "error checking web enrollment: timed out",
                    "error checking web enrollment",
                    "timed out",
                ]
                # Check if there are errors OTHER than non-fatal ones
                error_lines = [
                    line
                    for line in log_content.lower().split("\n")
                    if "error" in line or "failed" in line
                ]
                for line in error_lines:
                    is_non_fatal = any(
                        pattern in line for pattern in non_fatal_patterns
                    )
                    if not is_non_fatal:
                        has_real_error = True
                        break

            # Determine status - use counts if detailed lists are empty
            has_results = templates or cas or template_count > 0 or ca_count > 0

            if vulnerabilities:
                status = (
                    STATUS_WARNING
                    if any(v["severity"] == "high" for v in vulnerabilities)
                    else STATUS_DONE
                )
            elif has_results:
                status = STATUS_DONE
            elif has_real_error:
                status = STATUS_ERROR
            else:
                status = STATUS_NO_RESULTS

            result = {
                "tool": "certipy",
                "status": status,
                "target": target,
                "domain": domain,
                "certificate_authorities": cas,
                "templates": templates,
                "template_count": template_count,
                "ca_count": ca_count,
                "enabled_template_count": enabled_count,
                "vulnerabilities": vulnerabilities,
                "findings": vulnerabilities,  # For chaining compatibility
            }

            if vulnerabilities:
                logger.warning(
                    f"certipy: Found {len(vulnerabilities)} ADCS vulnerability(ies)!"
                )
            if template_count > 0 or templates:
                count = template_count if template_count > 0 else len(templates)
                logger.info(f"certipy: Found {count} certificate template(s)")

            return result

        except Exception as e:
            logger.error(f"Error parsing certipy job: {e}")
            return {"tool": "certipy", "status": STATUS_ERROR, "error": str(e)}

    def _get_esc_description(self, esc_type: str) -> str:
        """Get description for ESC vulnerability type."""
        descriptions = {
            "ESC1": "Template allows requestor to specify Subject Alternative Name (SAN). Attacker can request cert as any user.",
            "ESC2": "Template allows Any Purpose or no EKU. Can be used for any authentication.",
            "ESC3": "Template allows Certificate Request Agent enrollment. Can enroll on behalf of others.",
            "ESC4": "Template has vulnerable access control. Low-privileged users can modify template.",
            "ESC5": "PKI object has vulnerable access control. Can modify CA or template objects.",
            "ESC6": "CA has EDITF_ATTRIBUTESUBJECTALTNAME2 enabled. Requestor can specify SAN in any request.",
            "ESC7": "CA has vulnerable access control. Low-privileged users can manage CA.",
            "ESC8": "CA Web Enrollment or CEP/CES endpoints vulnerable to NTLM relay.",
            "ESC9": "Certificate has no security extension (szOID_NTDS_CA_SECURITY_EXT).",
            "ESC10": "Weak certificate mapping allows impersonation.",
        }
        return descriptions.get(esc_type, f"{esc_type} vulnerability detected")

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful certipy results."""
        import click

        parse_result = job.get("parse_result", {})

        domain = parse_result.get("domain", "")
        cas = parse_result.get("certificate_authorities", [])
        templates = parse_result.get("templates", [])
        vulnerabilities = parse_result.get("vulnerabilities", [])
        template_count = parse_result.get("template_count", 0)
        ca_count = parse_result.get("ca_count", 0)
        enabled_count = parse_result.get("enabled_template_count", 0)

        if domain:
            click.echo(f"  Domain: {domain}")

        # Show CA info
        if cas:
            click.secho(
                f"\n  Certificate Authorities ({len(cas)}):", fg="cyan", bold=True
            )
            for ca in cas:
                click.echo(f"    - {ca}")
        elif ca_count > 0:
            click.secho(
                f"\n  Certificate Authorities: {ca_count}", fg="cyan", bold=True
            )

        # Show template summary
        if template_count > 0 or enabled_count > 0:
            click.echo(
                f"\n  Templates: {template_count} total, {enabled_count} enabled"
            )

        if vulnerabilities:
            click.secho(
                f"\n  ADCS Vulnerabilities ({len(vulnerabilities)}):",
                fg="red",
                bold=True,
            )
            for vuln in vulnerabilities:
                esc_type = vuln.get("type", "")
                severity = vuln.get("severity", "medium")
                desc = vuln.get("description", "")

                color = "red" if severity == "high" else "yellow"
                click.secho(f"    [{esc_type}] {desc}", fg=color)
        elif template_count > 0:
            click.secho("\n  No vulnerable templates found (ESC1-ESC10)", fg="green")

        if templates and show_all:
            click.secho(f"\n  Certificate Templates ({len(templates)}):", fg="cyan")
            for template in templates[:10]:  # Limit display
                click.echo(f"    - {template}")
            if len(templates) > 10:
                click.echo(f"    ... and {len(templates) - 10} more")


# Register handler
handler = CertipyHandler()
