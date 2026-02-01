#!/usr/bin/env python3
"""
Impacket secretsdump handler.

Consolidates parsing and display logic for Impacket secretsdump credential extraction jobs.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class ImpacketSecretsdumpHandler(BaseToolHandler):
    """Handler for Impacket secretsdump credential extraction jobs."""

    tool_name = "impacket-secretsdump"  # Match the actual tool name with hyphen
    display_name = "Secretsdump"

    # All handlers enabled
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
        """
        Parse secretsdump job results.

        Extracts NTLM hashes, plaintext credentials, and Kerberos tickets.
        """
        try:
            from souleyez.parsers.impacket_parser import parse_secretsdump

            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()
            if credentials_manager is None:
                from souleyez.storage.credentials import CredentialsManager

                credentials_manager = CredentialsManager()

            target = job.get("target", "")
            parsed = parse_secretsdump(log_path, target)

            if "error" in parsed:
                return parsed

            # Get or create host
            host_id = None
            ip_match = re.search(r"@?(\d+\.\d+\.\d+\.\d+)", target)
            if ip_match:
                host_ip = ip_match.group(1)
                host_id = host_manager.add_or_update_host(
                    engagement_id, {"ip": host_ip, "status": "up"}
                )

            creds_added = 0
            hashes_added = 0

            # Store plaintext credentials
            for cred in parsed.get("credentials", []):
                try:
                    credentials_manager.add_credential(
                        engagement_id=engagement_id,
                        host_id=host_id,
                        username=cred.get("username"),
                        password=cred.get("password"),
                        service="windows",
                        status="valid",
                        credential_type="password",
                        tool="impacket_secretsdump",
                        domain=cred.get("domain"),
                    )
                    creds_added += 1
                except Exception:
                    pass

            # Store NTLM hashes
            for hash_data in parsed.get("hashes", []):
                try:
                    credentials_manager.add_credential(
                        engagement_id=engagement_id,
                        host_id=host_id,
                        username=hash_data.get("username"),
                        password=hash_data.get("nt_hash"),
                        service="windows",
                        status="valid",
                        credential_type="hash",
                        tool="impacket_secretsdump",
                        notes=f"RID: {hash_data.get('rid')}, LM: {hash_data.get('lm_hash')}",
                    )
                    hashes_added += 1
                except Exception:
                    pass

            return {
                "tool": "impacket_secretsdump",
                "status": (
                    STATUS_DONE
                    if (creds_added > 0 or hashes_added > 0)
                    else STATUS_NO_RESULTS
                ),
                "target": target,
                "credentials_added": creds_added,
                "hashes_added": hashes_added,
                "hashes_count": parsed.get("hashes_count", 0),
                "credentials_count": parsed.get("credentials_count", 0),
                "tickets_count": parsed.get("tickets_count", 0),
                "hashes": parsed.get("hashes", []),  # For chaining to hashcat
            }

        except Exception as e:
            logger.error(f"Error parsing secretsdump job: {e}")
            return {"error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful secretsdump results."""
        try:
            from souleyez.parsers.impacket_parser import parse_secretsdump

            if not log_path or not os.path.exists(log_path):
                return

            target = job.get("target", "unknown")
            parsed = parse_secretsdump(log_path, target)

            hashes = parsed.get("hashes", [])
            credentials = parsed.get("credentials", [])
            tickets = parsed.get("tickets", [])
            lsa_secrets = parsed.get("lsa_secrets", [])
            kerberos_keys = parsed.get("kerberos_keys", [])
            hashes_count = parsed.get("hashes_count", 0)
            creds_count = parsed.get("credentials_count", 0)
            tickets_count = parsed.get("tickets_count", 0)

            if not (hashes or credentials or tickets or lsa_secrets or kerberos_keys):
                self.display_no_results(job, log_path)
                return

            click.echo(click.style("=" * 70, fg="green"))
            click.echo(
                click.style("SECRETSDUMP - DOMAIN COMPROMISE!", bold=True, fg="green")
            )
            click.echo(click.style("=" * 70, fg="green"))
            click.echo()

            # Show summary
            click.echo(click.style("Summary:", bold=True))
            click.echo(f"  NTLM Hashes:      {hashes_count}")
            click.echo(f"  LSA Secrets:      {len(lsa_secrets)}")
            click.echo(f"  Kerberos Keys:    {len(kerberos_keys)}")
            click.echo(f"  Plaintext Creds:  {creds_count}")
            click.echo()

            # Highlight critical accounts
            critical_accounts = ["administrator", "krbtgt", "domain admins"]
            critical_found = [
                h
                for h in hashes
                if any(c in h.get("username", "").lower() for c in critical_accounts)
            ]
            if critical_found:
                click.echo(click.style("CRITICAL ACCOUNTS:", bold=True, fg="red"))
                for h in critical_found:
                    username = h.get("username", "?")
                    nt_hash = (
                        h.get("nt_hash", "?")
                        if show_passwords
                        else h.get("nt_hash", "?")[:16] + "..."
                    )
                    click.echo(
                        click.style(f"  {username}: {nt_hash}", fg="red", bold=True)
                    )
                click.echo()

            # Show LSA secrets (DefaultPassword, etc.)
            if lsa_secrets:
                click.echo(click.style("LSA Secrets:", bold=True, fg="magenta"))
                for secret in lsa_secrets:
                    secret_type = secret.get("secret_type", "Unknown")
                    value = secret.get("value", "***") if show_passwords else "***"
                    click.echo(click.style(f"  {secret_type}: {value}", fg="magenta"))
                click.echo()

            # Show hashes (limited)
            if hashes:
                click.echo(
                    click.style(f"NTLM Hashes ({len(hashes)}):", bold=True, fg="yellow")
                )
                max_show = None if show_all else 5
                display_hashes = hashes if max_show is None else hashes[:max_show]
                for h in display_hashes:
                    username = h.get("username", "?")
                    if show_passwords:
                        nt_hash = h.get("nt_hash", "?")
                    else:
                        nt_hash = (
                            h.get("nt_hash", "?")[:16] + "..."
                            if h.get("nt_hash")
                            else "?"
                        )
                    click.echo(f"  {username}: {nt_hash}")
                if max_show and len(hashes) > max_show:
                    click.echo(
                        click.style(
                            f"  ... and {len(hashes) - max_show} more hashes", dim=True
                        )
                    )
                click.echo()

            # Show plaintext credentials
            if credentials:
                click.echo(
                    click.style(
                        f"Plaintext Credentials ({len(credentials)}):",
                        bold=True,
                        fg="green",
                    )
                )
                max_show = None if show_all else 5
                display_creds = (
                    credentials if max_show is None else credentials[:max_show]
                )
                for c in display_creds:
                    domain = c.get("domain", "")
                    username = c.get("username", "?")
                    password = c.get("password", "?") if show_passwords else "***"
                    if domain:
                        click.echo(
                            click.style(
                                f"  {domain}\\{username}:{password}", fg="green"
                            )
                        )
                    else:
                        click.echo(click.style(f"  {username}:{password}", fg="green"))
                if max_show and len(credentials) > max_show:
                    click.echo(
                        click.style(
                            f"  ... and {len(credentials) - max_show} more", dim=True
                        )
                    )
                click.echo()

            # Show Kerberos keys (for golden ticket potential)
            if kerberos_keys:
                krbtgt_keys = [
                    k
                    for k in kerberos_keys
                    if "krbtgt" in k.get("username", "").lower()
                ]
                if krbtgt_keys:
                    click.echo(
                        click.style(
                            "GOLDEN TICKET MATERIAL (krbtgt keys):", bold=True, fg="red"
                        )
                    )
                    for k in krbtgt_keys:
                        key_type = k.get("key_type", "?")
                        click.echo(click.style(f"  {key_type}: [AVAILABLE]", fg="red"))
                    click.echo()

            # Show Kerberos tickets
            if tickets:
                click.echo(
                    click.style(
                        f"Kerberos Tickets ({len(tickets)}):", bold=True, fg="cyan"
                    )
                )
                max_show = None if show_all else 3
                display_tickets = tickets if max_show is None else tickets[:max_show]
                for t in display_tickets:
                    username = t.get("username", "?")
                    ticket_type = t.get("ticket_type", "Kerberos")
                    click.echo(f"  {username}: {ticket_type}")
                if max_show and len(tickets) > max_show:
                    click.echo(
                        click.style(
                            f"  ... and {len(tickets) - max_show} more tickets",
                            dim=True,
                        )
                    )
                click.echo()

            # Next steps
            click.echo(click.style("Next Steps:", bold=True))
            click.echo("  - Use hashes for Pass-the-Hash attacks")
            click.echo("  - Crack hashes with hashcat -m 1000")
            if any("krbtgt" in h.get("username", "").lower() for h in hashes):
                click.echo(
                    click.style("  - Create Golden Tickets with krbtgt hash!", fg="red")
                )
            click.echo()

            click.echo(click.style("=" * 70, fg="green"))
            click.echo()

        except Exception as e:
            logger.debug(f"Error in display_done: {e}")

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display warning status for secretsdump - but show results if we got them."""
        # Check if we actually got results (should be treated as success)
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        # If we have NTLM hashes, treat as success
        if log_content and (
            ":::" in log_content or "Dumping Domain Credentials" in log_content
        ):
            self.display_done(job, log_path)
            return

        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] SECRETSDUMP", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Credential dump completed with warnings.")
        click.echo("  Check raw logs for details (press 'r').")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display error status for secretsdump."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] SECRETSDUMP FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common secretsdump errors
        error_msg = None
        if log_content:
            if "Connection refused" in log_content:
                error_msg = "Connection refused - target SMB service may be down"
            elif (
                "Access denied" in log_content.lower()
                or "STATUS_ACCESS_DENIED" in log_content
            ):
                error_msg = "Access denied - insufficient privileges to dump secrets"
            elif "STATUS_LOGON_FAILURE" in log_content:
                error_msg = "Logon failure - invalid credentials"
            elif "timed out" in log_content.lower() or "timeout" in log_content.lower():
                error_msg = "Connection timed out - target may be unreachable"
            elif "DRSUAPI method not supported" in log_content:
                error_msg = (
                    "DRSUAPI not supported - may need different method (-use-vss)"
                )
            elif "Cannot reach" in log_content:
                error_msg = "Cannot reach target - check network connectivity"

        if error_msg:
            click.echo(f"  {error_msg}")
        else:
            click.echo(
                "  Credential dump failed - check raw logs for details (press 'r')"
            )

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for secretsdump."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("SECRETSDUMP RESULTS", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  No credentials or hashes were extracted.")
        click.echo()
        click.echo(click.style("Possible reasons:", dim=True))
        click.echo("  - Target has no stored credentials")
        click.echo("  - Insufficient privileges (need admin/SYSTEM)")
        click.echo("  - SAM/NTDS database is protected or unavailable")
        click.echo("  - Try -use-vss flag for VSS shadow copy extraction")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
