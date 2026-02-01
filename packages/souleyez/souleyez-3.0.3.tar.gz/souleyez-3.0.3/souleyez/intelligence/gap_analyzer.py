#!/usr/bin/env python3
"""
souleyez.intelligence.gap_analyzer - Gap analysis between Wazuh and scan findings

Compares vulnerabilities found by Wazuh (passive, agent-based) vs
SoulEyez scans (active, network-based) to identify detection gaps.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from souleyez.log_config import get_logger
from souleyez.storage.database import get_db
from souleyez.storage.wazuh_vulns import WazuhVulnsManager

logger = get_logger(__name__)


@dataclass
class VulnGap:
    """Represents a vulnerability gap between detection sources."""

    cve_id: str
    severity: str
    host_ip: str
    source: str  # 'wazuh', 'scan', 'both'
    wazuh_details: Optional[Dict[str, Any]] = None
    scan_details: Optional[Dict[str, Any]] = None
    recommendation: str = ""
    confidence: str = "high"  # high, medium, low


@dataclass
class GapAnalysisResult:
    """Result of gap analysis."""

    wazuh_total: int = 0
    scan_total: int = 0
    wazuh_only: List[VulnGap] = field(default_factory=list)
    scan_only: List[VulnGap] = field(default_factory=list)
    confirmed: List[VulnGap] = field(default_factory=list)
    coverage_pct: float = 0.0


class GapAnalyzer:
    """Analyzes gaps between Wazuh and scan vulnerability detection."""

    def __init__(self, engagement_id: int):
        """
        Initialize analyzer for an engagement.

        Args:
            engagement_id: Engagement ID
        """
        self.engagement_id = engagement_id
        self.db = get_db()
        self.vulns_manager = WazuhVulnsManager()

    def analyze(self) -> GapAnalysisResult:
        """
        Run full gap analysis comparing Wazuh vs scan findings.

        Returns:
            GapAnalysisResult with categorized vulnerabilities
        """
        result = GapAnalysisResult()

        # Get Wazuh vulnerabilities (with CVE IDs)
        wazuh_vulns = self._get_wazuh_cves()
        result.wazuh_total = len(wazuh_vulns)

        # Get scan findings with CVE IDs
        scan_findings = self._get_scan_cves()
        result.scan_total = len(scan_findings)

        # Build lookup sets
        wazuh_cve_hosts = {
            (v["cve_id"], v["host_ip"]): v for v in wazuh_vulns if v.get("cve_id")
        }
        scan_cve_hosts = {
            (f["cve_id"], f["host_ip"]): f for f in scan_findings if f.get("cve_id")
        }

        # Find confirmed (both sources)
        for key, wazuh_v in wazuh_cve_hosts.items():
            cve_id, host_ip = key
            if key in scan_cve_hosts:
                scan_f = scan_cve_hosts[key]
                result.confirmed.append(
                    VulnGap(
                        cve_id=cve_id,
                        severity=wazuh_v.get("severity", "Medium"),
                        host_ip=host_ip,
                        source="both",
                        wazuh_details=wazuh_v,
                        scan_details=scan_f,
                        recommendation="High confidence - confirmed by both sources",
                        confidence="high",
                    )
                )

        # Find Wazuh-only (scan missed)
        for key, wazuh_v in wazuh_cve_hosts.items():
            cve_id, host_ip = key
            if key not in scan_cve_hosts:
                # Check if any scan found this CVE on any host
                cve_found_elsewhere = any(c == cve_id for c, _ in scan_cve_hosts.keys())

                result.wazuh_only.append(
                    VulnGap(
                        cve_id=cve_id,
                        severity=wazuh_v.get("severity", "Medium"),
                        host_ip=host_ip,
                        source="wazuh",
                        wazuh_details=wazuh_v,
                        recommendation=self._get_scan_recommendation(cve_id, wazuh_v),
                        confidence="medium" if cve_found_elsewhere else "high",
                    )
                )

        # Find scan-only (Wazuh missed)
        for key, scan_f in scan_cve_hosts.items():
            cve_id, host_ip = key
            if key not in wazuh_cve_hosts:
                result.scan_only.append(
                    VulnGap(
                        cve_id=cve_id,
                        severity=scan_f.get("severity", "medium"),
                        host_ip=host_ip,
                        source="scan",
                        scan_details=scan_f,
                        recommendation="Wazuh agent may not have detection rule for this CVE",
                        confidence="medium",
                    )
                )

        # Calculate coverage percentage
        if result.wazuh_total > 0:
            result.coverage_pct = (len(result.confirmed) / result.wazuh_total) * 100

        return result

    def get_wazuh_only(self) -> List[Dict[str, Any]]:
        """
        Get CVEs found by Wazuh but NOT by SoulEyez scans.

        These represent detection gaps in active scanning.
        """
        result = self.analyze()
        return [
            {
                "cve_id": gap.cve_id,
                "severity": gap.severity,
                "host_ip": gap.host_ip,
                "package_name": (
                    gap.wazuh_details.get("package_name") if gap.wazuh_details else None
                ),
                "package_version": (
                    gap.wazuh_details.get("package_version")
                    if gap.wazuh_details
                    else None
                ),
                "recommendation": gap.recommendation,
            }
            for gap in result.wazuh_only
        ]

    def get_scan_only(self) -> List[Dict[str, Any]]:
        """
        Get CVEs found by scans but NOT in Wazuh.

        These may indicate:
        - Missing Wazuh agent on host
        - Wazuh detection rule gap
        - Network-only vulnerability (no package to detect)
        """
        result = self.analyze()
        return [
            {
                "cve_id": gap.cve_id,
                "severity": gap.severity,
                "host_ip": gap.host_ip,
                "tool": gap.scan_details.get("tool") if gap.scan_details else None,
                "recommendation": gap.recommendation,
            }
            for gap in result.scan_only
        ]

    def get_confirmed(self) -> List[Dict[str, Any]]:
        """
        Get CVEs found by BOTH sources - high confidence vulnerabilities.
        """
        result = self.analyze()
        return [
            {
                "cve_id": gap.cve_id,
                "severity": gap.severity,
                "host_ip": gap.host_ip,
                "package_name": (
                    gap.wazuh_details.get("package_name") if gap.wazuh_details else None
                ),
                "scan_tool": gap.scan_details.get("tool") if gap.scan_details else None,
                "confidence": "high",
            }
            for gap in result.confirmed
        ]

    def get_coverage_stats(self) -> Dict[str, Any]:
        """
        Get coverage statistics.

        Returns:
            Dict with counts and percentages
        """
        result = self.analyze()

        return {
            "wazuh_total": result.wazuh_total,
            "scan_total": result.scan_total,
            "wazuh_only_count": len(result.wazuh_only),
            "scan_only_count": len(result.scan_only),
            "confirmed_count": len(result.confirmed),
            "coverage_pct": round(result.coverage_pct, 1),
            "by_severity": self._get_severity_breakdown(result),
        }

    def get_actionable_gaps(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get prioritized list of actionable gaps (Wazuh-only vulns).

        Sorted by severity and exploitability.
        """
        result = self.analyze()

        # Sort by severity
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

        sorted_gaps = sorted(
            result.wazuh_only, key=lambda g: severity_order.get(g.severity, 4)
        )

        return [
            {
                "cve_id": gap.cve_id,
                "severity": gap.severity,
                "host_ip": gap.host_ip,
                "package": (
                    gap.wazuh_details.get("package_name") if gap.wazuh_details else None
                ),
                "version": (
                    gap.wazuh_details.get("package_version")
                    if gap.wazuh_details
                    else None
                ),
                "recommendation": gap.recommendation,
                "priority": (
                    "high" if gap.severity in ["Critical", "High"] else "medium"
                ),
            }
            for gap in sorted_gaps[:limit]
        ]

    def _get_wazuh_cves(self) -> List[Dict[str, Any]]:
        """Get Wazuh vulnerabilities with host IPs."""
        query = """
            SELECT
                wv.cve_id,
                wv.severity,
                wv.agent_ip as host_ip,
                wv.package_name,
                wv.package_version,
                wv.cvss_score,
                h.ip_address as mapped_host_ip
            FROM wazuh_vulnerabilities wv
            LEFT JOIN hosts h ON wv.host_id = h.id
            WHERE wv.engagement_id = ?
                AND wv.cve_id IS NOT NULL
        """
        results = self.db.execute(query, (self.engagement_id,))

        # Use mapped host IP if available, otherwise agent IP
        vulns = []
        for r in results:
            vuln = dict(r)
            vuln["host_ip"] = r.get("mapped_host_ip") or r.get("host_ip")
            vulns.append(vuln)

        return vulns

    def _get_scan_cves(self) -> List[Dict[str, Any]]:
        """Get CVEs from scan findings (nuclei, nmap, etc)."""
        findings = []

        # Get from nuclei_findings (has cve_id column)
        nuclei_query = """
            SELECT
                nf.cve_id,
                nf.severity,
                nf.matched_at as host_ip,
                'nuclei' as tool
            FROM nuclei_findings nf
            WHERE nf.engagement_id = ?
                AND nf.cve_id IS NOT NULL
        """
        nuclei_results = self.db.execute(nuclei_query, (self.engagement_id,))

        for r in nuclei_results:
            # Extract IP from matched_at URL
            host_ip = self._extract_ip(r.get("matched_at", ""))
            if host_ip:
                findings.append(
                    {
                        "cve_id": r["cve_id"],
                        "severity": r.get("severity", "medium"),
                        "host_ip": host_ip,
                        "tool": "nuclei",
                    }
                )

        # Get from findings table (check refs/title for CVE)
        findings_query = """
            SELECT
                f.title,
                f.refs,
                f.severity,
                f.tool,
                h.ip_address as host_ip
            FROM findings f
            LEFT JOIN hosts h ON f.host_id = h.id
            WHERE f.engagement_id = ?
        """
        findings_results = self.db.execute(findings_query, (self.engagement_id,))

        for r in findings_results:
            # Extract CVE from title or refs
            cve_id = self._extract_cve(r.get("title", "")) or self._extract_cve(
                r.get("refs", "")
            )
            if cve_id and r.get("host_ip"):
                findings.append(
                    {
                        "cve_id": cve_id,
                        "severity": r.get("severity", "medium"),
                        "host_ip": r["host_ip"],
                        "tool": r.get("tool", "unknown"),
                    }
                )

        return findings

    def _extract_cve(self, text: str) -> Optional[str]:
        """Extract CVE ID from text."""
        if not text:
            return None

        match = re.search(r"CVE-\d{4}-\d{4,}", text, re.IGNORECASE)
        if match:
            return match.group(0).upper()

        return None

    def _extract_ip(self, url: str) -> Optional[str]:
        """Extract IP address from URL or string."""
        if not url:
            return None

        # Try to extract IP from URL like https://10.0.0.1:443/path
        ip_pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        match = re.search(ip_pattern, url)
        if match:
            return match.group(1)

        return None

    def _get_scan_recommendation(self, cve_id: str, wazuh_details: Dict) -> str:
        """Generate scan recommendation for a Wazuh-only CVE."""
        package = wazuh_details.get("package_name", "unknown")
        severity = wazuh_details.get("severity", "Medium")

        if severity in ["Critical", "High"]:
            return f"Run targeted nuclei scan: nuclei -t cves/{cve_id.lower()}.yaml"

        return f"Verify {cve_id} in {package} - may not be network exploitable"

    def _get_severity_breakdown(
        self, result: GapAnalysisResult
    ) -> Dict[str, Dict[str, int]]:
        """Get counts by severity for each category."""
        breakdown = {
            "wazuh_only": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
            "scan_only": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
            "confirmed": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
        }

        for gap in result.wazuh_only:
            sev = gap.severity if gap.severity in breakdown["wazuh_only"] else "Medium"
            breakdown["wazuh_only"][sev] += 1

        for gap in result.scan_only:
            # Normalize severity (scan findings use lowercase)
            sev = gap.severity.capitalize() if gap.severity else "Medium"
            if sev not in breakdown["scan_only"]:
                sev = "Medium"
            breakdown["scan_only"][sev] += 1

        for gap in result.confirmed:
            sev = gap.severity if gap.severity in breakdown["confirmed"] else "Medium"
            breakdown["confirmed"][sev] += 1

        return breakdown
