"""
Wazuh Rule Mappings.

Maps attack types to Wazuh detection rule IDs and provides
rule metadata for detection validation and recommendations.
"""

from typing import Any, Dict, List

# Wazuh rule mappings by attack type
# These complement the attack_signatures.py definitions
WAZUH_ATTACK_RULES: Dict[str, Dict[str, Any]] = {
    "nmap": {
        "rule_ids": [5700, 5701, 5702, 5710, 87701, 87702],
        "rule_names": {
            5700: "Possible port scan detected",
            5701: "Port scan from host",
            5702: "SYN scan detected",
            5710: "Network scan detected",
            87701: "Suricata IDS alert - scan detected",
            87702: "Suricata IDS alert - probe detected",
        },
        "detection_guidance": (
            "Enable network scan detection rules. Monitor for: "
            "SYN scans, service enumeration, port sweeps. "
            "Log source: firewall, IDS, network flow data."
        ),
    },
    "hydra": {
        "rule_ids": [5551, 5710, 5712, 5720, 5763, 5764, 5765],
        "rule_names": {
            5551: "Multiple authentication failures",
            5710: "SSH brute force attempt",
            5712: "SSH authentication failure",
            5720: "Multiple failed logins",
            5763: "PAM: Multiple failed logins",
            5764: "PAM: Login session opened",
            5765: "PAM: User login failed",
        },
        "detection_guidance": (
            "Enable brute force detection rules. Monitor for: "
            "multiple failed authentication attempts, rapid login attempts. "
            "Log source: authentication logs, SSH, FTP, web server logs."
        ),
    },
    "medusa": {
        "rule_ids": [5551, 5710, 5712, 5720],
        "rule_names": {
            5551: "Multiple authentication failures",
            5710: "SSH brute force attempt",
            5712: "SSH authentication failure",
            5720: "Multiple failed logins",
        },
        "detection_guidance": (
            "Enable brute force detection rules. Monitor for: "
            "credential stuffing, password spraying patterns. "
            "Log source: authentication logs, PAM, web application logs."
        ),
    },
    "sqlmap": {
        "rule_ids": [31101, 31103, 31104, 31105, 31106, 31151, 31152, 31153],
        "rule_names": {
            31101: "Web attack - SQL injection attempt",
            31103: "SQL injection - UNION attack",
            31104: "SQL injection - Boolean blind",
            31105: "SQL injection - Time blind",
            31106: "SQL injection - Error based",
            31151: "ModSecurity - SQL injection",
            31152: "ModSecurity - Attack detected",
            31153: "ModSecurity - Access denied",
        },
        "detection_guidance": (
            "Enable web attack detection rules. Monitor for: "
            "SQL injection patterns, UNION SELECT, encoded payloads. "
            "Log source: web server logs, WAF, application logs."
        ),
    },
    "gobuster": {
        "rule_ids": [31100, 31101, 31120, 31121, 31122],
        "rule_names": {
            31100: "Web attack detected",
            31101: "Web attack - SQL injection attempt",
            31120: "Common web attack",
            31121: "Directory traversal attempt",
            31122: "Web scanner detected",
        },
        "detection_guidance": (
            "Enable directory enumeration detection. Monitor for: "
            "rapid 404/403 responses, sequential requests to common paths. "
            "Log source: web server access logs, WAF."
        ),
    },
    "ffuf": {
        "rule_ids": [31100, 31101, 31120, 31121, 31122],
        "rule_names": {
            31100: "Web attack detected",
            31101: "Web attack - SQL injection attempt",
            31120: "Common web attack",
            31121: "Directory traversal attempt",
            31122: "Web scanner detected",
        },
        "detection_guidance": (
            "Enable web fuzzing detection. Monitor for: "
            "high-frequency requests, parameter fuzzing, path enumeration. "
            "Log source: web server logs, reverse proxy logs."
        ),
    },
    "dirsearch": {
        "rule_ids": [31100, 31101, 31120],
        "rule_names": {
            31100: "Web attack detected",
            31101: "Web attack - SQL injection attempt",
            31120: "Common web attack",
        },
        "detection_guidance": (
            "Enable directory scanning detection. Monitor for: "
            "sequential path requests, common wordlist patterns. "
            "Log source: web server access logs."
        ),
    },
    "nikto": {
        "rule_ids": [31100, 31101, 31151, 31152, 31153, 31154],
        "rule_names": {
            31100: "Web attack detected",
            31101: "Web attack - SQL injection attempt",
            31151: "ModSecurity - SQL injection",
            31152: "ModSecurity - Attack detected",
            31153: "ModSecurity - Access denied",
            31154: "ModSecurity - Scanner detected",
        },
        "detection_guidance": (
            "Enable web vulnerability scanning detection. Monitor for: "
            "known scanner user agents, vulnerability probe patterns. "
            "Log source: web server logs, WAF, IDS."
        ),
    },
    "crackmapexec": {
        "rule_ids": [18104, 18105, 18106, 5710, 5720],
        "rule_names": {
            18104: "Windows - Multiple logon failures",
            18105: "Windows - Logon failure",
            18106: "Windows - Account lockout",
            5710: "SSH brute force attempt",
            5720: "Multiple failed logins",
        },
        "detection_guidance": (
            "Enable SMB/lateral movement detection. Monitor for: "
            "pass-the-hash attempts, SMB enumeration, remote execution. "
            "Log source: Windows Security logs, SMB audit logs."
        ),
    },
    "smbmap": {
        "rule_ids": [18104, 18105],
        "rule_names": {
            18104: "Windows - Multiple logon failures",
            18105: "Windows - Logon failure",
        },
        "detection_guidance": (
            "Enable SMB enumeration detection. Monitor for: "
            "share enumeration, anonymous access attempts. "
            "Log source: Windows Security logs, Samba logs."
        ),
    },
    "metasploit": {
        "rule_ids": [87700, 87701, 87702, 5710, 31101],
        "rule_names": {
            87700: "Suricata IDS alert",
            87701: "Suricata IDS alert - scan detected",
            87702: "Suricata IDS alert - probe detected",
            5710: "SSH brute force attempt",
            31101: "Web attack - SQL injection attempt",
        },
        "detection_guidance": (
            "Enable exploitation framework detection. Monitor for: "
            "known exploit signatures, reverse shells, staged payloads. "
            "Log source: IDS/IPS, endpoint detection, network flow."
        ),
    },
    "enum4linux": {
        "rule_ids": [18104, 18105, 18106],
        "rule_names": {
            18104: "Windows - Multiple logon failures",
            18105: "Windows - Logon failure",
            18106: "Windows - Account lockout",
        },
        "detection_guidance": (
            "Enable SMB/AD enumeration detection. Monitor for: "
            "RPC enumeration, null session access, user listing. "
            "Log source: Windows Security logs, DC audit logs."
        ),
    },
}


def get_wazuh_rules_for_attack(attack_type: str) -> Dict[str, Any]:
    """Get Wazuh rule information for an attack type.

    Args:
        attack_type: Tool/attack name (e.g., 'nmap', 'hydra')

    Returns:
        Dict with rule_ids, rule_names, detection_guidance
    """
    attack_lower = attack_type.lower()
    return WAZUH_ATTACK_RULES.get(
        attack_lower,
        {
            "rule_ids": [],
            "rule_names": {},
            "detection_guidance": "Review SIEM rule configuration for this attack category.",
        },
    )


def get_all_wazuh_rule_ids() -> List[int]:
    """Get all Wazuh rule IDs used for detection validation.

    Returns:
        List of unique rule IDs
    """
    all_ids = set()
    for attack_rules in WAZUH_ATTACK_RULES.values():
        all_ids.update(attack_rules.get("rule_ids", []))
    return sorted(list(all_ids))
