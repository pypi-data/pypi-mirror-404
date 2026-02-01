#!/usr/bin/env python3
"""
souleyez.plugins.ard

ARD/VNC (Apple Remote Desktop) enumeration plugin.
Discovers VNC/ARD services on macOS systems.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "ARD — Apple Remote Desktop/VNC Enumeration",
    "description": (
        "Enumerate VNC and Apple Remote Desktop (ARD) services on macOS.\n\n"
        "macOS systems often have remote access enabled:\n"
        "- Screen Sharing (built-in VNC on port 5900)\n"
        "- Apple Remote Desktop (ARD on port 3283)\n"
        "- Remote Management for administration\n\n"
        "This plugin discovers VNC/ARD services and checks authentication.\n\n"
        "Quick tips:\n"
        "- Port 5900 = Screen Sharing (VNC)\n"
        "- Port 3283 = Apple Remote Desktop\n"
        "- Some Macs allow VNC without password!\n"
        "- ARD auth bypass vulnerabilities exist in older versions\n"
    ),
    "usage": "souleyez jobs enqueue ard <target>",
    "examples": [
        "souleyez jobs enqueue ard 192.168.1.100",
        "souleyez jobs enqueue ard 192.168.1.0/24",
    ],
    "flags": [
        ["--deep", "Full VNC/ARD enumeration"],
    ],
    "presets": [
        {"name": "Quick Scan", "args": [], "desc": "Basic VNC/ARD detection"},
        {"name": "Full Scan", "args": ["--deep"], "desc": "All VNC scripts"},
    ],
    "help_sections": [
        {
            "title": "macOS Remote Access",
            "color": "cyan",
            "content": [
                {
                    "title": "Screen Sharing",
                    "desc": "Built-in VNC server (port 5900). Uses macOS user credentials or VNC password.",
                },
                {
                    "title": "Apple Remote Desktop",
                    "desc": "Enterprise management tool (port 3283). Used by IT admins for fleet management.",
                },
                {
                    "title": "Security Notes",
                    "desc": "VNC vulnerabilities",
                    "tips": [
                        "Some Macs have VNC with no auth",
                        "ARD auth bypass (CVE-2017-13872)",
                        "Weak VNC passwords common",
                        "Traffic often unencrypted",
                    ],
                },
            ],
        }
    ],
}


class ARDPlugin(PluginBase):
    name = "ARD"
    tool = "nmap"
    category = "scanning"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build nmap command for VNC/ARD enumeration."""
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
            scripts = "vnc-info,vnc-title,realvnc-auth-bypass"
        else:
            scripts = "vnc-info"

        # VNC = 5900, ARD = 3283
        cmd = [
            "nmap",
            "-sV",
            "-p",
            "5900,3283,5901,5902,5903",
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
        """Execute VNC/ARD enumeration."""
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        cmd = cmd_spec["cmd"]

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# VNC/ARD Enumeration on {target}\n")
                f.write(f"# Ports: 5900 (VNC), 3283 (ARD)\n")
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


plugin = ARDPlugin()
