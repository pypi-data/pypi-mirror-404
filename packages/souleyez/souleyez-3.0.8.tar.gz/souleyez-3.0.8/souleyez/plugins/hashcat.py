#!/usr/bin/env python3
"""
souleyez.plugins.hashcat

Hashcat password cracking plugin.
"""

import os
import subprocess
import time
from typing import List

from .plugin_base import PluginBase

HELP = {
    "name": "Hashcat — Advanced Password Recovery",
    "description": (
        "Found password hashes? Time to crack them!\n\n"
        "Hashcat is the world's fastest password cracker, supporting 300+ hash types including "
        "NTLM, MD5, SHA, bcrypt, and more. Uses GPU acceleration for maximum speed.\n\n"
        "Perfect for cracking hashes obtained from:\n"
        "- Windows SAM/NTDS dumps (NTLM)\n"
        "- Linux /etc/shadow (SHA512crypt, MD5crypt)\n"
        "- Database password hashes\n"
        "- Web application hashes\n\n"
        "Quick tips:\n"
        "- GPU cracking is 100x+ faster than CPU\n"
        "- Start with dictionary attacks, then rules, then masks\n"
        "- Use --show to see already-cracked hashes\n"
        "- Cracked passwords auto-imported back to credentials database\n"
    ),
    "usage": "hashcat -m <hash-type> <hash-file> <wordlist>",
    "examples": [
        "hashcat -m 1000 ntlm_hashes.txt data/wordlists/top100.txt  # Crack NTLM",
        "hashcat -m 1800 shadow_hashes.txt data/wordlists/top100.txt  # Crack Linux SHA512",
        "hashcat -m 0 md5_hashes.txt data/wordlists/top100.txt -r rules/best64.rule  # MD5 with rules",
        "hashcat -m 1000 hashes.txt -a 3 ?a?a?a?a?a?a  # NTLM mask attack (6 chars)",
    ],
    "common_hash_types": [
        ["0", "MD5"],
        ["100", "SHA1"],
        ["1000", "NTLM (Windows)"],
        ["1800", "SHA-512 (Unix)"],
        ["3200", "bcrypt"],
        ["5600", "NetNTLMv2"],
        ["13100", "Kerberos 5 TGS-REP"],
    ],
    "preset_categories": {
        "windows": [
            {
                "name": "NTLM Fast",
                "args": ["-m", "1000", "-a", "0", "--workload-profile", "3"],
                "desc": "Crack Windows NTLM hashes (fast dictionary)",
            },
            {
                "name": "NTLM with Rules",
                "args": ["-m", "1000", "-a", "0", "-r", "rules/best64.rule"],
                "desc": "Crack NTLM with best64 rules",
            },
            {
                "name": "NetNTLMv2",
                "args": ["-m", "5600", "-a", "0"],
                "desc": "Crack NetNTLMv2 hashes",
            },
        ],
        "linux": [
            {
                "name": "SHA-512 (shadow)",
                "args": ["-m", "1800", "-a", "0"],
                "desc": "Crack Linux SHA-512 shadow hashes",
            },
            {
                "name": "MD5 (shadow)",
                "args": ["-m", "500", "-a", "0"],
                "desc": "Crack Linux MD5 shadow hashes",
            },
        ],
        "web": [
            {
                "name": "MD5",
                "args": ["-m", "0", "-a", "0"],
                "desc": "Crack raw MD5 hashes",
            },
            {
                "name": "bcrypt",
                "args": ["-m", "3200", "-a", "0"],
                "desc": "Crack bcrypt hashes (slow)",
            },
        ],
    },
    "presets": [],  # Will be flattened from categories
    "notes": [
        "Requires hashcat installed (apt install hashcat)",
        "GPU acceleration recommended for performance",
        "Hashes must be in correct format for hash type",
        "Use hashcat --example-hashes to see hash formats",
        "Cracked results automatically imported to credentials",
    ],
    "category": "auxiliary",
}

# Flatten presets
for category_presets in HELP["preset_categories"].values():
    HELP["presets"].extend(category_presets)

HELP["help_sections"] = [
    {
        "title": "What is Hashcat?",
        "color": "cyan",
        "content": [
            {
                "title": "Overview",
                "desc": "Hashcat is the world's fastest password cracker, supporting 300+ hash types with GPU acceleration for maximum speed.",
            },
            {
                "title": "Use Cases",
                "desc": "Crack password hashes from various sources",
                "tips": [
                    "Windows NTLM hashes (mode 1000)",
                    "Linux shadow files (mode 1800 for SHA-512)",
                    "NetNTLMv2 from Responder (mode 5600)",
                    "Kerberos TGS-REP (mode 13100)",
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
                "desc": "1. Identify hash type (--example-hashes)\n     2. Start with dictionary attack (-a 0)\n     3. Apply rules for mutations (-r rules/best64.rule)\n     4. Use --show to see cracked passwords",
            },
            {
                "title": "Attack Modes",
                "desc": "Different cracking strategies",
                "tips": [
                    "Dictionary: -a 0 (fastest, use wordlists)",
                    "Combinator: -a 1 (combine two wordlists)",
                    "Mask: -a 3 (brute-force with patterns)",
                    "Rules: -r to mutate dictionary words",
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
                    "GPU is 100x+ faster than CPU",
                    "Start with dictionary, then rules, then masks",
                    "Use --show to check progress",
                    "NTLM is fast to crack (billions/sec on GPU)",
                    "bcrypt is very slow (security feature)",
                ],
            ),
            (
                "Common Issues:",
                [
                    "No GPU detected: Install correct drivers (CUDA/ROCm)",
                    "Out of memory: Reduce wordlist size or use -w lower",
                    "Wrong format: Verify hash type with --example-hashes",
                    "Too slow: bcrypt/scrypt are intentionally slow",
                ],
            ),
        ],
    },
]


class HashcatPlugin(PluginBase):
    """Hashcat password cracking plugin."""

    name = "hashcat"
    tool = "hashcat"
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

        # Hashcat syntax: hashcat [options] hashfile [wordlist]
        # Insert hashfile before wordlist (last positional arg)
        args_list = args if isinstance(args, list) else args.split()

        # Find last argument that looks like a file path (wordlist)
        wordlist_idx = None
        for i in range(len(args_list) - 1, -1, -1):
            arg = args_list[i]
            if not arg.startswith("-") and ("/" in arg or os.path.isfile(arg)):
                wordlist_idx = i
                break

        if wordlist_idx is not None:
            cmd = (
                ["hashcat"]
                + args_list[:wordlist_idx]
                + [target]
                + args_list[wordlist_idx:]
            )
        else:
            cmd = ["hashcat"] + args_list + [target]

        return {"cmd": cmd, "timeout": 7200}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """
        Execute hashcat and write output to log_path.

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

        # Build hashcat command
        # Hashcat syntax: hashcat [options] hashfile [wordlist]
        # Need to insert hashfile before the wordlist (last positional arg)
        # Find the last non-option argument that looks like a file path (wordlist)
        args_list = args if isinstance(args, list) else args.split()

        # Find last argument that looks like a file path (contains / or is a file)
        wordlist_idx = None
        for i in range(len(args_list) - 1, -1, -1):
            arg = args_list[i]
            if not arg.startswith("-") and ("/" in arg or os.path.isfile(arg)):
                wordlist_idx = i
                break

        if wordlist_idx is not None:
            # Insert hashfile before wordlist
            cmd = (
                ["hashcat"]
                + args_list[:wordlist_idx]
                + [target]
                + args_list[wordlist_idx:]
            )
        else:
            # No wordlist found, append hashfile at end
            cmd = ["hashcat"] + args_list + [target]

        if log_path:
            with open(log_path, "w") as f:
                f.write(f"# Hashcat password cracking\n")
                f.write(f"# Hash file: {target}\n")
                f.write(f"# Args input: {args}\n")
                f.write(f"# Args list: {args_list}\n")
                f.write(f"# Wordlist idx: {wordlist_idx}\n")
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
plugin = HashcatPlugin()
