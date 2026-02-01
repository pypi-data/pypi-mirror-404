#!/usr/bin/env python3
"""
Nmap handler.

Consolidates parsing and display logic for nmap and ARD (which uses nmap) jobs.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

import click

from souleyez.engine.job_status import STATUS_DONE, STATUS_ERROR, STATUS_NO_RESULTS
from souleyez.handlers.base import BaseToolHandler

logger = logging.getLogger(__name__)


class NmapHandler(BaseToolHandler):
    """Handler for nmap and nmap-based (ARD) jobs."""

    tool_name = "nmap"
    display_name = "Nmap"

    # All handlers enabled
    has_error_handler = True
    has_warning_handler = True
    has_no_results_handler = True
    has_done_handler = True

    # Risky ports that warrant security concerns
    RISKY_PORTS = {
        21: ("FTP", "Cleartext file transfer - check for anonymous access"),
        23: ("Telnet", "Cleartext remote access - highly insecure"),
        25: ("SMTP", "Mail relay - check for open relay"),
        69: ("TFTP", "Trivial FTP - no authentication"),
        111: ("RPC", "Remote procedure call - can expose NFS/services"),
        135: ("MSRPC", "Windows RPC - often targeted"),
        139: ("NetBIOS", "Legacy Windows networking"),
        445: ("SMB", "File sharing - frequent attack target"),
        512: ("rexec", "Remote execution - cleartext"),
        513: ("rlogin", "Remote login - cleartext, no auth"),
        514: ("rsh", "Remote shell - cleartext, no auth"),
        1433: ("MSSQL", "Database exposed - should not be public"),
        1521: ("Oracle", "Database exposed - should not be public"),
        2049: ("NFS", "Network file system - check exports"),
        3306: ("MySQL", "Database exposed - should not be public"),
        3389: ("RDP", "Remote desktop - brute forceable"),
        5432: ("PostgreSQL", "Database exposed - should not be public"),
        5900: ("VNC", "Remote desktop - often weak auth"),
        5901: ("VNC", "Remote desktop - often weak auth"),
        6000: ("X11", "Remote display - unencrypted"),
        6379: ("Redis", "Database/cache - often no auth"),
        27017: ("MongoDB", "Database exposed - often no auth"),
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
        Parse nmap job results.

        Imports hosts/services into database and creates findings for CVEs.
        """
        try:
            from souleyez.core.cve_matcher import CVEMatcher
            from souleyez.engine.result_handler import detect_tool_error
            from souleyez.parsers.nmap_parser import parse_nmap_log

            # Import managers if not provided
            if host_manager is None:
                from souleyez.storage.hosts import HostManager

                host_manager = HostManager()
            if findings_manager is None:
                from souleyez.storage.findings import FindingsManager

                findings_manager = FindingsManager()

            # Parse the log file
            parsed = parse_nmap_log(log_path)

            if "error" in parsed:
                return {"error": parsed["error"]}

            # Import into database
            result = host_manager.import_nmap_results(engagement_id, parsed)
            logger.info(
                f"Nmap import: {result['hosts_added']} hosts, "
                f"{result['services_added']} services in engagement {engagement_id}"
            )
            logger.debug(
                f"Info scripts to process: {len(parsed.get('info_scripts', []))}"
            )

            # Check for CVEs and common issues
            cve_matcher = CVEMatcher()
            findings_added = 0

            # First, store any script-detected vulnerabilities (from --script vuln)
            findings_added += self._store_vulnerabilities(
                parsed, engagement_id, host_manager, findings_manager
            )

            # Then check for inferred CVEs based on service versions
            findings_added += self._check_service_cves(
                parsed, engagement_id, host_manager, findings_manager, cve_matcher
            )

            # Store info script findings
            findings_added += self._store_info_scripts(
                parsed, engagement_id, host_manager, findings_manager
            )

            # Build host details list for summary
            host_details = self._build_host_details(parsed)

            # Determine scan type based on job args
            args = job.get("args", [])
            is_discovery = "-sn" in args or "--discovery" in args
            is_full_scan = any(x in args for x in ["-sV", "-O", "-A", "-p1-65535"])

            # Collect all services for tool chaining
            all_services = self._collect_chainable_services(parsed)

            # Check for nmap errors before determining status
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            nmap_error = detect_tool_error(log_content, "nmap")

            # Determine status based on results
            hosts_up = len(
                [h for h in parsed.get("hosts", []) if h.get("status") == "up"]
            )
            if nmap_error:
                status = STATUS_ERROR
            elif hosts_up > 0:
                status = STATUS_DONE
            else:
                status = STATUS_NO_RESULTS

            # Build summary for job queue display
            summary_parts = []
            if hosts_up > 0:
                summary_parts.append(f"{hosts_up} host(s) up")
            if result["services_added"] > 0:
                summary_parts.append(f"{result['services_added']} service(s)")
            if findings_added > 0:
                summary_parts.append(f"{findings_added} finding(s)")
            summary = " | ".join(summary_parts) if summary_parts else "No hosts found"

            return {
                "tool": "nmap",
                "status": status,
                "summary": summary,
                "hosts_added": result["hosts_added"],
                "services_added": result["services_added"],
                "findings_added": findings_added,
                "host_details": host_details,
                "is_discovery": is_discovery,
                "is_full_scan": is_full_scan,
                "services": all_services,
                "hosts": parsed.get("hosts", []),
                "domains": parsed.get(
                    "domains", []
                ),  # AD domains from LDAP/SMB banners
            }

        except Exception as e:
            logger.error(f"Error parsing nmap job: {e}")
            return {"error": str(e)}

    def _store_vulnerabilities(
        self, parsed: Dict, engagement_id: int, host_manager: Any, findings_manager: Any
    ) -> int:
        """Store script-detected vulnerabilities (from --script vuln)."""
        findings_added = 0

        for vuln in parsed.get("vulnerabilities", []):
            host_ip = vuln.get("host_ip")
            if not host_ip:
                continue

            host = host_manager.get_host_by_ip(engagement_id, host_ip)
            if not host:
                continue

            host_id = host["id"]

            # Determine severity from CVSS score
            cvss = vuln.get("cvss_score")
            if cvss:
                if cvss >= 9.0:
                    severity = "critical"
                elif cvss >= 7.0:
                    severity = "high"
                elif cvss >= 4.0:
                    severity = "medium"
                else:
                    severity = "low"
            else:
                severity = "high" if vuln.get("state") == "VULNERABLE" else "medium"

            # Build references string from CVE IDs
            cve_ids = vuln.get("cve_ids", [])
            refs = None
            if cve_ids:
                cve_refs = [
                    f"https://nvd.nist.gov/vuln/detail/{cve}" for cve in cve_ids[:3]
                ]
                refs = ", ".join(cve_refs)
            elif vuln.get("references"):
                refs = ", ".join(vuln.get("references", [])[:3])

            # Build description with CVSS and CVE info
            description = vuln.get(
                "description", f"Detected by nmap script: {vuln.get('script')}"
            )
            if cvss:
                description += f"\n\nCVSS Score: {cvss}"
            if cve_ids:
                description += f"\nCVE IDs: {', '.join(cve_ids[:5])}"

            # Build title - include CVE if available
            title = vuln.get("title", vuln.get("script", "Unknown Vulnerability"))
            if cve_ids and cve_ids[0] not in title:
                title = f"{cve_ids[0]}: {title}"

            findings_manager.add_finding(
                engagement_id=engagement_id,
                host_id=host_id,
                title=title,
                finding_type="vulnerability",
                severity=severity,
                description=description,
                port=vuln.get("port"),
                tool="nmap",
                refs=refs,
                evidence=f"Host: {vuln.get('host_ip', 'unknown')}:{vuln.get('port', 'N/A')}\nScript: {vuln.get('script', 'nmap')}",
            )
            findings_added += 1

        return findings_added

    def _check_service_cves(
        self,
        parsed: Dict,
        engagement_id: int,
        host_manager: Any,
        findings_manager: Any,
        cve_matcher: Any,
    ) -> int:
        """Check for inferred CVEs based on service versions."""
        findings_added = 0

        for host_data in parsed.get("hosts", []):
            if host_data.get("status") != "up":
                continue

            host = host_manager.get_host_by_ip(engagement_id, host_data.get("ip"))
            if not host:
                continue

            host_id = host["id"]

            for svc in host_data.get("services", []):
                service_info = {
                    "service_name": svc.get("service") or "",
                    "version": svc.get("version") or "",
                    "port": svc.get("port"),
                    "protocol": svc.get("protocol") or "tcp",
                }

                # Also check database for stored version if not in parsed data
                if not service_info["version"]:
                    services = host_manager.get_host_services(host_id)
                    for stored_svc in services:
                        if stored_svc["port"] == svc.get("port"):
                            service_info["version"] = stored_svc.get(
                                "service_version", ""
                            )
                            break

                # Check for CVEs
                cve_findings = cve_matcher.parse_nmap_service(service_info)
                for finding in cve_findings:
                    findings_manager.add_finding(
                        engagement_id=engagement_id,
                        host_id=host_id,
                        title=finding["title"],
                        finding_type="vulnerability",
                        severity=finding["severity"],
                        description=finding["description"],
                        port=finding.get("port"),
                        tool="nmap",
                        refs=f"https://nvd.nist.gov/vuln/detail/{finding.get('cve_id')}",
                    )
                    findings_added += 1

                # Check for common issues
                issue_findings = cve_matcher.scan_for_common_issues(service_info)
                for finding in issue_findings:
                    findings_manager.add_finding(
                        engagement_id=engagement_id,
                        host_id=host_id,
                        title=finding["title"],
                        finding_type="misconfiguration",
                        severity=finding["severity"],
                        description=finding["description"],
                        port=finding.get("port"),
                        tool="nmap",
                    )
                    findings_added += 1

        return findings_added

    def _store_info_scripts(
        self, parsed: Dict, engagement_id: int, host_manager: Any, findings_manager: Any
    ) -> int:
        """Store info script findings (vnc-info, ssh-hostkey, etc.)."""
        findings_added = 0

        for info in parsed.get("info_scripts", []):
            host_ip = info.get("host_ip")
            if not host_ip:
                logger.warning(f"Info script missing host_ip: {info.get('script')}")
                continue

            host = host_manager.get_host_by_ip(engagement_id, host_ip)
            if not host:
                logger.warning(
                    f"Host not found for info script: {host_ip} in engagement {engagement_id}"
                )
                continue

            host_id = host["id"]

            script_name = info.get("script", "unknown")
            title = info.get("title", script_name)
            description = info.get("description", "")

            port = info.get("port")
            if port:
                title = f"{title} (port {port})"

            findings_manager.add_finding(
                engagement_id=engagement_id,
                host_id=host_id,
                title=title,
                finding_type="info",
                severity="info",
                description=description,
                port=port,
                tool="nmap",
                evidence=f"Host: {host_ip}:{port if port else 'N/A'}\nScript: {script_name}",
            )
            findings_added += 1

        return findings_added

    def _build_host_details(self, parsed: Dict) -> List[Dict]:
        """Build host details list for summary."""
        host_details = []

        for host_data in parsed.get("hosts", []):
            if host_data.get("status") == "up":
                services = host_data.get("services", [])
                service_count = len(services)

                # Get top ports for detailed scans
                top_ports = []
                for svc in services[:5]:
                    port = svc.get("port")
                    service_name = svc.get("service", "unknown")
                    top_ports.append(f"{port}/{service_name}")

                host_details.append(
                    {
                        "ip": host_data.get("ip"),
                        "hostname": host_data.get("hostname"),
                        "os": host_data.get("os"),
                        "service_count": service_count,
                        "top_ports": top_ports,
                    }
                )

        return host_details

    def _collect_chainable_services(self, parsed: Dict) -> List[Dict]:
        """Collect all services for tool chaining."""
        chainable_states = {"open", "filtered", "open|filtered"}
        all_services = []

        for host_data in parsed.get("hosts", []):
            if host_data.get("status") == "up":
                for svc in host_data.get("services", []):
                    port_state = svc.get("state", "open").lower()
                    if port_state in chainable_states:
                        all_services.append(
                            {
                                "ip": host_data.get("ip"),
                                "port": svc.get("port"),
                                "protocol": svc.get("protocol", "tcp"),
                                "state": port_state,
                                "service_name": svc.get("service") or "",
                                "version": svc.get("version") or "",
                            }
                        )

        return all_services

    def _identify_security_concerns(self, hosts: List[Dict]) -> List[Dict]:
        """Identify risky services in discovered hosts."""
        security_concerns = []

        for host in hosts:
            ip = host.get("ip", "unknown")
            hostname = host.get("hostname", "")

            for svc in host.get("services", []):
                port = svc.get("port")
                state = svc.get("state") or ""
                service_name = svc.get("service") or ""

                if state != "open":
                    continue

                try:
                    port_num = int(port)
                    if port_num in self.RISKY_PORTS:
                        name, desc = self.RISKY_PORTS[port_num]
                        host_display = f"{ip}:{port}"
                        if hostname:
                            host_display += f" ({hostname})"
                        security_concerns.append(
                            {
                                "host": host_display,
                                "port": port_num,
                                "service": name,
                                "description": desc,
                            }
                        )
                    elif "vnc" in service_name.lower():
                        host_display = f"{ip}:{port}"
                        security_concerns.append(
                            {
                                "host": host_display,
                                "port": port_num,
                                "service": "VNC",
                                "description": "Remote desktop - often weak auth",
                            }
                        )
                except (ValueError, TypeError):
                    pass

        return security_concerns

    def display_done(
        self,
        job: Dict[str, Any],
        log_path: str,
        show_all: bool = False,
        show_passwords: bool = False,
    ) -> None:
        """Display successful nmap scan results."""
        try:
            from souleyez.parsers.nmap_parser import parse_nmap_output

            if not log_path or not os.path.exists(log_path):
                return

            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
            parsed = parse_nmap_output(log_content, job.get("target", ""))

            vulnerabilities = parsed.get("vulnerabilities", [])
            hosts = parsed.get("hosts", [])

            # If vulnerabilities found, show vuln-focused view
            if vulnerabilities:
                self._display_vulnerabilities(vulnerabilities, show_all)
            elif hosts:
                self._display_services(hosts, show_all)
            else:
                self.display_no_results(job, log_path)

        except Exception as e:
            logger.debug(f"Error in display_done: {e}")

    def _display_vulnerabilities(
        self, vulnerabilities: List[Dict], show_all: bool
    ) -> None:
        """Display vulnerability-focused view."""
        # Group by severity
        by_severity = {"critical": [], "high": [], "medium": [], "low": []}
        for vuln in vulnerabilities:
            cvss = vuln.get("cvss_score")
            if cvss and cvss >= 9.0:
                sev = "critical"
            elif cvss and cvss >= 7.0:
                sev = "high"
            elif cvss and cvss >= 4.0:
                sev = "medium"
            elif vuln.get("state") == "VULNERABLE":
                sev = "high"
            else:
                sev = "medium"
            by_severity[sev].append(vuln)

        # Count unique hosts scanned
        unique_hosts = set(
            v.get("host_ip") for v in vulnerabilities if v.get("host_ip")
        )

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("VULNERABILITY SCAN RESULTS", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Summary line
        crit_count = len(by_severity["critical"])
        high_count = len(by_severity["high"])
        med_count = len(by_severity["medium"])
        low_count = len(by_severity["low"])

        summary_parts = []
        if crit_count:
            summary_parts.append(
                click.style(f"CRITICAL: {crit_count}", fg="red", bold=True)
            )
        if high_count:
            summary_parts.append(click.style(f"HIGH: {high_count}", fg="red"))
        if med_count:
            summary_parts.append(click.style(f"MEDIUM: {med_count}", fg="yellow"))
        if low_count:
            summary_parts.append(click.style(f"LOW: {low_count}", fg="blue"))

        click.echo(
            f"  Hosts Scanned: {len(unique_hosts)}    Total Findings: {len(vulnerabilities)}"
        )
        click.echo(f"  {' | '.join(summary_parts)}")
        click.echo()

        # Display each severity section with interactive pagination
        items_per_page = 15
        done_viewing = False

        for severity in ["critical", "high", "medium", "low"]:
            if done_viewing:
                break

            items = by_severity[severity]
            if not items:
                continue

            # Section header with color
            if severity == "critical":
                header = click.style(
                    f"-- CRITICAL ({len(items)}) ", fg="red", bold=True
                )
            elif severity == "high":
                header = click.style(f"-- HIGH ({len(items)}) ", fg="red")
            elif severity == "medium":
                header = click.style(f"-- MEDIUM ({len(items)}) ", fg="yellow")
            else:
                header = click.style(f"-- LOW ({len(items)}) ", fg="blue")

            click.echo(header + click.style("-" * 50, dim=True))

            # Paginate through items
            current_idx = 0
            while current_idx < len(items):
                end_idx = min(current_idx + items_per_page, len(items))
                for vuln in items[current_idx:end_idx]:
                    title = vuln.get("title", vuln.get("script", "Unknown"))
                    host_ip = vuln.get("host_ip", "")
                    port = vuln.get("port", "")

                    location = f"{host_ip}:{port}" if port else host_ip
                    click.echo(f"    {location:<18} {title[:55]}")

                current_idx = end_idx
                remaining = len(items) - current_idx

                if remaining > 0 and not show_all:
                    try:
                        prompt_text = click.style(
                            f"    ({current_idx}/{len(items)}) [Enter]=more  [s]=skip  [d]=done: ",
                            dim=True,
                        )
                        choice = (
                            click.prompt(prompt_text, default="", show_default=False)
                            .lower()
                            .strip()
                        )

                        if choice == "d":
                            done_viewing = True
                            break
                        elif choice == "s":
                            click.echo(
                                click.style(
                                    f"    ... {remaining} more not shown", dim=True
                                )
                            )
                            break
                    except (KeyboardInterrupt, EOFError):
                        done_viewing = True
                        break

            click.echo()

        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

    def _display_services(self, hosts: List[Dict], show_all: bool) -> None:
        """Display discovered services view."""
        has_services = any(host.get("services", []) for host in hosts)

        # Security Concerns Analysis
        security_concerns = self._identify_security_concerns(hosts)

        # Display security concerns section if any found
        if security_concerns:
            click.echo(click.style("=" * 70, fg="yellow"))
            click.echo(click.style("SECURITY CONCERNS", bold=True, fg="yellow"))
            click.echo(click.style("=" * 70, fg="yellow"))
            click.echo()

            # Group by service type
            by_service = {}
            for concern in security_concerns:
                svc = concern["service"]
                if svc not in by_service:
                    by_service[svc] = []
                by_service[svc].append(concern)

            for service, concerns in sorted(by_service.items()):
                click.echo(
                    click.style(f"  {service}", bold=True, fg="yellow")
                    + click.style(f" - {concerns[0]['description']}", fg="bright_black")
                )
                for c in concerns:
                    click.echo(f"    - {c['host']}")
                click.echo()

            click.echo(click.style("=" * 70, fg="yellow"))
            click.echo()

        click.echo(click.style("=" * 70, fg="cyan"))
        if has_services:
            click.echo(click.style("DISCOVERED SERVICES", bold=True, fg="cyan"))
        else:
            click.echo(click.style("DISCOVERED HOSTS", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

        for host in hosts:
            ip = host.get("ip", "unknown")
            hostname = host.get("hostname")
            status = host.get("status", "unknown")
            services = host.get("services", [])

            if services:
                # Show host header
                click.echo(click.style(f"Host: {ip}", bold=True))
                if hostname:
                    click.echo(f"  Hostname: {hostname}")
                # Show each service
                for svc in services:
                    port = svc.get("port", "?")
                    protocol = svc.get("protocol", "tcp")
                    state = svc.get("state", "unknown")
                    service = svc.get("service", "unknown")
                    version = svc.get("version", "")

                    state_color = (
                        "green"
                        if state == "open"
                        else ("yellow" if state == "filtered" else None)
                    )
                    state_display = (
                        click.style(state, fg=state_color) if state_color else state
                    )
                    version_str = f" ({version})" if version else ""
                    click.echo(
                        f"  {port}/{protocol}  {state_display}  {service}{version_str}"
                    )
                click.echo()
            elif status == "up":
                host_display = f"  {ip}"
                if hostname:
                    host_display += f" ({hostname})"
                click.echo(host_display)

        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()

    def display_warning(
        self,
        job: Dict[str, Any],
        log_path: str,
        log_content: Optional[str] = None,
    ) -> None:
        """Display warning status for nmap scan."""
        click.echo(click.style("=" * 70, fg="yellow"))
        click.echo(click.style("[WARNING] NMAP SCAN", bold=True, fg="yellow"))
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
        """Display error status for nmap scan."""
        # Read log if not provided
        if log_content is None and log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            except Exception:
                log_content = ""

        click.echo(click.style("=" * 70, fg="red"))
        click.echo(click.style("[ERROR] NMAP SCAN FAILED", bold=True, fg="red"))
        click.echo(click.style("=" * 70, fg="red"))
        click.echo()

        # Check for common nmap errors
        error_msg = None
        if log_content:
            if "Failed to resolve" in log_content or "Failed to open" in log_content:
                error_msg = "Failed to resolve target hostname"
            elif "No targets were specified" in log_content:
                error_msg = "No valid targets specified"
            elif (
                "requires root privileges" in log_content
                or "Operation not permitted" in log_content
            ):
                error_msg = "Scan type requires root privileges (try sudo)"
            elif "Host seems down" in log_content:
                error_msg = "Host appears to be down or blocking probes"
            elif "timed out" in log_content.lower() or "timeout" in log_content.lower():
                error_msg = "Scan timed out - target may be slow or filtering"
            elif "Connection refused" in log_content:
                error_msg = "Connection refused - no services on target ports"

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
        """Display no_results status for nmap scan."""
        # Try to read log for additional context
        log_text = ""
        if log_path and os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    log_text = f.read()
            except Exception:
                pass

        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("NMAP SCAN RESULTS", bold=True, fg="cyan"))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
        click.echo("  No open ports or services discovered.")
        click.echo()

        # Check for additional context
        if "Host seems down" in log_text:
            click.echo(
                click.style(
                    "  Note: Host appears to be down or blocking probes", fg="yellow"
                )
            )
        elif "filtered" in log_text.lower():
            click.echo(
                click.style("  Note: Ports may be filtered by firewall", fg="yellow")
            )

        click.echo()
        click.echo(click.style("  This could mean:", fg="bright_black"))
        click.echo(
            click.style("    - All ports are closed or filtered", fg="bright_black")
        )
        click.echo(click.style("    - Host is behind a firewall", fg="bright_black"))
        click.echo(
            click.style(
                "    - Try different scan types (-sS, -sT, -sU)", fg="bright_black"
            )
        )
        click.echo(
            click.style("    - Try scanning more ports (-p-)", fg="bright_black")
        )
        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
