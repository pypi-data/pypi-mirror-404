#!/usr/bin/env python3
"""
souleyez.plugins.afp

AFP (Apple Filing Protocol) enumeration plugin.
Discovers AFP shares on macOS systems.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "AFP — Apple File Sharing Enumeration",
    "description": (
        "Enumerate AFP (Apple Filing Protocol) shares on macOS systems.\n\n"
        "AFP is Apple's native file sharing protocol, still used on macOS for:\n"
        "- Time Machine backups\n"
        "- Personal file sharing\n"
        "- Legacy Mac networks\n\n"
        "This plugin uses nmap NSE scripts to discover AFP shares and server info.\n\n"
        "Quick tips:\n"
        "- Default port is 548 (TCP)\n"
        "- Look for guest access (no password required)\n"
        "- Time Machine backups may contain sensitive data\n"
        "- AFP has known vulnerabilities in older versions\n"
    ),
    "usage": "souleyez jobs enqueue afp <target>",
    "examples": [
        "souleyez jobs enqueue afp 192.168.1.100",
        "souleyez jobs enqueue afp 192.168.1.0/24",
    ],
    "flags": [
        ["--deep", "Full AFP enumeration with all scripts"],
    ],
    "presets": [
        {"name": "Quick Scan", "args": [], "desc": "Basic AFP enumeration"},
        {"name": "Full Scan", "args": ["--deep"], "desc": "All AFP scripts"},
    ],
    "help_sections": [
        {
            "title": "What is AFP?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "AFP (Apple Filing Protocol) is Apple's native file sharing protocol, optimized for macOS features like resource forks and metadata.",
                },
                {
                    "title": "Security Notes",
                    "desc": "AFP security considerations",
                    "tips": [
                        "Guest access often enabled by default",
                        "Credentials transmitted in cleartext (older versions)",
                        "Time Machine backups may contain full disk images",
                        "Path traversal vulnerabilities in some versions",
                    ],
                },
            ],
        }
    ],
}


class AFPPlugin(PluginBase):
    name = "AFP"
    tool = "nmap"
    category = "scanning"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build nmap command for AFP enumeration."""
        args = args or []

        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        # Determine scripts
        if "--deep" in args:
            scripts = "afp-serverinfo,afp-showmount,afp-brute,afp-path-vuln"
        else:
            scripts = "afp-serverinfo,afp-showmount"

        cmd = [
            "nmap",
            "-sV",
            "-p",
            "548",
            "--script",
            scripts,
            "-oN",
            "-",
            "--open",
            "-T4",
            target,
        ]

        return {"cmd": cmd, "timeout": 600}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute AFP enumeration."""
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        cmd = cmd_spec["cmd"]

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# AFP Enumeration on {target}\n")
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
                    f.write("\n\n# ERROR: Scan timed out\n")
            return 124
        except Exception as e:
            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"\n\n# ERROR: {e}\n")
            return 1


plugin = AFPPlugin()
