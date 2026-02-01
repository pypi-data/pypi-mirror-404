#!/usr/bin/env python3
"""
Impacket GetUserSPNs handler.

Handles parsing and display for Kerberoasting results.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_ERROR, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class ImpacketGetUserSPNsHandler(BaseToolHandler):
    """Handler for Impacket GetUserSPNs Kerberoasting jobs."""

    tool_name = "impacket-GetUserSPNs"
    display_name = "GetUserSPNs (Kerberoast)"

    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    def parse_job(
        self,
        engagement_id: int,
        log_path: str,
        job: Dict[str, Any],
        host_manager: Optional[Any] = None,
        findings_manager: Optional[Any] = None,
        credentials_manager: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Parse GetUserSPNs Kerberoasting results."""
        try:
            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()
            if findings_manager is None:
                from souleyez.storage.findings import FindingsManager

                findings_manager = FindingsManager()
            if credentials_manager is None:
                from souleyez.storage.credentials import CredentialsManager

                credentials_manager = CredentialsManager()

            target = job.get("target", "")

            # Read log file
            if not log_path or not os.path.exists(log_path):
                return {
                    "tool": "impacket-GetUserSPNs",
                    "status": STATUS_ERROR,
                    "error": "Log file not found",
                }

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                output = f.read()

            # Parse for SPNs and hashes
            spns = []
            kerberos_hashes = []

            # Extract SPN entries (table format)
            # ServicePrincipalName  Name           MemberOf  PasswordLastSet  LastLogon  Delegation
            spn_pattern = r"^([^\s]+)\s+([^\s]+)\s+([^\s]*)\s+(\d{4}-\d{2}-\d{2}[^\s]*)\s+(\d{4}-\d{2}-\d{2}[^\s]*)"
            for line in output.split("\n"):
                # Skip header lines
                if "ServicePrincipalName" in line or "----" in line:
                    continue
                match = re.match(spn_pattern, line.strip())
                if match:
                    spns.append(
                        {
                            "spn": match.group(1),
                            "name": match.group(2),
                            "member_of": match.group(3) if match.group(3) else None,
                            "password_last_set": match.group(4),
                            "last_logon": match.group(5),
                        }
                    )

            # Extract Kerberos TGS hashes ($krb5tgs$...)
            hash_pattern = r"(\$krb5tgs\$\d+\$\*[^\s]+)"
            for match in re.finditer(hash_pattern, output):
                kerberos_hashes.append(match.group(1))

            # Get or create host
            host_id = None
            ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", target)
            if ip_match:
                host_ip = ip_match.group(1)
                host = host_manager.get_host_by_ip(engagement_id, host_ip)
                if host:
                    host_id = host["id"]
                else:
                    host_id = host_manager.add_or_update_host(
                        engagement_id, {"ip": host_ip, "status": "up"}
                    )

            # Store hashes as credentials
            hashes_stored = 0
            for hash_val in kerberos_hashes:
                # Extract username from hash ($krb5tgs$23$*USERNAME$REALM$...)
                user_match = re.search(
                    r"\$krb5tgs\$\d+\$\*([^$\*]+)\$([^$\*]+)", hash_val
                )
                if user_match and host_id:
                    username = user_match.group(1)
                    domain = user_match.group(2)
                    try:
                        credentials_manager.add_credential(
                            engagement_id=engagement_id,
                            host_id=host_id,
                            username=username,
                            password=hash_val,
                            credential_type="kerberos_tgs",
                            source="kerberoast",
                            tool="impacket-GetUserSPNs",
                            notes=f"Kerberos TGS hash for {username}@{domain} - crack with hashcat -m 13100",
                        )
                        hashes_stored += 1
                    except Exception as e:
                        logger.warning(f"Could not store Kerberos hash: {e}")

            # Create finding if SPNs found
            if spns and host_id:
                spn_list = ", ".join([s["name"] for s in spns])
                findings_manager.add_finding(
                    engagement_id=engagement_id,
                    host_id=host_id,
                    finding_type="kerberoastable_accounts",
                    severity="high",
                    title="Kerberoastable Service Accounts Found",
                    description=(
                        f"Found {len(spns)} account(s) with Service Principal Names (SPNs) that can be "
                        f"Kerberoasted: {spn_list}. TGS tickets have been requested and can be cracked "
                        f"offline to recover plaintext passwords."
                    ),
                    evidence=f"Accounts: {spn_list}\nHashes extracted: {len(kerberos_hashes)}",
                    tool="impacket-GetUserSPNs",
                )

            # Determine status
            if kerberos_hashes:
                status = STATUS_DONE
            elif spns:
                status = STATUS_DONE
            elif "error" in output.lower() or "exception" in output.lower():
                status = STATUS_ERROR
            else:
                status = STATUS_NO_RESULTS

            return {
                "tool": "impacket-GetUserSPNs",
                "status": status,
                "target": target,
                "spns_found": len(spns),
                "spns": spns,
                "hashes_found": len(kerberos_hashes),
                "hashes": kerberos_hashes,
                "hashes_stored": hashes_stored,
            }

        except Exception as e:
            logger.error(f"Error parsing GetUserSPNs job: {e}")
            return {
                "tool": "impacket-GetUserSPNs",
                "status": STATUS_ERROR,
                "error": str(e),
            }

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful Kerberoasting results."""
        click.echo()
        click.echo(click.style("=" * 70, fg="green"))
        click.echo(click.style("KERBEROASTING SUCCESSFUL!", fg="green", bold=True))
        click.echo(click.style("=" * 70, fg="green"))
        click.echo()

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                output = f.read()

            # Count SPNs and hashes
            spn_count = 0
            hash_count = 0
            accounts = []

            # Parse SPN table
            in_table = False
            for line in output.split("\n"):
                if "ServicePrincipalName" in line:
                    in_table = True
                    continue
                if in_table and "----" in line:
                    continue
                if in_table and line.strip():
                    parts = line.split()
                    if len(parts) >= 2 and "/" in parts[0]:
                        spn_count += 1
                        accounts.append(parts[1])  # Account name
                    elif not parts[0].startswith("$"):
                        in_table = False

            # Count hashes
            hash_count = len(re.findall(r"\$krb5tgs\$", output))

            if accounts:
                click.echo(
                    click.style(
                        f"  Kerberoastable Accounts: {len(accounts)}", bold=True
                    )
                )
                for acc in accounts:
                    click.echo(f"    - {click.style(acc, fg='cyan', bold=True)}")
                click.echo()

            if hash_count:
                click.echo(
                    click.style(
                        f"  TGS Hashes Captured: {hash_count}", fg="yellow", bold=True
                    )
                )
                click.echo()
                click.echo(click.style("  Crack with:", bold=True))
                click.echo("    hashcat -m 13100 hashes.txt /path/to/wordlist")
                click.echo()

            click.echo(click.style("  Next Steps:", bold=True))
            click.echo("    - Crack hashes offline with hashcat/john")
            click.echo("    - Use cracked passwords for lateral movement")
            click.echo("    - Check if accounts have admin privileges")

        except Exception as e:
            click.echo(f"  Error reading results: {e}")

        click.echo()
        click.echo(click.style("=" * 70, fg="green"))
        click.echo()

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display warning - but check if we actually got results."""
        # First check if we actually got hashes (success case)
        if log_content is None and log_path:
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        if log_content and "$krb5tgs$" in log_content:
            # We got hashes! Display as success
            self.display_done(job, log_path)
            return

        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("KERBEROASTING - WARNING", fg="yellow", bold=True))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Scan completed with warnings.")
        if log_content:
            if "KDC_ERR" in log_content:
                click.echo("  Kerberos error - credentials may be invalid")
            elif "CCache file is not found" in log_content:
                click.echo("  No cached credentials (this is normal)")
        click.echo()
        click.echo("  Press [r] to view raw logs for details.")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display Kerberoasting error."""
        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("KERBEROASTING FAILED", fg="red", bold=True))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                output = f.read()

            if "KDC_ERR_PREAUTH_FAILED" in output:
                click.echo("  Authentication failed - invalid credentials")
            elif "KDC_ERR_C_PRINCIPAL_UNKNOWN" in output:
                click.echo("  User not found in domain")
            elif "Connection refused" in output:
                click.echo("  Could not connect to domain controller")
            else:
                click.echo("  Kerberoasting failed - check raw logs for details")

        except Exception:
            click.echo("  Could not read error details")

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display no Kerberoastable accounts found."""
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("NO KERBEROASTABLE ACCOUNTS", fg="yellow", bold=True))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  No accounts with SPNs found in this domain.")
        click.echo("  This means there are no service accounts to Kerberoast.")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
