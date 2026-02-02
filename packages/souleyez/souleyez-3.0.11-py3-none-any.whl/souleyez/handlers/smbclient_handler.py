#!/usr/bin/env python3
"""
Handler for smbclient share browsing and file listing.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

import click

from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)

STATUS_DONE = "done"
STATUS_ERROR = "error"
STATUS_WARNING = "warning"
STATUS_NO_RESULTS = "no_results"


class SmbclientHandler(BaseToolHandler):
    """Handler for smbclient share browsing."""

    tool_name = "smbclient"
    display_name = "SMB Client"

    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    # Patterns for parsing smbclient ls output
    # Format: "  filename                          D        0  Tue Aug 22 10:17:06 2023"
    #         "  filename                          A     1234  Tue Aug 22 10:17:06 2023"
    # D = directory, A = archive (file), H = hidden, S = system, R = readonly
    DIR_ENTRY_PATTERN = (
        r"^\s{2}(\S.*?)\s{2,}([DAHSR]+)\s+(\d+)\s+\w+\s+\w+\s+\d+\s+[\d:]+\s+\d+"
    )

    # Error patterns
    ERROR_PATTERNS = [
        (r"NT_STATUS_ACCESS_DENIED", "Access denied"),
        (r"NT_STATUS_LOGON_FAILURE", "Authentication failed"),
        (r"NT_STATUS_BAD_NETWORK_NAME", "Share not found"),
        (r"NT_STATUS_HOST_UNREACHABLE", "Host unreachable"),
        (r"NT_STATUS_CONNECTION_REFUSED", "Connection refused"),
        (r"Connection to .* failed", "Connection failed"),
        (r"session setup failed", "Session setup failed"),
    ]

    # Directories to skip when extracting usernames
    # Note: 'library' removed - can be a valid username in some AD environments
    SKIP_DIRS = {
        ".",
        "..",
        "public",
        "shared",
        "common",
        "scripts",
        "profiles",
        "default",
        "all users",
        "default user",
        "public documents",
    }

    def parse_job(
        self,
        engagement_id: int,
        log_path: str,
        job: Dict[str, Any],
        host_manager: Optional[Any] = None,
        findings_manager: Optional[Any] = None,
        credentials_manager: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Parse smbclient results."""
        try:
            target = job.get("target", "")
            label = job.get("label", "")

            if not log_path or not os.path.exists(log_path):
                return {
                    "tool": "smbclient",
                    "status": STATUS_ERROR,
                    "error": "Log file not found",
                }

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Check for errors first
            for pattern, error_msg in self.ERROR_PATTERNS:
                if re.search(pattern, log_content, re.IGNORECASE):
                    return {
                        "tool": "smbclient",
                        "status": STATUS_ERROR,
                        "target": target,
                        "error": error_msg,
                    }

            # Extract share name from command or label
            share_name = ""
            share_match = re.search(r"//[^/]+/(\S+)", log_content)
            if share_match:
                share_name = share_match.group(1)
            elif "SMB_SPIDER_" in label:
                share_name = label.replace("SMB_SPIDER_", "")

            # Parse directory listing
            directories: List[Dict[str, Any]] = []
            files: List[Dict[str, Any]] = []
            extracted_usernames: List[str] = []

            for line in log_content.split("\n"):
                match = re.match(self.DIR_ENTRY_PATTERN, line)
                if match:
                    name = match.group(1).strip()
                    attrs = match.group(2)
                    size = int(match.group(3))

                    entry = {
                        "name": name,
                        "attrs": attrs,
                        "size": size,
                        "is_directory": "D" in attrs,
                    }

                    if "D" in attrs:
                        directories.append(entry)

                        # Check if this looks like a username (for homes shares)
                        if name.lower() not in self.SKIP_DIRS:
                            # Username patterns: FirstName.LastName, first.last, username
                            if re.match(r"^[A-Za-z][A-Za-z0-9._-]+$", name):
                                # Likely a username if it contains a dot (First.Last format)
                                # or is in a homes-type share
                                if "." in name or share_name.lower() in [
                                    "homes",
                                    "users",
                                    "home",
                                    "profiles",
                                ]:
                                    extracted_usernames.append(name)
                    else:
                        files.append(entry)

            # Check for interesting files
            interesting_files = []
            interesting_patterns = [
                (r"\.vbs$", "VBS script"),
                (r"\.ps1$", "PowerShell script"),
                (r"\.bat$", "Batch script"),
                (r"\.xml$", "XML config"),
                (r"Groups\.xml", "GPP file"),
                (r"web\.config", "Web config"),
                (r"\.ini$", "INI config"),
                (r"\.conf$", "Config file"),
                (r"password", "Password file"),
                (r"credential", "Credential file"),
            ]

            for f in files:
                for pattern, desc in interesting_patterns:
                    if re.search(pattern, f["name"], re.IGNORECASE):
                        interesting_files.append({"name": f["name"], "type": desc})
                        break

            # Determine status
            if directories or files:
                status = STATUS_DONE
            else:
                status = STATUS_NO_RESULTS

            # Build summary
            summary_parts = []
            if extracted_usernames:
                summary_parts.append(f"{len(extracted_usernames)} usernames extracted")
            if interesting_files:
                summary_parts.append(f"{len(interesting_files)} interesting files")
            if directories:
                summary_parts.append(f"{len(directories)} dirs")
            if files:
                summary_parts.append(f"{len(files)} files")
            summary = " | ".join(summary_parts) if summary_parts else "Empty share"

            result = {
                "tool": "smbclient",
                "status": status,
                "target": target,
                "share_name": share_name,
                "directories": directories,
                "files": files,
                "directory_count": len(directories),
                "file_count": len(files),
                "extracted_usernames": extracted_usernames,
                "interesting_files": interesting_files,
                "summary": summary,
            }

            if extracted_usernames:
                logger.info(
                    f"smbclient: Extracted {len(extracted_usernames)} potential usernames from {share_name}"
                )

                # Store extracted usernames as credentials
                if credentials_manager and host_manager:
                    try:
                        host = host_manager.get_host_by_ip(engagement_id, target)
                        if host:
                            for username in extracted_usernames:
                                try:
                                    credentials_manager.add_credential(
                                        engagement_id=engagement_id,
                                        host_id=host["id"],
                                        username=username,
                                        password="",
                                        service="smb",
                                        credential_type="username",
                                        tool="smbclient",
                                        status="untested",
                                    )
                                except Exception:
                                    pass  # Skip duplicates
                            logger.info(
                                f"smbclient: Stored {len(extracted_usernames)} usernames in credentials database"
                            )
                    except Exception as e:
                        logger.debug(f"Could not store usernames: {e}")

            if interesting_files:
                logger.info(
                    f"smbclient: Found {len(interesting_files)} interesting files in {share_name}"
                )

            return result

        except Exception as e:
            logger.error(f"Error parsing smbclient job: {e}")
            return {"tool": "smbclient", "status": STATUS_ERROR, "error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful smbclient results."""
        click.echo()
        click.echo(click.style("=" * 70, fg="green"))
        click.echo(click.style("SMB SHARE LISTING", fg="green", bold=True))
        click.echo(click.style("=" * 70, fg="green"))
        click.echo()

        parse_result = job.get("parse_result", {})
        share_name = parse_result.get("share_name", "Unknown")
        directories = parse_result.get("directories", [])
        files = parse_result.get("files", [])
        extracted_usernames = parse_result.get("extracted_usernames", [])
        interesting_files = parse_result.get("interesting_files", [])

        click.echo(f"  Share: {click.style(share_name, fg='cyan', bold=True)}")
        click.echo(f"  Directories: {len(directories)}  |  Files: {len(files)}")
        click.echo()

        # Show extracted usernames
        if extracted_usernames:
            click.echo(click.style("  EXTRACTED USERNAMES", bold=True, fg="yellow"))
            for username in extracted_usernames[:20]:  # Limit display
                click.echo(f"    {username}")
            if len(extracted_usernames) > 20:
                click.echo(f"    ... and {len(extracted_usernames) - 20} more")
            click.echo()

        # Show interesting files
        if interesting_files:
            click.echo(click.style("  INTERESTING FILES", bold=True, fg="red"))
            for f in interesting_files:
                click.echo(f"    {f['name']} ({f['type']})")
            click.echo()

        # Show directory listing if show_all
        if show_all and directories:
            click.echo(click.style("  DIRECTORIES", bold=True, fg="cyan"))
            for d in directories[:50]:
                click.echo(f"    {d['name']}/")
            click.echo()

        if show_all and files:
            click.echo(click.style("  FILES", bold=True, fg="cyan"))
            for f in files[:50]:
                size_str = f"{f['size']:,}" if f["size"] > 0 else "0"
                click.echo(f"    {f['name']:40} {size_str:>12} bytes")
            click.echo()

    def display_error(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display smbclient error."""
        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("SMB ACCESS FAILED", fg="red", bold=True))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        error = job.get("parse_result", {}).get("error") or job.get("error")
        if error:
            click.echo(f"  Error: {error}")
        else:
            click.echo("  Check log for details")
        click.echo()

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display smbclient warning."""
        # For smbclient, warning might indicate partial results
        self.display_done(job, log_path, show_all, False)

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
    ) -> None:
        """Display smbclient no results."""
        click.echo()
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("SMB SHARE EMPTY", fg="yellow", bold=True))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Share exists but contains no files or directories.")
        click.echo()


# Register handler
handler = SmbclientHandler()
