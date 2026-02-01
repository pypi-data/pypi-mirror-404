#!/usr/bin/env python3
"""
souleyez.plugins.nxc - NetExec (successor to CrackMapExec) for SMB/WinRM/etc
"""

import subprocess
import time
from typing import List

from .plugin_base import PluginBase

HELP = {
    "name": "NetExec - Network Service Exploitation",
    "description": (
        "NetExec (nxc) is the successor to CrackMapExec.\n\n"
        "Use it for:\n"
        "- SMB share enumeration\n"
        "- Credential validation and spraying\n"
        "- WinRM/RDP/MSSQL/LDAP attacks\n"
        "- Pass-the-hash/Pass-the-ticket\n"
        "- Command execution on compromised hosts\n\n"
        "Quick tips:\n"
        "- Use --shares to enumerate shares\n"
        "- Use --users to enumerate users\n"
        "- Use -x to execute commands\n"
        "- (Pwn3d!) means admin access achieved\n"
    ),
    "usage": 'souleyez jobs enqueue nxc <target> --args "smb <target> -u <user> -p <pass> --shares"',
    "examples": [
        "souleyez jobs enqueue nxc 10.0.0.82 --args \"smb 10.0.0.82 -u guest -p '' --shares\"",
        'souleyez jobs enqueue nxc 10.0.0.82 --args "smb 10.0.0.82 -u admin -p Password1 --shares"',
        'souleyez jobs enqueue nxc 10.0.0.82 --args "smb 10.0.0.82 -u users.txt -p passwords.txt --no-bruteforce"',
        'souleyez jobs enqueue nxc 10.0.0.82 --args "smb 10.0.0.82 -u admin -H <nthash> --shares"',
        'souleyez jobs enqueue nxc 10.0.0.82 --args "winrm 10.0.0.82 -u admin -p Password1"',
    ],
    "flags": [
        ["smb", "Target SMB service (port 445)"],
        ["winrm", "Target WinRM service (port 5985/5986)"],
        ["rdp", "Target RDP service (port 3389)"],
        ["ldap", "Target LDAP service (port 389/636)"],
        ["mssql", "Target MSSQL service (port 1433)"],
        ["-u <user>", "Username or file with usernames"],
        ["-p <pass>", "Password or file with passwords"],
        ["-H <hash>", "NTLM hash for pass-the-hash"],
        ["--shares", "Enumerate SMB shares"],
        ["--users", "Enumerate domain users"],
        ["--groups", "Enumerate domain groups"],
        ["--pass-pol", "Get password policy"],
        ["-x <cmd>", "Execute command on target"],
        ["--no-bruteforce", "Test user:pass pairs only (not combinations)"],
        ["--continue-on-success", "Continue after finding valid creds"],
    ],
    "preset_categories": {
        "enumeration": [
            {
                "name": "Guest Share Enum",
                "args": ["smb", "<target>", "-u", "guest", "-p", "", "--shares"],
                "desc": "Enumerate shares with guest account",
            },
            {
                "name": "Null Session Shares",
                "args": ["smb", "<target>", "-u", "", "-p", "", "--shares"],
                "desc": "Enumerate shares with null session",
            },
            {
                "name": "User Enumeration",
                "args": ["smb", "<target>", "-u", "<user>", "-p", "<pass>", "--users"],
                "desc": "Enumerate domain users",
            },
            {
                "name": "Password Policy",
                "args": [
                    "smb",
                    "<target>",
                    "-u",
                    "<user>",
                    "-p",
                    "<pass>",
                    "--pass-pol",
                ],
                "desc": "Get domain password policy",
            },
        ],
        "credential_attacks": [
            {
                "name": "Username=Password Spray",
                "args": [
                    "smb",
                    "<target>",
                    "-u",
                    "users.txt",
                    "-p",
                    "users.txt",
                    "--no-bruteforce",
                    "--continue-on-success",
                ],
                "desc": "Test username as password",
            },
            {
                "name": "Password Spray",
                "args": [
                    "smb",
                    "<target>",
                    "-u",
                    "users.txt",
                    "-p",
                    "<password>",
                    "--continue-on-success",
                ],
                "desc": "Spray single password",
            },
            {
                "name": "Pass-the-Hash",
                "args": ["smb", "<target>", "-u", "<user>", "-H", "<nthash>"],
                "desc": "Authenticate with NTLM hash",
            },
        ],
        "execution": [
            {
                "name": "WinRM Check",
                "args": ["winrm", "<target>", "-u", "<user>", "-p", "<pass>"],
                "desc": "Check WinRM access",
            },
            {
                "name": "Command Execution",
                "args": [
                    "smb",
                    "<target>",
                    "-u",
                    "<user>",
                    "-p",
                    "<pass>",
                    "-x",
                    "whoami",
                ],
                "desc": "Execute command via SMB",
            },
        ],
    },
    "presets": [],
}

# Flatten presets
for category_presets in HELP["preset_categories"].values():
    HELP["presets"].extend(category_presets)

HELP["help_sections"] = [
    {
        "title": "What is NetExec?",
        "color": "cyan",
        "content": [
            {
                "title": "Overview",
                "desc": "NetExec (nxc) is a network service exploitation tool that supports SMB, WinRM, RDP, LDAP, MSSQL and more.",
            },
            {
                "title": "Key Features",
                "desc": "Multi-protocol support",
                "tips": [
                    "SMB share enumeration and access",
                    "Credential spraying and validation",
                    "Pass-the-hash and pass-the-ticket",
                    "Command execution on compromised hosts",
                    "Domain enumeration (users, groups, policies)",
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
                "desc": "1. Enumerate shares with guest/null session\n     2. Test credentials (spray or PTH)\n     3. Enumerate domain with valid creds\n     4. Execute commands if admin",
            },
            {
                "title": "Success Indicators",
                "desc": "What to look for",
                "tips": [
                    "(Pwn3d!) = Admin access achieved",
                    "[+] = Successful operation",
                    "READ,WRITE = Share permissions",
                    "STATUS_LOGON_FAILURE = Invalid creds",
                ],
            },
        ],
    },
]


class NxcPlugin(PluginBase):
    name = "NetExec"
    tool = "nxc"
    category = "credential_access"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution with PID tracking."""
        args = args or []

        # Replace placeholders
        args = [arg.replace("<target>", target) for arg in args]

        # Build command
        cmd = ["nxc"]
        cmd.extend(args)

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute nxc and write output to log_path."""

        args = args or []

        # Replace placeholders
        args = [arg.replace("<target>", target) for arg in args]

        # Build command
        cmd = ["nxc"]
        cmd.extend(args)

        if not log_path:
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=600, check=False
                )
                return proc.returncode
            except Exception:
                return 1

        try:
            # Create metadata header
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write(f"=== Plugin: NetExec (nxc) ===\n")
                fh.write(f"Target: {target}\n")
                fh.write(f"Args: {args}\n")
                fh.write(f"Label: {label}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Command: {' '.join(cmd)}\n\n")

            # Run nxc
            proc = subprocess.run(
                cmd, capture_output=True, timeout=1800, check=False, text=True
            )

            # Write output
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                if proc.stdout:
                    fh.write(proc.stdout)

                if proc.stderr:
                    fh.write(f"\n{proc.stderr}")

                fh.write(
                    f"\n\n=== Completed: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} ===\n"
                )
                fh.write(f"Exit Code: {proc.returncode}\n")

            return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\n\nERROR: nxc timed out after 1800 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write("ERROR: nxc not found in PATH\n")
                fh.write("Install: pipx install netexec\n")
                fh.write("Or: sudo apt install netexec\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\n\nERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = NxcPlugin()
