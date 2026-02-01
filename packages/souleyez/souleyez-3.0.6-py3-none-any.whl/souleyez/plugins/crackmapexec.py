#!/usr/bin/env python3
"""
souleyez.plugins.crackmapexec - Swiss army knife for Windows/AD pentesting

Note: Uses NetExec (netexec/nxc), the successor to CrackMapExec
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "CrackMapExec (CME) - Windows/AD Pentesting Tool",
    "description": (
        "Want a Swiss army knife for Windows and Active Directory pentesting?\n\n"
        "CrackMapExec (now NetExec) is the industry-standard tool for Windows/AD enumeration, credential validation, "
        "and post-exploitation. It supports multiple protocols (SMB, WinRM, MSSQL, LDAP, RDP) and can "
        "enumerate shares, users, groups, check for vulnerabilities, and execute commands.\n\n"
        "Use CME for:\n"
        "- SMB share enumeration (replaces enum4linux)\n"
        "- Credential validation and spraying\n"
        "- Vulnerability checks (MS17-010, ZeroLogon, etc.)\n"
        "- User and group enumeration\n"
        "- Post-exploitation (command execution, hash dumping)\n\n"
        "Quick tips:\n"
        "- Start unauthenticated for basic enumeration\n"
        "- Use found credentials to pivot across the network\n"
        "- Check for MS17-010 (EternalBlue) on all SMB hosts\n"
        "- Results link to Impacket for follow-up attacks\n"
    ),
    "usage": 'souleyez jobs enqueue crackmapexec <target> --args "smb --shares"',
    "examples": [
        'souleyez jobs enqueue crackmapexec 10.0.0.82 --args "smb --shares"',
        'souleyez jobs enqueue crackmapexec 10.0.0.82 --args "smb -u admin -p password"',
        "souleyez jobs enqueue crackmapexec 10.0.0.82 --args \"smb -u '' -p '' -M ms17-010\"",
        'souleyez jobs enqueue crackmapexec 10.0.0.0/24 --args "smb --users"',
    ],
    "flags": [
        ["smb", "SMB protocol"],
        ["winrm", "WinRM protocol"],
        ["mssql", "MSSQL protocol"],
        ["ldap", "LDAP protocol"],
        ["-u <user>", "Username (use '' for null session)"],
        ["-p <pass>", "Password"],
        ["-d <domain>", "Domain"],
        ["--shares", "Enumerate shares"],
        ["--users", "Enumerate users"],
        ["--groups", "Enumerate groups"],
        ["-M <module>", "Run module (e.g., ms17-010)"],
    ],
    "preset_categories": {
        "unauthenticated": [
            {
                "name": "Basic SMB Enum",
                "args": ["smb", "--shares"],
                "desc": "Enumerate shares (no credentials)",
            },
            {
                "name": "Vulnerability Check",
                "args": ["smb", "-u", "", "-p", "", "-M", "ms17-010"],
                "desc": "Check for MS17-010 (EternalBlue)",
            },
            {
                "name": "User Enumeration",
                "args": ["smb", "--users"],
                "desc": "Enumerate domain users",
            },
        ],
        "authenticated": [
            {
                "name": "With Credentials",
                "args": ["smb", "-u", "<username>", "-p", "<password>", "--shares"],
                "desc": "Authenticated share enumeration",
            },
            {
                "name": "Domain Auth",
                "args": [
                    "smb",
                    "-u",
                    "<username>",
                    "-p",
                    "<password>",
                    "-d",
                    "<domain>",
                ],
                "desc": "Domain authentication",
            },
            {
                "name": "Password Spray",
                "args": ["smb", "-u", "users.txt", "-p", "password", "--no-bruteforce"],
                "desc": "Spray single password across user list",
            },
        ],
    },
    "presets": [
        {
            "name": "Basic SMB Enum",
            "args": ["smb", "--shares"],
            "desc": "Enumerate shares (no credentials)",
        },
        {
            "name": "Vulnerability Check",
            "args": ["smb", "-u", "", "-p", "", "-M", "ms17-010"],
            "desc": "Check for MS17-010 (EternalBlue)",
        },
        {
            "name": "User Enumeration",
            "args": ["smb", "--users"],
            "desc": "Enumerate domain users",
        },
        {
            "name": "With Credentials",
            "args": ["smb", "-u", "<username>", "-p", "<password>", "--shares"],
            "desc": "Authenticated share enumeration",
        },
    ],
    "help_sections": [
        {
            "title": "What is CrackMapExec?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "CrackMapExec (now NetExec) is the Swiss army knife for Windows and Active Directory pentesting, supporting SMB, WinRM, MSSQL, LDAP, and RDP protocols.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Industry-standard tool for Windows/AD enumeration and exploitation",
                    "tips": [
                        "Enumerate SMB shares without credentials",
                        "Validate credentials across multiple hosts",
                        "Check for critical vulnerabilities (MS17-010, ZeroLogon)",
                        "Execute commands and dump hashes with valid creds",
                    ],
                },
            ],
        },
        {
            "title": "How to Use",
            "color": "green",
            "content": [
                {
                    "title": "Basic Workflow",
                    "desc": "1. Start with unauthenticated scans (--shares)\n     2. Check for vulnerabilities (-M ms17-010)\n     3. Use found credentials to enumerate further\n     4. Pivot across network with credential spraying",
                },
                {
                    "title": "Common Tasks",
                    "desc": "Key enumeration and validation features",
                    "tips": [
                        "Share enumeration: netexec smb <target> --shares",
                        "User enumeration: netexec smb <target> --users",
                        "Credential validation: netexec smb <target> -u user -p pass",
                        "Vulnerability check: netexec smb <target> -M ms17-010",
                    ],
                },
            ],
        },
        {
            "title": "Tips & Best Practices",
            "color": "yellow",
            "content": [
                (
                    "Best Practices:",
                    [
                        "Start with unauthenticated enumeration",
                        "Check MS17-010 on all SMB hosts",
                        "Use found credentials for lateral movement",
                        "Save results for Impacket follow-up attacks",
                        "Test one credential at a time to avoid lockouts",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "Access denied: Try null session (-u '' -p '')",
                        "No output: Verify SMB is open (port 445)",
                        "Credential errors: Check domain name format (DOMAIN/user)",
                        "Module not found: Update NetExec to latest version",
                    ],
                ),
            ],
        },
    ],
}


class CrackMapExecPlugin(PluginBase):
    name = "CrackMapExec"
    tool = "crackmapexec"
    category = "scanning"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build CrackMapExec command for background execution with PID tracking."""
        # Handle multiple space-separated IPs
        target_list = []
        if " " in target:
            for ip in target.split():
                ip = ip.strip()
                if ip:
                    try:
                        validated = validate_target(ip)
                        target_list.append(validated)
                    except ValidationError as e:
                        if log_path:
                            with open(log_path, "w") as f:
                                f.write(f"ERROR: Invalid target '{ip}': {e}\n")
                        return None
        else:
            try:
                target = validate_target(target)
                target_list = [target]
            except ValidationError as e:
                if log_path:
                    with open(log_path, "w") as f:
                        f.write(f"ERROR: Invalid target: {e}\n")
                return None

        args = args or ["smb", "--shares"]
        args = [arg.replace("<target>", target_list[0]) for arg in args]

        protocol = (
            args[0]
            if args
            and args[0]
            in [
                "smb",
                "winrm",
                "mssql",
                "ldap",
                "ssh",
                "rdp",
                "ftp",
                "vnc",
                "nfs",
                "wmi",
            ]
            else "smb"
        )
        cmd = ["netexec", protocol] + target_list

        if len(args) > 1:
            cmd.extend(args[1:])
        elif protocol not in args:
            cmd.extend(["--shares"])

        # For anonymous enumeration, use null session with empty domain
        # netexec 1.5.0 requires -d '' for proper null session (1.4.0 didn't need it)
        has_creds = any(arg in cmd for arg in ["-u", "--username", "-p", "--password"])
        has_enum = any(
            arg in cmd
            for arg in [
                "--shares",
                "--users",
                "--groups",
                "--sessions",
                "--disks",
                "--loggedon-users",
            ]
        )

        if has_enum and not has_creds:
            insert_pos = 2 + len(target_list)
            cmd.insert(insert_pos, "-u")
            cmd.insert(insert_pos + 1, "")
            cmd.insert(insert_pos + 2, "-p")
            cmd.insert(insert_pos + 3, "")
            cmd.insert(insert_pos + 4, "-d")
            cmd.insert(insert_pos + 5, "")

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute CrackMapExec (NetExec) and write output to log_path."""

        # Handle multiple space-separated IPs (from multi-host selection)
        # NetExec needs them as separate arguments, not a single string
        target_list = []
        if " " in target:
            # Multiple IPs separated by spaces
            for ip in target.split():
                ip = ip.strip()
                if ip:
                    try:
                        # Validate each IP individually
                        validated = validate_target(ip)
                        target_list.append(validated)
                    except ValidationError as e:
                        if log_path:
                            with open(log_path, "w") as f:
                                f.write(f"ERROR: Invalid target '{ip}': {e}\n")
                            return 1
                        raise ValueError(f"Invalid target '{ip}': {e}")
        else:
            # Single target - validate it
            try:
                target = validate_target(target)
                target_list = [target]
            except ValidationError as e:
                if log_path:
                    with open(log_path, "w") as f:
                        f.write(f"ERROR: Invalid target: {e}\n")
                    return 1
                raise ValueError(f"Invalid target: {e}")

        args = args or ["smb", "--shares"]

        # Replace <target> placeholder with first target (for single target mode)
        args = [arg.replace("<target>", target_list[0]) for arg in args]

        # Detect protocol (first arg should be protocol)
        protocol = (
            args[0]
            if args
            and args[0]
            in [
                "smb",
                "winrm",
                "mssql",
                "ldap",
                "ssh",
                "rdp",
                "ftp",
                "vnc",
                "nfs",
                "wmi",
            ]
            else "smb"
        )

        # Use netexec (successor to crackmapexec)
        # Add all targets as separate arguments (NetExec supports multiple targets)
        cmd = ["netexec", protocol] + target_list

        # Add remaining args
        if len(args) > 1:
            cmd.extend(args[1:])
        elif protocol not in args:
            # No protocol specified in args, add default behavior
            cmd.extend(["--shares"])

        # For anonymous enumeration, use null session with empty domain
        # netexec 1.5.0 requires -d '' for proper null session (1.4.0 didn't need it)
        has_creds = any(arg in cmd for arg in ["-u", "--username", "-p", "--password"])
        has_enum = any(
            arg in cmd
            for arg in [
                "--shares",
                "--users",
                "--groups",
                "--sessions",
                "--disks",
                "--loggedon-users",
            ]
        )

        if has_enum and not has_creds:
            insert_pos = 2 + len(target_list)
            cmd.insert(insert_pos, "-u")
            cmd.insert(insert_pos + 1, "")
            cmd.insert(insert_pos + 2, "-p")
            cmd.insert(insert_pos + 3, "")
            cmd.insert(insert_pos + 4, "-d")
            cmd.insert(insert_pos + 5, "")

        if not log_path:
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=300, check=False
                )
                return proc.returncode
            except Exception:
                return 1

        try:
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write("=== CrackMapExec (NetExec) Scan ===\n")
                fh.write(f"Target(s): {' '.join(target_list)}\n")
                fh.write(f"Protocol: {protocol}\n")
                fh.write(f"Command: {' '.join(cmd)}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
                )
                fh.flush()

                proc = subprocess.run(
                    cmd, stdout=fh, stderr=subprocess.STDOUT, timeout=300, check=False
                )

                fh.write(
                    f"\n\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Exit Code: {proc.returncode}\n")

                return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: CrackMapExec timed out after 300 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: netexec/crackmapexec not found in PATH\n")
                fh.write("Install: apt install netexec\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\nERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = CrackMapExecPlugin()
