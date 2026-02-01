#!/usr/bin/env python3
"""
Attack surface analysis and scoring.
Analyzes engagement data to identify high-value targets and exploitation gaps.
"""

import math
import time
from typing import Dict, List, Optional

# Module-level cache shared across all instances
_ANALYSIS_CACHE = {}
_CACHE_TIMEOUT = 30


class AttackSurfaceAnalyzer:
    """Analyzes and scores attack surface for pentesting engagements."""

    def __init__(self):
        from souleyez.storage.credentials import CredentialsManager
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager
        from souleyez.storage.wazuh_vulns import WazuhVulnsManager

        self.hosts_mgr = HostManager()
        self.findings_mgr = FindingsManager()
        self.creds_mgr = CredentialsManager()
        self.wazuh_mgr = WazuhVulnsManager()

    def analyze_engagement(self, engagement_id: int) -> Dict:
        """
        Analyze complete attack surface for engagement.
        Results cached for 30 seconds to improve dashboard performance.

        Returns:
            {
                'overview': {...},
                'hosts': [...],  # Sorted by score
                'recommendations': [...]
            }
        """
        # Check cache first
        cache_key = f"engagement_{engagement_id}"
        if cache_key in _ANALYSIS_CACHE:
            cached_result, cached_time = _ANALYSIS_CACHE[cache_key]
            if time.time() - cached_time < _CACHE_TIMEOUT:
                return cached_result

        # Cache miss or expired - do the analysis
        all_hosts = self.hosts_mgr.list_hosts(engagement_id)

        # Fetch findings and creds once for efficiency
        findings = self.findings_mgr.list_findings(engagement_id)
        credentials = self.creds_mgr.list_credentials(engagement_id)

        # Fetch Wazuh vulnerabilities for this engagement
        wazuh_vulns = self.wazuh_mgr.list_vulnerabilities(engagement_id, limit=10000)

        # Fetch exploit attempts for this engagement
        from souleyez.storage.exploit_attempts import get_attempts_by_engagement

        exploit_attempts = get_attempts_by_engagement(engagement_id)

        # Filter to active hosts only
        hosts = [
            h
            for h in all_hosts
            if h.get("status") == "up" or self._has_activity(h, findings, credentials)
        ]

        # Get jobs
        from souleyez.engine.background import list_jobs

        all_jobs = list_jobs()
        jobs = [j for j in all_jobs if j.get("engagement_id") == engagement_id]

        # Calculate attack surface for each host
        host_surfaces = []
        for host in hosts:
            surface = self._analyze_host(
                host, findings, credentials, jobs, exploit_attempts, wazuh_vulns
            )
            host_surfaces.append(surface)

        # Sort by attack surface score (highest first)
        host_surfaces.sort(key=lambda x: x["score"], reverse=True)

        # Generate overview
        overview = self._generate_overview(host_surfaces, findings, credentials)

        # Generate recommendations
        recommendations = self._generate_recommendations(host_surfaces)

        result = {
            "overview": overview,
            "hosts": host_surfaces,
            "recommendations": recommendations,
        }

        # Cache the result
        _ANALYSIS_CACHE[cache_key] = (result, time.time())

        return result

    def _analyze_host(
        self,
        host: Dict,
        findings: List[Dict],
        credentials: List[Dict],
        jobs: List[Dict],
        exploit_attempts: List[Dict] = None,
        wazuh_vulns: List[Dict] = None,
    ) -> Dict:
        """Analyze attack surface for a single host."""
        host_ip = (
            host.get("ip") or host.get("ip_address") or host.get("address", "Unknown")
        )
        host_id = host.get("id")

        # Get services for this host from database
        services = []
        if host_id:
            services = self.hosts_mgr.get_host_services(host_id)
        else:
            # Fallback: check if services embedded in host object
            services = host.get("services", [])

        # Get findings for this host
        host_findings = [
            f
            for f in findings
            if f.get("ip_address") == host_ip
            or (f.get("url") or "").startswith(f"http://{host_ip}")
            or (f.get("url") or "").startswith(f"https://{host_ip}")
        ]
        critical_findings = [
            f for f in host_findings if f.get("severity") == "critical"
        ]
        high_findings = [f for f in host_findings if f.get("severity") == "high"]

        # Get Wazuh vulnerabilities for this host (by mapped host_id or agent_ip)
        host_wazuh_vulns = []
        if wazuh_vulns:
            host_wazuh_vulns = [
                v
                for v in wazuh_vulns
                if v.get("host_id") == host_id
                or v.get("agent_ip") == host_ip
                or v.get("host_ip") == host_ip
            ]
        wazuh_critical = [
            v for v in host_wazuh_vulns if v.get("severity") == "Critical"
        ]
        wazuh_high = [v for v in host_wazuh_vulns if v.get("severity") == "High"]

        # Fallback: Create synthetic services from findings if no services exist
        # This handles legacy data where web targets have findings but no service entries
        if not services and host_findings:
            ports_found = {}

            for finding in host_findings:
                port = finding.get("port")
                path = finding.get("path") or finding.get("url", "")

                # Extract port from URL if not directly available
                if not port and path:
                    if path.startswith("https://"):
                        port = 443
                    elif path.startswith("http://"):
                        port = 80

                if port:
                    # Determine service name from port
                    if port not in ports_found:
                        service_name = (
                            "http"
                            if port in [80, 8080, 8000]
                            else "https" if port == 443 else "unknown"
                        )
                        ports_found[port] = {
                            "port": port,
                            "service": service_name,
                            "service_name": service_name,
                            "protocol": "tcp",
                            "state": "open",
                            "version": None,
                            "synthetic": True,  # Flag as synthetic for reference
                            "status": "attempted",  # Has findings, so mark as attempted
                            "credentials": 0,
                            "findings": 0,
                            "jobs_run": 0,
                        }

            # Convert to list and count findings per synthetic service
            services = list(ports_found.values())
            for service in services:
                service["findings"] = len(
                    [
                        f
                        for f in host_findings
                        if f.get("port") == service["port"]
                        or (
                            (f.get("path") or "").startswith("https://")
                            and service["port"] == 443
                        )
                        or (
                            (f.get("path") or "").startswith("http://")
                            and service["port"] == 80
                        )
                    ]
                )
                service["credentials"] = len(
                    [c for c in credentials if c.get("port") == service["port"]]
                )

        # Calculate attack surface score (includes Wazuh vulnerabilities)
        score = self._calculate_score(
            host,
            services,
            host_findings,
            critical_findings,
            high_findings,
            host_wazuh_vulns,
            wazuh_critical,
            wazuh_high,
        )

        # Filter exploit attempts for this host
        host_exploit_attempts = []
        if exploit_attempts:
            host_exploit_attempts = [
                a
                for a in exploit_attempts
                if a.get("host_id") == host_id or a.get("ip_address") == host_ip
            ]

        # Analyze exploitation status per service
        service_statuses = []
        for service in services:
            status = self._analyze_service_exploitation(
                host_ip,
                service,
                jobs,
                credentials,
                host_findings,
                host_exploit_attempts,
            )
            service_statuses.append(status)

        # Count exploitation progress
        exploited = len([s for s in service_statuses if s["status"] == "exploited"])
        attempted = len([s for s in service_statuses if s["status"] == "attempted"])
        not_tried = len([s for s in service_statuses if s["status"] == "not_tried"])

        # Generate reasoning for why this host is high priority
        reasoning_parts = []
        if critical_findings:
            reasoning_parts.append(f"{len(critical_findings)} critical finding(s)")
        if high_findings:
            reasoning_parts.append(f"{len(high_findings)} high severity finding(s)")
        if wazuh_critical:
            reasoning_parts.append(f"{len(wazuh_critical)} Wazuh critical CVE(s)")
        if wazuh_high:
            reasoning_parts.append(f"{len(wazuh_high)} Wazuh high CVE(s)")
        if exploited > 0:
            reasoning_parts.append(f"{exploited} service(s) exploited")
        if not_tried > 0:
            reasoning_parts.append(f"{not_tried} untested service(s)")

        reasoning = (
            ", ".join(reasoning_parts)
            if reasoning_parts
            else "Open services discovered"
        )

        return {
            "host": host_ip,
            "hostname": host.get("hostname"),
            "score": score,
            "open_ports": len(services),
            "service_count": len(services),
            "services": service_statuses,  # Full list for display
            "findings": len(host_findings),
            "critical_findings": len(critical_findings),
            "high_findings": len(high_findings),
            "wazuh_vulns": len(host_wazuh_vulns),
            "wazuh_critical": len(wazuh_critical),
            "wazuh_high": len(wazuh_high),
            "reasoning": reasoning,
            "exploitation_progress": {
                "exploited": exploited,
                "attempted": attempted,
                "not_tried": not_tried,
                "total": len(services),
            },
        }

    def _calculate_score(
        self,
        host: Dict,
        services: List[Dict],
        findings: List[Dict],
        critical_findings: List[Dict],
        high_findings: List[Dict],
        wazuh_vulns: List[Dict] = None,
        wazuh_critical: List[Dict] = None,
        wazuh_high: List[Dict] = None,
    ) -> int:
        """
        Calculate attack surface score (0-100 scale).

        Uses logarithmic normalization to compress unbounded raw scores
        into a meaningful 0-100 range while preserving differentiation.

        Scoring factors:
        - Services: 2 pts each (discovery) + 3 pts each (identification)
        - Findings: 5 pts each, +8 for high severity, +15 for critical
        - Wazuh vulns: 4 pts each, +8 for high severity, +12 for critical
        """
        wazuh_vulns = wazuh_vulns or []
        wazuh_critical = wazuh_critical or []
        wazuh_high = wazuh_high or []

        # Calculate raw score using weighted factors
        raw_score = (
            len(services) * 2  # Each port/service
            + len(services) * 3  # Service identification
            + len(findings) * 5  # Total findings
            + len(high_findings) * 8  # High severity findings
            + len(critical_findings) * 15  # Critical severity findings
            + len(wazuh_vulns) * 4  # Wazuh vulnerabilities (passive detection)
            + len(wazuh_high) * 8  # Wazuh high severity
            + len(wazuh_critical) * 12  # Wazuh critical severity
        )

        # Normalize to 0-100 using logarithmic scale
        # Formula: min(100, 20 * log10(raw_score + 10))
        # - The +10 prevents log(0) errors for empty hosts
        # - The ×20 multiplier calibrates to 0-100 range
        # - The min(100, ...) ensures we never exceed 100
        #
        # Example transformations:
        #   raw=660 → normalized=95 (CRITICAL)
        #   raw=305 → normalized=85 (CRITICAL)
        #   raw=135 → normalized=70 (HIGH)
        #   raw=75  → normalized=55 (MEDIUM)
        #   raw=30  → normalized=35 (LOW)
        if raw_score == 0:
            return 0

        normalized_score = min(100, int(20 * math.log10(raw_score + 10)))
        return normalized_score

    def _analyze_service_exploitation(
        self,
        host: str,
        service: Dict,
        jobs: List[Dict],
        credentials: List[Dict],
        findings: List[Dict],
        exploit_attempts: List[Dict] = None,
    ) -> Dict:
        """Determine exploitation status for a service."""
        port = service.get("port")
        service_id = service.get("id")
        service_name = service.get("service_name") or "unknown"
        version = service.get("service_version") or ""

        # Check for manual exploit attempts on this service
        service_exploit_attempts = []
        if exploit_attempts:
            service_exploit_attempts = [
                a
                for a in exploit_attempts
                if a.get("service_id") == service_id or a.get("port") == port
            ]

        # Check for credentials on this service
        service_creds = [
            c
            for c in credentials
            if c.get("ip_address") == host and c.get("port") == port
        ]

        # Check for findings on this service - Multi-tier matching
        # Tier 1: Exact match by port
        service_findings = [
            f for f in findings if f.get("ip_address") == host and f.get("port") == port
        ]

        # Tier 2: Fallback for web services - match by host only if port-based match failed
        if not service_findings and port in [80, 443, 8080, 8000, 8443]:
            service_findings = [
                f
                for f in findings
                if f.get("ip_address") == host
                and f.get("severity") in ["critical", "high"]
            ]

        # Check for EXPLOIT jobs targeting this specific service (host + port)
        # Only count actual exploitation tools, not recon tools like nmap
        import re

        exploit_tools = {
            "msfconsole",
            "msf",
            "hydra",
            "medusa",
            "sqlmap",
            "crackmapexec",
        }
        service_jobs = []
        for j in jobs:
            if host not in (j.get("target") or ""):
                continue
            if j.get("status") not in ["done", "error", "no_results"]:
                continue
            if j.get("tool", "").lower() not in exploit_tools:
                continue
            # Extract port from job args
            args = j.get("args", [])
            args_str = " ".join(args) if args else ""
            port_match = re.search(
                r"RPORT\s+(\d+)|:(\d+)|-p\s+(\d+)", args_str, re.IGNORECASE
            )
            if port_match:
                job_port = int(
                    port_match.group(1) or port_match.group(2) or port_match.group(3)
                )
                if job_port == port:
                    service_jobs.append(j)

        # Determine exploitation status with keyword detection
        exploited = False
        manually_attempted = False

        # Check manual exploit attempts first (from exploit_attempts table)
        for attempt in service_exploit_attempts:
            attempt_status = attempt.get("status")
            if attempt_status == "success":
                exploited = True
                break
            elif attempt_status in ("attempted", "failed"):
                manually_attempted = True

        # Check for credentials (definitive exploitation)
        if not exploited and service_creds:
            exploited = True
        # Check for exploitation indicators in findings
        elif not exploited and service_findings:
            # Keywords that indicate successful exploitation
            exploitation_keywords = [
                "exploited",
                "breach",
                "dumped",
                "exfiltrated",
                "enumerated",
                "extracted",
                "compromised",
            ]

            for finding in service_findings:
                title = finding.get("title", "").lower()
                severity = finding.get("severity", "")

                # Check for exploitation keywords in title
                if any(keyword in title for keyword in exploitation_keywords):
                    exploited = True
                    break
                # Critical SQLi, RCE, or data breach findings are exploitation
                elif severity == "critical" and any(
                    vuln in title
                    for vuln in [
                        "sql injection",
                        "rce",
                        "command injection",
                        "data breach",
                    ]
                ):
                    exploited = True
                    break

        # Set final status
        # Note: service_findings alone does NOT mean "attempted" - those are just detected vulns
        # Only explicit exploit attempts or exploit tool jobs count as "attempted"
        if exploited:
            status = "exploited"
        elif manually_attempted or service_jobs:
            status = "attempted"
        else:
            status = "not_tried"

        return {
            "port": port,
            "service": service_name,
            "version": version,
            "status": status,
            "credentials": len(service_creds),
            "findings": len(service_findings),
            "jobs_run": len(service_jobs),
            "suggested_actions": self._suggest_actions(service_name, version, status),
        }

    def _suggest_actions(self, service: str, version: str, status: str) -> List[str]:
        """Suggest next actions for a service."""
        actions = []

        if status == "not_tried":
            # Suggest initial enumeration
            service_lower = service.lower()
            if "ssh" in service_lower or "telnet" in service_lower:
                actions.append("Enumerate users")
                actions.append("Brute force")
            elif (
                "mysql" in service_lower
                or "postgresql" in service_lower
                or "mssql" in service_lower
            ):
                actions.append("Try default creds")
                actions.append("Enumerate databases")
            elif "http" in service_lower:
                actions.append("Scan vulnerabilities")
                actions.append("Directory brute force")
            elif "smb" in service_lower or "netbios" in service_lower:
                actions.append("Enumerate shares")
                actions.append("Enumerate users")
            elif "ftp" in service_lower:
                actions.append("Anonymous login")
                actions.append("Brute force")
            else:
                actions.append("Enumerate service")

        elif status == "attempted":
            # Suggest next-level actions based on service type
            service_lower = service.lower()
            if (
                "ssh" in service_lower
                or "telnet" in service_lower
                or "login" in service_lower
            ):
                actions.append("Try different wordlist")
                actions.append("Check for known exploits")
            elif (
                "mysql" in service_lower
                or "postgresql" in service_lower
                or "mssql" in service_lower
            ):
                actions.append("Try SQL injection")
                actions.append("Check for CVEs")
            elif "http" in service_lower or "https" in service_lower:
                actions.append("Run Nuclei/Gobuster")
                actions.append("Check web app vulns")
            elif (
                "smb" in service_lower
                or "netbios" in service_lower
                or "microsoft-ds" in service_lower
            ):
                actions.append("Try null session")
                actions.append("Check EternalBlue")
            elif "ftp" in service_lower:
                actions.append("Check for backdoor")
                actions.append("Try credential stuffing")
            elif "rpc" in service_lower or "nfs" in service_lower:
                actions.append("Enumerate exports")
                actions.append("Check mount options")
            elif "vnc" in service_lower:
                actions.append("Try known passwords")
                actions.append("Check for no-auth")
            elif "domain" in service_lower or "dns" in service_lower:
                actions.append("Zone transfer")
                actions.append("Subdomain enum")
            elif "smtp" in service_lower or "mail" in service_lower:
                actions.append("User enumeration")
                actions.append("Check open relay")
            elif "irc" in service_lower:
                actions.append("Check for UnrealIRCd backdoor")
                actions.append("Connect and enum")
            elif "java" in service_lower or "rmi" in service_lower:
                actions.append("Check Java deserialization")
                actions.append("RMI registry enum")
            elif "ajp" in service_lower or "tomcat" in service_lower:
                actions.append("Ghostcat (CVE-2020-1938)")
                actions.append("Manager console access")
            elif (
                "exec" in service_lower
                or "shell" in service_lower
                or "bindshell" in service_lower
            ):
                actions.append("Direct connection attempt")
                actions.append("Check authentication")
            else:
                actions.append("Research service vulns")
                actions.append("Manual enumeration")

        elif status == "exploited":
            actions.append("Escalate privileges")
            actions.append("Dump credentials")

        return actions

    def _has_activity(
        self, host: Dict, findings: List[Dict], credentials: List[Dict]
    ) -> bool:
        """Check if host has any activity (services, findings, credentials)."""
        host_id = host.get("id")
        host_ip = host.get("ip") or host.get("ip_address")

        # Check for services
        services = self.hosts_mgr.get_host_services(host_id) if host_id else []
        if services:
            return True

        # Check for findings (passed in, no DB query)
        host_findings = [f for f in findings if f.get("ip_address") == host_ip]
        if host_findings:
            return True

        # Check for credentials (passed in, no DB query)
        host_creds = [c for c in credentials if c.get("ip_address") == host_ip]
        if host_creds:
            return True

        return False

    def _generate_overview(
        self, host_surfaces: List[Dict], findings: List[Dict], credentials: List[Dict]
    ) -> Dict:
        """Generate overview statistics."""
        total_services = sum(len(h.get("services", [])) for h in host_surfaces)
        exploited_services = sum(
            h.get("exploitation_progress", {}).get("exploited", 0)
            for h in host_surfaces
        )
        critical_findings = [f for f in findings if f.get("severity") == "critical"]

        # Wazuh vulnerability totals
        total_wazuh_vulns = sum(h.get("wazuh_vulns", 0) for h in host_surfaces)
        wazuh_critical = sum(h.get("wazuh_critical", 0) for h in host_surfaces)

        return {
            "total_hosts": len(host_surfaces),
            "total_services": total_services,
            "exploited_services": exploited_services,
            "exploitation_percentage": round(
                (
                    (exploited_services / total_services * 100)
                    if total_services > 0
                    else 0
                ),
                1,
            ),
            "credentials_found": len(credentials),
            "critical_findings": len(critical_findings),
            "wazuh_vulns": total_wazuh_vulns,
            "wazuh_critical": wazuh_critical,
        }

    def _generate_recommendations(self, host_surfaces: List[Dict]) -> List[Dict]:
        """Generate prioritized recommendations."""
        recommendations = []

        for host_surface in host_surfaces[:3]:  # Top 3 hosts
            for service_status in host_surface.get(
                "services", []
            ):  # Changed from 'service_statuses'
                if (
                    service_status["status"] == "not_tried"
                    and service_status["suggested_actions"]
                ):
                    # High priority: Untried services on top hosts
                    recommendations.append(
                        {
                            "priority": "high",
                            "host": host_surface["host"],
                            "port": service_status["port"],
                            "service": service_status["service"],
                            "action": service_status["suggested_actions"][0],
                            "reason": f"Untried service on high-value target",
                        }
                    )

                elif (
                    service_status["status"] == "attempted"
                    and len(recommendations) < 10
                ):
                    # Medium priority: Retry failed attempts
                    recommendations.append(
                        {
                            "priority": "medium",
                            "host": host_surface["host"],
                            "port": service_status["port"],
                            "service": service_status["service"],
                            "action": "Retry exploitation",
                            "reason": f"Previous attempt incomplete",
                        }
                    )

        # Sort by priority and limit to top 5
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order[x["priority"]])
        return recommendations[:5]
