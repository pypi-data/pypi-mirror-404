#!/usr/bin/env python3
"""
souleyez.parsers.service_explorer_parser

Parses Service Explorer JSON output into structured data for display and findings.
"""

import json
import re
from typing import Any, Dict, List


def parse_service_explorer_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse Service Explorer JSON output.

    Service Explorer outputs JSON with this structure:
    {
        "protocol": "ftp",
        "target": "192.168.1.100",
        "port": 21,
        "username": "anonymous",
        "files_found": 15,
        "interesting_files": 3,
        "downloaded": 2,
        "files": [...],
        "interesting": [...],
        "downloaded_files": [...],
        "errors": [...]
    }

    Args:
        output: Raw JSON output from Service Explorer
        target: Target IP/hostname from job

    Returns:
        Dict with parsed data
    """
    result = {
        "target": target,
        "protocol": None,
        "port": None,
        "username": None,
        "files_found": 0,
        "interesting_count": 0,
        "downloaded_count": 0,
        "files": [],
        "interesting_files": [],
        "downloaded_files": [],
        "errors": [],
        "server_info": None,
        "error": None,
    }

    # Try to parse as JSON first
    try:
        # Handle log file format (may have header lines)
        json_start = output.find("{")
        if json_start >= 0:
            json_str = output[json_start:]
            data = json.loads(json_str)

            result["protocol"] = data.get("protocol")
            result["port"] = data.get("port")
            result["username"] = data.get("username")
            result["target"] = data.get("target") or target
            result["files_found"] = data.get("files_found", 0)
            result["interesting_count"] = data.get("interesting_files", 0)
            result["downloaded_count"] = data.get("downloaded", 0)
            result["files"] = data.get("files", [])
            result["interesting_files"] = data.get("interesting", [])
            result["downloaded_files"] = data.get("downloaded_files", [])
            result["errors"] = data.get("errors", [])

            # Check for connection error
            if data.get("error"):
                result["error"] = data.get("error")

            # Extract server info if present (Redis/MongoDB)
            for item in result["files"]:
                if item.get("name") == "__SERVER_INFO__":
                    result["server_info"] = item.get("data", {})
                    result["files"].remove(item)
                    break

            return result

    except json.JSONDecodeError:
        pass

    # Fallback: try to extract info from non-JSON output
    if "Connection failed" in output or "connection failed" in output:
        result["error"] = "Connection failed"
    elif "not installed" in output:
        error_match = re.search(r"(\w+) not installed", output)
        if error_match:
            result["error"] = f"{error_match.group(1)} not installed"

    return result


def extract_findings(parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract security findings from parsed Service Explorer data.

    Returns:
        List of finding dictionaries with:
        {
            'title': str,
            'severity': str,  # high, medium, low, info
            'description': str,
            'evidence': str
        }
    """
    findings = []
    protocol = parsed_data.get("protocol", "unknown").upper()
    target = parsed_data.get("target", "unknown")
    username = parsed_data.get("username", "")

    # Finding: Sensitive files discovered
    sensitive_files = []
    for f in parsed_data.get("interesting_files", []):
        filename = f.get("name", "")
        # Categorize sensitivity
        if any(
            p in filename.lower()
            for p in ["passwd", "shadow", "password", "credential", "secret"]
        ):
            sensitive_files.append((f, "critical"))
        elif any(
            p in filename.lower() for p in ["id_rsa", "id_dsa", ".pem", ".key", ".pfx"]
        ):
            sensitive_files.append((f, "critical"))
        elif any(p in filename.lower() for p in [".sql", ".db", ".sqlite", ".mdb"]):
            sensitive_files.append((f, "high"))
        elif any(p in filename.lower() for p in [".conf", ".config", ".ini", ".env"]):
            sensitive_files.append((f, "medium"))
        elif any(
            p in filename.lower() for p in ["flag", "proof", "root.txt", "user.txt"]
        ):
            sensitive_files.append((f, "high"))  # CTF flags
        elif any(p in filename.lower() for p in [".bak", ".backup", ".old"]):
            sensitive_files.append((f, "medium"))
        else:
            sensitive_files.append((f, "low"))

    # Critical files
    critical_files = [(f, s) for f, s in sensitive_files if s == "critical"]
    if critical_files:
        findings.append(
            {
                "title": f"{protocol} Critical Sensitive Files Exposed",
                "severity": "high",
                "description": f"Found {len(critical_files)} critical sensitive file(s) on {protocol} service. "
                "These files may contain credentials, private keys, or other highly sensitive data.",
                "evidence": "\n".join(
                    [
                        f"- {f.get('full_path', f.get('name'))} ({f.get('size', 0)} bytes)"
                        for f, _ in critical_files[:10]
                    ]
                ),
            }
        )

    # High severity files
    high_files = [(f, s) for f, s in sensitive_files if s == "high"]
    if high_files:
        findings.append(
            {
                "title": f"{protocol} Database/Flag Files Found",
                "severity": "medium",
                "description": f"Found {len(high_files)} database or flag file(s) on {protocol} service.",
                "evidence": "\n".join(
                    [
                        f"- {f.get('full_path', f.get('name'))} ({f.get('size', 0)} bytes)"
                        for f, _ in high_files[:10]
                    ]
                ),
            }
        )

    # Finding: Anonymous/null session access
    if (
        username in ["anonymous", "guest", "", None]
        and parsed_data.get("files_found", 0) > 0
    ):
        findings.append(
            {
                "title": f"{protocol} Anonymous Access Allowed",
                "severity": "medium",
                "description": f"Anonymous/guest access is permitted on {protocol} service at {target}. "
                f"Found {parsed_data.get('files_found')} files accessible without authentication.",
                "evidence": f"Protocol: {protocol}\nTarget: {target}\nUsername: {username or 'anonymous'}\n"
                f"Files Found: {parsed_data.get('files_found')}\n"
                f"Interesting Files: {parsed_data.get('interesting_count')}",
            }
        )

    # Finding: Files downloaded
    if parsed_data.get("downloaded_count", 0) > 0:
        findings.append(
            {
                "title": f"{protocol} Files Downloaded",
                "severity": "info",
                "description": f"Successfully downloaded {parsed_data.get('downloaded_count')} file(s) "
                f"from {protocol} service for analysis.",
                "evidence": "\n".join(
                    [f"- {f}" for f in parsed_data.get("downloaded_files", [])[:10]]
                ),
            }
        )

    # Finding: Redis server info
    if protocol == "REDIS" and parsed_data.get("server_info"):
        info = parsed_data["server_info"]
        findings.append(
            {
                "title": "Redis Server Information Exposed",
                "severity": "medium",
                "description": "Redis server is accessible and exposes detailed configuration information. "
                "This may allow attackers to gather intelligence for further attacks.",
                "evidence": "\n".join(
                    [f"- {k}: {v}" for k, v in info.items() if v is not None]
                ),
            }
        )

        # Check for dangerous Redis config
        if info.get("total_keys", 0) > 0:
            findings.append(
                {
                    "title": "Redis Database Contains Data",
                    "severity": "medium",
                    "description": f"Redis database contains {info.get('total_keys')} keys. "
                    "May contain cached credentials, session tokens, or sensitive application data.",
                    "evidence": f"Total keys: {info.get('total_keys')}",
                }
            )

    # Finding: MongoDB server info
    if protocol in ["MONGO", "MONGODB"] and parsed_data.get("server_info"):
        info = parsed_data["server_info"]
        findings.append(
            {
                "title": "MongoDB Server Information Exposed",
                "severity": "medium",
                "description": "MongoDB server is accessible without authentication. "
                "This is a critical security misconfiguration.",
                "evidence": "\n".join(
                    [f"- {k}: {v}" for k, v in info.items() if v is not None]
                ),
            }
        )

    # Finding: General enumeration success
    if parsed_data.get("files_found", 0) > 0 and not findings:
        findings.append(
            {
                "title": f"{protocol} Service Enumeration Successful",
                "severity": "info",
                "description": f"Successfully enumerated {protocol} service and found "
                f"{parsed_data.get('files_found')} items.",
                "evidence": f"Protocol: {protocol}\nTarget: {target}\n"
                f"Files Found: {parsed_data.get('files_found')}\n"
                f"Interesting Files: {parsed_data.get('interesting_count')}",
            }
        )

    # Finding: Connection errors
    if parsed_data.get("errors"):
        findings.append(
            {
                "title": f"{protocol} Enumeration Errors",
                "severity": "info",
                "description": f"Encountered {len(parsed_data['errors'])} error(s) during enumeration.",
                "evidence": "\n".join([f"- {e}" for e in parsed_data["errors"][:5]]),
            }
        )

    return findings
