#!/usr/bin/env python3
"""
Intelligence View UI.
Visual interface for attack surface analysis and exploitation tracking.
"""

import shutil
from typing import Dict, List

import click


def get_terminal_width() -> int:
    """Get terminal width."""
    return shutil.get_terminal_size().columns


def view_intelligence(engagement_id: int):
    """Display Intelligence View - attack surface dashboard."""
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

    show_all_services = False  # Track if all services should be shown
    show_all_targets = False  # Track if all targets should be shown
    show_all_exploits = False  # Track if all exploit suggestions should be shown
    show_all_recommendations = False  # Track if all recommendations should be shown

    # Analyze once before entering loop
    click.echo(click.style("\n🔍 Analyzing attack surface...", fg="yellow", bold=True))
    try:
        analysis = analyzer.analyze_engagement(engagement_id)
    except Exception as e:
        click.echo(click.style(f"Error analyzing: {e}", fg="red"))
        click.pause()
        return

    while True:
        DesignSystem.clear_screen()

        # Header
        width = DesignSystem.get_terminal_width()
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " ATTACK SURFACE DASHBOARD ".center(width - 2), bold=True, fg="cyan"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()
        click.echo(
            f"Engagement: {click.style(engagement['name'], fg='green', bold=True)}"
        )
        click.echo()

        # Overview section
        display_overview(analysis["overview"], width)

        # Top targets
        display_top_targets(analysis["hosts"], width, show_all_targets)

        # Detailed service status for #1 host
        has_more_services = False
        if analysis["hosts"]:
            has_more_services = display_service_status(
                analysis["hosts"][0], width, show_all_services
            )

        # Exploit suggestions
        has_more_exploits = display_exploit_suggestions(
            engagement_id, analysis["hosts"], width, show_all_exploits
        )

        # Recommendations
        has_more_recommendations = display_recommendations(
            analysis["recommendations"], width, show_all_recommendations
        )

        # Menu
        display_menu(width)

        try:
            choice = input("\n  Select option: ").strip()

            if choice == "q" or choice.lower() == "q":
                return
            elif choice == "1":
                view_host_details(engagement_id, analysis["hosts"])
            elif choice == "2":
                filter_services(engagement_id, analysis)
            elif choice == "3":
                export_attack_surface_report(engagement_id, engagement, analysis)
            elif choice == "4":
                auto_exploit_untried(engagement_id, analysis["hosts"])
            elif choice == "5":
                continue  # Refresh
            elif choice == "6":
                show_all_targets = not show_all_targets  # Toggle all targets
                continue
            elif choice == "7":
                show_all_exploits = not show_all_exploits  # Toggle all exploits
                continue
            elif choice == "8":
                show_all_recommendations = (
                    not show_all_recommendations
                )  # Toggle all recommendations
                continue
            elif choice.lower() == "s":
                show_all_services = not show_all_services  # Toggle all services
                continue
            elif choice.lower() == "w":
                # Wazuh Vulnerabilities view
                from souleyez.ui.wazuh_vulns_view import show_wazuh_vulns_view

                show_wazuh_vulns_view(engagement_id, engagement.get("name", ""))
                continue
            elif choice.lower() == "g":
                # Gap Analysis view
                from souleyez.ui.gap_analysis_view import show_gap_analysis_view

                show_gap_analysis_view(engagement_id, engagement.get("name", ""))
                continue
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
    click.echo("  [1] View Host Details - Select and view specific host")
    click.echo("  [2] Filter Services - Filter by status, port, etc.")
    click.echo("  [3] Export Report - Generate attack surface report")
    click.echo("  [4] Auto-Exploit - Automatically exploit untried services")
    click.echo("  [5] Refresh Data - Reload attack surface analysis")
    click.echo()
    click.echo("  [6] Show All Targets - Display all discovered hosts")
    click.echo("  [7] Show All Exploits - Display all exploit suggestions")
    click.echo("  [8] Show All Recommendations - Display all next steps")
    click.echo()
    click.echo(click.style("  WAZUH INTEGRATION", bold=True, fg="blue"))
    click.echo("  [w] Wazuh Vulnerabilities - View agent-detected CVEs")
    click.echo("  [g] Gap Analysis - Compare Wazuh vs scan findings")
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
        choice = int(input("\n  Select option: ").strip())
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
