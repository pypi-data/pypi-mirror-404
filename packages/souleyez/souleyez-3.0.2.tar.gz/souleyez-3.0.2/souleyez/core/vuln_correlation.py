#!/usr/bin/env python3
"""
souleyez.core.vuln_correlation - Correlate findings across tools and identify attack paths

Analyzes findings from multiple tools to:
1. Identify duplicate/related vulnerabilities
2. Build attack chains (e.g., vuln A + cred B = exploit C)
3. Prioritize findings based on correlation
4. Suggest exploit paths
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CorrelatedFinding:
    """Represents a group of related findings from different tools."""

    cve_id: Optional[str] = None
    service: str = ""
    port: int = 0
    host_ip: str = ""
    severity: str = "info"
    finding_ids: List[int] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0 to 1.0
    description: str = ""
    exploit_available: bool = False

    def add_finding(self, finding: Dict[str, Any]):
        """Add a finding to this correlation group."""
        finding_id = finding.get("id")
        tool = finding.get("tool", "")

        if finding_id and finding_id not in self.finding_ids:
            self.finding_ids.append(finding_id)

        if tool and tool not in self.tools:
            self.tools.append(tool)

        # Update severity to highest
        severities = ["critical", "high", "medium", "low", "info"]
        current_idx = (
            severities.index(self.severity) if self.severity in severities else 4
        )
        new_idx = (
            severities.index(finding.get("severity", "info"))
            if finding.get("severity") in severities
            else 4
        )

        if new_idx < current_idx:
            self.severity = severities[new_idx]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cve_id": self.cve_id,
            "service": self.service,
            "port": self.port,
            "host_ip": self.host_ip,
            "severity": self.severity,
            "finding_ids": self.finding_ids,
            "tools": self.tools,
            "confidence": self.confidence,
            "description": self.description,
            "exploit_available": self.exploit_available,
        }


@dataclass
class AttackPath:
    """Represents a potential attack path using multiple findings."""

    name: str
    findings: List[Dict[str, Any]] = field(default_factory=list)
    success_probability: float = 0.0
    impact: str = "low"
    steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "finding_ids": [f.get("id") for f in self.findings],
            "success_probability": self.success_probability,
            "impact": self.impact,
            "steps": self.steps,
        }


class VulnerabilityCorrelator:
    """Correlates findings across tools to identify patterns and attack paths."""

    def __init__(self):
        """Initialize correlator."""

    def correlate_by_cve(
        self, findings: List[Dict[str, Any]]
    ) -> List[CorrelatedFinding]:
        """
        Group findings by CVE ID.

        Multiple tools might report the same CVE.
        """
        cve_groups = {}

        for finding in findings:
            # Extract CVE from various fields
            cve_id = finding.get("cve_id")
            if not cve_id:
                # Try to extract from refs or description
                refs = finding.get("refs", "")
                desc = finding.get("description", "")
                text = f"{refs} {desc}"

                cve_matches = re.findall(r"CVE-\d{4}-\d{4,7}", text, re.IGNORECASE)
                if cve_matches:
                    cve_id = cve_matches[0].upper()

            if cve_id:
                if cve_id not in cve_groups:
                    cve_groups[cve_id] = CorrelatedFinding(
                        cve_id=cve_id,
                        service=finding.get("service", ""),
                        port=finding.get("port", 0),
                        host_ip=self._extract_host_ip(finding),
                        confidence=0.95,  # High confidence for CVE matching
                    )

                cve_groups[cve_id].add_finding(finding)

        return list(cve_groups.values())

    def correlate_by_service(
        self, findings: List[Dict[str, Any]]
    ) -> List[CorrelatedFinding]:
        """
        Group findings by service/port combination.

        Findings about the same service on the same port are related.
        """
        service_groups = {}

        for finding in findings:
            host_ip = self._extract_host_ip(finding)
            port = finding.get("port", 0)

            # Skip findings without port/host
            if not host_ip or not port:
                continue

            key = f"{host_ip}:{port}"

            if key not in service_groups:
                service_groups[key] = CorrelatedFinding(
                    service=self._extract_service_name(finding),
                    port=port,
                    host_ip=host_ip,
                    confidence=0.7,  # Medium-high confidence
                )

            service_groups[key].add_finding(finding)

        # Only return groups with multiple findings
        return [g for g in service_groups.values() if len(g.finding_ids) > 1]

    def correlate_by_vulnerability_type(
        self, findings: List[Dict[str, Any]]
    ) -> List[CorrelatedFinding]:
        """
        Group findings by vulnerability type (SQL injection, XSS, RCE, etc.).
        """
        vuln_types = {
            "sqli": ["sql injection", "sqlmap", "blind sql"],
            "xss": ["cross-site scripting", "xss", "reflected xss", "stored xss"],
            "rce": [
                "remote code execution",
                "command injection",
                "shell upload",
                "arbitrary code",
            ],
            "lfi": ["local file inclusion", "directory traversal", "path traversal"],
            "auth_bypass": [
                "authentication bypass",
                "broken authentication",
                "default credentials",
            ],
            "info_disclosure": [
                "information disclosure",
                "sensitive data",
                "directory listing",
            ],
        }

        type_groups = {}

        for finding in findings:
            title = finding.get("title", "").lower()
            desc = finding.get("description", "").lower()
            text = f"{title} {desc}"

            for vuln_type, keywords in vuln_types.items():
                if any(kw in text for kw in keywords):
                    host_ip = self._extract_host_ip(finding)
                    key = f"{host_ip}:{vuln_type}"

                    if key not in type_groups:
                        type_groups[key] = CorrelatedFinding(
                            host_ip=host_ip,
                            description=f"Multiple {vuln_type.upper()} vulnerabilities",
                            confidence=0.6,
                        )

                    type_groups[key].add_finding(finding)

        # Only return groups with multiple findings
        return [g for g in type_groups.values() if len(g.finding_ids) > 1]

    def find_attack_paths(
        self,
        findings: List[Dict[str, Any]],
        credentials: List[Dict[str, Any]] = None,
        smb_shares: List[Dict[str, Any]] = None,
    ) -> List[AttackPath]:
        """
        Identify potential attack paths by chaining vulnerabilities and access.

        Examples:
        - RCE vuln + valid cred = complete compromise
        - Writable SMB share + RCE = lateral movement
        - SQL injection + database access = data exfiltration
        """
        paths = []
        credentials = credentials or []
        smb_shares = smb_shares or []

        # Group findings by host
        by_host = {}
        for finding in findings:
            host_ip = self._extract_host_ip(finding)
            if host_ip:
                if host_ip not in by_host:
                    by_host[host_ip] = []
                by_host[host_ip].append(finding)

        # Analyze each host
        for host_ip, host_findings in by_host.items():
            # Path 1: RCE + Valid Credentials
            rce_findings = [f for f in host_findings if self._is_rce(f)]
            host_creds = [
                c
                for c in credentials
                if c.get("ip_address") == host_ip and c.get("status") == "valid"
            ]

            if rce_findings and host_creds:
                path = AttackPath(
                    name=f"RCE + Credentials on {host_ip}",
                    findings=rce_findings + host_creds,
                    success_probability=0.8,
                    impact="critical",
                    steps=[
                        f"1. Exploit {rce_findings[0].get('title')} for code execution",
                        f"2. Use valid credentials: {host_creds[0].get('username')} / {host_creds[0].get('password')}",
                        "3. Establish persistent access",
                        "4. Escalate privileges if needed",
                    ],
                )
                paths.append(path)

            # Path 2: SQL Injection + Database
            sqli_findings = [
                f for f in host_findings if "sql" in f.get("title", "").lower()
            ]
            if sqli_findings:
                path = AttackPath(
                    name=f"SQL Injection on {host_ip}",
                    findings=sqli_findings,
                    success_probability=0.7,
                    impact="high",
                    steps=[
                        f"1. Exploit SQL injection: {sqli_findings[0].get('path', '')}",
                        "2. Enumerate database schema",
                        "3. Extract sensitive data (users, passwords, etc.)",
                        "4. Attempt to read files or execute commands (if possible)",
                    ],
                )
                paths.append(path)

            # Path 3: Writable SMB + Any Access
            host_shares = [
                s
                for s in smb_shares
                if s.get("ip_address") == host_ip and s.get("writable")
            ]
            if host_shares:
                path = AttackPath(
                    name=f"Writable SMB Share on {host_ip}",
                    findings=host_findings,
                    success_probability=0.6,
                    impact="high",
                    steps=[
                        f"1. Access writable share: \\\\{host_ip}\\{host_shares[0].get('share_name')}",
                        "2. Upload malicious files (exe, dll, script)",
                        "3. Wait for execution or trigger manually",
                        "4. Gain code execution on the system",
                    ],
                )
                paths.append(path)

            # Path 4: Authentication Bypass + Service Access
            auth_bypass = [
                f
                for f in host_findings
                if "auth" in f.get("title", "").lower()
                and "bypass" in f.get("title", "").lower()
            ]
            if auth_bypass:
                path = AttackPath(
                    name=f"Authentication Bypass on {host_ip}",
                    findings=auth_bypass,
                    success_probability=0.75,
                    impact="high",
                    steps=[
                        f"1. Exploit authentication bypass: {auth_bypass[0].get('title')}",
                        "2. Gain unauthorized access to application",
                        "3. Enumerate accessible functions",
                        "4. Look for privilege escalation opportunities",
                    ],
                )
                paths.append(path)

        # Sort by impact and probability
        impact_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        paths.sort(
            key=lambda p: (impact_order.get(p.impact, 3), -p.success_probability)
        )

        return paths

    def _extract_host_ip(self, finding: Dict[str, Any]) -> str:
        """Extract host IP from finding."""
        # Direct field
        if "ip_address" in finding:
            return finding["ip_address"]

        # From target field
        target = finding.get("target", "")
        # Extract IP from URL or plain IP
        import re

        ip_match = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", target)
        if ip_match:
            return ip_match.group(0)

        return ""

    def _extract_service_name(self, finding: Dict[str, Any]) -> str:
        """Extract service name from finding."""
        if "service" in finding:
            return finding["service"]

        # Try to infer from tool
        tool = finding.get("tool", "").lower()
        if tool == "nuclei":
            return "http"
        elif tool == "smbmap":
            return "smb"
        elif tool == "sqlmap":
            return "database"

        return finding.get("finding_type", "unknown")

    def _is_rce(self, finding: Dict[str, Any]) -> bool:
        """Check if finding is related to RCE."""
        text = f"{finding.get('title', '')} {finding.get('description', '')}".lower()
        rce_keywords = [
            "remote code execution",
            "command injection",
            "arbitrary code",
            "shell upload",
            "code exec",
            "rce",
        ]
        return any(kw in text for kw in rce_keywords)

    def generate_correlation_report(
        self,
        findings: List[Dict[str, Any]],
        credentials: List[Dict[str, Any]] = None,
        smb_shares: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive correlation report.

        Returns:
            {
                'cve_correlations': [...],
                'service_correlations': [...],
                'type_correlations': [...],
                'attack_paths': [...],
                'summary': {...}
            }
        }
        """
        cve_corr = self.correlate_by_cve(findings)
        service_corr = self.correlate_by_service(findings)
        type_corr = self.correlate_by_vulnerability_type(findings)
        attack_paths = self.find_attack_paths(findings, credentials, smb_shares)

        return {
            "cve_correlations": [c.to_dict() for c in cve_corr],
            "service_correlations": [c.to_dict() for c in service_corr],
            "type_correlations": [c.to_dict() for c in type_corr],
            "attack_paths": [p.to_dict() for p in attack_paths],
            "summary": {
                "total_findings": len(findings),
                "cve_groups": len(cve_corr),
                "service_groups": len(service_corr),
                "type_groups": len(type_corr),
                "attack_paths": len(attack_paths),
                "high_confidence_correlations": len(
                    [c for c in cve_corr if c.confidence > 0.8]
                ),
            },
        }


# Global instance
_correlator = None


def get_correlator() -> VulnerabilityCorrelator:
    """Get the global correlator instance."""
    global _correlator
    if _correlator is None:
        _correlator = VulnerabilityCorrelator()
    return _correlator
