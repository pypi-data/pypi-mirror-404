"""
souleyez.ai.report_context - Build context for AI report generation

Prepares engagement data in formats suitable for LLM prompt templates.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReportContextBuilder:
    """
    Builds context from engagement data for AI report generation.

    Transforms raw engagement data into formatted context suitable
    for the prompt templates in report_prompts.py.
    """

    def __init__(self):
        from souleyez.storage.credentials import CredentialsManager
        from souleyez.storage.engagements import EngagementManager
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager

        self.em = EngagementManager()
        self.fm = FindingsManager()
        self.hm = HostManager()
        self.cm = CredentialsManager()

    def build_executive_context(self, engagement_id: int) -> Dict[str, Any]:
        """
        Build context for executive summary generation.

        Args:
            engagement_id: Engagement to build context for

        Returns:
            dict: Context variables for EXECUTIVE_SUMMARY_PROMPT
        """
        engagement = self.em.get_by_id(engagement_id)
        if not engagement:
            logger.error(f"Engagement {engagement_id} not found")
            return {}

        findings = self.fm.list_findings(engagement_id)
        hosts = self.hm.list_hosts(engagement_id)
        creds = self.cm.list_credentials(engagement_id)

        # Count findings by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in findings:
            sev = f.get("severity", "info").lower()
            if sev in severity_counts:
                severity_counts[sev] += 1
            else:
                severity_counts["info"] += 1

        # Count hosts with critical/high findings
        hosts_with_issues = set()
        for f in findings:
            if f.get("severity", "").lower() in ["critical", "high"]:
                if f.get("host_id"):
                    hosts_with_issues.add(f["host_id"])

        # Build top findings summary
        top_findings = self._format_top_findings(findings, limit=5)

        # Engagement type and duration
        eng_type = engagement.get("type", "Penetration Test")
        duration = self._calculate_duration(engagement)
        scope = engagement.get("description", "Network and application assessment")

        return {
            "engagement_name": engagement.get("name", "Unknown"),
            "engagement_type": eng_type,
            "duration": duration,
            "scope_summary": scope[:200] if scope else "Full scope assessment",
            "total_findings": len(findings),
            "critical_count": severity_counts["critical"],
            "high_count": severity_counts["high"],
            "medium_count": severity_counts["medium"],
            "low_count": severity_counts["low"],
            "info_count": severity_counts["info"],
            "total_hosts": len(hosts),
            "compromised_hosts": len(hosts_with_issues),
            "credentials_count": len(creds),
            "top_findings": top_findings,
        }

    def build_finding_context(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build context for single finding enhancement.

        Args:
            finding: Finding dict from FindingsManager

        Returns:
            dict: Context variables for FINDING_ENHANCEMENT_PROMPT
        """
        # Get host info if available
        host_ip = "N/A"
        hostname = ""
        if finding.get("host_id"):
            host = self.hm.get_host(finding["host_id"])
            if host:
                host_ip = host.get("ip_address", "N/A")
                hostname = host.get("hostname", "")

        # Extract CVE/CWE
        cve = finding.get("refs", "") or "N/A"
        if isinstance(cve, list):
            cve = ", ".join(cve[:3])  # Limit to first 3

        # Clean evidence (truncate if too long)
        evidence = finding.get("evidence", "")
        if len(evidence) > 1000:
            evidence = evidence[:1000] + "\n... [truncated]"

        return {
            "title": finding.get("title", "Unknown Finding"),
            "severity": finding.get("severity", "Unknown").upper(),
            "host": host_ip,
            "hostname": hostname,
            "port": finding.get("port", "N/A"),
            "service": finding.get("service", "Unknown"),
            "tool": finding.get("tool", "Manual"),
            "description": finding.get("description", "No description provided"),
            "cve": cve,
            "evidence": evidence or "No evidence recorded",
        }

    def build_remediation_context(self, engagement_id: int) -> Dict[str, Any]:
        """
        Build context for remediation plan generation.

        Args:
            engagement_id: Engagement to build context for

        Returns:
            dict: Context variables for REMEDIATION_PLAN_PROMPT
        """
        findings = self.fm.list_findings(engagement_id)
        hosts = self.hm.list_hosts(engagement_id)
        creds = self.cm.list_credentials(engagement_id)

        # Count by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in findings:
            sev = f.get("severity", "info").lower()
            if sev in severity_counts:
                severity_counts[sev] += 1

        # Build findings summary by severity
        findings_summary = self._format_findings_by_severity(findings)

        # Top vulnerabilities (critical and high)
        top_vulns = self._format_top_findings(findings, limit=10, include_medium=True)

        return {
            "findings_summary": findings_summary,
            "total_hosts": len(hosts),
            "critical_count": severity_counts["critical"],
            "high_count": severity_counts["high"],
            "medium_count": severity_counts["medium"],
            "creds_count": len(creds),
            "top_vulnerabilities": top_vulns,
        }

    def _format_top_findings(
        self, findings: List[Dict], limit: int = 5, include_medium: bool = False
    ) -> str:
        """Format top critical/high findings as text."""
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

        # Filter to critical/high (and optionally medium)
        max_severity = 2 if include_medium else 1
        priority_findings = [
            f
            for f in findings
            if severity_order.get(f.get("severity", "info").lower(), 4) <= max_severity
        ]

        # Sort by severity
        priority_findings.sort(
            key=lambda f: severity_order.get(f.get("severity", "info").lower(), 4)
        )

        # Format
        lines = []
        for f in priority_findings[:limit]:
            sev = f.get("severity", "unknown").upper()
            title = f.get("title", "Unknown")
            desc = f.get("description", "")[:100]
            lines.append(f"- [{sev}] {title}")
            if desc:
                lines.append(f"  {desc}...")

        return "\n".join(lines) if lines else "No critical or high severity findings."

    def _format_findings_by_severity(self, findings: List[Dict]) -> str:
        """Format all findings grouped by severity."""
        by_severity = {"critical": [], "high": [], "medium": [], "low": [], "info": []}

        for f in findings:
            sev = f.get("severity", "info").lower()
            if sev in by_severity:
                by_severity[sev].append(f)
            else:
                by_severity["info"].append(f)

        lines = []
        for sev in ["critical", "high", "medium", "low"]:
            items = by_severity[sev]
            if items:
                lines.append(f"\n{sev.upper()} ({len(items)}):")
                for f in items[:5]:  # Limit to 5 per category
                    lines.append(f"  - {f.get('title', 'Unknown')}")
                if len(items) > 5:
                    lines.append(f"  ... and {len(items) - 5} more")

        return "\n".join(lines) if lines else "No findings recorded."

    def _calculate_duration(self, engagement: Dict) -> str:
        """Calculate engagement duration from dates."""
        from datetime import datetime

        start = engagement.get("start_date")
        end = engagement.get("end_date")

        if not start:
            return "Duration not specified"

        try:
            start_dt = (
                datetime.fromisoformat(start) if isinstance(start, str) else start
            )
            if end:
                end_dt = datetime.fromisoformat(end) if isinstance(end, str) else end
                days = (end_dt - start_dt).days
                return f"{days} days" if days > 0 else "1 day"
            else:
                return "Ongoing"
        except Exception:
            return "Duration not specified"
