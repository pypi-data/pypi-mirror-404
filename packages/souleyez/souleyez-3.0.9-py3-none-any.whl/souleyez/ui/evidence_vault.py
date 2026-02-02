#!/usr/bin/env python3
"""
Evidence & Artifacts - Unified evidence collection view.
Displays all artifacts organized by pentesting methodology phases.
Consolidates Evidence Vault and Screenshots into a single view.
"""

import shutil
from typing import Dict, List, Optional, Set

import click
from rich.console import Console
from rich.table import Table

from souleyez.ui.design_system import DesignSystem
from souleyez.ui.errors import engagement_not_found

# Rich console for table rendering
console = Console()

# Phase display info
PHASE_DISPLAY = {
    "reconnaissance": ("📡 RECON", "cyan"),
    "enumeration": ("🔍 ENUM", "blue"),
    "exploitation": ("💥 EXPLOIT", "red"),
    "post_exploitation": ("🎯 POST", "magenta"),
}

PHASE_ORDER = ["reconnaissance", "enumeration", "exploitation", "post_exploitation"]


def _flatten_evidence(
    evidence: Dict[str, List[Dict]], phase_filter: Optional[str] = None
) -> List[Dict]:
    """Flatten evidence dict into a single list with phase info."""
    flat = []
    for phase_key in PHASE_ORDER:
        if phase_filter and phase_key != phase_filter:
            continue
        for item in evidence.get(phase_key, []):
            item_copy = item.copy()
            item_copy["phase"] = phase_key
            flat.append(item_copy)
    return flat


def _build_evidence_table(
    items: List[Dict], selected_ids: Set[int], page: int, page_size: int, view_all: bool
) -> tuple:
    """Build Rich table for evidence items.

    Returns (table, total_pages, displayed_items).
    """
    total_items = len(items)
    total_pages = max(1, (total_items + page_size - 1) // page_size)

    # Paginate
    if view_all:
        displayed = items
    else:
        start = page * page_size
        end = min(start + page_size, total_items)
        displayed = items[start:end]

    # Create table
    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=DesignSystem.TABLE_BOX,
        padding=(0, 1),
        expand=True,
    )

    table.add_column("○", width=3, justify="center")
    table.add_column("#", width=4, justify="right")
    table.add_column("Phase", width=12)
    table.add_column("Type", width=10)
    table.add_column("Tool", width=10)
    table.add_column("Title")
    table.add_column("Description", width=30)
    table.add_column("Severity", width=10, justify="center")

    for idx, item in enumerate(displayed):
        # Row number (global index)
        if view_all:
            row_num = idx + 1
        else:
            row_num = (page * page_size) + idx + 1

        # Checkbox
        item_id = item.get("id", idx)
        checkbox = "●" if item_id in selected_ids else "○"

        # Phase with color
        phase_key = item.get("phase", "reconnaissance")
        phase_label, phase_color = PHASE_DISPLAY.get(phase_key, ("?", "white"))
        phase_display = f"[{phase_color}]{phase_label}[/{phase_color}]"

        # Type
        item_type = item.get("type", "job").capitalize()

        # Tool
        tool = item.get("tool", "-").upper()

        # Title - use label for jobs, title for findings
        if item_type.lower() == "job":
            title = item.get("label") or item.get("title", "-")
        else:
            title = item.get("title", "-")

        # Description - actual description field
        desc = item.get("description", "-")
        if not desc or desc == "None":
            desc = "-"
        if len(str(desc)) > 28:
            desc = str(desc)[:28] + "…"

        # Severity with color
        severity = item.get("severity", "")
        if severity in ["critical", "high"]:
            sev_display = f"[red]🔴 HIGH[/red]"
        elif severity == "medium":
            sev_display = f"[yellow]🟡 MED[/yellow]"
        elif severity in ["low", "info"]:
            sev_display = f"[green]🟢 LOW[/green]"
        else:
            sev_display = "[dim]--[/dim]"

        table.add_row(
            checkbox,
            str(row_num),
            phase_display,
            item_type,
            tool,
            title,
            desc,
            sev_display,
        )

    return table, total_pages, displayed


def get_terminal_width() -> int:
    """Get terminal width."""
    return shutil.get_terminal_size().columns


def view_evidence_vault(engagement_id: int):
    """Display Evidence & Artifacts for engagement.

    Consolidates Evidence Vault and Screenshots into a unified view.
    """
    from souleyez.storage.engagements import EngagementManager
    from souleyez.storage.evidence import EvidenceManager
    from souleyez.storage.screenshots import ScreenshotManager

    em = EngagementManager()
    evm = EvidenceManager()
    sm = ScreenshotManager()

    engagement = em.get_by_id(engagement_id)
    if not engagement:
        engagement_not_found(engagement_id)
        click.pause()
        return

    # State variables
    filters = {}
    page = 0
    page_size = 15
    view_all = False
    selected_ids: Set[int] = set()
    phase_filter: Optional[str] = None

    while True:
        DesignSystem.clear_screen()
        width = get_terminal_width()

        # Header
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " EVIDENCE & ARTIFACTS ".center(width - 2), bold=True, fg="cyan"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Get evidence and screenshots
        evidence = evm.get_all_evidence(engagement_id, filters)
        screenshots = sm.list_screenshots(engagement_id)
        screenshot_count = len(screenshots)

        # Calculate stats
        total_count = sum(len(items) for items in evidence.values())
        credentials_count = sum(
            1
            for phase_items in evidence.values()
            for item in phase_items
            if item.get("type") == "credential"
        )
        findings_count = sum(
            1
            for phase_items in evidence.values()
            for item in phase_items
            if item.get("type") == "finding"
        )
        high_value = sum(
            1
            for phase_items in evidence.values()
            for item in phase_items
            if item.get("severity") in ["critical", "high"]
        )

        # Summary line
        click.echo(click.style("📊 SUMMARY", bold=True))
        click.echo(
            f"  Total: {total_count}  │  🔑 Credentials: {credentials_count}  │  🔍 Findings: {findings_count}  │  🔴 High-Value: {high_value}  │  📸 Screenshots: {screenshot_count}"
        )
        click.echo()

        # Engagement and filter info
        filter_parts = [f"Engagement: {engagement['name']}"]
        if phase_filter:
            phase_label, _ = PHASE_DISPLAY.get(phase_filter, (phase_filter, "white"))
            filter_parts.append(f"Phase: {phase_label}")
        if filters:
            if "tool" in filters:
                filter_parts.append(f"Tool: {filters['tool']}")
            if "host" in filters:
                filter_parts.append(f"Host: {filters['host']}")
            if "days" in filters:
                filter_parts.append(f"Last {filters['days']} days")

        # Flatten evidence for table display
        flat_evidence = _flatten_evidence(evidence, phase_filter)
        total_items = len(flat_evidence)
        total_pages = max(1, (total_items + page_size - 1) // page_size)

        # Clamp page to valid range
        if page >= total_pages:
            page = max(0, total_pages - 1)

        filter_parts.append(f"Page {page + 1}/{total_pages}")
        click.echo("  " + "  │  ".join(filter_parts))
        click.echo()

        # Build and display table
        if total_items == 0:
            click.echo(click.style("  No evidence collected yet", fg="bright_black"))
        else:
            table, _, displayed_items = _build_evidence_table(
                flat_evidence, selected_ids, page, page_size, view_all
            )
            console.print("  ", table)

        # Tip line
        click.echo()
        click.echo("  💡 TIP: Press 'i' for interactive mode")

        # Selection count
        if selected_ids:
            click.echo(
                click.style(
                    f"  Selected: {len(selected_ids)} item(s)", fg="cyan", bold=True
                )
            )

        # Menu
        click.echo()
        click.echo("─" * width)
        click.echo()
        click.echo("  [#] View evidence details")
        click.echo("  [t] Toggle pagination" + (" (showing all)" if view_all else ""))
        click.echo(
            "  [g] Filter by phase"
            + (
                f" ({PHASE_DISPLAY.get(phase_filter, ('All', ''))[0]})"
                if phase_filter
                else " (All)"
            )
        )
        click.echo("  [c] Screenshots" + f" ({screenshot_count})")
        click.echo("  [s] Search evidence")
        click.echo("  [f] Filter by tool/host/date")
        click.echo(
            "  [x] Export"
            + (f" ({len(selected_ids)} selected)" if selected_ids else " all")
        )
        click.echo("  [?] Help")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = input("  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "t":
                view_all = not view_all
                page = 0
            elif choice == "n" and not view_all:
                if page < total_pages - 1:
                    page += 1
            elif choice == "p" and not view_all:
                if page > 0:
                    page -= 1
            elif choice == "g":
                # Inline phase filter submenu
                click.echo("\n  Filter by phase:")
                click.echo("    [0] All phases")
                click.echo("    [1] 📡 RECON")
                click.echo("    [2] 🔍 ENUM")
                click.echo("    [3] 💥 EXPLOIT")
                click.echo("    [4] 🎯 POST")
                click.echo()
                phase_choice = input("  Select option: ").strip()
                phase_map = {
                    "0": None,
                    "1": "reconnaissance",
                    "2": "enumeration",
                    "3": "exploitation",
                    "4": "post_exploitation",
                }
                if phase_choice in phase_map:
                    phase_filter = phase_map[phase_choice]
                    page = 0
            elif choice == "c":
                view_screenshots(engagement_id, screenshots, sm)
            elif choice == "s":
                search_evidence(engagement_id, evidence)
            elif choice == "f":
                filters = apply_filters()
                page = 0
            elif choice == "x":
                if selected_ids:
                    # Export selected items
                    click.echo(
                        click.style(
                            f"\nExporting {len(selected_ids)} selected items...",
                            fg="yellow",
                        )
                    )
                    export_evidence_bundle(engagement_id, engagement, evidence)
                else:
                    export_evidence_bundle(engagement_id, engagement, evidence)
            elif choice == "?":
                _show_evidence_help()
            elif choice == "i":
                # Interactive mode
                _interactive_evidence_select(flat_evidence, selected_ids, engagement_id)
            elif choice.isdigit():
                # View evidence detail by row number
                row_num = int(choice)
                if 1 <= row_num <= total_items:
                    item = flat_evidence[row_num - 1]
                    _view_evidence_detail(item)
                else:
                    click.echo(
                        click.style(f"Invalid row number (1-{total_items})", fg="red")
                    )
                    click.pause()
            elif choice.startswith(" ") and choice.strip().isdigit():
                # Toggle selection with space+number
                row_num = int(choice.strip())
                if 1 <= row_num <= total_items:
                    item = flat_evidence[row_num - 1]
                    item_id = item.get("id", row_num - 1)
                    if item_id in selected_ids:
                        selected_ids.discard(item_id)
                    else:
                        selected_ids.add(item_id)
            elif choice == "":
                pass  # Just refresh
            else:
                click.echo(click.style("Invalid option. Press ? for help.", fg="red"))
                click.pause()

        except (KeyboardInterrupt, EOFError):
            return
        except ValueError:
            click.echo(click.style("Invalid input", fg="red"))
            click.pause()


def _interactive_evidence_select(
    items: List[Dict], selected_ids: Set[int], engagement_id: int
):
    """Interactive mode for evidence selection with arrow keys."""
    from souleyez.ui.interactive_selector import interactive_select

    if not items:
        click.echo(click.style("\nNo evidence to display", fg="yellow"))
        click.pause()
        return

    # Build item dicts for selector
    item_dicts = []
    for item in items:
        item_type = item.get("type", "job")
        if item_type == "job":
            title = item.get("label") or item.get("title", "-")
        else:
            title = item.get("title", "-")
        if len(str(title)) > 50:
            title = str(title)[:50] + "…"

        phase_key = item.get("phase", "reconnaissance")
        phase_label, _ = PHASE_DISPLAY.get(phase_key, ("?", "white"))

        severity = item.get("severity", "")
        if severity in ["critical", "high"]:
            sev_display = "🔴 HIGH"
        elif severity == "medium":
            sev_display = "🟡 MED"
        elif severity in ["low", "info"]:
            sev_display = "🟢 LOW"
        else:
            sev_display = "--"

        item_dicts.append(
            {
                "id": item.get("id", 0),
                "phase": phase_label,
                "type": item.get("type", "job").capitalize(),
                "tool": item.get("tool", "-").upper(),
                "title": title,
                "severity": sev_display,
            }
        )

    def on_action(action: str, selected: set, current_item: dict):
        if action == "v" and current_item:
            # View details
            item_id = current_item.get("id")
            for item in items:
                if item.get("id") == item_id:
                    _view_evidence_detail(item)
                    break

    while True:
        interactive_select(
            items=item_dicts,
            columns=[
                {"name": "Phase", "width": 12, "key": "phase"},
                {"name": "Type", "width": 10, "key": "type"},
                {"name": "Tool", "width": 10, "key": "tool"},
                {"name": "Title", "key": "title"},
                {"name": "Severity", "width": 10, "key": "severity"},
            ],
            selected_ids=selected_ids,
            get_id=lambda x: x.get("id"),
            title="SELECT EVIDENCE",
        )

        if not selected_ids:
            return

        result = _evidence_bulk_action_menu(items, selected_ids, engagement_id)
        if result == "back":
            return


def _evidence_bulk_action_menu(
    items: List[Dict], selected_ids: Set[int], engagement_id: int
) -> str:
    """Show action menu for selected evidence items."""
    selected_items = [item for item in items if item.get("id") in selected_ids]

    if not selected_items:
        return "continue"

    click.echo()
    click.echo(f"  Selected: {len(selected_items)} item(s)")
    click.echo("    [v] View first item")
    click.echo("    [x] Export selected")
    click.echo("    [c] Clear selection")
    click.echo("    [q] Back")
    click.echo()

    try:
        choice = (
            click.prompt("  Select option", default="q", show_default=False)
            .strip()
            .lower()
        )

        if choice == "q":
            return "back"
        elif choice == "v" and selected_items:
            _view_evidence_detail(selected_items[0])
            return "continue"
        elif choice == "x":
            _export_selected_evidence(selected_items, engagement_id)
            return "continue"
        elif choice == "c":
            selected_ids.clear()
            click.echo(click.style("  ✓ Selection cleared", fg="green"))
            return "continue"

    except (KeyboardInterrupt, EOFError):
        pass

    return "continue"


def _export_selected_evidence(selected_items: List[Dict], engagement_id: int):
    """Export selected evidence items to a ZIP file."""
    import os
    import zipfile
    from datetime import datetime

    from souleyez.storage.engagement import EngagementManager

    click.echo(
        click.style(f"\n  Exporting {len(selected_items)} item(s)...", fg="yellow")
    )

    try:
        # Get engagement info
        em = EngagementManager()
        engagement = em.get_by_id(engagement_id)
        eng_name = engagement["name"] if engagement else f"engagement_{engagement_id}"

        # Create output directory
        output_dir = os.path.expanduser("~/.souleyez/exports")
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = eng_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        zip_filename = f"{safe_name}_selected_evidence_{timestamp}.zip"
        zip_path = os.path.join(output_dir, zip_filename)

        # Create ZIP
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add README
            readme_lines = [
                "=" * 70,
                f"SELECTED EVIDENCE EXPORT: {eng_name}",
                "=" * 70,
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Engagement ID: {engagement_id}",
                f"Items Exported: {len(selected_items)}",
                "",
                "CONTENTS:",
                "-" * 70,
            ]

            for idx, item in enumerate(selected_items, 1):
                item_type = item.get("type", "unknown")
                tool = item.get("tool", "N/A")
                target = item.get("target", "N/A")
                readme_lines.append(f"  {idx}. [{item_type}] {tool} -> {target}")

                # Export job logs
                if item_type == "job":
                    log_path = item.get("log_path")
                    if log_path and os.path.exists(log_path):
                        safe_tool = tool.replace("/", "_").replace("\\", "_")
                        safe_target = (
                            str(target).replace("/", "_").replace(":", "_")[:50]
                        )
                        phase = item.get("phase", "general").replace("_", "-")
                        arcname = f"{phase}/{idx:03d}_{safe_tool}_{safe_target}.log"
                        zipf.write(log_path, arcname)
                        readme_lines.append(f"       -> {arcname}")

            readme_lines.extend(["", "=" * 70])
            zipf.writestr("README.txt", "\n".join(readme_lines))

        click.echo(click.style(f"\n  ✓ Exported to:", fg="green"))
        click.echo(f"    {zip_path}")

    except Exception as e:
        click.echo(click.style(f"\n  ✗ Export failed: {e}", fg="red"))

    click.pause()


def _show_evidence_help():
    """Display help for evidence vault navigation."""
    DesignSystem.clear_screen()
    width = get_terminal_width()

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            " EVIDENCE & ARTIFACTS - HELP ".center(width - 2), bold=True, fg="cyan"
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    click.echo(click.style("  NAVIGATION", bold=True, fg="yellow"))
    click.echo("  ───────────────────────────────────────")
    click.echo("  [#]        Enter a row number to view details")
    click.echo("  [n/p]      Next/Previous page (when paginated)")
    click.echo("  [t]        Toggle between paginated and full view")
    click.echo()

    click.echo(click.style("  FILTERING", bold=True, fg="yellow"))
    click.echo("  ───────────────────────────────────────")
    click.echo("  [g]        Filter by phase (shows submenu)")
    click.echo("  [f]        Apply filters by tool, host, or date range")
    click.echo("  [s]        Full-text search across all evidence")
    click.echo()

    click.echo(click.style("  ACTIONS", bold=True, fg="yellow"))
    click.echo("  ───────────────────────────────────────")
    click.echo("  [space #]  Toggle selection for row # (e.g., ' 3' selects row 3)")
    click.echo("  [x]        Export evidence (selected items or all)")
    click.echo("  [c]        View and manage screenshots")
    click.echo()

    click.echo(click.style("  OTHER", bold=True, fg="yellow"))
    click.echo("  ───────────────────────────────────────")
    click.echo("  [?]        Show this help")
    click.echo("  [q]        Return to main menu")
    click.echo()

    click.pause("Press any key to return...")


def _view_evidence_detail(item: Dict):
    """Display detailed view of a single evidence item."""
    DesignSystem.clear_screen()
    width = get_terminal_width()

    # Header
    item_type = item.get("type", "item").upper()
    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            f" EVIDENCE DETAIL - {item_type} ".center(width - 2), bold=True, fg="cyan"
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    # Phase badge
    phase_key = item.get("phase", "reconnaissance")
    phase_label, phase_color = PHASE_DISPLAY.get(phase_key, ("?", "white"))
    click.echo(f"  {click.style(phase_label, fg=phase_color, bold=True)}")
    click.echo()

    # Main info
    click.echo(click.style("  TITLE", bold=True))
    click.echo(f"  {item.get('title', 'Untitled')}")
    click.echo()

    click.echo(click.style("  DESCRIPTION", bold=True))
    desc = item.get("description", "No description")
    # Word wrap description
    for line in desc.split("\n"):
        click.echo(f"  {line}")
    click.echo()

    # Tool and target
    click.echo(click.style("  DETAILS", bold=True))
    click.echo(f"  Tool:   {item.get('tool', '-').upper()}")
    target = item.get("target", item.get("host", "-"))
    if isinstance(target, list):
        target = ", ".join(target) if target else "-"
    click.echo(f"  Target: {target}")

    # Severity for findings
    if item.get("severity"):
        severity = item["severity"].upper()
        if severity in ["CRITICAL", "HIGH"]:
            sev_str = click.style(f"🔴 {severity}", fg="red", bold=True)
        elif severity == "MEDIUM":
            sev_str = click.style(f"🟡 {severity}", fg="yellow")
        else:
            sev_str = click.style(f"🟢 {severity}", fg="green")
        click.echo(f"  Severity: {sev_str}")

    # Status for jobs
    if item.get("status"):
        status = item["status"]
        if status == "done":
            status_str = click.style("✓ Completed", fg="green")
        elif status == "error":
            status_str = click.style("✗ Error", fg="red")
        elif status == "running":
            status_str = click.style("⟳ Running", fg="yellow")
        else:
            status_str = status
        click.echo(f"  Status: {status_str}")

    # Date
    if item.get("created_at"):
        click.echo(f"  Date:   {item['created_at'][:19].replace('T', ' ')}")

    click.echo()

    # Additional metadata if present
    metadata_keys = [
        "port",
        "service",
        "version",
        "cve",
        "cvss",
        "username",
        "raw_output",
    ]
    has_metadata = any(item.get(k) for k in metadata_keys)

    if has_metadata:
        click.echo(click.style("  METADATA", bold=True))
        for key in metadata_keys:
            if item.get(key):
                value = item[key]
                if key == "raw_output":
                    click.echo(f"  {key}:")
                    for line in str(value)[:500].split("\n")[:10]:
                        click.echo(f"    {line}")
                    if len(str(value)) > 500:
                        click.echo("    ... (truncated)")
                else:
                    click.echo(f"  {key}: {value}")
        click.echo()

    click.echo("─" * width)
    click.echo()
    click.echo("  [q] Back to list")
    click.echo()

    input("  Select option: ")


def display_evidence_item(item: Dict):
    """Display a single evidence item."""
    # Icon based on type
    icons = {"job": "📄", "finding": "🔍", "credential": "🔑", "file": "📁"}
    icon = icons.get(item["type"], "•")

    # Format date
    try:
        date_str = item["created_at"][:16].replace("T", " ")
    except:
        date_str = "Unknown date"

    # Add severity icon for findings
    severity_icon = ""
    if item.get("severity") in ["critical", "high"]:
        severity_icon = " 🔴"
    elif item.get("severity") == "medium":
        severity_icon = " 🟡"

    # Main line
    tool_upper = item["tool"].upper()
    click.echo(
        f"  {icon} [{click.style(tool_upper, fg='cyan')}]{severity_icon} {item['title']}"
    )
    click.echo(f"     → {item['description']}")
    click.echo(f"     {click.style(date_str, fg='bright_black')}", nl=False)

    # Type-specific info
    if item["type"] == "job":
        if item.get("status") == "done":
            click.echo(f" | {click.style('Completed', fg='green')}", nl=False)
        elif item.get("status") == "error":
            click.echo(f" | {click.style('Error', fg='red')}", nl=False)
    elif item["type"] == "finding":
        severity = item.get("severity", "info").upper()
        sev_color = (
            "red"
            if severity in ["CRITICAL", "HIGH"]
            else "yellow" if severity == "MEDIUM" else "blue"
        )
        click.echo(f" | {click.style(f'Severity: {severity}', fg=sev_color)}", nl=False)
    elif item["type"] == "credential":
        click.echo(f" | {click.style('Credential Found', fg='green')}", nl=False)

    click.echo()  # New line
    click.echo()  # Spacing


def view_phase_details(engagement_id: int, evidence: Dict[str, List[Dict]]):
    """View detailed items for a specific phase."""
    click.echo("\n" + click.style("Select Phase:", bold=True))
    click.echo("  [1] Reconnaissance")
    click.echo("  [2] Enumeration")
    click.echo("  [3] Exploitation")
    click.echo("  [4] Post-Exploitation")
    click.echo("  [q] Cancel")
    click.echo()

    choice = input("  Select option: ").strip()

    phase_map = {
        "1": "reconnaissance",
        "2": "enumeration",
        "3": "exploitation",
        "4": "post_exploitation",
    }

    if choice == "q":
        return

    phase_key = phase_map.get(choice)
    if not phase_key:
        click.echo(click.style("Invalid selection", fg="red"))
        click.pause()
        return

    # Show all items in this phase
    DesignSystem.clear_screen()
    width = get_terminal_width()

    phase_names = {
        "reconnaissance": "RECONNAISSANCE",
        "enumeration": "ENUMERATION",
        "exploitation": "EXPLOITATION",
        "post_exploitation": "POST-EXPLOITATION",
    }

    click.echo("\n" + "=" * width)
    click.echo(click.style(phase_names[phase_key], bold=True, fg="cyan").center(width))
    click.echo("=" * width + "\n")

    items = evidence.get(phase_key, [])

    if not items:
        click.echo(click.style("No evidence in this phase", fg="yellow"))
    else:
        for idx, item in enumerate(items, 1):
            click.echo(f"\n{click.style(f'[{idx}]', fg='cyan', bold=True)} ", nl=False)
            display_evidence_item(item)

    click.pause("\nPress any key to return...")


def apply_filters() -> Dict:
    """Apply filters to evidence view."""
    click.echo("\n" + click.style("Filter Evidence", bold=True, fg="cyan"))
    click.echo("─" * 40)
    click.echo()

    filters = {}

    # Tool filter
    tool = input("Filter by tool (or 'all'): ").strip()
    if tool and tool.lower() != "all":
        filters["tool"] = tool

    # Host filter
    host = input("Filter by host/target (or 'all'): ").strip()
    if host and host.lower() != "all":
        filters["host"] = host

    # Date filter
    click.echo("\nFilter by date:")
    click.echo("  [1] Last 24 hours")
    click.echo("  [2] Last 7 days")
    click.echo("  [3] Last 30 days")
    click.echo("  [4] All time")

    date_choice = input("  Select option: ").strip()

    days_map = {"1": 1, "2": 7, "3": 30, "4": None}
    days = days_map.get(date_choice)

    if days:
        filters["days"] = days

    if filters:
        click.echo("\n" + click.style("✓ Filters applied", fg="green"))
    else:
        click.echo("\n" + click.style("No filters applied", fg="yellow"))

    click.pause()
    return filters


def search_evidence(engagement_id: int, evidence: Dict[str, List[Dict]]):
    """Search evidence with full-text search."""
    click.echo()
    search_term = click.prompt("Enter search term", default="").strip()

    if not search_term:
        return

    search_lower = search_term.lower()
    results = []

    # Search across all evidence
    for phase, items in evidence.items():
        for item in items:
            # Search in title, description, tool
            searchable = f"{item.get('title', '')} {item.get('description', '')} {item.get('tool', '')}".lower()
            if search_lower in searchable:
                results.append((phase, item))

    # Display results
    DesignSystem.clear_screen()
    click.echo()
    click.echo(
        click.style(f"🔍 SEARCH RESULTS FOR: {search_term}", bold=True, fg="cyan")
    )
    click.echo("=" * 80)
    click.echo()

    if not results:
        click.echo(click.style("  No matches found", fg="yellow"))
    else:
        click.echo(f"Found {len(results)} match(es):\n")
        for phase, item in results[:20]:  # Show first 20
            severity_icon = ""
            if item.get("severity") in ["critical", "high"]:
                severity_icon = " 🔴"
            elif item.get("severity") == "medium":
                severity_icon = " 🟡"

            icon = {"job": "📄", "finding": "🔍", "credential": "🔑", "file": "📁"}.get(
                item["type"], "•"
            )
            click.echo(f"  {icon} [{phase.upper()}]{severity_icon} {item['title']}")
            click.echo(f"     → {item['description'][:80]}")
            click.echo()

        if len(results) > 20:
            click.echo(f"  ... and {len(results) - 20} more matches")

    click.echo()
    click.pause()


def export_evidence_bundle(
    engagement_id: int, engagement: Dict, evidence: Dict[str, List[Dict]]
):
    """Export all evidence as ZIP bundle."""
    click.echo("\n" + click.style("Exporting evidence bundle...", fg="yellow"))

    try:
        from souleyez.export.evidence_bundle import create_evidence_bundle

        zip_path = create_evidence_bundle(engagement_id, engagement, evidence)
        click.echo(click.style(f"\n✓ Evidence bundle created:", fg="green"))
        click.echo(f"  {zip_path}")

    except Exception as e:
        click.echo(click.style(f"\n✗ Export failed: {e}", fg="red"))

    click.pause()


def view_screenshots(engagement_id: int, screenshots: List[Dict], sm):
    """View and manage screenshots for the engagement.

    Embedded screenshots view within Evidence & Artifacts.
    """
    import subprocess
    import sys
    from pathlib import Path

    from rich.console import Console
    from rich.table import Table

    while True:
        DesignSystem.clear_screen()
        width = get_terminal_width()

        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(" SCREENSHOTS ".center(width - 2), bold=True, fg="cyan")
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Refresh screenshots list
        screenshots = sm.list_screenshots(engagement_id)

        if not screenshots:
            click.echo(click.style("  No screenshots found", fg="yellow"))
            click.echo()
            click.echo(
                "  💡 Add screenshots with: souleyez screenshots add /path/to/image.png"
            )
            click.echo()
            click.echo("  [q] ← Back")
            click.echo()

            choice = click.prompt(
                "Select option", type=str, default="q", show_default=False
            )
            if choice == "q":
                return
            continue

        click.echo(f"  Total Screenshots: {len(screenshots)}")
        click.echo()

        # Display table
        console = Console()
        table = Table(
            show_header=True,
            header_style="bold",
            box=DesignSystem.TABLE_BOX,
            expand=True,
        )
        table.add_column("#", width=4)
        table.add_column("ID", width=6)
        table.add_column("Title", width=30)
        table.add_column("Size", width=10)
        table.add_column("Links", width=20)
        table.add_column("Created", width=12)

        for idx, s in enumerate(screenshots, 1):
            # Format size
            size = s["file_size"]
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"

            # Format links
            links = []
            if s["host_id"]:
                links.append(f"Host:{s['host_id']}")
            if s["finding_id"]:
                links.append(f"Finding:{s['finding_id']}")
            if s["job_id"]:
                links.append(f"Job:{s['job_id']}")
            links_str = ", ".join(links) if links else "-"

            title = s["title"] or s["filename"]
            if len(title) > 30:
                title = title[:27] + "..."

            table.add_row(
                str(idx),
                str(s["id"]),
                title,
                size_str,
                links_str,
                s["created_at"][:10] if s["created_at"] else "N/A",
            )

        console.print(table)
        click.echo()

        click.echo("  [v] View screenshot")
        click.echo("  [d] Delete screenshot")
        click.echo("  [q] ← Back")
        click.echo()

        choice = (
            click.prompt("Select option", type=str, default="q", show_default=False)
            .strip()
            .lower()
        )

        if choice == "q":
            return
        elif choice == "d":
            # Delete screenshot
            try:
                screenshot_id = click.prompt(
                    "  Enter screenshot ID to delete", type=int
                )
                screenshot = sm.get_screenshot(screenshot_id)
                if screenshot:
                    if click.confirm(
                        f"  Delete screenshot '{screenshot['title']}'?", default=False
                    ):
                        sm.delete_screenshot(screenshot_id)
                        click.echo(click.style("  ✓ Screenshot deleted", fg="green"))
                else:
                    click.echo(
                        click.style(f"  Screenshot {screenshot_id} not found", fg="red")
                    )
            except (ValueError, KeyboardInterrupt):
                pass
            click.pause()
        elif choice == "v":
            # View screenshot by number
            try:
                idx = click.prompt("  Enter screenshot # to view", type=int) - 1
                if 0 <= idx < len(screenshots):
                    s = screenshots[idx]
                    filepath = Path(s["filepath"])
                    if filepath.exists():
                        click.echo()
                        click.echo(click.style(f"  Opening: {s['title']}", fg="cyan"))
                        click.echo(f"  Location: {filepath}")
                        # Try to open with default viewer
                        try:
                            if sys.platform == "darwin":  # macOS
                                subprocess.run(["open", str(filepath)])
                            elif sys.platform.startswith("linux"):  # Linux
                                subprocess.run(["xdg-open", str(filepath)])
                            else:  # Windows
                                subprocess.run(["start", str(filepath)], shell=True)
                            click.echo(click.style("  ✓ Screenshot opened", fg="green"))
                        except Exception as e:
                            click.echo(
                                click.style(
                                    f"  Could not open screenshot: {e}", fg="yellow"
                                )
                            )
                            click.echo(f"  Manual path: {filepath}")
                    else:
                        click.echo(
                            click.style("  Screenshot file not found!", fg="red")
                        )
                else:
                    click.echo(click.style("  Invalid screenshot number", fg="red"))
            except (ValueError, click.Abort):
                pass
            click.pause()
        else:
            click.echo(click.style("  Invalid option", fg="red"))
            click.pause()
