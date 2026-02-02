#!/usr/bin/env python3
"""
souleyez.parsers.wpscan_parser

Parses WPScan WordPress vulnerability scan output into structured findings.
"""

import json
import re
from typing import Any, Dict, List, Optional


def parse_wpscan_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse WPScan output and extract WordPress vulnerabilities and information.

    WPScan provides text output with sections for:
    - WordPress version and vulnerabilities
    - Installed plugins and their vulnerabilities
    - Installed themes and their vulnerabilities
    - Enumerated users
    - Security issues

    Args:
        output: Raw wpscan output text
        target: Target URL from job

    Returns:
        Dict with structure:
        {
            'target_url': str,
            'wordpress_version': str,
            'users': [str],  # Enumerated usernames
            'findings': [
                {
                    'title': str,
                    'type': str,  # 'core', 'plugin', 'theme', 'config'
                    'name': str,  # plugin/theme name or 'WordPress Core'
                    'version': str,
                    'severity': str,  # 'critical', 'high', 'medium', 'low', 'info'
                    'description': str,
                    'references': [str],  # CVE IDs, URLs
                    'fixed_in': str  # Version where fixed
                }
            ],
            'plugins': [
                {
                    'name': str,
                    'version': str,
                    'location': str,
                    'vulnerable': bool
                }
            ],
            'themes': [
                {
                    'name': str,
                    'version': str,
                    'location': str,
                    'vulnerable': bool
                }
            ]
        }
    """
    result = {
        "target_url": target,
        "wordpress_version": None,
        "version_status": None,  # 'Insecure', 'Outdated', etc.
        "version_release_date": None,
        "users": [],
        "findings": [],
        "plugins": [],
        "themes": [],
        "info": [],  # Additional findings (multisite, wp-cron, readme, headers, etc.)
    }

    # Strip ANSI escape codes from output (wpscan uses colored output)
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m|\[[\d;]*m")
    output = ansi_escape.sub("", output)

    lines = output.split("\n")
    current_section = None
    # current_plugin and current_theme not used currently

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Extract WordPress version with status
        if "WordPress version" in line or line_stripped.startswith(
            "[+] WordPress version"
        ):
            version_match = re.search(
                r"WordPress version[:\s]+(\d+\.\d+(?:\.\d+)?)", line
            )
            if version_match:
                result["wordpress_version"] = version_match.group(1)

                # Check for insecure/outdated status
                if "Insecure" in line:
                    result["version_status"] = "Insecure"
                elif "Outdated" in line:
                    result["version_status"] = "Outdated"

                # Extract release date
                date_match = re.search(r"released on (\d{4}-\d{2}-\d{2})", line)
                if date_match:
                    result["version_release_date"] = date_match.group(1)

        # Detect multisite
        if "seems to be a multisite" in line.lower():
            # Check if not already added
            if not any(
                item["title"] == "WordPress Multisite Detected"
                for item in result["info"]
            ):
                result["info"].append(
                    {
                        "type": "config",
                        "title": "WordPress Multisite Detected",
                        "description": "This installation is configured as a WordPress multisite network.",
                        "severity": "info",
                    }
                )

        # Detect WP-Cron
        if "external WP-Cron seems to be enabled" in line.lower():
            if not any(
                item["title"] == "External WP-Cron Enabled" for item in result["info"]
            ):
                result["info"].append(
                    {
                        "type": "config",
                        "title": "External WP-Cron Enabled",
                        "description": "The external WP-Cron endpoint is accessible.",
                        "severity": "low",
                    }
                )

        # Detect README file
        if "readme found:" in line.lower() and "readme.html" in line.lower():
            if not any(
                item["title"] == "WordPress README File Exposed"
                for item in result["info"]
            ):
                result["info"].append(
                    {
                        "type": "disclosure",
                        "title": "WordPress README File Exposed",
                        "description": "The WordPress readme.html file is accessible, which can reveal version information.",
                        "severity": "low",
                    }
                )

        # Detect interesting headers
        if line_stripped.startswith("|") and any(
            header in line for header in ["X-Mod-Pagespeed", "X-Powered-By", "Server:"]
        ):
            header_match = re.search(r"\|\s+[-\s]+([^:]+):\s+(.+)", line)
            if header_match:
                header_name = header_match.group(1).strip()
                header_value = header_match.group(2).strip()
                header_title = f"HTTP Header: {header_name}"
                if not any(item["title"] == header_title for item in result["info"]):
                    result["info"].append(
                        {
                            "type": "header",
                            "title": header_title,
                            "description": f"Server header detected: {header_name}: {header_value}",
                            "severity": "info",
                        }
                    )

        # Detect no API token warning
        if "No WPScan API Token given" in line:
            if not any(
                item["title"] == "No WPScan API Token" for item in result["info"]
            ):
                result["info"].append(
                    {
                        "type": "warning",
                        "title": "No WPScan API Token",
                        "description": "Vulnerability data not included. Register at https://wpscan.com/register for a free API token.",
                        "severity": "info",
                    }
                )

        # Detect theme detection failure
        if "main theme could not be detected" in line.lower():
            if not any(
                item["title"] == "Theme Detection Failed" for item in result["info"]
            ):
                result["info"].append(
                    {
                        "type": "info",
                        "title": "Theme Detection Failed",
                        "description": "WPScan could not identify the active theme.",
                        "severity": "info",
                    }
                )

        # Detect no plugins found
        if "[i] No plugins Found" in line or "No plugins Found" in line:
            if not any(
                item["title"] == "No Plugins Detected" for item in result["info"]
            ):
                result["info"].append(
                    {
                        "type": "info",
                        "title": "No Plugins Detected",
                        "description": "WPScan did not detect any WordPress plugins.",
                        "severity": "info",
                    }
                )

        # Detect sections
        if "[+] WordPress theme in use:" in line or "Theme(s) Detected:" in line:
            current_section = "themes"
        elif "[+] Plugins Found:" in line or "Plugin(s) Identified:" in line:
            current_section = "plugins"
        elif "User(s) Identified:" in line or "Username(s) Identified:" in line:
            current_section = "users"

        # Parse vulnerabilities with [!] marker
        # WPScan outputs vulns as either "[!] Title:" or "| [!] Title:" (indented under sections)
        if line_stripped.startswith("[!]") or line_stripped.startswith("| [!]"):
            finding = _parse_vulnerability_line(line, lines[i : i + 10])
            if finding:
                result["findings"].append(finding)

        # Parse enumerated users - format: [+] username (on its own line)
        if current_section == "users":
            # End users section on [!] warning or [+] Finished/Requests
            if (
                line_stripped.startswith("[!]")
                or "Finished:" in line
                or "Requests Done:" in line
            ):
                current_section = None
            else:
                # Match username after [+] at start of line (username may have spaces)
                user_match = re.match(r"^\[\+\]\s*(.+)$", line_stripped)
                if user_match:
                    username = user_match.group(1).strip()
                    if (
                        username
                        and username not in result["users"]
                        and username.lower() not in ("id", "found by")
                    ):
                        result["users"].append(username)

        # Parse plugin info
        if current_section == "plugins":
            plugin_match = re.search(r"\[i\]\s+Plugin\(s\)\s+Identified:\s+(.+)", line)
            if not plugin_match:
                plugin_match = re.search(r"\|\s+Name:\s+(.+)", line)

            if plugin_match:
                plugin_name = plugin_match.group(1).strip()
                plugin_data = {
                    "name": plugin_name,
                    "version": None,
                    "location": None,
                    "vulnerable": False,
                }

                # Look ahead for version and location
                for j in range(i + 1, min(i + 10, len(lines))):
                    if "Latest version:" in lines[j] or "Version:" in lines[j]:
                        ver_match = re.search(r"(\d+\.\d+(?:\.\d+)?)", lines[j])
                        if ver_match:
                            plugin_data["version"] = ver_match.group(1)
                    if "Location:" in lines[j]:
                        loc_match = re.search(r"Location:\s+(.+)", lines[j])
                        if loc_match:
                            plugin_data["location"] = loc_match.group(1).strip()
                    if "[!]" in lines[j]:
                        plugin_data["vulnerable"] = True

                if plugin_name:
                    result["plugins"].append(plugin_data)

        # Parse theme info
        if current_section == "themes":
            theme_match = re.search(r"\|\s+Name:\s+(.+)", line)
            if theme_match:
                theme_name = theme_match.group(1).strip()
                theme_data = {
                    "name": theme_name,
                    "version": None,
                    "location": None,
                    "vulnerable": False,
                }

                # Look ahead for version and location
                for j in range(i + 1, min(i + 10, len(lines))):
                    if "Version:" in lines[j]:
                        ver_match = re.search(r"(\d+\.\d+(?:\.\d+)?)", lines[j])
                        if ver_match:
                            theme_data["version"] = ver_match.group(1)
                    if "Location:" in lines[j]:
                        loc_match = re.search(r"Location:\s+(.+)", lines[j])
                        if loc_match:
                            theme_data["location"] = loc_match.group(1).strip()
                    if "[!]" in lines[j]:
                        theme_data["vulnerable"] = True

                if theme_name:
                    result["themes"].append(theme_data)

    return result


def _parse_vulnerability_line(
    line: str, context_lines: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Parse a vulnerability line and surrounding context.

    Format:
    [!] Title: Vulnerability Name
     |  Fixed in: 1.2.3
     |  References:
     |   - https://wpvulndb.com/vulnerabilities/xxxx
     |   - CVE-2021-12345
    """
    # Extract title - must have "Title:" prefix for actual vulnerabilities
    # WPScan uses "[!] Title: ..." for vulns, other [!] lines are warnings/info
    title_match = re.search(r"\[!\]\s+Title:\s+(.+)", line)
    if not title_match:
        # Only accept lines with explicit "Title:" prefix - skip warnings like:
        # "[!] No WPScan API Token given..."
        # "[!] The version is out of date..."
        # "[!] 121 vulnerabilities identified:"
        return None

    title = title_match.group(1).strip()

    finding = {
        "title": title,
        "type": "unknown",
        "name": "",
        "version": None,
        "severity": "medium",  # Default
        "description": title,
        "references": [],
        "fixed_in": None,
    }

    # Determine type and severity from title
    if "WordPress" in title and "Core" in title:
        finding["type"] = "core"
        finding["name"] = "WordPress Core"
    elif "plugin" in title.lower():
        finding["type"] = "plugin"
    elif "theme" in title.lower():
        finding["type"] = "theme"
    elif "config" in title.lower() or "header" in title.lower():
        finding["type"] = "config"

    # Severity indicators
    if any(
        word in title.lower()
        for word in ["critical", "rce", "sql injection", "remote code"]
    ):
        finding["severity"] = "critical"
    elif any(
        word in title.lower()
        for word in ["high", "authentication bypass", "privilege escalation"]
    ):
        finding["severity"] = "high"
    elif any(word in title.lower() for word in ["xss", "csrf", "medium"]):
        finding["severity"] = "medium"
    elif any(word in title.lower() for word in ["disclosure", "enumeration", "low"]):
        finding["severity"] = "low"
    elif any(word in title.lower() for word in ["info", "version"]):
        finding["severity"] = "info"

    # Extract additional info from context lines (stop at blank line or next vuln)
    for context_line in context_lines[1:]:
        context_stripped = context_line.strip()

        # Stop parsing context at blank lines or next vulnerability marker
        if not context_stripped or context_stripped == "|":
            break
        if "[!]" in context_stripped and "Title:" in context_stripped:
            break

        if "Fixed in:" in context_stripped:
            fixed_match = re.search(
                r"Fixed in:\s+(\d+\.\d+(?:\.\d+)?)", context_stripped
            )
            if fixed_match:
                finding["fixed_in"] = fixed_match.group(1)

        elif "CVE-" in context_stripped:
            cve_matches = re.findall(r"CVE-\d{4}-\d+", context_stripped)
            finding["references"].extend(cve_matches)

        elif "https://" in context_stripped or "http://" in context_stripped:
            url_match = re.search(r"(https?://[^\s<>]+)", context_stripped)
            if url_match:
                url = url_match.group(1).rstrip(",.;)")
                if url not in finding["references"]:
                    finding["references"].append(url)

    return finding


def map_to_findings(
    parsed_data: Dict[str, Any], engagement_id: int
) -> List[Dict[str, Any]]:
    """
    Convert parsed WPScan data into finding records for database storage.

    Args:
        parsed_data: Output from parse_wpscan_output()
        engagement_id: Current engagement ID

    Returns:
        List of finding dicts ready for FindingsManager.add()
    """
    findings = []

    for vuln in parsed_data.get("findings", []):
        finding = {
            "title": vuln["title"],
            "severity": vuln["severity"],
            "description": vuln["description"],
            "affected_target": parsed_data.get("target_url", ""),
            "tool": "wpscan",
            "category": "web",
            "remediation": (
                f"Update {vuln['name']} to version {vuln['fixed_in']}"
                if vuln["fixed_in"]
                else "Review WordPress security settings"
            ),
            "references": "\n".join(vuln["references"]) if vuln["references"] else None,
            "cvss_score": _severity_to_cvss(vuln["severity"]),
            "metadata": json.dumps(
                {
                    "wordpress_version": parsed_data.get("wordpress_version"),
                    "component_type": vuln["type"],
                    "component_name": vuln["name"],
                    "component_version": vuln["version"],
                    "fixed_in": vuln["fixed_in"],
                }
            ),
        }
        findings.append(finding)

    return findings


def _severity_to_cvss(severity: str) -> Optional[float]:
    """Map severity string to approximate CVSS score."""
    severity_map = {
        "critical": 9.5,
        "high": 7.5,
        "medium": 5.0,
        "low": 3.0,
        "info": 0.0,
    }
    return severity_map.get(severity.lower())


# Export the main function
__all__ = ["parse_wpscan_output", "map_to_findings"]
