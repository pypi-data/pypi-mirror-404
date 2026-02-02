#!/usr/bin/env python3
"""
souleyez.plugins.impacket_smbclient - SMB client for file operations
"""

import subprocess
import time
from typing import List

from .impacket_common import find_impacket_command
from .plugin_base import PluginBase

HELP = {
    "name": "Impacket smbclient - SMB File Operations",
    "description": (
        "Need to browse and download files from SMB shares?\n\n"
        "smbclient provides an interactive SMB client for file operations, similar to "
        "FTP. It can list, download, upload, and delete files on remote SMB shares.\n\n"
        "Use smbclient after discovering shares to:\n"
        "- Browse share contents recursively\n"
        "- Download sensitive files and documents\n"
        "- Upload tools and payloads\n"
        "- Enumerate accessible data\n\n"
        "Quick tips:\n"
        "- Can work without authentication (null sessions)\n"
        "- Use 'ls' to list files, 'get' to download\n"
        "- Supports wildcards for bulk operations\n"
        "- Can use pass-the-hash authentication\n"
    ),
    "usage": 'souleyez jobs enqueue impacket-smbclient <target> --args "DOMAIN/user:pass@host"',
    "examples": [
        'souleyez jobs enqueue impacket-smbclient 10.0.0.82 --args "Administrator:Password123@10.0.0.82"',
        'souleyez jobs enqueue impacket-smbclient 10.0.0.82 --args "guest@10.0.0.82 -no-pass"',
        'souleyez jobs enqueue impacket-smbclient 10.0.0.82 --args "Administrator@10.0.0.82 -hashes :8846f7eaee8fb117ad06bdd830b7586c"',
    ],
    "flags": [
        ["-hashes <LM:NT>", "Pass-the-hash authentication"],
        ["-no-pass", "Don't ask for password (null session)"],
        ["-k", "Use Kerberos authentication"],
        ["-inputfile <file>", "Execute commands from file"],
    ],
    "preset_categories": {
        "browse": [
            {
                "name": "Anonymous Login (Null Session)",
                "args": ["-no-pass"],
                "desc": "Attempt anonymous SMB connection",
            },
            {
                "name": "Browse Shares (Authenticated)",
                "args": [],
                "desc": "Connect and list available shares with credentials",
            },
        ],
        "download": [
            {
                "name": "Execute Commands from File",
                "args": ["-inputfile", "commands.txt"],
                "desc": "Execute SMB commands from file (e.g., 'shares', 'use C$', 'ls')",
            }
        ],
        "authentication": [
            {
                "name": "Pass-the-Hash (NTLM)",
                "args": ["-hashes", ":<ntlm_hash>"],
                "desc": "Authenticate with NTLM hash",
            },
            {
                "name": "Kerberos Authentication",
                "args": ["-k", "-no-pass"],
                "desc": "Use Kerberos ticket for SMB access",
            },
        ],
    },
    "presets": [],
}

# Flatten presets
for category_presets in HELP["preset_categories"].values():
    HELP["presets"].extend(category_presets)

HELP["help_sections"] = [
    {
        "title": "What is smbclient?",
        "color": "cyan",
        "content": [
            {
                "title": "Overview",
                "desc": "smbclient provides an interactive SMB client for file operations, similar to FTP, allowing you to browse, download, upload, and delete files on remote SMB shares.",
            },
            {
                "title": "Use Cases",
                "desc": "SMB file operations and data collection",
                "tips": [
                    "Browse share contents recursively",
                    "Download sensitive files and documents",
                    "Upload tools and payloads",
                    "Enumerate accessible data",
                ],
            },
        ],
    },
    {
        "title": "How to Use",
        "color": "green",
        "content": [
            {
                "title": "Basic Workflow",
                "desc": "1. Connect to target with credentials\n     2. List shares and select target share\n     3. Browse files with ls command\n     4. Download files with get command",
            },
            {
                "title": "Key Commands",
                "desc": "Common smbclient operations",
                "tips": [
                    "ls: List files in current directory",
                    "get <file>: Download file",
                    "put <file>: Upload file",
                    "cd <dir>: Change directory",
                ],
            },
        ],
    },
    {
        "title": "Tips & Best Practices",
        "color": "yellow",
        "content": [
            (
                "Best Practices:",
                [
                    "Can work without authentication (null sessions)",
                    "Use -share to connect directly to specific share",
                    "Supports wildcards for bulk operations",
                    "Can use pass-the-hash authentication",
                    "Save interesting files for analysis",
                ],
            ),
            (
                "Common Issues:",
                [
                    "Access denied: Try guest or null session",
                    "Share not found: List shares first without -share",
                    "Connection refused: Verify SMB (445) is open",
                    "Timeout errors: Check network connectivity",
                ],
            ),
        ],
    },
]


class ImpacketSmbclientPlugin(PluginBase):
    name = "Impacket smbclient"
    tool = "impacket-smbclient"
    category = "discovery_collection"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution with PID tracking."""
        args = args or []

        # Replace <target> placeholder
        args = [arg.replace("<target>", target) for arg in args]

        # Find the correct command (varies by install: apt vs pipx)
        smbclient_cmd = find_impacket_command("smbclient")
        if not smbclient_cmd:
            return None  # Tool not installed

        # Build command (args should include credentials)
        cmd = [smbclient_cmd] + args

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute impacket-smbclient and write output to log_path."""

        args = args or []

        # Replace <target> placeholder
        args = [arg.replace("<target>", target) for arg in args]

        # Find the correct command (varies by install: apt vs pipx)
        smbclient_cmd = find_impacket_command("smbclient")
        if not smbclient_cmd:
            if log_path:
                with open(log_path, "w", encoding="utf-8") as fh:
                    fh.write("ERROR: smbclient not found. Install with:\n")
                    fh.write("  Kali: sudo apt install python3-impacket\n")
                    fh.write("  Ubuntu: pipx install impacket\n")
            return 1

        # Build command
        cmd = [smbclient_cmd]

        # Add args (should include credentials like "DOMAIN/user:pass@host")
        cmd.extend(args)

        if not log_path:
            try:
                proc = subprocess.run(cmd, capture_output=True, timeout=60, check=False)
                return proc.returncode
            except Exception:
                return 1

        try:
            # Create metadata header
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write(f"=== Plugin: Impacket smbclient ===\n")
                fh.write(f"Target: {target}\n")
                fh.write(f"Args: {args}\n")
                fh.write(f"Label: {label}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Command: {' '.join(cmd)}\n\n")

            # Run smbclient (non-interactive)
            # Note: For interactive mode, would need special handling
            proc = subprocess.run(
                cmd, capture_output=True, timeout=60, check=False, text=True
            )

            # Write output
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                if proc.stdout:
                    fh.write(proc.stdout)

                if proc.stderr:
                    fh.write(f"\n\n# Error output:\n{proc.stderr}\n")

                fh.write(
                    f"\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Exit Code: {proc.returncode}\n")

            return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\n\nERROR: smbclient timed out after 60 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write("ERROR: impacket-smbclient not found in PATH\n")
                fh.write("Install: apt install python3-impacket\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\n\nERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = ImpacketSmbclientPlugin()
