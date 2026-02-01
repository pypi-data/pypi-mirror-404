#!/usr/bin/env python3
"""
souleyez.parsers.msf_parser - Parse Metasploit auxiliary module output
"""

import re
from typing import Any, Dict


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes and other terminal control sequences from text."""
    # Pattern 1: Standard ANSI escape sequences
    text = re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", text)
    # Pattern 2: OSC sequences (Operating System Command)
    text = re.sub(r"\x1B\].*?\x07", "", text)
    # Pattern 3: Simple color codes
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    # Pattern 4: Carriage returns and other control chars (except newlines)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text


def parse_msf_ssh_version(output: str, target: str) -> Dict[str, Any]:
    """
    Parse MSF ssh_version module output.

    Returns:
        {
            'services': [],  # Service info (version, etc.)
            'findings': []   # Security findings (deprecated crypto, etc.)
        }
    """
    services = []
    findings = []

    # Strip ANSI color codes first
    clean_output = strip_ansi_codes(output)

    # Extract SSH version
    version_match = re.search(r"SSH server version:\s*(.+)", clean_output)
    if version_match:
        ssh_version = version_match.group(1).strip()

        # Extract just the version number and product
        # e.g., "SSH-2.0-OpenSSH_4.7p1 Debian-8ubuntu1"
        product_match = re.search(r"SSH-[\d.]+-(\S+)", ssh_version)
        if product_match:
            product = product_match.group(1)

            services.append(
                {
                    "port": 22,
                    "protocol": "tcp",
                    "service_name": "ssh",
                    "service_version": product,
                }
            )

    # Extract OS information
    os_version = None
    os_match = re.search(r"os\.version\s+(.+)", clean_output)
    if os_match:
        os_version = os_match.group(1).strip()

    os_vendor = None
    vendor_match = re.search(r"os\.vendor\s+(.+)", clean_output)
    if vendor_match:
        os_vendor = vendor_match.group(1).strip()

    if os_vendor and os_version:
        findings.append(
            {
                "title": f"SSH OS Detection: {os_vendor} {os_version}",
                "severity": "info",
                "description": f"SSH banner reveals OS: {os_vendor} {os_version}",
                "port": 22,
                "service": "ssh",
            }
        )

    # Extract deprecated encryption algorithms
    deprecated_algos = []
    for line in clean_output.split("\n"):
        if "Deprecated" in line and "encryption.encryption" in line:
            # Extract algorithm name
            parts = line.split()
            if len(parts) >= 2:
                algo = parts[1]
                deprecated_algos.append(algo)

    if deprecated_algos:
        findings.append(
            {
                "title": "SSH Deprecated Encryption Algorithms",
                "severity": "medium",
                "description": f'SSH server supports deprecated encryption: {", ".join(deprecated_algos[:5])}{"..." if len(deprecated_algos) > 5 else ""}',
                "port": 22,
                "service": "ssh",
            }
        )

    # Extract deprecated HMAC algorithms
    deprecated_hmac = []
    for line in clean_output.split("\n"):
        if "Deprecated" in line and "encryption.hmac" in line:
            parts = line.split()
            if len(parts) >= 2:
                algo = parts[1]
                deprecated_hmac.append(algo)

    if deprecated_hmac:
        findings.append(
            {
                "title": "SSH Deprecated HMAC Algorithms",
                "severity": "low",
                "description": f'SSH server supports deprecated HMAC: {", ".join(deprecated_hmac[:3])}{"..." if len(deprecated_hmac) > 3 else ""}',
                "port": 22,
                "service": "ssh",
            }
        )

    # Extract weak key exchange methods
    weak_kex = []
    for line in clean_output.split("\n"):
        if "Deprecated" in line and "encryption.key_exchange" in line:
            parts = line.split()
            if len(parts) >= 2:
                algo = parts[1]
                weak_kex.append(algo)

    if weak_kex:
        findings.append(
            {
                "title": "SSH Weak Key Exchange Methods",
                "severity": "medium",
                "description": f'SSH server supports weak key exchange: {", ".join(weak_kex)}',
                "port": 22,
                "service": "ssh",
            }
        )

    return {"services": services, "findings": findings}


def parse_msf_mysql_login(output: str, target: str) -> Dict[str, Any]:
    """
    Parse MySQL login scanner output.

    Extracts MySQL version info and any successful logins.

    Returns:
        {
            'services': [],     # MySQL service with version
            'findings': [],     # Version detection + any successful logins
            'credentials': []   # Valid credentials if found
        }
    """
    services = []
    findings = []
    credentials = []
    clean_output = strip_ansi_codes(output)

    # Check if scan was skipped due to unsupported version
    # MSF still reports "credential was successful" even when skipped, which is misleading
    scan_skipped = (
        "Unsupported target version" in clean_output and "Skipping" in clean_output
    )

    if scan_skipped:
        findings.append(
            {
                "title": "MySQL Login Scan Skipped",
                "severity": "info",
                "description": "MySQL version is unsupported by the mysql_login module. The target may be running a very old or very new MySQL version.",
                "port": 3306,
                "service": "mysql",
            }
        )

    # Extract MySQL version
    # Format: [+] 10.0.0.73:3306 - 10.0.0.73:3306 - Found remote MySQL version 5.0.51a
    version_pattern = r"\[\+\]\s+([\d.]+):(\d+).*Found remote MySQL version\s+(\S+)"
    version_match = re.search(version_pattern, clean_output)

    if version_match:
        ip = version_match.group(1)
        port = int(version_match.group(2))
        mysql_version = version_match.group(3)

        services.append(
            {
                "port": port,
                "protocol": "tcp",
                "service_name": "mysql",
                "service_version": f"MySQL {mysql_version}",
            }
        )

        findings.append(
            {
                "title": f"MySQL Version Detected: {mysql_version}",
                "severity": "info",
                "description": f"MySQL server version {mysql_version} detected.",
                "port": port,
                "service": "mysql",
            }
        )

    # Check for successful logins
    # Format: [+] 10.0.0.73:3306 - 10.0.0.73:3306 - Success: 'root:password'
    # Format: [+] 10.0.0.73:3306 - Login Successful: root:password@database
    success_patterns = [
        r'\[\+\]\s+[\d.]+:(\d+).*Success:\s+[\'"]?([^:\'\"]+):([^\'\"@\s]+)',
        r"\[\+\]\s+[\d.]+:(\d+).*Login Successful:\s+([^:]+):([^@\s]+)",
    ]

    seen_creds = set()
    for pattern in success_patterns:
        for match in re.finditer(pattern, clean_output):
            port = int(match.group(1))
            username = match.group(2)
            password = match.group(3)

            cred_key = (port, username, password)
            if cred_key not in seen_creds:
                seen_creds.add(cred_key)

                findings.append(
                    {
                        "title": "MySQL Valid Credentials Found",
                        "severity": "critical",
                        "description": f"Valid MySQL credentials: {username}:{password}",
                        "port": port,
                        "service": "mysql",
                    }
                )

                credentials.append(
                    {
                        "username": username,
                        "password": password,
                        "service": "mysql",
                        "port": port,
                        "status": "valid",
                    }
                )

    # Check for newer MSF format: "Bruteforce completed, X credential was successful"
    # This format doesn't show the actual credential in logs
    # IMPORTANT: Skip this if scan was skipped - MSF incorrectly reports success for pre-existing creds
    bruteforce_pattern = (
        r"\[\*\]\s+[\d.]+:(\d+).*Bruteforce completed,\s*(\d+)\s+credential.*successful"
    )
    bf_match = re.search(bruteforce_pattern, clean_output)
    if (
        bf_match and not credentials and not scan_skipped
    ):  # Only if we didn't find explicit credentials AND scan wasn't skipped
        port = int(bf_match.group(1))
        num_creds = int(bf_match.group(2))
        findings.append(
            {
                "title": f"MySQL Credentials Found ({num_creds} valid)",
                "severity": "critical",
                "description": f'{num_creds} valid MySQL credential(s) discovered. Run "creds" command in msfconsole to view credentials.',
                "port": port,
                "service": "mysql",
            }
        )

    return {"services": services, "findings": findings, "credentials": credentials}


def parse_msf_login_success(output: str, target: str, module: str) -> Dict[str, Any]:
    """
    Parse MSF login module output for successful authentication.

    Returns:
        {
            'findings': [],     # Successful login attempts
            'credentials': [],  # Credential objects
            'sessions': []      # Session info if created
        }
    """
    findings = []
    credentials = []
    sessions = []

    # Strip ANSI color codes first
    clean_output = strip_ansi_codes(output)

    # Determine service name from module
    service = "unknown"
    if "ssh" in module:
        service = "ssh"
    elif "telnet" in module:
        service = "telnet"
    elif "mysql" in module:
        service = "mysql"
    elif "postgres" in module:
        service = "postgresql"
    elif "vnc" in module:
        service = "vnc"
    elif "rlogin" in module:
        service = "rlogin"
    elif "smb" in module:
        service = "smb"
    elif "rdp" in module:
        service = "rdp"
    elif "ftp" in module:
        service = "ftp"

    seen_creds = set()  # Avoid duplicates

    # Pattern 1: [+] 10.0.0.82:22 - Success: 'username:password' 'additional info'
    # Also handles: [+] 10.0.0.82:22 - Success: "username:password"
    success_pattern1 = (
        r'\[\+\]\s+[\d.]+:(\d+)\s+-\s+Success:\s+[\'"]([^:]+):([^\'\"]+)[\'"]'
    )

    # Pattern 2: [+] IP:PORT - IP:PORT - Login Successful: user:pass@database
    # Note: MSF often outputs IP:PORT twice. Using .* to handle both cases.
    success_pattern2 = r"\[\+\]\s+[\d.]+:(\d+).*Login Successful:\s+([^:]*):([^@\s]+)"

    # Pattern 3: VNC format [+] 10.0.0.73:5900 - 10.0.0.73:5900 - Login Successful: :password
    # Note: VNC often has empty username
    success_pattern3 = r"\[\+\]\s+[\d.]+:(\d+).*Login Successful:\s*:(\S+)"

    # Pattern 4: Telnet format [+] 192.168.2.230:23 - 192.168.2.230:23 - msfadmin:msfadmin login: Login OK
    # MSF telnet_login uses "username:password login: Login OK" format
    success_pattern_telnet = (
        r"\[\+\]\s+[\d.]+:(\d+).*-\s+([^:\s]+):([^\s]+)\s+login:\s+Login OK"
    )

    # Pattern 5: Flexible [+] with credentials anywhere (fallback)
    # Handles: [+] 10.0.0.82:22 Found credentials: user:pass
    success_pattern_flexible = r'\[\+\]\s+[\d.]+:(\d+).*(?:credential|found|valid).*?[\'"]?([^:\s\'\"]+):([^\'\"@\s]+)[\'"]?'

    # Pattern 6: RDP format [+] 10.0.0.82:3389 - DOMAIN\user:password - Success
    success_pattern_rdp = (
        r"\[\+\]\s+[\d.]+:(\d+).*?([^\\:\s]+\\)?([^:\s]+):([^\s-]+)\s*-\s*Success"
    )

    # Try pattern 3 first (VNC with empty username)
    for match in re.finditer(success_pattern3, clean_output):
        port = int(match.group(1))
        password = match.group(2)
        username = ""  # VNC typically has no username

        cred_key = (port, username, password)
        if cred_key not in seen_creds:
            seen_creds.add(cred_key)

            findings.append(
                {
                    "title": f"{service.upper()} Valid Credentials Found",
                    "severity": "critical",
                    "description": f"Valid {service} password found (no username required): {password}",
                    "port": port,
                    "service": service,
                }
            )

            credentials.append(
                {
                    "username": username,
                    "password": password,
                    "service": service,
                    "port": port,
                    "status": "valid",
                }
            )

    # Try other patterns (username:password style)
    for pattern in [
        success_pattern1,
        success_pattern2,
        success_pattern_telnet,
        success_pattern_flexible,
    ]:
        for match in re.finditer(pattern, clean_output, re.IGNORECASE):
            port = int(match.group(1))
            username = match.group(2)
            password = match.group(3)

            cred_key = (port, username, password)
            if cred_key not in seen_creds:
                seen_creds.add(cred_key)

                findings.append(
                    {
                        "title": f"{service.upper()} Valid Credentials Found",
                        "severity": "critical",
                        "description": f"Valid {service} credentials: {username}:{password}",
                        "port": port,
                        "service": service,
                    }
                )

                credentials.append(
                    {
                        "username": username,
                        "password": password,
                        "service": service,
                        "port": port,
                        "status": "valid",
                    }
                )

    # Check for session opened (login modules can spawn sessions)
    # Format: [*] Command shell session 1 opened (192.168.1.224:37125 -> 192.168.1.240:23)
    session_pattern = (
        r"\[\*\]\s+(Command shell|Meterpreter)\s+session\s+(\d+)\s+opened\s+\(([^)]+)\)"
    )
    for match in re.finditer(session_pattern, clean_output, re.IGNORECASE):
        session_type = match.group(1)
        session_id = match.group(2)
        tunnel = match.group(3)

        sessions.append(
            {
                "id": session_id,
                "type": session_type.lower(),
                "tunnel": tunnel,
                "module": module,
            }
        )

        findings.append(
            {
                "title": f"{service.upper()} Session Opened",
                "severity": "critical",
                "description": f"{session_type} session {session_id} opened via {service} login. Tunnel: {tunnel}",
                "service": service,
                "data": {
                    "module": module,
                    "session_id": session_id,
                    "session_type": session_type.lower(),
                    "tunnel": tunnel,
                },
            }
        )

    # Check for newer MSF format: "Bruteforce completed, X credential was successful"
    # This format doesn't show the actual credential in logs
    if not credentials:  # Only if we didn't find explicit credentials
        bruteforce_pattern = r"\[\*\]\s+[\d.]+:?(\d*)\s*-?\s*Bruteforce completed,\s*(\d+)\s+credential.*successful"
        bf_match = re.search(bruteforce_pattern, clean_output)
        if bf_match:
            port = int(bf_match.group(1)) if bf_match.group(1) else None
            num_creds = int(bf_match.group(2))
            findings.append(
                {
                    "title": f"{service.upper()} Credentials Found ({num_creds} valid)",
                    "severity": "critical",
                    "description": f'{num_creds} valid {service} credential(s) discovered via bruteforce. Run "creds" command in msfconsole to view.',
                    "service": service,
                    "port": port,
                }
            )

    return {"findings": findings, "credentials": credentials, "sessions": sessions}


def parse_msf_smb_version(output: str, target: str) -> Dict[str, Any]:
    """
    Parse SMB version detection output.

    Returns:
        {
            'services': [],  # SMB service with version info
            'findings': []   # Findings (especially for known vulnerable versions)
        }
    """
    services = []
    findings = []
    clean_output = strip_ansi_codes(output)

    # Pattern 1: Host could not be identified: Unix (Samba 3.0.20-Debian)
    # Pattern 2: Host is running Windows 10 Pro (build 19041)
    # Pattern 3: SMB Detected (versions:1, 2, 3) (preferred dialect:SMB 3.1.1)
    # Pattern 4: [+] Host is running Version X.X.X (unknown OS)
    version_patterns = [
        # Samba detection - [*] 10.0.0.73:445 - Host could not be identified: Unix (Samba 3.0.20-Debian)
        r"\[\*\]\s+([\d.]+):(\d+)\s+-\s+Host could not be identified:\s+(\S+)\s+\(([^)]+)\)",
        # Windows detection - [*] 10.0.0.73:445 - Host is running Windows 10 Pro (build 19041)
        r"\[\*\]\s+([\d.]+):(\d+)\s+-\s+Host is running\s+(.+)",
        # Version detection with [+] - [+] 10.0.0.73:445 - Host is running Version 6.1.0 (unknown OS)
        r"\[\+\]\s+([\d.]+):(\d+)\s+-\s+Host is running\s+(.+)",
        # Generic SMB version - [+] 10.0.0.73:445 - SMB Detected...
        r"\[\+\]\s+([\d.]+):(\d+)\s+-\s+SMB Detected\s+(.+)",
        # SMB Detected with [*] - [*] 10.0.0.73:445 - SMB Detected (versions:1, 2, 3)
        r"\[\*\]\s+([\d.]+):(\d+)\s+-\s+SMB Detected\s+(.+)",
    ]

    smb_version = None
    os_info = None
    port = 445

    for pattern in version_patterns:
        match = re.search(pattern, clean_output)
        if match:
            port = int(match.group(2))
            if "could not be identified" in pattern:
                # Samba format: OS type and version in parens
                os_info = match.group(3)  # e.g., "Unix"
                smb_version = match.group(4)  # e.g., "Samba 3.0.20-Debian"
            else:
                # Windows/other format
                smb_version = match.group(3).strip()
            break

    if smb_version:
        services.append(
            {
                "port": port,
                "protocol": "tcp",
                "service_name": "smb",
                "service_version": smb_version,
            }
        )

        # Check for known vulnerable Samba versions
        vuln_samba_versions = {
            "Samba 3.0.20": (
                "CVE-2007-2447",
                "critical",
                "Samba username map script command injection",
            ),
            "Samba 3.0.21": (
                "CVE-2007-2447",
                "critical",
                "Samba username map script command injection",
            ),
            "Samba 3.0.22": (
                "CVE-2007-2447",
                "critical",
                "Samba username map script command injection",
            ),
            "Samba 3.0.23": (
                "CVE-2007-2447",
                "critical",
                "Samba username map script command injection",
            ),
            "Samba 3.0.24": (
                "CVE-2007-2447",
                "critical",
                "Samba username map script command injection",
            ),
            "Samba 3.0.25": (
                "CVE-2007-2447",
                "critical",
                "Samba username map script command injection",
            ),
            "Samba 3.5.0": (
                "CVE-2017-7494",
                "critical",
                "SambaCry/EternalRed remote code execution",
            ),
        }

        # Check if version matches any known vulnerable version
        for vuln_ver, (cve, severity, desc) in vuln_samba_versions.items():
            if vuln_ver in smb_version:
                findings.append(
                    {
                        "title": f"Vulnerable Samba Version ({cve})",
                        "severity": severity,
                        "description": f"{desc}. Detected version: {smb_version}",
                        "port": port,
                        "service": "smb",
                        "data": {"cve": cve, "version": smb_version},
                    }
                )
                break
        else:
            # No specific vulnerability, just report version as info
            findings.append(
                {
                    "title": f"SMB Version Detected: {smb_version}",
                    "severity": "info",
                    "description": f"SMB/Samba version detected: {smb_version}"
                    + (f" (OS: {os_info})" if os_info else ""),
                    "port": port,
                    "service": "smb",
                }
            )

    return {"services": services, "findings": findings}


def parse_msf_smb_enumshares(output: str, target: str) -> Dict[str, Any]:
    """
    Parse SMB share enumeration output.

    Returns:
        {
            'findings': []  # Discovered SMB shares
        }
    """
    findings = []
    clean_output = strip_ansi_codes(output)

    # Parse share lines
    # Format: [+] 10.0.0.82:445 - ADMIN$ - (DISK) Remote Admin
    # Format: [+] 10.0.0.82:445 - IPC$ - (IPC) Remote IPC
    share_pattern = r"\[\+\]\s+[\d.]+:(\d+)\s+-\s+(\S+)\s+-\s+\((\w+)\)\s*(.*)"

    shares = []
    for match in re.finditer(share_pattern, clean_output):
        port = int(match.group(1))
        share_name = match.group(2)
        share_type = match.group(3)
        comment = match.group(4).strip()

        shares.append(
            {"name": share_name, "type": share_type, "comment": comment, "port": port}
        )

    if shares:
        # Determine severity based on share types
        severity = "info"
        if any(s["name"] not in ["IPC$", "ADMIN$", "C$"] for s in shares):
            severity = "medium"  # Non-default shares found

        share_list = ", ".join([s["name"] for s in shares])
        findings.append(
            {
                "title": f"SMB Shares Discovered ({len(shares)} shares)",
                "severity": severity,
                "description": f"Found {len(shares)} SMB shares: {share_list}",
                "port": 445,
                "service": "smb",
                "data": {"shares": shares},
            }
        )

    return {"findings": findings}


def parse_msf_ssh_enumusers(output: str, target: str) -> Dict[str, Any]:
    """
    Parse SSH user enumeration output.

    Returns:
        {
            'findings': []  # Discovered SSH users
            'credentials': []  # Username-only credentials
            'status': str  # Optional status override (e.g., 'warning' for false positives)
            'warning': str  # Optional warning message
        }
    """
    findings = []
    credentials = []
    clean_output = strip_ansi_codes(output)
    result = {}

    # Check for false positive detection (module aborted)
    # Format: [-] 192.168.1.157:22 - SSH - throws false positive results. Aborting.
    if "false positive" in clean_output.lower() and "aborting" in clean_output.lower():
        result["status"] = "warning"
        result["warning"] = (
            "SSH user enumeration aborted: target throws false positive results"
        )
        result["findings"] = []
        result["credentials"] = []
        return result

    # Parse user enumeration results
    # Format: [+] 10.0.0.82:22 - SSH - User 'root' found
    # Format: [+] 10.0.0.82:22 - SSH - User 'admin' found
    user_pattern = r'\[\+\]\s+[\d.]+:(\d+)\s+-\s+SSH\s+-\s+User\s+[\'"]([^\'\"]+)[\'"]'

    users = []
    for match in re.finditer(user_pattern, clean_output):
        port = int(match.group(1))
        username = match.group(2)
        users.append(username)

        # Add as credential (username-only, no password)
        credentials.append(
            {
                "username": username,
                "password": "",  # Empty password for username-only
                "service": "ssh",
                "port": port,
                "status": "untested",  # Username discovered but not validated
            }
        )

    if users:
        user_list = ", ".join(users)
        findings.append(
            {
                "title": f"SSH Users Enumerated ({len(users)} users)",
                "severity": "medium",
                "description": f"Found {len(users)} SSH users: {user_list}",
                "port": 22,
                "service": "ssh",
                "data": {"users": users},
            }
        )

    result["findings"] = findings
    result["credentials"] = credentials
    return result


def parse_msf_kerberos_enumusers(output: str, target: str) -> Dict[str, Any]:
    """
    Parse Kerberos user enumeration output (kerberos_enumusers module).

    Returns:
        {
            'findings': []  # Discovered Kerberos users
            'credentials': []  # Username-only credentials
        }
    """
    findings = []
    credentials = []
    clean_output = strip_ansi_codes(output)

    # Parse valid usernames - MSF kerberos_enumusers format
    # Format: [+] 10.129.234.72 - User: "administrator" is present
    # Format: [+] 10.129.234.72 - User: "guest" is present
    valid_pattern = r'\[\+\]\s+[\d.]+\s+-\s+User:\s+"([^"]+)"\s+is present'

    users = []
    port = 88  # Kerberos port

    for match in re.finditer(valid_pattern, clean_output, re.IGNORECASE):
        username = match.group(1)
        if username not in users:
            users.append(username)

            # Add as credential (username-only, no password)
            credentials.append(
                {
                    "username": username,
                    "password": "",  # Empty password for username-only
                    "service": "kerberos",
                    "port": port,
                    "status": "untested",  # Username discovered but not validated
                }
            )

    if users:
        user_list = ", ".join(users)
        findings.append(
            {
                "title": f"Kerberos Users Enumerated ({len(users)} users)",
                "severity": "medium",
                "description": f"Found {len(users)} valid Kerberos users: {user_list}",
                "port": port,
                "service": "kerberos",
                "data": {"users": users},
            }
        )

    return {"findings": findings, "credentials": credentials}


def parse_msf_smtp_enum(output: str, target: str) -> Dict[str, Any]:
    """
    Parse SMTP user enumeration output.

    Returns:
        {
            'findings': [],      # Discovered SMTP users
            'credentials': []    # Username credentials (no passwords)
        }
    """
    findings = []
    credentials = []
    clean_output = strip_ansi_codes(output)

    # Parse SMTP user enumeration (VRFY/EXPN/RCPT)
    # Format: [+] 10.0.0.82:25 - Users found: admin, root, user
    users = []

    # Method 1: Users found line
    users_found_pattern = r"Users found:\s*(.+)"
    match = re.search(users_found_pattern, clean_output)
    if match:
        user_list = match.group(1).strip()
        users = [u.strip() for u in user_list.split(",") if u.strip()]

    # Method 2: Individual user lines
    # Format: [+] 10.0.0.82:25 - Found user: root
    user_pattern = r"\[\+\]\s+[\d.]+:(\d+)\s+-\s+Found user:\s+(\S+)"
    for match in re.finditer(user_pattern, clean_output):
        username = match.group(2)
        if username not in users:
            users.append(username)

    if users:
        user_list = ", ".join(users)
        findings.append(
            {
                "title": f"SMTP Users Enumerated ({len(users)} users)",
                "severity": "medium",
                "description": f"Found {len(users)} SMTP users: {user_list}",
                "port": 25,
                "service": "smtp",
                "data": {"users": users},
            }
        )

        # Add each user as a credential (username only, no password)
        for username in users:
            credentials.append(
                {
                    "username": username,
                    "password": None,
                    "service": "smtp",
                    "port": 25,
                    "status": "enumerated",  # Not validated, just discovered
                }
            )

    return {"findings": findings, "credentials": credentials}


def parse_msf_ftp_anonymous(output: str, target: str) -> Dict[str, Any]:
    """
    Parse FTP anonymous access scanner output.

    Returns:
        {
            'findings': [],     # FTP anonymous access findings
            'credentials': []   # Anonymous credential
        }
    """
    findings = []
    credentials = []
    clean_output = strip_ansi_codes(output)

    # Pattern: [+] 10.0.0.73:21 - 10.0.0.73:21 - Anonymous READ (220 (vsFTPd 2.3.4))
    # Pattern: [+] 10.0.0.73:21 - Anonymous READ/WRITE (...)
    anon_pattern = r"\[\+\]\s+[\d.]+:(\d+).*Anonymous\s+(READ|WRITE|READ/WRITE)"

    for match in re.finditer(anon_pattern, clean_output, re.IGNORECASE):
        port = int(match.group(1))
        access_type = match.group(2).upper()

        severity = "high" if "WRITE" in access_type else "medium"

        findings.append(
            {
                "title": f"FTP Anonymous Access ({access_type})",
                "severity": severity,
                "description": f"FTP server allows anonymous access with {access_type} permissions. This may expose sensitive files.",
                "port": port,
                "service": "ftp",
            }
        )

        # Add anonymous credential
        credentials.append(
            {
                "username": "anonymous",
                "password": "anonymous@",
                "service": "ftp",
                "port": port,
                "status": "valid",
            }
        )

    return {"findings": findings, "credentials": credentials}


def parse_msf_nfs_mount(output: str, target: str) -> Dict[str, Any]:
    """
    Parse NFS mount enumeration output.

    Returns:
        {
            'findings': []  # Discovered NFS mounts
        }
    """
    findings = []
    clean_output = strip_ansi_codes(output)

    exports = []

    # Pattern 1: New MSF format
    # Format: [+] 10.0.0.73:111 - 10.0.0.73 Mountable NFS Export: / [*]
    export_pattern1 = r"\[\+\]\s+[\d.]+:(\d+)\s+-\s+[\d.]+\s+Mountable NFS Export:\s+(\S+)\s*(\[.*?\])?"
    for match in re.finditer(export_pattern1, clean_output):
        port = int(match.group(1))
        mount_path = match.group(2)
        permissions = match.group(3) or "*"

        exports.append(
            {"path": mount_path, "permissions": permissions.strip(), "port": port}
        )

    # Pattern 2: Old format
    # Format: [+] 10.0.0.82:111 - /home *
    # Format: [+] 10.0.0.82:2049 - /var/nfs *(rw,sync,no_subtree_check)
    if not exports:
        export_pattern2 = r"\[\+\]\s+[\d.]+:(\d+)\s+-\s+(/\S+)\s+(.*)"
        for match in re.finditer(export_pattern2, clean_output):
            port = int(match.group(1))
            mount_path = match.group(2)
            permissions = match.group(3).strip()

            exports.append(
                {"path": mount_path, "permissions": permissions, "port": port}
            )

    if exports:
        # Determine severity based on path and permissions
        severity = "medium"
        # Root export is always high severity
        if any(e["path"] == "/" for e in exports):
            severity = "high"
        elif any("rw" in e["permissions"] for e in exports):
            severity = "high"  # Writable mounts are more severe

        export_list = ", ".join([e["path"] for e in exports])
        findings.append(
            {
                "title": f"NFS Exports Discovered ({len(exports)} mounts)",
                "severity": severity,
                "description": f"Found {len(exports)} NFS exports: {export_list}",
                "port": 2049,
                "service": "nfs",
                "data": {"exports": exports},
            }
        )

    return {"findings": findings}


def parse_msf_java_rmi(output: str, target: str) -> Dict[str, Any]:
    """
    Parse Java RMI scanner output.

    Returns:
        {
            'findings': [],  # Java RMI findings
            'services': []   # RMI service info
        }
    """
    findings = []
    services = []
    clean_output = strip_ansi_codes(output)

    # Parse Java RMI detection
    # Format: [+] 10.0.0.82:1099 - Java RMI Endpoint Detected: Class Loader Enabled
    rmi_pattern = r"\[\+\]\s+([\d.]+):(\d+)\s+-\s+(.+)"

    for match in re.finditer(rmi_pattern, clean_output):
        ip = match.group(1)
        port = int(match.group(2))
        message = match.group(3).strip()

        # Check for specific vulnerabilities
        severity = "medium"
        if "Class Loader Enabled" in message:
            severity = "high"
            findings.append(
                {
                    "title": "Java RMI Class Loader Enabled",
                    "severity": severity,
                    "description": f"Java RMI endpoint with Class Loader enabled detected. This may allow remote code execution via deserialization attacks.",
                    "port": port,
                    "service": "java-rmi",
                }
            )
        elif "Endpoint Detected" in message:
            findings.append(
                {
                    "title": "Java RMI Endpoint Detected",
                    "severity": "medium",
                    "description": f"Java RMI endpoint detected: {message}",
                    "port": port,
                    "service": "java-rmi",
                }
            )

        # Add service info
        services.append(
            {
                "port": port,
                "protocol": "tcp",
                "service_name": "java-rmi",
                "service_version": "Java RMI Registry",
            }
        )

    return {"findings": findings, "services": services}


def parse_msf_vnc_auth(output: str, target: str) -> Dict[str, Any]:
    """
    Parse VNC authentication scanner output.

    Returns:
        {
            'findings': [],  # VNC findings
            'services': []   # VNC service info
        }
    """
    findings = []
    services = []
    clean_output = strip_ansi_codes(output)

    # Parse VNC security types
    # Format: [+] 10.0.0.82:5900 - VNC server security types supported: VNC
    # Format: [+] 10.0.0.82:5900 - VNC server security types supported: None
    vnc_pattern = (
        r"\[\+\]\s+([\d.]+):(\d+)\s+-\s+VNC server security types supported:\s*(.+)"
    )

    for match in re.finditer(vnc_pattern, clean_output):
        ip = match.group(1)
        port = int(match.group(2))
        sec_types = match.group(3).strip()

        # Check for no authentication
        if "None" in sec_types:
            findings.append(
                {
                    "title": "VNC No Authentication Required",
                    "severity": "critical",
                    "description": f"VNC server at port {port} allows connections without authentication. Security types: {sec_types}",
                    "port": port,
                    "service": "vnc",
                }
            )
        else:
            findings.append(
                {
                    "title": f"VNC Security Types Detected",
                    "severity": "info",
                    "description": f"VNC server security types: {sec_types}",
                    "port": port,
                    "service": "vnc",
                }
            )

        services.append(
            {
                "port": port,
                "protocol": "tcp",
                "service_name": "vnc",
                "service_version": f"Security: {sec_types}",
            }
        )

    # Also check for vnc_none_auth specific output
    # Format: [*] 10.0.0.82:5900 - VNC server protocol version: ...
    # Format: [+] 10.0.0.82:5900 - VNC server does not require authentication
    no_auth_pattern = (
        r"\[\+\]\s+([\d.]+):(\d+)\s+-\s+VNC server does not require authentication"
    )
    for match in re.finditer(no_auth_pattern, clean_output):
        ip = match.group(1)
        port = int(match.group(2))

        # Avoid duplicates
        if not any(
            f["port"] == port and "No Authentication" in f["title"] for f in findings
        ):
            findings.append(
                {
                    "title": "VNC No Authentication Required",
                    "severity": "critical",
                    "description": f"VNC server at port {port} does not require authentication.",
                    "port": port,
                    "service": "vnc",
                }
            )

    return {"findings": findings, "services": services}


def parse_msf_endpoint_mapper(output: str, target: str) -> Dict[str, Any]:
    """
    Parse MSF endpoint_mapper (RPC enumeration) output.

    The endpoint_mapper module discovers RPC endpoints which can reveal:
    - Services running on the target
    - Named pipes available for exploitation
    - Protocol bindings and UUIDs

    Returns:
        {
            'findings': [],  # RPC endpoint discoveries
            'services': []   # Services detected
        }
    """
    findings = []
    services = []
    clean_output = strip_ansi_codes(output)

    endpoints = []
    pipes = []
    service_names = []

    # Pattern for endpoint entries - actual MSF format:
    # [*] 10.129.48.183:135 - d95afe70-a6d5-4259-822e-2c84da1ddb0d v1.0 TCP (49152) 10.129.48.183
    # [*] 10.129.48.183:135 - 897e2e5f-93f3-4376-9c9c-fd2277495c27 v1.0 LRPC (...) [Frs2 Service]
    uuid_pattern = r"\[\*\]\s+[\d.]+:(\d+)\s+-\s+([a-f0-9-]{36})\s+v?([0-9.]+)\s+(\w+)\s+\([^)]+\)(?:\s+[\d.]+)?(?:\s+\[([^\]]+)\])?"
    for match in re.finditer(uuid_pattern, clean_output, re.IGNORECASE):
        port = int(match.group(1))
        uuid = match.group(2)
        version = match.group(3) or ""
        protocol = match.group(4)  # TCP, LRPC, PIPE, HTTP
        svc_name = match.group(5)  # Service name in brackets if present
        endpoints.append(
            {
                "uuid": uuid,
                "version": version,
                "protocol": protocol,
                "port": port,
                "service": svc_name,
            }
        )
        if svc_name and svc_name not in service_names:
            service_names.append(svc_name)

    # Pattern for PIPE entries specifically
    # [*] 10.129.48.183:135 - e3514235-4b06-11d1-ab04-00c04fc2dcd2 v4.0 PIPE (\pipe\lsass) \\DC [MS NT Directory DRS Interface]
    pipe_pattern = (
        r"\[\*\]\s+[\d.]+:(\d+)\s+-\s+[a-f0-9-]+\s+v?[0-9.]+\s+PIPE\s+\(([^)]+)\)"
    )
    for match in re.finditer(pipe_pattern, clean_output, re.IGNORECASE):
        port = int(match.group(1))
        pipe = match.group(2)
        if pipe not in pipes:
            pipes.append(pipe)

    # Also look for old format patterns as fallback
    # Format: [*] 10.0.0.1:135 - UUID: d95afe70-a6d5-4259-822e-2c84da1ddb0d v1.0
    old_uuid_pattern = (
        r"\[\*\]\s+[\d.]+:(\d+)\s+-\s+UUID:\s+([a-f0-9-]+)\s+v?([0-9.]+)?"
    )
    for match in re.finditer(old_uuid_pattern, clean_output, re.IGNORECASE):
        port = int(match.group(1))
        uuid = match.group(2)
        version = match.group(3) or ""
        if not any(e.get("uuid") == uuid for e in endpoints):
            endpoints.append({"uuid": uuid, "version": version, "port": port})

    # Pattern for [+] success lines (discovered services)
    success_pattern = r"\[\+\]\s+[\d.]+:(\d+)\s+-\s+(.+)"
    for match in re.finditer(success_pattern, clean_output):
        port = int(match.group(1))
        message = match.group(2).strip()
        if message and message not in [e.get("message") for e in endpoints]:
            endpoints.append({"message": message, "port": port})

    # Create findings if we discovered anything
    if endpoints or pipes or service_names:
        # Unique endpoints count
        unique_uuids = len(set(e.get("uuid", "") for e in endpoints if e.get("uuid")))
        desc_parts = []
        if unique_uuids:
            desc_parts.append(f"{unique_uuids} RPC UUIDs")
        if pipes:
            desc_parts.append(f"{len(pipes)} named pipes")
        if service_names:
            desc_parts.append(f"{len(service_names)} services")

        # Build description with discovered services
        description = f'RPC endpoint enumeration found: {", ".join(desc_parts)}.'
        if service_names:
            svc_list = ", ".join(service_names[:8])
            if len(service_names) > 8:
                svc_list += f"... (+{len(service_names) - 8} more)"
            description += f" Services: {svc_list}"
        if pipes:
            description += (
                f' Pipes: {", ".join(pipes[:5])}{"..." if len(pipes) > 5 else ""}'
            )

        findings.append(
            {
                "title": f'RPC Endpoints Discovered ({", ".join(desc_parts)})',
                "severity": "medium",  # Upgraded from info - this is useful recon
                "description": description,
                "port": 135,
                "service": "msrpc",
                "data": {
                    "endpoints": endpoints[:20],  # Limit for storage
                    "pipes": pipes,
                    "service_names": service_names,
                },
            }
        )

        # Add msrpc service
        services.append(
            {
                "port": 135,
                "protocol": "tcp",
                "service_name": "msrpc",
                "service_version": f"RPC ({len(endpoints)} endpoints)",
            }
        )

        # Check for interesting pipes that indicate attack vectors
        interesting_pipes = {
            "spoolss": ("Print Spooler", "medium", "PrintNightmare potential"),
            "samr": ("SAM Remote", "medium", "User enumeration possible"),
            "lsass": ("LSASS", "medium", "Domain/credential operations"),
            "lsarpc": ("LSA Remote", "medium", "Domain enumeration possible"),
            "netlogon": ("Netlogon", "high", "ZeroLogon check recommended"),
            "epmapper": ("Endpoint Mapper", "info", "RPC enumeration confirmed"),
            "protected_storage": (
                "Protected Storage",
                "medium",
                "Credential storage access",
            ),
        }

        found_interesting = set()
        for pipe in pipes:
            # Normalize pipe path - handles \pipe\lsass and \\pipe\\lsass formats
            pipe_lower = (
                pipe.lower().replace("\\pipe\\", "").replace("\\", "").replace("/", "")
            )
            for key, (name, sev, desc) in interesting_pipes.items():
                if key in pipe_lower and key not in found_interesting:
                    found_interesting.add(key)
                    findings.append(
                        {
                            "title": f"{name} Pipe Available",
                            "severity": sev,
                            "description": f"{desc}. Pipe: {pipe}",
                            "port": 135,
                            "service": "msrpc",
                        }
                    )

    return {"findings": findings, "services": services}


def parse_msf_ghostcat(output: str, target: str) -> Dict[str, Any]:
    """
    Parse Tomcat Ghostcat (CVE-2020-1938) scanner output.

    Returns:
        {
            'findings': []  # Ghostcat findings
        }
    """
    findings = []
    clean_output = strip_ansi_codes(output)

    # Look for file content (indicates successful file read)
    # Ghostcat returns file contents like web.xml
    has_xml_content = "<?xml" in clean_output or "<web-app" in clean_output
    has_file_content = "WEB-INF" in clean_output or "servlet" in clean_output.lower()

    # Check for explicit success messages
    # Format: [+] File contents retrieved successfully
    success_pattern = r"\[\+\]\s+(.+)"
    success_messages = re.findall(success_pattern, clean_output)

    if has_xml_content or has_file_content:
        findings.append(
            {
                "title": "Tomcat Ghostcat File Read (CVE-2020-1938)",
                "severity": "high",
                "description": "Successfully read file contents via Tomcat AJP connector. This confirms CVE-2020-1938 vulnerability allowing arbitrary file read from the web application directory.",
                "port": 8009,
                "service": "ajp13",
                "data": {"evidence": "XML/file content returned in response"},
            }
        )
    elif success_messages:
        for msg in success_messages:
            if "File" in msg or "content" in msg.lower():
                findings.append(
                    {
                        "title": "Tomcat Ghostcat Vulnerability Confirmed",
                        "severity": "high",
                        "description": f"Ghostcat vulnerability (CVE-2020-1938) confirmed: {msg}",
                        "port": 8009,
                        "service": "ajp13",
                    }
                )
                break

    return {"findings": findings}


def parse_msf_exploit(output: str, target: str, module: str) -> Dict[str, Any]:
    """
    Parse MSF exploit module output for session creation.

    Returns:
        {
            'findings': [],     # Exploit success/failure findings
            'sessions': []      # Session info if created
        }
    """
    findings = []
    sessions = []
    clean_output = strip_ansi_codes(output)

    # Extract module name for display
    module_name = module.split("/")[-1] if "/" in module else module

    # Check for session opened
    # Format: [*] Command shell session 1 opened (192.168.1.224:4444 -> 192.168.1.240:35807)
    # Format: [*] Meterpreter session 1 opened (10.0.0.1:4444 -> 10.0.0.82:45678)
    session_pattern = (
        r"\[\*\]\s+(Command shell|Meterpreter)\s+session\s+(\d+)\s+opened\s+\(([^)]+)\)"
    )
    for match in re.finditer(session_pattern, clean_output, re.IGNORECASE):
        session_type = match.group(1)
        session_id = match.group(2)
        tunnel = match.group(3)

        sessions.append(
            {
                "id": session_id,
                "type": session_type.lower(),
                "tunnel": tunnel,
                "exploit": module,
            }
        )

        findings.append(
            {
                "title": f"Exploit Successful: {module_name}",
                "severity": "critical",
                "description": f"{session_type} session {session_id} opened via {module}. Tunnel: {tunnel}",
                "service": "exploit",
                "data": {
                    "exploit": module,
                    "session_id": session_id,
                    "session_type": session_type.lower(),
                    "tunnel": tunnel,
                },
            }
        )

    # Also check for "Session X created in the background"
    bg_session_pattern = r"\[\*\]\s+Session\s+(\d+)\s+created in the background"
    for match in re.finditer(bg_session_pattern, clean_output, re.IGNORECASE):
        session_id = match.group(1)
        # Only add if not already found
        if not any(s["id"] == session_id for s in sessions):
            sessions.append(
                {
                    "id": session_id,
                    "type": "unknown",
                    "tunnel": "background",
                    "exploit": module,
                }
            )

    # Check for exploit failure indicators
    if not sessions:
        # Look for common failure patterns
        failure_patterns = [
            (
                r"Exploit completed, but no session was created",
                "Exploit ran but target not vulnerable or payload failed",
            ),
            (r"Exploit failed", "Exploit execution failed"),
            (r"Target is not vulnerable", "Target not vulnerable to this exploit"),
            (r"Connection refused", "Could not connect to target service"),
            (r"Connection timed out", "Connection to target timed out"),
        ]

        for pattern, desc in failure_patterns:
            if re.search(pattern, clean_output, re.IGNORECASE):
                findings.append(
                    {
                        "title": f"Exploit Failed: {module_name}",
                        "severity": "info",
                        "description": desc,
                        "service": "exploit",
                        "data": {"exploit": module, "reason": desc},
                    }
                )
                break

    return {"findings": findings, "sessions": sessions}


def parse_msf_generic(output: str, target: str, module: str) -> Dict[str, Any]:
    """
    Generic parser for MSF modules without specific parsers.
    Extracts [+] success lines and important [*] info lines as findings.

    Returns:
        {
            'findings': [],
            'services': []
        }
    """
    findings = []
    services = []
    clean_output = strip_ansi_codes(output)

    # Extract all [+] lines (success indicators in MSF)
    # Format: [+] 10.0.0.82:port - Message
    success_pattern = r"\[\+\]\s+([\d.]+):?(\d*)\s*-?\s*(.+)"

    # Also extract important [*] lines (info that contains findings)
    # These patterns indicate actual results worth reporting
    important_info_patterns = [
        r"\[\*\]\s+([\d.]+):?(\d*)\s*-?\s*(.*(?:Host is running|SMB Detected|detected|found|version|running).*)",
        r"\[\*\]\s+([\d.]+):?(\d*)\s*-?\s*(.*(?:credential|successful|authenticated|session).*)",
    ]

    seen_messages = set()  # Avoid duplicate findings

    # Process [+] lines first (always findings)
    for match in re.finditer(success_pattern, clean_output):
        ip = match.group(1)
        port_str = match.group(2)
        message = match.group(3).strip()

        # Skip empty or duplicate messages
        if not message or message in seen_messages:
            continue
        seen_messages.add(message)

        port = int(port_str) if port_str else None

        # Determine severity based on message content
        severity = "info"
        if any(
            word in message.lower()
            for word in ["vulnerability", "vulnerable", "exploit", "rce", "injection"]
        ):
            severity = "high"
        elif any(
            word in message.lower()
            for word in ["password", "credential", "authentication", "success"]
        ):
            severity = "critical"
        elif any(
            word in message.lower() for word in ["detected", "found", "enabled", "open"]
        ):
            severity = "medium"

        # Extract module name for title
        module_name = module.split("/")[-1] if "/" in module else module

        findings.append(
            {
                "title": f'{module_name}: {message[:60]}{"..." if len(message) > 60 else ""}',
                "severity": severity,
                "description": message,
                "port": port,
                "service": "unknown",
            }
        )

    # Process important [*] lines (only if they contain real findings)
    for pattern in important_info_patterns:
        for match in re.finditer(pattern, clean_output, re.IGNORECASE):
            ip = match.group(1)
            port_str = match.group(2)
            message = match.group(3).strip()

            # Skip empty, duplicate, or progress messages
            if not message or message in seen_messages:
                continue
            if "Scanned" in message and "of" in message and "hosts" in message:
                continue  # Skip "Scanned X of Y hosts" progress messages
            if "module execution completed" in message.lower():
                continue  # Skip completion messages

            seen_messages.add(message)

            port = int(port_str) if port_str else None

            # Determine severity
            severity = "info"
            if any(
                word in message.lower()
                for word in ["credential", "successful", "password"]
            ):
                severity = "critical"
            elif any(
                word in message.lower() for word in ["detected", "version", "running"]
            ):
                severity = "medium"

            module_name = module.split("/")[-1] if "/" in module else module

            findings.append(
                {
                    "title": f'{module_name}: {message[:60]}{"..." if len(message) > 60 else ""}',
                    "severity": severity,
                    "description": message,
                    "port": port,
                    "service": "unknown",
                }
            )

    return {"findings": findings, "services": services}


def parse_msf_log(log_path: str) -> Dict[str, Any]:
    """
    Parse an MSF auxiliary module log file.

    Args:
        log_path: Path to MSF log file

    Returns:
        Parsed data with services and findings
    """
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Extract module and target from header
        # New format: "=== Plugin: Metasploit Auxiliary ===" + "Args: ['auxiliary/...', '-o', ...]"
        # Old format: "Module: auxiliary/..." + "Target: ..."
        module_match = re.search(r"^Module:\s*(.+)$", content, re.MULTILINE)
        # Fixed regex: extract first element from Args list (handles lists with multiple items)
        args_match = re.search(r'^Args:\s*\[[\'"]([^\'"]+)[\'"]', content, re.MULTILINE)
        target_match = re.search(r"^Target:\s*(.+)$", content, re.MULTILINE)

        # Determine module name (prefer Module: header, fallback to Args: parsing)
        if module_match:
            module = module_match.group(1).strip()
        elif args_match:
            module = args_match.group(1).strip()
        else:
            # Try to find module from "use" command in output
            use_match = re.search(r"use\s+(auxiliary/\S+|exploit/\S+)", content)
            if use_match:
                module = use_match.group(1).strip()
            else:
                return {
                    "error": "Could not parse MSF log header - no module/args found"
                }

        if not target_match:
            return {"error": "Could not parse MSF log header - no target found"}

        target = target_match.group(1).strip()

        # Route to appropriate parser based on module
        if "ssh_version" in module:
            return parse_msf_ssh_version(content, target)
        elif "smb_version" in module:
            return parse_msf_smb_version(content, target)
        elif "ssh_enumusers" in module:
            return parse_msf_ssh_enumusers(content, target)
        elif "kerberos_enumusers" in module:
            return parse_msf_kerberos_enumusers(content, target)
        elif "smb_enumshares" in module:
            return parse_msf_smb_enumshares(content, target)
        elif "smtp_enum" in module:
            return parse_msf_smtp_enum(content, target)
        elif "nfsmount" in module:
            return parse_msf_nfs_mount(content, target)
        elif "ftp/anonymous" in module or "ftp_anonymous" in module:
            # FTP anonymous access scanner
            return parse_msf_ftp_anonymous(content, target)
        elif "mysql_login" in module:
            # MySQL login scanner - extracts version + credentials
            return parse_msf_mysql_login(content, target)
        elif "vnc_login" in module:
            # VNC login scanner - route to login parser for credentials
            return parse_msf_login_success(content, target, module)
        elif any(x in module for x in ["_login", "brute"]):
            # Any login/brute force module
            return parse_msf_login_success(content, target, module)
        elif "java_rmi" in module:
            return parse_msf_java_rmi(content, target)
        elif "vnc_none_auth" in module:
            return parse_msf_vnc_auth(content, target)
        elif "ghostcat" in module or "tomcat_ghostcat" in module:
            return parse_msf_ghostcat(content, target)
        elif "endpoint_mapper" in module:
            return parse_msf_endpoint_mapper(content, target)
        elif module.startswith("exploit/"):
            # Route exploit modules to exploit parser
            return parse_msf_exploit(content, target, module)
        else:
            # Generic parser - extract [+] lines as findings
            return parse_msf_generic(content, target, module)

    except FileNotFoundError:
        return {"error": f"File not found: {log_path}"}
    except Exception as e:
        return {"error": str(e)}
