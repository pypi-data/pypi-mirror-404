#!/usr/bin/env python3
"""
Correlation view UI for displaying attack correlation and gaps.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from souleyez.intelligence.correlation_analyzer import CorrelationAnalyzer
from souleyez.intelligence.gap_detector import GapDetector
from souleyez.storage.engagements import EngagementManager
from souleyez.ui.design_system import DesignSystem


def show_correlation_view(engagement_id: int):
    """Display correlation analysis for engagement."""
    console = Console()
    analyzer = CorrelationAnalyzer()
    detector = GapDetector()

    while True:
        DesignSystem.clear_screen()

        # Header
        width = DesignSystem.get_terminal_width()
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " ATTACK CORRELATION & GAP ANALYSIS ".center(width - 2),
                bold=True,
                fg="cyan",
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Run analysis
        try:
            analysis = analyzer.analyze_engagement(engagement_id)
        except Exception as e:
            import traceback

            click.echo(click.style(f"Error analyzing engagement: {e}", fg="red"))
            click.echo()
            click.echo(click.style("Full traceback:", fg="yellow"))
            click.echo(traceback.format_exc())
            click.pause()
            return

        summary = analysis["summary"]

        # Exploitation Summary
        console.print("[bold cyan]📊 EXPLOITATION SUMMARY[/bold cyan]")
        console.print(f"  ├─ Total Services: {summary['total_services']}")

        # Calculate percentages
        total = summary["total_services"]
        if total > 0:
            exploited_pct = int((summary["exploited_services"] / total) * 100)
            attempted_pct = int((summary["attempted_services"] / total) * 100)
            not_attempted_pct = int((summary["not_attempted_services"] / total) * 100)
        else:
            exploited_pct = attempted_pct = not_attempted_pct = 0

        console.print(
            f"  ├─ [green]✅ Exploited: {summary['exploited_services']} ({exploited_pct}%)[/green]"
        )
        console.print(
            f"  ├─ [yellow]🔄 Attempted: {summary['attempted_services']} ({attempted_pct}%)[/yellow]"
        )
        console.print(
            f"  └─ [red]⚠️  Not Attempted: {summary['not_attempted_services']} ({not_attempted_pct}%)[/red]"
        )
        console.print()

        # Compromised Hosts
        if summary["compromised_hosts"] > 0:
            console.print("[bold green]🎯 COMPROMISED HOSTS[/bold green]")

            for host_analysis in analysis["hosts"]:
                host_summary = host_analysis["summary"]
                if host_summary["access_level"] != "none":
                    host = host_analysis["host"]
                    access_emoji = {"user": "👤", "root": "👑", "admin": "🔑"}.get(
                        host_summary["access_level"], "❓"
                    )

                    console.print(
                        f"  ├─ {access_emoji} {host['ip_address']} [{host_summary['access_level'].upper()} ACCESS] - {host_summary['exploited']} services exploited"
                    )

            console.print()

        # Exploitation Gaps
        gaps = analysis["gaps"]

        if gaps:
            # Prioritize gaps
            prioritized_gaps = detector.prioritize_gaps(gaps)

            gap_summary = detector.get_gap_summary(engagement_id)

            console.print(
                f"[bold yellow]⚠️  EXPLOITATION GAPS ({len(gaps)} total)[/bold yellow]"
            )
            console.print(f"  ├─ 🔴 Critical: {gap_summary['by_severity']['critical']}")
            console.print(f"  ├─ 🟠 High: {gap_summary['by_severity']['high']}")
            console.print(f"  ├─ 🟡 Medium: {gap_summary['by_severity']['medium']}")
            console.print(f"  └─ ⚪ Low: {gap_summary['by_severity']['low']}")
            console.print()

            # Show top 5 gaps
            console.print("[bold]🎯 TOP PRIORITY GAPS:[/bold]")

            for idx, gap in enumerate(prioritized_gaps[:5], 1):
                severity_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "⚪",
                }.get(gap["severity"], "⚪")

                service_display = gap["service"]
                if gap.get("version"):
                    service_display += f" ({gap['version']})"

                console.print(
                    f"\n  {severity_emoji} [bold]#{idx} {gap['host']}:{gap['port']}[/bold] ({service_display})"
                )
                console.print(f"     Priority Score: {gap['priority_score']}/100")
                console.print(f"     Reason: {gap['reason']}")

                # Show top 2 suggested actions
                if gap.get("suggested_actions"):
                    console.print("     💡 Suggested:")
                    for action in gap["suggested_actions"][:2]:
                        console.print(f"        • {action}")
        else:
            console.print(
                "[bold green]✅ NO GAPS - All discovered services have been attempted![/bold green]"
            )
            console.print()

        # Credentials Summary
        if summary["total_credentials"] > 0:
            console.print(
                f"[bold green]🔑 {summary['total_credentials']} credential(s) discovered[/bold green]"
            )
            console.print()

        # Menu
        click.echo(DesignSystem.separator())
        click.echo(click.style("ACTIONS", bold=True, fg="yellow"))
        click.echo("─" * 170)
        click.echo()
        click.echo("  [1] View Detailed Host Breakdown - See per-host gap analysis")
        click.echo("  [2] View All Gaps - Detailed gap listing")
        click.echo("  [3] View Service Timeline - Service-specific timeline")
        click.echo("  [4] Export Gap Report - Generate gap analysis report")
        click.echo()
        click.echo("  [5] Refresh Analysis - Reload correlation data")
        click.echo()
        click.echo(DesignSystem.separator())
        click.echo()
        click.echo("  [q] ← Back")
        click.echo()

        choice = click.prompt(
            "Select option", type=str, default="q", show_default=False
        )

        if choice == "q":
            return
        elif choice == "1":
            show_host_breakdown(engagement_id, analysis)
        elif choice == "2":
            show_all_gaps(engagement_id, detector)
        elif choice == "3":
            show_service_timeline_menu(engagement_id, analysis)
        elif choice == "4":
            export_gap_report(engagement_id, gaps)
        elif choice == "5":
            continue
        else:
            click.echo(click.style("Invalid choice", fg="red"))
            click.pause()


def show_host_breakdown(engagement_id: int, analysis: dict):
    """Show detailed breakdown per host with pagination."""
    console = Console()

    # Pagination settings
    hosts_per_page = 10
    current_page = 1
    show_empty_hosts = False  # Filter hosts with 0 services by default

    while True:
        # Filter hosts based on show_empty_hosts setting
        if show_empty_hosts:
            filtered_hosts = analysis["hosts"]
        else:
            filtered_hosts = [
                h for h in analysis["hosts"] if h["summary"]["total_services"] > 0
            ]

        if not filtered_hosts:
            DesignSystem.clear_screen()
            width = DesignSystem.get_terminal_width()
            click.echo("\n┌" + "─" * (width - 2) + "┐")
            click.echo(
                "│"
                + click.style(
                    " HOST BREAKDOWN ".center(width - 2), bold=True, fg="cyan"
                )
                + "│"
            )
            click.echo("└" + "─" * (width - 2) + "┘")
            click.echo()
            console.print("[yellow]No hosts with services found.[/yellow]")
            click.pause()
            return

        total_hosts = len(filtered_hosts)
        total_pages = (total_hosts + hosts_per_page - 1) // hosts_per_page

        # Ensure current page is valid
        if current_page > total_pages:
            current_page = total_pages
        if current_page < 1:
            current_page = 1

        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(" HOST BREAKDOWN ".center(width - 2), bold=True, fg="cyan")
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Calculate page range
        start_idx = (current_page - 1) * hosts_per_page
        end_idx = min(start_idx + hosts_per_page, total_hosts)
        page_hosts = filtered_hosts[start_idx:end_idx]

        # Display hosts for current page
        for host_analysis in page_hosts:
            host = host_analysis["host"]
            summary = host_analysis["summary"]

            console.print(f"\n[bold cyan]{'═' * 80}[/bold cyan]")
            console.print(f"[bold]HOST: {host['ip_address']}[/bold]", end="")
            if host.get("hostname"):
                console.print(f" ({host['hostname']})", end="")
            console.print()
            console.print(
                f"Access Level: [{_get_access_color(summary['access_level'])}]{summary['access_level'].upper()}[/{_get_access_color(summary['access_level'])}]"
            )
            console.print()

            # Service summary
            console.print(
                f"Services: {summary['total_services']} total | "
                f"[green]{summary['exploited']} exploited[/green] | "
                f"[yellow]{summary['attempted']} attempted[/yellow] | "
                f"[red]{summary['not_attempted']} not attempted[/red]"
            )
            console.print(f"Credentials: {summary['credentials_found']}")
            console.print()

            # Show services
            for svc_analysis in host_analysis["services"]:
                service = svc_analysis["service"]
                status = svc_analysis["exploitation_status"]

                status_emoji = {
                    "EXPLOITED": "✅",
                    "ATTEMPTED": "🔄",
                    "NOT_ATTEMPTED": "⚠️",
                }[status]

                service_display = f"{service['port']}/{service['protocol']} ({service.get('service_name') or 'unknown'})"
                if service.get("version"):
                    service_display += f" - {service['version']}"

                console.print(f"  {status_emoji} {service_display}")

                # Show job count
                job_count = len(svc_analysis["jobs"])
                cred_count = len(svc_analysis["credentials"])

                if job_count > 0:
                    success_rate = int(svc_analysis["success_rate"] * 100)
                    console.print(
                        f"     Jobs: {job_count} | Success Rate: {success_rate}% | Credentials: {cred_count}"
                    )

                # Show top recommendation
                if svc_analysis["recommendations"]:
                    console.print(f"     💡 {svc_analysis['recommendations'][0]}")

        console.print(f"\n[bold cyan]{'═' * 80}[/bold cyan]")
        click.echo()

        # Pagination info
        click.echo(
            click.style(f"Page {current_page} of {total_pages}", fg="cyan", bold=True)
            + f" (Showing {start_idx + 1}-{end_idx} of {total_hosts} hosts"
            + ("" if show_empty_hosts else " with services")
            + ")"
        )
        click.echo()

        # Navigation options
        nav_options = []
        if current_page > 1:
            nav_options.append("[p] Previous page")
        if current_page < total_pages:
            nav_options.append("[n] Next page")
        if not show_empty_hosts:
            nav_options.append("[a] Show all hosts (including empty)")
        else:
            nav_options.append("[a] Hide empty hosts")
        nav_options.append("[q] Back")

        click.echo("  " + " | ".join(nav_options))
        click.echo()

        choice = click.prompt(
            "Select option", type=str, default="q", show_default=False
        ).lower()

        if choice == "q":
            return
        elif choice == "n" and current_page < total_pages:
            current_page += 1
        elif choice == "p" and current_page > 1:
            current_page -= 1
        elif choice == "a":
            show_empty_hosts = not show_empty_hosts
            current_page = 1  # Reset to first page when toggling filter
        elif choice.isdigit():
            page_num = int(choice)
            if 1 <= page_num <= total_pages:
                current_page = page_num
            else:
                click.echo(click.style("Invalid page number", fg="red"))
                click.pause()
        else:
            click.echo(click.style("Invalid option", fg="red"))
            click.pause()


def show_all_gaps(engagement_id: int, detector: GapDetector):
    """Show all gaps with full details and pagination."""
    console = Console()

    gaps = detector.find_gaps(engagement_id)
    prioritized = detector.prioritize_gaps(gaps)

    if not prioritized:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " EXPLOITATION GAPS - DETAILED VIEW ".center(width - 2),
                bold=True,
                fg="yellow",
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()
        console.print(
            "[bold green]✅ No gaps found! All services have been attempted.[/bold green]"
        )
        click.pause()
        return

    # Pagination settings
    items_per_page = 20
    total_items = len(prioritized)
    total_pages = (
        total_items + items_per_page - 1
    ) // items_per_page  # Ceiling division
    current_page = 1

    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " EXPLOITATION GAPS - DETAILED VIEW ".center(width - 2),
                bold=True,
                fg="yellow",
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Calculate page range
        start_idx = (current_page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        page_items = prioritized[start_idx:end_idx]

        # Create table
        table = Table(
            show_header=True,
            header_style="bold",
            box=DesignSystem.TABLE_BOX,
            expand=True,
        )
        table.add_column("#", width=8)
        table.add_column("Host", width=22)
        table.add_column("Port", width=10)
        table.add_column("Service", width=20)
        table.add_column("Version", width=27)
        table.add_column("Priority", width=15)
        table.add_column("Suggested Action", width=40)

        for idx in range(start_idx, end_idx):
            gap = prioritized[idx]
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "⚪",
            }[gap["severity"]]

            # Get first suggested action
            first_action = (
                gap["suggested_actions"][0]
                if gap["suggested_actions"]
                else "No suggestions"
            )

            table.add_row(
                str(idx + 1),
                gap["host"],
                str(gap["port"]),
                gap["service"],
                (gap.get("version") or "Unknown")[:26],
                f"{severity_emoji} {gap['priority_score']}",
                first_action[:40],
            )

        console.print(table)
        click.echo()

        # Pagination info
        click.echo(
            click.style(f"Page {current_page} of {total_pages}", fg="cyan", bold=True)
            + f" (Showing {start_idx + 1}-{end_idx} of {total_items} gaps)"
        )
        click.echo()

        # Navigation options
        nav_options = []
        if current_page > 1:
            nav_options.append("[p] Previous page")
        if current_page < total_pages:
            nav_options.append("[n] Next page")
        nav_options.append("[q] Back")

        click.echo("  " + " | ".join(nav_options))
        click.echo()

        choice = click.prompt(
            "Select option", type=str, default="q", show_default=False
        ).lower()

        if choice == "q":
            return
        elif choice == "n" and current_page < total_pages:
            current_page += 1
        elif choice == "p" and current_page > 1:
            current_page -= 1
        elif choice.isdigit():
            page_num = int(choice)
            if 1 <= page_num <= total_pages:
                current_page = page_num
            else:
                click.echo(click.style("Invalid page number", fg="red"))
                click.pause()
        else:
            click.echo(click.style("Invalid option", fg="red"))
            click.pause()


def show_service_timeline_menu(engagement_id: int, analysis: dict):
    """Select a service to view timeline."""
    console = Console()

    DesignSystem.clear_screen()
    width = DesignSystem.get_terminal_width()
    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            " SELECT SERVICE FOR TIMELINE ".center(width - 2), bold=True, fg="cyan"
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    # Build service list
    services = []
    for host_analysis in analysis["hosts"]:
        host = host_analysis["host"]
        for svc_analysis in host_analysis["services"]:
            if len(svc_analysis["jobs"]) > 0:  # Only show services with jobs
                services.append(
                    {
                        "host": host,
                        "service": svc_analysis["service"],
                        "analysis": svc_analysis,
                    }
                )

    if not services:
        console.print("[yellow]No services with exploitation attempts found.[/yellow]")
        click.pause()
        return

    # Display services
    for idx, svc_data in enumerate(services, 1):
        host = svc_data["host"]
        service = svc_data["service"]
        analysis = svc_data["analysis"]

        status_emoji = {"EXPLOITED": "✅", "ATTEMPTED": "🔄", "NOT_ATTEMPTED": "⚠️"}[
            analysis["exploitation_status"]
        ]

        console.print(
            f"[{idx}] {status_emoji} {host['ip_address']}:{service['port']} ({service['service_name']}) - {len(analysis['jobs'])} attempts"
        )

    click.echo()
    choice = click.prompt("Select option", type=int, default=0, show_default=False)

    if choice > 0 and choice <= len(services):
        selected = services[choice - 1]
        show_service_timeline(
            selected["host"], selected["service"], selected["analysis"]
        )


def show_service_timeline(host: dict, service: dict, analysis: dict):
    """Show attack progression timeline for a service."""
    console = Console()

    DesignSystem.clear_screen()
    width = DesignSystem.get_terminal_width()
    click.echo("\n┌" + "─" * (width - 2) + "┐")
    service_title = f" ATTACK TIMELINE: {host['ip_address']}:{service['port']} ({service['service_name']}) "
    click.echo(
        "│" + click.style(service_title.center(width - 2), bold=True, fg="cyan") + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    # Service details
    console.print(f"[bold]Service:[/bold] {service['service_name']}")
    if service.get("version"):
        console.print(f"[bold]Version:[/bold] {service['version']}")
    console.print(
        f"[bold]Status:[/bold] [{_get_status_color(analysis['exploitation_status'])}]{analysis['exploitation_status']}[/{_get_status_color(analysis['exploitation_status'])}]"
    )
    console.print()

    # Timeline
    console.print("[bold cyan]📅 TIMELINE[/bold cyan]")
    console.print()

    # Show jobs chronologically
    for idx, job in enumerate(analysis["jobs"], 1):
        timestamp = job.get("created_at", "Unknown")[:19].replace("T", " ")

        # Job status emoji
        if job.get("success"):
            emoji = "✅"
            color = "green"
        elif job["status"] == "failed":
            emoji = "❌"
            color = "red"
        elif job["status"] == "killed":
            emoji = "🛑"
            color = "yellow"
        else:
            emoji = "🔄"
            color = "blue"

        console.print(f"[{color}][{timestamp}] {emoji} Attempt #{idx}[/{color}]")
        console.print(f"  ├─ Tool: {job['tool']}")

        if job.get("label"):
            console.print(f"  ├─ Label: {job['label']}")

        console.print(f"  ├─ Status: {job['status'].upper()}")

        if job.get("success"):
            console.print("  └─ Result: [bold green]SUCCESS ✅[/bold green]")
        else:
            console.print("  └─ Result: [yellow]No credentials found[/yellow]")

        console.print()

    # Show credentials found
    if analysis["credentials"]:
        console.print("[bold green]🔐 CREDENTIALS OBTAINED[/bold green]")
        for cred in analysis["credentials"]:
            username = cred.get("username", "N/A")
            password = cred.get("password", "N/A")
            status = cred.get("status", "unknown")

            status_emoji = "✅" if status == "valid" else "❓"
            console.print(f"  {status_emoji} {username}:{password} [{status}]")
        console.print()

    # Show recommendations
    if analysis["recommendations"]:
        console.print("[bold yellow]💡 RECOMMENDATIONS[/bold yellow]")
        for rec in analysis["recommendations"]:
            console.print(f"  • {rec}")
        console.print()

    click.pause()


def export_gap_report(engagement_id: int, gaps: list):
    """Export gaps to a text report."""
    from datetime import datetime
    from pathlib import Path

    eng_mgr = EngagementManager()
    engagement = eng_mgr.get_by_id(engagement_id)

    if not engagement:
        click.echo(click.style("Engagement not found", fg="red"))
        click.pause()
        return

    # Create reports directory in user home
    reports_dir = Path.home() / ".souleyez" / "data" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gap_report_{engagement['name']}_{timestamp}.txt"
    filepath = reports_dir / filename

    # Write report
    with open(filepath, "w") as f:
        f.write("=" * 80 + "\n")
        f.write(f"EXPLOITATION GAP REPORT\n")
        f.write(f"Engagement: {engagement['name']}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Total Gaps: {len(gaps)}\n\n")

        for idx, gap in enumerate(gaps, 1):
            f.write(f"GAP #{idx}\n")
            f.write("-" * 80 + "\n")
            f.write(f"Host: {gap['host']}\n")
            if gap.get("hostname"):
                f.write(f"Hostname: {gap['hostname']}\n")
            f.write(f"Port: {gap['port']}\n")
            f.write(f"Service: {gap['service']}\n")
            if gap.get("version"):
                f.write(f"Version: {gap['version']}\n")
            f.write(f"Severity: {gap['severity'].upper()}\n")
            f.write(f"Priority Score: {gap['priority_score']}/100\n")
            f.write(f"Reason: {gap['reason']}\n")
            f.write("\nSuggested Actions:\n")
            for action in gap["suggested_actions"]:
                f.write(f"  - {action}\n")

            if gap.get("msf_modules"):
                f.write("\nMetasploit Modules:\n")
                for module in gap["msf_modules"]:
                    f.write(f"  - {module}\n")

            f.write("\n")

    click.echo(click.style(f"✅ Gap report exported to: {filepath}", fg="green"))
    click.pause()


def _get_access_color(access_level: str) -> str:
    """Get color for access level."""
    colors = {"root": "red", "admin": "red", "user": "yellow", "none": "dim"}
    return colors.get(access_level, "white")


def _get_status_color(status: str) -> str:
    """Get color for exploitation status."""
    colors = {"EXPLOITED": "green", "ATTEMPTED": "yellow", "NOT_ATTEMPTED": "red"}
    return colors.get(status, "white")
