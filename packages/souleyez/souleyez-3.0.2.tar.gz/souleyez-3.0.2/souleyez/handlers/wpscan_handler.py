#!/usr/bin/env python3
"""
WPScan handler.

Consolidates parsing and display logic for WPScan WordPress security scanner jobs.
"""

import logging
import os
import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_ERROR, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class WPScanHandler(BaseToolHandler):
    """Handler for WPScan WordPress security scanner jobs."""

    tool_name = "wpscan"
    display_name = "WPScan"

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
        Parse WPScan job results.

        Extracts WordPress vulnerabilities for plugins, themes, and core.
        """
        try:
            from souleyez.engine.result_handler import detect_tool_error
            from souleyez.parsers.wpscan_parser import parse_wpscan_output

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
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                output = f.read()

            parsed = parse_wpscan_output(output, target)

            # Get or create host
            host_id = None
            target_ip = target
            if "://" in str(target):
                parsed_url = urlparse(target)
                target_ip = parsed_url.hostname or target

            if target_ip:
                host = host_manager.get_host_by_ip(engagement_id, target_ip)
                if not host:
                    host_id = host_manager.add_or_update_host(
                        engagement_id, {"ip": target_ip, "status": "up"}
                    )
                else:
                    host_id = host["id"]

            # Store findings
            findings_added = 0

            # WordPress version vulnerabilities
            for vuln in parsed.get("findings", []):
                findings_manager.add_finding(
                    engagement_id=engagement_id,
                    host_id=host_id,
                    title=vuln["title"],
                    finding_type="vulnerability",
                    severity=vuln.get("severity", "medium"),
                    description=vuln.get("description", ""),
                    tool="wpscan",
                    refs=", ".join(vuln.get("references", [])),
                )
                findings_added += 1

            # Plugin vulnerabilities (parser returns list of dicts)
            plugins = parsed.get("plugins", [])
            if isinstance(plugins, list):
                for plugin_data in plugins:
                    if isinstance(plugin_data, dict):
                        plugin_name = plugin_data.get("name", "Unknown")
                        for vuln in plugin_data.get("vulnerabilities", []):
                            findings_manager.add_finding(
                                engagement_id=engagement_id,
                                host_id=host_id,
                                title=f"WordPress Plugin: {plugin_name} - {vuln['title']}",
                                finding_type="vulnerability",
                                severity=vuln.get("severity", "medium"),
                                description=vuln.get("description", ""),
                                tool="wpscan",
                                refs=", ".join(vuln.get("references", [])),
                            )
                            findings_added += 1

            # Theme vulnerabilities (parser returns list of dicts)
            themes = parsed.get("themes", [])
            if isinstance(themes, list):
                for theme_data in themes:
                    if isinstance(theme_data, dict):
                        theme_name = theme_data.get("name", "Unknown")
                        for vuln in theme_data.get("vulnerabilities", []):
                            findings_manager.add_finding(
                                engagement_id=engagement_id,
                                host_id=host_id,
                                title=f"WordPress Theme: {theme_name} - {vuln['title']}",
                                finding_type="vulnerability",
                                severity=vuln.get("severity", "medium"),
                                description=vuln.get("description", ""),
                                tool="wpscan",
                                refs=", ".join(vuln.get("references", [])),
                            )
                            findings_added += 1

            # Check for wpscan errors
            wpscan_error = detect_tool_error(output, "wpscan")

            # Count WordPress info as results (version, users, plugins, themes)
            wp_version = parsed.get("version") or parsed.get("wordpress_version")
            users_list = parsed.get("users", [])
            users_found = len(users_list)
            plugins_found = len(parsed.get("plugins", []))
            themes_found = len(parsed.get("themes", []))
            has_wp_info = (
                wp_version or users_found > 0 or plugins_found > 0 or themes_found > 0
            )

            # Add enumerated users to credentials (for brute force chaining)
            credentials_added = 0
            if users_list and credentials_manager:
                for username in users_list:
                    try:
                        credentials_manager.add_credential(
                            engagement_id=engagement_id,
                            host_id=host_id,
                            service="wordpress",
                            username=username,
                            password=None,
                            status="untested",
                            tool="wpscan",
                        )
                        credentials_added += 1
                    except Exception as cred_err:
                        logger.debug(
                            f"Could not add credential for {username}: {cred_err}"
                        )

            # Determine status based on results
            if wpscan_error:
                status = STATUS_ERROR
            elif findings_added > 0 or has_wp_info:
                # CVE findings OR WordPress info = successful scan
                status = STATUS_DONE
            else:
                status = STATUS_NO_RESULTS

            return {
                "tool": "wpscan",
                "status": status,
                "target": target,
                "wp_version": parsed.get("version") or parsed.get("wordpress_version"),
                "plugins_found": len(parsed.get("plugins", {})),
                "themes_found": len(parsed.get("themes", {})),
                "users_found": len(parsed.get("users", [])),
                "findings_added": findings_added,
                "users": parsed.get("users", []),  # For hydra chaining
            }

        except Exception as e:
            logger.error(f"Error parsing wpscan job: {e}")
            return {"error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful WPScan results."""
        try:
            from souleyez.parsers.wpscan_parser import parse_wpscan_output

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            parsed = parse_wpscan_output(log_content, job.get("target", ""))

            # Check if we have any results
            has_results = (
                parsed.get("wordpress_version")
                or parsed.get("findings")
                or parsed.get("plugins")
                or parsed.get("themes")
                or parsed.get("users")
                or parsed.get("info")
            )

            if not has_results:
                self.display_no_results(job, log_path)
                return

            # Header
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo(
                click.style("WPSCAN WORDPRESS SECURITY SCAN", bold=True, fg="cyan")
            )
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

            # WordPress version with status
            if parsed.get("wordpress_version"):
                version_str = parsed["wordpress_version"]
                version_status = parsed.get("version_status")
                version_date = parsed.get("version_release_date")

                click.echo(click.style("WordPress Version: ", bold=True), nl=False)
                if version_status == "Insecure":
                    click.echo(
                        click.style(f"{version_str} (Insecure)", fg="red", bold=True),
                        nl=False,
                    )
                elif version_status == "Outdated":
                    click.echo(
                        click.style(
                            f"{version_str} (Outdated)", fg="yellow", bold=True
                        ),
                        nl=False,
                    )
                else:
                    click.echo(version_str, nl=False)

                if version_date:
                    click.echo(f" - Released {version_date}")
                else:
                    click.echo()
                click.echo()

            # Additional information/findings
            info_items = parsed.get("info", [])
            if info_items:
                click.echo(click.style("Scan Findings:", bold=True))
                for item in info_items:
                    title = item.get("title", "Unknown")
                    severity = item.get("severity", "info").lower()
                    item_type = item.get("type", "info")

                    # Icon based on severity/type
                    if severity == "low" or item_type == "warning":
                        icon = "!"
                        color = "yellow"
                    elif item_type == "config":
                        icon = "*"
                        color = "cyan"
                    elif item_type == "disclosure":
                        icon = "#"
                        color = "yellow"
                    elif item_type == "header":
                        icon = "?"
                        color = "cyan"
                    else:
                        icon = "i"
                        color = "white"

                    click.echo(click.style(f"  [{icon}] {title}", fg=color))

                click.echo()

            # Vulnerabilities/Findings
            findings = parsed.get("findings", [])
            if findings:
                # Group by severity
                severity_order = ["critical", "high", "medium", "low", "info"]
                severity_groups = {sev: [] for sev in severity_order}
                for finding in findings:
                    severity = finding.get("severity", "medium").lower()
                    if severity in severity_groups:
                        severity_groups[severity].append(finding)

                click.echo(
                    click.style(
                        f"Vulnerabilities Found: {len(findings)}", bold=True, fg="red"
                    )
                )
                click.echo()

                max_per_severity = None if show_all else 3
                for severity in severity_order:
                    if severity_groups[severity]:
                        # Color code by severity
                        if severity in ("critical", "high"):
                            color = "red"
                        elif severity == "medium":
                            color = "yellow"
                        elif severity == "low":
                            color = "green"
                        else:
                            color = "cyan"

                        click.echo(
                            click.style(
                                f"[{severity.upper()}] ({len(severity_groups[severity])})",
                                bold=True,
                                fg=color,
                            )
                        )

                        display_findings = (
                            severity_groups[severity]
                            if max_per_severity is None
                            else severity_groups[severity][:max_per_severity]
                        )
                        for finding in display_findings:
                            click.echo(
                                f"  - {finding.get('title', 'Unknown vulnerability')}"
                            )
                            if finding.get("type") and finding.get("name"):
                                click.echo(
                                    f"    Type: {finding['type']} - {finding['name']}"
                                )
                            if finding.get("fixed_in"):
                                click.echo(f"    Fixed in: {finding['fixed_in']}")
                            if finding.get("references"):
                                refs = finding["references"][
                                    :2
                                ]  # Show first 2 references
                                for ref in refs:
                                    click.echo(f"    Ref: {ref}")
                            click.echo()

                        if (
                            max_per_severity
                            and len(severity_groups[severity]) > max_per_severity
                        ):
                            click.echo(
                                f"  ... and {len(severity_groups[severity]) - max_per_severity} more {severity} severity issues"
                            )
                            click.echo()

            # Plugins
            plugins = parsed.get("plugins", [])
            if plugins:
                vulnerable_plugins = [p for p in plugins if p.get("vulnerable")]
                click.echo(click.style(f"Plugins Detected: {len(plugins)}", bold=True))
                if vulnerable_plugins:
                    click.echo(
                        click.style(
                            f"  ! {len(vulnerable_plugins)} vulnerable", fg="red"
                        )
                    )
                click.echo()

                max_plugins = None if show_all else 5
                display_plugins = (
                    plugins if max_plugins is None else plugins[:max_plugins]
                )
                for plugin in display_plugins:
                    vuln_marker = (
                        click.style("!", fg="red") if plugin.get("vulnerable") else " "
                    )
                    plugin_name = plugin.get("name", "Unknown")
                    plugin_version = plugin.get("version", "Unknown version")
                    click.echo(f"  {vuln_marker} {plugin_name} - {plugin_version}")

                if max_plugins and len(plugins) > max_plugins:
                    click.echo(f"  ... and {len(plugins) - max_plugins} more plugins")
                click.echo()

            # Themes
            themes = parsed.get("themes", [])
            if themes:
                vulnerable_themes = [t for t in themes if t.get("vulnerable")]
                click.echo(click.style(f"Themes Detected: {len(themes)}", bold=True))
                if vulnerable_themes:
                    click.echo(
                        click.style(
                            f"  ! {len(vulnerable_themes)} vulnerable", fg="red"
                        )
                    )
                click.echo()

                max_themes = None if show_all else 3
                display_themes = themes if max_themes is None else themes[:max_themes]
                for theme in display_themes:
                    vuln_marker = (
                        click.style("!", fg="red") if theme.get("vulnerable") else " "
                    )
                    theme_name = theme.get("name", "Unknown")
                    theme_version = theme.get("version", "Unknown version")
                    click.echo(f"  {vuln_marker} {theme_name} - {theme_version}")

                if max_themes and len(themes) > max_themes:
                    click.echo(f"  ... and {len(themes) - max_themes} more themes")
                click.echo()

            # Enumerated users
            users = parsed.get("users", [])
            if users:
                click.echo(
                    click.style(
                        f"Users Enumerated: {len(users)}", bold=True, fg="yellow"
                    )
                )
                max_users = None if show_all else 10
                display_users = users if max_users is None else users[:max_users]
                for user in display_users:
                    click.echo(f"  - {user}")
                if max_users and len(users) > max_users:
                    click.echo(f"  ... and {len(users) - max_users} more users")
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
        """Display warning status for WPScan."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] WPSCAN", bold=True, fg="yellow"))
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
        """Display error status for WPScan."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] WPSCAN FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common wpscan errors
        error_msg = None
        if log_content:
            if "The target is NOT running WordPress" in log_content:
                error_msg = "Target is not running WordPress"
            elif "could not resolve" in log_content.lower():
                error_msg = "Could not resolve target hostname"
            elif (
                "Connection refused" in log_content
                or "Unable to connect" in log_content
            ):
                error_msg = "Connection refused - web server may be down"
            elif "timed out" in log_content.lower() or "timeout" in log_content.lower():
                error_msg = "Connection timed out - target may be slow or filtering"
            elif "SSL" in log_content and (
                "error" in log_content.lower() or "fail" in log_content.lower()
            ):
                error_msg = "SSL error - try with --disable-tls-checks"
            elif (
                "api limit" in log_content.lower()
                or "rate limit" in log_content.lower()
            ):
                error_msg = "WPScan API rate limit reached - try again later"
            elif "[!]" in log_content:
                match = re.search(r"\[!\]\s*(.+?)(?:\n|$)", log_content)
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
        """Display no_results status for WPScan."""
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("WPSCAN WORDPRESS SECURITY SCAN", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

        if job.get("target"):
            click.echo(click.style(f"Target: {job.get('target')}", bold=True))
            click.echo()

        click.echo(
            click.style(
                "Result: No WordPress detected or no issues found",
                fg="green",
                bold=True,
            )
        )
        click.echo()
        click.echo("  The scan did not find WordPress or any security issues.")
        click.echo()
        click.echo(click.style("Tips:", dim=True))
        click.echo("  - Verify the target is a WordPress site")
        click.echo("  - Try enumeration: --enumerate ap,at,u")
        click.echo("  - Check API token for vuln database access")
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
