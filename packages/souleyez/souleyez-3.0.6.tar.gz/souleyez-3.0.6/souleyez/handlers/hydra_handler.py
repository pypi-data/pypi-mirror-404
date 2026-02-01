#!/usr/bin/env python3
"""
Hydra handler.

Consolidates parsing and display logic for Hydra brute-force jobs.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import (
    STATUS_DONE,
    STATUS_ERROR,
    STATUS_NO_RESULTS,
    STATUS_WARNING,
)
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class HydraHandler(BaseToolHandler):
    """Handler for Hydra brute-force attack jobs."""

    tool_name = "hydra"
    display_name = "Hydra"

    # All handlers enabled
    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    # Connection failure patterns
    CONNECTION_FAILURE_PATTERNS = [
        (r"connection refused", "Connection refused"),
        (r"timed?\s*out|timeout", "Connection timed out"),
        (r"could not connect|can not connect", "Could not connect"),
        (r"no route to host", "No route to host"),
        (r"network is unreachable", "Network unreachable"),
    ]

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
        Parse Hydra job results.

        Extracts credentials and usernames from the output.
        """
        try:
            from souleyez.engine.result_handler import detect_tool_error
            from souleyez.parsers.hydra_parser import parse_hydra_output

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

            # Read the log file
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Parse Hydra output
            target = job.get("target", "")
            parsed = parse_hydra_output(log_content, target)

            creds_added = 0
            usernames_added = 0
            hosts_affected = set()

            # Get target host for username-only entries
            target_host = parsed.get("target_host", target)
            # Extract IP from URL if needed
            if "://" in str(target_host):
                from urllib.parse import urlparse

                parsed_url = urlparse(target_host)
                target_host = parsed_url.hostname or target_host

            for cred in parsed.get("credentials", []):
                # Get actual host from credential
                actual_host = cred.get("host", target_host)

                # Skip if still contains multi-target string
                if not actual_host or " " in str(actual_host):
                    continue

                hosts_affected.add(actual_host)

                # Get or create host for this specific IP
                host = host_manager.get_host_by_ip(engagement_id, actual_host)
                if not host:
                    host = host_manager.add_or_update_host(
                        engagement_id, {"ip": actual_host, "status": "up"}
                    )
                host_id = host["id"]

                # Add credential
                credentials_manager.add_credential(
                    engagement_id=engagement_id,
                    host_id=host_id,
                    username=cred["username"],
                    password=cred["password"],
                    service=cred.get("service", parsed.get("service", "unknown")),
                    port=cred.get("port", parsed.get("port")),
                    credential_type="password",
                    tool="hydra",
                    status="valid",
                )
                creds_added += 1

            # Handle username-only enumeration results
            for username in parsed.get("usernames", []):
                actual_host = target_host
                if not actual_host or " " in str(actual_host):
                    continue

                hosts_affected.add(actual_host)

                # Get or create host
                host = host_manager.get_host_by_ip(engagement_id, actual_host)
                if not host:
                    host = host_manager.add_or_update_host(
                        engagement_id, {"ip": actual_host, "status": "up"}
                    )
                host_id = host["id"]

                # Add username-only credential
                credentials_manager.add_credential(
                    engagement_id=engagement_id,
                    host_id=host_id,
                    username=username,
                    password="",
                    service=parsed.get("service", "http-post-form"),
                    port=parsed.get("port"),
                    credential_type="username",
                    tool="hydra",
                    status="username_valid",
                )
                usernames_added += 1

            # Create findings
            findings_added = 0

            # Finding for valid credentials (high severity)
            if parsed.get("credentials"):
                cred_list = parsed["credentials"]
                usernames_str = ", ".join([c["username"] for c in cred_list])
                service = parsed.get("service", "unknown")
                port = parsed.get("port", "")

                first_host = list(hosts_affected)[0] if hosts_affected else target_host
                host = host_manager.get_host_by_ip(engagement_id, first_host)
                finding_host_id = host["id"] if host else None

                findings_manager.add_finding(
                    engagement_id=engagement_id,
                    title=f"Valid Credentials Found - {service.upper()}",
                    finding_type="credential",
                    severity="high",
                    description=f"Hydra brute-force attack discovered {len(cred_list)} valid credential(s) on {service}:{port}.\n\n"
                    f"Affected usernames: {usernames_str}\n\n"
                    f"These credentials allow direct access to the service.",
                    host_id=finding_host_id,
                    tool="hydra",
                )
                findings_added += 1

            # Finding for username enumeration (medium severity)
            if parsed.get("usernames"):
                username_list = parsed["usernames"]
                usernames_str = ", ".join(username_list)
                service = parsed.get("service", "http-post-form")
                port = parsed.get("port", 80)

                first_host = list(hosts_affected)[0] if hosts_affected else target_host
                host = host_manager.get_host_by_ip(engagement_id, first_host)
                finding_host_id = host["id"] if host else None

                findings_manager.add_finding(
                    engagement_id=engagement_id,
                    title="Username Enumeration - Valid Usernames Discovered",
                    finding_type="enumeration",
                    severity="medium",
                    description=f"Username enumeration via {service}:{port} revealed {len(username_list)} valid username(s).\n\n"
                    f"Valid usernames: {usernames_str}\n\n"
                    f"The application differentiates between valid and invalid usernames in error messages, "
                    f"allowing attackers to enumerate valid accounts.",
                    host_id=finding_host_id,
                    tool="hydra",
                )
                findings_added += 1

            # Check for hydra errors
            hydra_error = detect_tool_error(log_content, "hydra")
            summary = None

            # Determine status based on results
            if hydra_error:
                hydra_error_lower = hydra_error.lower()
                if "connection refused" in hydra_error_lower:
                    status = STATUS_WARNING
                    summary = "Target unreachable (connection refused)"
                elif "timed out" in hydra_error_lower or "timeout" in hydra_error_lower:
                    status = STATUS_WARNING
                    summary = "Target unreachable (connection timed out)"
                elif (
                    "could not connect" in hydra_error_lower
                    or "can not connect" in hydra_error_lower
                ):
                    status = STATUS_WARNING
                    summary = "Target unreachable (could not connect)"
                elif "no route to host" in hydra_error_lower:
                    status = STATUS_WARNING
                    summary = "Target unreachable (no route to host)"
                elif "network is unreachable" in hydra_error_lower:
                    status = STATUS_WARNING
                    summary = "Target unreachable (network unreachable)"
                else:
                    status = STATUS_ERROR
                    summary = f"Error: {hydra_error}"
            elif len(parsed.get("credentials", [])) > 0:
                status = STATUS_DONE
                cred_count = len(parsed.get("credentials", []))
                summary = f"Found {cred_count} valid credential{'s' if cred_count != 1 else ''}"
            elif len(parsed.get("usernames", [])) > 0:
                status = STATUS_DONE
                user_count = len(parsed.get("usernames", []))
                summary = (
                    f"Found {user_count} valid username{'s' if user_count != 1 else ''}"
                )
            else:
                status = STATUS_NO_RESULTS
                summary = "No valid credentials found (target responded)"

            result = {
                "tool": "hydra",
                "status": status,
                "target": target,
                "hosts_affected": list(hosts_affected),
                "service": parsed.get("service"),
                "port": parsed.get("port"),
                "credentials_found": len(parsed.get("credentials", [])),
                "credentials_added": creds_added,
                "credentials": parsed.get(
                    "credentials", []
                ),  # Include actual creds for smart chains
                "usernames_found": len(parsed.get("usernames", [])),
                "usernames": parsed.get("usernames", []),
                "usernames_added": usernames_added,
                "findings_added": findings_added,
                "attempts": parsed.get("attempts", 0),
            }
            if summary:
                result["summary"] = summary
            return result

        except Exception as e:
            logger.error(f"Error parsing hydra job: {e}")
            return {"error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful Hydra attack results."""
        try:
            from souleyez.parsers.hydra_parser import parse_hydra_output

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            parsed = parse_hydra_output(log_content, job.get("target", ""))

            credentials = parsed.get("credentials", [])
            usernames = parsed.get("usernames", [])

            if credentials:
                click.echo(click.style("=" * 70, fg="cyan"))
                click.echo(click.style("HYDRA CREDENTIALS FOUND", bold=True, fg="cyan"))
                click.echo(click.style("=" * 70, fg="cyan"))
                click.echo()

                # Summary info
                click.echo(
                    click.style(
                        f"Target: {parsed.get('target_host', 'unknown')}", bold=True
                    )
                )
                click.echo(
                    f"Service: {parsed.get('service', 'unknown')} (port {parsed.get('port', 'unknown')})"
                )
                click.echo(
                    click.style(
                        f"\n{len(credentials)} Valid Credential(s) Found",
                        fg="green",
                        bold=True,
                    )
                )
                click.echo()

                # Display credentials
                for i, cred in enumerate(credentials, 1):
                    host = cred.get("host", parsed.get("target_host", "unknown"))
                    service = cred.get("service", parsed.get("service", "unknown"))
                    port = cred.get("port", parsed.get("port", "unknown"))

                    click.echo(
                        click.style(
                            f"[{i}] {host}:{port} ({service})", bold=True, fg="green"
                        )
                    )
                    click.echo(
                        f"    Username: {click.style(cred['username'], fg='yellow')}"
                    )
                    if show_passwords:
                        click.echo(
                            f"    Password: {click.style(cred['password'], fg='yellow')}"
                        )
                    else:
                        click.echo(
                            f"    Password: {click.style('********', fg='red', dim=True)}"
                        )
                    click.echo()

                if not show_passwords:
                    click.echo(
                        click.style(
                            "Passwords are hidden. Use [p] to reveal.",
                            fg="yellow",
                            dim=True,
                        )
                    )
                    click.echo()

                # Check if credentials were saved
                engagement_id = job.get("engagement_id")
                if engagement_id:
                    try:
                        from souleyez.storage.credentials import CredentialsManager

                        cm = CredentialsManager()
                        all_creds = cm.list_credentials(engagement_id)
                        hydra_creds = [c for c in all_creds if c.get("tool") == "hydra"]
                        if hydra_creds:
                            click.echo(
                                click.style(
                                    f"Credentials saved to database ({len(hydra_creds)} total from Hydra)",
                                    fg="green",
                                )
                            )
                            click.echo()
                    except Exception:
                        pass

                click.echo(click.style("=" * 70, fg="cyan"))
                click.echo()

            elif usernames:
                # Username-only enumeration results
                click.echo(click.style("=" * 70, fg="yellow"))
                click.echo(
                    click.style("HYDRA VALID USERNAMES FOUND", bold=True, fg="yellow")
                )
                click.echo(click.style("=" * 70, fg="yellow"))
                click.echo()

                click.echo(
                    click.style(
                        f"Target: {parsed.get('target_host', 'unknown')}", bold=True
                    )
                )
                click.echo(
                    f"Service: {parsed.get('service', 'unknown')} (port {parsed.get('port', 'unknown')})"
                )
                click.echo(
                    click.style(
                        f"\n{len(usernames)} Valid Username(s) Found (password unknown)",
                        fg="yellow",
                        bold=True,
                    )
                )
                click.echo()

                for i, username in enumerate(usernames, 1):
                    click.echo(
                        click.style(
                            f"[{i}] Username: {username}", bold=True, fg="yellow"
                        )
                    )
                click.echo()

                click.echo(
                    click.style(
                        "Note: These usernames exist but passwords were not cracked.",
                        fg="white",
                    )
                )
                click.echo(
                    click.style(
                        "Consider running targeted password attacks on these accounts.",
                        fg="white",
                    )
                )
                click.echo()

                click.echo(click.style("=" * 70, fg="yellow"))
                click.echo()

        except Exception as e:
            logger.debug(f"Error in display_done: {e}")

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display warning status for Hydra attack."""
        parse_result = job.get("parse_result", {})
        summary = "Hydra attack encountered issues"
        if isinstance(parse_result, dict):
            summary = parse_result.get("summary", "Hydra attack encountered issues")

        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] HYDRA ATTACK", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo(f"  {summary}")
        click.echo()
        click.echo(click.style("  Common causes:", fg="bright_black"))
        click.echo(
            click.style(
                "    - Target unreachable (firewall, network issue)", fg="bright_black"
            )
        )
        click.echo(
            click.style("    - Service not running on expected port", fg="bright_black")
        )
        click.echo(
            click.style(
                "    - Too many connections - try reducing threads", fg="bright_black"
            )
        )
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display error status for Hydra attack."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] HYDRA ATTACK FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common hydra errors
        error_msg = None
        if log_content:
            if "Connection refused" in log_content:
                error_msg = "Connection refused - service may be down or port closed"
            elif "could not connect" in log_content.lower():
                error_msg = "Could not connect to target service"
            elif "timed out" in log_content.lower() or "timeout" in log_content.lower():
                error_msg = "Connection timed out - target may be slow or filtering"
            elif "too many connections" in log_content.lower():
                error_msg = "Too many connections - try reducing threads with -t"
            elif "target does not support" in log_content.lower():
                error_msg = "Target does not support the specified protocol"
            elif "ERROR" in log_content:
                match = re.search(r"\[ERROR\]\s*(.+?)(?:\n|$)", log_content)
                if match:
                    error_msg = match.group(1).strip()[:100]

        if error_msg:
            click.echo(f"  {error_msg}")
        else:
            click.echo("  Attack failed - see raw logs for details (press 'r')")

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for Hydra attack."""
        # Try to get target info from log
        target = job.get("target", "unknown")
        service = "unknown"
        port = "unknown"

        if log_path and os.path.exists(log_path):
            try:
                from souleyez.parsers.hydra_parser import parse_hydra_output

                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
                parsed = parse_hydra_output(log_content, target)
                target = parsed.get("target_host") or target
                service = parsed.get("service", "unknown")
                port = parsed.get("port", "unknown")
            except Exception:
                pass

        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("HYDRA PASSWORD ATTACK", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

        click.echo(click.style(f"Target: {target}", bold=True))
        if service != "unknown" or port != "unknown":
            click.echo(f"Service: {service} (port {port})")
        click.echo()

        click.echo(
            click.style("Result: No valid credentials found", fg="yellow", bold=True)
        )
        click.echo()
        click.echo("  The password attack completed without finding valid credentials.")
        click.echo()
        click.echo(click.style("Tips:", dim=True))
        click.echo("  - Try a larger wordlist")
        click.echo("  - Verify the service is accessible")
        click.echo("  - Check if account lockout is enabled")
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
