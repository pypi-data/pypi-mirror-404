#!/usr/bin/env python3
"""
souleyez.plugins.rdp_sec_check - RDP security configuration checker
"""

import subprocess
import time
from typing import List

from .plugin_base import PluginBase

HELP = {
    "name": "RDP Security Check",
    "description": (
        "Check RDP security configuration and identify misconfigurations.\n\n"
        "rdp-sec-check tests Remote Desktop Protocol security settings:\n"
        "- Network Level Authentication (NLA) requirements\n"
        "- Encryption levels (None/Low/Client/High/FIPS)\n"
        "- Supported protocols (RDP/TLS/CredSSP)\n\n"
        "Use when:\n"
        "- RDP (port 3389) is detected on a target\n"
        "- Assessing Windows server security posture\n"
        "- Checking for BlueKeep/MITM vulnerability prerequisites\n"
    ),
    "usage": 'souleyez jobs enqueue rdp-sec-check <target> --args "<target>"',
    "examples": [
        'souleyez jobs enqueue rdp-sec-check 10.0.0.1 --args "10.0.0.1"',
        'souleyez jobs enqueue rdp-sec-check 10.0.0.1 --args "10.0.0.1:3389"',
    ],
    "flags": [
        ["<target>", "Target IP or IP:port (default port 3389)"],
    ],
    "preset_categories": {
        "scanning": [
            {
                "name": "RDP Security Scan",
                "args": ["<target>"],
                "desc": "Check RDP security configuration",
            },
        ]
    },
    "presets": [],
}

# Flatten presets
for category_presets in HELP["preset_categories"].values():
    HELP["presets"].extend(category_presets)


class RdpSecCheckPlugin(PluginBase):
    name = "RDP Security Check"
    tool = "rdp-sec-check"
    category = "scanning"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution."""
        args = args or [target]
        args = [arg.replace("<target>", target) for arg in args]

        cmd = ["rdp-sec-check"]
        cmd.extend(args)

        return {"cmd": cmd, "timeout": 300}  # 5 minutes should be plenty

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute rdp-sec-check and write output to log_path."""
        args = args or [target]
        args = [arg.replace("<target>", target) for arg in args]

        cmd = ["rdp-sec-check"]
        cmd.extend(args)

        if not log_path:
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=300, check=False
                )
                return proc.returncode
            except Exception:
                return 1

        try:
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write(f"=== Plugin: RDP Security Check ===\n")
                fh.write(f"Target: {target}\n")
                fh.write(f"Args: {args}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Command: {' '.join(cmd)}\n\n")

            proc = subprocess.run(
                cmd, capture_output=True, timeout=300, check=False, text=True
            )

            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                if proc.stdout:
                    fh.write(proc.stdout)
                if proc.stderr:
                    fh.write(f"\n{proc.stderr}")
                fh.write(
                    f"\n\n=== Completed: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} ===\n"
                )
                fh.write(f"Exit Code: {proc.returncode}\n")

            return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\n\nERROR: rdp-sec-check timed out after 300 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write("ERROR: rdp-sec-check not found in PATH\n")
                fh.write("Install on Kali: sudo apt install rdp-sec-check\n")
                fh.write("Install on Ubuntu: See docs for manual installation\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\n\nERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = RdpSecCheckPlugin()
