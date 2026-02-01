"""
Attack Signature Definitions.

Maps SoulEyez tool names to expected Wazuh detection rules and search patterns.
Used for correlating attacks with SIEM alerts.
"""

from typing import Any, Dict, List

# Detection window in seconds after attack completes
DEFAULT_DETECTION_WINDOW = 300  # 5 minutes


ATTACK_SIGNATURES: Dict[str, Dict[str, Any]] = {
    # Port scanning and discovery
    "nmap": {
        "description": "Port scan / service detection",
        "category": "reconnaissance",
        "wazuh_rules": [5700, 5701, 5702, 5710, 87701, 87702],
        "search_patterns": ["scan", "port scan", "nmap", "SYN scan"],
        "expected_fields": ["srcip", "dstip"],
        "detection_window_seconds": 300,
        "severity": "low",
    },
    # Brute force attacks
    "hydra": {
        "description": "Brute force authentication",
        "category": "credential_access",
        "wazuh_rules": [5551, 5710, 5712, 5720, 5763, 5764, 5765],
        "search_patterns": [
            "brute force",
            "authentication failure",
            "failed login",
            "invalid user",
        ],
        "expected_fields": ["srcip", "user"],
        "detection_window_seconds": 600,
        "severity": "high",
    },
    "medusa": {
        "description": "Brute force authentication",
        "category": "credential_access",
        "wazuh_rules": [5551, 5710, 5712, 5720],
        "search_patterns": ["brute force", "authentication failure", "failed login"],
        "expected_fields": ["srcip", "user"],
        "detection_window_seconds": 600,
        "severity": "high",
    },
    # Web application attacks
    "sqlmap": {
        "description": "SQL injection attempts",
        "category": "web_attack",
        "wazuh_rules": [31101, 31103, 31104, 31105, 31106, 31151, 31152, 31153],
        "search_patterns": ["SQL injection", "sqlmap", "UNION SELECT", "' OR '1'='1"],
        "expected_fields": ["srcip", "url", "data.url"],
        "detection_window_seconds": 300,
        "severity": "critical",
    },
    "gobuster": {
        "description": "Directory enumeration / forced browsing",
        "category": "web_attack",
        "wazuh_rules": [31100, 31101, 31120, 31121, 31122],
        "search_patterns": [
            "web scanner",
            "directory traversal",
            "404",
            "403 forbidden",
        ],
        "expected_fields": ["srcip", "url"],
        "detection_window_seconds": 300,
        "severity": "medium",
    },
    "ffuf": {
        "description": "Fuzzing / directory enumeration",
        "category": "web_attack",
        "wazuh_rules": [31100, 31101, 31120, 31121, 31122],
        "search_patterns": ["web scanner", "directory", "fuzzing"],
        "expected_fields": ["srcip", "url"],
        "detection_window_seconds": 300,
        "severity": "medium",
    },
    "dirsearch": {
        "description": "Directory enumeration",
        "category": "web_attack",
        "wazuh_rules": [31100, 31101, 31120],
        "search_patterns": ["web scanner", "directory", "dirsearch"],
        "expected_fields": ["srcip", "url"],
        "detection_window_seconds": 300,
        "severity": "medium",
    },
    "nikto": {
        "description": "Web vulnerability scanning",
        "category": "web_attack",
        "wazuh_rules": [31100, 31101, 31151, 31152, 31153, 31154],
        "search_patterns": ["nikto", "web scanner", "vulnerability scan"],
        "expected_fields": ["srcip", "url"],
        "detection_window_seconds": 300,
        "severity": "medium",
    },
    # SMB/Network attacks
    "crackmapexec": {
        "description": "SMB enumeration and lateral movement",
        "category": "lateral_movement",
        "wazuh_rules": [18104, 18105, 18106, 5710, 5720],
        "search_patterns": ["SMB", "pass the hash", "authentication", "NTLM"],
        "expected_fields": ["srcip", "dstip"],
        "detection_window_seconds": 300,
        "severity": "high",
    },
    "smbclient": {
        "description": "SMB share enumeration",
        "category": "reconnaissance",
        "wazuh_rules": [18104, 18105],
        "search_patterns": ["SMB", "share", "enumeration"],
        "expected_fields": ["srcip", "dstip"],
        "detection_window_seconds": 300,
        "severity": "low",
    },
    # DNS enumeration
    "dnsrecon": {
        "description": "DNS reconnaissance",
        "category": "reconnaissance",
        "wazuh_rules": [87700, 87701],
        "search_patterns": ["DNS", "zone transfer", "enumeration"],
        "expected_fields": ["srcip"],
        "detection_window_seconds": 300,
        "severity": "low",
    },
    "fierce": {
        "description": "DNS reconnaissance",
        "category": "reconnaissance",
        "wazuh_rules": [87700, 87701],
        "search_patterns": ["DNS", "enumeration"],
        "expected_fields": ["srcip"],
        "detection_window_seconds": 300,
        "severity": "low",
    },
    # Password attacks
    "hashcat": {
        "description": "Password cracking (offline)",
        "category": "credential_access",
        "wazuh_rules": [],  # Offline, no network detection expected
        "search_patterns": [],
        "expected_fields": [],
        "detection_window_seconds": 0,
        "severity": "info",
        "offline": True,
    },
    "john": {
        "description": "Password cracking (offline)",
        "category": "credential_access",
        "wazuh_rules": [],
        "search_patterns": [],
        "expected_fields": [],
        "detection_window_seconds": 0,
        "severity": "info",
        "offline": True,
    },
    # Exploitation
    "metasploit": {
        "description": "Exploitation framework",
        "category": "exploitation",
        "wazuh_rules": [87700, 87701, 87702, 5710, 31101],
        "search_patterns": ["exploit", "payload", "meterpreter", "shell"],
        "expected_fields": ["srcip", "dstip"],
        "detection_window_seconds": 600,
        "severity": "critical",
    },
    # Generic/fallback
    "custom": {
        "description": "Custom tool execution",
        "category": "unknown",
        "wazuh_rules": [],
        "search_patterns": [],
        "expected_fields": ["srcip"],
        "detection_window_seconds": 300,
        "severity": "medium",
    },
}


def get_signature(tool_name: str) -> Dict[str, Any]:
    """
    Get attack signature for a tool.

    Args:
        tool_name: Name of the tool (case-insensitive)

    Returns:
        Signature dict or custom fallback
    """
    tool_lower = tool_name.lower()

    # Direct match
    if tool_lower in ATTACK_SIGNATURES:
        return ATTACK_SIGNATURES[tool_lower]

    # Partial match (e.g., "nmap -sV" matches "nmap")
    for key in ATTACK_SIGNATURES:
        if key in tool_lower or tool_lower.startswith(key):
            return ATTACK_SIGNATURES[key]

    # Return custom fallback
    return ATTACK_SIGNATURES["custom"]


def get_detection_categories() -> List[str]:
    """Get unique detection categories."""
    return list(set(sig["category"] for sig in ATTACK_SIGNATURES.values()))
