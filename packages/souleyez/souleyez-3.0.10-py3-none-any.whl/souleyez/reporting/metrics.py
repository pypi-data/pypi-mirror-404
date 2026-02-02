#!/usr/bin/env python3
"""
Report metrics and risk score calculations.
Provides executive dashboard metrics for pentest reports.
"""

from datetime import datetime
from typing import Dict, List


class MetricsCalculator:
    """Calculate executive dashboard metrics and risk scores."""

    def __init__(self):
        pass

    def calculate_risk_score(self, findings_by_severity: Dict) -> int:
        """
        Calculate overall risk score (0-100).

        Weighted scoring:
        - Critical: 25 points each
        - High: 10 points each
        - Medium: 3 points each
        - Low: 1 point each
        - Info: 0 points

        Capped at 100.
        """
        score = 0
        score += len(findings_by_severity.get("critical", [])) * 25
        score += len(findings_by_severity.get("high", [])) * 10
        score += len(findings_by_severity.get("medium", [])) * 3
        score += len(findings_by_severity.get("low", [])) * 1

        return min(score, 100)

    def calculate_exploitation_rate(self, attack_surface: Dict) -> float:
        """Calculate percentage of services successfully exploited."""
        overview = attack_surface.get("overview", {})
        total_services = overview.get("total_services", 0)
        exploited = overview.get("exploited_services", 0)

        if total_services == 0:
            return 0.0

        return round((exploited / total_services) * 100, 1)

    def estimate_remediation_timeline(self, findings_by_severity: Dict) -> Dict:
        """
        Estimate remediation timeline in days.

        Estimates:
        - Critical: 1 day each
        - High: 0.5 days each
        - Medium: 0.25 days each
        - Low: 0.1 days each
        """
        critical_days = len(findings_by_severity.get("critical", [])) * 1
        high_days = len(findings_by_severity.get("high", [])) * 0.5
        medium_days = len(findings_by_severity.get("medium", [])) * 0.25
        low_days = len(findings_by_severity.get("low", [])) * 0.1

        total_days = critical_days + high_days + medium_days + low_days

        return {
            "total_days": round(total_days, 1),
            "weeks": round(total_days / 5, 1),  # Business days
            "critical": round(critical_days, 1),
            "high": round(high_days, 1),
            "medium": round(medium_days, 1),
            "low": round(low_days, 1),
        }

    def calculate_host_risk_distribution(self, attack_surface: Dict) -> Dict:
        """Calculate risk distribution across hosts."""
        hosts = attack_surface.get("hosts", [])

        distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for host in hosts:
            critical_findings = host.get("critical_findings", 0)
            total_findings = host.get("findings", 0)

            if critical_findings > 0:
                distribution["critical"] += 1
            elif total_findings >= 5:
                distribution["high"] += 1
            elif total_findings >= 2:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1

        return distribution

    def get_dashboard_metrics(self, data: Dict) -> Dict:
        """
        Generate all executive dashboard metrics.

        Returns comprehensive metrics dict for dashboard rendering.
        """
        findings_by_severity = data["findings_by_severity"]
        attack_surface = data["attack_surface"]

        risk_score = self.calculate_risk_score(findings_by_severity)
        exploitation_rate = self.calculate_exploitation_rate(attack_surface)
        remediation = self.estimate_remediation_timeline(findings_by_severity)
        host_distribution = self.calculate_host_risk_distribution(attack_surface)

        # Determine risk level
        if risk_score >= 75:
            risk_level = "CRITICAL"
            risk_color = "red"
        elif risk_score >= 50:
            risk_level = "HIGH"
            risk_color = "orange"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
            risk_color = "yellow"
        else:
            risk_level = "LOW"
            risk_color = "green"

        # Total findings
        total_findings = sum(
            len(findings) for findings in findings_by_severity.values()
        )

        # Overview stats
        overview = attack_surface.get("overview", {})

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_color": risk_color,
            "total_findings": total_findings,
            "critical_findings": len(findings_by_severity.get("critical", [])),
            "high_findings": len(findings_by_severity.get("high", [])),
            "medium_findings": len(findings_by_severity.get("medium", [])),
            "low_findings": len(findings_by_severity.get("low", [])),
            "info_findings": len(findings_by_severity.get("info", [])),
            "total_hosts": overview.get("total_hosts", 0),
            "vulnerable_hosts": overview.get("vulnerable_hosts", 0),
            "total_services": overview.get("total_services", 0),
            "exploited_services": overview.get("exploited_services", 0),
            "exploitation_rate": exploitation_rate,
            "remediation_timeline": remediation,
            "host_risk_distribution": host_distribution,
            "credentials_found": len(data.get("credentials", [])),
        }
