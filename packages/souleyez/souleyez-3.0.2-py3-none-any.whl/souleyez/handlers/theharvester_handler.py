#!/usr/bin/env python3
"""
TheHarvester handler.

Consolidates parsing and display logic for theHarvester OSINT jobs.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class TheHarvesterHandler(BaseToolHandler):
    """Handler for theHarvester OSINT jobs."""

    tool_name = "theharvester"
    display_name = "TheHarvester"

    # All handlers enabled
    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    # URL patterns for security concerns
    URL_PATTERNS = {
        "auth_endpoints": {
            "patterns": [
                r"/login",
                r"/signin",
                r"/auth",
                r"/oauth",
                r"/sso",
                r"/password",
                r"/forgot",
            ],
            "label": "Authentication endpoint",
            "severity": "medium",
        },
        "admin_panels": {
            "patterns": [
                r"/admin",
                r"/administrator",
                r"/manager",
                r"/console",
                r"/dashboard",
                r"/portal",
            ],
            "label": "Admin/management panel",
            "severity": "high",
        },
        "api_endpoints": {
            "patterns": [
                r"/api/",
                r"/api$",
                r"/graphql",
                r"/rest/",
                r"/v1/",
                r"/v2/",
                r"/swagger",
                r"/openapi",
            ],
            "label": "API endpoint",
            "severity": "medium",
        },
        "file_access": {
            "patterns": [
                r"/upload",
                r"/download",
                r"/files",
                r"/documents",
                r"/attachments",
            ],
            "label": "File access endpoint",
            "severity": "medium",
        },
        "sensitive_pages": {
            "patterns": [
                r"/config",
                r"/settings",
                r"/backup",
                r"/debug",
                r"/phpinfo",
                r"/info\.php",
                r"/test/",
            ],
            "label": "Potentially sensitive page",
            "severity": "high",
        },
    }

    # Subdomain patterns for security concerns
    SUBDOMAIN_PATTERNS = {
        "dev_staging": {
            "patterns": [
                r"^dev\.",
                r"^staging\.",
                r"^stage\.",
                r"^test\.",
                r"^qa\.",
                r"^uat\.",
                r"^sandbox\.",
                r"^demo\.",
            ],
            "label": "Development/staging environment",
            "severity": "high",
        },
        "internal": {
            "patterns": [
                r"^internal\.",
                r"^intranet\.",
                r"^private\.",
                r"^corp\.",
                r"^vpn\.",
                r"^remote\.",
            ],
            "label": "Internal/corporate system",
            "severity": "high",
        },
        "infrastructure": {
            "patterns": [
                r"^mail\.",
                r"^smtp\.",
                r"^mx\.",
                r"^ftp\.",
                r"^sftp\.",
                r"^ns\d*\.",
                r"^dns\.",
            ],
            "label": "Infrastructure service",
            "severity": "medium",
        },
        "admin_systems": {
            "patterns": [
                r"^admin\.",
                r"^manage\.",
                r"^portal\.",
                r"^panel\.",
                r"^cms\.",
                r"^backend\.",
            ],
            "label": "Administrative system",
            "severity": "high",
        },
        "database": {
            "patterns": [
                r"^db\.",
                r"^database\.",
                r"^mysql\.",
                r"^postgres\.",
                r"^mongo\.",
                r"^redis\.",
                r"^elastic\.",
            ],
            "label": "Database system exposed",
            "severity": "high",
        },
        "cloud_services": {
            "patterns": [
                r"^api\.",
                r"^cdn\.",
                r"^static\.",
                r"^assets\.",
                r"^media\.",
                r"^storage\.",
                r"^s3\.",
            ],
            "label": "Cloud/CDN service",
            "severity": "low",
        },
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
        """
        Parse theHarvester job results.

        Extracts OSINT data and stores it in the database.
        """
        try:
            from souleyez.parsers.theharvester_parser import (
                get_osint_stats,
                parse_theharvester_output,
            )

            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()

            # Read the log file
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

            # Parse theHarvester output
            target = job.get("target", "")
            parsed = parse_theharvester_output(log_content, target)

            # Store OSINT data
            from souleyez.storage.osint import OsintManager

            om = OsintManager()
            osint_added = 0

            # Add emails
            if parsed["emails"]:
                count = om.bulk_add_osint_data(
                    engagement_id, "email", parsed["emails"], "theHarvester", target
                )
                osint_added += count

            # Add hosts/subdomains
            if parsed["hosts"]:
                count = om.bulk_add_osint_data(
                    engagement_id, "host", parsed["hosts"], "theHarvester", target
                )
                osint_added += count

            # Add IPs
            if parsed["ips"]:
                count = om.bulk_add_osint_data(
                    engagement_id, "ip", parsed["ips"], "theHarvester", target
                )
                osint_added += count

            # Add URLs
            if parsed["urls"]:
                count = om.bulk_add_osint_data(
                    engagement_id, "url", parsed["urls"], "theHarvester", target
                )
                osint_added += count

            # Add ASNs
            if parsed["asns"]:
                count = om.bulk_add_osint_data(
                    engagement_id, "asn", parsed["asns"], "theHarvester", target
                )
                osint_added += count

            # Also add discovered IPs and hosts to the hosts table
            hosts_added = 0
            for ip in parsed["ips"]:
                try:
                    host_id = host_manager.add_or_update_host(
                        engagement_id, {"ip": ip, "status": "discovered"}
                    )
                    hosts_added += 1
                    logger.debug(f"Added IP {ip} to hosts table (host_id={host_id})")
                except Exception as e:
                    logger.warning(f"Failed to add IP {ip} to hosts: {e}")

            stats = get_osint_stats(parsed)

            # Determine status based on results
            total_osint_found = (
                len(parsed["emails"])
                + len(parsed["hosts"])
                + len(parsed["ips"])
                + len(parsed["urls"])
            )
            if total_osint_found > 0:
                status = STATUS_DONE
            else:
                status = STATUS_NO_RESULTS

            return {
                "tool": "theHarvester",
                "status": status,
                "osint_added": osint_added,
                "hosts_added": hosts_added,
                "stats": stats,
                "domains": [target] if target else [],
                "target": target,
                "urls": parsed["urls"],
                "ips": parsed["ips"],
            }
        except Exception as e:
            logger.error(f"Error parsing theHarvester job: {e}")
            return {"error": str(e)}

    def _identify_security_concerns(
        self, urls: List[str], subdomains: List[str]
    ) -> List[Dict]:
        """Identify security concerns in discovered URLs and subdomains."""
        security_concerns = []

        # Check URLs
        for url in urls:
            try:
                parsed_url = urlparse(url)
                url_path = parsed_url.path.lower()
                if not url_path or url_path == "/":
                    continue
            except Exception:
                continue

            for concern_type, concern_info in self.URL_PATTERNS.items():
                matched = False
                for pattern in concern_info["patterns"]:
                    if re.search(pattern, url_path, re.IGNORECASE):
                        security_concerns.append(
                            {
                                "item": url,
                                "type": concern_type,
                                "label": concern_info["label"],
                                "severity": concern_info["severity"],
                                "category": "url",
                            }
                        )
                        matched = True
                        break
                if matched:
                    break

        # Check subdomains
        for sub in subdomains:
            sub_lower = sub.lower()
            for concern_type, concern_info in self.SUBDOMAIN_PATTERNS.items():
                matched = False
                for pattern in concern_info["patterns"]:
                    if re.search(pattern, sub_lower, re.IGNORECASE):
                        security_concerns.append(
                            {
                                "item": sub,
                                "type": concern_type,
                                "label": concern_info["label"],
                                "severity": concern_info["severity"],
                                "category": "subdomain",
                            }
                        )
                        matched = True
                        break
                if matched:
                    break

        return security_concerns

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful theHarvester scan results."""
        try:
            from souleyez.parsers.theharvester_parser import parse_theharvester_output

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            parsed = parse_theharvester_output(log_content, job.get("target", ""))

            # Collect all results
            emails = parsed.get("emails", [])
            ips = parsed.get("ips", [])
            asns = parsed.get("asns", [])
            urls = parsed.get("urls", parsed.get("base_urls", []))
            subdomains = parsed.get("subdomains", [])

            has_results = emails or ips or asns or urls or subdomains

            # Run security analysis
            security_concerns = self._identify_security_concerns(urls, subdomains)

            # Display security concerns FIRST
            if security_concerns:
                self._display_security_concerns(security_concerns)

            # Display discovered assets
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo(click.style("DISCOVERED ASSETS", bold=True, fg="cyan"))
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

            click.echo(
                click.style(f"Target: {job.get('target', 'unknown')}", bold=True)
            )
            click.echo()

            if has_results:
                max_items = None if show_all else 10
                max_urls = None if show_all else 15

                # Emails
                if emails:
                    self._display_list("Emails", emails, max_items)

                # IPs
                if ips:
                    self._display_list("IP Addresses", ips, max_items)

                # ASNs
                if asns:
                    self._display_list("ASNs", asns, max_items)

                # URLs
                if urls:
                    self._display_list("Interesting URLs", urls, max_urls)

                # Subdomains
                if subdomains:
                    self._display_list("Hosts Found", subdomains, max_urls)
            else:
                self.display_no_results(job, log_path)
                return

            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

        except Exception as e:
            logger.debug(f"Error in display_done: {e}")

    def _display_list(
        self, title: str, items: List[str], max_items: Optional[int]
    ) -> None:
        """Display a list of items with optional truncation."""
        click.echo(click.style(f"{title}: {len(items)}", bold=True))
        display_items = items if max_items is None else items[:max_items]
        for item in display_items:
            click.echo(f"  - {item}")
        if max_items and len(items) > max_items:
            click.echo(f"  ... and {len(items) - max_items} more")
        click.echo()

    def _display_security_concerns(self, security_concerns: List[Dict]) -> None:
        """Display security concerns grouped by severity."""
        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("SECURITY CONCERNS", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Group by severity
        high_concerns = [c for c in security_concerns if c["severity"] == "high"]
        medium_concerns = [c for c in security_concerns if c["severity"] == "medium"]
        low_concerns = [c for c in security_concerns if c["severity"] == "low"]

        if high_concerns:
            click.echo(click.style("[HIGH] Critical findings:", fg="red", bold=True))
            by_label = {}
            for c in high_concerns:
                if c["label"] not in by_label:
                    by_label[c["label"]] = []
                by_label[c["label"]].append(c["item"])
            for label, items in by_label.items():
                click.echo(f"  {label}:")
                for item in items[:5]:
                    click.echo(f"    - {item}")
                if len(items) > 5:
                    click.echo(f"    ... and {len(items) - 5} more")
            click.echo()

        if medium_concerns:
            click.echo(
                click.style("[MEDIUM] Notable findings:", fg="yellow", bold=True)
            )
            by_label = {}
            for c in medium_concerns:
                if c["label"] not in by_label:
                    by_label[c["label"]] = []
                by_label[c["label"]].append(c["item"])
            for label, items in by_label.items():
                click.echo(f"  {label}:")
                for item in items[:5]:
                    click.echo(f"    - {item}")
                if len(items) > 5:
                    click.echo(f"    ... and {len(items) - 5} more")
            click.echo()

        if low_concerns:
            click.echo(
                click.style("[LOW] Informational:", fg="bright_black", bold=True)
            )
            by_label = {}
            for c in low_concerns:
                if c["label"] not in by_label:
                    by_label[c["label"]] = []
                by_label[c["label"]].append(c["item"])
            for label, items in by_label.items():
                click.echo(f"  {label}:")
                for item in items[:3]:
                    click.echo(f"    - {item}")
                if len(items) > 3:
                    click.echo(f"    ... and {len(items) - 3} more")
            click.echo()

        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display warning status for theHarvester scan."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] THEHARVESTER SCAN", bold=True, fg="yellow"))
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
        """Display error status for theHarvester scan."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] THEHARVESTER FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common theharvester errors
        error_msg = None
        if log_content:
            if "No results found" in log_content:
                error_msg = "No results found for the specified domain"
            elif "Could not resolve" in log_content or (
                "DNS" in log_content and "fail" in log_content.lower()
            ):
                error_msg = "Could not resolve domain"
            elif "timed out" in log_content.lower() or "timeout" in log_content.lower():
                error_msg = "Connection timed out - source may be slow"
            elif (
                "rate limit" in log_content.lower() or "blocked" in log_content.lower()
            ):
                error_msg = "Rate limited or blocked by source"
            elif "API" in log_content and (
                "key" in log_content.lower() or "error" in log_content.lower()
            ):
                error_msg = "API key error - check your API keys configuration"
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
        """Display no_results status for theHarvester scan."""
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("DISCOVERED ASSETS", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

        click.echo(click.style(f"Target: {job.get('target', 'unknown')}", bold=True))
        click.echo()
        click.echo(click.style("Result: No assets discovered", fg="yellow", bold=True))
        click.echo()
        click.echo("  The scan completed without finding any publicly exposed assets.")
        click.echo()
        click.echo(click.style("Tips:", dim=True))
        click.echo("  - Try different data sources (-b google,bing,linkedin)")
        click.echo("  - Check if the domain is correct")
        click.echo("  - Some organizations have minimal public exposure")
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
