#!/usr/bin/env python3
"""
DNSRecon handler.

Consolidates parsing and display logic for DNSRecon DNS enumeration jobs.
"""

import logging
import os
import re
from typing import Any, Dict, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_ERROR, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class DNSReconHandler(BaseToolHandler):
    """Handler for DNSRecon DNS enumeration jobs."""

    tool_name = "dnsrecon"
    display_name = "DNSRecon"

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
        Parse DNSRecon job results.

        Extracts DNS records and stores them as OSINT data.
        """
        try:
            from souleyez.engine.result_handler import detect_tool_error
            from souleyez.parsers.dnsrecon_parser import parse_dnsrecon_output
            from souleyez.storage.osint import OsintManager

            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()

            target = job.get("target", "")

            # Read log file
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                output = f.read()

            parsed = parse_dnsrecon_output(output, target)

            # Store OSINT data
            om = OsintManager()
            osint_added = 0

            # Add nameservers
            if parsed.get("nameservers"):
                count = om.bulk_add_osint_data(
                    engagement_id,
                    "nameserver",
                    parsed["nameservers"],
                    "dnsrecon",
                    target,
                )
                osint_added += count

            # Add mail servers
            if parsed.get("mail_servers"):
                count = om.bulk_add_osint_data(
                    engagement_id,
                    "mail_server",
                    parsed["mail_servers"],
                    "dnsrecon",
                    target,
                )
                osint_added += count

            # Add TXT records
            if parsed.get("txt_records"):
                # Limit TXT record length
                txt_records = [txt[:500] for txt in parsed["txt_records"]]
                count = om.bulk_add_osint_data(
                    engagement_id, "txt_record", txt_records, "dnsrecon", target
                )
                osint_added += count

            # Add subdomains/hosts
            if parsed.get("subdomains"):
                count = om.bulk_add_osint_data(
                    engagement_id, "host", parsed["subdomains"], "dnsrecon", target
                )
                osint_added += count

            # Also add discovered hosts to the hosts table
            hosts_added = 0
            for host_data in parsed.get("hosts", []):
                try:
                    hostname = host_data.get("hostname", "")
                    ip = host_data.get("ip", "")

                    if ip and hostname:
                        host_manager.add_or_update_host(
                            engagement_id,
                            {
                                "ip": ip,
                                "hostname": hostname,
                                "status": "up",
                                "notes": f"Discovered by dnsrecon for domain: {target}",
                            },
                        )
                        hosts_added += 1
                except Exception:
                    pass  # Skip if invalid

            # Check for dnsrecon errors
            dnsrecon_error = detect_tool_error(output, "dnsrecon")

            # Determine status
            if dnsrecon_error:
                status = STATUS_ERROR
            elif osint_added > 0 or hosts_added > 0:
                status = STATUS_DONE
            else:
                status = STATUS_NO_RESULTS

            return {
                "tool": "dnsrecon",
                "status": status,
                "domain": parsed.get("target_domain", target),
                "hosts_found": len(parsed.get("hosts", [])),
                "nameservers": len(parsed.get("nameservers", [])),
                "mail_servers": len(parsed.get("mail_servers", [])),
                "txt_records": len(parsed.get("txt_records", [])),
                "subdomains": len(parsed.get("subdomains", [])),
                "osint_records_added": osint_added,
                "hosts_added": hosts_added,
            }

        except Exception as e:
            logger.error(f"Error parsing dnsrecon job: {e}")
            return {"error": str(e)}

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful DNSRecon results."""
        try:
            from souleyez.parsers.dnsrecon_parser import parse_dnsrecon_output

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            parsed = parse_dnsrecon_output(log_content, job.get("target", ""))

            # Collect all results
            hosts = parsed.get("hosts", [])
            ns = parsed.get("nameservers", [])
            mx = parsed.get("mail_servers", [])
            txt = parsed.get("txt_records", [])
            subdomains = parsed.get("subdomains", [])

            has_results = hosts or ns or mx or txt or subdomains

            if not has_results:
                self.display_no_results(job, log_path)
                return

            # Header
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo(click.style("DISCOVERED DNS RECORDS", bold=True, fg="cyan"))
            click.echo(click.style("=" * 70, fg="cyan"))
            click.echo()

            click.echo(
                click.style(f"Target: {job.get('target', 'unknown')}", bold=True)
            )
            click.echo()

            # Hosts (A records)
            if hosts:
                click.echo(click.style(f"Hosts (A Records): {len(hosts)}", bold=True))
                max_hosts = None if show_all else 20
                display_hosts = hosts if max_hosts is None else hosts[:max_hosts]
                for host in display_hosts:
                    click.echo(f"  - {host['hostname']} -> {host['ip']}")
                if max_hosts and len(hosts) > max_hosts:
                    click.echo(f"  ... and {len(hosts) - max_hosts} more")
                click.echo()

            # Nameservers
            if ns:
                click.echo(click.style(f"Nameservers (NS): {len(ns)}", bold=True))
                for server in ns:
                    click.echo(f"  - {server}")
                click.echo()

            # Mail servers
            if mx:
                click.echo(click.style(f"Mail Servers (MX): {len(mx)}", bold=True))
                max_mx = None if show_all else 5
                display_mx = mx if max_mx is None else mx[:max_mx]
                for server in display_mx:
                    click.echo(f"  - {server}")
                if max_mx and len(mx) > max_mx:
                    click.echo(f"  ... and {len(mx) - max_mx} more")
                click.echo()

            # TXT records
            if txt:
                click.echo(click.style(f"TXT Records: {len(txt)}", bold=True))
                for record in txt:
                    # Truncate long records
                    display = record[:80] + "..." if len(record) > 80 else record
                    click.echo(f"  - {display}")
                click.echo()

            # Subdomains
            if subdomains:
                click.echo(click.style(f"Subdomains: {len(subdomains)}", bold=True))
                max_subs = None if show_all else 10
                display_subs = subdomains if max_subs is None else subdomains[:max_subs]
                for sub in display_subs:
                    click.echo(f"  - {sub}")
                if max_subs and len(subdomains) > max_subs:
                    click.echo(f"  ... and {len(subdomains) - max_subs} more")
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
        """Display warning status for DNSRecon."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] DNSRECON", bold=True, fg="yellow"))
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
        """Display error status for DNSRecon."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] DNSRECON FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common dnsrecon errors
        error_msg = None
        if log_content:
            if "Could not resolve" in log_content or "NXDOMAIN" in log_content:
                error_msg = "Could not resolve domain - check if domain exists"
            elif "timed out" in log_content.lower() or "timeout" in log_content.lower():
                error_msg = "DNS query timed out - DNS server may be slow"
            elif "SERVFAIL" in log_content:
                error_msg = "DNS server failure (SERVFAIL)"
            elif "REFUSED" in log_content:
                error_msg = "DNS query refused - server may be blocking queries"
            elif "No DNS records" in log_content:
                error_msg = "No DNS records found for domain"
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
        """Display no_results status for DNSRecon."""
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("DISCOVERED DNS RECORDS", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

        if job.get("target"):
            click.echo(click.style(f"Target: {job.get('target')}", bold=True))
            click.echo()

        click.echo(
            click.style("Result: No DNS records discovered", fg="yellow", bold=True)
        )
        click.echo()
        click.echo("  The scan did not find any DNS records.")
        click.echo()
        click.echo(click.style("Tips:", dim=True))
        click.echo("  - Verify the domain name is correct")
        click.echo("  - Try zone transfer: -a -t axfr")
        click.echo("  - Check if domain has public DNS records")
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
