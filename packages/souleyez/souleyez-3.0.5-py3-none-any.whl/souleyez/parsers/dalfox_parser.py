#!/usr/bin/env python3
"""
souleyez.parsers.dalfox_parser

Parses Dalfox XSS scanner output into structured data.
"""

import json
import re
from typing import Any, Dict, List


def parse_dalfox_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse Dalfox output and extract XSS findings.

    Dalfox JSON output format (one per line):
    {"type":"V","data":"[V] Vulnerable...","poc":"http://...","cwe":"CWE-79"}
    {"type":"I","data":"[I] Information..."}
    {"type":"W","data":"[W] Warning..."}

    Or text output:
    [V] Vulnerable: http://example.com/search?q=<script>alert(1)</script>
    [POC] http://example.com/search?q=%3Cscript%3Ealert(1)%3C/script%3E
    [I] Found parameter: q
    [W] WAF detected

    Returns:
        Dict with structure:
        {
            'target': str,
            'vulnerabilities': [
                {
                    'type': str,  # 'reflected', 'dom', 'stored'
                    'parameter': str,
                    'payload': str,
                    'poc': str,
                    'cwe': str,
                    'raw': str
                },
                ...
            ],
            'parameters': [str, ...],  # Discovered parameters
            'warnings': [str, ...],
            'stats': {
                'total_vulns': int,
                'reflected': int,
                'dom': int,
                'parameters_found': int
            }
        }
    """
    result = {
        "target": target,
        "vulnerabilities": [],
        "parameters": [],
        "warnings": [],
        "info": [],
        "stats": {"total_vulns": 0, "reflected": 0, "dom": 0, "parameters_found": 0},
    }

    lines = output.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Try JSON parsing first
        if line.startswith("{"):
            try:
                data = json.loads(line)
                _process_json_line(data, result)
                continue
            except json.JSONDecodeError:
                pass

        # Fall back to text parsing
        _process_text_line(line, result)

    # Update stats
    result["stats"]["total_vulns"] = len(result["vulnerabilities"])
    result["stats"]["parameters_found"] = len(result["parameters"])

    return result


def _process_json_line(data: Dict, result: Dict):
    """Process a JSON-formatted line from Dalfox."""
    msg_type = data.get("type", "")
    msg_data = data.get("data", "")
    poc = data.get("poc", "")
    cwe = data.get("cwe", "")

    if msg_type == "V":
        # Vulnerability found
        vuln = {
            "type": _detect_xss_type(msg_data),
            "parameter": _extract_parameter(poc or msg_data),
            "payload": _extract_payload(poc or msg_data),
            "poc": poc,
            "cwe": cwe,
            "raw": msg_data,
        }
        result["vulnerabilities"].append(vuln)

        if "dom" in msg_data.lower():
            result["stats"]["dom"] += 1
        else:
            result["stats"]["reflected"] += 1

    elif msg_type == "I":
        result["info"].append(msg_data)
        # Check for parameter discovery
        param = _extract_discovered_param(msg_data)
        if param and param not in result["parameters"]:
            result["parameters"].append(param)

    elif msg_type == "W":
        result["warnings"].append(msg_data)


def _process_text_line(line: str, result: Dict):
    """Process a text-formatted line from Dalfox."""

    # Vulnerability line: [V] or [POC]
    if line.startswith("[V]") or "Vulnerable" in line:
        vuln = {
            "type": _detect_xss_type(line),
            "parameter": _extract_parameter(line),
            "payload": _extract_payload(line),
            "poc": "",
            "cwe": "CWE-79",
            "raw": line,
        }
        result["vulnerabilities"].append(vuln)

        if "dom" in line.lower():
            result["stats"]["dom"] += 1
        else:
            result["stats"]["reflected"] += 1

    elif line.startswith("[POC]"):
        # Add POC to last vulnerability
        poc = line.replace("[POC]", "").strip()
        if result["vulnerabilities"]:
            result["vulnerabilities"][-1]["poc"] = poc

    elif line.startswith("[I]") or "Found parameter" in line:
        result["info"].append(line)
        param = _extract_discovered_param(line)
        if param and param not in result["parameters"]:
            result["parameters"].append(param)

    elif line.startswith("[W]") or "WAF" in line:
        result["warnings"].append(line)


def _detect_xss_type(text: str) -> str:
    """Detect the type of XSS from the message."""
    text_lower = text.lower()
    if "dom" in text_lower:
        return "dom"
    elif "stored" in text_lower:
        return "stored"
    else:
        return "reflected"


def _extract_parameter(text: str) -> str:
    """Extract the vulnerable parameter name from text."""
    # Look for common patterns like ?param=, &param=
    match = re.search(r"[?&]([a-zA-Z0-9_-]+)=", text)
    if match:
        return match.group(1)
    return ""


def _extract_payload(text: str) -> str:
    """Extract the XSS payload from text."""
    # Look for script tags or event handlers
    patterns = [
        r"(<script[^>]*>.*?</script>)",
        r"(<img[^>]*onerror[^>]*>)",
        r"(<svg[^>]*onload[^>]*>)",
        r'(javascript:[^\s"\']+)',
        r"(%3C[^%]*%3E)",  # URL encoded
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def _extract_discovered_param(text: str) -> str:
    """Extract discovered parameter name from info message."""
    # Patterns like "Found parameter: q" or "parameter q"
    patterns = [
        r"parameter[:\s]+([a-zA-Z0-9_-]+)",
        r"param[:\s]+([a-zA-Z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def get_vulnerable_parameters(parsed: Dict[str, Any]) -> List[str]:
    """Get list of parameters that have XSS vulnerabilities."""
    params = set()
    for vuln in parsed.get("vulnerabilities", []):
        param = vuln.get("parameter")
        if param:
            params.add(param)
    return list(params)


def get_pocs(parsed: Dict[str, Any]) -> List[str]:
    """Get list of proof-of-concept URLs."""
    pocs = []
    for vuln in parsed.get("vulnerabilities", []):
        poc = vuln.get("poc")
        if poc:
            pocs.append(poc)
    return pocs


def has_critical_findings(parsed: Dict[str, Any]) -> bool:
    """Check if there are any XSS vulnerabilities (always critical)."""
    return len(parsed.get("vulnerabilities", [])) > 0
