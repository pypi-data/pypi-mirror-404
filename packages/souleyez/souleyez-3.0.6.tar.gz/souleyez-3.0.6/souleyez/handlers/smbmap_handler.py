#!/usr/bin/env python3
"""
SMBMap handler.

Consolidates parsing and display logic for SMBMap SMB share enumeration jobs.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_ERROR, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class SMBMapHandler(BaseToolHandler):
    """Handler for SMBMap SMB share enumeration jobs."""

    tool_name = "smbmap"
    display_name = "SMBMap"

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
        Parse SMBMap job results.

        Extracts SMB shares and stores them along with findings.
        """
        try:
            from souleyez.engine.result_handler import detect_tool_error
            from souleyez.parsers.smbmap_parser import (
                extract_findings,
                parse_smbmap_output,
            )
            from souleyez.storage.smb_shares import SMBSharesManager

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

            parsed = parse_smbmap_output(output, target)

            # Get or create host from target
            host_id = None
            if parsed.get("target"):
                is_ip = re.match(
                    r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", parsed["target"]
                )

                if is_ip:
                    host = host_manager.get_host_by_ip(engagement_id, parsed["target"])
                    if host:
                        host_id = host["id"]
                    else:
                        host_id = host_manager.add_or_update_host(
                            engagement_id, {"ip": parsed["target"], "status": "up"}
                        )

            if not host_id:
                return {"error": "Could not determine target host"}

            # Store SMB shares
            smm = SMBSharesManager()
            shares_added = 0
            files_added = 0

            for share in parsed.get("shares", []):
                share_id = smm.add_share(host_id, share)
                shares_added += 1

                # Add files if any
                share_files = [
                    f
                    for f in parsed.get("files", [])
                    if f.get("share") == share["name"]
                ]
                for file_data in share_files:
                    smm.add_file(share_id, file_data)
                    files_added += 1

            # Extract and store findings
            findings_added = 0
            findings = extract_findings(parsed)
            for finding in findings:
                findings_manager.add_finding(
                    engagement_id=engagement_id,
                    host_id=host_id,
                    finding_type="smb_share",
                    severity=finding.get("severity"),
                    title=finding.get("title"),
                    description=finding.get("description"),
                    evidence=finding.get("evidence"),
                    tool="smbmap",
                )
                findings_added += 1

            # Check for smbmap errors
            smbmap_error = detect_tool_error(output, "smbmap")

            # Detect GPP (Group Policy Preferences) files/directories containing credentials
            gpp_files = []

            # GPP XML files that contain credentials
            gpp_xml_patterns = [
                r"Groups\.xml",
                r"ScheduledTasks\.xml",
                r"Services\.xml",
                r"Drives\.xml",
                r"DataSources\.xml",
                r"Printers\.xml",
            ]

            # GPP directory names -> corresponding XML file
            # If we see these directories under Preferences, the XML file is inside
            gpp_dir_to_file = {
                "groups": "Groups.xml",
                "scheduledtasks": "ScheduledTasks.xml",
                "services": "Services.xml",
                "drives": "Drives.xml",
                "datasources": "DataSources.xml",
                "printers": "Printers.xml",
            }

            # Check raw output for GPP file paths
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                raw_output = f.read()

            # Track the current path context from smbmap output
            current_path = None
            current_share = None

            for line in raw_output.split("\n"):
                # Detect path headers like: ./Replication//active.htb/Policies/{GUID}/MACHINE/Preferences
                path_header = re.match(r"\./([^/]+)//(.+)", line.strip())
                if path_header:
                    current_share = path_header.group(1)
                    current_path = path_header.group(2)
                    continue

                # Method 1: Direct XML file detection (if depth is sufficient)
                for pattern in gpp_xml_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Found actual XML file in listing
                        file_match = re.search(
                            r"(Groups|ScheduledTasks|Services|Drives|DataSources|Printers)\.xml",
                            line,
                            re.IGNORECASE,
                        )
                        if file_match and current_path:
                            gpp_files.append(
                                {
                                    "share": current_share,
                                    "path": current_path + "/" + file_match.group(0),
                                    "file": file_match.group(0),
                                    "detected_by": "direct",
                                }
                            )

                # Method 2: Detect GPP directories under Preferences (infer XML file inside)
                # This handles shallow depth scans where we see Groups directory but not Groups.xml
                if current_path and "/Preferences" in current_path:
                    for dir_name, xml_file in gpp_dir_to_file.items():
                        # Match directory listing ending with the GPP dir name
                        # Format: dr--r--r--    0 Sat Jul 21 00:37:44 2018    Groups
                        if re.search(r"\s" + dir_name + r"\s*$", line, re.IGNORECASE):
                            # Found GPP directory - infer the XML file path
                            inferred_path = (
                                current_path
                                + "/"
                                + dir_name.capitalize()
                                + "/"
                                + xml_file
                            )
                            gpp_files.append(
                                {
                                    "share": current_share,
                                    "path": inferred_path,
                                    "file": xml_file,
                                    "detected_by": "directory_inference",
                                }
                            )
                            break

            # Deduplicate GPP files
            seen_paths = set()
            unique_gpp = []
            for gpp in gpp_files:
                path_key = gpp.get("path", "")
                if path_key and path_key not in seen_paths:
                    seen_paths.add(path_key)
                    unique_gpp.append(gpp)
            gpp_files = unique_gpp

            if gpp_files:
                logger.info(
                    f"smbmap found {len(gpp_files)} GPP file(s) - potential credentials!"
                )

            # Determine status
            if smbmap_error:
                status = STATUS_ERROR
            elif shares_added > 0 or findings_added > 0:
                status = STATUS_DONE
            else:
                status = STATUS_NO_RESULTS

            return {
                "tool": "smbmap",
                "status": status,
                "host": parsed.get("target"),
                "connection_status": parsed.get("status", "Unknown"),
                "shares_added": shares_added,
                "files_added": files_added,
                "findings_added": findings_added,
                "gpp_files": gpp_files,
                "has_gpp_files": len(gpp_files) > 0,
            }

        except Exception as e:
            logger.error(f"Error parsing smbmap job: {e}")
            return {"error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful SMBMap results."""
        try:
            from souleyez.parsers.smbmap_parser import parse_smbmap_output

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            parsed = parse_smbmap_output(log_content, job.get("target", ""))

            shares = parsed.get("shares", [])

            # Header
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo(click.style("SMB SHARE ENUMERATION", bold=True, fg="cyan"))
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

            if parsed.get("target"):
                click.echo(click.style(f"Target: {parsed['target']}", bold=True))
            elif job.get("target"):
                click.echo(click.style(f"Target: {job.get('target')}", bold=True))
            if parsed.get("status"):
                auth_color = (
                    "green" if parsed["status"] == "Authenticated" else "yellow"
                )
                click.echo(
                    f"Authentication: {click.style(parsed['status'], fg=auth_color)}"
                )
            click.echo()

            if not shares:
                self.display_no_results(job, log_path)
                return

            # Group shares by permissions
            writable = [s for s in shares if s.get("writable")]
            readable = [
                s for s in shares if s.get("readable") and not s.get("writable")
            ]
            no_access = [
                s for s in shares if not s.get("readable") and not s.get("writable")
            ]

            # Writable shares (HIGH RISK)
            if writable:
                click.echo(
                    click.style(
                        f"Writable Shares ({len(writable)}):", bold=True, fg="red"
                    )
                )
                for share in writable:
                    comment = f" - {share['comment']}" if share.get("comment") else ""
                    click.echo(f"  - {share['name']} ({share['permissions']}){comment}")
                click.echo()

            # Readable shares
            if readable:
                click.echo(
                    click.style(
                        f"Readable Shares ({len(readable)}):", bold=True, fg="yellow"
                    )
                )
                for share in readable:
                    comment = f" - {share['comment']}" if share.get("comment") else ""
                    click.echo(f"  - {share['name']} ({share['permissions']}){comment}")
                click.echo()

            # No access shares
            if no_access:
                click.echo(
                    click.style(
                        f"Restricted Shares ({len(no_access)}):", bold=True, dim=True
                    )
                )
                max_no_access = None if show_all else 5
                display_no_access = (
                    no_access if max_no_access is None else no_access[:max_no_access]
                )
                for share in display_no_access:
                    comment = f" - {share['comment']}" if share.get("comment") else ""
                    click.echo(f"  - {share['name']}{comment}")
                if max_no_access and len(no_access) > max_no_access:
                    click.echo(f"  ... and {len(no_access) - max_no_access} more")
                click.echo()

            # File enumeration results
            files = parsed.get("files", [])
            if files:
                click.echo(click.style(f"Files Enumerated: {len(files)}", bold=True))
                if show_all:
                    for f in files[:50]:
                        click.echo(
                            f"  - {f.get('share', '?')}/{f.get('name', 'unknown')}"
                        )
                    if len(files) > 50:
                        click.echo(f"  ... and {len(files) - 50} more files")
                click.echo()

            # Extract and display directory tree from raw output
            # Look for path headers like ./Share//path
            tree_lines = []
            gpp_paths = []
            for line in log_content.split("\n"):
                # Match path headers: ./Replication//active.htb/Policies/...
                path_match = re.match(r"\./([^/]+)//(.+)", line.strip())
                if path_match:
                    share = path_match.group(1)
                    path = path_match.group(2)
                    full_path = f"{share}/{path}"
                    tree_lines.append(full_path)
                    # Check for GPP-related paths
                    if "/Preferences/" in path or "/Preferences" in path:
                        gpp_paths.append(full_path)

            if tree_lines:
                click.echo(click.style("Directory Tree:", bold=True))
                # Show unique directory paths (limit to avoid spam)
                shown = 0
                max_show = 15 if not show_all else 50
                for path in tree_lines:
                    if shown >= max_show:
                        click.echo(f"  ... and {len(tree_lines) - shown} more paths")
                        break
                    # Highlight GPP paths
                    if "/Preferences" in path:
                        click.echo(
                            f"  {click.style('→', fg='yellow')} {click.style(path, fg='yellow', bold=True)}"
                        )
                    else:
                        click.echo(f"    {path}")
                    shown += 1
                click.echo()

            # Highlight GPP findings
            if gpp_paths:
                click.echo(
                    click.style(
                        "⚠️  GPP (Group Policy Preferences) Paths Found!",
                        bold=True,
                        fg="yellow",
                    )
                )
                click.echo(
                    click.style(
                        "   These may contain encrypted credentials (MS14-025):",
                        fg="yellow",
                    )
                )
                for gpp_path in gpp_paths[:5]:
                    click.echo(f"   • {gpp_path}")
                click.echo()

            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

        except Exception as e:
            logger.debug(f"Error in display_done: {e}")

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display warning status for SMBMap."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] SMBMAP", bold=True, fg="yellow"))
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo()
        click.echo("  Scan completed with warnings. Check raw logs for details.")
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
        """Display error status for SMBMap."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] SMBMAP FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common smbmap errors
        error_msg = None
        if log_content:
            if "Connection refused" in log_content or "Connection reset" in log_content:
                error_msg = "Connection refused - SMB service may be down"
            elif "timed out" in log_content.lower() or "timeout" in log_content.lower():
                error_msg = "Connection timed out - target may be slow or filtering"
            elif (
                "Authentication error" in log_content or "LOGON_FAILURE" in log_content
            ):
                error_msg = "Authentication failed - invalid credentials"
            elif "access denied" in log_content.lower():
                error_msg = "Access denied - insufficient privileges"
            elif "Errno 113" in log_content or "No route to host" in log_content:
                error_msg = "No route to host - network unreachable"
            elif "[-]" in log_content:
                match = re.search(r"\[-\]\s*(.+?)(?:\n|$)", log_content)
                if match:
                    error_msg = match.group(1).strip()[:100]

        if error_msg:
            click.echo(f"  {error_msg}")
        else:
            click.echo("  Scan failed - see raw logs for details (press 'r')")

        click.echo()
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_no_results(
        self,
        job: Dict[str, Any],
        log_path: str,
    ) -> None:
        """Display no_results status for SMBMap."""
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("SMB SHARE ENUMERATION", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

        if job.get("target"):
            click.echo(click.style(f"Target: {job.get('target')}", bold=True))
            click.echo()

        click.echo(click.style("Result: No SMB shares found", fg="yellow", bold=True))
        click.echo()
        click.echo("  The scan did not find any accessible SMB shares.")
        click.echo()
        click.echo(click.style("Tips:", dim=True))
        click.echo("  - Try with credentials: -u user -p password")
        click.echo("  - Check if SMB is enabled on the target")
        click.echo("  - Verify the target IP is correct")
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
