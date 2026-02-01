#!/usr/bin/env python3
"""
souleyez.plugins.john

John the Ripper password cracking plugin.
"""

import os
import subprocess
import time
from typing import List

from .plugin_base import PluginBase

HELP = {
    "name": "John the Ripper — Password Cracker",
    "description": (
        "The legendary password cracker!\n\n"
        "John the Ripper is perfect for cracking Linux/Unix password hashes from /etc/shadow. "
        "Simpler than hashcat for basic attacks and automatically detects hash formats.\n\n"
        "Perfect for:\n"
        "- Linux /etc/shadow files (use 'unshadow' first)\n"
        "- Windows LM/NTLM hashes\n"
        "- ZIP/RAR password-protected archives\n"
        "- Auto-detecting hash types\n\n"
        "Quick tips:\n"
        "- Use 'unshadow passwd shadow > hashes' to prepare Linux files\n"
        "- John auto-detects most hash formats\n"
        "- Use --show to see cracked passwords\n"
        "- Cracked passwords stored in ~/.john/john.pot\n"
    ),
    "usage": "john hashfile [options]",
    "examples": [
        "john hashes.txt  # Auto-detect and crack with default wordlist",
        "john hashes.txt --wordlist=data/wordlists/top100.txt  # Dictionary attack",
        "john --show hashes.txt  # Show cracked passwords",
        "john --format=NT hashes.txt  # Force NTLM format",
        "john --incremental hashes.txt  # Brute force attack",
    ],
    "preset_categories": {
        "quick": [
            {
                "name": "Quick Dictionary (Top 1000)",
                "description": "Fast dictionary attack with top 1000 passwords",
                "args": "--wordlist=data/wordlists/top100.txt",
            },
            {
                "name": "Dictionary Attack (RockYou)",
                "description": "Full dictionary attack with rockyou.txt",
                "args": "--wordlist=data/wordlists/top100.txt",
            },
        ],
        "formats": [
            {
                "name": "MD5 Crypt (Linux Shadow)",
                "description": "Linux /etc/shadow MD5 hashes",
                "args": "--format=md5crypt",
            },
            {
                "name": "SHA-512 Crypt (Modern Linux)",
                "description": "Modern Linux /etc/shadow SHA-512 hashes",
                "args": "--format=sha512crypt",
            },
            {
                "name": "NTLM (Windows)",
                "description": "Windows NTLM password hashes",
                "args": "--format=NT",
            },
        ],
        "advanced": [
            {
                "name": "Incremental Brute Force",
                "description": "Try all possible combinations (slow but thorough)",
                "args": "--incremental",
            },
            {
                "name": "Single Crack Mode",
                "description": "Use usernames and GECOS info to generate passwords",
                "args": "--single",
            },
            {
                "name": "Rules with Wordlist",
                "description": "Apply mutation rules to wordlist",
                "args": "--wordlist=data/wordlists/top100.txt --rules",
            },
        ],
    },
    "help_sections": [
        {
            "title": "What is John the Ripper?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "John the Ripper is the legendary password cracker, perfect for Linux/Unix shadow files with automatic hash format detection.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Simpler than hashcat for basic cracking",
                    "tips": [
                        "Crack Linux /etc/shadow files (use unshadow first)",
                        "Auto-detect hash formats",
                        "Windows LM/NTLM hashes",
                        "ZIP/RAR password-protected archives",
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
                    "desc": "1. Prepare hashes (unshadow passwd shadow > hashes)\n     2. Run john with wordlist or incremental mode\n     3. Use --show to see cracked passwords\n     4. Results saved in ~/.john/john.pot",
                },
                {
                    "title": "Attack Modes",
                    "desc": "Different cracking strategies",
                    "tips": [
                        "Dictionary: john --wordlist=wordlist.txt hashes",
                        "Incremental: john --incremental hashes (brute-force)",
                        "Single: john --single hashes (uses usernames)",
                        "Rules: john --rules --wordlist=wordlist.txt hashes",
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
                        "Use unshadow to combine passwd and shadow files",
                        "John auto-detects most hash formats",
                        "Check progress with --show",
                        "Cracked passwords in ~/.john/john.pot",
                        "Use --format to force specific hash type",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "No hash format: Use --format=<type> to specify",
                        "Slow progress: Try different attack mode or wordlist",
                        "Can't find john.pot: Check ~/.john/ directory",
                        "Unshadow needed: Combine passwd and shadow first",
                    ],
                ),
            ],
        },
    ],
}


class JohnPlugin(PluginBase):
    """John the Ripper password cracking plugin."""

    name = "john"
    tool = "john"
    category = "credential_access"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution with PID tracking."""
        if not target:
            if log_path:
                with open(log_path, "w") as f:
                    f.write("ERROR: Hash file path is required\n")
            return None

        # Validate hash file exists
        if not os.path.isfile(target):
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Hash file not found: {target}\n")
            return None

        args = args or []

        # John syntax: john [options] hashfile
        args_list = args if isinstance(args, list) else args.split()
        cmd = ["john"] + args_list + [target]

        return {"cmd": cmd, "timeout": 7200}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """
        Execute john and write output to log_path.

        Note: 'target' is used as the hash file path for this plugin.
        """
        if not target:
            raise ValueError("Hash file path is required")

        # Validate hash file exists
        if not os.path.isfile(target):
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Hash file not found: {target}\n")
            return 1

        if args is None:
            args = []

        # Build john command - simple! Just john [options] hashfile
        args_list = args if isinstance(args, list) else args.split()
        cmd = ["john"] + args_list + [target]

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# John the Ripper password cracking\n")
                f.write(f"# Hash file: {target}\n")
                f.write(f"# Command: {' '.join(cmd)}\n")
                f.write(f"# Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3600  # 1 hour timeout
            )

            if log_path:
                with open(log_path, "a") as f:
                    f.write(result.stdout)
                    if result.stderr:
                        f.write(f"\n\n# Errors:\n{result.stderr}\n")

                    # Add helper to show cracked passwords
                    f.write(f"\n\n# To view cracked passwords, run:\n")
                    f.write(f"# john --show {target}\n")

            return result.returncode

        except subprocess.TimeoutExpired:
            if log_path:
                with open(log_path, "a") as f:
                    f.write("\n\n# ERROR: Command timed out after 1 hour\n")
            return 124
        except Exception as e:
            if log_path:
                with open(log_path, "a") as f:
                    f.write(f"\n\n# ERROR: {str(e)}\n")
            return 1


# Export plugin instance
plugin = JohnPlugin()
