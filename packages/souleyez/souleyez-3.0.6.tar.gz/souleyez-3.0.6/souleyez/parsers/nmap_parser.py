#!/usr/bin/env python3
"""
souleyez.parsers.nmap_parser - Parse nmap output into structured data
"""

import re
from typing import Any, Dict, List


def parse_nmap_vuln_scripts(output: str) -> List[Dict[str, Any]]:
    """
    Parse nmap vulnerability script output (--script vuln).

    Extracts vulnerabilities from script output blocks like:
    | ssl-poodle:
    |   VULNERABLE:
    |   SSL POODLE information leak
    |     State: VULNERABLE
    |     IDs:  CVE:CVE-2014-3566  BID:70574

    Also handles vulners output:
    | vulners:
    |   cpe:/a:apache:http_server:2.2.8:
    |     CVE-2010-0425  10.0  https://vulners.com/cve/CVE-2010-0425

    Returns:
        List of vulnerability findings with:
        - host_ip: IP address
        - port: Port number
        - script: Script name
        - title: Vulnerability title
        - state: VULNERABLE, NOT VULNERABLE, etc.
        - cve_ids: List of CVE identifiers
        - cvss_score: CVSS score if available
        - references: List of reference URLs
        - description: Full description
    """
    vulnerabilities = []
    current_host_ip = None
    current_port = None

    lines = output.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Track current host - "Nmap scan report for 10.0.0.73"
        if line.startswith("Nmap scan report for"):
            match = re.search(r"for (\d+\.\d+\.\d+\.\d+)", line)
            if match:
                current_host_ip = match.group(1)
            else:
                # Try hostname (IP in parens)
                match = re.search(r"\((\d+\.\d+\.\d+\.\d+)\)", line)
                if match:
                    current_host_ip = match.group(1)

        # Track current port - "80/tcp   open  http"
        elif re.match(r"^\d+/(tcp|udp)", line):
            parts = line.split()
            if parts:
                port_proto = parts[0].split("/")
                current_port = int(port_proto[0])

        # Parse vulnerability script blocks
        elif line.startswith("| ") and ":" in line and current_host_ip:
            # Could be start of a script block like "| ssl-poodle:"
            script_match = re.match(r"\|\s*([a-zA-Z0-9_-]+):\s*$", line)
            if script_match:
                script_name = script_match.group(1)

                # Collect all lines of this script block
                script_lines = []
                i += 1
                while i < len(lines) and (
                    lines[i].startswith("|") or lines[i].startswith("|_")
                ):
                    script_lines.append(lines[i])
                    if lines[i].startswith("|_"):
                        break
                    i += 1

                script_block = "\n".join(script_lines)

                # Parse vulners output specially (CVE lists with scores)
                if script_name == "vulners":
                    vulns = _parse_vulners_block(
                        script_block, current_host_ip, current_port
                    )
                    vulnerabilities.extend(vulns)
                else:
                    # Parse standard vuln script output
                    vuln = _parse_vuln_script_block(
                        script_name, script_block, current_host_ip, current_port
                    )
                    if vuln:
                        vulnerabilities.extend(vuln)

                continue  # Already advanced i in the while loop

        i += 1

    return vulnerabilities


def _parse_vulners_block(block: str, host_ip: str, port: int) -> List[Dict[str, Any]]:
    """
    Parse vulners script output which lists CVEs with scores.

    Format variations:
    |   cpe:/a:apache:http_server:2.2.8:
    |     CVE-2010-0425  10.0  https://vulners.com/cve/CVE-2010-0425
    |   nginx 1.19.0:
    |     NGINX:CVE-2022-41741    7.8    https://vulners.com/nginx/NGINX:CVE-2022-41741
    |     3F71F065-66D4-541F-A813-9F1A2F2B1D91    8.8    https://vulners.com/...    *EXPLOIT*
    |     EDB-ID:50973    7.7    https://vulners.com/exploitdb/EDB-ID:50973    *EXPLOIT*
    """
    vulnerabilities = []
    current_software = None

    for line in block.split("\n"):
        line = line.strip().lstrip("|").lstrip("_").strip()
        if not line:
            continue

        # Track CPE or software version (e.g., "nginx 1.19.0:")
        if line.startswith("cpe:/") or (
            line.endswith(":") and not line.startswith("http")
        ):
            current_software = line.rstrip(":")
            continue

        # Parse vulners line - multiple formats:
        # 1. "CVE-2010-0425  10.0  https://..."
        # 2. "NGINX:CVE-2022-41741    7.8    https://..."
        # 3. "3F71F065-...    8.8    https://...    *EXPLOIT*"
        # 4. "EDB-ID:50973    7.7    https://..."

        # Generic pattern: ID  SCORE  URL  [*EXPLOIT*]
        vuln_match = re.match(r"(\S+)\s+(\d+\.?\d*)\s+(https?://\S+)", line)
        if vuln_match:
            vuln_id = vuln_match.group(1)
            cvss_score = float(vuln_match.group(2))
            ref_url = vuln_match.group(3)
            is_exploit = "*EXPLOIT*" in line

            # Extract CVE from various formats
            cve_ids = []
            cve_in_id = re.search(r"CVE-\d{4}-\d+", vuln_id, re.IGNORECASE)
            if cve_in_id:
                cve_ids.append(cve_in_id.group(0).upper())

            # Also check the URL for CVE
            cve_in_url = re.search(r"CVE-\d{4}-\d+", ref_url, re.IGNORECASE)
            if cve_in_url and cve_in_url.group(0).upper() not in cve_ids:
                cve_ids.append(cve_in_url.group(0).upper())

            # Determine title
            if cve_ids:
                title = f"{cve_ids[0]} (CVSS: {cvss_score})"
            elif is_exploit:
                title = f"Exploit {vuln_id} (CVSS: {cvss_score})"
            else:
                title = f"{vuln_id} (CVSS: {cvss_score})"

            # Include high-severity vulns (CVSS >= 7.0) and all exploits
            if cvss_score >= 7.0 or is_exploit:
                vulnerabilities.append(
                    {
                        "host_ip": host_ip,
                        "port": port,
                        "script": "vulners",
                        "title": title,
                        "state": "VULNERABLE",
                        "cve_ids": cve_ids,
                        "cvss_score": cvss_score,
                        "references": [ref_url],
                        "description": f"{'Exploit available: ' if is_exploit else ''}{vuln_id} detected via vulners database",
                        "software": current_software,
                        "is_exploit": is_exploit,
                    }
                )

    return vulnerabilities


def _parse_vuln_script_block(
    script_name: str, block: str, host_ip: str, port: int
) -> List[Dict[str, Any]]:
    """
    Parse a standard nmap vuln script block.

    Looks for VULNERABLE state and extracts CVE IDs, descriptions, references.
    """
    vulnerabilities = []

    # Check if this block indicates a vulnerability
    if "VULNERABLE" not in block.upper():
        return []

    # Split into individual vulnerability entries (some scripts report multiple)
    # Each vuln typically starts with a title line after VULNERABLE:
    vuln_sections = re.split(r"\|\s+VULNERABLE:", block, flags=re.IGNORECASE)

    for section in vuln_sections[1:]:  # Skip first empty part
        vuln = {
            "host_ip": host_ip,
            "port": port,
            "script": script_name,
            "title": None,
            "state": "VULNERABLE",
            "cve_ids": [],
            "cvss_score": None,
            "references": [],
            "description": "",
        }

        lines = section.strip().split("\n")
        description_parts = []

        for line in lines:
            line = line.strip().lstrip("|").lstrip("_").strip()

            if not line:
                continue

            # Extract title (first non-empty line after VULNERABLE:)
            if (
                not vuln["title"]
                and line
                and not line.startswith("State:")
                and not line.startswith("IDs:")
            ):
                vuln["title"] = line

            # Extract CVE IDs
            cve_matches = re.findall(
                r"CVE[:\s-]*(CVE-\d{4}-\d+|(\d{4}-\d+))", line, re.IGNORECASE
            )
            for match in cve_matches:
                cve = match[0] if match[0].startswith("CVE-") else f"CVE-{match[1]}"
                if cve not in vuln["cve_ids"]:
                    vuln["cve_ids"].append(cve)

            # Also check for CVE format without prefix
            simple_cve = re.findall(r"\bCVE-(\d{4}-\d+)\b", line)
            for cve_num in simple_cve:
                cve = f"CVE-{cve_num}"
                if cve not in vuln["cve_ids"]:
                    vuln["cve_ids"].append(cve)

            # Extract references
            if "http" in line.lower():
                urls = re.findall(r"https?://\S+", line)
                vuln["references"].extend(urls)

            # Build description (skip metadata lines)
            if (
                not line.startswith("State:")
                and not line.startswith("IDs:")
                and not line.startswith("References:")
            ):
                if line.startswith("Disclosure date:") or line.startswith(
                    "Check results:"
                ):
                    description_parts.append(line)
                elif vuln["title"] and line != vuln["title"]:
                    description_parts.append(line)

        vuln["description"] = " ".join(
            description_parts[:3]
        )  # First 3 lines of description

        # Generate title from script name if not found
        if not vuln["title"]:
            vuln["title"] = script_name.replace("-", " ").replace("_", " ").title()

        # Add CVE to title if found
        if vuln["cve_ids"] and vuln["cve_ids"][0] not in vuln["title"]:
            vuln["title"] = f"{vuln['cve_ids'][0]} - {vuln['title']}"

        if vuln["title"]:
            vulnerabilities.append(vuln)

    return vulnerabilities


def parse_nmap_text(output: str) -> Dict[str, Any]:
    """
    Parse nmap text output into structured data.

    Returns:
        {
            'hosts': [
                {
                    'ip': '10.0.0.5',
                    'hostname': 'example.com',
                    'status': 'up',
                    'os': 'Linux 5.x',
                    'services': [
                        {'port': 22, 'protocol': 'tcp', 'state': 'open', 'service': 'ssh', 'version': 'OpenSSH 8.2'}
                    ]
                }
            ]
        }
    """
    hosts = []
    domains = []  # Track AD domains discovered from LDAP/SMB banners
    current_host = None

    lines = output.split("\n")

    for line in lines:
        line = line.strip()

        # Extract AD domain from LDAP/SMB banners like:
        # "Microsoft Windows Active Directory LDAP (Domain: active.htb, Site: Default-First-Site-Name)"
        # Note: Nmap's LDAP scripts sometimes incorrectly append digits to domain names
        # (e.g., "baby.vl0." instead of "baby.vl"). Clean up these artifacts.
        domain_match = re.search(r"\(Domain:\s*([^,\)]+)", line)
        if domain_match:
            domain_name = domain_match.group(1).strip()
            # Strip trailing dots (FQDN format) and trailing digits that are nmap artifacts
            # Pattern: strip trailing digits followed by optional dot (e.g., "baby.vl0." → "baby.vl")
            domain_name = re.sub(r"\d+\.?$", "", domain_name).rstrip(".")
            if domain_name and not any(d["domain"] == domain_name for d in domains):
                domains.append(
                    {
                        "domain": domain_name,
                        "ip": current_host.get("ip") if current_host else None,
                        "source": "nmap_banner",
                    }
                )

        # Parse host line: "Nmap scan report for 10.0.0.5" or "Nmap scan report for example.com (10.0.0.5)"
        # Also handles: "Nmap scan report for 10.0.0.5 [host down, received no-response]"
        if line.startswith("Nmap scan report for"):
            if current_host and current_host not in hosts:
                hosts.append(current_host)

            # Extract IP and hostname, removing any trailing status info like [host down...]
            # Remove the [host down...] part first
            clean_line = re.sub(r"\s*\[host.*?\].*$", "", line)

            # Extract IP and hostname
            match = re.search(r"for (.+?)(?:\s+\((.+?)\))?$", clean_line)
            if match:
                target = match.group(1)
                paren_content = match.group(2)

                # Determine if target is IP or hostname
                if re.match(r"^\d+\.\d+\.\d+\.\d+$", target):
                    ip = target
                    hostname = paren_content if paren_content else None
                else:
                    hostname = target
                    ip = paren_content if paren_content else None

                # Check if this host already exists (e.g., from "Discovered open port" lines)
                existing_host = None
                for h in hosts:
                    if h.get("ip") == ip:
                        existing_host = h
                        break

                if existing_host:
                    # Use existing host and update hostname if needed
                    current_host = existing_host
                    if hostname and not current_host.get("hostname"):
                        current_host["hostname"] = hostname
                else:
                    current_host = {
                        "ip": ip,
                        "hostname": hostname,
                        "status": "unknown",
                        "os": None,
                        "mac_address": None,
                        "os_accuracy": None,
                        "services": [],
                    }

            # Check if the line indicates host is down
            if "[host down" in line and current_host:
                current_host["status"] = "down"

        # Parse host status
        elif "Host is up" in line and current_host:
            current_host["status"] = "up"

        elif "Host is down" in line and current_host:
            current_host["status"] = "down"

        # Parse "Skipping host" (host timeout) - still mark as up since we got some response
        elif "Skipping host" in line and "due to host timeout" in line:
            # Extract the IP from the line
            match = re.search(r"Skipping host (\d+\.\d+\.\d+\.\d+)", line)
            if match:
                skip_ip = match.group(1)
                # Find the host with this IP and mark it (it may have discovered ports)
                for h in hosts:
                    if h.get("ip") == skip_ip:
                        h["status"] = "up"  # Host responded, just timed out
                        break
                if current_host and current_host.get("ip") == skip_ip:
                    current_host["status"] = "up"

        # Parse "Discovered open port" lines (shown during scan, before timeout)
        # Format: "Discovered open port 443/tcp on 10.0.0.48"
        elif "Discovered open port" in line:
            match = re.search(
                r"Discovered open port (\d+)/(tcp|udp) on (\d+\.\d+\.\d+\.\d+)", line
            )
            if match:
                port = int(match.group(1))
                protocol = match.group(2)
                host_ip = match.group(3)

                # Find or create host entry for this IP
                target_host = None
                for h in hosts:
                    if h.get("ip") == host_ip:
                        target_host = h
                        break

                if (
                    not target_host
                    and current_host
                    and current_host.get("ip") == host_ip
                ):
                    target_host = current_host
                elif not target_host:
                    # Create a new host entry
                    target_host = {
                        "ip": host_ip,
                        "hostname": None,
                        "status": "up",
                        "os": None,
                        "mac_address": None,
                        "os_accuracy": None,
                        "services": [],
                    }
                    hosts.append(target_host)

                # Check if we already have this port
                existing = False
                for svc in target_host["services"]:
                    if svc["port"] == port and svc["protocol"] == protocol:
                        existing = True
                        break

                if not existing:
                    # Infer service name from common ports
                    service_name = None
                    if port == 80:
                        service_name = "http"
                    elif port == 443:
                        service_name = "https"
                    elif port == 22:
                        service_name = "ssh"
                    elif port == 21:
                        service_name = "ftp"
                    elif port == 23:
                        service_name = "telnet"
                    elif port == 25:
                        service_name = "smtp"
                    elif port == 53:
                        service_name = "domain"
                    elif port == 445:
                        service_name = "microsoft-ds"
                    elif port == 139:
                        service_name = "netbios-ssn"
                    elif port == 3306:
                        service_name = "mysql"
                    elif port == 5432:
                        service_name = "postgresql"

                    target_host["services"].append(
                        {
                            "port": port,
                            "protocol": protocol,
                            "state": "open",
                            "service": service_name,
                            "product": None,
                            "version": None,
                            "raw_version": None,
                        }
                    )

        # Parse service line: "22/tcp   open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.1"
        elif re.match(r"^\d+/(tcp|udp)", line) and current_host:
            parts = line.split(None, 4)  # Split on whitespace, max 5 parts
            if len(parts) >= 3:
                port_proto = parts[0].split("/")
                port = int(port_proto[0])
                protocol = port_proto[1] if len(port_proto) > 1 else "tcp"
                state = parts[1]
                service_name = parts[2] if len(parts) > 2 else None

                # Everything after service name is version info
                raw_version = " ".join(parts[3:]) if len(parts) > 3 else None

                # Parse product and version from raw version string
                product = None
                version = None

                if raw_version:
                    try:
                        # Remove nmap metadata: "syn-ack ttl XX", "reset ttl XX", etc.
                        cleaned = raw_version
                        # Handle various nmap scan type prefixes
                        metadata_prefixes = [
                            "syn-ack",
                            "reset",
                            "conn-refused",
                            "no-response",
                        ]
                        for prefix in metadata_prefixes:
                            if cleaned.lower().startswith(prefix):
                                parts_ver = cleaned.split()
                                # Skip prefix and "ttl XX" if present
                                if len(parts_ver) > 1 and "ttl" in parts_ver:
                                    try:
                                        ttl_idx = parts_ver.index("ttl")
                                        cleaned = " ".join(
                                            parts_ver[ttl_idx + 2 :]
                                        )  # Skip "ttl XX"
                                    except (ValueError, IndexError):
                                        cleaned = " ".join(
                                            parts_ver[1:]
                                        )  # Skip just prefix
                                else:
                                    cleaned = " ".join(
                                        parts_ver[1:]
                                    )  # Skip just prefix
                                break

                        # Extract product and version with multiple patterns
                        # Pattern: "ProductName version.number rest of string"
                        # Examples:
                        #   "ProFTPD 1.3.5" → product="ProFTPD", version="1.3.5"
                        #   "Apache httpd 2.4.7 ((Ubuntu))" → product="Apache httpd", version="2.4.7"
                        #   "OpenSSH 6.6.1p1 Ubuntu 2ubuntu2.13" → product="OpenSSH", version="6.6.1p1"

                        version_patterns = [
                            r"([A-Za-z][\w\s\-\.]+?)\s+(v?\d+[\.\d]+[\w\-\.]*)",  # Standard
                            r"^([A-Za-z][\w\-]+)\s+(\d[\w\.\-]+)",  # ProductName vX.Y.Z
                            r"^([A-Za-z][\w\s]+?)\s+v?(\d+(?:\.\d+)+)",  # "Product Name 1.2.3"
                        ]

                        matched = False
                        for pattern in version_patterns:
                            match = re.search(pattern, cleaned)
                            if match:
                                product = match.group(1).strip()
                                version = match.group(2).strip()
                                matched = True
                                break

                        if not matched:
                            # Fallback: use cleaned string as version, service as product
                            product = service_name
                            version = cleaned.strip() if cleaned.strip() else None
                    except Exception:
                        # If version parsing fails, use raw values
                        product = service_name
                        version = raw_version

                # Fallback: If service is unknown but port is a common web port, assume HTTP
                # This handles cases where nmap misidentifies or can't fingerprint web apps
                # Common misidentifications: ppp (port 3000), upnp (port 8000), tcpwrapped
                # Note: nmap adds "?" suffix for uncertain matches (e.g., "ppp?")
                # Port 11434 is Ollama API - runs HTTP but nmap often identifies as "unknown"
                common_web_ports = [3000, 8080, 8000, 8888, 9090, 11434]
                misidentified_services = [
                    "unknown",
                    "tcpwrapped",
                    "ppp",
                    "ppp?",
                    "upnp",
                    "upnp?",
                    None,
                ]
                if (
                    service_name in misidentified_services or not service_name
                ) and port in common_web_ports:
                    service_name = "http"
                    if not product:
                        product = "http"

                # Check if we already have this port (from "Discovered open port" lines)
                existing_svc = None
                for svc in current_host["services"]:
                    if svc["port"] == port and svc["protocol"] == protocol:
                        existing_svc = svc
                        break

                if existing_svc:
                    # Update existing entry with richer info from port table
                    existing_svc["state"] = state
                    if service_name:
                        existing_svc["service"] = service_name
                    if product:
                        existing_svc["product"] = product
                    if version:
                        existing_svc["version"] = version
                    if raw_version:
                        existing_svc["raw_version"] = raw_version
                else:
                    current_host["services"].append(
                        {
                            "port": port,
                            "protocol": protocol,
                            "state": state,
                            "service": service_name,
                            "product": product,
                            "version": version,
                            "raw_version": raw_version,
                        }
                    )

        # Parse OS detection: "Running: Linux 4.X|5.X" or "OS details: Linux 5.4"
        elif ("Running:" in line or "OS details:" in line) and current_host:
            os_info = line.split(":", 1)[1].strip()
            current_host["os"] = os_info

        # Parse MAC address: "MAC Address: 00:11:22:33:44:55 (Vendor)"
        elif "MAC Address:" in line and current_host:
            match = re.search(r"MAC Address:\s+([0-9A-Fa-f:]{17})", line)
            if match:
                current_host["mac_address"] = match.group(1)

        # Parse OS with confidence: "OS: Linux 5.x (95%)"
        elif line.startswith("OS:") and current_host:
            match = re.search(r"OS:\s+(.+?)\s+\((\d+)%\)", line)
            if match:
                current_host["os"] = match.group(1).strip()
                current_host["os_accuracy"] = int(match.group(2))

        # Parse OS from Service Info line: "Service Info: OSs: Windows, Windows Server 2008 R2 - 2012"
        elif "Service Info:" in line and "OSs:" in line and current_host:
            match = re.search(r"OSs?:\s+([^;]+)", line)
            if match:
                os_info = match.group(1).strip()
                # Only update if we don't already have more specific OS info
                if not current_host.get("os"):
                    current_host["os"] = os_info

        # Parse OS from Service Info line: "Service Info: OS: Linux"
        elif (
            "Service Info:" in line
            and "OS:" in line
            and "OSs:" not in line
            and current_host
        ):
            match = re.search(r"OS:\s+([^;,]+)", line)
            if match:
                os_info = match.group(1).strip()
                # Only update if we don't already have more specific OS info
                if not current_host.get("os"):
                    current_host["os"] = os_info

        # Parse hostname from Service Info: "Service Info: Host: VAGRANT-2008R2"
        elif "Service Info:" in line and "Host:" in line and current_host:
            match = re.search(r"Host:\s+([^\s;,]+)", line)
            if match:
                hostname = match.group(1).strip()
                # Only update if we don't already have a hostname
                if not current_host.get("hostname"):
                    current_host["hostname"] = hostname

        # Parse OS from SMB script: "|   OS: Windows Server 2008 R2 Standard 7601 Service Pack 1"
        elif line.strip().startswith("|") and "OS:" in line and current_host:
            # This is from smb-os-discovery script - more detailed than Service Info
            match = re.search(r"\|\s+OS:\s+(.+?)(?:\s+\(|$)", line)
            if match:
                os_info = match.group(1).strip()
                # SMB OS discovery is very accurate, so always update
                if (
                    os_info and os_info != "Windows"
                ):  # Don't overwrite with generic "Windows"
                    current_host["os"] = os_info
                    current_host["os_accuracy"] = (
                        95  # High confidence for SMB detection
                    )

    # Don't forget the last host (if not already added)
    if current_host and current_host not in hosts:
        hosts.append(current_host)

    # Parse vulnerability scripts (--script vuln output)
    vulnerabilities = parse_nmap_vuln_scripts(output)

    # Parse info scripts (vnc-info, ssh-hostkey, etc.)
    info_scripts = parse_nmap_info_scripts(output)

    return {
        "hosts": hosts,
        "vulnerabilities": vulnerabilities,
        "info_scripts": info_scripts,
        "domains": domains,
    }


def parse_nmap_info_scripts(output: str) -> List[Dict[str, Any]]:
    """
    Parse nmap info script output (non-vulnerability scripts).

    Extracts results from scripts like vnc-info, ssh-hostkey, etc.
    These provide useful information that should be captured as findings.

    Returns:
        List of info findings with:
        - host_ip: IP address
        - port: Port number
        - script: Script name
        - title: Finding title
        - severity: Always 'info' for info scripts
        - description: Script output content
    """
    findings = []
    current_host_ip = None
    current_port = None

    lines = output.split("\n")
    i = 0

    # Info scripts to capture (add more as needed)
    info_scripts = {
        "vnc-info": "VNC Server Information",
        "ssh-hostkey": "SSH Host Key",
        "http-server-header": "HTTP Server Header",
        "ssl-cert": "SSL Certificate",
        "http-title": "HTTP Page Title",
        "smb-os-discovery": "SMB OS Discovery",
        "rdp-ntlm-info": "RDP NTLM Information",
    }

    while i < len(lines):
        line = lines[i]

        # Track current host - "Nmap scan report for 10.0.0.73"
        if line.startswith("Nmap scan report for"):
            match = re.search(r"for (\d+\.\d+\.\d+\.\d+)", line)
            if match:
                current_host_ip = match.group(1)
            else:
                # Try hostname (IP in parens)
                match = re.search(r"\((\d+\.\d+\.\d+\.\d+)\)", line)
                if match:
                    current_host_ip = match.group(1)

        # Track current port - "80/tcp   open  http"
        elif re.match(r"^\d+/(tcp|udp)", line):
            parts = line.split()
            if parts:
                port_proto = parts[0].split("/")
                current_port = int(port_proto[0])

        # Parse info script blocks
        elif line.startswith("| ") and ":" in line and current_host_ip:
            # Could be start of a script block like "| vnc-info:"
            script_match = re.match(r"\|\s*([a-zA-Z0-9_-]+):\s*$", line)
            if script_match:
                script_name = script_match.group(1)

                # Only process info scripts we care about
                if script_name in info_scripts:
                    # Collect all lines of this script block
                    script_lines = []
                    i += 1
                    while i < len(lines) and (
                        lines[i].startswith("|") or lines[i].startswith("|_")
                    ):
                        # Clean up the line
                        clean_line = lines[i].lstrip("|").lstrip("_").strip()
                        if clean_line:
                            script_lines.append(clean_line)
                        if lines[i].startswith("|_"):
                            break
                        i += 1

                    if script_lines:
                        findings.append(
                            {
                                "host_ip": current_host_ip,
                                "port": current_port,
                                "script": script_name,
                                "title": info_scripts[script_name],
                                "severity": "info",
                                "description": "\n".join(script_lines),
                            }
                        )
                    continue

        i += 1

    return findings


def parse_nmap_output(content: str, target: str = "") -> Dict[str, Any]:
    """
    Wrapper for parse_nmap_text that matches the display interface.

    Args:
        content: Raw nmap output text
        target: Target from job (unused, for interface compatibility)

    Returns:
        Parsed nmap data structure
    """
    return parse_nmap_text(content)


def parse_nmap_log(log_path: str) -> Dict[str, Any]:
    """
    Parse an nmap log file.

    Args:
        log_path: Path to nmap log file

    Returns:
        Parsed nmap data with hosts, services, and vulnerabilities
    """
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        return parse_nmap_text(content)
    except FileNotFoundError:
        return {
            "hosts": [],
            "vulnerabilities": [],
            "error": f"File not found: {log_path}",
        }
    except Exception as e:
        return {"hosts": [], "vulnerabilities": [], "error": str(e)}
