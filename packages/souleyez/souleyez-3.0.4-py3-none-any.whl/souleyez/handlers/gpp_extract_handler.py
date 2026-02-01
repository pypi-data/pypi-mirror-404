#!/usr/bin/env python3
"""
GPP Extract handler.

Handles parsing and credential storage for GPP (Group Policy Preferences) extraction jobs.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_ERROR, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class GppExtractHandler(BaseToolHandler):
    """Handler for GPP credential extraction jobs."""

    tool_name = "gpp_extract"
    display_name = "GPP Extract"

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
        """Parse GPP extraction results and store credentials."""
        try:
            from souleyez.storage.credentials import CredentialsManager
            from souleyez.storage.findings import FindingsManager
            from souleyez.storage.hosts import HostManager

            # Import managers if not provided
            if host_manager is None:
                host_manager = HostManager()
            if findings_manager is None:
                findings_manager = FindingsManager()
            if credentials_manager is None:
                credentials_manager = CredentialsManager()

            target = job.get("target", "")

            # Read log file
            if not log_path or not os.path.exists(log_path):
                return {
                    "tool": "gpp_extract",
                    "status": STATUS_ERROR,
                    "error": "Log file not found",
                }

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                output = f.read()

            # Get or create host
            host_id = None
            if target:
                is_ip = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", target)
                if is_ip:
                    host = host_manager.get_host_by_ip(engagement_id, target)
                    if host:
                        host_id = host["id"]
                    else:
                        host_id = host_manager.add_or_update_host(
                            engagement_id, {"ip": target, "status": "up"}
                        )

            # Parse output for credentials
            gpp_file_found = "Downloaded GPP file successfully" in output
            decryption_success = "=== CREDENTIALS FOUND ===" in output

            # The log contains both the bash script AND the actual output
            # The script section ends with "Timeout:" - split there to get actual output
            output_section = output
            if "Timeout:" in output:
                parts = output.split("Timeout:", 1)
                if len(parts) > 1:
                    output_section = parts[1]

            # Extract username from actual output (not bash script)
            username = None
            username_match = re.search(
                r"\[\+\] Username:\s*(.+?)(?:\n|$)", output_section
            )
            if username_match:
                username = username_match.group(1).strip()

            # Extract password from actual output
            password = None
            password_match = re.search(
                r"\[\+\] Decrypted Password:\s*(.+?)(?:\n|$)", output_section
            )
            if password_match:
                password = password_match.group(1).strip()

            # Build credentials list from what was found in output
            credentials_found = []
            stored_in_db = False

            if username and password:
                credentials_found.append({"username": username, "password": password})

                # Try to store in database if we have a host_id
                if host_id:
                    try:
                        cred_id = credentials_manager.add_credential(
                            engagement_id=engagement_id,
                            host_id=host_id,
                            username=username,
                            password=password,
                            credential_type="plaintext",
                            source="gpp",
                            tool="gpp_extract",
                            notes="Extracted from Group Policy Preferences (GPP) file",
                        )
                        credentials_found[0]["id"] = cred_id
                        stored_in_db = True
                        logger.info(
                            f"GPP credentials stored: {username}:*** (cred_id={cred_id})"
                        )

                        # Create a finding
                        findings_manager.add_finding(
                            engagement_id=engagement_id,
                            host_id=host_id,
                            finding_type="credential_disclosure",
                            severity="critical",
                            title="GPP Password Disclosure (MS14-025)",
                            description=(
                                f"Group Policy Preferences (GPP) file contained plaintext credentials "
                                f"for user '{username}'. GPP passwords are encrypted with a known AES key "
                                f"published by Microsoft (MS14-025), making them trivially decryptable."
                            ),
                            evidence=f"Username: {username}\nSource: GPP XML file",
                            tool="gpp_extract",
                        )
                    except Exception as db_err:
                        logger.warning(
                            f"Could not store GPP credentials in DB: {db_err}"
                        )
                else:
                    logger.warning(
                        f"GPP credentials found but no host_id to store: {username}"
                    )

            # Determine status based on what was FOUND, not what was stored
            if credentials_found:
                status = STATUS_DONE
            elif gpp_file_found and not decryption_success:
                # File found but no password in it
                status = STATUS_NO_RESULTS
            elif "Failed to download" in output:
                status = STATUS_ERROR
            else:
                status = STATUS_NO_RESULTS

            return {
                "tool": "gpp_extract",
                "status": status,
                "target": target,
                "gpp_file_found": gpp_file_found,
                "decryption_success": decryption_success,
                "credentials_found": len(credentials_found),
                "credentials": credentials_found,
                "stored_in_db": stored_in_db,
                "username": username,
                "password": password,
            }

        except Exception as e:
            logger.error(f"Error parsing gpp_extract job: {e}")
            return {"tool": "gpp_extract", "status": STATUS_ERROR, "error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful GPP extraction results."""
        click.echo()
        click.echo(click.style("=" * 70, fg="green"))
        click.echo(click.style("GPP CREDENTIALS EXTRACTED!", fg="green", bold=True))
        click.echo(click.style("=" * 70, fg="green"))
        click.echo()

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                output = f.read()

            # Extract and display credentials from actual output section (after Timeout:)
            output_section = output
            if "Timeout:" in output:
                parts = output.split("Timeout:", 1)
                if len(parts) > 1:
                    output_section = parts[1]

            username_match = re.search(
                r"\[\+\] Username:\s*(.+?)(?:\n|$)", output_section
            )
            password_match = re.search(
                r"\[\+\] Decrypted Password:\s*(.+?)(?:\n|$)", output_section
            )

            if username_match:
                username = username_match.group(1).strip()
                click.echo(f"  Username: {click.style(username, fg='cyan', bold=True)}")

            if password_match:
                password = password_match.group(1).strip()
                if show_passwords:
                    click.echo(
                        f"  Password: {click.style(password, fg='yellow', bold=True)}"
                    )
                else:
                    click.echo(
                        f"  Password: {click.style('*' * len(password), fg='yellow')} (use --show-passwords to reveal)"
                    )

            click.echo()
            click.echo(click.style("  Next Steps:", bold=True))
            click.echo("    - Try these credentials on SMB, WinRM, RDP")
            click.echo("    - Check for Kerberoasting with these creds")
            click.echo("    - Run secretsdump for domain credential extraction")

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
        """Display GPP extraction warning."""
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("GPP EXTRACTION - WARNING", fg="yellow", bold=True))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

        # Read log if not provided
        if log_content is None and log_path:
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        if log_content:
            if "AttributeError" in log_content or "Traceback" in log_content:
                click.echo("  Plugin encountered an error during execution.")
                click.echo("  This may be a bug - please report it.")
            elif "Failed to download" in log_content:
                click.echo("  Could not download GPP file from share.")
                click.echo("  - Check if path is correct")
                click.echo("  - Verify anonymous access is allowed")
            else:
                click.echo("  Extraction completed with warnings.")

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
        """Display GPP extraction error."""
        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("GPP EXTRACTION FAILED", fg="red", bold=True))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                output = f.read()

            if "Failed to download" in output:
                click.echo("  Could not download GPP file from share")
                click.echo("  - Check if path is correct")
                click.echo("  - Verify anonymous access is allowed")
            elif "gpp-decrypt not found" in output:
                click.echo("  gpp-decrypt tool not installed")
                click.echo("  Install: apt install gpp-decrypt")
            else:
                click.echo("  Extraction failed - check raw logs for details")

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
        """Display no results for GPP extraction."""
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("GPP FILE - NO CREDENTIALS", fg="yellow", bold=True))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  GPP file was found but contained no cpassword attribute.")
        click.echo("  This GPP file may configure settings without credentials.")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
