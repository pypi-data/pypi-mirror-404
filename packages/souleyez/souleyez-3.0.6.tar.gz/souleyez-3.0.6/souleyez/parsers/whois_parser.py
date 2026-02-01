#!/usr/bin/env python3
"""
souleyez.parsers.whois_parser

Parses WHOIS domain information output into structured OSINT data.
"""

import re
from typing import Any, Dict, List


def parse_whois_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse WHOIS output and extract domain registration information.

    WHOIS output varies by registrar but typically includes:
    - Domain name
    - Registrar
    - Registration/expiration dates
    - Registrant contact information
    - Administrative contact
    - Technical contact
    - Name servers
    - Domain status

    Args:
        output: Raw whois output text
        target: Target domain from job

    Returns:
        Dict with structure:
        {
            'domain': str,
            'registrar': str,
            'registrant': {
                'name': str,
                'organization': str,
                'email': str,
                'phone': str,
                'address': str
            },
            'admin_contact': {...},
            'tech_contact': {...},
            'dates': {
                'created': str,
                'updated': str,
                'expires': str
            },
            'nameservers': [str],
            'status': [str],
            'dnssec': str
        }
    """
    result = {
        "domain": target,
        "registrar": None,
        "registrant": {},
        "admin_contact": {},
        "tech_contact": {},
        "dates": {},
        "nameservers": [],
        "status": [],
        "dnssec": None,
    }

    lines = output.split("\n")
    current_section = None

    for line in lines:
        line_stripped = line.strip()

        # Skip comments and empty lines
        if (
            not line_stripped
            or line_stripped.startswith("%")
            or line_stripped.startswith("#")
        ):
            continue

        # Convert to lowercase for matching
        line_lower = line_stripped.lower()

        # Extract domain name
        if not result["domain"] or result["domain"] == "":
            domain_match = re.match(
                r"domain name:\s+(.+)", line_stripped, re.IGNORECASE
            )
            if domain_match:
                result["domain"] = domain_match.group(1).strip()

        # Extract registrar
        if "registrar:" in line_lower and not result["registrar"]:
            registrar_match = re.search(
                r"registrar:\s+(.+)", line_stripped, re.IGNORECASE
            )
            if registrar_match:
                result["registrar"] = registrar_match.group(1).strip()

        # Extract dates
        if "creation date" in line_lower or "created" in line_lower:
            date_match = re.search(
                r":\s+(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})", line_stripped
            )
            if date_match:
                result["dates"]["created"] = date_match.group(1).strip()

        if (
            "updated date" in line_lower
            or "last updated" in line_lower
            or "modified" in line_lower
        ):
            date_match = re.search(
                r":\s+(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})", line_stripped
            )
            if date_match:
                result["dates"]["updated"] = date_match.group(1).strip()

        if "expir" in line_lower:
            date_match = re.search(
                r":\s+(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})", line_stripped
            )
            if date_match:
                result["dates"]["expires"] = date_match.group(1).strip()

        # Detect contact sections
        if "registrant" in line_lower and "name:" in line_lower:
            current_section = "registrant"
        elif "admin" in line_lower and (
            "name:" in line_lower or "contact" in line_lower
        ):
            current_section = "admin"
        elif "tech" in line_lower and (
            "name:" in line_lower or "contact" in line_lower
        ):
            current_section = "tech"

        # Extract contact information based on current section
        if current_section:
            contact_dict = _get_contact_dict(result, current_section)

            if "name:" in line_lower and "domain name" not in line_lower:
                name_match = re.search(r"name:\s+(.+)", line_stripped, re.IGNORECASE)
                if name_match:
                    contact_dict["name"] = name_match.group(1).strip()

            if "organi" in line_lower:
                org_match = re.search(
                    r"organi[zs]ation:\s+(.+)", line_stripped, re.IGNORECASE
                )
                if org_match:
                    contact_dict["organization"] = org_match.group(1).strip()

            if "email" in line_lower:
                email_match = re.search(r"email:\s+(.+)", line_stripped, re.IGNORECASE)
                if email_match:
                    contact_dict["email"] = email_match.group(1).strip()

            if "phone" in line_lower:
                phone_match = re.search(r"phone:\s+(.+)", line_stripped, re.IGNORECASE)
                if phone_match:
                    contact_dict["phone"] = phone_match.group(1).strip()

        # Extract nameservers
        if "name server" in line_lower or "nserver" in line_lower:
            ns_match = re.search(
                r"(?:name server|nserver):\s+(.+)", line_stripped, re.IGNORECASE
            )
            if ns_match:
                nameserver = ns_match.group(1).strip().lower()
                if nameserver not in result["nameservers"]:
                    result["nameservers"].append(nameserver)

        # Extract status
        if "status:" in line_lower:
            status_match = re.search(r"status:\s+(.+)", line_stripped, re.IGNORECASE)
            if status_match:
                status = status_match.group(1).strip()
                if status not in result["status"]:
                    result["status"].append(status)

        # Extract DNSSEC
        if "dnssec:" in line_lower:
            dnssec_match = re.search(r"dnssec:\s+(.+)", line_stripped, re.IGNORECASE)
            if dnssec_match:
                result["dnssec"] = dnssec_match.group(1).strip()

    return result


def _get_contact_dict(result: Dict[str, Any], section: str) -> Dict[str, Any]:
    """Get the appropriate contact dictionary based on section."""
    if section == "registrant":
        return result["registrant"]
    elif section == "admin":
        return result["admin_contact"]
    elif section == "tech":
        return result["tech_contact"]
    return {}


def extract_emails(parsed_data: Dict[str, Any]) -> List[str]:
    """
    Extract all email addresses from WHOIS data.

    Args:
        parsed_data: Output from parse_whois_output()

    Returns:
        List of unique email addresses
    """
    emails = []

    for contact in [
        parsed_data.get("registrant", {}),
        parsed_data.get("admin_contact", {}),
        parsed_data.get("tech_contact", {}),
    ]:
        email = contact.get("email")
        if email and email not in emails and "@" in email:
            emails.append(email)

    return emails


def map_to_osint_data(
    parsed_data: Dict[str, Any], engagement_id: int
) -> Dict[str, Any]:
    """
    Convert parsed WHOIS data into OSINT record for database storage.

    Args:
        parsed_data: Output from parse_whois_output()
        engagement_id: Current engagement ID

    Returns:
        OSINT data dict ready for OsintManager.add()
    """
    import json

    # Extract key information for quick reference
    summary_parts = []

    if parsed_data.get("registrar"):
        summary_parts.append(f"Registrar: {parsed_data['registrar']}")

    if parsed_data.get("dates", {}).get("created"):
        summary_parts.append(f"Created: {parsed_data['dates']['created']}")

    if parsed_data.get("dates", {}).get("expires"):
        summary_parts.append(f"Expires: {parsed_data['dates']['expires']}")

    if parsed_data.get("registrant", {}).get("organization"):
        summary_parts.append(f"Org: {parsed_data['registrant']['organization']}")

    summary = (
        " | ".join(summary_parts)
        if summary_parts
        else "Domain registration information"
    )

    # Extract emails for OSINT correlation
    emails = extract_emails(parsed_data)

    osint_record = {
        "target": parsed_data.get("domain", ""),
        "data_type": "domain_info",
        "source": "whois",
        "content": json.dumps(parsed_data, indent=2),
        "summary": summary,
        "metadata": json.dumps(
            {
                "registrar": parsed_data.get("registrar"),
                "nameservers": parsed_data.get("nameservers", []),
                "emails": emails,
                "expiration_date": parsed_data.get("dates", {}).get("expires"),
                "dnssec": parsed_data.get("dnssec"),
            }
        ),
    }

    return osint_record


def check_privacy_protection(parsed_data: Dict[str, Any]) -> bool:
    """
    Check if domain uses privacy protection service.

    Args:
        parsed_data: Output from parse_whois_output()

    Returns:
        True if privacy protection detected
    """
    privacy_indicators = [
        "privacy",
        "redacted",
        "protected",
        "whoisguard",
        "domains by proxy",
        "private registration",
    ]

    # Check registrant info
    registrant_text = str(parsed_data.get("registrant", {})).lower()

    for indicator in privacy_indicators:
        if indicator in registrant_text:
            return True

    # Check registrar
    registrar = str(parsed_data.get("registrar", "")).lower()
    for indicator in privacy_indicators:
        if indicator in registrar:
            return True

    return False


# Export the main functions
__all__ = [
    "parse_whois_output",
    "map_to_osint_data",
    "extract_emails",
    "check_privacy_protection",
]
