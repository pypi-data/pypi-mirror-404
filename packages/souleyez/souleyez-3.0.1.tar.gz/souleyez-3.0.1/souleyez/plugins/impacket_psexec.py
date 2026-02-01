#!/usr/bin/env python3
"""
souleyez.plugins.impacket_psexec - Remote command execution via SMB
"""

import subprocess
import time
from typing import List

from .impacket_common import find_impacket_command
from .plugin_base import PluginBase

HELP = {
    "name": "Impacket psexec - Remote Command Execution",
    "description": (
        "Need to execute commands on remote Windows systems?\n\n"
        "psexec provides remote command execution using SMB and named pipes, similar to "
        "Sysinternals PsExec. It uploads a service binary and executes commands with "
        "SYSTEM privileges.\n\n"
        "Use psexec after obtaining admin credentials to:\n"
        "- Execute commands remotely with SYSTEM privileges\n"
        "- Get interactive shells on Windows hosts\n"
        "- Run post-exploitation scripts\n"
        "- Pivot through compromised systems\n\n"
        "Quick tips:\n"
        "- Requires admin credentials or hashes\n"
        "- Less stealthy than other exec methods (creates service)\n"
        "- Works even if PowerShell is disabled\n"
        "- Can use pass-the-hash with -hashes\n"
    ),
    "usage": 'souleyez jobs enqueue impacket-psexec <target> --args "DOMAIN/user:pass@host"',
    "examples": [
        'souleyez jobs enqueue impacket-psexec 10.0.0.82 --args "Administrator:Password123@10.0.0.82"',
        'souleyez jobs enqueue impacket-psexec 10.0.0.82 --args "CONTOSO/Administrator@10.0.0.82 -hashes :8846f7eaee8fb117ad06bdd830b7586c"',
        'souleyez jobs enqueue impacket-psexec 10.0.0.82 --args "Administrator:Password123@10.0.0.82 whoami"',
    ],
    "flags": [
        ["-hashes <LM:NT>", "Pass-the-hash authentication"],
        ["-no-pass", "Don't ask for password"],
        ["-k", "Use Kerberos authentication"],
        ["-aesKey <key>", "AES key for Kerberos"],
        ["<command>", "Command to execute (optional, default: interactive shell)"],
    ],
    "preset_categories": {
        "execution": [
            {
                "name": "Interactive Shell",
                "args": [],
                "desc": "Get interactive SYSTEM shell (default behavior)",
            },
            {
                "name": "Execute Single Command",
                "args": ["whoami"],
                "desc": "Execute single command and exit (replace 'whoami' with your command)",
            },
            {
                "name": "Execute and Save Output",
                "args": ["cmd.exe", "/c", "dir C:\\ > C:\\output.txt"],
                "desc": "Run command and save output to file",
            },
        ],
        "authentication": [
            {
                "name": "Pass-the-Hash (NTLM)",
                "args": ["-hashes", ":<ntlm_hash>"],
                "desc": "Authenticate with NTLM hash instead of password",
            },
            {
                "name": "Pass-the-Hash + Execute Command",
                "args": ["-hashes", ":<ntlm_hash>", "whoami"],
                "desc": "Use hash authentication and run command",
            },
            {
                "name": "Kerberos Authentication",
                "args": ["-k", "-no-pass"],
                "desc": "Use Kerberos ticket for authentication",
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
        "title": "What is psexec?",
        "color": "cyan",
        "content": [
            {
                "title": "Overview",
                "desc": "psexec provides remote command execution on Windows systems using SMB and named pipes, similar to Sysinternals PsExec, executing commands with SYSTEM privileges.",
            },
            {
                "title": "Use Cases",
                "desc": "Remote command execution and lateral movement",
                "tips": [
                    "Execute commands with SYSTEM privileges",
                    "Get interactive shells on Windows hosts",
                    "Run post-exploitation scripts remotely",
                    "Pivot through compromised systems",
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
                "desc": "1. Obtain admin credentials or hashes\n     2. Connect to target with psexec\n     3. Execute commands or get interactive shell\n     4. Run post-exploitation tasks",
            },
            {
                "title": "Key Options",
                "desc": "Essential psexec parameters",
                "tips": [
                    "Basic: psexec user:pass@host",
                    "Pass-the-hash: psexec -hashes :ntlm_hash user@host",
                    "Execute command: psexec user:pass@host whoami",
                    "Interactive shell: psexec user:pass@host (default)",
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
                    "Requires admin credentials or hashes",
                    "Less stealthy (creates service on target)",
                    "Works even if PowerShell is disabled",
                    "Can use pass-the-hash with -hashes",
                    "SYSTEM-level access by default",
                ],
            ),
            (
                "Common Issues:",
                [
                    "Access denied: Verify admin credentials",
                    "Service creation failed: Check admin rights",
                    "Connection timeout: Verify SMB (445) is open",
                    "Antivirus blocks: Use alternative exec methods (wmiexec, smbexec)",
                ],
            ),
        ],
    },
]


class ImpacketPsexecPlugin(PluginBase):
    name = "Impacket psexec"
    tool = "impacket-psexec"
    category = "lateral_movement"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution with PID tracking."""
        args = args or []

        # Replace <target> placeholder
        args = [arg.replace("<target>", target) for arg in args]

        # Find the correct command (varies by install: apt vs pipx)
        psexec_cmd = find_impacket_command("psexec")
        if not psexec_cmd:
            return None  # Tool not installed

        # Build command (args should include credentials)
        cmd = [psexec_cmd] + args

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute impacket-psexec and write output to log_path."""

        args = args or []

        # Replace <target> placeholder
        args = [arg.replace("<target>", target) for arg in args]

        # Find the correct command (varies by install: apt vs pipx)
        psexec_cmd = find_impacket_command("psexec")
        if not psexec_cmd:
            if log_path:
                with open(log_path, "w", encoding="utf-8") as fh:
                    fh.write("ERROR: psexec not found. Install with:\n")
                    fh.write("  Kali: sudo apt install python3-impacket\n")
                    fh.write("  Ubuntu: pipx install impacket\n")
            return 1

        # Build command
        cmd = [psexec_cmd]

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
                fh.write(f"=== Plugin: Impacket psexec ===\n")
                fh.write(f"Target: {target}\n")
                fh.write(f"Args: {args}\n")
                fh.write(f"Label: {label}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Command: {' '.join(cmd)}\n\n")

            # Run psexec (non-interactive)
            # Note: For interactive shells, this would need special handling
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
                fh.write("\n\nERROR: psexec timed out after 60 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write("ERROR: impacket-psexec not found in PATH\n")
                fh.write("Install: apt install python3-impacket\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\n\nERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = ImpacketPsexecPlugin()
