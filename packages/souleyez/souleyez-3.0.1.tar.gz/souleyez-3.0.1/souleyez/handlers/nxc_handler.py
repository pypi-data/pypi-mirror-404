#!/usr/bin/env python3
"""
Handler for NetExec (nxc) - successor to CrackMapExec.
Parses shares, credentials, and authentication results.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)

STATUS_DONE = "done"
STATUS_ERROR = "error"
STATUS_WARNING = "warning"
STATUS_NO_RESULTS = "no_results"


class NxcHandler(BaseToolHandler):
    """Handler for NetExec SMB/WinRM/etc enumeration."""

    tool_name = "nxc"
    display_name = "NetExec"

    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    # Patterns for parsing
    SHARE_PATTERN = r"^\s*(\S+)\s+(READ|WRITE|READ,WRITE|NO ACCESS)\s*(.*)$"
    VALID_CRED_PATTERN = r"\[\+\]\s+(\S+)\\([^:]+):([^\s]+)"
    PWNED_PATTERN = r"\(Pwn3d!\)"

    def parse_job(
        self,
        engagement_id: int,
        log_path: str,
        job: Dict[str, Any],
        host_manager: Optional[Any] = None,
        findings_manager: Optional[Any] = None,
        credentials_manager: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Parse nxc results."""
        try:
            target = job.get("target", "")
            if not log_path or not os.path.exists(log_path):
                return {
                    "tool": "nxc",
                    "status": STATUS_ERROR,
                    "error": "Log file not found",
                }

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Strip ANSI codes
            log_content = re.sub(r"\x1b\[[0-9;]*m", "", log_content)

            shares = []
            readable_shares = []
            writable_shares = []
            credentials = []
            expired_credentials = []  # Credentials that need password change
            is_pwned = False
            domain = ""
            hostname = ""

            # Parse domain/hostname from banner
            # Format: SMB 10.129.234.72 445 DC [*] Windows Server 2022 (name:DC) (domain:baby2.vl)
            banner_match = re.search(
                r"\(name:([^)]+)\).*\(domain:([^)]+)\)", log_content
            )
            if banner_match:
                hostname = banner_match.group(1)
                domain = banner_match.group(2)

            # Check for Pwn3d (SMB admin access)
            if re.search(self.PWNED_PATTERN, log_content):
                is_pwned = True

            # Check for SSH Shell access (Linux)
            # Format: [+] leia_organa:help_me_obiwan  Linux - Shell access!
            has_shell_access = False
            if "Shell access!" in log_content:
                has_shell_access = True
                # Parse SSH credentials
                ssh_cred_pattern = r"\[\+\]\s+([^:\s]+):(\S+)\s+.*Shell access!"
                for match in re.finditer(ssh_cred_pattern, log_content):
                    username = match.group(1)
                    password = match.group(2)
                    cred = {
                        "username": username,
                        "password": password,
                        "domain": "",
                        "service": "ssh",
                        "status": "valid",
                    }
                    credentials.append(cred)

                    # Store in database
                    if credentials_manager and host_manager:
                        try:
                            host = host_manager.get_host_by_ip(engagement_id, target)
                            if host:
                                credentials_manager.add_credential(
                                    engagement_id=engagement_id,
                                    host_id=host["id"],
                                    username=username,
                                    password=password,
                                    service="ssh",
                                    port=22,
                                    credential_type="password",
                                    tool="nxc",
                                    status="valid",
                                )
                                logger.warning(
                                    f"SSH SHELL ACCESS: {username}:{password} on {target}"
                                )
                        except Exception as e:
                            logger.debug(f"Could not store SSH credential: {e}")

            # Parse valid credentials
            # Format: [+] baby2.vl\Carl.Moore:Carl.Moore
            for match in re.finditer(self.VALID_CRED_PATTERN, log_content):
                domain_part = match.group(1)
                username = match.group(2)
                password = match.group(3)

                cred = {
                    "username": username,
                    "password": password,
                    "domain": domain_part,
                    "service": "smb",
                    "status": "valid",
                }
                credentials.append(cred)

                # Store in database
                if credentials_manager and host_manager:
                    try:
                        host = host_manager.get_host_by_ip(engagement_id, target)
                        if host:
                            credentials_manager.add_credential(
                                engagement_id=engagement_id,
                                host_id=host["id"],
                                username=username,
                                password=password,
                                service="smb",
                                credential_type="password",
                                tool="nxc",
                                status="valid",
                            )
                            logger.warning(
                                f"CREDENTIAL FOUND: {domain_part}\\{username}:{password}"
                            )
                    except Exception as e:
                        logger.debug(f"Could not store credential: {e}")

            # Parse expired credentials (STATUS_PASSWORD_MUST_CHANGE)
            # Format: [-] baby.vl\Caroline.Robinson:BabyStart123! STATUS_PASSWORD_MUST_CHANGE
            expired_pattern = (
                r"\[-\]\s+(\S+)\\([^:]+):(\S+)\s+STATUS_PASSWORD_MUST_CHANGE"
            )
            for match in re.finditer(expired_pattern, log_content):
                domain_part = match.group(1)
                username = match.group(2)
                password = match.group(3)

                cred = {
                    "username": username,
                    "password": password,
                    "domain": domain_part,
                    "service": "smb",
                    "status": "expired",
                }
                expired_credentials.append(cred)

                # Store in database with expired status
                if credentials_manager and host_manager:
                    try:
                        host = host_manager.get_host_by_ip(engagement_id, target)
                        if host:
                            credentials_manager.add_credential(
                                engagement_id=engagement_id,
                                host_id=host["id"],
                                username=username,
                                password=password,
                                service="smb",
                                credential_type="password",
                                tool="nxc",
                                status="expired",
                            )
                            logger.warning(
                                f"EXPIRED CREDENTIAL FOUND: {domain_part}\\{username}:{password} - PASSWORD MUST CHANGE"
                            )
                    except Exception as e:
                        logger.debug(f"Could not store expired credential: {e}")

            # Parse shares
            # nxc format: SMB  IP  PORT  HOST  ShareName  Permissions  Remark
            # Example: SMB  10.129.234.72  445  DC  homes  READ,WRITE
            share_section = False
            for line in log_content.split("\n"):
                if "Enumerated shares" in line:
                    share_section = True
                    continue
                if share_section and line.strip():
                    # Skip header and separator lines
                    if "Share" in line and "Permissions" in line and "Remark" in line:
                        continue
                    if "-----" in line:
                        continue
                    # Stop at completion marker
                    if "=== Completed" in line or "Exit Code" in line:
                        break

                    # nxc output has: SMB  IP  PORT  HOST  ShareName  Permissions  Comment
                    # Parse by splitting on whitespace and extracting after the hostname
                    parts = line.split()
                    if len(parts) >= 5 and parts[0] == "SMB":
                        # Find the share name - it's after the hostname (4th column)
                        # Format: SMB IP PORT HOSTNAME SHARENAME [PERMISSIONS] [COMMENT...]
                        # Index:  0   1  2    3        4         5             6+
                        share_name = parts[4] if len(parts) > 4 else ""

                        # Skip metadata lines
                        if not share_name or share_name in [
                            "[*]",
                            "[+]",
                            "[-]",
                            "Share",
                        ]:
                            continue

                        # Permissions (if present) - look for READ, WRITE, READ,WRITE
                        perms = ""
                        comment = ""
                        if len(parts) > 5:
                            # Check if 5th element is a permission
                            if parts[5] in ["READ", "WRITE", "READ,WRITE"]:
                                perms = parts[5]
                                comment = " ".join(parts[6:]) if len(parts) > 6 else ""
                            else:
                                # No permissions, rest is comment
                                comment = " ".join(parts[5:])

                        share = {
                            "name": share_name,
                            "permissions": perms,
                            "comment": comment,
                        }
                        shares.append(share)

                        if "READ" in perms:
                            readable_shares.append(share)
                        if "WRITE" in perms:
                            writable_shares.append(share)

            # Determine status based on results found
            # Retry logic is handled by background.py before parsing
            if credentials:
                status = STATUS_DONE
            elif has_shell_access:
                status = STATUS_DONE  # SSH shell access without parsed creds
            elif expired_credentials:
                status = STATUS_WARNING  # Expired creds need attention
            elif shares:
                status = STATUS_DONE
            else:
                status = STATUS_NO_RESULTS

            # Build summary
            summary_parts = []
            if credentials:
                summary_parts.append(f"{len(credentials)} valid credential(s)")
            if expired_credentials:
                summary_parts.append(
                    f"{len(expired_credentials)} expired credential(s)"
                )
            if is_pwned:
                summary_parts.append("PWNED!")
            if has_shell_access:
                summary_parts.append("SHELL ACCESS!")
            if shares:
                summary_parts.append(
                    f"{len(shares)} shares ({len(readable_shares)} readable, {len(writable_shares)} writable)"
                )
            summary = " | ".join(summary_parts) if summary_parts else "No findings"

            result = {
                "tool": "nxc",
                "status": status,
                "target": target,
                "domain": domain,
                "hostname": hostname,
                "shares": shares,
                "readable_shares": readable_shares,
                "writable_shares": writable_shares,
                "credentials": credentials,
                "expired_credentials": expired_credentials,
                "is_pwned": is_pwned,
                "has_shell_access": has_shell_access,
                "summary": summary,
            }

            if credentials:
                logger.info(f"nxc: Found {len(credentials)} valid credential(s)")
            if expired_credentials:
                logger.warning(
                    f"nxc: Found {len(expired_credentials)} EXPIRED credential(s) - password change required!"
                )
            if shares:
                logger.info(
                    f"nxc: Found {len(shares)} share(s) ({len(readable_shares)} readable, {len(writable_shares)} writable)"
                )

            return result

        except Exception as e:
            logger.error(f"Error parsing nxc job: {e}")
            return {"tool": "nxc", "status": STATUS_ERROR, "error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful nxc results."""
        import click

        parse_result = job.get("parse_result", {})

        domain = parse_result.get("domain", "")
        hostname = parse_result.get("hostname", "")
        shares = parse_result.get("shares", [])
        credentials = parse_result.get("credentials", [])
        expired_credentials = parse_result.get("expired_credentials", [])
        is_pwned = parse_result.get("is_pwned", False)
        target = parse_result.get("target", "")

        if domain or hostname:
            click.echo(
                f"  Target: {hostname}.{domain}" if hostname else f"  Domain: {domain}"
            )

        if is_pwned:
            click.secho("  [!] Pwn3d! - Admin access achieved", fg="red", bold=True)

        if credentials:
            click.secho(
                f"\n  Valid Credentials ({len(credentials)}):", fg="green", bold=True
            )
            for cred in credentials:
                domain_part = cred.get("domain", "")
                username = cred.get("username", "")
                password = cred.get("password", "") if show_passwords else "********"
                click.echo(f"    {domain_part}\\{username}:{password}")

        if expired_credentials:
            click.secho(
                f"\n  Expired Credentials ({len(expired_credentials)}):",
                fg="yellow",
                bold=True,
            )
            click.secho("  [!] Password must be changed before use!", fg="yellow")
            for cred in expired_credentials:
                domain_part = cred.get("domain", "")
                username = cred.get("username", "")
                password = cred.get("password", "") if show_passwords else "********"
                click.echo(f"    {domain_part}\\{username}:{password}")
            click.secho(f"\n  To change password, run:", fg="cyan")
            for cred in expired_credentials:
                domain_part = cred.get("domain", "")
                username = cred.get("username", "")
                click.echo(
                    f"    smbpasswd -U {domain_part}/{username} -r {target or domain}"
                )

        if shares:
            click.secho(f"\n  Shares ({len(shares)}):", fg="cyan", bold=True)
            for share in shares:
                name = share.get("name", "")
                perms = share.get("permissions", "")
                comment = share.get("comment", "")

                # Color based on permissions
                if "WRITE" in perms:
                    click.secho(f"    {name:20} {perms:15} {comment}", fg="yellow")
                elif "READ" in perms:
                    click.secho(f"    {name:20} {perms:15} {comment}", fg="green")
                else:
                    click.echo(f"    {name:20} {perms:15} {comment}")


# Register handler
handler = NxcHandler()
