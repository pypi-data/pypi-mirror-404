#!/usr/bin/env python3
"""
souleyez.parsers.theharvester_parser

Parses theHarvester OSINT output into structured data.
"""

import re
from typing import Any, Dict


def parse_theharvester_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse theHarvester text output and extract OSINT data.

    theHarvester output format:
    [*] Target: domain.com
    [*] Searching Source.
    [*] ASNS found: N
    --------------------
    AS12345
    [*] Interesting Urls found: N
    --------------------
    http://example.com/path
    [*] IPs found: N
    -------------------
    1.2.3.4
    [*] Emails found: N
    -------------------
    email@example.com
    [*] Hosts found: N
    ---------------------
    subdomain.example.com

    Args:
        output: Raw theHarvester output text
        target: Target domain from job

    Returns:
        Dict with structure:
        {
            'target': str,
            'emails': [str, ...],
            'hosts': [str, ...],
            'ips': [str, ...],
            'urls': [str, ...],
            'asns': [str, ...]
        }
    """
    result = {
        "target": target,
        "emails": [],
        "hosts": [],
        "ips": [],
        "urls": [],
        "asns": [],
    }

    lines = output.split("\n")
    current_section = None

    for line in lines:
        line = line.strip()

        # Detect target
        if line.startswith("[*] Target:"):
            target_match = re.search(r"\[?\*\]?\s*Target:\s*(\S+)", line)
            if target_match:
                result["target"] = target_match.group(1)

        # Detect section headers (case-insensitive, multiple format variations)
        line_lower = line.lower()
        if any(
            x in line_lower for x in ["asns found", "asn found", "autonomous system"]
        ):
            current_section = "asns"
        elif any(
            x in line_lower for x in ["urls found", "interesting urls", "url found"]
        ):
            current_section = "urls"
        elif any(x in line_lower for x in ["ips found", "ip found", "ip addresses"]):
            current_section = "ips"
        elif any(
            x in line_lower for x in ["emails found", "email found", "email addresses"]
        ):
            current_section = "emails"
        elif any(
            x in line_lower
            for x in [
                "hosts found",
                "host found",
                "subdomains found",
                "subdomain found",
            ]
        ):
            current_section = "hosts"
        elif any(
            x in line_lower for x in ["people found", "no people found", "linkedin"]
        ):
            current_section = "people"  # We'll skip this for now

        # Skip separator lines and empty lines
        elif line.startswith("---") or not line:
            continue

        # Skip "No X found" messages
        elif "[*] No" in line:
            current_section = None
            continue

        # Skip header/banner lines
        elif line.startswith("*") or line.startswith("[*] Searching"):
            continue

        # Parse data based on current section
        elif current_section == "asns":
            # ASN format: AS12345
            if line.startswith("AS") and line[2:].isdigit():
                result["asns"].append(line)

        elif current_section == "urls":
            # URL format: http(s)://...
            if line.startswith("http://") or line.startswith("https://"):
                # Clean up trailing punctuation
                url = line.rstrip(".,;)")
                if url not in result["urls"]:
                    result["urls"].append(url)

        elif current_section == "ips":
            # IP format: N.N.N.N
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", line):
                if line not in result["ips"]:
                    result["ips"].append(line)

        elif current_section == "emails":
            # Email format: user@domain
            if "@" in line and "." in line:
                # More permissive email validation (supports international domains)
                # Pattern allows: standard emails, plus-addressing, dots, underscores
                email = line.strip().lower()
                # Remove any leading/trailing brackets or quotes
                email = re.sub(r"^[\[\(<\'\"]+|[\]\)>\'\"]$", "", email)
                if re.match(
                    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email
                ):
                    if email not in result["emails"]:
                        result["emails"].append(email)

        elif current_section == "hosts":
            # Host format: subdomain.domain.tld
            if "." in line and not line.startswith("http"):
                # Clean and validate hostname
                host = line.strip().lower()
                # Remove any leading/trailing brackets, quotes, or trailing dots
                host = re.sub(r"^[\[\(<\'\"]+|[\]\)>\'\".]+$", "", host)
                # More permissive validation: allows underscores (common in some hosts)
                # and longer TLDs (some are 4+ chars)
                if re.match(r"^[a-zA-Z0-9._-]+\.[a-zA-Z]{2,}$", host) and len(host) > 3:
                    if host not in result["hosts"]:
                        result["hosts"].append(host)

    # Add alias fields for backward compatibility with display code
    result["subdomains"] = result["hosts"]  # Alias for display
    result["base_urls"] = result["urls"]  # Alias for display

    return result


def get_osint_stats(parsed: Dict[str, Any]) -> Dict[str, int]:
    """
    Get statistics from parsed theHarvester results.

    Args:
        parsed: Output from parse_theharvester_output()

    Returns:
        Dict with counts: {'emails': 5, 'hosts': 10, ...}
    """
    return {
        "emails": len(parsed.get("emails", [])),
        "hosts": len(parsed.get("hosts", [])),
        "ips": len(parsed.get("ips", [])),
        "urls": len(parsed.get("urls", [])),
        "asns": len(parsed.get("asns", [])),
    }
