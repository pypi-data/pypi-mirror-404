#!/usr/bin/env python3
"""
souleyez.core.msf_chain_engine - Orchestrate progressive MSF attack chains
"""

from typing import Dict, List

from souleyez.core.msf_auto_mapper import MSFAutoMapper
from souleyez.core.msf_integration import MSFModuleSelector, MSFResourceGenerator


class MSFChainEngine:
    """Orchestrate progressive MSF attack chains."""

    def __init__(self, engagement_id: int):
        self.engagement_id = engagement_id
        self.auto_mapper = MSFAutoMapper(engagement_id)
        self.resource_gen = MSFResourceGenerator()
        self.module_selector = MSFModuleSelector()

    def build_attack_chain(
        self,
        target_hosts: List[int],
        objectives: List[str] = None,
        risk_tolerance: str = "moderate",
    ) -> Dict:
        """
        Build progressive attack chain.

        Args:
            target_hosts: List of host IDs
            objectives: List of objectives ['recon', 'exploit', 'escalate', 'pivot', 'persist']
            risk_tolerance: 'safe', 'moderate', or 'aggressive'

        Returns:
            Chain definition with phases and modules
        """
        if objectives is None:
            objectives = ["recon", "exploit", "escalate"]

        # Map risk tolerance to risk levels
        risk_map = {
            "safe": ["safe"],
            "moderate": ["safe", "noisy", "moderate"],
            "aggressive": ["safe", "noisy", "moderate", "dangerous"],
        }
        risk_levels = risk_map.get(risk_tolerance, ["safe", "noisy"])

        chain = {
            "chain_id": f"attack_chain_{self.engagement_id}",
            "engagement_id": self.engagement_id,
            "target_hosts": target_hosts,
            "objectives": objectives,
            "risk_tolerance": risk_tolerance,
            "phases": [],
        }

        # Build phases based on objectives
        if "recon" in objectives:
            chain["phases"].append(self._build_recon_phase(target_hosts))

        if "exploit" in objectives:
            chain["phases"].append(
                self._build_exploitation_phase(target_hosts, risk_levels)
            )

        if "escalate" in objectives or "pivot" in objectives or "persist" in objectives:
            post_objectives = []
            if "escalate" in objectives:
                post_objectives.append("escalate")
            if "pivot" in objectives:
                post_objectives.append("pivot")
            if "persist" in objectives:
                post_objectives.append("persist")

            chain["phases"].append(self._build_post_exploitation_phase(post_objectives))

        return chain

    def _build_recon_phase(self, target_hosts: List[int]) -> Dict:
        """Build reconnaissance phase."""
        try:
            from souleyez.storage.hosts import HostManager

            hm = HostManager()

            modules = []

            for host_id in target_hosts:
                services = hm.get_host_services(host_id)

                for service in services:
                    service_name = service.get("service_name", "").lower()

                    # Get version scanners
                    recommendations = self.module_selector.get_recommendations(
                        service=service_name, include_risk=["safe"]
                    )

                    # Filter to version scanners
                    scanners = [
                        r
                        for r in recommendations
                        if "version" in r.get("name", "").lower()
                    ]

                    for scanner in scanners:
                        modules.append(
                            {
                                "module": scanner.get("path"),
                                "target_host": hm.get_host(host_id).get("ip_address"),
                                "target_service": service_name,
                                "risk": "safe",
                            }
                        )

            return {
                "name": "reconnaissance",
                "modules": modules,
                "auto_advance": True,
                "success_criteria": "all_services_fingerprinted",
                "expected_duration": f"{len(modules) * 30} seconds",
            }
        except:
            return {
                "name": "reconnaissance",
                "modules": [],
                "auto_advance": True,
                "success_criteria": "all_services_fingerprinted",
            }

    def _build_exploitation_phase(
        self, target_hosts: List[int], risk_levels: List[str]
    ) -> Dict:
        """Build exploitation phase with ranked targets."""
        try:
            from souleyez.storage.hosts import HostManager

            hm = HostManager()

            exploits = []

            for host_id in target_hosts:
                services = hm.get_host_services(host_id)

                for service in services:
                    service_name = service.get("service_name", "")
                    version = service.get("service_version", "")

                    # Get exploit recommendations
                    recommendations = (
                        self.module_selector.get_recommendations_for_service(
                            service=service_name,
                            version=version,
                            engagement_id=self.engagement_id,
                            risk_levels=risk_levels,
                            include_cve_matches=True,
                        )
                    )

                    # Filter to exploits only
                    exploit_mods = [
                        r for r in recommendations if r.get("category") == "exploit"
                    ]

                    for exploit in exploit_mods:
                        exploits.append(
                            {
                                "module": exploit.get("path"),
                                "target_host": hm.get_host(host_id).get("ip_address"),
                                "target_service": service_name,
                                "score": exploit.get("score", 0),
                                "cves": exploit.get("cve", []),
                                "reliability": exploit.get("reliability", "unknown"),
                                "risk": exploit.get("risk", "moderate"),
                            }
                        )

            # Sort by score descending
            exploits.sort(key=lambda x: x.get("score", 0), reverse=True)

            return {
                "name": "exploitation",
                "modules": exploits[:20],  # Top 20 exploits
                "auto_advance": False,
                "success_criteria": "session_obtained",
                "fallback": "brute_force_authentication",
                "expected_duration": f"{len(exploits[:20]) * 120} seconds",
            }
        except:
            return {
                "name": "exploitation",
                "modules": [],
                "auto_advance": False,
                "success_criteria": "session_obtained",
            }

    def _build_post_exploitation_phase(self, objectives: List[str]) -> Dict:
        """Build post-exploitation phase."""
        modules = []

        # Common post-exploitation modules
        common_modules = [
            {
                "module": "post/multi/recon/local_exploit_suggester",
                "description": "Suggest local privilege escalation exploits",
                "objective": "escalate",
            },
            {
                "module": "post/windows/gather/hashdump",
                "description": "Dump password hashes (Windows)",
                "objective": "escalate",
            },
            {
                "module": "post/linux/gather/hashdump",
                "description": "Dump password hashes (Linux)",
                "objective": "escalate",
            },
            {
                "module": "post/multi/manage/autoroute",
                "description": "Setup routing for pivoting",
                "objective": "pivot",
            },
            {
                "module": "post/windows/manage/persistence_exe",
                "description": "Install persistent backdoor (Windows)",
                "objective": "persist",
            },
        ]

        # Filter by objectives
        for module in common_modules:
            if module["objective"] in objectives:
                modules.append(module)

        return {
            "name": "post_exploitation",
            "modules": modules,
            "triggers": ["session_obtained"],
            "auto_advance": False,
            "success_criteria": "credentials_dumped or persistence_established",
            "expected_duration": f"{len(modules) * 60} seconds",
        }

    def generate_progressive_chain(self, host_id: int) -> Dict:
        """
        Generate progressive attack chain for a single host.

        Args:
            host_id: Host ID

        Returns:
            Progressive chain definition
        """
        try:
            from souleyez.storage.hosts import HostManager

            hm = HostManager()

            host = hm.get_host(host_id)
            services = hm.get_host_services(host_id)

            chain = {
                "target": host.get("ip_address", "Unknown"),
                "host_id": host_id,
                "phases": [],
            }

            # Phase 1: Reconnaissance
            recon_modules = self._build_recon_phase_for_host(host_id, services)
            chain["phases"].append(
                {
                    "name": "reconnaissance",
                    "modules": recon_modules,
                    "auto_advance": True,
                    "success_criteria": "all_services_fingerprinted",
                }
            )

            # Phase 2: Vulnerability Assessment
            vuln_modules = self._build_vuln_assessment_phase(services)
            chain["phases"].append(
                {
                    "name": "vulnerability_assessment",
                    "modules": vuln_modules,
                    "auto_advance": False,
                    "success_criteria": "vulnerabilities_confirmed",
                }
            )

            # Phase 3: Exploitation
            exploit_modules = self._build_exploitation_phase_for_host(host_id, services)
            chain["phases"].append(
                {
                    "name": "exploitation",
                    "modules": exploit_modules,
                    "auto_advance": False,
                    "success_criteria": "session_obtained",
                    "fallback": "brute_force_authentication",
                }
            )

            # Phase 4: Post-Exploitation
            post_modules = self._build_post_exploitation_phase_for_host(host)
            chain["phases"].append(
                {
                    "name": "post_exploitation",
                    "modules": post_modules,
                    "triggers": ["session_obtained"],
                    "auto_advance": False,
                    "success_criteria": "credentials_dumped",
                }
            )

            return chain
        except Exception as e:
            return {"target": "Unknown", "phases": [], "error": str(e)}

    def _build_recon_phase_for_host(
        self, host_id: int, services: List[Dict]
    ) -> List[Dict]:
        """Build recon modules for a specific host."""
        modules = []

        for service in services:
            service_name = service.get("service_name", "").lower()

            # Get version scanner
            version_module = self._get_version_scanner(service_name)
            if version_module:
                modules.append(
                    {
                        "module": version_module,
                        "target_service": service_name,
                        "risk": "safe",
                    }
                )

        return modules

    def _get_version_scanner(self, service_name: str) -> str:
        """Get version scanner module for service."""
        scanner_map = {
            "ssh": "auxiliary/scanner/ssh/ssh_version",
            "smb": "auxiliary/scanner/smb/smb_version",
            "http": "auxiliary/scanner/http/http_version",
            "https": "auxiliary/scanner/http/http_version",
            "ftp": "auxiliary/scanner/ftp/ftp_version",
            "mysql": "auxiliary/scanner/mysql/mysql_version",
            "postgresql": "auxiliary/scanner/postgres/postgres_version",
            "mssql": "auxiliary/scanner/mssql/mssql_ping",
        }

        return scanner_map.get(service_name)

    def _build_vuln_assessment_phase(self, services: List[Dict]) -> List[Dict]:
        """Build vulnerability assessment modules."""
        modules = []

        for service in services:
            service_name = service.get("service_name", "").lower()

            # Add service-specific vuln scanners
            if service_name == "smb":
                modules.append(
                    {
                        "module": "auxiliary/scanner/smb/smb_ms17_010",
                        "description": "Check for MS17-010 (EternalBlue)",
                        "risk": "safe",
                    }
                )

        return modules

    def _build_exploitation_phase_for_host(
        self, host_id: int, services: List[Dict]
    ) -> List[Dict]:
        """Build exploitation modules for a specific host."""
        exploits = []

        for service in services:
            service_id = service.get("id")
            service_name = service.get("service_name", "")
            version = service.get("service_version", "")

            # Get exploit recommendations
            recommendations = self.module_selector.get_recommendations_for_service(
                service=service_name,
                version=version,
                engagement_id=self.engagement_id,
                include_cve_matches=True,
            )

            # Filter to exploits
            exploit_mods = [
                r for r in recommendations if r.get("category") == "exploit"
            ]

            for exploit in exploit_mods:
                exploits.append(
                    {
                        "module": exploit.get("path"),
                        "score": exploit.get("score", 0),
                        "cves": exploit.get("cve", []),
                        "reliability": exploit.get("reliability", "unknown"),
                    }
                )

        # Sort by score
        exploits.sort(key=lambda x: x.get("score", 0), reverse=True)

        return exploits

    def _build_post_exploitation_phase_for_host(self, host: Dict) -> List[Dict]:
        """Build post-exploitation modules for a specific host."""
        modules = []

        # OS-specific modules
        os_type = host.get("os", "unknown").lower()

        if "windows" in os_type:
            modules.extend(
                [
                    {
                        "module": "post/windows/gather/hashdump",
                        "description": "Dump password hashes",
                    },
                    {
                        "module": "post/windows/gather/enum_patches",
                        "description": "Enumerate installed patches",
                    },
                ]
            )
        elif "linux" in os_type:
            modules.extend(
                [
                    {
                        "module": "post/linux/gather/hashdump",
                        "description": "Dump password hashes",
                    },
                    {
                        "module": "post/linux/gather/enum_system",
                        "description": "Enumerate system information",
                    },
                ]
            )

        # Universal modules
        modules.append(
            {
                "module": "post/multi/recon/local_exploit_suggester",
                "description": "Suggest privilege escalation exploits",
            }
        )

        return modules


class MSFChainTemplates:
    """Pre-built attack chain templates for common scenarios."""

    TEMPLATES = {
        "windows_domain_takeover": {
            "name": "Windows Domain Takeover",
            "description": "Progressive attack to compromise AD domain",
            "phases": [
                {
                    "name": "Initial Foothold",
                    "modules": [
                        "auxiliary/scanner/smb/smb_ms17_010",
                        "exploit/windows/smb/ms17_010_eternalblue",
                        "auxiliary/scanner/smb/smb_enumshares",
                    ],
                },
                {
                    "name": "Credential Harvesting",
                    "modules": [
                        "post/windows/gather/hashdump",
                        "post/windows/gather/credentials/credential_collector",
                        "post/windows/gather/cachedump",
                    ],
                    "triggers": ["session_obtained"],
                },
                {
                    "name": "Lateral Movement",
                    "modules": [
                        "exploit/windows/smb/psexec",
                        "exploit/windows/local/bypassuac",
                    ],
                    "triggers": ["credentials_obtained"],
                },
            ],
        },
        "linux_privilege_escalation": {
            "name": "Linux Privilege Escalation Chain",
            "description": "Escalate from user to root on Linux",
            "phases": [
                {
                    "name": "Initial Access",
                    "modules": ["auxiliary/scanner/ssh/ssh_login"],
                },
                {
                    "name": "Enumeration",
                    "modules": [
                        "post/linux/gather/enum_system",
                        "post/linux/gather/checkvm",
                        "post/linux/gather/enum_configs",
                    ],
                    "triggers": ["session_obtained"],
                },
                {
                    "name": "Privilege Escalation",
                    "modules": [
                        "exploit/linux/local/cve_2021_4034_pwnkit_lpe_pkexec",
                        "exploit/linux/local/sudo_baron_samedit",
                        "post/multi/recon/local_exploit_suggester",
                    ],
                    "triggers": ["user_session_obtained"],
                },
            ],
        },
        "web_app_to_system": {
            "name": "Web Application to System Access",
            "description": "From web vuln to full system compromise",
            "phases": [
                {
                    "name": "Web Exploitation",
                    "modules": [
                        "auxiliary/scanner/http/dir_scanner",
                        "exploit/multi/http/php_cgi_arg_injection",
                    ],
                },
                {
                    "name": "Reverse Shell",
                    "modules": ["payload/php/meterpreter/reverse_tcp"],
                    "triggers": ["web_access_obtained"],
                },
                {
                    "name": "Privilege Escalation",
                    "modules": ["post/multi/recon/local_exploit_suggester"],
                    "triggers": ["shell_obtained"],
                },
            ],
        },
    }

    @classmethod
    def get_template(cls, template_name: str) -> Dict:
        """Get attack chain template by name."""
        return cls.TEMPLATES.get(template_name)

    @classmethod
    def list_templates(cls) -> List[str]:
        """List available template names."""
        return list(cls.TEMPLATES.keys())
