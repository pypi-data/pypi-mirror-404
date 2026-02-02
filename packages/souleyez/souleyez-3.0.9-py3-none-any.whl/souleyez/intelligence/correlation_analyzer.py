#!/usr/bin/env python3
"""
Correlation analyzer for tracking exploitation status.
Links services, findings, jobs, credentials, and evidence together.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from souleyez.engine.background import get_job, list_jobs
from souleyez.intelligence.target_parser import TargetParser
from souleyez.storage.credentials import CredentialsManager
from souleyez.storage.findings import FindingsManager
from souleyez.storage.hosts import HostManager


class CorrelationAnalyzer:
    """Analyze relationships between services, findings, jobs, and credentials."""

    def __init__(self):
        self.hosts_mgr = HostManager()
        self.findings_mgr = FindingsManager()
        self.creds_mgr = CredentialsManager()
        self.target_parser = TargetParser()

    def analyze_service(
        self, engagement_id: int, host_id: int, port: int, protocol: str = "tcp"
    ) -> Dict:
        """
        Analyze exploitation status for a single service.

        Returns:
            {
                'service': {
                    'host_id': 123,
                    'host_ip': '10.0.0.5',
                    'port': 3306,
                    'protocol': 'tcp',
                    'service_name': 'mysql',
                    'version': 'MySQL 5.0.51a'
                },
                'findings': [...],
                'jobs': [...],
                'credentials': [...],
                'evidence': [...],
                'exploitation_status': 'EXPLOITED',  # NOT_ATTEMPTED | ATTEMPTED | EXPLOITED
                'access_level': 'user',
                'last_attempt': '2025-11-05T16:30:00Z',
                'success_rate': 0.5,
                'recommendations': [...]
            }
        """
        # Get host info
        host = self.hosts_mgr.get_host(host_id)
        if not host:
            return {}

        # Get service info
        services = self.hosts_mgr.get_host_services(host_id)
        service_info = None
        for svc in services:
            if svc["port"] == port and svc["protocol"] == protocol:
                service_info = svc
                break

        if not service_info:
            # Service not in database - create minimal info
            service_info = {
                "host_id": host_id,
                "port": port,
                "protocol": protocol,
                "service_name": self.target_parser.infer_service_from_port(port)
                or "unknown",
                "version": None,
            }

        result = {
            "service": {
                "host_id": host_id,
                "host_ip": host["ip_address"],
                "hostname": host.get("hostname"),
                "port": port,
                "protocol": protocol,
                "service_name": service_info.get("service_name", "unknown"),
                "version": service_info.get("version"),
                "state": service_info.get("state", "open"),
            }
        }

        # Find related findings
        findings = self._find_findings_for_service(
            engagement_id, host["ip_address"], port
        )
        result["findings"] = findings

        # Find related jobs
        jobs = self._link_jobs_to_service(
            engagement_id, host["ip_address"], port, service_info.get("service_name")
        )
        result["jobs"] = jobs

        # Find related credentials
        credentials = self._find_credentials_for_service(
            engagement_id, host["ip_address"], port, service_info.get("service_name")
        )
        result["credentials"] = credentials

        # Collect evidence paths
        evidence = []
        for job in jobs:
            # Log file
            log_path = Path.home() / ".souleyez" / "data" / "jobs" / f"{job['id']}.log"
            if log_path.exists():
                evidence.append(
                    {"type": "log", "path": str(log_path), "job_id": job["id"]}
                )

            # Output file (if exists)
            output_path = (
                Path.home() / ".souleyez" / "data" / "jobs" / f"{job['id']}_output.txt"
            )
            if output_path.exists():
                evidence.append(
                    {"type": "output", "path": str(output_path), "job_id": job["id"]}
                )

        result["evidence"] = evidence

        # Determine exploitation status
        result["exploitation_status"] = self._determine_exploitation_status(
            jobs, credentials, host.get("access_level", "none")
        )

        # Access level from host
        result["access_level"] = host.get("access_level", "none")

        # Calculate last attempt time
        if jobs:
            last_job = max(jobs, key=lambda j: j.get("created_at", ""))
            result["last_attempt"] = last_job.get("created_at")
        else:
            result["last_attempt"] = None

        # Calculate success rate
        result["success_rate"] = self._calculate_success_rate(jobs, credentials)

        # Generate recommendations
        result["recommendations"] = self._generate_recommendations(
            result["service"], result["exploitation_status"], credentials, findings
        )

        return result

    def analyze_host(self, engagement_id: int, host_id: int) -> Dict:
        """
        Analyze all services for a host.

        Returns:
            {
                'host': {...},
                'services': [<analyze_service results>],
                'summary': {
                    'total_services': 5,
                    'exploited': 2,
                    'attempted': 2,
                    'not_attempted': 1,
                    'credentials_found': 3,
                    'access_level': 'user'
                }
            }
        """
        host = self.hosts_mgr.get_host(host_id)
        if not host:
            return {}

        # Get all services
        services = self.hosts_mgr.get_host_services(host_id)

        # Analyze each service
        service_analyses = []
        for svc in services:
            analysis = self.analyze_service(
                engagement_id, host_id, svc["port"], svc.get("protocol", "tcp")
            )
            service_analyses.append(analysis)

        # Calculate summary stats
        summary = {
            "total_services": len(service_analyses),
            "exploited": sum(
                1 for s in service_analyses if s["exploitation_status"] == "EXPLOITED"
            ),
            "attempted": sum(
                1 for s in service_analyses if s["exploitation_status"] == "ATTEMPTED"
            ),
            "not_attempted": sum(
                1
                for s in service_analyses
                if s["exploitation_status"] == "NOT_ATTEMPTED"
            ),
            "credentials_found": sum(len(s["credentials"]) for s in service_analyses),
            "access_level": host.get("access_level", "none"),
        }

        return {"host": host, "services": service_analyses, "summary": summary}

    def analyze_engagement(self, engagement_id: int) -> Dict:
        """
        Analyze complete engagement.

        Returns:
            {
                'hosts': [<analyze_host results>],
                'summary': {
                    'total_hosts': 10,
                    'total_services': 45,
                    'exploited_services': 12,
                    'attempted_services': 20,
                    'not_attempted_services': 13,
                    'total_credentials': 8,
                    'compromised_hosts': 3
                },
                'gaps': [...]
            }
        """
        # Get all hosts for engagement
        hosts = self.hosts_mgr.list_hosts(engagement_id)

        # Analyze each host
        host_analyses = []
        for host in hosts:
            analysis = self.analyze_host(engagement_id, host["id"])
            if analysis:
                host_analyses.append(analysis)

        # Calculate engagement-wide summary
        summary = {
            "total_hosts": len(host_analyses),
            "total_services": sum(
                h["summary"]["total_services"] for h in host_analyses
            ),
            "exploited_services": sum(h["summary"]["exploited"] for h in host_analyses),
            "attempted_services": sum(h["summary"]["attempted"] for h in host_analyses),
            "not_attempted_services": sum(
                h["summary"]["not_attempted"] for h in host_analyses
            ),
            "total_credentials": sum(
                h["summary"]["credentials_found"] for h in host_analyses
            ),
            "compromised_hosts": sum(
                1 for h in host_analyses if h["summary"]["access_level"] != "none"
            ),
        }

        # Identify gaps
        gaps = self._identify_gaps(host_analyses)

        return {"hosts": host_analyses, "summary": summary, "gaps": gaps}

    def _link_jobs_to_service(
        self, engagement_id: int, host_ip: str, port: int, service_name: str = None
    ) -> List[Dict]:
        """
        Find all jobs that targeted a specific service.

        Logic:
        1. Get all jobs for engagement
        2. For each job, parse target
        3. Match: host IP + port OR host IP + service name
        4. Return matching jobs with enriched info
        """
        all_jobs = [j for j in list_jobs() if j.get("engagement_id") == engagement_id]
        matching_jobs = []

        for job in all_jobs:
            try:
                # Parse job args (handle both string and already-parsed list)
                args = job.get("args")
                if args:
                    if isinstance(args, str):
                        args = json.loads(args)
                else:
                    args = None

                # Parse job target
                target_info = self.target_parser.parse_target(
                    job["tool"], job["target"], args
                )

                # Check if this job targets our service
                if target_info.get("host") != host_ip:
                    continue

                # Match by port
                if target_info.get("port") == port:
                    matching_jobs.append(self._enrich_job_info(job))
                    continue

                # Match by ports list (e.g., Nmap scan)
                if port in target_info.get("ports", []):
                    matching_jobs.append(self._enrich_job_info(job))
                    continue

                # Match by service name
                if service_name and target_info.get("service") == service_name:
                    matching_jobs.append(self._enrich_job_info(job))
                    continue

            except Exception:
                # Skip jobs we can't parse
                continue

        # Sort by creation time
        matching_jobs.sort(key=lambda j: j.get("created_at", ""))

        return matching_jobs

    def _enrich_job_info(self, job: Dict) -> Dict:
        """Add enriched information to job dict."""
        enriched = job.copy()

        # Determine if job was successful
        enriched["success"] = self._is_job_successful(job)

        # Parse args for display
        if job.get("args"):
            try:
                enriched["parsed_args"] = json.loads(job["args"])
            except:
                enriched["parsed_args"] = job["args"]

        return enriched

    def _is_job_successful(self, job: Dict) -> bool:
        """
        Determine if a job was successful.

        Heuristics:
        - Status = 'done' (baseline)
        - Has parse_result with valuable data
        - Credentials found for this job
        """
        if job["status"] != "done":
            return False

        # Check parse_result
        if job.get("parse_result"):
            try:
                result = json.loads(job["parse_result"])

                # Check for credentials
                if result.get("credentials"):
                    return True

                # Check for vulnerabilities
                if result.get("vulnerabilities"):
                    return True

                # Check for exploits
                if result.get("exploits"):
                    return True

            except:
                pass

        # Check if credentials exist for this job
        creds = self.creds_mgr.list_credentials_for_engagement(job["engagement_id"])
        for cred in creds:
            if cred.get("source_job_id") == job["id"]:
                return True

        return False

    def _find_findings_for_service(
        self, engagement_id: int, host_ip: str, port: int
    ) -> List[Dict]:
        """Find all findings related to a service."""
        all_findings = self.findings_mgr.list_findings(engagement_id)

        matching = []
        for finding in all_findings:
            # Match by ip_address from JOIN with hosts table
            if finding.get("ip_address") != host_ip:
                continue

            # Match by port field or check if port mentioned in affected_service
            if finding.get("port") == port:
                matching.append(finding)
                continue

            # Also check affected_service text field for legacy findings
            affected_svc = finding.get("affected_service", "")
            if affected_svc and (
                str(port) in affected_svc or f":{port}" in affected_svc
            ):
                matching.append(finding)

        return matching

    def _find_credentials_for_service(
        self, engagement_id: int, host_ip: str, port: int, service_name: str = None
    ) -> List[Dict]:
        """Find credentials related to a service."""
        all_creds = self.creds_mgr.list_credentials_for_engagement(engagement_id)

        matching = []
        for cred in all_creds:
            # Match by host (use ip_address from JOIN, not 'host')
            if cred.get("ip_address") != host_ip:
                continue

            # Match by port (if port is set on credential)
            if cred.get("port") == port:
                matching.append(cred)
                continue

            # Match by service name
            if service_name and cred.get("service") == service_name:
                matching.append(cred)
                continue

            # For web services, match credentials without specific port set
            # (e.g., SQLMap credentials for 'web' service)
            cred_service = cred.get("service", "").lower()
            if cred_service == "web":
                # Match if service_name is a web service OR if port is 80/443/8080/8443
                is_web_service = service_name and service_name.lower() in [
                    "http",
                    "https",
                    "web",
                ]
                is_web_port = port in [80, 443, 8080, 8443, 8000, 8888]

                if (is_web_service or is_web_port) and cred.get("port") is None:
                    matching.append(cred)
                    continue

        return matching

    def _determine_exploitation_status(
        self, jobs: List, credentials: List, access_level: str
    ) -> str:
        """
        Determine exploitation status based on evidence.

        Logic:
        - If no jobs: 'NOT_ATTEMPTED'
        - If jobs but no creds and access_level='none': 'ATTEMPTED'
        - If credentials found OR access_level != 'none': 'EXPLOITED'
        """
        if not jobs:
            return "NOT_ATTEMPTED"

        # Check for successful exploitation
        if credentials or access_level != "none":
            return "EXPLOITED"

        # Jobs exist but no success
        return "ATTEMPTED"

    def _calculate_success_rate(self, jobs: List, credentials: List) -> float:
        """Calculate success rate of exploitation attempts."""
        if not jobs:
            return 0.0

        successful_jobs = sum(1 for j in jobs if j.get("success", False))

        return successful_jobs / len(jobs)

    def _generate_recommendations(
        self, service: Dict, status: str, credentials: List, findings: List
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        service_name = (service.get("service_name") or "").lower()
        port = service.get("port")

        if status == "NOT_ATTEMPTED":
            # Suggest initial attack vectors
            if service_name == "ssh" or port == 22:
                recommendations.append("Try ssh_login with common credentials")
                recommendations.append("Check for weak SSH configurations")

            elif service_name == "ftp" or port == 21:
                recommendations.append("Try anonymous FTP login")
                recommendations.append("Check for vsftpd backdoor (version 2.3.4)")

            elif service_name in ["mysql", "mariadb"] or port == 3306:
                recommendations.append("Try mysql_login brute force")
                recommendations.append("Check for CVE-2009-2446 (yaSSL overflow)")

            elif service_name == "smb" or port in [139, 445]:
                recommendations.append("Try SMB null session enumeration")
                recommendations.append("Check for EternalBlue vulnerability")

            elif service_name == "http" or port in [80, 443, 8080, 8443]:
                recommendations.append("Run Nuclei web vulnerability scan")
                recommendations.append("Try directory brute-forcing with Gobuster")

            else:
                recommendations.append(f"Research common exploits for {service_name}")
                recommendations.append(f"Try brute-forcing port {port}")

        elif status == "ATTEMPTED":
            # Suggest retrying with different tactics
            recommendations.append("Retry with expanded wordlist")
            recommendations.append("Try different exploitation modules")

            if service_name in ["ssh", "ftp", "mysql", "smb"]:
                recommendations.append("Attempt password spraying")

        elif status == "EXPLOITED":
            # Suggest post-exploitation
            if credentials:
                recommendations.append("Attempt privilege escalation")
                recommendations.append("Enumerate for additional access")

            recommendations.append("Collect evidence and document access")

        return recommendations

    def _identify_gaps(self, host_analyses: List[Dict]) -> List[Dict]:
        """
        Identify services that haven't been exploited.

        Returns list of gaps with suggested actions.
        """
        gaps = []

        for host_analysis in host_analyses:
            host = host_analysis["host"]

            for service_analysis in host_analysis["services"]:
                if service_analysis["exploitation_status"] == "NOT_ATTEMPTED":
                    service = service_analysis["service"]
                    severity = self._assess_gap_severity(service)

                    gap = {
                        "host": service["host_ip"],
                        "hostname": service.get("hostname"),
                        "port": service["port"],
                        "service": service["service_name"],
                        "version": service.get("version"),
                        "reason": "Service discovered but no exploitation attempts",
                        "severity": severity,
                        "priority_score": self._calculate_priority_score(
                            service, severity
                        ),
                        "suggested_actions": service_analysis["recommendations"],
                    }

                    gaps.append(gap)

        return gaps

    def _assess_gap_severity(self, service: Dict) -> str:
        """Assess severity of an exploitation gap."""
        service_name = (service.get("service_name") or "").lower()
        port = service.get("port")

        # Critical services
        if service_name in ["mysql", "postgres", "mssql", "mongodb", "redis"]:
            return "critical"

        if port in [3306, 5432, 1433, 27017, 6379]:
            return "critical"

        # High-value services
        if service_name in ["ssh", "rdp", "smb", "ftp"]:
            return "high"

        if port in [21, 22, 139, 445, 3389]:
            return "high"

        # Medium-value services
        if service_name in ["http", "https", "smtp", "imap", "pop3"]:
            return "medium"

        # Low-value
        return "low"

    def _calculate_priority_score(self, service: Dict, severity: str) -> int:
        """
        Calculate priority score for a service (0-100).
        Higher scores = higher priority to exploit.
        """
        # Base scores by severity
        severity_scores = {"critical": 90, "high": 70, "medium": 50, "low": 30}

        score = severity_scores.get(severity, 30)

        # Bonus for known vulnerable versions
        version = service.get("version") or ""
        if version and any(
            vuln in version.lower()
            for vuln in ["vsftpd 2.3.4", "proftpd 1.3.3", "unrealircd"]
        ):
            score += 10

        # Bonus for services commonly with weak auth
        service_name = service.get("service_name") or ""
        if service_name and service_name.lower() in [
            "ftp",
            "telnet",
            "mysql",
            "postgres",
            "smb",
        ]:
            score += 5

        return min(score, 100)
