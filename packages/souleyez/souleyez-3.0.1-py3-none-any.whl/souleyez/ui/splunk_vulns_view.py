#!/usr/bin/env python3
"""
souleyez.ui.splunk_vulns_view - Splunk Vulnerabilities View

Displays vulnerabilities synced from Wazuh to Splunk with
filtering and display capabilities.
"""

from typing import Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table

from souleyez.ui.design_system import DesignSystem

console = Console()

# Severity colors
SEVERITY_COLORS = {
    "Critical": "red",
    "High": "yellow",
    "Medium": "white",
    "Low": "bright_black",
}


def show_splunk_vulns_view(engagement_id: int, engagement_name: str = "") -> None:
    """
    Display Splunk vulnerabilities view with pagination and filtering.

    Args:
        engagement_id: Current engagement ID
        engagement_name: Engagement name for display
    """
    from souleyez.integrations.wazuh.config import WazuhConfig

    # Pagination and filter state
    page = 0
    page_size = 25
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
                " SPLUNK VULNERABILITIES ".center(width - 2), bold=True, fg="cyan"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Check if Splunk is configured
        config = WazuhConfig.get_config(engagement_id)

        if (
            not config
            or config.get("siem_type") != "splunk"
            or not config.get("enabled")
        ):
            click.echo(
                click.style(
                    "  Splunk is not configured for this engagement.", fg="yellow"
                )
            )
            click.echo()
            click.echo("  Configure Splunk in Settings -> SIEM Integration")
            click.echo()
            click.echo("─" * width)
            click.echo()
            click.echo("  [q] Back")
            click.echo()
            try:
                if click.getchar().lower() == "q":
                    return
            except (KeyboardInterrupt, EOFError):
                return
            continue

        # Get Splunk client
        try:
            from souleyez.integrations.siem.splunk import SplunkSIEMClient

            client = SplunkSIEMClient.from_config(
                {
                    "api_url": config.get("api_url", ""),
                    "username": config.get("username", ""),
                    "password": config.get("password", ""),
                    "verify_ssl": config.get("verify_ssl", False),
                    "default_index": config.get("default_index", "main"),
                }
            )
        except Exception as e:
            click.echo(click.style(f"  Error connecting to Splunk: {e}", fg="red"))
            click.echo()
            click.pause("  Press any key to return...")
            return

        # Get vulnerability summary
        try:
            summary = client.get_vulnerability_summary()
            vulns = client.get_vulnerabilities(
                severity=severity_filter, agent_name=host_filter, limit=1000
            )
        except Exception as e:
            click.echo(click.style(f"  Error querying Splunk: {e}", fg="red"))
            click.echo()
            click.echo("  Make sure the wazuh_vulns index exists and has data.")
            click.echo(
                "  Run the vuln sync script: python3 scripts/wazuh_vuln_to_splunk.py --all"
            )
            click.echo()
            click.pause("  Press any key to return...")
            return

        # Display table with summary
        page, total_pages = _display_vulns_table(
            console,
            vulns,
            page,
            page_size,
            view_all,
            severity_filter,
            host_filter,
            width,
            summary,
        )

        # Menu
        click.echo("─" * width)
        click.echo()
        click.echo("  [#] View vuln details")
        click.echo("  [i] Interactive mode")
        click.echo("  [t] Toggle pagination")
        click.echo("  [f] Filter by severity")
        click.echo("  [h] Filter by host")
        click.echo("  [c] Clear filters")
        click.echo("  [r] Refresh")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = input("  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "r":
                continue  # Refresh
            elif choice == "i":
                _interactive_vulns_mode(vulns)
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
                host_filter = _select_host_filter()
                page = 0
            elif choice == "c":
                severity_filter = None
                host_filter = None
                page = 0
            elif choice.isdigit():
                vuln_idx = int(choice) - 1
                if 0 <= vuln_idx < len(vulns):
                    _show_vuln_detail(vulns[vuln_idx])
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
    page: int,
    page_size: int,
    view_all: bool,
    severity_filter: Optional[str],
    host_filter: Optional[str],
    width: int,
    summary: Dict,
) -> tuple:
    """Display vulnerabilities table with summary header.

    Returns: (current_page, total_pages)
    """
    by_sev = summary.get("by_severity", {})

    # Summary header
    click.echo("═" * width)
    click.echo(
        click.style(
            f" SPLUNK VULNERABILITIES ({summary.get('total', 0)} total, {summary.get('unique_cves', 0)} unique CVEs)",
            bold=True,
            fg="yellow",
        )
    )

    # Severity breakdown
    sev_line = (
        f"  Critical: {by_sev.get('Critical', 0)}  │  "
        f"High: {by_sev.get('High', 0)}  │  "
        f"Medium: {by_sev.get('Medium', 0)}  │  "
        f"Low: {by_sev.get('Low', 0)}"
    )
    click.echo(sev_line)

    # Agents line
    click.echo(
        click.style(
            f"  Agents affected: {summary.get('agents_affected', 0)}", fg="bright_black"
        )
    )

    # Show active filters
    if severity_filter or host_filter:
        filter_parts = []
        if severity_filter:
            filter_parts.append(f"Severity: {severity_filter}")
        if host_filter:
            filter_parts.append(f"Host: {host_filter}")
        click.echo(click.style(f"  Filters: {', '.join(filter_parts)}", fg="cyan"))

    click.echo("─" * width)
    click.echo()

    if not vulns:
        click.echo("  " + click.style("No vulnerabilities found!", fg="green"))
        click.echo("  Make sure Wazuh vuln data is synced to Splunk.")
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

    table.add_column("○", width=3, justify="center")
    table.add_column("#", width=4, justify="right")
    table.add_column("CVE", width=18)
    table.add_column("Severity", width=10)
    table.add_column("CVSS", width=6, justify="center")
    table.add_column("Host", width=16)
    table.add_column("Package", width=25)
    table.add_column("OS", width=12)

    for idx, vuln in enumerate(page_vulns):
        if view_all:
            display_idx = idx + 1
        else:
            display_idx = (page * page_size) + idx + 1

        cve = vuln.get("cve_id", "-")
        severity = vuln.get("severity", "Medium")
        sev_color = SEVERITY_COLORS.get(severity, "white")
        sev_display = f"[{sev_color}]{severity}[/{sev_color}]"

        cvss = vuln.get("cvss_score")
        cvss_display = f"{cvss:.1f}" if cvss else "-"

        host = vuln.get("agent_name", "-")[:15]
        package = vuln.get("package_name", "-")[:24]
        os_name = vuln.get("os_name", "-")[:11]

        table.add_row(
            "○",
            str(display_idx),
            cve,
            sev_display,
            cvss_display,
            host,
            package,
            os_name,
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


def _select_host_filter() -> Optional[str]:
    """Show host filter prompt."""
    click.echo()
    ip = click.prompt(
        "  Enter host/agent name (partial match, or 'c' to clear)", default=""
    )

    if ip.lower() == "c" or not ip:
        return None
    return ip


def _show_vuln_detail(vuln: Dict) -> None:
    """Show detailed vulnerability info."""
    DesignSystem.clear_screen()
    width = DesignSystem.get_terminal_width()

    cve = vuln.get("cve_id", "Unknown")
    severity = vuln.get("severity", "Medium")
    sev_color = SEVERITY_COLORS.get(severity, "white")

    click.echo("\n" + "─" * (width - 2) + "┐")
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

    click.echo(click.style("  Host/Agent:", bold=True))
    click.echo(f"    Agent ID: {vuln.get('agent_id', '-')}")
    click.echo(f"    Agent Name: {vuln.get('agent_name', '-')}")
    click.echo(f"    OS: {vuln.get('os_name', '-')}")
    click.echo()

    click.echo(click.style("  Package:", bold=True))
    click.echo(f"    Name: {vuln.get('package_name', '-')}")
    click.echo(f"    Version: {vuln.get('package_version', '-')}")
    click.echo()

    click.echo(click.style("  Detection:", bold=True))
    click.echo(f"    Detected: {vuln.get('detected_at', '-')}")
    click.echo()

    # Description (truncated)
    desc = vuln.get("description", "")
    if desc:
        click.echo(click.style("  Description:", bold=True))
        # Word wrap description
        words = desc.split()
        line = "    "
        for word in words:
            if len(line) + len(word) + 1 > width - 4:
                click.echo(line)
                line = "    " + word
            else:
                line += " " + word if line != "    " else word
        if line.strip():
            click.echo(line)

    click.echo()
    click.pause("  Press any key to return...")


def _interactive_vulns_mode(vulns: List[Dict]) -> None:
    """Interactive selection mode for vulnerabilities."""
    from souleyez.ui.interactive_selector import interactive_select

    if not vulns:
        click.echo(click.style("  No vulnerabilities to select.", fg="yellow"))
        click.pause()
        return

    # Prepare items for interactive selector
    vuln_items = []
    for vuln in vulns:
        vuln_items.append(
            {
                "id": id(vuln),
                "cve_id": vuln.get("cve_id", "-"),
                "severity": vuln.get("severity", "Medium"),
                "cvss": (
                    f"{vuln.get('cvss_score', 0):.1f}"
                    if vuln.get("cvss_score")
                    else "-"
                ),
                "host": vuln.get("agent_name", "-")[:15],
                "package": vuln.get("package_name", "-")[:20],
                "os": vuln.get("os_name", "-")[:12],
                "raw": vuln,
            }
        )

    columns = [
        {"name": "CVE", "key": "cve_id", "width": 18},
        {"name": "Severity", "key": "severity", "width": 10},
        {"name": "CVSS", "key": "cvss", "width": 6},
        {"name": "Host", "key": "host", "width": 15},
        {"name": "Package", "key": "package", "width": 20},
    ]

    def format_cell(item: Dict, key: str) -> str:
        if key == "severity":
            sev = item.get("severity", "Medium")
            color = SEVERITY_COLORS.get(sev, "white")
            return f"[{color}]{sev}[/{color}]"
        return str(item.get(key, "-"))

    selected_ids: set = set()
    interactive_select(
        items=vuln_items,
        columns=columns,
        selected_ids=selected_ids,
        get_id=lambda v: v["id"],
        title="SPLUNK VULNERABILITIES",
        format_cell=format_cell,
    )

    # Show details of first selected
    if selected_ids:
        for item in vuln_items:
            if item["id"] in selected_ids:
                _show_vuln_detail(item["raw"])
                break
