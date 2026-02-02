#!/usr/bin/env python3
"""
souleyez.plugins.upnp

UPnP (Universal Plug and Play) enumeration plugin using nmap scripts.
Discovers UPnP services, device info, and potential misconfigurations.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "UPnP — Router/IoT Discovery",
    "description": (
        "UPnP (Universal Plug and Play) enumeration for routers and IoT devices.\n\n"
        "UPnP allows devices on a network to discover each other and establish services "
        "for data sharing, communications, and entertainment. Unfortunately, many routers "
        "have UPnP enabled by default with poor security.\n\n"
        "This plugin uses nmap NSE scripts to discover and enumerate UPnP services, "
        "which can reveal:\n"
        "- Device type, manufacturer, and model\n"
        "- Firmware version information\n"
        "- Available services (port forwarding, media, etc.)\n"
        "- Potential for abuse (add/remove port mappings)\n\n"
        "Quick tips:\n"
        "- Most home routers have UPnP on port 1900 (UDP)\n"
        "- Control URLs are usually on port 49152+ (TCP)\n"
        "- Enabled UPnP can allow attackers to add port forwards\n"
        "- Look for firmware versions to find known vulnerabilities\n"
    ),
    "usage": "souleyez jobs enqueue upnp <target>",
    "examples": [
        "souleyez jobs enqueue upnp 192.168.1.1",
        "souleyez jobs enqueue upnp 192.168.1.0/24",
        'souleyez jobs enqueue upnp 10.0.0.1 --args "--script upnp-info"',
    ],
    "flags": [
        ["--full", "Run all UPnP scripts (info + brute)"],
        ["--quick", "Quick discovery only (default)"],
    ],
    "presets": [
        {"name": "Quick Discovery", "args": [], "desc": "Fast UPnP service discovery"},
        {
            "name": "Full Enumeration",
            "args": ["--full"],
            "desc": "All UPnP scripts including brute force",
        },
    ],
    "help_sections": [
        {
            "title": "What is UPnP?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "UPnP allows devices to discover and communicate with each other automatically. Routers use it for NAT traversal (port forwarding).",
                },
                {
                    "title": "Security Issues",
                    "desc": "Common UPnP vulnerabilities",
                    "tips": [
                        "Unauthenticated port forwarding (expose internal services)",
                        "Device information disclosure (model, firmware)",
                        "Known exploits for specific router firmware",
                        "Can be abused for DDoS amplification",
                    ],
                },
            ],
        },
        {
            "title": "What to Look For",
            "color": "green",
            "content": [
                {
                    "title": "Indicators",
                    "desc": "Signs of vulnerable UPnP",
                    "tips": [
                        "UPnP enabled and externally accessible",
                        "Old firmware versions with known CVEs",
                        "Add port mapping action available",
                        "Device info revealing make/model",
                    ],
                }
            ],
        },
    ],
}


class UPnPPlugin(PluginBase):
    name = "UPnP"
    tool = "nmap"  # Uses nmap under the hood
    category = "scanning"
    HELP = HELP

    def _is_root(self) -> bool:
        """Check if running as root."""
        import os

        return os.geteuid() == 0

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build nmap command for UPnP enumeration."""
        args = args or []

        # Validate target
        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        # Determine which scripts to run
        if "--full" in args:
            scripts = "upnp-info,broadcast-upnp-info"
        else:
            scripts = "upnp-info"

        # Build nmap command for UPnP
        # UPnP uses UDP 1900 for discovery (SSDP) and TCP high ports for control
        cmd = [
            "nmap",
            "-sU",
            "-sS",  # UDP and TCP SYN scan
            "-p",
            "U:1900,T:49152-49156,5000,2869",  # Common UPnP ports
            "--script",
            scripts,
            "-oN",
            "-",  # Output to stdout
            "--open",
            "-T4",
            target,
        ]

        # UPnP scan requires root (uses -sU and -sS)
        if not self._is_root():
            cmd = ["sudo", "-n"] + cmd

        return {"cmd": cmd, "timeout": 600}  # 10 minute timeout

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute UPnP enumeration."""
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        cmd = cmd_spec["cmd"]

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# UPnP Enumeration on {target}\n")
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


plugin = UPnPPlugin()
