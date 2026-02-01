#!/usr/bin/env python3
"""
souleyez.ui.gap_analysis_view - Gap Analysis View

Displays comparison between Wazuh (passive) and scan (active)
vulnerability detection to identify gaps in coverage.
"""

from typing import Dict, List

import click
from rich.console import Console
from rich.table import Table

from souleyez.integrations.wazuh import WazuhConfig, WazuhVulnSync
from souleyez.intelligence.gap_analyzer import GapAnalysisResult, GapAnalyzer
from souleyez.ui.design_system import DesignSystem

console = Console()

# Severity colors for click
SEVERITY_COLORS = {
    "Critical": "red",
    "High": "yellow",
    "Medium": "white",
    "Low": "bright_black",
    "critical": "red",
    "high": "yellow",
    "medium": "white",
    "low": "bright_black",
}


def show_gap_analysis_view(engagement_id: int, engagement_name: str = "") -> None:
    """
    Display gap analysis view.

    Args:
        engagement_id: Current engagement ID
        engagement_name: Engagement name for display
    """
    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        # Header
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " WAZUH GAP ANALYSIS ".center(width - 2), bold=True, fg="cyan"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()
        click.echo(
            click.style(
                "  Compare Wazuh (passive) vs Scan (active) findings", fg="bright_black"
            )
        )
        click.echo()

        # Check if Wazuh is configured
        config = WazuhConfig.get_config(engagement_id)
        if not config or not config.get("enabled"):
            click.echo(
                click.style(
                    "  ⚠️  Wazuh is not configured for this engagement.", fg="yellow"
                )
            )
            click.echo()
            click.echo("  Configure Wazuh in Settings → Integrations → Wazuh SIEM")
            click.echo("  Then sync vulnerabilities before running gap analysis.")
            click.echo()
            click.echo("─" * width)
            click.echo()
            click.echo("  [q] Back")
            click.echo()
            if click.getchar().lower() == "q":
                return
            continue

        # Check sync status
        sync = WazuhVulnSync(engagement_id)
        sync_status = sync.get_sync_status()

        if not sync_status.get("synced"):
            click.echo(click.style("  ⚠️  No Wazuh data synced yet.", fg="yellow"))
            click.echo()
            click.echo("  Press [s] to sync vulnerabilities from Wazuh first.")
            click.echo()
            click.echo("─" * width)
            click.echo()
            click.echo("  [s] Sync Now")
            click.echo("  [q] Back")
            click.echo()

            key = click.getchar().lower()
            if key == "s":
                _do_sync(engagement_id)
            elif key == "q":
                return
            continue

        # Run gap analysis
        analyzer = GapAnalyzer(engagement_id)
        result = analyzer.analyze()
        stats = analyzer.get_coverage_stats()

        # Summary dashboard
        _render_summary_dashboard(result, stats, width)

        # Menu
        click.echo("─" * width)
        click.echo()
        click.echo("  [1] Wazuh Only (scan missed)")
        click.echo("  [2] Scan Only (Wazuh missed)")
        click.echo("  [3] Confirmed (both)")
        click.echo("  [a] Actionable Gaps")
        click.echo("  [s] Re-sync")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = input("  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "1":
                _show_wazuh_only(result, width)
            elif choice == "2":
                _show_scan_only(result, width)
            elif choice == "3":
                _show_confirmed(result, width)
            elif choice == "a":
                _show_actionable_gaps(engagement_id, width)
            elif choice == "s":
                _do_sync(engagement_id)
        except (KeyboardInterrupt, EOFError):
            return


def _render_summary_dashboard(
    result: GapAnalysisResult, stats: Dict, width: int
) -> None:
    """Render the summary dashboard."""
    wazuh_total = result.wazuh_total
    scan_total = result.scan_total
    confirmed = len(result.confirmed)
    wazuh_only = len(result.wazuh_only)
    scan_only = len(result.scan_only)
    coverage = stats.get("coverage_pct", 0)

    # Coverage color
    if coverage >= 80:
        coverage_color = "green"
    elif coverage >= 50:
        coverage_color = "yellow"
    else:
        coverage_color = "red"

    # Detection Sources
    click.echo(click.style("  DETECTION SOURCES", bold=True))
    click.echo(
        f"    Wazuh (passive):  {click.style(str(wazuh_total), fg='cyan', bold=True)} CVEs"
    )
    click.echo(
        f"    Scans (active):   {click.style(str(scan_total), fg='cyan', bold=True)} CVEs"
    )
    click.echo()

    # Analysis Results
    click.echo(click.style("  ANALYSIS RESULTS", bold=True))
    click.echo(
        f"    {click.style('✓', fg='green')} Confirmed (both):     {click.style(str(confirmed), bold=True)}"
    )
    click.echo(
        f"    {click.style('⚠', fg='yellow')} Wazuh Only:           {click.style(str(wazuh_only), bold=True)}  ← Scans missed these"
    )
    click.echo(
        f"    {click.style('○', fg='blue')} Scan Only:            {click.style(str(scan_only), bold=True)}  ← Wazuh missed these"
    )
    click.echo()

    # Coverage
    click.echo(
        f"  Coverage: "
        + click.style(f"{coverage:.1f}%", fg=coverage_color, bold=True)
        + " of Wazuh vulns confirmed by scans"
    )
    click.echo()

    # Severity breakdown
    sev_breakdown = stats.get("by_severity", {})
    if (
        sev_breakdown.get("wazuh_only")
        or sev_breakdown.get("scan_only")
        or sev_breakdown.get("confirmed")
    ):
        _render_severity_breakdown(sev_breakdown, width)


def _render_severity_breakdown(breakdown: Dict, width: int) -> None:
    """Render severity breakdown."""
    from rich import box
    from rich.table import Table

    SEVERITY_ICONS = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "⚪"}

    table = Table(
        show_header=True,
        header_style="bold",
        box=box.SIMPLE,
        padding=(0, 2),
        expand=False,
    )

    table.add_column("Severity", width=14)
    table.add_column("Wazuh Only", width=12, justify="right")
    table.add_column("Scan Only", width=12, justify="right")
    table.add_column("Confirmed", width=12, justify="right")

    for sev in ["Critical", "High", "Medium", "Low"]:
        icon = SEVERITY_ICONS.get(sev, "")
        color = SEVERITY_COLORS.get(sev, "white")
        wazuh_only = breakdown.get("wazuh_only", {}).get(sev, 0)
        scan_only = breakdown.get("scan_only", {}).get(sev, 0)
        confirmed = breakdown.get("confirmed", {}).get(sev, 0)

        table.add_row(
            f"{icon} [{color}]{sev}[/{color}]",
            str(wazuh_only) if wazuh_only else "-",
            str(scan_only) if scan_only else "-",
            str(confirmed) if confirmed else "-",
        )

    console.print("  ", table)
    click.echo()


def _show_wazuh_only(result: GapAnalysisResult, width: int) -> None:
    """Show vulnerabilities found only by Wazuh with pagination."""
    page = 0
    page_size = 20
    view_all = False
    gaps = result.wazuh_only

    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " WAZUH ONLY - SCANS MISSED ".center(width - 2), bold=True, fg="yellow"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        click.echo(f"  {len(gaps)} CVEs detected by Wazuh but NOT by active scans.")
        click.echo(
            click.style(
                "  These may be local/package vulnerabilities not exposed to network scanning.",
                fg="bright_black",
            )
        )
        click.echo()

        if not gaps:
            click.echo(
                click.style(
                    "  ✓ No gaps - all Wazuh vulns confirmed by scans!", fg="green"
                )
            )
            click.echo()
            click.pause("  Press any key to return...")
            return

        # Pagination
        total_pages = max(1, (len(gaps) + page_size - 1) // page_size)
        page = min(page, total_pages - 1)

        if view_all:
            page_gaps = gaps
        else:
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(gaps))
            page_gaps = gaps[start_idx:end_idx]

        _render_gaps_table(
            page_gaps,
            width,
            show_package=True,
            page=page,
            page_size=page_size,
            view_all=view_all,
        )

        # Pagination info
        if view_all:
            click.echo(f"\n  Showing all {len(gaps)} results")
        else:
            click.echo(f"\n  Page {page + 1}/{total_pages}")

        click.echo()
        click.echo("  💡 TIP: Press 'i' for interactive mode")
        if total_pages > 1 and not view_all:
            click.echo("  n/p: Next/Previous page")

        # Menu
        click.echo()
        click.echo("─" * width)
        click.echo()
        click.echo("  [#] View details")
        click.echo("  [t] Toggle pagination")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = input("  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "i":
                _interactive_gaps_mode(gaps, "WAZUH ONLY GAPS", show_package=True)
            elif choice == "t":
                view_all = not view_all
                if not view_all:
                    page = 0
            elif choice == "n" and not view_all and page < total_pages - 1:
                page += 1
            elif choice == "p" and not view_all and page > 0:
                page -= 1
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(page_gaps):
                    _show_gap_detail(page_gaps[idx])
        except (KeyboardInterrupt, EOFError):
            return


def _show_scan_only(result: GapAnalysisResult, width: int) -> None:
    """Show vulnerabilities found only by scans with pagination."""
    page = 0
    page_size = 20
    view_all = False
    gaps = result.scan_only

    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " SCAN ONLY - WAZUH MISSED ".center(width - 2), bold=True, fg="blue"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        click.echo(f"  {len(gaps)} CVEs detected by active scans but NOT by Wazuh.")
        click.echo(
            click.style(
                "  This may indicate: missing Wazuh agent, detection rule gap, or network-only vuln.",
                fg="bright_black",
            )
        )
        click.echo()

        if not gaps:
            click.echo(
                click.style(
                    "  ✓ No gaps - Wazuh detected all scan findings!", fg="green"
                )
            )
            click.echo()
            click.pause("  Press any key to return...")
            return

        # Pagination
        total_pages = max(1, (len(gaps) + page_size - 1) // page_size)
        page = min(page, total_pages - 1)

        if view_all:
            page_gaps = gaps
        else:
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(gaps))
            page_gaps = gaps[start_idx:end_idx]

        _render_gaps_table(
            page_gaps,
            width,
            show_tool=True,
            page=page,
            page_size=page_size,
            view_all=view_all,
        )

        # Pagination info
        if view_all:
            click.echo(f"\n  Showing all {len(gaps)} results")
        else:
            click.echo(f"\n  Page {page + 1}/{total_pages}")

        click.echo()
        click.echo("  💡 TIP: Press 'i' for interactive mode")
        if total_pages > 1 and not view_all:
            click.echo("  n/p: Next/Previous page")

        # Menu
        click.echo()
        click.echo("─" * width)
        click.echo()
        click.echo("  [#] View details")
        click.echo("  [t] Toggle pagination")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = input("  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "i":
                _interactive_gaps_mode(gaps, "SCAN ONLY GAPS", show_tool=True)
            elif choice == "t":
                view_all = not view_all
                if not view_all:
                    page = 0
            elif choice == "n" and not view_all and page < total_pages - 1:
                page += 1
            elif choice == "p" and not view_all and page > 0:
                page -= 1
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(page_gaps):
                    _show_gap_detail(page_gaps[idx])
        except (KeyboardInterrupt, EOFError):
            return


def _show_confirmed(result: GapAnalysisResult, width: int) -> None:
    """Show vulnerabilities confirmed by both sources with pagination."""
    page = 0
    page_size = 20
    view_all = False
    gaps = result.confirmed

    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " CONFIRMED - BOTH SOURCES ".center(width - 2), bold=True, fg="green"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        click.echo(f"  {len(gaps)} CVEs detected by BOTH Wazuh and active scans.")
        click.echo(
            click.style(
                "  High confidence - prioritize these for exploitation.",
                fg="bright_black",
            )
        )
        click.echo()

        if not gaps:
            click.echo(
                click.style(
                    "  No confirmed matches between Wazuh and scans.", fg="yellow"
                )
            )
            click.echo()
            click.pause("  Press any key to return...")
            return

        # Pagination
        total_pages = max(1, (len(gaps) + page_size - 1) // page_size)
        page = min(page, total_pages - 1)

        if view_all:
            page_gaps = gaps
        else:
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(gaps))
            page_gaps = gaps[start_idx:end_idx]

        _render_gaps_table(
            page_gaps,
            width,
            show_both=True,
            page=page,
            page_size=page_size,
            view_all=view_all,
        )

        # Pagination info
        if view_all:
            click.echo(f"\n  Showing all {len(gaps)} results")
        else:
            click.echo(f"\n  Page {page + 1}/{total_pages}")

        click.echo()
        click.echo("  💡 TIP: Press 'i' for interactive mode")
        if total_pages > 1 and not view_all:
            click.echo("  n/p: Next/Previous page")

        # Menu
        click.echo()
        click.echo("─" * width)
        click.echo()
        click.echo("  [#] View details")
        click.echo("  [t] Toggle pagination")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = input("  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "i":
                _interactive_gaps_mode(gaps, "CONFIRMED GAPS", show_both=True)
            elif choice == "t":
                view_all = not view_all
                if not view_all:
                    page = 0
            elif choice == "n" and not view_all and page < total_pages - 1:
                page += 1
            elif choice == "p" and not view_all and page > 0:
                page -= 1
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(page_gaps):
                    _show_gap_detail(page_gaps[idx])
        except (KeyboardInterrupt, EOFError):
            return


def _show_actionable_gaps(engagement_id: int, width: int) -> None:
    """Show actionable gaps with recommendations and pagination."""
    page = 0
    page_size = 20
    view_all = False

    analyzer = GapAnalyzer(engagement_id)
    gaps = analyzer.get_actionable_gaps(limit=100)

    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(" ACTIONABLE GAPS ".center(width - 2), bold=True, fg="yellow")
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        click.echo(
            f"  {len(gaps)} prioritized vulnerabilities from Wazuh that need targeted scanning."
        )
        click.echo()

        if not gaps:
            click.echo(
                click.style("  ✓ No actionable gaps - great scan coverage!", fg="green")
            )
            click.echo()
            click.pause("  Press any key to return...")
            return

        # Pagination
        total_pages = max(1, (len(gaps) + page_size - 1) // page_size)
        page = min(page, total_pages - 1)

        if view_all:
            page_gaps = gaps
        else:
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(gaps))
            page_gaps = gaps[start_idx:end_idx]

        # Render table
        table = DesignSystem.create_table()

        table.add_column("○", width=3, justify="center")
        table.add_column("#", width=3, style="dim")
        table.add_column("PRIORITY", width=8)
        table.add_column("CVE", width=18)
        table.add_column("SEVERITY", width=10)
        table.add_column("HOST", width=15)
        table.add_column("PACKAGE", width=20)
        table.add_column("RECOMMENDATION", width=35)

        for idx, gap in enumerate(page_gaps):
            # Calculate display index
            if view_all:
                display_idx = idx + 1
            else:
                display_idx = (page * page_size) + idx + 1

            priority = gap.get("priority", "medium")
            priority_display = (
                "[red]HIGH[/red]" if priority == "high" else "[yellow]MEDIUM[/yellow]"
            )

            severity = gap.get("severity", "Medium")
            sev_color = SEVERITY_COLORS.get(severity, "white")

            table.add_row(
                "○",
                str(display_idx),
                priority_display,
                gap.get("cve_id", "-"),
                f"[{sev_color}]{severity}[/{sev_color}]",
                gap.get("host_ip", "-"),
                gap.get("package", "-")[:19],
                gap.get("recommendation", "-")[:34],
            )

        console.print(table)

        # Pagination info
        if view_all:
            click.echo(f"\n  Showing all {len(gaps)} results")
        else:
            click.echo(f"\n  Page {page + 1}/{total_pages}")

        click.echo()
        click.echo("  💡 TIP: Press 'i' for interactive mode")
        if total_pages > 1 and not view_all:
            click.echo("  n/p: Next/Previous page")

        # Menu
        click.echo()
        click.echo("─" * width)
        click.echo()
        click.echo("  [#] View details")
        click.echo("  [t] Toggle pagination")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = input("  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "i":
                _interactive_actionable_gaps_mode(gaps, "ACTIONABLE GAPS")
            elif choice == "t":
                view_all = not view_all
                if not view_all:
                    page = 0
            elif choice == "n" and not view_all and page < total_pages - 1:
                page += 1
            elif choice == "p" and not view_all and page > 0:
                page -= 1
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(page_gaps):
                    _show_actionable_gap_detail(page_gaps[idx])
        except (KeyboardInterrupt, EOFError):
            return


def _render_gaps_table(
    gaps: List,
    width: int,
    show_package: bool = False,
    show_tool: bool = False,
    show_both: bool = False,
    page: int = 0,
    page_size: int = 20,
    view_all: bool = False,
) -> None:
    """Render gaps table with pagination support."""
    table = DesignSystem.create_table()

    table.add_column("○", width=3, justify="center")
    table.add_column("#", width=3, style="dim")
    table.add_column("CVE", width=18)
    table.add_column("SEVERITY", width=10)
    table.add_column("HOST", width=15)

    if show_package:
        table.add_column("PACKAGE", width=25)
        table.add_column("RECOMMENDATION", width=35)
    elif show_tool:
        table.add_column("TOOL", width=15)
        table.add_column("RECOMMENDATION", width=40)
    elif show_both:
        table.add_column("PACKAGE", width=20)
        table.add_column("SCAN TOOL", width=15)
        table.add_column("CONFIDENCE", width=10)

    for idx, gap in enumerate(gaps):
        # Calculate display index for proper numbering
        if view_all:
            display_idx = idx + 1
        else:
            display_idx = (page * page_size) + idx + 1

        severity = gap.severity
        sev_color = SEVERITY_COLORS.get(severity, "white")

        row = [
            "○",
            str(display_idx),
            gap.cve_id,
            f"[{sev_color}]{severity}[/{sev_color}]",
            gap.host_ip or "-",
        ]

        if show_package:
            package = (
                gap.wazuh_details.get("package_name", "-") if gap.wazuh_details else "-"
            )
            row.append(package[:24])
            row.append(gap.recommendation[:34])
        elif show_tool:
            tool = gap.scan_details.get("tool", "-") if gap.scan_details else "-"
            row.append(tool)
            row.append(gap.recommendation[:39])
        elif show_both:
            package = (
                gap.wazuh_details.get("package_name", "-") if gap.wazuh_details else "-"
            )
            tool = gap.scan_details.get("tool", "-") if gap.scan_details else "-"
            row.append(package[:19])
            row.append(tool)
            row.append(f"[green]{gap.confidence}[/green]")

        table.add_row(*row)

    console.print(table)


def _show_gap_detail(gap) -> None:
    """Show detailed info for a gap item."""
    DesignSystem.clear_screen()
    width = DesignSystem.get_terminal_width()

    cve = gap.cve_id or "Unknown"
    severity = gap.severity or "Medium"
    sev_color = SEVERITY_COLORS.get(severity, "white")

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│" + click.style(f" {cve} ".center(width - 2), bold=True, fg="cyan") + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    click.echo(f"  Severity: " + click.style(severity, fg=sev_color, bold=True))
    click.echo(f"  Host: {gap.host_ip or '-'}")
    click.echo(f"  Source: {gap.source or '-'}")
    click.echo(f"  Confidence: {gap.confidence or '-'}")
    click.echo()

    if gap.wazuh_details:
        click.echo(click.style("  Wazuh Details:", bold=True))
        click.echo(f"    Package: {gap.wazuh_details.get('package_name', '-')}")
        click.echo(f"    Version: {gap.wazuh_details.get('package_version', '-')}")
        click.echo(f"    CVSS: {gap.wazuh_details.get('cvss_score', '-')}")
        click.echo()

    if gap.scan_details:
        click.echo(click.style("  Scan Details:", bold=True))
        click.echo(f"    Tool: {gap.scan_details.get('tool', '-')}")
        click.echo(f"    Port: {gap.scan_details.get('port', '-')}")
        click.echo(f"    Service: {gap.scan_details.get('service', '-')}")
        click.echo()

    if gap.recommendation:
        click.echo(click.style("  Recommendation:", bold=True))
        click.echo(f"    {gap.recommendation}")
        click.echo()

    click.pause("  Press any key to return...")


def _show_actionable_gap_detail(gap: Dict) -> None:
    """Show detailed info for an actionable gap."""
    DesignSystem.clear_screen()
    width = DesignSystem.get_terminal_width()

    cve = gap.get("cve_id", "Unknown")
    severity = gap.get("severity", "Medium")
    sev_color = SEVERITY_COLORS.get(severity, "white")

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│" + click.style(f" {cve} ".center(width - 2), bold=True, fg="cyan") + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    priority = gap.get("priority", "medium")
    priority_color = "red" if priority == "high" else "yellow"

    click.echo(f"  Severity: " + click.style(severity, fg=sev_color, bold=True))
    click.echo(
        f"  Priority: " + click.style(priority.upper(), fg=priority_color, bold=True)
    )
    click.echo(f"  Host: {gap.get('host_ip', '-')}")
    click.echo()

    click.echo(click.style("  Package:", bold=True))
    click.echo(f"    Name: {gap.get('package', '-')}")
    click.echo(f"    Version: {gap.get('package_version', '-')}")
    click.echo()

    if gap.get("recommendation"):
        click.echo(click.style("  Recommendation:", bold=True))
        click.echo(f"    {gap.get('recommendation')}")
        click.echo()

    if gap.get("scan_command"):
        click.echo(click.style("  Suggested Scan Command:", bold=True))
        click.echo(f"    {gap.get('scan_command')}")
        click.echo()

    click.pause("  Press any key to return...")


def _interactive_gaps_mode(
    gaps: List,
    title: str,
    show_package: bool = False,
    show_tool: bool = False,
    show_both: bool = False,
) -> None:
    """Interactive selection mode for gaps."""
    from souleyez.ui.interactive_selector import interactive_select

    if not gaps:
        click.echo(click.style("  No gaps to select.", fg="yellow"))
        click.pause()
        return

    # Prepare items for interactive selector
    gap_items = []
    for gap in gaps:
        item = {
            "id": id(gap),
            "cve_id": gap.cve_id or "-",
            "severity": gap.severity or "Medium",
            "host": gap.host_ip or "-",
            "raw": gap,
        }
        if show_package:
            item["package"] = (
                gap.wazuh_details.get("package_name", "-")[:20]
                if gap.wazuh_details
                else "-"
            )
        elif show_tool:
            item["tool"] = (
                gap.scan_details.get("tool", "-") if gap.scan_details else "-"
            )
        elif show_both:
            item["package"] = (
                gap.wazuh_details.get("package_name", "-")[:15]
                if gap.wazuh_details
                else "-"
            )
            item["tool"] = (
                gap.scan_details.get("tool", "-") if gap.scan_details else "-"
            )
        gap_items.append(item)

    columns = [
        {"name": "CVE", "key": "cve_id", "width": 18},
        {"name": "Severity", "key": "severity", "width": 10},
        {"name": "Host", "key": "host", "width": 15},
    ]

    if show_package:
        columns.append({"name": "Package", "key": "package", "width": 20})
    elif show_tool:
        columns.append({"name": "Tool", "key": "tool", "width": 15})
    elif show_both:
        columns.append({"name": "Package", "key": "package", "width": 15})
        columns.append({"name": "Tool", "key": "tool", "width": 15})

    def format_cell(item: Dict, key: str) -> str:
        if key == "severity":
            sev = item.get("severity", "Medium")
            color = SEVERITY_COLORS.get(sev, "white")
            return f"[{color}]{sev}[/{color}]"
        return str(item.get(key, "-"))

    selected_ids: set = set()
    interactive_select(
        items=gap_items,
        columns=columns,
        selected_ids=selected_ids,
        get_id=lambda g: g["id"],
        title=title,
        format_cell=format_cell,
    )

    # Show details of first selected
    if selected_ids:
        for item in gap_items:
            if item["id"] in selected_ids:
                _show_gap_detail(item["raw"])
                break


def _interactive_actionable_gaps_mode(gaps: List[Dict], title: str) -> None:
    """Interactive selection mode for actionable gaps."""
    from souleyez.ui.interactive_selector import interactive_select

    if not gaps:
        click.echo(click.style("  No gaps to select.", fg="yellow"))
        click.pause()
        return

    # Prepare items for interactive selector
    gap_items = []
    for gap in gaps:
        gap_items.append(
            {
                "id": id(gap),
                "cve_id": gap.get("cve_id", "-"),
                "severity": gap.get("severity", "Medium"),
                "priority": gap.get("priority", "medium").upper(),
                "host": gap.get("host_ip", "-"),
                "package": gap.get("package", "-")[:20],
                "raw": gap,
            }
        )

    columns = [
        {"name": "Priority", "key": "priority", "width": 8},
        {"name": "CVE", "key": "cve_id", "width": 18},
        {"name": "Severity", "key": "severity", "width": 10},
        {"name": "Host", "key": "host", "width": 15},
        {"name": "Package", "key": "package", "width": 20},
    ]

    def format_cell(item: Dict, key: str) -> str:
        if key == "severity":
            sev = item.get("severity", "Medium")
            color = SEVERITY_COLORS.get(sev, "white")
            return f"[{color}]{sev}[/{color}]"
        elif key == "priority":
            pri = item.get("priority", "MEDIUM")
            color = "red" if pri == "HIGH" else "yellow"
            return f"[{color}]{pri}[/{color}]"
        return str(item.get(key, "-"))

    selected_ids: set = set()
    interactive_select(
        items=gap_items,
        columns=columns,
        selected_ids=selected_ids,
        get_id=lambda g: g["id"],
        title=title,
        format_cell=format_cell,
    )

    # Show details of first selected
    if selected_ids:
        for item in gap_items:
            if item["id"] in selected_ids:
                _show_actionable_gap_detail(item["raw"])
                break


def _do_sync(engagement_id: int) -> None:
    """Perform sync from Wazuh."""
    DesignSystem.clear_screen()
    width = DesignSystem.get_terminal_width()

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" SYNCING FROM WAZUH ".center(width - 2), bold=True, fg="blue")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    click.echo("  Fetching vulnerabilities...")

    sync = WazuhVulnSync(engagement_id)
    result = sync.sync_full()

    click.echo()

    if result.success:
        click.echo(click.style("  ✓ Sync complete!", fg="green", bold=True))
        click.echo(f"    Fetched: {result.total_fetched}")
        click.echo(f"    Mapped hosts: {result.mapped_hosts}")
    else:
        click.echo(click.style("  ✗ Sync failed", fg="red", bold=True))
        for err in result.errors:
            click.echo(click.style(f"    {err}", fg="red"))

    click.echo()
    click.pause("  Press any key to continue...")
