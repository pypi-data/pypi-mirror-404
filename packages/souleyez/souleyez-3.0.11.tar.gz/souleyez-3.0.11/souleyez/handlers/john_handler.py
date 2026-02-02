#!/usr/bin/env python3
"""
John the Ripper handler.

Consolidates parsing and display logic for John the Ripper password cracking jobs.
"""

import logging
import os
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class JohnHandler(BaseToolHandler):
    """Handler for John the Ripper password cracking jobs."""

    tool_name = "john"
    display_name = "John the Ripper"

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
        Parse John the Ripper job results.

        Extracts cracked passwords and stores them as credentials.
        """
        try:
            from souleyez.parsers.john_parser import parse_john_output

            # Import managers if not provided
            if findings_manager is None:
                from souleyez.storage.findings import FindingsManager

                findings_manager = FindingsManager()
            if credentials_manager is None:
                from souleyez.storage.credentials import CredentialsManager

                credentials_manager = CredentialsManager()

            # Read the log file
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Get hash file from job metadata if available
            hash_file = job.get("metadata", {}).get("hash_file", None)

            # Parse john output
            parsed = parse_john_output(log_content, hash_file)

            # Store credentials
            creds_added = 0
            for cred in parsed.get("cracked", []):
                username = cred.get("username", "")
                password = cred.get("password", "")

                if password:  # At minimum we need a password
                    try:
                        credentials_manager.add_credential(
                            engagement_id=engagement_id,
                            host_id=None,  # Hash cracking typically not tied to a specific host
                            username=username if username != "unknown" else "",
                            password=password,
                            service="cracked_hash",
                            credential_type="password",
                            tool="john",
                            status="cracked",
                            notes="Cracked by John the Ripper",
                        )
                        creds_added += 1
                    except Exception:
                        pass  # Skip duplicates

            # Create finding if we cracked passwords
            findings_added = 0
            if parsed.get("cracked"):
                usernames = [
                    c.get("username", "unknown")
                    for c in parsed["cracked"]
                    if c.get("username")
                ]
                usernames_str = ", ".join(usernames[:10])  # First 10
                if len(usernames) > 10:
                    usernames_str += f" (+{len(usernames) - 10} more)"

                findings_manager.add_finding(
                    engagement_id=engagement_id,
                    title=f"Password Hashes Cracked - {len(parsed['cracked'])} passwords recovered",
                    finding_type="credential",
                    severity="high",
                    description=f"John the Ripper successfully cracked {len(parsed['cracked'])} password hash(es).\n\n"
                    f"Usernames: {usernames_str}\n"
                    f"Session status: {parsed.get('session_status', 'unknown')}",
                    tool="john",
                )
                findings_added += 1

            # Determine status
            if creds_added > 0:
                status = STATUS_DONE
            elif parsed.get("session_status") == "completed":
                status = STATUS_NO_RESULTS  # Ran to completion but found nothing
            else:
                status = STATUS_NO_RESULTS

            return {
                "tool": "john",
                "status": status,
                "cracked_count": len(parsed.get("cracked", [])),
                "credentials_added": creds_added,
                "findings_added": findings_added,
                "session_status": parsed.get("session_status", "unknown"),
                "total_loaded": parsed.get("total_loaded", 0),
            }

        except Exception as e:
            logger.error(f"Error parsing john job: {e}")
            return {"error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful John the Ripper results."""
        try:
            from souleyez.parsers.john_parser import parse_john_output

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            parsed = parse_john_output(log_content)

            cracked = parsed.get("cracked", [])
            total_loaded = parsed.get("total_loaded", 0)
            total_cracked = parsed.get("total_cracked", len(cracked))
            session_status = parsed.get("session_status", "unknown")

            click.echo(click.style("=" * 70, fg="green"))
            click.echo(click.style("JOHN THE RIPPER RESULTS", bold=True, fg="green"))
            click.echo(click.style("=" * 70, fg="green"))
            click.echo()

            # Summary
            click.echo(click.style("Summary:", bold=True))
            click.echo(f"  Hashes loaded: {total_loaded}")
            click.echo(f"  Passwords cracked: {total_cracked}")
            click.echo(f"  Session status: {session_status}")
            click.echo()

            # Show cracked passwords
            if cracked:
                click.echo(
                    click.style(
                        f"Cracked Passwords ({len(cracked)}):", bold=True, fg="green"
                    )
                )
                max_show = None if show_all else 10
                display_cracked = cracked if max_show is None else cracked[:max_show]
                for c in display_cracked:
                    username = c.get("username", "?")
                    password = c.get("password", "?")
                    if show_passwords:
                        click.echo(click.style(f"  {username}:{password}", fg="green"))
                    else:
                        click.echo(click.style(f"  {username}:***", fg="green"))
                if max_show and len(cracked) > max_show:
                    click.echo(
                        click.style(
                            f"  ... and {len(cracked) - max_show} more", dim=True
                        )
                    )
            else:
                click.echo(click.style("  No passwords cracked.", fg="yellow"))

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
        """Display warning status for John the Ripper."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] JOHN THE RIPPER", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Password cracking completed with warnings.")
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
        """Display error status for John the Ripper."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] JOHN THE RIPPER FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common john errors
        error_msg = None
        if log_content:
            if "No password hashes loaded" in log_content:
                error_msg = "No password hashes loaded - check hash file format"
            elif "Unknown ciphertext format" in log_content:
                error_msg = "Unknown hash format - try specifying --format=TYPE"
            elif "No such file" in log_content or "cannot open" in log_content.lower():
                error_msg = "Hash file not found or cannot be opened"
            elif "out of memory" in log_content.lower():
                error_msg = "Out of memory - try reducing parallel tasks"
            elif "Invalid session name" in log_content:
                error_msg = "Invalid session name or session file corrupted"

        if error_msg:
            click.echo(f"  {error_msg}")
        else:
            click.echo(
                "  Password cracking failed - check raw logs for details (press 'r')"
            )

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for John the Ripper."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("JOHN THE RIPPER RESULTS", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  No passwords cracked.")
        click.echo()
        click.echo(click.style("Suggestions:", dim=True))
        click.echo("  - Try a larger wordlist")
        click.echo("  - Use rules: --rules=best64 or --rules=dive")
        click.echo("  - Try incremental mode: --incremental")
        click.echo("  - Check hash format is correct: --format=TYPE")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
