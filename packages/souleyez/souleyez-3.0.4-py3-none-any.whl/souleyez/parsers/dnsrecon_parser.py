#!/usr/bin/env python3
"""
souleyez.parsers.dnsrecon_parser

Parses DNSRecon output into host records and OSINT data.
"""

import re
from typing import Any, Dict, List


def parse_dnsrecon_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse DNSRecon output and extract discovered hosts and DNS records.

    DNSRecon output contains various DNS record types:
    - A records (hostnames -> IPs)
    - MX records (mail servers)
    - NS records (nameservers)
    - TXT records (SPF, DKIM, etc.)
    - Subdomains from various sources

    Args:
        output: Raw dnsrecon output text
        target: Target domain from job

    Returns:
        Dict with structure:
        {
            'target_domain': str,
            'hosts': [{'hostname': str, 'ip': str, 'type': str}],
            'nameservers': [str],
            'mail_servers': [str],
            'txt_records': [str],
            'subdomains': [str],
            'count': int
        }
    """
    result = {
        "target_domain": target,
        "hosts": [],
        "nameservers": [],
        "mail_servers": [],
        "txt_records": [],
        "subdomains": [],
        "count": 0,
    }

    lines = output.split("\n")
    seen_hosts = set()
    seen_subdomains = set()

    for line in lines:
        line_stripped = line.strip()

        # Skip empty lines and headers
        if not line_stripped or line_stripped.startswith("[-]"):
            continue

        # Parse DNS records from dnsrecon output
        # Format: [*]   A cybersoulsecurity.com 198.185.159.144 (info)
        # Format: [+]   A www.vulnweb.com 44.228.249.3 (found records)
        # New format: 2026-01-08T13:50:16.302153-1000 INFO      SOA dns1.p01.nsone.net 198.51.44.1
        # New format: 2026-01-08T13:50:17.112742-1000 INFO      NS dns4.p01.nsone.net 198.51.45.65

        record_type = None
        hostname = None
        ip = None

        if line_stripped.startswith("[*]") or line_stripped.startswith("[+]"):
            # Format: [*] or [+] <type> <hostname> <ip>
            # [*] = informational, [+] = found/success
            parts = line_stripped.split()
            if len(parts) >= 4:
                record_type = parts[1]
                hostname = parts[2].lower()
                ip = parts[3] if len(parts) > 3 else ""
        elif " INFO " in line_stripped:
            # New format: TIMESTAMP INFO <type> <hostname> <ip>
            # Split on INFO and parse the rest
            info_idx = line_stripped.find(" INFO ")
            if info_idx != -1:
                record_part = line_stripped[info_idx + 6 :].strip()
                parts = record_part.split()
                if len(parts) >= 3:
                    record_type = parts[0]
                    hostname = parts[1].lower()
                    ip = parts[2] if len(parts) > 2 else ""

        if record_type and hostname:
            # Validate IP (both IPv4 and basic IPv6)
            is_ipv4 = (
                re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip) if ip else False
            )

            if record_type == "A" and is_ipv4:
                if hostname not in seen_hosts:
                    seen_hosts.add(hostname)
                    result["hosts"].append(
                        {"hostname": hostname, "ip": ip, "type": "A"}
                    )
                    if hostname != target and hostname not in seen_subdomains:
                        seen_subdomains.add(hostname)
                        result["subdomains"].append(hostname)

            elif record_type == "NS":
                if hostname not in result["nameservers"]:
                    result["nameservers"].append(hostname)

            elif record_type == "MX":
                if hostname not in result["mail_servers"]:
                    result["mail_servers"].append(hostname)

            elif record_type == "SOA":
                # SOA records can also be nameservers
                if hostname not in result["nameservers"]:
                    result["nameservers"].append(hostname)

        # Parse subdomain brute force results: [*] Subdomain: api.example.com IP: 1.2.3.4
        subdomain_match = re.search(
            r"Subdomain:\s+(\S+)\s+IP:\s+(\d+\.\d+\.\d+\.\d+)", line_stripped
        )
        if subdomain_match:
            hostname = subdomain_match.group(1).lower()
            ip = subdomain_match.group(2)
            if hostname not in seen_hosts:
                seen_hosts.add(hostname)
                result["hosts"].append(
                    {"hostname": hostname, "ip": ip, "type": "Subdomain"}
                )
                if hostname not in seen_subdomains:
                    seen_subdomains.add(hostname)
                    result["subdomains"].append(hostname)

    result["count"] = len(result["hosts"])

    return result


def map_to_hosts(
    parsed_data: Dict[str, Any], engagement_id: int
) -> List[Dict[str, Any]]:
    """
    Convert parsed DNSRecon data into host records for database storage.

    Creates a host record for each discovered hostname/IP pair.

    Args:
        parsed_data: Output from parse_dnsrecon_output()
        engagement_id: Current engagement ID

    Returns:
        List of host dicts ready for HostManager.add()
    """
    hosts = []

    for host_data in parsed_data.get("hosts", []):
        hostname = host_data.get("hostname", "")
        ip = host_data.get("ip", "")
        record_type = host_data.get("type", "Unknown")

        host = {
            "ip_address": ip,
            "hostname": hostname,
            "os_name": "Unknown",
            "status": "up",
            "notes": f"Discovered by dnsrecon ({record_type} record) for domain: {parsed_data.get('target_domain', '')}",
            "tags": ["dns", "dnsrecon", record_type.lower()],
            "source": "dnsrecon",
        }
        hosts.append(host)

    return hosts


def map_to_osint(
    parsed_data: Dict[str, Any], engagement_id: int, job_id: int = None
) -> List[Dict[str, Any]]:
    """
    Convert parsed DNSRecon data into OSINT records for database storage.

    Extracts nameservers, mail servers, TXT records, and subdomains.

    Args:
        parsed_data: Output from parse_dnsrecon_output()
        engagement_id: Current engagement ID
        job_id: Optional job ID for linking

    Returns:
        List of OSINT dicts ready for storage
    """
    osint_records = []
    target = parsed_data.get("target_domain", "unknown")

    # Add nameservers
    for ns in parsed_data.get("nameservers", []):
        osint_records.append(
            {
                "data_type": "nameserver",
                "value": ns,
                "source": "dnsrecon",
                "engagement_id": engagement_id,
                "job_id": job_id,
                "notes": f"Nameserver for {target}",
            }
        )

    # Add mail servers
    for mx in parsed_data.get("mail_servers", []):
        osint_records.append(
            {
                "data_type": "mail_server",
                "value": mx,
                "source": "dnsrecon",
                "engagement_id": engagement_id,
                "job_id": job_id,
                "notes": f"Mail server for {target}",
            }
        )

    # Add TXT records (often contain SPF, DKIM, DMARC, verification codes)
    for txt in parsed_data.get("txt_records", []):
        osint_records.append(
            {
                "data_type": "txt_record",
                "value": txt[:500],  # Limit length
                "source": "dnsrecon",
                "engagement_id": engagement_id,
                "job_id": job_id,
                "notes": f"TXT record for {target}",
            }
        )

    # Add subdomains as hosts
    for subdomain in parsed_data.get("subdomains", []):
        osint_records.append(
            {
                "data_type": "host",
                "value": subdomain,
                "source": "dnsrecon",
                "engagement_id": engagement_id,
                "job_id": job_id,
                "notes": f"Subdomain of {target}",
            }
        )

    return osint_records


# Export the main functions
__all__ = ["parse_dnsrecon_output", "map_to_hosts", "map_to_osint"]
