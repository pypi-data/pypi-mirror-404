#!/usr/bin/env python3
"""
Gap detector for identifying unexploited services.
Prioritizes gaps by exploitation potential.
"""

from typing import Dict, List

from souleyez.intelligence.correlation_analyzer import CorrelationAnalyzer


class GapDetector:
    """Detect gaps in exploitation coverage."""

    def __init__(self):
        self.analyzer = CorrelationAnalyzer()

    def find_gaps(self, engagement_id: int) -> List[Dict]:
        """
        Find services that haven't been attempted.

        Returns:
            [
                {
                    'host': '10.0.0.5',
                    'hostname': 'target.local',
                    'port': 3306,
                    'service': 'mysql',
                    'version': 'MySQL 5.0.51a',
                    'reason': 'Service discovered but no exploitation attempts',
                    'severity': 'high',
                    'suggested_actions': [...],
                    'msf_modules': [...],
                    'priority_score': 85
                }
            ]
        """
        # Run full engagement analysis
        analysis = self.analyzer.analyze_engagement(engagement_id)

        # Extract gaps
        gaps = analysis.get("gaps", [])

        # Enrich gaps with MSF modules and priority scores
        enriched_gaps = []
        for gap in gaps:
            enriched = gap.copy()

            # Add MSF module suggestions
            enriched["msf_modules"] = self._get_msf_modules(
                gap.get("service"), gap.get("version")
            )

            # Calculate priority score
            enriched["priority_score"] = self._calculate_priority_score(gap)

            enriched_gaps.append(enriched)

        return enriched_gaps

    def prioritize_gaps(self, gaps: List[Dict]) -> List[Dict]:
        """
        Prioritize gaps by exploitation potential.

        Ranking factors:
        1. Service criticality (database > admin > standard)
        2. Known vulnerabilities (version-specific exploits)
        3. Port accessibility (open vs filtered)
        4. Version info available
        """
        # Sort by priority_score (descending)
        prioritized = sorted(
            gaps, key=lambda g: g.get("priority_score", 0), reverse=True
        )

        return prioritized

    def _calculate_priority_score(self, gap: Dict) -> int:
        """
        Calculate priority score (0-100).

        Factors:
        - Severity: critical=40, high=30, medium=20, low=10
        - Version known: +20
        - Known CVE in version: +30
        - Database/admin service: +10
        """
        score = 0

        # Severity baseline
        severity_scores = {"critical": 40, "high": 30, "medium": 20, "low": 10}
        score += severity_scores.get(gap.get("severity", "low"), 10)

        # Version information available
        if gap.get("version"):
            score += 20

            # Check for known vulnerable versions
            if gap.get("service") and self._has_known_vulnerability(
                gap["service"], gap["version"]
            ):
                score += 30

        # High-value service types
        service = (gap.get("service") or "").lower()
        if service in [
            "mysql",
            "postgres",
            "mssql",
            "mongodb",
            "redis",
            "ssh",
            "rdp",
            "smb",
        ]:
            score += 10

        return min(score, 100)

    def _has_known_vulnerability(self, service: str, version: str) -> bool:
        """Check if service version has known vulnerabilities."""
        if not version:
            return False

        if not service:
            return False

        version_lower = version.lower()
        service_lower = service.lower()

        # Known vulnerable versions
        vulnerable_patterns = {
            "vsftpd": ["2.3.4"],
            "mysql": ["5.0", "5.1"],
            "samba": ["3.5", "3.6", "4.4", "4.5"],
            "openssh": ["7.2", "7.3", "7.4"],
            "proftpd": ["1.3.3", "1.3.5"],
        }

        if service_lower in vulnerable_patterns:
            for vuln_version in vulnerable_patterns[service_lower]:
                if vuln_version in version_lower:
                    return True

        return False

    def get_suggested_actions(self, service: str, version: str = None) -> List[str]:
        """
        Get suggested exploitation actions for a service.

        Examples:
            get_suggested_actions('mysql') → ['Try mysql_login', 'Check for weak passwords']
            get_suggested_actions('ftp', 'vsftpd 2.3.4') → ['Try vsftpd_234_backdoor exploit']
        """
        actions = []

        if not service:
            return actions

        service_lower = service.lower()

        # Version-specific exploits
        if version:
            version_lower = version.lower()

            if "vsftpd 2.3.4" in version_lower:
                actions.append("💥 CRITICAL: Try vsftpd_234_backdoor exploit")

            if "samba" in version_lower or "smb" in service_lower:
                if any(v in version_lower for v in ["3.5", "3.6", "4.4", "4.5", "4.6"]):
                    actions.append("💥 CRITICAL: Check for SambaCry (CVE-2017-7494)")

            if "mysql" in version_lower and "5.0" in version_lower:
                actions.append(
                    "💥 HIGH: Try mysql_yassl_getname exploit (CVE-2009-2446)"
                )

        # Generic service actions
        if service_lower == "ssh":
            actions.extend(
                [
                    "Try ssh_login with default credentials",
                    "Brute force with passwords_brute.txt",
                    "Check for user enumeration (CVE-2018-15473)",
                ]
            )

        elif service_lower == "ftp":
            actions.extend(
                [
                    "Try anonymous FTP login",
                    "Check for directory traversal",
                    "Test for bounce attack",
                ]
            )

        elif service_lower in ["mysql", "mariadb"]:
            actions.extend(
                [
                    "Try mysql_login brute force",
                    "Check for default root password",
                    "Test for mysql_hashdump access",
                ]
            )

        elif service_lower == "smb":
            actions.extend(
                [
                    "Try SMB null session enumeration",
                    "Check for EternalBlue (MS17-010)",
                    "Test smb_login brute force",
                ]
            )

        elif service_lower in ["http", "https"]:
            actions.extend(
                [
                    "Run Nuclei vulnerability scan",
                    "Try Gobuster directory enumeration",
                    "Check for SQLi with SQLMap",
                ]
            )

        elif service_lower == "rdp":
            actions.extend(
                [
                    "Try BlueKeep exploit (CVE-2019-0708)",
                    "Brute force RDP credentials",
                    "Check for weak encryption",
                ]
            )

        elif service_lower == "postgres":
            actions.extend(
                [
                    "Try postgres_login brute force",
                    "Check for default postgres password",
                    "Test for SQL injection",
                ]
            )

        elif service_lower == "telnet":
            actions.extend(
                [
                    "Try telnet_login with defaults",
                    "Brute force credentials",
                    "Capture credentials with packet sniffing",
                ]
            )

        elif service_lower == "smtp":
            actions.extend(
                [
                    "Enumerate users with VRFY/EXPN",
                    "Check for open relay",
                    "Try SMTP auth brute force",
                ]
            )

        else:
            actions.append(f"Research exploits for {service}")
            actions.append(f"Try default credential lists")

        return actions

    def _get_msf_modules(self, service: str, version: str = None) -> List[str]:
        """Get relevant Metasploit modules for a service."""
        if not service:
            return []

        modules = []
        service_lower = service.lower()

        # Version-specific exploits
        if version:
            version_lower = version.lower()

            if "vsftpd 2.3.4" in version_lower:
                modules.append("exploit/unix/ftp/vsftpd_234_backdoor")

            if "mysql" in version_lower and "5.0" in version_lower:
                modules.append("exploit/linux/mysql/mysql_yassl_getname")

            if "samba" in version_lower:
                modules.append("exploit/linux/samba/is_known_pipename")

        # Generic service modules
        if service_lower == "ssh":
            modules.extend(
                [
                    "auxiliary/scanner/ssh/ssh_login",
                    "auxiliary/scanner/ssh/ssh_enumusers",
                ]
            )

        elif service_lower == "ftp":
            modules.extend(
                ["auxiliary/scanner/ftp/ftp_login", "auxiliary/scanner/ftp/anonymous"]
            )

        elif service_lower in ["mysql", "mariadb"]:
            modules.extend(
                [
                    "auxiliary/scanner/mysql/mysql_login",
                    "auxiliary/admin/mysql/mysql_enum",
                    "auxiliary/admin/mysql/mysql_hashdump",
                ]
            )

        elif service_lower == "smb":
            modules.extend(
                [
                    "auxiliary/scanner/smb/smb_login",
                    "exploit/windows/smb/ms17_010_eternalblue",
                    "auxiliary/scanner/smb/smb_ms17_010",
                ]
            )

        elif service_lower == "rdp":
            modules.extend(
                [
                    "auxiliary/scanner/rdp/rdp_scanner",
                    "exploit/windows/rdp/cve_2019_0708_bluekeep_rce",
                ]
            )

        elif service_lower == "postgres":
            modules.extend(
                [
                    "auxiliary/scanner/postgres/postgres_login",
                    "auxiliary/admin/postgres/postgres_sql",
                ]
            )

        elif service_lower == "telnet":
            modules.extend(
                [
                    "auxiliary/scanner/telnet/telnet_login",
                    "auxiliary/scanner/telnet/telnet_version",
                ]
            )

        elif service_lower == "smtp":
            modules.extend(
                [
                    "auxiliary/scanner/smtp/smtp_enum",
                    "auxiliary/scanner/smtp/smtp_version",
                ]
            )

        return modules

    def get_gap_summary(self, engagement_id: int) -> Dict:
        """
        Get quick summary of exploitation gaps.

        Returns:
            {
                'total_gaps': 10,
                'by_severity': {
                    'critical': 3,
                    'high': 4,
                    'medium': 2,
                    'low': 1
                },
                'top_priorities': [
                    {'host': '10.0.0.5', 'port': 3306, 'service': 'mysql', 'score': 90}
                ]
            }
        """
        gaps = self.find_gaps(engagement_id)
        prioritized = self.prioritize_gaps(gaps)

        # Count by severity
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for gap in gaps:
            severity = gap.get("severity", "low")
            by_severity[severity] = by_severity.get(severity, 0) + 1

        # Get top 5 priorities
        top_priorities = []
        for gap in prioritized[:5]:
            top_priorities.append(
                {
                    "host": gap["host"],
                    "port": gap["port"],
                    "service": gap.get("service") or "unknown",
                    "score": gap["priority_score"],
                }
            )

        return {
            "total_gaps": len(gaps),
            "by_severity": by_severity,
            "top_priorities": top_priorities,
        }
