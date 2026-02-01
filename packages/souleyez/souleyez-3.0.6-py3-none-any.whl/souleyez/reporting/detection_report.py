"""
Detection Coverage Report Data Gatherer.

Collects and analyzes detection coverage data for generating
client-ready detection validation reports.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from souleyez.detection.attack_signatures import ATTACK_SIGNATURES, get_signature
from souleyez.detection.mitre_mappings import (
    MITRE_TACTICS,
    MITREMappings,
    TacticResult,
    TechniqueResult,
)
from souleyez.detection.validator import (
    DetectionResult,
    DetectionValidator,
    EngagementDetectionSummary,
)
from souleyez.storage.database import get_db
from souleyez.storage.engagements import EngagementManager


@dataclass
class RuleRecommendation:
    """Recommendation for improving detection coverage."""

    attack_type: str
    gap_description: str
    priority: str  # critical, high, medium, low
    suggested_rule_ids: List[str] = field(default_factory=list)
    rule_category: str = ""
    detection_guidance: str = ""
    mitre_technique: str = ""


@dataclass
class HostDetectionStats:
    """Detection statistics for a single host."""

    host_ip: str
    total_attacks: int = 0
    detected: int = 0
    not_detected: int = 0
    partial: int = 0
    offline: int = 0
    coverage_percent: float = 0.0
    attack_types: List[str] = field(default_factory=list)


@dataclass
class SeverityBreakdown:
    """Breakdown of alerts by severity level."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    total: int = 0


@dataclass
class TopRule:
    """A frequently triggered rule/sourcetype."""

    rule_id: str
    rule_name: str
    count: int
    severity: str = "info"
    description: str = ""


@dataclass
class SampleAlert:
    """A sample alert for display in the report."""

    rule_id: str
    rule_name: str
    severity: str
    timestamp: str
    source: str
    description: str
    raw_snippet: str = ""


@dataclass
class HostVulnerability:
    """Vulnerability info for a host."""

    cve_id: str
    name: str
    severity: str
    cvss_score: float
    package_name: str = ""
    package_version: str = ""


@dataclass
class HostVulnerabilitySummary:
    """Vulnerability summary for a single host."""

    host_ip: str
    agent_name: str = ""
    total_vulns: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    top_vulns: List[HostVulnerability] = field(default_factory=list)
    was_attacked: bool = False


@dataclass
class VulnerabilitySection:
    """Vulnerability data for the report."""

    total_vulns: int = 0
    hosts_with_vulns: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    host_summaries: List[HostVulnerabilitySummary] = field(default_factory=list)
    top_cves: List[HostVulnerability] = field(default_factory=list)


@dataclass
class DetectionReportData:
    """Complete data structure for a detection coverage report."""

    engagement: Dict[str, Any]
    summary: EngagementDetectionSummary
    detection_results: List[DetectionResult]
    mitre_coverage: Dict[str, TechniqueResult]
    tactic_summary: Dict[str, TacticResult]
    heatmap_data: List[Dict[str, Any]]
    gaps: List[DetectionResult]
    mitre_gaps: List[TechniqueResult]
    per_host_analysis: Dict[str, HostDetectionStats]
    rule_recommendations: List[RuleRecommendation]
    generated_at: datetime
    siem_type: str = "wazuh"
    # Enhanced report fields
    severity_breakdown: SeverityBreakdown = field(default_factory=SeverityBreakdown)
    top_rules: List[TopRule] = field(default_factory=list)
    sample_alerts: List[SampleAlert] = field(default_factory=list)
    executive_summary: str = ""
    risk_level: str = "UNKNOWN"  # CRITICAL, HIGH, MEDIUM, LOW
    avg_detection_latency: str = ""
    vulnerability_section: VulnerabilitySection = field(
        default_factory=VulnerabilitySection
    )


class DetectionReportGatherer:
    """Gathers and analyzes detection coverage data for reporting."""

    def __init__(self, engagement_id: int):
        """
        Initialize gatherer for an engagement.

        Args:
            engagement_id: The engagement to report on
        """
        self.engagement_id = engagement_id
        self.validator = DetectionValidator(engagement_id)
        self.mitre = MITREMappings()
        self.em = EngagementManager()

    def gather_data(self) -> DetectionReportData:
        """
        Gather all detection coverage data for reporting.

        Returns:
            DetectionReportData with all report sections populated
        """
        # Get engagement details
        engagement = self.em.get_by_id(self.engagement_id)
        if not engagement:
            raise ValueError(f"Engagement {self.engagement_id} not found")

        # Run detection validation
        summary = self.validator.validate_engagement()
        gaps = self.validator.get_detection_gaps()

        # Build MITRE coverage matrix
        mitre_coverage = self.mitre.build_coverage_matrix(summary.results)
        tactic_summary = self.mitre.build_tactic_summary(mitre_coverage)
        heatmap_data = self.mitre.get_heatmap_data(mitre_coverage)
        mitre_gaps = self.mitre.get_coverage_gaps(mitre_coverage)

        # Build per-host analysis
        per_host_analysis = self._build_per_host_analysis(summary.results)

        # Generate rule recommendations
        rule_recommendations = self._generate_rule_recommendations(gaps, mitre_gaps)

        # Get actual SIEM type from validator
        siem_type = self.validator.get_siem_type() or "unknown"

        # Build enhanced report data
        severity_breakdown = self._build_severity_breakdown(summary.results)
        top_rules = self._get_top_rules(summary.results)
        sample_alerts = self._get_sample_alerts(summary.results)
        executive_summary = self._generate_executive_summary(
            summary, severity_breakdown, gaps, mitre_gaps
        )
        risk_level = self._calculate_risk_level(summary.coverage_percent, gaps)

        # Gather vulnerability data for attacked hosts (Wazuh only)
        vulnerability_section = self._gather_vulnerability_data(per_host_analysis)

        return DetectionReportData(
            engagement=engagement,
            summary=summary,
            detection_results=summary.results,
            mitre_coverage=mitre_coverage,
            tactic_summary=tactic_summary,
            heatmap_data=heatmap_data,
            gaps=gaps,
            mitre_gaps=mitre_gaps,
            per_host_analysis=per_host_analysis,
            rule_recommendations=rule_recommendations,
            generated_at=datetime.now(),
            siem_type=siem_type,
            severity_breakdown=severity_breakdown,
            top_rules=top_rules,
            sample_alerts=sample_alerts,
            executive_summary=executive_summary,
            risk_level=risk_level,
            vulnerability_section=vulnerability_section,
        )

    def _build_per_host_analysis(
        self, results: List[DetectionResult]
    ) -> Dict[str, HostDetectionStats]:
        """
        Build detection statistics grouped by target host.

        Args:
            results: List of DetectionResult objects

        Returns:
            Dict mapping host_ip -> HostDetectionStats
        """
        hosts: Dict[str, HostDetectionStats] = {}

        for result in results:
            # Get target IP - handle both object and dict
            target_ip = getattr(result, "target_ip", None)
            if target_ip is None and isinstance(result, dict):
                target_ip = result.get("target_ip")
            if not target_ip:
                target_ip = "unknown"

            # Get attack type
            attack_type = getattr(result, "attack_type", None)
            if attack_type is None and isinstance(result, dict):
                attack_type = result.get("attack_type", "unknown")

            # Get status
            status = getattr(result, "status", None)
            if status is None and isinstance(result, dict):
                status = result.get("status", "unknown")

            # Initialize host stats if needed
            if target_ip not in hosts:
                hosts[target_ip] = HostDetectionStats(host_ip=target_ip)

            host = hosts[target_ip]
            host.total_attacks += 1

            # Track attack types
            if attack_type and attack_type not in host.attack_types:
                host.attack_types.append(attack_type)

            # Update status counts
            if status == "detected":
                host.detected += 1
            elif status == "not_detected":
                host.not_detected += 1
            elif status == "partial":
                host.partial += 1
            elif status == "offline":
                host.offline += 1

        # Calculate coverage percentages
        for host in hosts.values():
            countable = host.detected + host.not_detected + host.partial
            if countable > 0:
                host.coverage_percent = round((host.detected / countable) * 100, 1)

        return hosts

    def _generate_rule_recommendations(
        self, gaps: List[DetectionResult], mitre_gaps: List[TechniqueResult]
    ) -> List[RuleRecommendation]:
        """
        Generate SIEM rule recommendations for detection gaps.

        Args:
            gaps: List of undetected attacks
            mitre_gaps: List of undetected MITRE techniques

        Returns:
            List of RuleRecommendation objects
        """
        recommendations: List[RuleRecommendation] = []
        seen_attack_types: set = set()

        for gap in gaps:
            # Get attack type
            attack_type = getattr(gap, "attack_type", None)
            if attack_type is None and isinstance(gap, dict):
                attack_type = gap.get("attack_type")
            if not attack_type or attack_type in seen_attack_types:
                continue

            seen_attack_types.add(attack_type)

            # Get signature info
            signature = get_signature(attack_type)
            category = signature.get("category", "unknown")
            severity = signature.get("severity", "medium")

            # Map severity to priority
            priority_map = {
                "critical": "critical",
                "high": "high",
                "medium": "medium",
                "low": "low",
                "info": "low",
            }
            priority = priority_map.get(severity, "medium")

            # Get expected rule IDs from signature
            expected_rules = signature.get("wazuh_rules", [])
            rule_ids = [str(r) for r in expected_rules]

            # Get MITRE technique for this tool
            techniques = self.mitre.map_tool_to_techniques(attack_type)
            mitre_tech = techniques[0]["id"] if techniques else ""

            # Generate detection guidance
            guidance = self._get_detection_guidance(attack_type, signature)

            rec = RuleRecommendation(
                attack_type=attack_type,
                gap_description=f"{attack_type.upper()} attacks not detected by SIEM",
                priority=priority,
                suggested_rule_ids=rule_ids,
                rule_category=category,
                detection_guidance=guidance,
                mitre_technique=mitre_tech,
            )
            recommendations.append(rec)

        # Sort by priority (critical first)
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 4))

        return recommendations

    def _get_detection_guidance(
        self, attack_type: str, signature: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable detection guidance for an attack type.

        Args:
            attack_type: Tool name
            signature: Attack signature dict

        Returns:
            Detection guidance string
        """
        guidance_map = {
            "nmap": (
                "Enable network scan detection rules. Monitor for: "
                "SYN scans, service enumeration, port sweeps. "
                "Log source: firewall, IDS, network flow data."
            ),
            "hydra": (
                "Enable brute force detection rules. Monitor for: "
                "multiple failed authentication attempts, rapid login attempts. "
                "Log source: authentication logs, SSH, FTP, web server logs."
            ),
            "medusa": (
                "Enable brute force detection rules. Monitor for: "
                "credential stuffing, password spraying patterns. "
                "Log source: authentication logs, PAM, web application logs."
            ),
            "sqlmap": (
                "Enable web attack detection rules. Monitor for: "
                "SQL injection patterns, UNION SELECT, encoded payloads. "
                "Log source: web server logs, WAF, application logs."
            ),
            "gobuster": (
                "Enable directory enumeration detection. Monitor for: "
                "rapid 404/403 responses, sequential requests to common paths. "
                "Log source: web server access logs, WAF."
            ),
            "ffuf": (
                "Enable web fuzzing detection. Monitor for: "
                "high-frequency requests, parameter fuzzing, path enumeration. "
                "Log source: web server logs, reverse proxy logs."
            ),
            "nikto": (
                "Enable web vulnerability scanning detection. Monitor for: "
                "known scanner user agents, vulnerability probe patterns. "
                "Log source: web server logs, WAF, IDS."
            ),
            "crackmapexec": (
                "Enable SMB/lateral movement detection. Monitor for: "
                "pass-the-hash attempts, SMB enumeration, remote execution. "
                "Log source: Windows Security logs, SMB audit logs."
            ),
            "metasploit": (
                "Enable exploitation framework detection. Monitor for: "
                "known exploit signatures, reverse shells, staged payloads. "
                "Log source: IDS/IPS, endpoint detection, network flow."
            ),
        }

        guidance = guidance_map.get(attack_type.lower())
        if guidance:
            return guidance

        # Generic guidance based on category
        category = signature.get("category", "unknown")
        category_guidance = {
            "reconnaissance": (
                "Enable reconnaissance detection rules. "
                "Monitor for enumeration patterns and scanning activity."
            ),
            "credential_access": (
                "Enable credential attack detection. "
                "Monitor for brute force and credential theft attempts."
            ),
            "web_attack": (
                "Enable web attack detection rules. "
                "Monitor for injection attempts and web scanning."
            ),
            "lateral_movement": (
                "Enable lateral movement detection. "
                "Monitor for remote execution and authentication anomalies."
            ),
            "exploitation": (
                "Enable exploitation detection. "
                "Monitor for known exploit signatures and shellcode."
            ),
        }

        return category_guidance.get(
            category, "Review SIEM rule configuration for this attack category."
        )

    def _build_severity_breakdown(
        self, results: List[DetectionResult]
    ) -> SeverityBreakdown:
        """
        Build severity breakdown from detected alerts.

        Args:
            results: List of DetectionResult objects

        Returns:
            SeverityBreakdown with counts per severity level
        """
        breakdown = SeverityBreakdown()

        for result in results:
            if result.status != "detected" or not result.alerts:
                continue

            for alert in result.alerts:
                severity = str(alert.get("severity", "info")).lower()
                breakdown.total += 1

                if severity in ("critical", "crit"):
                    breakdown.critical += 1
                elif severity == "high":
                    breakdown.high += 1
                elif severity in ("medium", "med"):
                    breakdown.medium += 1
                elif severity == "low":
                    breakdown.low += 1
                else:
                    breakdown.info += 1

        return breakdown

    def _get_top_rules(
        self, results: List[DetectionResult], limit: int = 10
    ) -> List[TopRule]:
        """
        Get the most frequently triggered rules.

        Args:
            results: List of DetectionResult objects
            limit: Maximum number of rules to return

        Returns:
            List of TopRule objects sorted by count
        """
        rule_counts: Dict[str, Dict[str, Any]] = {}

        for result in results:
            if result.status != "detected" or not result.alerts:
                continue

            for alert in result.alerts:
                rule_id = str(alert.get("rule_id", "unknown"))
                rule_name = alert.get("rule_name", alert.get("name", "Unknown Rule"))
                severity = str(alert.get("severity", "info")).lower()
                description = alert.get("description", "")

                if rule_id not in rule_counts:
                    rule_counts[rule_id] = {
                        "rule_id": rule_id,
                        "rule_name": rule_name,
                        "severity": severity,
                        "description": description,
                        "count": 0,
                    }
                rule_counts[rule_id]["count"] += 1

        # Sort by count descending
        sorted_rules = sorted(
            rule_counts.values(), key=lambda r: r["count"], reverse=True
        )[:limit]

        return [
            TopRule(
                rule_id=r["rule_id"],
                rule_name=r["rule_name"],
                count=r["count"],
                severity=r["severity"],
                description=r["description"][:200] if r["description"] else "",
            )
            for r in sorted_rules
        ]

    def _get_sample_alerts(
        self, results: List[DetectionResult], limit: int = 5
    ) -> List[SampleAlert]:
        """
        Get sample alerts for display in the report.

        Args:
            results: List of DetectionResult objects
            limit: Maximum number of samples to return

        Returns:
            List of SampleAlert objects
        """
        samples: List[SampleAlert] = []

        # Prioritize alerts from detected attacks, favor higher severity
        severity_order = {
            "critical": 0,
            "crit": 0,
            "high": 1,
            "medium": 2,
            "med": 2,
            "low": 3,
            "info": 4,
        }

        all_alerts = []
        for result in results:
            if result.status != "detected" or not result.alerts:
                continue
            for alert in result.alerts[:3]:  # Max 3 per result
                all_alerts.append((result.attack_type, alert))

        # Sort by severity
        all_alerts.sort(
            key=lambda x: severity_order.get(
                str(x[1].get("severity", "info")).lower(), 5
            )
        )

        for attack_type, alert in all_alerts[:limit]:
            # Extract raw snippet from alert data
            raw_data = alert.get("raw_data", {})
            raw_snippet = ""
            if isinstance(raw_data, dict):
                # Try to get meaningful snippet
                full_log = raw_data.get("full_log", "")
                if full_log:
                    raw_snippet = full_log[:300]
                else:
                    # Try message or description
                    raw_snippet = raw_data.get("message", "")[:300]
            elif isinstance(raw_data, str):
                raw_snippet = raw_data[:300]

            timestamp = alert.get("timestamp", "")
            if hasattr(timestamp, "isoformat"):
                timestamp = timestamp.isoformat()

            samples.append(
                SampleAlert(
                    rule_id=str(alert.get("rule_id", "N/A")),
                    rule_name=alert.get("rule_name", alert.get("name", "Unknown")),
                    severity=str(alert.get("severity", "info")),
                    timestamp=str(timestamp),
                    source=attack_type,
                    description=alert.get("description", "")[:200],
                    raw_snippet=raw_snippet,
                )
            )

        return samples

    def _generate_executive_summary(
        self,
        summary: EngagementDetectionSummary,
        severity: SeverityBreakdown,
        gaps: List[DetectionResult],
        mitre_gaps: List[TechniqueResult],
    ) -> str:
        """
        Generate an executive summary paragraph for the report.

        Args:
            summary: Engagement detection summary
            severity: Alert severity breakdown
            gaps: Undetected attacks
            mitre_gaps: Undetected MITRE techniques

        Returns:
            Executive summary text
        """
        coverage = summary.coverage_percent
        risk_level = self._calculate_risk_level(coverage, gaps)

        # Build summary text
        parts = []

        # Overall assessment
        if coverage >= 75:
            parts.append(
                f"The security monitoring infrastructure demonstrates strong detection "
                f"capabilities with {coverage:.1f}% coverage of tested attack techniques."
            )
        elif coverage >= 50:
            parts.append(
                f"The security monitoring shows moderate detection coverage at {coverage:.1f}%. "
                f"Several improvements are recommended to strengthen the security posture."
            )
        elif coverage >= 25:
            parts.append(
                f"Detection coverage is concerning at {coverage:.1f}%. "
                f"Significant gaps exist that require immediate attention."
            )
        else:
            parts.append(
                f"Critical detection gaps identified with only {coverage:.1f}% coverage. "
                f"The current SIEM configuration requires substantial improvements."
            )

        # Attack statistics
        parts.append(
            f"Out of {summary.total_attacks} attack scenarios tested, "
            f"{summary.detected} were detected and {summary.not_detected} went undetected."
        )

        # Alert severity context
        if severity.total > 0:
            high_sev = severity.critical + severity.high
            if high_sev > 0:
                parts.append(
                    f"The SIEM generated {severity.total} alerts, including "
                    f"{severity.critical} critical and {severity.high} high severity alerts."
                )
            else:
                parts.append(
                    f"The SIEM generated {severity.total} alerts, "
                    f"primarily of medium to low severity."
                )

        # MITRE gaps
        if mitre_gaps:
            technique_names = [g.name for g in mitre_gaps[:3]]
            if len(mitre_gaps) > 3:
                parts.append(
                    f"Key detection gaps include {', '.join(technique_names)}, "
                    f"and {len(mitre_gaps) - 3} additional MITRE ATT&CK techniques."
                )
            else:
                parts.append(
                    f"Key detection gaps include: {', '.join(technique_names)}."
                )

        # Risk assessment
        parts.append(f"Overall risk assessment: {risk_level}.")

        return " ".join(parts)

    def _calculate_risk_level(
        self, coverage_percent: float, gaps: List[DetectionResult]
    ) -> str:
        """
        Calculate overall risk level based on coverage and gap severity.

        Args:
            coverage_percent: Detection coverage percentage
            gaps: List of undetected attacks

        Returns:
            Risk level string (CRITICAL, HIGH, MEDIUM, LOW)
        """
        # Check for critical gaps
        critical_gaps = 0
        for gap in gaps:
            attack_type = gap.attack_type if hasattr(gap, "attack_type") else ""
            signature = get_signature(attack_type)
            if signature.get("severity") in ("critical", "high"):
                critical_gaps += 1

        # Determine risk level
        if coverage_percent < 25 or critical_gaps >= 3:
            return "CRITICAL"
        elif coverage_percent < 50 or critical_gaps >= 1:
            return "HIGH"
        elif coverage_percent < 75:
            return "MEDIUM"
        else:
            return "LOW"

    def _gather_vulnerability_data(
        self, per_host_analysis: Dict[str, HostDetectionStats]
    ) -> VulnerabilitySection:
        """
        Gather vulnerability data for hosts that were attacked.

        Cross-references attacked hosts with Wazuh vulnerability data
        to show what vulnerabilities existed on targeted systems.

        Args:
            per_host_analysis: Dict of host IP -> detection stats

        Returns:
            VulnerabilitySection with aggregated vulnerability data
        """
        from souleyez.storage.wazuh_vulns import WazuhVulnsManager

        section = VulnerabilitySection()

        try:
            vulns_manager = WazuhVulnsManager()

            # Get all vulnerabilities for this engagement
            all_vulns = vulns_manager.list_vulnerabilities(
                engagement_id=self.engagement_id, limit=1000
            )

            if not all_vulns:
                return section

            # Get attacked host IPs
            attacked_ips = set(per_host_analysis.keys())

            # Build summary by severity
            for vuln in all_vulns:
                section.total_vulns += 1
                severity = (vuln.get("severity") or "Low").lower()
                if severity == "critical":
                    section.critical_count += 1
                elif severity == "high":
                    section.high_count += 1
                elif severity == "medium":
                    section.medium_count += 1
                else:
                    section.low_count += 1

            # Group vulnerabilities by host/agent IP
            host_vulns: Dict[str, List[Dict]] = {}
            for vuln in all_vulns:
                agent_ip = vuln.get("agent_ip") or vuln.get("host_ip") or "unknown"
                if agent_ip not in host_vulns:
                    host_vulns[agent_ip] = []
                host_vulns[agent_ip].append(vuln)

            section.hosts_with_vulns = len(host_vulns)

            # Build per-host summaries, prioritizing attacked hosts
            for host_ip, vulns in host_vulns.items():
                was_attacked = host_ip in attacked_ips

                host_summary = HostVulnerabilitySummary(
                    host_ip=host_ip,
                    agent_name=vulns[0].get("agent_name", "") if vulns else "",
                    total_vulns=len(vulns),
                    was_attacked=was_attacked,
                )

                # Count by severity for this host
                for v in vulns:
                    sev = (v.get("severity") or "Low").lower()
                    if sev == "critical":
                        host_summary.critical += 1
                    elif sev == "high":
                        host_summary.high += 1
                    elif sev == "medium":
                        host_summary.medium += 1
                    else:
                        host_summary.low += 1

                # Get top 5 vulns for this host (by CVSS score)
                sorted_vulns = sorted(
                    vulns, key=lambda x: x.get("cvss_score") or 0, reverse=True
                )[:5]

                for v in sorted_vulns:
                    host_summary.top_vulns.append(
                        HostVulnerability(
                            cve_id=v.get("cve_id", "N/A"),
                            name=v.get("name", "")[:100],
                            severity=v.get("severity", "Low"),
                            cvss_score=v.get("cvss_score") or 0.0,
                            package_name=v.get("package_name", ""),
                            package_version=v.get("package_version", ""),
                        )
                    )

                section.host_summaries.append(host_summary)

            # Sort host summaries: attacked hosts first, then by vuln count
            section.host_summaries.sort(
                key=lambda h: (not h.was_attacked, -h.total_vulns)
            )

            # Get top 10 CVEs across all hosts
            all_cves: Dict[str, Dict] = {}
            for vuln in all_vulns:
                cve_id = vuln.get("cve_id")
                if not cve_id:
                    continue
                if cve_id not in all_cves:
                    all_cves[cve_id] = vuln
                elif (vuln.get("cvss_score") or 0) > (
                    all_cves[cve_id].get("cvss_score") or 0
                ):
                    all_cves[cve_id] = vuln

            sorted_cves = sorted(
                all_cves.values(), key=lambda x: x.get("cvss_score") or 0, reverse=True
            )[:10]

            for v in sorted_cves:
                section.top_cves.append(
                    HostVulnerability(
                        cve_id=v.get("cve_id", "N/A"),
                        name=v.get("name", "")[:100],
                        severity=v.get("severity", "Low"),
                        cvss_score=v.get("cvss_score") or 0.0,
                        package_name=v.get("package_name", ""),
                        package_version=v.get("package_version", ""),
                    )
                )

        except Exception as e:
            # Log but don't fail the report
            import logging

            logging.getLogger(__name__).warning(
                f"Failed to gather vulnerability data: {e}"
            )

        return section

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for quick display.

        Returns:
            Dict with key metrics
        """
        data = self.gather_data()

        # Calculate risk level based on coverage
        coverage = data.summary.coverage_percent
        if coverage >= 75:
            risk_level = "LOW"
        elif coverage >= 50:
            risk_level = "MEDIUM"
        elif coverage >= 25:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        # Count tactics with coverage
        tactics_tested = sum(
            1 for t in data.tactic_summary.values() if t.techniques_tested > 0
        )
        tactics_with_gaps = sum(
            1 for t in data.tactic_summary.values() if t.techniques_not_detected > 0
        )

        return {
            "coverage_percent": data.summary.coverage_percent,
            "total_attacks": data.summary.total_attacks,
            "detected": data.summary.detected,
            "not_detected": data.summary.not_detected,
            "risk_level": risk_level,
            "tactics_tested": tactics_tested,
            "tactics_with_gaps": tactics_with_gaps,
            "techniques_tested": len(data.mitre_coverage),
            "techniques_detected": sum(
                1 for t in data.mitre_coverage.values() if t.detected > 0
            ),
            "hosts_tested": len(data.per_host_analysis),
            "critical_recommendations": sum(
                1 for r in data.rule_recommendations if r.priority == "critical"
            ),
        }


def gather_detection_report_data(engagement_id: int) -> DetectionReportData:
    """
    Convenience function to gather detection report data.

    Args:
        engagement_id: Engagement to report on

    Returns:
        DetectionReportData
    """
    gatherer = DetectionReportGatherer(engagement_id)
    return gatherer.gather_data()
