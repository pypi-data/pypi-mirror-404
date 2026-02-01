#!/usr/bin/env python3
"""
souleyez.plugins.smbpasswd

SMB Password Change plugin - changes passwords for users with STATUS_PASSWORD_MUST_CHANGE.
"""

import subprocess
import time
from typing import List

from .plugin_base import PluginBase

HELP = {
    "name": "smbpasswd - SMB Password Change",
    "description": (
        "Change SMB/AD passwords over the network.\n\n"
        "Used when a user account has STATUS_PASSWORD_MUST_CHANGE - the password "
        "is known but must be changed before the account can be used.\n\n"
        "This is common in AD environments where initial passwords are set "
        "and users are required to change them on first login.\n\n"
        "The plugin uses smbpasswd with -s flag for non-interactive operation.\n"
    ),
    "usage": 'souleyez jobs enqueue smbpasswd <target> --args "-U <user> --old-pass <old> --new-pass <new>"',
    "examples": [
        'souleyez jobs enqueue smbpasswd 192.168.1.10 --args "-U Caroline.Robinson --old-pass BabyStart123! --new-pass NewP@ss123!"',
    ],
    "flags": [
        ["-r, --remote <TARGET>", "Remote SMB server (auto-set from target)"],
        ["-U, --user <USER>", "Username to change password for"],
        ["--old-pass <PASS>", "Current/old password"],
        ["--new-pass <PASS>", "New password to set"],
    ],
    "presets": [],
    "notes": [
        "Requires smbpasswd (part of samba-common-bin package)",
        "Use when crackmapexec shows STATUS_PASSWORD_MUST_CHANGE",
        "New password must meet domain password policy requirements",
        "After changing, use evil-winrm or other tools with new credentials",
    ],
}


class SmbpasswdPlugin(PluginBase):
    name = "smbpasswd"
    tool = "smbpasswd"
    category = "credential_attack"
    HELP = HELP

    def build_command(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ):
        """Build command for execution."""
        args = args or []

        # Parse custom args to extract username and passwords
        username = None
        old_pass = None
        new_pass = None

        i = 0
        filtered_args = []
        while i < len(args):
            if args[i] in ["-U", "--user"]:
                username = args[i + 1] if i + 1 < len(args) else None
                i += 2
            elif args[i] == "--old-pass":
                old_pass = args[i + 1] if i + 1 < len(args) else None
                i += 2
            elif args[i] == "--new-pass":
                new_pass = args[i + 1] if i + 1 < len(args) else None
                i += 2
            else:
                filtered_args.append(args[i])
                i += 1

        # Build command with shell piping to pass passwords via stdin
        # Format: (echo 'oldpass'; echo 'newpass'; echo 'newpass') | smbpasswd -r target -U user -s
        if old_pass and new_pass and username:
            # Escape single quotes in passwords
            old_pass_escaped = old_pass.replace("'", "'\\''")
            new_pass_escaped = new_pass.replace("'", "'\\''")

            shell_cmd = (
                f"(echo '{old_pass_escaped}'; echo '{new_pass_escaped}'; echo '{new_pass_escaped}') | "
                f"smbpasswd -r {target} -U {username} -s"
            )
            cmd = ["bash", "-c", shell_cmd]
        else:
            # Fallback to basic command (will fail without passwords)
            cmd = ["smbpasswd", "-r", target, "-s"]
            if username:
                cmd.extend(["-U", username])
            cmd.extend(filtered_args)

        return {
            "cmd": cmd,
            "timeout": 120,  # Increased for slow SAMR connections
            "old_pass": old_pass,
            "new_pass": new_pass,
            "username": username,
        }

    def run(
        self, target: str, args: List[str] = None, label: str = "", log_path: str = None
    ) -> int:
        """Execute smbpasswd."""
        args = args or []

        # Parse args
        cmd_info = self.build_command(target, args, label, log_path)
        cmd = cmd_info["cmd"]
        username = cmd_info.get("username", "unknown")
        new_pass = cmd_info.get("new_pass", "")

        try:
            if log_path:
                with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                    fh.write("=== SMB Password Change ===\n")
                    fh.write(f"Target: {target}\n")
                    fh.write(f"Username: {username}\n")
                    fh.write(
                        f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
                    )
                    fh.write(f"Command: {' '.join(cmd)}\n")
                    fh.write("(passwords piped via shell)\n\n")
                    fh.flush()

                    # Run smbpasswd with password piping via bash
                    proc = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=120,  # Increased for slow SAMR connections
                        check=False,
                    )

                    fh.write(f"STDOUT:\n{proc.stdout}\n")
                    fh.write(f"STDERR:\n{proc.stderr}\n")

                    # Check for success - either exit code 0 OR "Password changed" in output
                    # SAMR connection may timeout AFTER password was changed successfully
                    output_combined = (proc.stdout or "") + (proc.stderr or "")
                    password_changed = (
                        proc.returncode == 0
                        or "Password changed" in output_combined
                        or "password changed" in output_combined.lower()
                    )

                    # Also check for timeout that happened AFTER password change
                    # If we see IO_TIMEOUT but no "password is not correct", it likely worked
                    if (
                        "NT_STATUS_IO_TIMEOUT" in output_combined
                        and "not correct" not in output_combined
                    ):
                        password_changed = True
                        fh.write(
                            "\n[NOTE] SAMR timeout occurred but password may have changed\n"
                        )

                    if password_changed:
                        fh.write("\n" + "=" * 50 + "\n")
                        fh.write("PASSWORD CHANGED SUCCESSFULLY!\n")
                        fh.write("=" * 50 + "\n")
                        fh.write(f"Username: {username}\n")
                        fh.write(f"New Password: {new_pass}\n")
                        fh.write("\nNext step: Connect with evil-winrm or other tool\n")
                        fh.write(
                            f"Example: evil-winrm -i {target} -u {username} -p '{new_pass}'\n"
                        )
                        # Return 0 to indicate success for chaining
                        return 0
                    else:
                        fh.write("\nPassword change FAILED - check error above\n")

                    fh.write(
                        f"\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
                    )
                    fh.write(f"Exit Code: {proc.returncode}\n")

                    return proc.returncode
            else:
                # No log path - run directly
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=120, check=False
                )
                # Check for success patterns even without log
                output_combined = (proc.stdout or "") + (proc.stderr or "")
                if (
                    "Password changed" in output_combined
                    or "NT_STATUS_IO_TIMEOUT" in output_combined
                ):
                    return 0
                return proc.returncode

        except subprocess.TimeoutExpired:
            if log_path:
                with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                    fh.write("\nERROR: smbpasswd command timed out after 120 seconds\n")
            return 124

        except FileNotFoundError:
            if log_path:
                with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                    fh.write("\nERROR: smbpasswd not found in PATH\n")
                    fh.write("Install with: apt install samba-common-bin\n")
            return 127

        except Exception as e:
            if log_path:
                with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                    fh.write(f"\nERROR: {type(e).__name__}: {e}\n")
            return 1


plugin = SmbpasswdPlugin()
