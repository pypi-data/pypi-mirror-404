#!/usr/bin/env python3
"""
souleyez.plugins.mdns

mDNS/Bonjour discovery plugin.
Discovers Apple devices and services via multicast DNS.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "mDNS — Bonjour Service Discovery",
    "description": (
        "Discover Apple devices and services via mDNS (Bonjour).\n\n"
        "mDNS (multicast DNS) is Apple's zero-configuration networking protocol.\n"
        "Devices advertise services like:\n"
        "- AirPlay (_airplay._tcp)\n"
        "- AirDrop (_airdrop._tcp)\n"
        "- Screen Sharing (_rfb._tcp)\n"
        "- File Sharing (_afpovertcp._tcp)\n"
        "- Printers, speakers, and more\n\n"
        "This plugin uses nmap to discover mDNS-advertised services.\n\n"
        "Quick tips:\n"
        "- mDNS uses UDP port 5353\n"
        "- Broadcast discovery finds all Apple devices\n"
        "- Service records reveal device capabilities\n"
        "- Works on local network segment only\n"
    ),
    "usage": "souleyez jobs enqueue mdns <target>",
    "examples": [
        "souleyez jobs enqueue mdns 192.168.1.0/24",
        "souleyez jobs enqueue mdns 192.168.1.100",
    ],
    "flags": [
        ["--services", "Query for common service types"],
    ],
    "presets": [
        {"name": "Quick Discovery", "args": [], "desc": "Basic mDNS discovery"},
        {
            "name": "Service Query",
            "args": ["--services"],
            "desc": "Query specific services",
        },
    ],
    "help_sections": [
        {
            "title": "Common Bonjour Services",
            "color": "cyan",
            "content": [
                {"title": "_airplay._tcp", "desc": "AirPlay video streaming"},
                {"title": "_rfb._tcp", "desc": "Screen Sharing (VNC)"},
                {"title": "_afpovertcp._tcp", "desc": "AFP file sharing"},
                {"title": "_smb._tcp", "desc": "SMB file sharing"},
                {"title": "_ssh._tcp", "desc": "SSH remote access"},
                {"title": "_printer._tcp", "desc": "Network printers"},
            ],
        }
    ],
}


class MDNSPlugin(PluginBase):
    name = "mDNS"
    tool = "nmap"
    category = "scanning"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build nmap command for mDNS discovery."""
        args = args or []

        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        # Use broadcast-dns-service-discovery for mDNS
        if "--services" in args:
            scripts = "dns-service-discovery,broadcast-dns-service-discovery"
        else:
            scripts = "dns-service-discovery"

        cmd = [
            "nmap",
            "-sU",
            "-p",
            "5353",
            "--script",
            scripts,
            "-oN",
            "-",
            "--open",
            "-T4",
            target,
        ]

        return {"cmd": cmd, "timeout": 300}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute mDNS discovery."""
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        cmd = cmd_spec["cmd"]

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# mDNS/Bonjour Discovery on {target}\n")
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


plugin = MDNSPlugin()
