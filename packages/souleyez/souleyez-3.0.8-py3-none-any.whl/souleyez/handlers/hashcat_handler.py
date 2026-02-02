#!/usr/bin/env python3
"""
Hashcat handler.

Consolidates parsing and display logic for Hashcat password cracking jobs.
"""

import logging
import os
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class HashcatHandler(BaseToolHandler):
    """Handler for Hashcat password cracking jobs."""

    tool_name = "hashcat"
    display_name = "Hashcat"

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
        Parse Hashcat job results.

        Extracts cracked passwords and stores them as credentials.
        """
        try:
            from souleyez.parsers.hashcat_parser import parse_hashcat_output

            # Import managers if not provided
            if findings_manager is None:
                from souleyez.storage.findings import FindingsManager

                findings_manager = FindingsManager()
            if credentials_manager is None:
                from souleyez.storage.credentials import CredentialsManager

                credentials_manager = CredentialsManager()

            # Read the log file if it exists
            log_content = ""
            if log_path and os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()

            # Parse hashcat output
            # hash_file can be in metadata or as the job target (since target IS the hash file for hashcat)
            hash_file = job.get("metadata", {}).get("hash_file", "") or job.get(
                "target", ""
            )
            parsed = parse_hashcat_output(log_content, hash_file)

            # If no cracked passwords but potfile hits OR no log, check potfile directly
            # This handles both: (1) no log file, (2) log exists but hashes were in potfile
            has_potfile_hits = parsed.get("stats", {}).get("potfile_hits", 0) > 0
            no_cracked = not parsed.get("cracked")
            if (no_cracked and has_potfile_hits) or (not log_content and hash_file):
                if hash_file and os.path.exists(hash_file):
                    from souleyez.parsers.hashcat_parser import _get_potfile_cracked

                    # Build hash → username mapping from hash file
                    hash_to_username = {}
                    try:
                        import re

                        with open(
                            hash_file, "r", encoding="utf-8", errors="replace"
                        ) as f:
                            for line in f:
                                line = line.strip()
                                if ":" in line and not line.startswith("#"):
                                    parts = line.split(":")
                                    if len(parts) >= 2:
                                        potential_user = parts[0].strip()
                                        potential_hash = parts[1].strip()
                                        if re.match(
                                            r"^[a-fA-F0-9]+$", potential_hash
                                        ) or potential_hash.startswith("$"):
                                            hash_to_username[potential_hash.lower()] = (
                                                potential_user
                                            )
                    except Exception:
                        pass
                    potfile_cracked = _get_potfile_cracked(hash_file, hash_to_username)
                    if potfile_cracked:
                        parsed["cracked"] = potfile_cracked
                        parsed["stats"]["cracked_count"] = len(potfile_cracked)
                        parsed["stats"]["status"] = "already_cracked"
                        parsed["stats"]["potfile_hits"] = len(potfile_cracked)

            # Store credentials
            creds_added = 0
            for cracked in parsed.get("cracked", []):
                try:
                    # Extract username if available (Kerberos hashes include it)
                    username = cracked.get("username", "")
                    hash_type = cracked.get("hash_type", "unknown")

                    # Determine service based on hash type
                    if hash_type == "kerberos":
                        service = "kerberos"
                    else:
                        service = "cracked_hash"

                    credentials_manager.add_credential(
                        engagement_id=engagement_id,
                        host_id=None,  # Hash cracking typically not tied to a specific host
                        username=username,
                        password=cracked["password"],
                        service=service,
                        credential_type="password",
                        tool="hashcat",
                        status="cracked",
                        notes=f"Cracked {hash_type} hash: {cracked['hash'][:50]}...",
                    )
                    creds_added += 1
                    logger.info(f"Hashcat cracked: {username}:{cracked['password']}")
                except Exception as e:
                    logger.debug(f"Error adding credential: {e}")
                    pass  # Skip duplicates

            # Create finding if we cracked passwords
            findings_added = 0
            if parsed.get("cracked"):
                findings_manager.add_finding(
                    engagement_id=engagement_id,
                    title=f"Password Hashes Cracked - {len(parsed['cracked'])} passwords recovered",
                    finding_type="credential",
                    severity="high",
                    description=f"Hashcat successfully cracked {len(parsed['cracked'])} password hash(es).\n\n"
                    f"Status: {parsed['stats'].get('status', 'unknown')}\n"
                    f"Cracked: {parsed['stats'].get('cracked_count', len(parsed['cracked']))}",
                    tool="hashcat",
                )
                findings_added += 1

            # Determine status - check multiple indicators
            cracked_list = parsed.get("cracked", [])
            hashcat_status = parsed["stats"].get("status", "unknown")

            if creds_added > 0 or cracked_list or hashcat_status == "cracked":
                status = STATUS_DONE
            elif hashcat_status == "exhausted":
                status = STATUS_NO_RESULTS  # Ran to completion but found nothing
            else:
                status = STATUS_NO_RESULTS

            # Build summary for job queue display
            summary_parts = []
            total_count = parsed["stats"].get("total_count", 0)
            cracked_count = len(cracked_list)
            if cracked_count > 0:
                summary_parts.append(f"{cracked_count}/{total_count} cracked")
            elif total_count > 0:
                summary_parts.append(f"0/{total_count} cracked")
            if hashcat_status and hashcat_status != "unknown":
                summary_parts.append(hashcat_status)
            summary = " | ".join(summary_parts) if summary_parts else "No results"

            return {
                "tool": "hashcat",
                "status": status,
                "summary": summary,
                "cracked_count": len(cracked_list),
                "cracked": cracked_list,  # Include cracked list for chaining
                "credentials_added": creds_added,
                "findings_added": findings_added,
                "hashcat_status": hashcat_status,
            }

        except Exception as e:
            logger.error(f"Error parsing hashcat job: {e}")
            return {"error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful Hashcat results."""
        try:
            from souleyez.parsers.hashcat_parser import parse_hashcat_output

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            parsed = parse_hashcat_output(log_content)

            cracked = parsed.get("cracked", [])
            stats = parsed.get("stats", {})
            cracked_count = stats.get("cracked_count", len(cracked))
            total_count = stats.get("total_count", 0)
            potfile_hits = stats.get("potfile_hits", 0)
            status = stats.get("status", "unknown")

            # Adjust title based on whether we have new cracks or potfile hits
            if cracked:
                title = "HASHCAT RESULTS"
            elif potfile_hits > 0:
                title = "HASHCAT - ALREADY CRACKED"
            else:
                title = "HASHCAT RESULTS"

            click.echo(click.style("=" * 70, fg="green"))
            click.echo(click.style(title, bold=True, fg="green"))
            click.echo(click.style("=" * 70, fg="green"))
            click.echo()

            # Summary
            click.echo(click.style("Summary:", bold=True))
            if total_count > 0:
                click.echo(f"  Recovered: {cracked_count}/{total_count}")
            elif cracked_count > 0:
                click.echo(f"  Cracked: {cracked_count}")
            if potfile_hits > 0:
                click.echo(f"  Already cracked (potfile): {potfile_hits}")
            click.echo(f"  Status: {status}")
            click.echo()

            # Show cracked passwords
            if cracked:
                click.echo(
                    click.style(
                        f"Cracked Hashes ({len(cracked)}):", bold=True, fg="green"
                    )
                )
                max_show = None if show_all else 10
                display_cracked = cracked if max_show is None else cracked[:max_show]
                for c in display_cracked:
                    username = c.get("username", "")
                    password = c.get("password", "?")
                    hash_type = c.get("hash_type", "unknown")

                    if username:
                        # Show username:password for Kerberos
                        if show_passwords:
                            click.echo(
                                click.style(
                                    f"  [{hash_type}] {username}:{password}", fg="green"
                                )
                            )
                        else:
                            click.echo(
                                click.style(
                                    f"  [{hash_type}] {username}:***", fg="green"
                                )
                            )
                    else:
                        # Show hash preview for other types
                        hash_preview = c.get("hash", "?")[:24] + "..."
                        if show_passwords:
                            click.echo(
                                click.style(
                                    f"  {hash_preview} -> {password}", fg="green"
                                )
                            )
                        else:
                            click.echo(
                                click.style(f"  {hash_preview} -> ***", fg="green")
                            )
                if max_show and len(cracked) > max_show:
                    click.echo(
                        click.style(
                            f"  ... and {len(cracked) - max_show} more", dim=True
                        )
                    )

                # Hint about viewing passwords
                click.echo()
                click.echo(
                    click.style(
                        "  Tip: Use 'souleyez creds list' to view all cracked credentials",
                        dim=True,
                    )
                )
            elif potfile_hits > 0:
                # No new cracks but potfile hits - show how to view
                click.echo(
                    click.style(
                        f"  {potfile_hits} hash(es) were already cracked in a previous run.",
                        fg="green",
                    )
                )
                click.echo()
                click.echo(click.style("To view cracked passwords:", bold=True))
                target = job.get("target", "")
                if target:
                    click.echo(f"  hashcat --show {target}")
                click.echo("  souleyez creds list")
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
        """Display warning status for Hashcat."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] HASHCAT", bold=True, fg="yellow"))
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
        """Display error status for Hashcat."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] HASHCAT FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common hashcat errors
        error_msg = None
        if log_content:
            if "No hashes loaded" in log_content:
                error_msg = "No hashes loaded - check hash file format"
            elif "Token length exception" in log_content:
                error_msg = "Invalid hash format - wrong hash type (-m) specified"
            elif "Cannot find input" in log_content or "No such file" in log_content:
                error_msg = "Hash file or wordlist not found"
            elif "CUDA" in log_content or "OpenCL" in log_content:
                if "error" in log_content.lower():
                    error_msg = "GPU driver or OpenCL/CUDA error - check GPU drivers"
            elif "out of memory" in log_content.lower():
                error_msg = "GPU out of memory - try smaller workload (-w)"
            elif "Separator unmatched" in log_content:
                error_msg = "Invalid hash format or separator"

        if error_msg:
            click.echo(f"  {error_msg}")
        else:
            click.echo(
                "  Hash cracking failed - check raw logs for details (press 'r')"
            )

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for Hashcat."""
        # Check if hashes were already cracked (potfile hits)
        potfile_hits = 0
        if log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
                # Count potfile hits
                potfile_hits = log_content.count("Removed hash found as potfile entry")
                # Also check for bulk message
                import re

                bulk_match = re.search(
                    r"Removed (\d+) hash(?:es)? found as potfile entr", log_content
                )
                if bulk_match:
                    potfile_hits = int(bulk_match.group(1))
            except Exception:
                pass

        if potfile_hits > 0:
            # Hashes already cracked - show success message
            click.echo(click.style("=" * 70, fg="green"))
            click.echo(click.style("HASHCAT - ALREADY CRACKED", bold=True, fg="green"))
            click.echo(click.style("=" * 70, fg="green"))
            click.echo()
            click.echo(f"  {potfile_hits} hash(es) already cracked in previous run.")
            click.echo()
            click.echo(click.style("To view cracked passwords:", bold=True))
            target = job.get("target", "")
            if target:
                click.echo(f"  hashcat --show {target}")
            click.echo("  souleyez creds list")
            click.echo()
            click.echo(click.style("=" * 70, fg="green"))
            click.echo()
        else:
            # Actually no results
            click.echo(click.style("=" * 70, fg="yellow"))
            click.echo(click.style("HASHCAT RESULTS", bold=True, fg="yellow"))
            click.echo(click.style("=" * 70, fg="yellow"))
            click.echo()
            click.echo("  No passwords cracked.")
            click.echo()
            click.echo(click.style("Suggestions:", dim=True))
            click.echo("  - Try a larger wordlist")
            click.echo("  - Use rules: -r best64.rule or -r dive.rule")
            click.echo("  - Try mask attack: -a 3 ?a?a?a?a?a?a")
            click.echo("  - Verify hash mode is correct: -m HASHTYPE")
            click.echo()
            click.echo(click.style("=" * 70, fg="yellow"))
            click.echo()
