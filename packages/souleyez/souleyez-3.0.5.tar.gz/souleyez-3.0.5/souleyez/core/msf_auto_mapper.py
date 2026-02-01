#!/usr/bin/env python3
"""
souleyez.core.msf_auto_mapper - Automatically map engagement data to MSF modules
"""

import re
from typing import Dict, List

from souleyez.core.msf_integration import MSFModuleSelector, VersionMatcher


class MSFAutoMapper:
    """Automatically map engagement data to MSF modules."""

    def __init__(self, engagement_id: int):
        self.engagement_id = engagement_id
        self.module_selector = MSFModuleSelector()
        self.version_matcher = VersionMatcher()

    def map_services_to_modules(self) -> Dict[int, List[Dict]]:
        """
        Map all services in engagement to applicable MSF modules.

        Returns:
            Dictionary mapping service_id to list of recommended modules
        """
        try:
            from souleyez.storage.hosts import HostManager

            hm = HostManager()
            service_map = {}

            # Get all hosts in engagement
            hosts = hm.list_hosts(self.engagement_id)

            for host in hosts:
                # Get services for this host
                services = hm.get_host_services(host["id"])

                for service in services:
                    service_id = service["id"]
                    service_name = service.get("service_name", "").lower()
                    version = service.get("service_version", "")

                    # Get recommendations
                    recommendations = (
                        self.module_selector.get_recommendations_for_service(
                            service=service_name,
                            version=version,
                            engagement_id=self.engagement_id,
                            include_cve_matches=True,
                            risk_levels=["safe", "noisy", "moderate", "dangerous"],
                        )
                    )

                    # Only store services with actual recommendations
                    if recommendations:
                        service_map[service_id] = recommendations[:10]

            return service_map
        except Exception as e:
            return {}

    def map_findings_to_exploits(self) -> Dict[int, List[Dict]]:
        """
        Map all findings to exploitable MSF modules.

        Returns:
            Dictionary mapping finding_id to list of exploit modules
        """
        try:
            from souleyez.storage.findings import FindingsManager

            fm = FindingsManager()
            finding_map = {}

            findings = fm.list_findings(self.engagement_id)

            for finding in findings:
                finding_id = finding["id"]

                # Extract CVEs from finding
                cves = self._extract_cves_from_finding(finding)

                # Match to exploits
                exploits = self.module_selector.match_vulnerability_to_exploit(
                    vuln_title=finding.get("title", ""),
                    vuln_desc=finding.get("description", ""),
                    cves=cves,
                )

                if exploits:
                    finding_map[finding_id] = exploits

            return finding_map
        except Exception as e:
            return {}

    def _extract_cves_from_finding(self, finding: Dict) -> List[str]:
        """Extract CVE IDs from finding title/description."""
        text = finding.get("title", "") + " " + finding.get("description", "")
        cve_pattern = r"CVE-\d{4}-\d{4,7}"

        return re.findall(cve_pattern, text, re.IGNORECASE)

    def generate_attack_surface_report(self) -> Dict:
        """
        Generate comprehensive attack surface report with MSF modules.

        Returns:
            Dictionary containing attack surface analysis
        """
        try:
            from souleyez.storage.hosts import HostManager

            hm = HostManager()
            service_map = self.map_services_to_modules()
            finding_map = self.map_findings_to_exploits()

            # Count services
            total_services = len(service_map)
            exploitable_services = sum(
                1
                for modules in service_map.values()
                if any(m.get("category") == "exploit" for m in modules)
            )

            # Identify critical targets
            critical_targets = []

            for service_id, modules in service_map.items():
                # Find high-value targets (exploits with high scores)
                exploits = [m for m in modules if m.get("category") == "exploit"]
                high_score_exploits = [e for e in exploits if e.get("score", 0) >= 80]

                if high_score_exploits:
                    try:
                        service = hm.get_service(service_id)
                        if service:
                            host = hm.get_host(service.get("host_id"))
                            critical_targets.append(
                                {
                                    "host": host.get("ip_address", "Unknown"),
                                    "service": service.get("service_name", "Unknown"),
                                    "port": service.get("port", 0),
                                    "modules": [
                                        e.get("path") for e in high_score_exploits
                                    ],
                                    "success_probability": "high",
                                    "impact": "critical",
                                    "top_score": max(
                                        e.get("score", 0) for e in high_score_exploits
                                    ),
                                }
                            )
                    except:
                        pass

            # Sort critical targets by score
            critical_targets.sort(key=lambda x: x.get("top_score", 0), reverse=True)

            report = {
                "total_services": total_services,
                "exploitable_services": exploitable_services,
                "critical_targets": critical_targets[:10],  # Top 10
                "total_findings_with_exploits": len(finding_map),
                "recommended_attack_path": self._generate_attack_path(critical_targets),
            }

            return report
        except Exception as e:
            return {
                "total_services": 0,
                "exploitable_services": 0,
                "critical_targets": [],
                "total_findings_with_exploits": 0,
                "recommended_attack_path": [],
            }

    def _generate_attack_path(self, critical_targets: List[Dict]) -> List[str]:
        """Generate recommended attack path."""
        if not critical_targets:
            return ["No critical targets identified"]

        path = []

        # Start with highest priority target
        if critical_targets:
            target = critical_targets[0]
            path.append(
                f"Step 1: Exploit {target['service']} on {target['host']} "
                f"using {target['modules'][0]}"
            )

        # Add post-exploitation step
        if len(critical_targets) >= 1:
            path.append(
                "Step 2: Dump credentials using hashdump or credential_collector"
            )

        # Add lateral movement if multiple targets
        if len(critical_targets) > 1:
            path.append("Step 3: Use credentials for lateral movement to other hosts")

        return path

    def get_service_mappings(self) -> List[Dict]:
        """
        Get service mappings with full context for display.

        Returns:
            List of dicts with ip_address, port, service, modules
        """
        try:
            from souleyez.storage.hosts import HostManager

            hm = HostManager()
            results = []
            hosts = hm.list_hosts(self.engagement_id)

            for host in hosts:
                services = hm.get_host_services(host["id"])

                for service in services:
                    service_name = service.get("service_name", "").lower()
                    version = service.get("service_version", "")

                    recommendations = (
                        self.module_selector.get_recommendations_for_service(
                            service=service_name,
                            version=version,
                            engagement_id=self.engagement_id,
                            include_cve_matches=True,
                            risk_levels=["safe", "noisy", "moderate", "dangerous"],
                        )
                    )

                    if recommendations:
                        results.append(
                            {
                                "ip_address": host.get("ip_address", "?"),
                                "port": service.get("port", "?"),
                                "service": service_name or "unknown",
                                "version": version,
                                "modules": recommendations[:5],
                            }
                        )

            return results
        except Exception:
            return []

    def get_finding_mappings(self) -> List[Dict]:
        """
        Get finding mappings with full context for display.

        Returns:
            List of dicts with title, severity, exploits
        """
        try:
            from souleyez.storage.findings import FindingsManager

            fm = FindingsManager()
            results = []
            findings = fm.list_findings(self.engagement_id)

            for finding in findings:
                cves = self._extract_cves_from_finding(finding)

                exploits = self.module_selector.match_vulnerability_to_exploit(
                    vuln_title=finding.get("title", ""),
                    vuln_desc=finding.get("description", ""),
                    cves=cves,
                )

                if exploits:
                    results.append(
                        {
                            "title": finding.get("title", "?"),
                            "severity": finding.get("severity", "unknown"),
                            "cves": cves,
                            "exploits": exploits[:5],
                        }
                    )

            return results
        except Exception:
            return []

    def get_service_exploitation_suggestions(self, service_id: int) -> Dict:
        """
        Get detailed exploitation suggestions for a specific service.

        Args:
            service_id: Service ID

        Returns:
            Dictionary with exploitation suggestions
        """
        try:
            from souleyez.storage.hosts import HostManager

            hm = HostManager()
            service = hm.get_service(service_id)

            if not service:
                return {}

            host = hm.get_host(service.get("host_id"))
            service_name = service.get("service_name", "")
            version = service.get("service_version", "")

            # Get recommendations
            recommendations = self.module_selector.get_recommendations_for_service(
                service=service_name,
                version=version,
                engagement_id=self.engagement_id,
                include_cve_matches=True,
                risk_levels=["safe", "noisy", "moderate", "dangerous"],
            )

            # Separate scanners and exploits
            scanners = [r for r in recommendations if r.get("category") == "scanner"]
            exploits = [r for r in recommendations if r.get("category") == "exploit"]

            return {
                "host": host.get("ip_address", "Unknown"),
                "service": service_name,
                "version": version,
                "port": service.get("port", 0),
                "recommended_scanners": scanners[:5],
                "recommended_exploits": exploits[:5],
                "exploitation_complexity": (
                    "low"
                    if exploits and exploits[0].get("score", 0) >= 80
                    else "medium"
                ),
            }
        except Exception as e:
            return {}
