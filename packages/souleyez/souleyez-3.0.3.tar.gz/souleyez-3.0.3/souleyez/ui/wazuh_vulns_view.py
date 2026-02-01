#!/usr/bin/env python3
"""
souleyez.ui.wazuh_vulns_view - Wazuh Vulnerabilities View

Displays vulnerabilities discovered by Wazuh agents with sync,
filtering, and status management capabilities.
"""

from typing import Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table

from souleyez.integrations.wazuh import WazuhConfig, WazuhHostMapper, WazuhVulnSync
from souleyez.storage.wazuh_vulns import WazuhVulnsManager
from souleyez.ui.design_system import DesignSystem
from souleyez.ui.interactive_selector import interactive_select

console = Console()

# Severity colors
SEVERITY_COLORS = {
    "Critical": "red",
    "High": "yellow",
    "Medium": "white",
    "Low": "bright_black",
}


def show_wazuh_vulns_view(engagement_id: int, engagement_name: str = "") -> None:
    """
    Display Wazuh vulnerabilities view with interactive selection and pagination.

    Args:
        engagement_id: Current engagement ID
        engagement_name: Engagement name for display
    """
    vulns_manager = WazuhVulnsManager()
    host_mapper = WazuhHostMapper()

    # Pagination and filter state
    page = 0
    page_size = 25
    selected_ids: set = set()
    severity_filter: Optional[str] = None
    host_filter: Optional[str] = None
    view_all = False

    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        # Header
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " WAZUH VULNERABILITIES ".center(width - 2), bold=True, fg="cyan"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
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
            click.echo()
            click.echo("─" * width)
            click.echo()
            click.echo("  [q] Back")
            click.echo()
            if click.getchar().lower() == "q":
                return
            continue

        # Get sync status
        sync = WazuhVulnSync(engagement_id)
        sync_status = sync.get_sync_status()

        # Sync status line at top
        if sync_status.get("synced"):
            last_sync = sync_status.get("last_sync_at", "Unknown")
            stale = sync_status.get("is_stale")
            status_color = "yellow" if stale else "green"
            status_text = "(stale)" if stale else "(fresh)"
            click.echo(
                f"  Last sync: {last_sync} "
                + click.style(status_text, fg=status_color)
                + f" | Count: {sync_status.get('last_sync_count', 0)}"
            )
            click.echo()
        else:
            click.echo(
                click.style("  Never synced - press [s] to sync now", fg="yellow")
            )
            click.echo()

        # Get summary
        summary = vulns_manager.get_summary(engagement_id)
        mapping_stats = host_mapper.get_mapping_stats(engagement_id)

        total = summary.get("total", 0)
        verified = summary.get("verified", 0)
        by_sev = summary.get("by_severity", {})
        mapped = mapping_stats.get("mapped", 0)
        unmapped = mapping_stats.get("unmapped", 0)

        # Get all vulnerabilities with filters
        filter_kwargs = {}
        if severity_filter:
            filter_kwargs["severity"] = severity_filter
        if host_filter:
            filter_kwargs["agent_ip"] = host_filter

        all_vulns = vulns_manager.list_vulnerabilities(
            engagement_id, limit=1000, **filter_kwargs
        )

        # Display table with summary header
        page, total_pages = _display_vulns_table(
            console,
            all_vulns,
            selected_ids,
            page,
            page_size,
            view_all,
            severity_filter,
            host_filter,
            width,
            by_sev,
            total,
            mapped,
            unmapped,
            verified,
        )

        # Menu
        click.echo("─" * width)
        click.echo()
        click.echo("  [#] View vuln details")
        click.echo("  [t] Toggle pagination")
        click.echo("  [f] Filter by severity")
        click.echo("  [h] Filter by host")
        click.echo("  [c] Clear filters")
        click.echo("  [s] Sync from Wazuh")
        click.echo("  [m] Map hosts")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = input("  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "s":
                _do_sync(engagement_id)
            elif choice == "m":
                _mapping_menu(engagement_id)
            elif choice == "i":
                # Interactive mode
                _interactive_mode(engagement_id, all_vulns, selected_ids)
            elif choice == "t":
                view_all = not view_all
                if not view_all:
                    page = 0
            elif choice == "n" and not view_all and page < total_pages - 1:
                page += 1
            elif choice == "p" and not view_all and page > 0:
                page -= 1
            elif choice == "f":
                severity_filter = _select_severity_filter()
                page = 0
            elif choice == "h":
                host_filter = _select_host_filter(engagement_id)
                page = 0
            elif choice == "c":
                severity_filter = None
                host_filter = None
                page = 0
            elif choice.isdigit():
                # View vuln details by number
                vuln_idx = int(choice) - 1
                if 0 <= vuln_idx < len(all_vulns):
                    _show_vuln_detail(all_vulns[vuln_idx])
                else:
                    click.echo(click.style("  Invalid number", fg="red"))
                    click.pause()
            else:
                click.echo(click.style("Invalid option", fg="red"))
                click.pause()

        except (KeyboardInterrupt, EOFError):
            return


def _display_vulns_table(
    console: Console,
    vulns: List[Dict],
    selected_ids: set,
    page: int,
    page_size: int,
    view_all: bool,
    severity_filter: Optional[str],
    host_filter: Optional[str],
    width: int,
    by_sev: Dict,
    total: int,
    mapped: int,
    unmapped: int,
    verified: int,
) -> tuple:
    """Display vulnerabilities table with summary header.

    Returns: (current_page, total_pages)
    """
    # Count by severity from current vulns
    severity_counts = {
        "Critical": sum(1 for v in vulns if v.get("severity") == "Critical"),
        "High": sum(1 for v in vulns if v.get("severity") == "High"),
        "Medium": sum(1 for v in vulns if v.get("severity") == "Medium"),
        "Low": sum(1 for v in vulns if v.get("severity") == "Low"),
    }

    # Summary header
    click.echo("═" * width)
    click.echo(
        click.style(
            f"⚠️  WAZUH VULNERABILITIES ({len(vulns)} total)", bold=True, fg="yellow"
        )
    )

    # Severity breakdown line with emojis
    sev_line = (
        f"  🔴 Critical: {severity_counts['Critical']}  │  "
        f"🟠 High: {severity_counts['High']}  │  "
        f"🟡 Medium: {severity_counts['Medium']}  │  "
        f"⚪ Low: {severity_counts['Low']}"
    )
    click.echo(sev_line)

    # Stats line
    click.echo(
        click.style(
            f"  Verified: {verified}  │  Mapped: {mapped}  │  Unmapped: {unmapped}",
            fg="bright_black",
        )
    )

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

    if not vulns:
        click.echo("  " + click.style("No vulnerabilities found!", fg="green"))
        click.echo("  Press [s] to sync from Wazuh.")
        click.echo()
        return 0, 1

    # Pagination
    total_pages = max(1, (len(vulns) + page_size - 1) // page_size)
    page = min(page, total_pages - 1)

    if view_all:
        page_vulns = vulns
    else:
        start_idx = page * page_size
        end_idx = min(start_idx + page_size, len(vulns))
        page_vulns = vulns[start_idx:end_idx]

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
    table.add_column("CVE", width=18)
    table.add_column("Severity", width=10)
    table.add_column("Host", width=16)
    table.add_column("Package", width=25)
    table.add_column("CVSS", width=6, justify="center")

    for idx, vuln in enumerate(page_vulns):
        # Calculate display index
        if view_all:
            display_idx = idx + 1
        else:
            display_idx = (page * page_size) + idx + 1

        vuln_id = vuln.get("id")

        # Checkbox
        checkbox = "●" if vuln_id in selected_ids else "○"

        # CVE
        cve = vuln.get("cve_id", "-")

        # Severity with color
        severity = vuln.get("severity", "Medium")
        sev_color = SEVERITY_COLORS.get(severity, "white")
        sev_display = f"[{sev_color}]{severity}[/{sev_color}]"

        # Host
        host_ip = vuln.get("host_ip") or vuln.get("agent_ip", "-")

        # Package (truncated)
        package = vuln.get("package_name", "-")[:24]

        # CVSS
        cvss = vuln.get("cvss_score")
        cvss_display = f"{cvss:.1f}" if cvss else "-"

        table.add_row(
            checkbox, str(display_idx), cve, sev_display, host_ip, package, cvss_display
        )

    console.print("  ", table)

    # Pagination info
    if view_all:
        click.echo(f"\n  Showing all {len(vulns)} vulnerabilities")
    else:
        click.echo(f"\n  Page {page + 1}/{total_pages}")

    click.echo()
    click.echo("  💡 TIP: Press 'i' for interactive mode")
    if total_pages > 1 and not view_all:
        click.echo("  n/p: Next/Previous page")

    click.echo()

    return page, total_pages


def _interactive_mode(engagement_id: int, vulns: List[Dict], selected_ids: set) -> None:
    """Run interactive selection mode."""
    if not vulns:
        click.echo(click.style("  No vulnerabilities to select.", fg="yellow"))
        click.pause()
        return

    # Prepare items for interactive selector
    vuln_items = []
    for vuln in vulns:
        vuln_items.append(
            {
                "id": vuln.get("id"),
                "cve_id": vuln.get("cve_id", "-"),
                "severity": vuln.get("severity", "Medium"),
                "host": vuln.get("host_ip") or vuln.get("agent_ip", "-"),
                "package": vuln.get("package_name", "-")[:24],
                "cvss": (
                    f"{vuln.get('cvss_score', 0):.1f}"
                    if vuln.get("cvss_score")
                    else "-"
                ),
                "raw": vuln,
            }
        )

    columns = [
        {"name": "CVE", "key": "cve_id", "width": 18},
        {"name": "Severity", "key": "severity", "width": 10},
        {"name": "Host", "key": "host", "width": 16},
        {"name": "Package", "key": "package", "width": 24},
        {"name": "CVSS", "key": "cvss", "width": 6, "justify": "center"},
    ]

    def format_cell(item: Dict, key: str) -> str:
        if key == "severity":
            sev = item.get("severity", "Medium")
            color = SEVERITY_COLORS.get(sev, "white")
            return f"[{color}]{sev}[/{color}]"
        return str(item.get(key, "-"))

    interactive_select(
        items=vuln_items,
        columns=columns,
        selected_ids=selected_ids,
        get_id=lambda v: v["id"],
        title="SELECT WAZUH VULNERABILITIES",
        format_cell=format_cell,
    )

    if selected_ids:
        _bulk_action_menu(engagement_id, vuln_items, selected_ids)


def _bulk_action_menu(
    engagement_id: int, vuln_items: List[Dict], selected_ids: set
) -> None:
    """Show bulk action menu for selected vulnerabilities."""
    selected = [v for v in vuln_items if v["id"] in selected_ids]

    if not selected:
        return

    click.echo()
    click.echo(
        click.style(f"  Selected: {len(selected)} vulnerability(ies)", bold=True)
    )
    click.echo("    [v] View details")
    click.echo("    [r] Mark as verified")
    click.echo("    [e] Export to file")
    click.echo("    [x] Mark as false positive")
    click.echo("    [c] Clear selection")
    click.echo("    [q] Back")
    click.echo()

    try:
        choice = (
            click.prompt("  Select option", default="q", show_default=False)
            .strip()
            .lower()
        )

        if choice == "v":
            # View details of first selected
            vuln = selected[0]["raw"]
            _show_vuln_detail(vuln)
        elif choice == "r":
            # Mark as verified
            vulns_manager = WazuhVulnsManager()
            count = 0
            for item in selected:
                try:
                    vulns_manager.update_vulnerability(
                        item["id"], status="confirmed", verified_by_scan=True
                    )
                    count += 1
                except Exception:
                    pass
            click.echo(click.style(f"  ✓ Verified {count} vulnerabilities", fg="green"))
            click.pause("  Press any key to continue...")
            selected_ids.clear()
        elif choice == "x":
            # Mark as false positive
            vulns_manager = WazuhVulnsManager()
            count = 0
            for item in selected:
                try:
                    vulns_manager.update_vulnerability(
                        item["id"], status="false_positive"
                    )
                    count += 1
                except Exception:
                    pass
            click.echo(
                click.style(f"  ✓ Marked {count} as false positive", fg="yellow")
            )
            click.pause("  Press any key to continue...")
            selected_ids.clear()
        elif choice == "e":
            # Export selected
            _export_selected(selected)
        elif choice == "c":
            selected_ids.clear()

    except (KeyboardInterrupt, EOFError):
        pass


def _export_selected(selected: List[Dict]) -> None:
    """Export selected vulnerabilities to file."""
    import json
    from datetime import datetime

    filename = f"wazuh_vulns_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    export_data = []
    for item in selected:
        vuln = item.get("raw", item)
        export_data.append(
            {
                "cve_id": vuln.get("cve_id"),
                "severity": vuln.get("severity"),
                "cvss_score": vuln.get("cvss_score"),
                "host_ip": vuln.get("host_ip") or vuln.get("agent_ip"),
                "package_name": vuln.get("package_name"),
                "package_version": vuln.get("package_version"),
            }
        )

    with open(filename, "w") as f:
        json.dump(export_data, f, indent=2)

    click.echo(
        click.style(
            f"  ✓ Exported {len(selected)} vulnerabilities to {filename}", fg="green"
        )
    )
    click.pause("  Press any key to continue...")


def _select_severity_filter() -> Optional[str]:
    """Show severity filter menu."""
    click.echo()
    click.echo("  Select severity:")
    click.echo("    [1] Critical  [2] High  [3] Medium  [4] Low  [c] Clear")
    click.echo()

    key = click.getchar().lower()
    severity_map = {"1": "Critical", "2": "High", "3": "Medium", "4": "Low"}

    if key == "c":
        return None
    return severity_map.get(key)


def _select_host_filter(engagement_id: int) -> Optional[str]:
    """Show host filter prompt."""
    click.echo()
    ip = click.prompt("  Enter host IP (partial match, or 'c' to clear)", default="")

    if ip.lower() == "c" or not ip:
        return None
    return ip


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
        click.echo(f"    New: {result.new_vulns}")
        click.echo(f"    Updated: {result.updated_vulns}")
        click.echo(f"    Mapped hosts: {result.mapped_hosts}")

        if result.unmapped_agents:
            click.echo()
            click.echo(
                click.style(
                    f"  Unmapped agents ({len(result.unmapped_agents)}):", fg="yellow"
                )
            )
            for agent_ip in result.unmapped_agents[:5]:
                click.echo(f"    - {agent_ip}")
            if len(result.unmapped_agents) > 5:
                click.echo(f"    ... and {len(result.unmapped_agents) - 5} more")

        if result.errors:
            click.echo()
            click.echo(click.style(f"  Errors ({len(result.errors)}):", fg="yellow"))
            for err in result.errors[:3]:
                click.echo(f"    - {err}")
    else:
        click.echo(click.style("  ✗ Sync failed", fg="red", bold=True))
        for err in result.errors:
            click.echo(click.style(f"    {err}", fg="red"))

    click.echo()
    click.echo(
        click.style(f"  Duration: {result.duration_seconds:.1f}s", fg="bright_black")
    )
    click.echo()
    click.pause("  Press any key to continue...")


def _mapping_menu(engagement_id: int) -> None:
    """Show host mapping options."""
    host_mapper = WazuhHostMapper()

    DesignSystem.clear_screen()
    width = DesignSystem.get_terminal_width()

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" HOST MAPPING ".center(width - 2), bold=True, fg="cyan")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    # Get mapping stats
    stats = host_mapper.get_mapping_stats(engagement_id)
    click.echo(
        f"  Mapped: {stats['mapped']} | Unmapped: {stats['unmapped']} | Total: {stats['total']}"
    )
    click.echo()

    # Show unmapped agents
    unmapped = host_mapper.get_unmapped_agents(engagement_id)
    if unmapped:
        click.echo(click.style("  Unmapped Agents:", fg="yellow"))
        for agent in unmapped[:10]:
            click.echo(
                f"    - {agent.get('agent_ip')} ({agent.get('agent_name', 'unknown')}) - {agent.get('vuln_count')} vulns"
            )

        # Show suggestions
        suggestions = host_mapper.suggest_mappings(engagement_id)
        if suggestions:
            click.echo()
            click.echo(click.style("  Suggested Mappings:", fg="cyan"))
            for sug in suggestions[:5]:
                click.echo(
                    f"    {sug['agent_ip']} → {sug['suggested_host_ip']} "
                    f"({sug.get('suggested_host_name', '-')}) - {sug['reason']}"
                )
    else:
        click.echo(click.style("  ✓ All agents are mapped to hosts.", fg="green"))

    click.echo()
    click.echo("─" * width)
    click.echo()
    click.echo("  [1] Auto-map all")
    click.echo("  [2] Manual map")
    click.echo("  [q] Back")
    click.echo()

    key = click.getchar().lower()

    if key == "1":
        click.echo()
        click.echo("  Auto-mapping agents to hosts...")
        mapping = host_mapper.auto_map_all(engagement_id)

        mapped_count = sum(1 for h in mapping.values() if h)
        click.echo(
            click.style(f"  ✓ Mapped {mapped_count} agents to hosts", fg="green")
        )
        click.echo()
        click.pause("  Press any key to continue...")


def _show_vuln_detail(vuln: Dict) -> None:
    """Show detailed vulnerability info."""
    DesignSystem.clear_screen()
    width = DesignSystem.get_terminal_width()

    cve = vuln.get("cve_id", "Unknown")
    severity = vuln.get("severity", "Medium")
    sev_color = SEVERITY_COLORS.get(severity, "white")

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
