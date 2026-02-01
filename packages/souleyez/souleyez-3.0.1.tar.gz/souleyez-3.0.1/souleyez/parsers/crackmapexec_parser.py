#!/usr/bin/env python3
"""
souleyez.parsers.crackmapexec_parser - Parse CrackMapExec (NetExec) output
"""

import re
from typing import Any, Dict, List


def parse_crackmapexec_output(content: str, target: str = "") -> Dict[str, Any]:
    """
    Wrapper function that parses CrackMapExec output from string content.

    Args:
        content: Raw CME output text
        target: Target that was scanned

    Returns:
        Dict containing parsed findings
    """
    return _parse_content(content, target)


def parse_crackmapexec(log_path: str, target: str) -> Dict[str, Any]:
    """
    Parse CrackMapExec/NetExec log output from file.

    Args:
        log_path: Path to CME output file
        target: Target that was scanned

    Returns:
        Dict containing parsed findings
    """
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            return _parse_content(content, target)
    except FileNotFoundError:
        return {
            "tool": "crackmapexec",
            "target": target,
            "error": "Log file not found",
            "findings": {
                "hosts": [],
                "shares": [],
                "users": [],
                "groups": [],
                "credentials": [],
                "vulnerabilities": [],
            },
        }


def _parse_content(content: str, target: str) -> Dict[str, Any]:
    """
    Internal function to parse CrackMapExec output content.

    Args:
        content: Raw CME output text
        target: Target that was scanned

    Returns:
        Dict containing parsed findings
    """
    findings = {
        "hosts": [],
        "shares": [],
        "users": [],
        "groups": [],
        "credentials": [],
        "vulnerabilities": [],
        "auth_info": {},
        "password_must_change": [],  # Users with STATUS_PASSWORD_MUST_CHANGE
    }

    # Remove ANSI color codes first
    content = re.sub(r"\x1b\[[0-9;]*m", "", content)

    for line in content.split("\n"):
        # Parse host information (Windows OR Unix/Samba)
        # Format variations:
        # SMB  10.0.0.88  445  HOSTNAME  [*] Windows/Unix ... (name:HOSTNAME) (domain:DOMAIN) ...
        # SMB         10.0.0.88    445    HOSTNAME [*] Windows Server 2016 ...
        # WINRM  10.0.0.88  5985  HOSTNAME  [*] http://10.0.0.88:5985/wsman

        os_keywords = ["Windows", "Unix", "Samba", "Linux", "Server", "Microsoft"]
        if (
            any(proto in line for proto in ["SMB", "WINRM", "SSH", "RDP"])
            and "[*]" in line
        ):
            # Try multiple patterns for host info
            host_match = None

            # Pattern 1: Standard format with flexible whitespace
            host_match = re.search(
                r"(\d+\.\d+\.\d+\.\d+)\s+(\d+)\s+(\S+)\s+\[\*\]\s*(.+)", line
            )

            # Pattern 2: Protocol prefix format
            if not host_match:
                host_match = re.search(
                    r"(?:SMB|WINRM|SSH|RDP)\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+)\s+(\S+)\s+\[\*\]\s*(.+)",
                    line,
                )

            if host_match:
                ip = host_match.group(1)
                port = int(host_match.group(2))
                hostname = host_match.group(3)
                details = host_match.group(4).strip()

                # Only process as host info if it looks like OS/version info
                if any(kw in details for kw in os_keywords) or "(domain:" in details:
                    # Extract domain from (domain:DOMAIN) or domain: pattern
                    domain_match = re.search(
                        r"\(?domain:?\s*([^)\s]+)\)?", details, re.IGNORECASE
                    )
                    domain = domain_match.group(1) if domain_match else None

                    # Extract OS info (everything before the first parenthesis)
                    os_match = re.match(r"([^(]+)", details)
                    os_info = os_match.group(1).strip() if os_match else details

                    # Extract SMB signing status (multiple formats)
                    signing_match = re.search(
                        r"\(?signing:?\s*(\w+)\)?", details, re.IGNORECASE
                    )
                    signing = signing_match.group(1) if signing_match else None

                    # Extract SMBv1 status
                    smbv1_match = re.search(
                        r"\(?SMBv1:?\s*(\w+)\)?", details, re.IGNORECASE
                    )
                    smbv1 = smbv1_match.group(1) if smbv1_match else None

                    findings["hosts"].append(
                        {
                            "ip": ip,
                            "port": port,
                            "hostname": hostname,
                            "domain": domain,
                            "os": os_info,
                            "signing": signing,
                            "smbv1": smbv1,
                        }
                    )

        # Parse authentication status
        # Format: SMB  10.0.0.14  445  HOSTNAME  [+] \: (Guest)
        if "SMB" in line and "[+]" in line and ("Guest" in line or "\\" in line):
            auth_match = re.search(r"\[\+\]\s+(.+)", line)
            if auth_match:
                auth_str = auth_match.group(1).strip()
                findings["auth_info"] = {
                    "status": "success",
                    "details": auth_str,
                    "is_guest": "Guest" in auth_str,
                }

        # Parse share enumeration (shares WITH permissions)
        # Format variations:
        # SMB ... ADMIN$  READ,WRITE  Remote Admin
        # SMB ... ADMIN$  READ, WRITE  Remote Admin (with space)
        # SMB ... C$  READ ONLY  Default share
        share_perm_match = re.search(
            r"SMB.*\s+(\S+\$?)\s+(READ,?\s*WRITE|READ\s*ONLY|WRITE\s*ONLY|READ|WRITE|NO\s*ACCESS)\s*(.*)$",
            line,
            re.IGNORECASE,
        )
        if share_perm_match:
            share_name = share_perm_match.group(1)
            # Skip if it looks like a header or status line
            if share_name not in ["Share", "Permissions", "shares"]:
                findings["shares"].append(
                    {
                        "name": share_name,
                        "permissions": share_perm_match.group(2)
                        .upper()
                        .replace(" ", ""),
                        "comment": (
                            share_perm_match.group(3).strip()
                            if share_perm_match.group(3)
                            else ""
                        ),
                    }
                )
        # Parse share enumeration (shares WITHOUT explicit permissions - just listed)
        elif (
            "SMB" in line
            and not ("Share" in line and "Permissions" in line)
            and not "-----" in line
        ):
            # Look for lines with share names (ending with $, or common names like print$, public, IPC$)
            share_list_match = re.search(
                r"SMB\s+\S+\s+\d+\s+\S+\s+(\w+\$?|\w+)\s+(.+)?$", line
            )
            if share_list_match:
                share_name = share_list_match.group(1).strip()
                remark = (
                    share_list_match.group(2).strip()
                    if share_list_match.group(2)
                    else ""
                )
                # Only add if it looks like a share (not header text, not empty)
                if (
                    share_name
                    and share_name not in ["Share", "Enumerated", "shares"]
                    and not share_name.startswith("[")
                ):
                    # Check if not already added
                    if not any(s["name"] == share_name for s in findings["shares"]):
                        findings["shares"].append(
                            {"name": share_name, "permissions": None, "comment": remark}
                        )

        # Parse user enumeration with flexible format
        # Format variations:
        # username badpwdcount: 0 desc: Description
        # username  badpwdcount:0  desc:Description
        # username baddpwdcount: 0 description: Description
        if "badpwdcount" in line.lower() or "baddpwdcount" in line.lower():
            user_match = re.search(
                r"(\S+)\s+bad+pwdcount:?\s*(\d+)\s+(?:desc(?:ription)?:?\s*)?(.+)?",
                line,
                re.IGNORECASE,
            )
            if user_match:
                findings["users"].append(
                    {
                        "username": user_match.group(1),
                        "badpwdcount": int(user_match.group(2)),
                        "description": (
                            user_match.group(3).strip() if user_match.group(3) else ""
                        ),
                    }
                )

        # Parse vulnerability findings
        if "vulnerable" in line.lower() or "MS17-010" in line:
            vuln_match = re.search(r"\[\+\]\s+(.+)", line)
            if vuln_match:
                findings["vulnerabilities"].append(
                    {"description": vuln_match.group(1).strip()}
                )

        # Parse STATUS_PASSWORD_MUST_CHANGE - user needs to change password
        # Format: SMB  IP  445  HOST  [-] domain\user:password STATUS_PASSWORD_MUST_CHANGE
        if "STATUS_PASSWORD_MUST_CHANGE" in line:
            pwchange_match = re.search(
                r"\[-\]\s*([^\\/:]+)[\\\/]+([^:]+):([^\s]+)\s+STATUS_PASSWORD_MUST_CHANGE",
                line,
                re.IGNORECASE,
            )
            if pwchange_match:
                findings["password_must_change"].append(
                    {
                        "domain": pwchange_match.group(1).strip(),
                        "username": pwchange_match.group(2).strip(),
                        "password": pwchange_match.group(3).strip(),
                    }
                )

        # Parse valid credentials (but not Guest authentication)
        # Format variations:
        # [+] DOMAIN\username:password (Pwn3d!)
        # [+] DOMAIN\\username:password (Pwn3d!)
        # [+] username:password (Pwn3d!)
        # [+] DOMAIN/username:password (Pwn3d!)
        if "[+]" in line and ("Pwn3d" in line or ":" in line):
            # Try domain\user:pass format first
            cred_match = re.search(
                r"\[\+\]\s*([^\\/:]+)[\\\/]+([^:]+):([^\s(]+)\s*(\(Pwn3d!?\))?",
                line,
                re.IGNORECASE,
            )
            if cred_match:
                findings["credentials"].append(
                    {
                        "domain": cred_match.group(1).strip(),
                        "username": cred_match.group(2).strip(),
                        "password": cred_match.group(3).strip(),
                        "admin": bool(cred_match.group(4)),
                    }
                )
            else:
                # Try user:pass format (no domain)
                cred_match = re.search(
                    r"\[\+\]\s*([^:@\s]+):([^\s(]+)\s*(\(Pwn3d!?\))?",
                    line,
                    re.IGNORECASE,
                )
                if cred_match and "@" not in cred_match.group(1):
                    findings["credentials"].append(
                        {
                            "domain": "",
                            "username": cred_match.group(1).strip(),
                            "password": cred_match.group(2).strip(),
                            "admin": bool(cred_match.group(3)),
                        }
                    )

    # Extract admin credentials for auto-chaining
    admin_creds = [c for c in findings["credentials"] if c.get("admin")]

    # Extract unique domains for auto-chaining
    domains = []
    seen_domains = set()
    for host in findings["hosts"]:
        domain = host.get("domain")
        if domain and domain not in seen_domains:
            domains.append({"domain": domain, "ip": host.get("ip")})
            seen_domains.add(domain)

    return {
        "tool": "crackmapexec",
        "target": target,
        "hosts_found": len(findings["hosts"]),
        "shares_found": len(findings["shares"]),
        "users_found": len(findings["users"]),
        "valid_credentials": len(findings["credentials"]),
        "vulnerabilities_found": len(findings["vulnerabilities"]),
        "password_must_change_found": len(findings["password_must_change"]),
        "findings": findings,
        "domains": domains,  # For auto-chaining to GetNPUsers and other AD tools
        "valid_admin_credentials": admin_creds,  # For auto-chaining to secretsdump
        "password_must_change": findings[
            "password_must_change"
        ],  # For smbpasswd chaining
    }
