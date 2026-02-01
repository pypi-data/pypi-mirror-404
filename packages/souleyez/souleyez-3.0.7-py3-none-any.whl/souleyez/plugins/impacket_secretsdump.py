#!/usr/bin/env python3
"""
souleyez.plugins.impacket_secretsdump - Dump credentials from SAM/NTDS/LSA
"""

import subprocess
import time
from typing import List

from .impacket_common import find_impacket_command
from .plugin_base import PluginBase

HELP = {
    "name": "Impacket secretsdump - Credential Extraction",
    "description": (
        "Need to dump credentials from Windows systems?\n\n"
        "secretsdump extracts password hashes, Kerberos keys, and plaintext passwords "
        "from SAM, SECURITY, SYSTEM, and NTDS.dit files. It can operate remotely with "
        "valid credentials or locally on extracted registry hives.\n\n"
        "Use secretsdump after getting admin access to:\n"
        "- Dump local SAM database hashes\n"
        "- Extract Domain Controller NTDS.dit (all domain hashes)\n"
        "- Retrieve LSA secrets (service account passwords)\n"
        "- Get cached domain credentials\n\n"
        "Quick tips:\n"
        "- Requires admin/domain admin credentials\n"
        "- Use -just-dc for DC credential extraction\n"
        "- Output includes NT hashes for pass-the-hash attacks\n"
        "- Can work with local files or remote connections\n"
    ),
    "usage": 'souleyez jobs enqueue impacket-secretsdump <target> --args "DOMAIN/user:pass@host"',
    "examples": [
        'souleyez jobs enqueue impacket-secretsdump 10.0.0.82 --args "CONTOSO/Administrator:Password123@10.0.0.82"',
        'souleyez jobs enqueue impacket-secretsdump 10.0.0.82 --args "Administrator:Password123@10.0.0.82 -just-dc"',
        'souleyez jobs enqueue impacket-secretsdump 10.0.0.82 --args "Administrator@10.0.0.82 -hashes :8846f7eaee8fb117ad06bdd830b7586c"',
    ],
    "flags": [
        ["-just-dc", "Extract only NTDS.DIT data (Domain Controller)"],
        ["-just-dc-ntlm", "Extract only NTLM hashes from NTDS.DIT"],
        ["-just-dc-user <user>", "Extract specific user credentials"],
        ["-hashes <LM:NT>", "Pass-the-hash authentication"],
        ["-history", "Dump password history"],
    ],
    "preset_categories": {
        "domain_controller": [
            {
                "name": "Extract NTDS.dit (All Domain Hashes)",
                "args": ["-just-dc", "-outputfile", "domain_hashes"],
                "desc": "Extract all domain password hashes from DC (requires DA)",
            },
            {
                "name": "Extract NTDS.dit (NTLM Only)",
                "args": ["-just-dc-ntlm", "-outputfile", "ntlm_hashes"],
                "desc": "Extract only NTLM hashes (faster, smaller output)",
            },
            {
                "name": "Extract Specific User",
                "args": ["-just-dc-user", "administrator", "-outputfile", "admin_hash"],
                "desc": "Extract credentials for specific domain user",
            },
            {
                "name": "Extract with Password History",
                "args": ["-just-dc", "-history", "-outputfile", "hashes_with_history"],
                "desc": "Extract current and historical password hashes",
            },
        ],
        "local_sam": [
            {
                "name": "Dump Local SAM",
                "args": ["-sam", "-outputfile", "local_hashes"],
                "desc": "Extract local user password hashes from SAM",
            },
            {
                "name": "Dump LSA Secrets",
                "args": ["-security", "-outputfile", "lsa_secrets"],
                "desc": "Extract LSA secrets (cached credentials, service passwords)",
            },
            {
                "name": "Dump Everything (SAM + LSA + Cached)",
                "args": [
                    "-sam",
                    "-security",
                    "-system",
                    "-outputfile",
                    "all_credentials",
                ],
                "desc": "Complete local credential extraction",
            },
        ],
        "pass_the_hash": [
            {
                "name": "Use Pass-the-Hash (NTLM)",
                "args": [
                    "-hashes",
                    ":<ntlm_hash>",
                    "-just-dc-ntlm",
                    "-outputfile",
                    "pth_dump",
                ],
                "desc": "Authenticate with NTLM hash instead of password",
            }
        ],
    },
    "presets": [],
}

# Flatten presets
for category_presets in HELP["preset_categories"].values():
    HELP["presets"].extend(category_presets)

HELP["help_sections"] = [
    {
        "title": "What is secretsdump?",
        "color": "cyan",
        "content": [
            {
                "title": "Overview",
                "desc": "secretsdump extracts password hashes, Kerberos keys, and plaintext passwords from SAM, SECURITY, SYSTEM, and NTDS.dit files on Windows systems.",
            },
            {
                "title": "Use Cases",
                "desc": "Credential extraction after gaining admin access",
                "tips": [
                    "Dump local SAM database hashes",
                    "Extract Domain Controller NTDS.dit (all domain hashes)",
                    "Retrieve LSA secrets (service passwords)",
                    "Get cached domain credentials",
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
                "desc": "1. Obtain admin/domain admin credentials\n     2. Use -just-dc for DC hash extraction\n     3. Save output with -outputfile\n     4. Crack hashes or use for pass-the-hash",
            },
            {
                "title": "Key Options",
                "desc": "Essential secretsdump parameters",
                "tips": [
                    "-just-dc: Extract NTDS.dit only (DC)",
                    "-just-dc-ntlm: NTLM hashes only (faster)",
                    "-just-dc-user <user>: Specific user only",
                    "-hashes: Pass-the-hash authentication",
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
                    "Use -outputfile to save all hashes",
                    "Requires admin (local SAM) or Domain Admin (NTDS)",
                    "Output includes NT hashes for pass-the-hash",
                    "Use -history to get password history",
                    "Crack with hashcat mode 1000 (NTLM)",
                ],
            ),
            (
                "Common Issues:",
                [
                    "Access denied: Verify admin/DA credentials",
                    "Connection timeout: Check network connectivity to DC",
                    "Empty output: May need different authentication method",
                    "Permission errors: Ensure proper privilege level",
                ],
            ),
        ],
    },
]


class ImpacketSecretsdumpPlugin(PluginBase):
    name = "Impacket secretsdump"
    tool = "impacket-secretsdump"
    category = "credential_access"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution with PID tracking."""
        args = args or []

        # Replace <target> placeholder
        args = [arg.replace("<target>", target) for arg in args]

        # Find the correct command (varies by install: apt vs pipx)
        secretsdump_cmd = find_impacket_command("secretsdump")
        if not secretsdump_cmd:
            return None  # Tool not installed

        # Build command (args should include credentials)
        cmd = [secretsdump_cmd] + args

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute impacket-secretsdump and write output to log_path."""

        args = args or []

        # Replace <target> placeholder
        args = [arg.replace("<target>", target) for arg in args]

        # Find the correct command (varies by install: apt vs pipx)
        secretsdump_cmd = find_impacket_command("secretsdump")
        if not secretsdump_cmd:
            if log_path:
                with open(log_path, "w", encoding="utf-8") as fh:
                    fh.write("ERROR: secretsdump not found. Install with:\n")
                    fh.write("  Kali: sudo apt install python3-impacket\n")
                    fh.write("  Ubuntu: pipx install impacket\n")
            return 1

        # Build command
        cmd = [secretsdump_cmd]

        # Add target/credentials (should be in args like "DOMAIN/user:pass@host")
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
            # Create metadata header
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write(f"=== Plugin: Impacket secretsdump ===\n")
                fh.write(f"Target: {target}\n")
                fh.write(f"Args: {args}\n")
                fh.write(f"Label: {label}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Command: {' '.join(cmd)}\n\n")

            # Run secretsdump
            proc = subprocess.run(
                cmd, capture_output=True, timeout=300, check=False, text=True
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
                fh.write("\n\nERROR: secretsdump timed out after 300 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write("ERROR: impacket-secretsdump not found in PATH\n")
                fh.write("Install: apt install python3-impacket\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\n\nERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = ImpacketSecretsdumpPlugin()
