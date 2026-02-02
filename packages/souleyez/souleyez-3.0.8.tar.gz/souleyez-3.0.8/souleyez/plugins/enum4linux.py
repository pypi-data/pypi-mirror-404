#!/usr/bin/env python3
"""
souleyez.plugins.enum4linux

Enum4linux SMB enumeration plugin with unified interface.
"""

import subprocess
import time
from typing import List

from souleyez.security.validation import ValidationError, validate_target

from .plugin_base import PluginBase

HELP = {
    "name": "enum4linux (SMB Enumeration)",
    "description": (
        "Want comprehensive SMB enumeration for legacy Samba systems?\n\n"
        "Enum4linux is a focused SMB/CIFS enumeration tool for Windows and Samba systems. It automates common recon tasks "
        "like listing shares, enumerating users and groups, pulling OS and domain info, and checking for null/anonymous access. "
        "Think of it as the first-pass investigator that maps file shares, permissions, and exposed services so you know where "
        "to look next — without exploiting anything.\n\n"
        "Results are collected so you can add the interesting bits to your job log, convert them into Findings, or fold them "
        "into reports and dashboards. Play nice: some techniques (user enumeration, RID cycling, etc.) can be noisy and may "
        "trigger alerts — always run with authorization and follow your rules of engagement. 😇\n\n"
        "Quick tips:\n"
        "- Best used for SMB reconnaissance: shares, users/groups, OS and domain metadata, and anonymous access checks.\n"
        "- Ideal for spotting anonymous or misconfigured shares and weak permissions.\n"
        "- Capture output to the job log so nothing gets lost during triage and reporting.\n"
        "- Be cautious with noisy probes (userenum / RID cycling); run them only with explicit permission.\n"
        "- Correlate Enum4linux output with other SMB checks (smbclient, smbmap, bloodhound, etc.) for a fuller risk picture.\n"
    ),
    "usage": 'souleyez jobs enqueue enum4linux <target> --args "-a"',
    "examples": [
        'souleyez jobs enqueue enum4linux 10.0.0.5 --args "-a"',
        'souleyez jobs enqueue enum4linux 10.0.0.5 --args "-U -S"',
    ],
    "flags": [
        ["-U", "Get userlist"],
        ["-S", "Get sharelist"],
        ["-G", "Get group/member list"],
        ["-P", "Get password policy"],
        ["-a", "All simple enumeration"],
    ],
    "presets": [
        {
            "name": "Full Enum",
            "args": ["-a"],
            "desc": "All enumeration (users, shares, groups, etc.)",
        },
        {"name": "Shares Only", "args": ["-S"], "desc": "Enumerate shares only"},
        {
            "name": "Users & Shares",
            "args": ["-U", "-S"],
            "desc": "Enumerate users and shares",
        },
    ],
    "help_sections": [
        {
            "title": "What is enum4linux?",
            "color": "cyan",
            "content": [
                {
                    "title": "Overview",
                    "desc": "enum4linux is a comprehensive SMB/CIFS enumeration tool for Windows and Samba systems, automating common reconnaissance tasks.",
                },
                {
                    "title": "Use Cases",
                    "desc": "Best for legacy Samba and Windows SMB enumeration",
                    "tips": [
                        "List shares and permissions",
                        "Enumerate users and groups via RID cycling",
                        "Pull OS and domain information",
                        "Check for null/anonymous access",
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
                    "desc": "1. Run full enumeration (-a) for complete picture\n     2. Review shares for anonymous access\n     3. Check user/group lists for attack targets\n     4. Document findings in job log",
                },
                {
                    "title": "Key Options",
                    "desc": "Common enumeration tasks",
                    "tips": [
                        "-a: All enumeration (recommended start)",
                        "-U: User enumeration",
                        "-S: Share enumeration",
                        "-G: Group and member enumeration",
                        "-P: Password policy information",
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
                        "Start with -a for comprehensive baseline",
                        "Flag anonymous shares as security findings",
                        "Correlate with smbmap and CrackMapExec results",
                        "Save output for later analysis and reporting",
                        "Document weak permissions and exposed data",
                    ],
                ),
                (
                    "Common Issues:",
                    [
                        "RID cycling fails: Try with credentials or different host",
                        "Timeout errors: Some checks can be slow on large domains",
                        "Access denied: Check if guest/anonymous access is disabled",
                        "No users found: Requires SMB enumeration to be enabled",
                    ],
                ),
            ],
        },
    ],
}


class Enum4linuxPlugin(PluginBase):
    name = "enum4linux (SMB)"
    tool = "enum4linux"
    alt_tools = ["enum4linux-ng"]  # Ubuntu uses enum4linux-ng
    category = "scanning"
    HELP = HELP

    def _get_tool_command(self) -> str:
        """Get the actual tool command available on the system."""
        import shutil

        # Check primary command first
        if shutil.which(self.tool):
            return self.tool
        # Check alternative commands (e.g., enum4linux-ng on Ubuntu)
        for alt in getattr(self, "alt_tools", []):
            if shutil.which(alt):
                return alt
        return self.tool  # Return default, will fail with clear error

    def _translate_args_for_ng(self, args: List[str], tool_cmd: str) -> List[str]:
        """Translate enum4linux args to enum4linux-ng format if needed.

        enum4linux-ng uses different flags than the original:
        - -a (all) becomes -A
        - Most other flags (-U, -S, -G, -P) are the same
        """
        if "enum4linux-ng" not in tool_cmd:
            return args

        # Argument mapping: enum4linux -> enum4linux-ng
        arg_map = {
            "-a": "-A",  # All enumeration
        }

        translated = []
        for arg in args:
            translated.append(arg_map.get(arg, arg))
        return translated

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for background execution with PID tracking."""
        args = args or []

        # Get the actual tool command (enum4linux or enum4linux-ng)
        tool_cmd = self._get_tool_command()

        # Check if tool exists
        import shutil

        if not shutil.which(tool_cmd):
            if log_path:
                with open(log_path, "w") as f:
                    f.write(
                        f"ERROR: Neither enum4linux nor enum4linux-ng found in PATH\n"
                    )
                    f.write("Install with:\n")
                    f.write("  Kali/Parrot: sudo apt install enum4linux\n")
                    f.write(
                        "  Ubuntu: pipx install git+https://github.com/cddmp/enum4linux-ng\n"
                    )
            return None

        # Validate target
        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
            return None

        # Translate arguments if using enum4linux-ng
        args = self._translate_args_for_ng(args, tool_cmd)

        # Build command using detected tool
        cmd = [tool_cmd] + args

        # Only add target if not already in args
        if target not in args:
            cmd.append(target)

        return {"cmd": cmd, "timeout": 1800}  # 30 minutes

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """
        Execute enum4linux scan and write output to log_path.

        Args:
            target: Target IP address or hostname
            args: Enum4linux arguments (e.g. ["-a"])
            label: Optional label for this scan
            log_path: Path to write output (required for background jobs)

        Returns:
            int: Exit code (0=success, non-zero=error)
        """
        # Validate target
        try:
            target = validate_target(target)
        except ValidationError as e:
            if log_path:
                with open(log_path, "w") as f:
                    f.write(f"ERROR: Invalid target: {e}\n")
                return 1
            raise ValueError(f"Invalid target: {e}")

        args = args or []

        # Replace <target> placeholder if present
        args = [arg.replace("<target>", target) for arg in args]

        # Get the actual tool command (enum4linux or enum4linux-ng)
        tool_cmd = self._get_tool_command()

        # Translate arguments if using enum4linux-ng
        args = self._translate_args_for_ng(args, tool_cmd)

        # Build command using detected tool
        cmd = [tool_cmd] + args
        if target not in args:
            cmd.append(target)

        if not log_path:
            # Fallback for direct calls
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, timeout=300, check=False
                )
                return proc.returncode
            except Exception:
                return 1

        # Run with logging
        try:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"Command: {' '.join(cmd)}\n")
                fh.write(
                    f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
                )
                fh.flush()

                proc = subprocess.run(
                    cmd, stdout=fh, stderr=subprocess.STDOUT, timeout=300, check=False
                )

                fh.write(
                    f"\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                )
                fh.write(f"Exit Code: {proc.returncode}\n")

                return proc.returncode

        except subprocess.TimeoutExpired:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: enum4linux timed out after 300 seconds\n")
            return 124

        except FileNotFoundError:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\nERROR: enum4linux not found in PATH\n")
            return 127

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\nERROR: {type(e).__name__}: {e}\n")
            return 1


# Export plugin instance
plugin = Enum4linuxPlugin()
