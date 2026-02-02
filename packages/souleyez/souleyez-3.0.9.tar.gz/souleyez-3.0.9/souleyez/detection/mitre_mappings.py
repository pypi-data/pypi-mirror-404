"""
MITRE ATT&CK Framework Mappings.

Maps SoulEyez attack tools to MITRE ATT&CK techniques and tactics.
Used for generating detection coverage reports with ATT&CK heatmaps.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# MITRE ATT&CK Tactics (Enterprise Matrix)
# Reference: https://attack.mitre.org/tactics/enterprise/
MITRE_TACTICS: Dict[str, Dict[str, Any]] = {
    "TA0043": {
        "name": "Reconnaissance",
        "description": "Gathering information to plan future operations",
        "phase": "pre-attack",
        "order": 1,
    },
    "TA0042": {
        "name": "Resource Development",
        "description": "Establishing resources to support operations",
        "phase": "pre-attack",
        "order": 2,
    },
    "TA0001": {
        "name": "Initial Access",
        "description": "Trying to get into your network",
        "phase": "attack",
        "order": 3,
    },
    "TA0002": {
        "name": "Execution",
        "description": "Trying to run malicious code",
        "phase": "attack",
        "order": 4,
    },
    "TA0003": {
        "name": "Persistence",
        "description": "Trying to maintain their foothold",
        "phase": "post-attack",
        "order": 5,
    },
    "TA0004": {
        "name": "Privilege Escalation",
        "description": "Trying to gain higher-level permissions",
        "phase": "post-attack",
        "order": 6,
    },
    "TA0005": {
        "name": "Defense Evasion",
        "description": "Trying to avoid being detected",
        "phase": "post-attack",
        "order": 7,
    },
    "TA0006": {
        "name": "Credential Access",
        "description": "Stealing account names and passwords",
        "phase": "attack",
        "order": 8,
    },
    "TA0007": {
        "name": "Discovery",
        "description": "Trying to figure out your environment",
        "phase": "attack",
        "order": 9,
    },
    "TA0008": {
        "name": "Lateral Movement",
        "description": "Moving through your environment",
        "phase": "attack",
        "order": 10,
    },
    "TA0009": {
        "name": "Collection",
        "description": "Gathering data of interest",
        "phase": "post-attack",
        "order": 11,
    },
    "TA0011": {
        "name": "Command and Control",
        "description": "Communicating with compromised systems",
        "phase": "post-attack",
        "order": 12,
    },
    "TA0010": {
        "name": "Exfiltration",
        "description": "Stealing data",
        "phase": "post-attack",
        "order": 13,
    },
    "TA0040": {
        "name": "Impact",
        "description": "Manipulate, interrupt, or destroy systems and data",
        "phase": "post-attack",
        "order": 14,
    },
}


# MITRE ATT&CK Techniques mapped to SoulEyez tools
# Reference: https://attack.mitre.org/techniques/enterprise/
MITRE_TECHNIQUES: Dict[str, Dict[str, Any]] = {
    # Reconnaissance techniques
    "T1595": {
        "name": "Active Scanning",
        "tactic_id": "TA0043",
        "tactic_name": "Reconnaissance",
        "description": "Actively probe victim infrastructure",
        "tools": ["nmap", "nikto"],
        "sub_techniques": ["T1595.001", "T1595.002", "T1595.003"],
    },
    "T1595.001": {
        "name": "Scanning IP Blocks",
        "tactic_id": "TA0043",
        "tactic_name": "Reconnaissance",
        "description": "Scan IP blocks to gather victim network information",
        "tools": ["nmap"],
        "parent": "T1595",
    },
    "T1595.002": {
        "name": "Vulnerability Scanning",
        "tactic_id": "TA0043",
        "tactic_name": "Reconnaissance",
        "description": "Scan for vulnerabilities in victim systems",
        "tools": ["nmap", "nikto", "nuclei"],
        "parent": "T1595",
    },
    # Initial Access techniques
    "T1190": {
        "name": "Exploit Public-Facing Application",
        "tactic_id": "TA0001",
        "tactic_name": "Initial Access",
        "description": "Exploit vulnerabilities in internet-facing systems",
        "tools": ["sqlmap", "metasploit", "nuclei"],
    },
    "T1133": {
        "name": "External Remote Services",
        "tactic_id": "TA0001",
        "tactic_name": "Initial Access",
        "description": "Leverage external-facing remote services",
        "tools": ["hydra", "medusa", "crackmapexec"],
    },
    # Execution techniques
    "T1059": {
        "name": "Command and Scripting Interpreter",
        "tactic_id": "TA0002",
        "tactic_name": "Execution",
        "description": "Abuse command and script interpreters",
        "tools": ["metasploit"],
    },
    # Credential Access techniques
    "T1110": {
        "name": "Brute Force",
        "tactic_id": "TA0006",
        "tactic_name": "Credential Access",
        "description": "Use brute force techniques to access accounts",
        "tools": ["hydra", "medusa", "crackmapexec"],
        "sub_techniques": ["T1110.001", "T1110.002", "T1110.003", "T1110.004"],
    },
    "T1110.001": {
        "name": "Password Guessing",
        "tactic_id": "TA0006",
        "tactic_name": "Credential Access",
        "description": "Guess passwords to access user accounts",
        "tools": ["hydra", "medusa"],
        "parent": "T1110",
    },
    "T1110.002": {
        "name": "Password Cracking",
        "tactic_id": "TA0006",
        "tactic_name": "Credential Access",
        "description": "Crack password hashes offline",
        "tools": ["hashcat", "john"],
        "parent": "T1110",
        "offline": True,
    },
    "T1110.003": {
        "name": "Password Spraying",
        "tactic_id": "TA0006",
        "tactic_name": "Credential Access",
        "description": "Use single password against many accounts",
        "tools": ["hydra", "crackmapexec"],
        "parent": "T1110",
    },
    "T1552": {
        "name": "Unsecured Credentials",
        "tactic_id": "TA0006",
        "tactic_name": "Credential Access",
        "description": "Search for insecurely stored credentials",
        "tools": ["crackmapexec", "smbclient"],
    },
    # Discovery techniques
    "T1046": {
        "name": "Network Service Discovery",
        "tactic_id": "TA0007",
        "tactic_name": "Discovery",
        "description": "Get listing of services running on remote hosts",
        "tools": ["nmap"],
    },
    "T1083": {
        "name": "File and Directory Discovery",
        "tactic_id": "TA0007",
        "tactic_name": "Discovery",
        "description": "Enumerate files and directories on a system",
        "tools": ["gobuster", "ffuf", "dirsearch"],
    },
    "T1135": {
        "name": "Network Share Discovery",
        "tactic_id": "TA0007",
        "tactic_name": "Discovery",
        "description": "Look for shared folders on remote systems",
        "tools": ["smbclient", "crackmapexec", "enum4linux"],
    },
    "T1018": {
        "name": "Remote System Discovery",
        "tactic_id": "TA0007",
        "tactic_name": "Discovery",
        "description": "Get listing of remote systems on a network",
        "tools": ["nmap", "dnsrecon", "fierce"],
    },
    "T1087": {
        "name": "Account Discovery",
        "tactic_id": "TA0007",
        "tactic_name": "Discovery",
        "description": "Get a listing of accounts on a system",
        "tools": ["enum4linux", "crackmapexec"],
    },
    # Lateral Movement techniques
    "T1021": {
        "name": "Remote Services",
        "tactic_id": "TA0008",
        "tactic_name": "Lateral Movement",
        "description": "Use valid accounts to log into remote services",
        "tools": ["crackmapexec", "smbclient"],
        "sub_techniques": ["T1021.001", "T1021.002", "T1021.004"],
    },
    "T1021.002": {
        "name": "SMB/Windows Admin Shares",
        "tactic_id": "TA0008",
        "tactic_name": "Lateral Movement",
        "description": "Use SMB to interact with a remote network share",
        "tools": ["crackmapexec", "smbclient"],
        "parent": "T1021",
    },
    "T1550": {
        "name": "Use Alternate Authentication Material",
        "tactic_id": "TA0008",
        "tactic_name": "Lateral Movement",
        "description": "Use alternate authentication material like hashes",
        "tools": ["crackmapexec"],
        "sub_techniques": ["T1550.002"],
    },
    "T1550.002": {
        "name": "Pass the Hash",
        "tactic_id": "TA0008",
        "tactic_name": "Lateral Movement",
        "description": "Use stolen password hashes to authenticate",
        "tools": ["crackmapexec"],
        "parent": "T1550",
    },
}


# Map attack_signatures.py categories to MITRE tactics
CATEGORY_TO_TACTICS: Dict[str, List[str]] = {
    "reconnaissance": ["TA0043", "TA0007"],
    "credential_access": ["TA0006"],
    "web_attack": ["TA0001", "TA0007"],
    "lateral_movement": ["TA0008"],
    "exploitation": ["TA0001", "TA0002"],
    "unknown": [],
}


@dataclass
class TechniqueResult:
    """Result of a technique being tested."""

    technique_id: str
    technique_name: str
    tactic_id: str
    tactic_name: str
    tested: int = 0
    detected: int = 0
    not_detected: int = 0
    partial: int = 0
    detection_rate: float = 0.0
    tools_used: List[str] = field(default_factory=list)


@dataclass
class TacticResult:
    """Result of a tactic being tested."""

    tactic_id: str
    tactic_name: str
    techniques_tested: int = 0
    techniques_detected: int = 0
    techniques_not_detected: int = 0
    coverage_rate: float = 0.0
    technique_results: List[TechniqueResult] = field(default_factory=list)


class MITREMappings:
    """Maps detection results to MITRE ATT&CK framework."""

    def __init__(self):
        self._tool_to_techniques_cache: Dict[str, List[str]] = {}
        self._build_tool_cache()

    def _build_tool_cache(self):
        """Build reverse mapping from tools to techniques."""
        for tech_id, tech_data in MITRE_TECHNIQUES.items():
            for tool in tech_data.get("tools", []):
                tool_lower = tool.lower()
                if tool_lower not in self._tool_to_techniques_cache:
                    self._tool_to_techniques_cache[tool_lower] = []
                self._tool_to_techniques_cache[tool_lower].append(tech_id)

    def map_tool_to_techniques(self, tool_name: str) -> List[Dict[str, Any]]:
        """
        Map a tool name to MITRE ATT&CK techniques.

        Args:
            tool_name: Name of the attack tool (e.g., 'nmap', 'sqlmap')

        Returns:
            List of technique dictionaries with id, name, tactic info
        """
        tool_lower = tool_name.lower()

        # Direct match
        technique_ids = self._tool_to_techniques_cache.get(tool_lower, [])

        # Partial match (e.g., "nmap -sV" matches "nmap")
        if not technique_ids:
            for cached_tool, tech_ids in self._tool_to_techniques_cache.items():
                if cached_tool in tool_lower or tool_lower.startswith(cached_tool):
                    technique_ids = tech_ids
                    break

        techniques = []
        for tech_id in technique_ids:
            tech_data = MITRE_TECHNIQUES.get(tech_id, {})
            techniques.append(
                {
                    "id": tech_id,
                    "name": tech_data.get("name", "Unknown"),
                    "tactic_id": tech_data.get("tactic_id", ""),
                    "tactic_name": tech_data.get("tactic_name", ""),
                    "description": tech_data.get("description", ""),
                    "is_subtechnique": "." in tech_id,
                    "offline": tech_data.get("offline", False),
                }
            )

        return techniques

    def map_category_to_tactics(self, category: str) -> List[Dict[str, Any]]:
        """
        Map an attack category to MITRE tactics.

        Args:
            category: Category from attack_signatures.py

        Returns:
            List of tactic dictionaries
        """
        tactic_ids = CATEGORY_TO_TACTICS.get(category.lower(), [])
        tactics = []
        for tactic_id in tactic_ids:
            tactic_data = MITRE_TACTICS.get(tactic_id, {})
            tactics.append(
                {
                    "id": tactic_id,
                    "name": tactic_data.get("name", "Unknown"),
                    "phase": tactic_data.get("phase", ""),
                }
            )
        return tactics

    def get_technique_by_id(self, technique_id: str) -> Optional[Dict[str, Any]]:
        """Get technique details by ID."""
        return MITRE_TECHNIQUES.get(technique_id)

    def get_tactic_by_id(self, tactic_id: str) -> Optional[Dict[str, Any]]:
        """Get tactic details by ID."""
        return MITRE_TACTICS.get(tactic_id)

    def get_all_tactics(self) -> List[Dict[str, Any]]:
        """Get all tactics sorted by attack phase order."""
        tactics = []
        for tactic_id, tactic_data in MITRE_TACTICS.items():
            tactics.append(
                {
                    "id": tactic_id,
                    "name": tactic_data["name"],
                    "description": tactic_data["description"],
                    "phase": tactic_data["phase"],
                    "order": tactic_data["order"],
                }
            )
        return sorted(tactics, key=lambda x: x["order"])

    def build_coverage_matrix(
        self, detection_results: List[Any]
    ) -> Dict[str, TechniqueResult]:
        """
        Build MITRE ATT&CK coverage matrix from detection results.

        Args:
            detection_results: List of DetectionResult objects

        Returns:
            Dict mapping technique_id -> TechniqueResult with coverage stats
        """
        matrix: Dict[str, TechniqueResult] = {}

        for result in detection_results:
            # Get attack_type (tool name) from result
            attack_type = getattr(result, "attack_type", None)
            if not attack_type:
                # Try dict access for backwards compatibility
                attack_type = (
                    result.get("attack_type") if isinstance(result, dict) else None
                )
            if not attack_type:
                continue

            # Get detection status
            status = getattr(result, "status", None)
            if not status:
                status = (
                    result.get("detection_status") if isinstance(result, dict) else None
                )
            if not status:
                status = result.get("status") if isinstance(result, dict) else "unknown"

            # Map tool to techniques
            techniques = self.map_tool_to_techniques(attack_type)

            for tech in techniques:
                tech_id = tech["id"]

                if tech_id not in matrix:
                    matrix[tech_id] = TechniqueResult(
                        technique_id=tech_id,
                        technique_name=tech["name"],
                        tactic_id=tech["tactic_id"],
                        tactic_name=tech["tactic_name"],
                    )

                matrix[tech_id].tested += 1

                if attack_type not in matrix[tech_id].tools_used:
                    matrix[tech_id].tools_used.append(attack_type)

                # Update status counts
                if status == "detected":
                    matrix[tech_id].detected += 1
                elif status == "not_detected":
                    matrix[tech_id].not_detected += 1
                elif status == "partial":
                    matrix[tech_id].partial += 1

        # Calculate detection rates
        for tech_result in matrix.values():
            countable = (
                tech_result.detected + tech_result.not_detected + tech_result.partial
            )
            if countable > 0:
                tech_result.detection_rate = round(
                    (tech_result.detected / countable) * 100, 1
                )

        return matrix

    def build_tactic_summary(
        self, technique_matrix: Dict[str, TechniqueResult]
    ) -> Dict[str, TacticResult]:
        """
        Build tactic-level summary from technique coverage matrix.

        Args:
            technique_matrix: Output from build_coverage_matrix()

        Returns:
            Dict mapping tactic_id -> TacticResult
        """
        tactic_summary: Dict[str, TacticResult] = {}

        # Initialize all tactics
        for tactic_id, tactic_data in MITRE_TACTICS.items():
            tactic_summary[tactic_id] = TacticResult(
                tactic_id=tactic_id,
                tactic_name=tactic_data["name"],
            )

        # Aggregate technique results into tactics
        for tech_id, tech_result in technique_matrix.items():
            tactic_id = tech_result.tactic_id
            if tactic_id not in tactic_summary:
                continue

            tactic = tactic_summary[tactic_id]
            tactic.techniques_tested += 1
            tactic.technique_results.append(tech_result)

            # Count technique as detected if any test was detected
            if tech_result.detected > 0:
                tactic.techniques_detected += 1
            elif tech_result.not_detected > 0:
                tactic.techniques_not_detected += 1

        # Calculate coverage rates
        for tactic in tactic_summary.values():
            if tactic.techniques_tested > 0:
                tactic.coverage_rate = round(
                    (tactic.techniques_detected / tactic.techniques_tested) * 100, 1
                )

        return tactic_summary

    def get_coverage_gaps(
        self, technique_matrix: Dict[str, TechniqueResult]
    ) -> List[TechniqueResult]:
        """
        Get techniques that were tested but not detected.

        Args:
            technique_matrix: Output from build_coverage_matrix()

        Returns:
            List of TechniqueResult for undetected techniques
        """
        gaps = []
        for tech_result in technique_matrix.values():
            if tech_result.not_detected > 0 and tech_result.detected == 0:
                gaps.append(tech_result)
        return sorted(gaps, key=lambda x: x.not_detected, reverse=True)

    def get_heatmap_data(
        self, technique_matrix: Dict[str, TechniqueResult]
    ) -> List[Dict[str, Any]]:
        """
        Generate heatmap data for visualization.

        Returns data structured for rendering a MITRE ATT&CK matrix heatmap.

        Args:
            technique_matrix: Output from build_coverage_matrix()

        Returns:
            List of dicts with tactic, technique, and coverage status
        """
        heatmap = []
        tactics = self.get_all_tactics()

        for tactic in tactics:
            tactic_id = tactic["id"]
            tactic_techniques = [
                t for t in technique_matrix.values() if t.tactic_id == tactic_id
            ]

            for tech in tactic_techniques:
                # Determine cell status
                if tech.detected > 0 and tech.not_detected == 0:
                    status = "detected"
                elif tech.not_detected > 0 and tech.detected == 0:
                    status = "not_detected"
                elif tech.detected > 0 and tech.not_detected > 0:
                    status = "partial"
                else:
                    status = "not_tested"

                heatmap.append(
                    {
                        "tactic_id": tactic_id,
                        "tactic_name": tactic["name"],
                        "tactic_order": tactic["order"],
                        "technique_id": tech.technique_id,
                        "technique_name": tech.technique_name,
                        "status": status,
                        "tested": tech.tested,
                        "detected": tech.detected,
                        "not_detected": tech.not_detected,
                        "detection_rate": tech.detection_rate,
                        "tools_used": tech.tools_used,
                    }
                )

        return sorted(heatmap, key=lambda x: (x["tactic_order"], x["technique_id"]))


# Module-level convenience functions
_mappings_instance: Optional[MITREMappings] = None


def get_mappings() -> MITREMappings:
    """Get singleton instance of MITREMappings."""
    global _mappings_instance
    if _mappings_instance is None:
        _mappings_instance = MITREMappings()
    return _mappings_instance


def map_tool_to_techniques(tool_name: str) -> List[Dict[str, Any]]:
    """Map a tool to MITRE techniques."""
    return get_mappings().map_tool_to_techniques(tool_name)


def build_coverage_matrix(detection_results: List[Any]) -> Dict[str, TechniqueResult]:
    """Build MITRE coverage matrix from detection results."""
    return get_mappings().build_coverage_matrix(detection_results)
