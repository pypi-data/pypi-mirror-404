#!/usr/bin/env python3
"""
Evidence bundle export to ZIP.
Creates organized ZIP archive of all engagement evidence.
"""

import os
import zipfile
from datetime import datetime
from typing import Dict, List


def create_evidence_bundle(
    engagement_id: int, engagement: Dict, evidence: Dict[str, List[Dict]]
) -> str:
    """
    Create ZIP bundle of all evidence.

    Returns:
        Path to created ZIP file
    """
    # Create output directory
    output_dir = os.path.expanduser("~/.souleyez/exports")
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = (
        engagement["name"].replace(" ", "_").replace("/", "_").replace("\\", "_")
    )
    zip_filename = f"{safe_name}_evidence_{timestamp}.zip"
    zip_path = os.path.join(output_dir, zip_filename)

    # Create ZIP
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add README
        readme = generate_readme(engagement, evidence)
        zipf.writestr("README.txt", readme)

        # Add evidence by phase
        for phase, items in evidence.items():
            phase_dir = phase.replace("_", "-")

            # Create phase summary
            phase_summary = generate_phase_summary(phase, items)
            zipf.writestr(f"{phase_dir}/SUMMARY.txt", phase_summary)

            for idx, item in enumerate(items, 1):
                if item["type"] == "job":
                    # Add job log if exists
                    log_path = item.get("log_path")
                    if log_path and os.path.exists(log_path):
                        safe_tool = item["tool"].replace("/", "_")
                        safe_target = (
                            item["target"].replace("/", "_").replace(":", "_")[:50]
                        )
                        arcname = f"{phase_dir}/{idx:03d}_{safe_tool}_{safe_target}.log"
                        zipf.write(log_path, arcname)

        # Add credentials file
        creds_content = export_credentials(engagement_id)
        if creds_content:
            zipf.writestr("CREDENTIALS.txt", creds_content)

        # Add findings file
        findings_content = export_findings(engagement_id)
        if findings_content:
            zipf.writestr("FINDINGS.txt", findings_content)

        # Add hosts summary
        hosts_content = export_hosts(engagement_id)
        if hosts_content:
            zipf.writestr("HOSTS.txt", hosts_content)

    return zip_path


def generate_readme(engagement: Dict, evidence: Dict[str, List[Dict]]) -> str:
    """Generate README for evidence bundle."""
    lines = []
    lines.append("=" * 70)
    lines.append(f"EVIDENCE BUNDLE: {engagement['name']}")
    lines.append("=" * 70)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Engagement ID: {engagement['id']}")
    lines.append("")

    # Summary
    total = sum(len(items) for items in evidence.values())
    lines.append(f"Total Evidence Items: {total}")
    lines.append("")

    lines.append("Evidence by Phase:")
    lines.append("-" * 70)
    for phase, items in evidence.items():
        phase_name = phase.replace("_", " ").title()
        lines.append(f"  {phase_name:30} {len(items):3} items")

    lines.append("")
    lines.append("=" * 70)
    lines.append("")
    lines.append("DIRECTORY STRUCTURE")
    lines.append("=" * 70)
    lines.append("")
    lines.append("  reconnaissance/")
    lines.append("    - Port scans (nmap, masscan)")
    lines.append("    - OSINT data (theHarvester, whois)")
    lines.append("    - DNS enumeration (dnsrecon)")
    lines.append("")
    lines.append("  enumeration/")
    lines.append("    - Web scanning (nuclei, gobuster)")
    lines.append("    - Service enumeration (SMB, NFS)")
    lines.append("    - User discovery")
    lines.append("")
    lines.append("  exploitation/")
    lines.append("    - Exploit attempts (Metasploit)")
    lines.append("    - SQL injection (sqlmap)")
    lines.append("    - Brute force (hydra)")
    lines.append("    - Credentials discovered")
    lines.append("    - Security findings")
    lines.append("")
    lines.append("  post-exploitation/")
    lines.append("    - System files")
    lines.append("    - Configuration files")
    lines.append("    - Database dumps")
    lines.append("")
    lines.append("  CREDENTIALS.txt  - All discovered credentials")
    lines.append("  FINDINGS.txt     - All security findings")
    lines.append("  HOSTS.txt        - Discovered hosts summary")
    lines.append("")
    lines.append("=" * 70)
    lines.append("")
    lines.append("NOTES")
    lines.append("=" * 70)
    lines.append("")
    lines.append("- Log files contain full tool output")
    lines.append("- Each phase has a SUMMARY.txt with item details")
    lines.append("- Timestamps are in UTC")
    lines.append("- Sensitive data (passwords) may be redacted")
    lines.append("")

    return "\n".join(lines)


def generate_phase_summary(phase: str, items: List[Dict]) -> str:
    """Generate summary for a phase."""
    lines = []
    phase_name = phase.replace("_", " ").upper()

    lines.append("=" * 70)
    lines.append(f"{phase_name} - EVIDENCE SUMMARY")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Total Items: {len(items)}")
    lines.append("")

    for idx, item in enumerate(items, 1):
        lines.append(f"[{idx:03d}] {item['title']}")
        lines.append(f"      Tool: {item['tool']}")
        lines.append(f"      Target: {item['target']}")
        lines.append(f"      Date: {item['created_at']}")
        lines.append(f"      Description: {item['description']}")

        if item["type"] == "finding":
            lines.append(f"      Severity: {item['severity'].upper()}")
        elif item["type"] == "credential":
            lines.append(f"      Type: Credential Discovery")

        lines.append("")

    return "\n".join(lines)


def export_credentials(engagement_id: int) -> str:
    """Export credentials as text."""
    from souleyez.storage.credentials import CredentialsManager

    cm = CredentialsManager()
    creds = cm.list_credentials(engagement_id)

    if not creds:
        return ""

    lines = []
    lines.append("=" * 70)
    lines.append("CREDENTIALS DISCOVERED")
    lines.append("=" * 70)
    lines.append(f"Total: {len(creds)} credentials")
    lines.append("")

    for idx, cred in enumerate(creds, 1):
        lines.append(
            f"[{idx:03d}] Host: {cred.get('host', 'N/A')}:{cred.get('port', '?')}"
        )
        lines.append(f"      Service: {cred.get('service', 'unknown')}")
        lines.append(f"      Username: {cred.get('username', 'N/A')}")
        lines.append(f"      Status: {cred.get('status', 'unknown')}")
        lines.append(f"      Source: {cred.get('source', 'unknown')}")
        lines.append(f"      Created: {cred.get('created_at', 'N/A')}")
        lines.append("-" * 70)

    return "\n".join(lines)


def export_findings(engagement_id: int) -> str:
    """Export findings as text."""
    from souleyez.storage.findings import FindingsManager

    fm = FindingsManager()
    findings = fm.list_findings(engagement_id)

    if not findings:
        return ""

    lines = []
    lines.append("=" * 70)
    lines.append("SECURITY FINDINGS")
    lines.append("=" * 70)
    lines.append(f"Total: {len(findings)} findings")
    lines.append("")

    # Group by severity
    by_severity = {}
    for finding in findings:
        sev = finding.get("severity", "info")
        if sev not in by_severity:
            by_severity[sev] = []
        by_severity[sev].append(finding)

    for severity in ["critical", "high", "medium", "low", "info"]:
        sev_findings = by_severity.get(severity, [])
        if sev_findings:
            lines.append(f"\n{severity.upper()}: {len(sev_findings)} findings")
            lines.append("-" * 70)

            for finding in sev_findings:
                lines.append(f"\nTitle: {finding['title']}")
                lines.append(f"Tool: {finding.get('tool', 'Unknown')}")
                target = finding.get("host") or finding.get("url", "Unknown")
                lines.append(f"Target: {target}")

                if finding.get("cve"):
                    lines.append(f"CVE: {finding['cve']}")
                if finding.get("cvss"):
                    lines.append(f"CVSS: {finding['cvss']}")

                desc = finding.get("description", "")
                if desc:
                    lines.append(f"Description: {desc[:500]}")

                lines.append("")

    return "\n".join(lines)


def export_hosts(engagement_id: int) -> str:
    """Export hosts summary."""
    from souleyez.storage.hosts import HostManager

    hm = HostManager()
    hosts = hm.list_hosts(engagement_id)

    if not hosts:
        return ""

    lines = []
    lines.append("=" * 70)
    lines.append("DISCOVERED HOSTS")
    lines.append("=" * 70)
    lines.append(f"Total: {len(hosts)} hosts")
    lines.append("")

    for host in hosts:
        lines.append(f"Host: {host.get('ip', 'N/A')}")
        lines.append(f"  Hostname: {host.get('hostname', 'N/A')}")
        lines.append(f"  Status: {host.get('status', 'unknown')}")
        lines.append(f"  OS: {host.get('os', 'Unknown')}")

        # Get services count
        services = host.get("services", [])
        if services:
            lines.append(f"  Services: {len(services)}")
            for svc in services[:5]:  # First 5 services
                lines.append(
                    f"    - {svc.get('port', '?')}/{svc.get('protocol', 'tcp')}: {svc.get('service', 'unknown')}"
                )
            if len(services) > 5:
                lines.append(f"    (and {len(services) - 5} more...)")

        lines.append("")

    return "\n".join(lines)
