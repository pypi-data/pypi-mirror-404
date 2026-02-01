#!/usr/bin/env python3
"""
souleyez.plugins.evil_winrm

Evil-WinRM - Windows Remote Management Shell plugin.
"""

import subprocess
import time
from typing import List

from .plugin_base import PluginBase

HELP = {
    "name": "Evil-WinRM - Windows Remote Shell",
    "description": (
        "Got Windows creds and need a shell?\n\n"
        "Evil-WinRM is the ultimate WinRM shell for hacking. It provides a fully "
        "interactive PowerShell session on Windows targets over WinRM (port 5985/5986).\n\n"
        "Perfect for post-exploitation after discovering valid credentials through "
        "Hydra, secretsdump, or other credential attacks.\n\n"
        "Quick tips:\n"
        "- Supports password, NTLM hash (pass-the-hash), and Kerberos authentication\n"
        "- Built-in file upload/download functionality\n"
        "- Execute commands non-interactively with -c flag\n"
        "- Works when SMB is blocked but WinRM is open\n"
        "- Default ports: 5985 (HTTP) and 5986 (HTTPS/SSL)\n"
    ),
    "usage": 'souleyez jobs enqueue evil_winrm <target> --args "-u <user> -p <pass>"',
    "examples": [
        'souleyez jobs enqueue evil_winrm 192.168.1.10 --args "-u administrator -p Password123!"',
        'souleyez jobs enqueue evil_winrm 192.168.1.10 --args "-u admin -H aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0"',
        "souleyez jobs enqueue evil_winrm 192.168.1.10 --args \"-u admin -p Password123! -c 'whoami /all'\"",
        "souleyez jobs enqueue evil_winrm 192.168.1.10 --args \"-u admin@DOMAIN -p Password123! -c 'hostname'\"",
    ],
    "flags": [
        ["-i, --ip <IP>", "Remote host IP or hostname"],
        ["-u, --user <USER>", "Username for authentication"],
        ["-p, --password <PASS>", "Password for authentication"],
        ["-H, --hash <HASH>", "NTLM hash for pass-the-hash (LM:NT or just NT)"],
        ["-P, --port <PORT>", "WinRM port (default: 5985)"],
        ["-s, --ssl", "Enable SSL (port 5986)"],
        ["-c, --command <CMD>", "Execute command and exit (non-interactive)"],
        ["-S, --scripts <PATH>", "PowerShell scripts local path"],
        ["-e, --executables <PATH>", "C# executables local path"],
        ["-r, --realm <DOMAIN>", "Kerberos realm (domain)"],
    ],
    "preset_categories": {
        "authentication": [
            {
                "name": "Password Auth",
                "args": ["-u", "administrator", "-p", "PASSWORD"],
                "desc": "Authenticate with username and password",
            },
            {
                "name": "Pass-the-Hash",
                "args": ["-u", "administrator", "-H", "HASH"],
                "desc": "Authenticate with NTLM hash",
            },
            {
                "name": "SSL Connection",
                "args": ["-u", "administrator", "-p", "PASSWORD", "-s", "-P", "5986"],
                "desc": "Connect over SSL (HTTPS)",
            },
        ],
        "command_execution": [
            {
                "name": "Whoami",
                "args": ["-u", "USER", "-p", "PASSWORD", "-c", "whoami /all"],
                "desc": "Check current user and privileges",
            },
            {
                "name": "System Info",
                "args": ["-u", "USER", "-p", "PASSWORD", "-c", "systeminfo"],
                "desc": "Get system information",
            },
            {
                "name": "Network Info",
                "args": ["-u", "USER", "-p", "PASSWORD", "-c", "ipconfig /all"],
                "desc": "Get network configuration",
            },
            {
                "name": "List Users",
                "args": ["-u", "USER", "-p", "PASSWORD", "-c", "net user"],
                "desc": "List local users",
            },
            {
                "name": "List Domain Users",
                "args": ["-u", "USER", "-p", "PASSWORD", "-c", "net user /domain"],
                "desc": "List domain users",
            },
        ],
        "enumeration": [
            {
                "name": "Enum Shares",
                "args": ["-u", "USER", "-p", "PASSWORD", "-c", "net share"],
                "desc": "List network shares",
            },
            {
                "name": "Enum Services",
                "args": ["-u", "USER", "-p", "PASSWORD", "-c", "sc query"],
                "desc": "List running services",
            },
            {
                "name": "Enum Processes",
                "args": ["-u", "USER", "-p", "PASSWORD", "-c", "tasklist"],
                "desc": "List running processes",
            },
        ],
    },
    "presets": [],
    "common_options": {
        "-i": "Target IP address (can also be positional)",
        "-u": "Username (user@domain for domain accounts)",
        "-p": "Password",
        "-H": "NTLM hash (format: LM:NT or just NT)",
        "-P": "Port number (default 5985, use 5986 for SSL)",
        "-s": "Enable SSL connection",
        "-c": "Command to execute (non-interactive mode)",
    },
    "notes": [
        "Requires evil-winrm gem installed (gem install evil-winrm)",
        "Target must have WinRM enabled (port 5985 or 5986)",
        "For domain accounts, use user@domain or domain\\\\user format",
        "Pass-the-hash only works with local admin accounts (not domain accounts)",
        "Use -c for non-interactive command execution in automated chains",
    ],
    "help_sections": [
        {
            "title": "What is Evil-WinRM?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "Evil-WinRM is a WinRM shell for pentesting that provides a fully interactive PowerShell session over Windows Remote Management.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Post-exploitation access to Windows systems",
                    "tips": [
                        "Shell access after credential discovery",
                        "Pass-the-hash attacks with NTLM hashes",
                        "File upload/download for data exfil",
                        "Command execution for enumeration",
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
                    "desc": "1. Find valid credentials (Hydra, secretsdump, etc.)\n     2. Check if WinRM is open (port 5985/5986)\n     3. Connect with evil-winrm using creds\n     4. Run commands or drop into interactive shell",
                },
                {
                    "title": "Authentication Methods",
                    "desc": "Different ways to authenticate",
                    "tips": [
                        "Password: -u user -p password",
                        "NTLM Hash: -u user -H hash (pass-the-hash)",
                        "Kerberos: -u user@domain -r REALM",
                        "SSL: Add -s flag for port 5986",
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
                        "Use -c flag for automated command execution",
                        "Check 'whoami /priv' for privilege escalation vectors",
                        "Use domain\\\\user or user@domain format for AD",
                        "Try both port 5985 and 5986 if one fails",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "Access denied: Check credentials and permissions",
                        "Connection refused: WinRM may be disabled",
                        "Timeout: Target may be filtering WinRM ports",
                        "Kerberos errors: Check realm and DNS settings",
                    ],
                ),
            ],
        },
    ],
}

# Flatten presets from categories
for category_presets in HELP["preset_categories"].values():
    HELP["presets"].extend(category_presets)


class EvilWinRMPlugin(PluginBase):
    name = "Evil-WinRM"
    tool = "evil_winrm"
    category = "lateral_movement"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution with PID tracking."""
        args = args or []

        # Build evil-winrm command
        cmd = ["evil-winrm", "-i", target]

        # Add any extra arguments
        cmd.extend(args)

        return {"cmd": cmd, "timeout": 300}  # 5 minute timeout for commands

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute Evil-WinRM."""
        args = args or []

        if log_path:
            return self._run_with_logpath(target, args, log_path)

        return self._run_legacy(target, args)

    def _run_with_logpath(self, target: str, args: List[str], log_path: str) -> int:
        """Run Evil-WinRM and write output to log_path."""
        try:
            cmd = ["evil-winrm", "-i", target]
            cmd.extend(args)

            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write("=== Evil-WinRM Session ===\n")
                fh.write(f"Target: {target}\n")
                fh.write(f"Args: {' '.join(args)}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
                )
                fh.write(f"Command: {' '.join(cmd)}\n\n")
                fh.flush()

                # Run evil-winrm
                proc = subprocess.run(
                    cmd,
                    stdout=fh,
                    stderr=subprocess.STDOUT,
                    timeout=300,  # 5 minutes
                    check=False,
                )

                fh.write(
                    f"\n\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Exit Code: {proc.returncode}\n")

                return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: Evil-WinRM command timed out after 300 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: evil-winrm not found in PATH\n")
                fh.write("Install with: gem install evil-winrm\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\nERROR: {type(e).__name__}: {e}\n")
            return 1

    def _run_legacy(self, target: str, args: List[str]) -> int:
        """Legacy execution without log_path."""
        cmd = ["evil-winrm", "-i", target]
        cmd.extend(args)

        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=300, check=False)
            return proc.returncode
        except Exception:
            return 1


plugin = EvilWinRMPlugin()
