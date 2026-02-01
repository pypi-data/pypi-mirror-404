#!/usr/bin/env python3
"""
souleyez.handlers.lfi_extract_handler - Handler for LFI credential extraction

Parses LFI extract results and stores discovered credentials in the database.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_ERROR, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class LfiExtractHandler(BaseToolHandler):
    """Handler for LFI Extract custom tool."""

    tool_name = "lfi_extract"
    display_name = "LFI Extract"

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
        Parse LFI extract job results.

        Extracts credentials from the JSON result and stores them in the database.
        """
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

            # Read log file
            if not log_path or not os.path.exists(log_path):
                return {
                    "error": "Log file not found",
                    "status": STATUS_ERROR,
                    "summary": "Log file not found",
                }

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Extract JSON result
            json_match = re.search(
                r"=== JSON_RESULT ===\s*\n(.*?)\n=== END_JSON_RESULT ===",
                log_content,
                re.DOTALL,
            )

            if not json_match:
                return {
                    "error": "No JSON result found in log",
                    "status": STATUS_ERROR,
                    "summary": "Failed to parse output",
                }

            try:
                result = json.loads(json_match.group(1))
            except json.JSONDecodeError as e:
                return {
                    "error": f"Failed to parse JSON result: {e}",
                    "status": STATUS_ERROR,
                    "summary": "Failed to parse output",
                }

            credentials = result.get("credentials", [])

            if not credentials:
                files_decoded = result.get("decoded_files", [])
                if files_decoded:
                    summary = f"Decoded {len(files_decoded)} file{'s' if len(files_decoded) != 1 else ''}, no credentials found"
                else:
                    summary = "No files decoded, no credentials found"
                return {
                    "tool": "lfi_extract",
                    "status": STATUS_NO_RESULTS,
                    "sources_processed": result.get("sources_processed", 0),
                    "sources_failed": result.get("sources_failed", 0),
                    "credentials_found": 0,
                    "decoded_files": files_decoded,
                    "summary": summary,
                }

            # Get or create host from target URL
            target = job.get("target", "")
            host_id = None

            if target:
                from urllib.parse import urlparse

                parsed_url = urlparse(target)
                target_host = parsed_url.hostname or target

                host_result = host_manager.add_or_update_host(
                    engagement_id, {"ip": target_host, "status": "up"}
                )
                if isinstance(host_result, dict):
                    host_id = host_result.get("id")
                else:
                    host_id = host_result

            # Store credentials and create findings
            stored_credentials = []

            for cred in credentials:
                cred_type = cred.get("credential_type", "unknown")

                if cred_type == "database":
                    # Store database credential
                    try:
                        cred_id = credentials_manager.add_credential(
                            engagement_id=engagement_id,
                            host_id=host_id,
                            username=cred.get("username"),
                            password=cred.get("password"),
                            service=cred.get("database", "mysql"),
                            credential_type="database",
                            status="untested",
                            tool="lfi_extract",
                        )
                        stored_credentials.append(
                            {
                                "id": cred_id,
                                "type": "database",
                                "username": cred.get("username"),
                                "password": cred.get("password"),
                                "credential_type": "database",
                            }
                        )

                        # Create critical finding
                        findings_manager.add_finding(
                            engagement_id=engagement_id,
                            host_id=host_id,
                            title=f"LFI Credential Extraction: {cred.get('username')}@{cred.get('database', 'database')}",
                            finding_type="credential",
                            severity="critical",
                            description=(
                                f"Database credentials extracted via LFI vulnerability:\n\n"
                                f"**Username:** {cred.get('username')}\n"
                                f"**Database:** {cred.get('database', 'unknown')}\n"
                                f"**Host:** {cred.get('host', 'localhost')}\n\n"
                                f"**Source File:** {cred.get('source_file', 'unknown')}\n"
                                f"**Source URL:** {cred.get('source_url', 'unknown')}\n\n"
                                f"This indicates a critical LFI vulnerability that exposes database credentials. "
                                f"The attacker can now attempt to access the database directly."
                            ),
                            tool="lfi_extract",
                        )
                        logger.info(
                            f"Stored database credential: {cred.get('username')}@{cred.get('database')}"
                        )

                    except Exception as e:
                        logger.warning(f"Failed to store credential: {e}")

                elif cred_type in ("api_key", "secret_key"):
                    # Store API key as credential
                    try:
                        api_key = cred.get("api_key", "")
                        cred_id = credentials_manager.add_credential(
                            engagement_id=engagement_id,
                            host_id=host_id,
                            username=cred_type,
                            password=api_key,
                            service="api",
                            credential_type=cred_type,
                            status="untested",
                            tool="lfi_extract",
                        )
                        stored_credentials.append(
                            {
                                "id": cred_id,
                                "type": cred_type,
                                "credential_type": cred_type,
                            }
                        )

                        # Create finding for API key
                        findings_manager.add_finding(
                            engagement_id=engagement_id,
                            host_id=host_id,
                            title=f"LFI Exposed {cred_type.replace('_', ' ').title()}",
                            finding_type="credential",
                            severity="high",
                            description=(
                                f"API key/secret extracted via LFI vulnerability:\n\n"
                                f"**Type:** {cred_type}\n"
                                f"**Key (truncated):** {api_key[:20]}...{api_key[-10:] if len(api_key) > 30 else ''}\n\n"
                                f"**Source File:** {cred.get('source_file', 'unknown')}\n"
                                f"**Source URL:** {cred.get('source_url', 'unknown')}\n\n"
                                f"This key may provide access to external services or APIs."
                            ),
                            tool="lfi_extract",
                        )
                        logger.info(f"Stored {cred_type}")

                    except Exception as e:
                        logger.warning(f"Failed to store API key: {e}")

            # Build summary for UI display
            cred_count = len(stored_credentials)
            files_decoded = result.get("decoded_files", [])
            if cred_count > 0:
                summary = f"Extracted {cred_count} credential{'s' if cred_count != 1 else ''} from {len(files_decoded)} file{'s' if len(files_decoded) != 1 else ''}"
            elif files_decoded:
                summary = f"Decoded {len(files_decoded)} file{'s' if len(files_decoded) != 1 else ''}, no credentials found"
            else:
                summary = "No files decoded"

            return {
                "tool": "lfi_extract",
                "status": STATUS_DONE,
                "sources_processed": result.get("sources_processed", 0),
                "sources_failed": result.get("sources_failed", 0),
                "credentials_found": cred_count,
                "credentials": stored_credentials,
                "decoded_files": files_decoded,
                "summary": summary,
            }

        except Exception as e:
            logger.error(f"Error parsing lfi_extract job: {e}")
            return {"error": str(e), "status": STATUS_ERROR, "summary": f"Error: {e}"}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful LFI extract results."""
        try:
            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Extract JSON result
            json_match = re.search(
                r"=== JSON_RESULT ===\s*\n(.*?)\n=== END_JSON_RESULT ===",
                log_content,
                re.DOTALL,
            )

            if not json_match:
                click.echo("No results to display.")
                return

            result = json.loads(json_match.group(1))
            credentials = result.get("credentials", [])

            click.echo(click.style("=" * 70, fg="green"))
            click.echo(
                click.style("LFI EXTRACT - CREDENTIALS FOUND", bold=True, fg="green")
            )
            click.echo(click.style("=" * 70, fg="green"))
            click.echo()
            click.echo(f"  Sources processed: {result.get('sources_processed', 0)}")
            click.echo(
                f"  Files decoded: {', '.join(result.get('decoded_files', [])) or 'None'}"
            )
            click.echo()

            if credentials:
                click.echo(click.style("-" * 40, fg="green"))
                click.echo(click.style("EXTRACTED CREDENTIALS:", bold=True, fg="green"))
                click.echo(click.style("-" * 40, fg="green"))
                click.echo()

                for i, cred in enumerate(credentials, 1):
                    cred_type = cred.get("credential_type", "unknown")

                    if cred_type == "database":
                        click.echo(
                            click.style(
                                f"  [{i}] DATABASE CREDENTIALS", bold=True, fg="yellow"
                            )
                        )
                        click.echo(f"      Username: {cred.get('username')}")
                        if show_passwords:
                            click.echo(f"      Password: {cred.get('password')}")
                        else:
                            click.echo(
                                f"      Password: {'*' * 8} (use --show-passwords to reveal)"
                            )
                        click.echo(f"      Database: {cred.get('database', 'unknown')}")
                        click.echo(f"      Host: {cred.get('host', 'localhost')}")
                        click.echo(
                            f"      Source: {cred.get('source_file', 'unknown')}"
                        )

                    elif cred_type in ("api_key", "secret_key"):
                        click.echo(
                            click.style(
                                f"  [{i}] {cred_type.upper()}", bold=True, fg="yellow"
                            )
                        )
                        api_key = cred.get("api_key", "")
                        if show_passwords:
                            click.echo(f"      Key: {api_key}")
                        else:
                            click.echo(
                                f"      Key: {api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else ''}"
                            )
                        click.echo(
                            f"      Source: {cred.get('source_file', 'unknown')}"
                        )

                    click.echo()

                click.echo(click.style("-" * 40, fg="cyan"))
                click.echo(click.style("NEXT STEPS:", bold=True, fg="cyan"))
                click.echo(click.style("-" * 40, fg="cyan"))
                click.echo("  1. Test database credentials against MySQL/PostgreSQL")
                click.echo(
                    "  2. Check if credentials work on other services (SSH, FTP)"
                )
                click.echo("  3. Use 'souleyez creds list' to view all credentials")
                click.echo("  4. Chain to Hydra for credential spraying")
                click.echo()

            click.echo(click.style("=" * 70, fg="green"))
            click.echo()

        except Exception as e:
            logger.debug(f"Error in display_done: {e}")

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display error status for LFI extract."""
        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] LFI EXTRACT FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        if log_content:
            # Look for error messages
            if "Error:" in log_content:
                match = re.search(r"Error:\s*(.+?)(?:\n|$)", log_content)
                if match:
                    click.echo(f"  Error: {match.group(1)}")
            elif "No PHP filter URLs" in log_content:
                click.echo("  No PHP filter URLs were provided to extract from.")
                click.echo()
                click.echo(
                    click.style("  This tool expects URLs like:", fg="bright_black")
                )
                click.echo(
                    click.style(
                        "    http://target/?page=php://filter/convert.base64-encode/resource=config",
                        fg="bright_black",
                    )
                )
            else:
                click.echo("  Extraction failed - see raw logs for details.")
                click.echo("  Press [r] to view raw logs.")

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for LFI extract."""
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(
            click.style("LFI EXTRACT - NO CREDENTIALS FOUND", bold=True, fg="cyan")
        )
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
        click.echo("  The PHP source code was decoded but no credentials were found.")
        click.echo()
        click.echo(click.style("  This could mean:", fg="bright_black"))
        click.echo(
            click.style(
                "    - Config file doesn't contain database credentials",
                fg="bright_black",
            )
        )
        click.echo(
            click.style(
                "    - Credentials use a format not recognized by the parser",
                fg="bright_black",
            )
        )
        click.echo(
            click.style(
                "    - Try targeting different config files (wp-config.php, .env, etc.)",
                fg="bright_black",
            )
        )
        click.echo()
        click.echo(
            click.style(
                "  Check the raw logs for the decoded source code.", fg="bright_black"
            )
        )
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display warning status for LFI extract."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] LFI EXTRACT", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Extraction completed with warnings. Some URLs may have failed.")
        click.echo("  Press [r] to view raw logs for details.")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
