#!/usr/bin/env python3
"""
souleyez.plugins.firmware_extract

Firmware extraction and analysis plugin using binwalk.
Extracts and analyzes router firmware images.
"""

import os
import shutil
import subprocess
import time
from typing import List

from .plugin_base import PluginBase

HELP = {
    "name": "Firmware Extract — Firmware Analysis",
    "description": (
        "Extract and analyze router firmware images using binwalk.\n\n"
        "After gaining access to a router, you can often download the firmware "
        "for offline analysis. This plugin extracts:\n"
        "- Filesystem contents (busybox, config files)\n"
        "- Hardcoded credentials\n"
        "- SSL certificates and keys\n"
        "- Backdoor accounts\n"
        "- Vulnerable binaries\n\n"
        "Quick tips:\n"
        "- Firmware files are often .bin, .img, .chk, .trx\n"
        "- Look for /etc/passwd, /etc/shadow equivalents\n"
        "- Check for telnet/SSH keys\n"
        "- Search for 'password', 'admin', 'root' strings\n"
    ),
    "usage": "souleyez jobs enqueue firmware_extract <firmware_file>",
    "examples": [
        "souleyez jobs enqueue firmware_extract /tmp/router_firmware.bin",
        'souleyez jobs enqueue firmware_extract firmware.img --args "--deep"',
    ],
    "flags": [
        ["--deep", "Deep extraction with recursive analysis"],
        ["--entropy", "Show entropy graph (detect encryption)"],
    ],
    "presets": [
        {"name": "Quick Extract", "args": [], "desc": "Standard extraction"},
        {"name": "Deep Analysis", "args": ["--deep"], "desc": "Recursive extraction"},
        {
            "name": "Entropy Check",
            "args": ["--entropy"],
            "desc": "Check for encryption",
        },
    ],
    "help_sections": [
        {
            "title": "What is Firmware Extraction?",
            "color": "cyan",
            "content": [
                (
                    "Overview",
                    [
                        "Extracts and analyzes router firmware images using binwalk",
                        "Reveals filesystem contents, configs, and embedded credentials",
                        "Useful for offline analysis after obtaining firmware file",
                    ],
                ),
                (
                    "What You Can Find",
                    [
                        "Hardcoded credentials (admin passwords, SSH keys)",
                        "Configuration files (network settings, VPN configs)",
                        "SSL certificates and private keys",
                        "Backdoor accounts created by manufacturer",
                        "Vulnerable binaries (outdated busybox, etc.)",
                    ],
                ),
            ],
        },
        {
            "title": "Usage & Examples",
            "color": "green",
            "content": [
                (
                    "Basic Extraction",
                    [
                        "souleyez jobs enqueue firmware_extract /tmp/router.bin",
                        "  → Extracts filesystem to router.bin.extracted/",
                    ],
                ),
                (
                    "Deep Analysis",
                    [
                        'souleyez jobs enqueue firmware_extract /tmp/router.bin --args "--deep"',
                        "  → Recursive extraction (nested archives)",
                    ],
                ),
                (
                    "Entropy Check",
                    [
                        'souleyez jobs enqueue firmware_extract /tmp/router.bin --args "--entropy"',
                        "  → Checks for encrypted sections",
                    ],
                ),
            ],
        },
        {
            "title": "Tips & What to Look For",
            "color": "yellow",
            "content": [
                (
                    "Interesting Files",
                    [
                        "/etc/passwd, /etc/shadow - User accounts",
                        "*.pem, *.key - SSL/SSH private keys",
                        "*config*, *password* - Configuration with creds",
                        "/etc/init.d/* - Startup scripts (backdoor locations)",
                    ],
                ),
                (
                    "Getting Firmware",
                    [
                        "Download from manufacturer support page",
                        "Extract from router via TFTP/FTP if accessible",
                        "Use hardware tools (UART, JTAG) for direct dump",
                        "Capture during OTA update (MITM)",
                    ],
                ),
                (
                    "Common Formats",
                    [
                        ".bin, .img - Raw firmware images",
                        ".chk, .trx - Vendor-specific formats",
                        ".ubi, .squashfs - Embedded Linux filesystems",
                    ],
                ),
            ],
        },
    ],
}


class FirmwareExtractPlugin(PluginBase):
    name = "Firmware Extract"
    tool = "binwalk"
    category = "discovery_collection"
    HELP = HELP

    def check_tool_available(self) -> tuple:
        """Check if binwalk is available."""
        if shutil.which("binwalk"):
            return True, None
        return False, "binwalk not found. Install with: sudo apt install binwalk"

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build binwalk command for firmware extraction."""
        args = args or []

        # Target is the firmware file path
        if not os.path.exists(target):
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Firmware file not found: {target}\n")
            return None

        # Determine extraction options
        deep = "--deep" in args
        entropy = "--entropy" in args

        cmd = ["binwalk"]

        if entropy:
            cmd.extend(["-E", target])  # Entropy analysis only
        elif deep:
            cmd.extend(["-Me", target])  # Matryoshka extraction
        else:
            cmd.extend(["-e", target])  # Standard extraction

        return {
            "cmd": cmd,
            "timeout": 1800,  # 30 minutes for large firmware
            "cwd": os.path.dirname(target) or ".",
        }

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute firmware extraction."""
        cmd_spec = self.build_command(target, args, label, log_path)
        if cmd_spec is None:
            return 1

        cmd = cmd_spec["cmd"]

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# Firmware Extraction: {target}\n")
                f.write(f"# Command: {' '.join(cmd)}\n")
                f.write(f"# Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        try:
            with open(log_path, "a") as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    timeout=cmd_spec["timeout"],
                    cwd=cmd_spec.get("cwd"),
                )

            # List extracted files
            extract_dir = f"{target}.extracted"
            if os.path.exists(extract_dir):
                with open(log_path, "a") as f:
                    f.write(f"\n\n{'='*60}\n")
                    f.write("EXTRACTED FILES\n")
                    f.write(f"{'='*60}\n\n")

                    for root, dirs, files in os.walk(extract_dir):
                        level = root.replace(extract_dir, "").count(os.sep)
                        indent = "  " * level
                        f.write(f"{indent}{os.path.basename(root)}/\n")
                        sub_indent = "  " * (level + 1)
                        for file in files[:50]:  # Limit output
                            f.write(f"{sub_indent}{file}\n")
                        if len(files) > 50:
                            f.write(
                                f"{sub_indent}... and {len(files) - 50} more files\n"
                            )

                    # Search for interesting files
                    f.write(f"\n{'='*60}\n")
                    f.write("INTERESTING FILES\n")
                    f.write(f"{'='*60}\n\n")

                    interesting = [
                        "passwd",
                        "shadow",
                        "config",
                        "password",
                        "admin",
                        "key",
                        "cert",
                        "pem",
                    ]
                    found_interesting = []

                    for root, dirs, files in os.walk(extract_dir):
                        for file in files:
                            for pattern in interesting:
                                if pattern in file.lower():
                                    found_interesting.append(os.path.join(root, file))
                                    break

                    if found_interesting:
                        for path in found_interesting[:20]:
                            f.write(f"  {path}\n")
                    else:
                        f.write("  No obvious interesting files found\n")

            return result.returncode

        except subprocess.TimeoutExpired:
            if log_path:
                with open(log_path, "a") as f:
                    f.write("\n\n# ERROR: Extraction timed out\n")
            return 124
        except FileNotFoundError:
            if log_path:
                with open(log_path, "a") as f:
                    f.write("\n\n# ERROR: binwalk not found\n")
            return 127
        except Exception as e:
            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"\n\n# ERROR: {e}\n")
            return 1


plugin = FirmwareExtractPlugin()
