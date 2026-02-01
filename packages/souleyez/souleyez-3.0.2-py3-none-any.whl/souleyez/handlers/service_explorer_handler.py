#!/usr/bin/env python3
"""
Service Explorer handler.

Consolidates parsing and display logic for Service Explorer jobs.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_ERROR, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class ServiceExplorerHandler(BaseToolHandler):
    """Handler for Service Explorer file/data browser jobs."""

    tool_name = "service_explorer"
    display_name = "Service Explorer"

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
        Parse Service Explorer job results.

        Extracts files/data discovered and stores findings.
        """
        try:
            from souleyez.parsers.service_explorer_parser import (
                extract_findings,
                parse_service_explorer_output,
            )

            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()
            if findings_manager is None:
                from souleyez.storage.findings import FindingsManager

                findings_manager = FindingsManager()

            target = job.get("target", "")

            # Read log file
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                output = f.read()

            parsed = parse_service_explorer_output(output, target)

            # Get or create host from target
            host_id = None
            host_target = parsed.get("target") or target
            if host_target:
                # Extract IP from URL if needed
                if "://" in host_target:
                    from urllib.parse import urlparse

                    parsed_url = urlparse(host_target)
                    host_target = parsed_url.hostname or host_target

                is_ip = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", host_target)

                if is_ip:
                    host = host_manager.get_host_by_ip(engagement_id, host_target)
                    if host:
                        host_id = host["id"]
                    else:
                        host_id = host_manager.add_or_update_host(
                            engagement_id, {"ip": host_target, "status": "up"}
                        )

            # Extract and store findings
            findings_added = 0
            if host_id:
                findings = extract_findings(parsed)
                protocol = parsed.get("protocol", "unknown")

                for finding in findings:
                    findings_manager.add_finding(
                        engagement_id=engagement_id,
                        host_id=host_id,
                        finding_type=f"{protocol}_access",
                        severity=finding.get("severity"),
                        title=finding.get("title"),
                        description=finding.get("description"),
                        evidence=finding.get("evidence"),
                        tool="service_explorer",
                    )
                    findings_added += 1

            # Determine status
            if parsed.get("error"):
                status = STATUS_ERROR
            elif parsed.get("files_found", 0) > 0 or findings_added > 0:
                status = STATUS_DONE
            else:
                status = STATUS_NO_RESULTS

            return {
                "tool": "service_explorer",
                "status": status,
                "protocol": parsed.get("protocol"),
                "host": parsed.get("target"),
                "files_found": parsed.get("files_found", 0),
                "interesting_files": parsed.get("interesting_count", 0),
                "downloaded_files": parsed.get("downloaded_count", 0),
                "findings_added": findings_added,
                "errors": parsed.get("errors", []),
            }

        except Exception as e:
            logger.error(f"Error parsing service_explorer job: {e}")
            return {"error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful Service Explorer results."""
        try:
            from souleyez.parsers.service_explorer_parser import (
                parse_service_explorer_output,
            )

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            parsed = parse_service_explorer_output(log_content, job.get("target", ""))

            protocol = (parsed.get("protocol") or "SERVICE").upper()
            files = parsed.get("files", [])
            interesting = parsed.get("interesting_files", [])
            downloaded = parsed.get("downloaded_files", [])

            # Header
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo(
                click.style(f"{protocol} SERVICE EXPLORATION", bold=True, fg="cyan")
            )
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

            # Connection info
            if parsed.get("target"):
                click.echo(click.style(f"Target: {parsed['target']}", bold=True))
            if parsed.get("port"):
                click.echo(f"Port: {parsed['port']}")
            if parsed.get("username"):
                click.echo(f"Username: {parsed['username']}")
            click.echo()

            # Server info (Redis/MongoDB)
            if parsed.get("server_info"):
                click.echo(click.style("Server Information:", bold=True, fg="blue"))
                for key, value in parsed["server_info"].items():
                    if value is not None:
                        click.echo(f"  {key}: {value}")
                click.echo()

            if not files and not interesting:
                self.display_no_results(job, log_path)
                return

            # Summary
            click.echo(click.style("Summary:", bold=True))
            click.echo(f"  Total Items: {parsed.get('files_found', len(files))}")
            click.echo(
                f"  Interesting Files: {parsed.get('interesting_count', len(interesting))}"
            )
            click.echo(
                f"  Downloaded: {parsed.get('downloaded_count', len(downloaded))}"
            )
            click.echo()

            # Interesting files (HIGH PRIORITY)
            if interesting:
                click.echo(
                    click.style(
                        f"Interesting Files ({len(interesting)}):", bold=True, fg="red"
                    )
                )
                max_show = None if show_all else 15
                for item in (
                    interesting if max_show is None else interesting[:max_show]
                ):
                    path = item.get("full_path", item.get("name", "?"))
                    size = item.get("size", 0)
                    size_str = self._format_size(size)
                    click.echo(f"  {click.style(path, fg='yellow')} ({size_str})")
                if max_show and len(interesting) > max_show:
                    click.echo(f"  ... and {len(interesting) - max_show} more")
                click.echo()

            # Downloaded files
            if downloaded:
                click.echo(
                    click.style(
                        f"Downloaded Files ({len(downloaded)}):", bold=True, fg="green"
                    )
                )
                # Build evidence path
                target_host = parsed.get("target", job.get("target", "unknown"))
                proto = (parsed.get("protocol") or "files").lower()
                evidence_dir = os.path.expanduser(
                    f"~/.souleyez/evidence/{target_host}/{proto}"
                )
                for path in downloaded[:10]:
                    filename = os.path.basename(path)
                    local_path = os.path.join(evidence_dir, filename)
                    click.echo(f"  - {path}")
                    click.echo(f"    → {click.style(local_path, fg='cyan')}")
                if len(downloaded) > 10:
                    click.echo(f"  ... and {len(downloaded) - 10} more")
                click.echo()

            # File tree (if show_all or limited)
            if files and (show_all or len(files) <= 30):
                click.echo(click.style("File Listing:", bold=True))
                self._display_file_tree(files, show_all)
                click.echo()

            # Errors
            if parsed.get("errors"):
                click.echo(
                    click.style(
                        f"Errors ({len(parsed['errors'])}):", bold=True, fg="yellow"
                    )
                )
                for error in parsed["errors"][:5]:
                    click.echo(f"  - {error[:100]}")
                click.echo()

            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

        except Exception as e:
            logger.debug(f"Error in display_done: {e}")

    def _display_file_tree(self, files: list, show_all: bool = False) -> None:
        """Display files in a tree-like structure."""
        # Group by directory
        dirs = {}
        for item in files:
            path = item.get("path", "/")
            if path not in dirs:
                dirs[path] = []
            dirs[path].append(item)

        max_dirs = None if show_all else 10
        max_files_per_dir = None if show_all else 5
        dirs_shown = 0

        for dir_path, items in sorted(dirs.items()):
            if max_dirs and dirs_shown >= max_dirs:
                click.echo(f"  ... and {len(dirs) - max_dirs} more directories")
                break

            click.echo(f"  {click.style(dir_path, fg='blue')}/ ({len(items)} items)")
            files_shown = 0

            for item in items:
                if max_files_per_dir and files_shown >= max_files_per_dir:
                    click.echo(f"    ... and {len(items) - max_files_per_dir} more")
                    break

                name = item.get("name", "?")
                item_type = item.get("type", "file")
                size = item.get("size", 0)
                is_interesting = item.get("interesting", False)

                if item_type == "directory":
                    click.echo(f"    {click.style(name + '/', fg='blue')}")
                elif is_interesting:
                    click.echo(
                        f"    {click.style(name, fg='yellow')} ({self._format_size(size)})"
                    )
                else:
                    click.echo(f"    {name} ({self._format_size(size)})")

                files_shown += 1

            dirs_shown += 1

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable form."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display warning status for Service Explorer."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] SERVICE EXPLORER", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Exploration completed with warnings. Check raw logs for details.")
        click.echo("  Press [r] to view raw logs.")
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display error status for Service Explorer."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] SERVICE EXPLORER FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common errors
        error_msg = None
        if log_content:
            if (
                "Connection refused" in log_content
                or "connection failed" in log_content.lower()
            ):
                error_msg = "Connection refused - service may be down"
            elif "timed out" in log_content.lower() or "timeout" in log_content.lower():
                error_msg = "Connection timed out - target may be slow or filtering"
            elif "not installed" in log_content.lower():
                # Extract which package
                match = re.search(r"(\w+)\s+not installed", log_content, re.IGNORECASE)
                if match:
                    error_msg = f"Required package not installed: {match.group(1)}"
                else:
                    error_msg = "Required package not installed"
            elif (
                "authentication" in log_content.lower()
                or "login failed" in log_content.lower()
            ):
                error_msg = "Authentication failed - invalid credentials"
            elif '"error"' in log_content:
                # Try to extract JSON error
                import json

                try:
                    json_start = log_content.find("{")
                    if json_start >= 0:
                        data = json.loads(log_content[json_start:])
                        if data.get("error"):
                            error_msg = data["error"]
                except Exception:
                    pass

        if error_msg:
            click.echo(f"  {error_msg}")
        else:
            click.echo("  Exploration failed - see raw logs for details (press 'r')")

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for Service Explorer."""
        # Try to get protocol from job target
        protocol = "SERVICE"
        target = job.get("target", "")
        if "://" in target:
            protocol = target.split("://")[0].upper()

        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style(f"{protocol} SERVICE EXPLORATION", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

        if target:
            click.echo(click.style(f"Target: {target}", bold=True))
            click.echo()

        click.echo(
            click.style("Result: No files or data found", fg="yellow", bold=True)
        )
        click.echo()
        click.echo("  The service was accessible but no files or data were found.")
        click.echo()
        click.echo(click.style("Tips:", dim=True))
        click.echo("  - Try with credentials if available")
        click.echo("  - Increase depth with --depth 5")
        click.echo("  - Check if service requires specific paths")
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
