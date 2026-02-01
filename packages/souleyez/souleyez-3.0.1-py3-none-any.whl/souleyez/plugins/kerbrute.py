#!/usr/bin/env python3
"""
souleyez.plugins.kerbrute - Kerberos username enumeration and password spraying
"""

import subprocess
import time
from typing import List

from .plugin_base import PluginBase

HELP = {
    "name": "Kerbrute - Kerberos User Enumeration",
    "description": (
        "Need to enumerate Active Directory usernames?\n\n"
        "Kerbrute uses Kerberos pre-authentication to enumerate valid usernames "
        "and perform password spraying attacks. Unlike LDAP enumeration, it works "
        "even when anonymous binds are disabled.\n\n"
        "Use Kerbrute when:\n"
        "- Anonymous LDAP enumeration is blocked\n"
        "- You need to find valid AD usernames\n"
        "- You want to password spray without lockouts\n"
        "- enum4linux/RID cycling fails with ACCESS_DENIED\n\n"
        "Quick tips:\n"
        "- Uses Kerberos pre-auth responses to identify valid users\n"
        "- Faster than LDAP enumeration\n"
        "- Works without any credentials\n"
        "- Can also perform password spraying\n"
    ),
    "usage": 'souleyez jobs enqueue kerbrute <target> --args "userenum -d <domain> --dc <dc_ip> <userlist>"',
    "examples": [
        'souleyez jobs enqueue kerbrute 10.0.0.82 --args "userenum -d CONTOSO.LOCAL --dc 10.0.0.82 users.txt"',
        'souleyez jobs enqueue kerbrute 10.0.0.82 --args "passwordspray -d CONTOSO.LOCAL --dc 10.0.0.82 users.txt Password123"',
        'souleyez jobs enqueue kerbrute 10.0.0.82 --args "userenum -d CONTOSO.LOCAL users.txt"',
    ],
    "flags": [
        ["userenum", "Enumerate valid usernames via Kerberos"],
        ["passwordspray", "Spray a password against user list"],
        ["bruteuser", "Brute force a single user's password"],
        ["-d <domain>", "Domain name (e.g., CONTOSO.LOCAL)"],
        ["--dc <ip>", "Domain Controller IP address"],
        ["-t <threads>", "Number of threads (default: 10)"],
        ["-o <file>", "Output file for valid users"],
    ],
    "preset_categories": {
        "enumeration": [
            {
                "name": "Username Enumeration",
                "args": [
                    "userenum",
                    "-d",
                    "<domain>",
                    "--dc",
                    "<target>",
                    "data/wordlists/ad_users.txt",
                ],
                "desc": "Enumerate valid AD usernames via Kerberos",
            },
            {
                "name": "Fast Username Enum",
                "args": [
                    "userenum",
                    "-d",
                    "<domain>",
                    "--dc",
                    "<target>",
                    "-t",
                    "50",
                    "data/wordlists/ad_users.txt",
                ],
                "desc": "Fast enumeration with 50 threads",
            },
        ],
        "spraying": [
            {
                "name": "Password Spray",
                "args": [
                    "passwordspray",
                    "-d",
                    "<domain>",
                    "--dc",
                    "<target>",
                    "users.txt",
                    "<password>",
                ],
                "desc": "Spray single password against user list",
            }
        ],
    },
    "presets": [],
}

# Flatten presets
for category_presets in HELP["preset_categories"].values():
    HELP["presets"].extend(category_presets)

HELP["help_sections"] = [
    {
        "title": "What is Kerbrute?",
        "color": "cyan",
        "content": [
            {
                "title": "Overview",
                "desc": "Kerbrute uses Kerberos pre-authentication to enumerate valid usernames and perform password attacks without triggering account lockouts.",
            },
            {
                "title": "Use Cases",
                "desc": "Enumerate AD users when LDAP is restricted",
                "tips": [
                    "Find valid usernames when anonymous LDAP is blocked",
                    "Faster than RID cycling or LDAP enumeration",
                    "Password spray without lockouts (by default)",
                    "Works without any credentials",
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
                "desc": "1. Run userenum with username wordlist\n     2. Collect valid usernames\n     3. Optionally password spray\n     4. Use valid credentials for access",
            },
            {
                "title": "Key Commands",
                "desc": "Essential Kerbrute modes",
                "tips": [
                    "userenum: Find valid usernames",
                    "passwordspray: Test one password against many users",
                    "bruteuser: Brute force single user",
                    "-d: Specify domain name",
                    "--dc: Domain Controller IP",
                ],
            },
        ],
    },
]


class KerbrutePlugin(PluginBase):
    name = "Kerbrute"
    tool = "kerbrute"
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
        cmd = ["kerbrute"]
        cmd.extend(args)

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute kerbrute and write output to log_path."""

        args = args or []

        # Replace placeholders
        args = [arg.replace("<target>", target) for arg in args]

        # Build command
        cmd = ["kerbrute"]
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
                fh.write(f"=== Plugin: Kerbrute ===\n")
                fh.write(f"Target: {target}\n")
                fh.write(f"Args: {args}\n")
                fh.write(f"Label: {label}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Command: {' '.join(cmd)}\n\n")

            # Run kerbrute
            proc = subprocess.run(
                cmd, capture_output=True, timeout=600, check=False, text=True
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
                fh.write("\n\nERROR: Kerbrute timed out after 600 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write("ERROR: kerbrute not found in PATH\n")
                fh.write("Install: go install github.com/ropnop/kerbrute@latest\n")
                fh.write(
                    "Or download from: https://github.com/ropnop/kerbrute/releases\n"
                )
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\n\nERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = KerbrutePlugin()
