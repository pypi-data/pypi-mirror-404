#!/usr/bin/env python3
"""
souleyez.ui.pending_chains_view

UI for reviewing and approving/rejecting pending chain operations.
This implements the "active orchestration" workflow where users can
review suggested follow-up scans before execution.
"""

import math
from typing import List, Set, Tuple

import click

from souleyez.core.pending_chains import (
    CHAIN_APPROVED,
    CHAIN_EXECUTED,
    CHAIN_PENDING,
    CHAIN_REJECTED,
    approve_all_pending,
    approve_chain,
    get_chain_stats,
    get_pending_chain,
    list_pending_chains,
    reject_all_pending,
    reject_chain,
)
from souleyez.core.tool_chaining import ToolChaining
from souleyez.ui.design_system import DesignSystem
from souleyez.ui.menu_components import StandardMenu


def manage_pending_chains(engagement_id: int = None):
    """Main interface for reviewing and approving pending chains.

    Args:
        engagement_id: Filter chains by engagement (None = show all)
    """
    chaining = ToolChaining()
    preview_page = 0  # Track current page for preview pagination

    while True:
        preview_page, total_pages = _display_pending_dashboard(
            chaining, preview_page, engagement_id
        )

        options = [
            {
                "number": 1,
                "label": "Review & Approve Chains",
                "description": "View pending chains and approve/reject them",
            },
            {
                "number": 2,
                "label": "Approve All Pending",
                "description": "Approve all pending chains at once",
            },
            {
                "number": 3,
                "label": "Reject All Pending",
                "description": "Reject all pending chains",
            },
            {
                "number": 4,
                "label": "Execute Approved",
                "description": "Run all approved chains now",
            },
            {
                "number": 5,
                "label": "Toggle Approval Mode",
                "description": "Switch between auto/approval modes",
            },
            {
                "number": 6,
                "label": "View Chain History",
                "description": "See executed and rejected chains",
            },
        ]

        # Build shortcuts for page navigation
        shortcuts = {"?": -3}  # Help shortcut
        if total_pages > 1:
            if preview_page > 0:
                shortcuts["p"] = -1  # Previous page
            if preview_page < total_pages - 1:
                shortcuts["n"] = -2  # Next page

        try:
            choice = StandardMenu.render(
                options,
                shortcuts=shortcuts,
                show_shortcuts=False,
                tip="Type ? for Active Orchestration help guide",
            )

            # Handle page navigation and help
            if choice == -1:  # Previous page
                preview_page = max(0, preview_page - 1)
                continue
            elif choice == -2:  # Next page
                preview_page = min(total_pages - 1, preview_page + 1)
                continue
            elif choice == -3:  # Help
                show_active_orchestration_help()
                continue
            elif choice == 0:
                return
            elif choice == 1:
                _review_pending_chains(chaining, engagement_id)
                preview_page = 0  # Reset page after review
            elif choice == 2:
                _approve_all_interactive(chaining, engagement_id)
                preview_page = 0
            elif choice == 3:
                _reject_all_interactive(engagement_id)
                preview_page = 0
            elif choice == 4:
                _execute_approved_chains(chaining, engagement_id)
            elif choice == 5:
                _toggle_approval_mode(chaining)
            elif choice == 6:
                _view_chain_history(engagement_id)

        except (KeyboardInterrupt, EOFError):
            return


def _display_pending_dashboard(
    chaining: ToolChaining, preview_page: int = 0, engagement_id: int = None
) -> Tuple[int, int]:
    """Display pending chains dashboard with paginated preview.

    Args:
        chaining: ToolChaining instance
        preview_page: Current page number for pagination
        engagement_id: Filter by engagement (None = show all)

    Returns tuple of (preview_page, total_pages).
    """
    PAGE_SIZE = 10

    DesignSystem.clear_screen()

    width = DesignSystem.get_terminal_width()

    # Header
    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            " PENDING CHAINS - ACTIVE ORCHESTRATION ".center(width - 2),
            bold=True,
            fg="cyan",
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    # Mode indicator
    if chaining.is_approval_mode():
        mode_text = click.style("APPROVAL MODE", fg="yellow", bold=True)
        mode_desc = "Chains queue for your review before execution"
    else:
        mode_text = click.style("AUTO MODE", fg="green", bold=True)
        mode_desc = "Chains execute automatically (use option [5] to enable approval)"

    click.echo(f"  Mode: {mode_text}")
    click.echo(click.style(f"  {mode_desc}", fg="bright_black"))
    click.echo()

    # Stats
    stats = get_chain_stats(engagement_id)
    pending = stats["pending"]
    approved = stats["approved"]
    rejected = stats["rejected"]
    executed = stats["executed"]

    click.echo(click.style("📊 CHAIN STATISTICS", bold=True, fg="cyan"))
    click.echo("─" * width)

    if pending > 0:
        click.echo(
            f"  ⏳ Pending:   {click.style(str(pending), fg='yellow', bold=True)} chains awaiting your decision"
        )
    else:
        click.echo(f"  ⏳ Pending:   {pending}")

    if approved > 0:
        click.echo(
            f"  ✓ Approved:  {click.style(str(approved), fg='green', bold=True)} ready to execute"
        )
    else:
        click.echo(f"  ✓ Approved:  {approved}")

    click.echo(f"  ✗ Rejected:  {rejected}")
    click.echo(f"  ▶ Executed:  {executed}")
    click.echo()

    # Preview of pending chains with pagination
    total_pages = 1  # Default when no pending chains
    if pending > 0:
        total_pages = max(1, math.ceil(pending / PAGE_SIZE))
        preview_page = min(preview_page, total_pages - 1)  # Clamp to valid range

        # Get chains for current page
        offset = preview_page * PAGE_SIZE
        pending_chains = list_pending_chains(
            status=CHAIN_PENDING,
            engagement_id=engagement_id,
            limit=PAGE_SIZE,
            offset=offset,
        )

        # Header with page info
        page_info = f"Page {preview_page + 1}/{total_pages}" if total_pages > 1 else ""
        click.echo(
            click.style("📋 PENDING CHAINS PREVIEW ", bold=True, fg="cyan")
            + click.style(page_info, fg="bright_black")
        )
        click.echo("─" * width)

        for chain in pending_chains:
            tool = chain.get("tool", "unknown")
            target = chain.get("target", "")[:30]
            priority = chain.get("priority", 5)

            pri_color = (
                "green" if priority >= 8 else "yellow" if priority >= 5 else "white"
            )
            click.echo(
                f"  • {click.style(tool.upper(), fg='magenta')} → {target} "
                f"(Priority: {click.style(str(priority), fg=pri_color)})"
            )

        # Page navigation hints
        if total_pages > 1:
            nav_hints = []
            if preview_page > 0:
                nav_hints.append("[p] Prev")
            if preview_page < total_pages - 1:
                nav_hints.append("[n] Next")
            if nav_hints:
                click.echo(click.style(f"  {' │ '.join(nav_hints)}", fg="bright_black"))
        click.echo()

    return preview_page, total_pages


def _review_pending_chains(chaining: ToolChaining, engagement_id: int = None):
    """Interactive review of pending chains with approve/reject actions.

    Args:
        chaining: ToolChaining instance
        engagement_id: Filter by engagement (None = show all)
    """
    from souleyez.ui.interactive_selector import interactive_select

    while True:
        # Get pending chains
        pending_chains = list_pending_chains(
            status=CHAIN_PENDING, engagement_id=engagement_id, limit=200
        )
        total_pending = len(pending_chains)

        if total_pending == 0:
            DesignSystem.clear_screen()
            click.echo("\n" + click.style("  No pending chains to review!", fg="green"))
            click.echo(
                click.style("  All chains have been processed.", fg="bright_black")
            )
            click.echo()
            click.pause()
            return

        # Convert chains to dicts for selector
        chain_items = []
        for chain in pending_chains:
            chain_items.append(
                {
                    "id": chain["id"],
                    "tool": chain.get("tool", ""),
                    "target": chain.get("target", ""),
                    "priority": chain.get("priority", 5),
                    "parent_id": chain.get("parent_job_id", "?"),
                    "args": chain.get("args", []),
                }
            )

        selected_ids: Set[int] = set()
        columns = [
            {"name": "#", "width": 5, "key": "id", "justify": "right"},
            {"name": "Tool", "width": 15, "key": "tool"},
            {"name": "Target", "width": 35, "key": "target"},
            {"name": "Priority", "width": 8, "key": "priority", "justify": "center"},
            {"name": "From", "width": 10, "key": "parent_id"},
        ]

        def format_chain_cell(item: dict, key: str) -> str:
            value = item.get(key)
            if key == "priority":
                pri = value or 5
                if pri >= 8:
                    return f"[green]{pri}[/green]"
                elif pri >= 5:
                    return f"[yellow]{pri}[/yellow]"
                return str(pri)
            if key == "parent_id":
                return f"Job #{value}"
            if key == "target":
                target = str(value) if value else ""
                return target[:35] if len(target) > 35 else target
            return str(value) if value else "-"

        # Run interactive selector
        interactive_select(
            items=chain_items,
            columns=columns,
            selected_ids=selected_ids,
            get_id=lambda c: c.get("id"),
            title=f"SELECT PENDING CHAINS ({total_pending} total)",
            format_cell=format_chain_cell,
            page_size=20,
        )

        # After selection, show action menu
        if not selected_ids:
            return  # User exited without selection

        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(" CHAIN ACTIONS ".center(width - 2), bold=True, fg="cyan")
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        click.echo(
            f"  Selected: {click.style(str(len(selected_ids)), fg='cyan', bold=True)} chain(s)"
        )
        click.echo()

        # Show selected chains summary
        for chain_id in list(selected_ids)[:10]:
            chain = next((c for c in chain_items if c["id"] == chain_id), None)
            if chain:
                click.echo(f"    #{chain_id}: {chain['tool']} → {chain['target'][:40]}")
        if len(selected_ids) > 10:
            click.echo(f"    ... and {len(selected_ids) - 10} more")
        click.echo()

        click.echo(
            "  " + click.style("[a]", fg="green", bold=True) + " Approve selected"
        )
        click.echo("  " + click.style("[r]", fg="red", bold=True) + " Reject selected")
        click.echo(
            "  "
            + click.style("[d]", fg="cyan", bold=True)
            + " View details (first selected)"
        )
        click.echo(
            "  " + click.style("[q]", fg="white", bold=True) + " Back to selection"
        )
        click.echo()

        try:
            choice = (
                click.prompt("Select option", default="0", show_default=False)
                .strip()
                .lower()
            )

            if choice == "q":
                continue  # Go back to selection
            elif choice == "a":
                approved = 0
                for chain_id in list(selected_ids):
                    if approve_chain(chain_id):
                        approved += 1
                click.echo(
                    click.style(f"\n  ✓ Approved {approved} chain(s)", fg="green")
                )
                click.pause()
                # Continue loop to show remaining
            elif choice == "r":
                rejected = 0
                for chain_id in list(selected_ids):
                    if reject_chain(chain_id):
                        rejected += 1
                click.echo(
                    click.style(f"\n  ✗ Rejected {rejected} chain(s)", fg="yellow")
                )
                click.pause()
                # Continue loop to show remaining
            elif choice == "d":
                first_id = list(selected_ids)[0]
                _show_chain_details(first_id)
                continue
            else:
                continue

        except (KeyboardInterrupt, EOFError):
            return


def _show_chain_details(chain_id: int):
    """Display detailed information about a chain."""
    chain = get_pending_chain(chain_id)
    if not chain:
        click.echo(click.style(f"\n  Chain #{chain_id} not found", fg="red"))
        click.pause()
        return

    DesignSystem.clear_screen()
    width = DesignSystem.get_terminal_width()

    # Header
    click.echo("\n" + "═" * width)
    click.echo(click.style(f"  CHAIN #{chain_id} DETAILS", bold=True, fg="cyan"))
    click.echo("═" * width)
    click.echo()

    # Status
    status = chain.get("status", "unknown")
    if status == CHAIN_PENDING:
        status_display = click.style("⏳ PENDING", fg="yellow", bold=True)
    elif status == CHAIN_APPROVED:
        status_display = click.style("✓ APPROVED", fg="green", bold=True)
    elif status == CHAIN_REJECTED:
        status_display = click.style("✗ REJECTED", fg="red", bold=True)
    elif status == CHAIN_EXECUTED:
        status_display = click.style("▶ EXECUTED", fg="blue", bold=True)
    else:
        status_display = status

    click.echo(f"  Status:       {status_display}")
    click.echo()

    # Tool info
    click.echo(click.style("  Tool Information:", bold=True))
    click.echo(
        f"    Tool:       {click.style(chain.get('tool', 'unknown').upper(), fg='magenta')}"
    )
    click.echo(f"    Target:     {chain.get('target', 'N/A')}")
    click.echo(f"    Priority:   {chain.get('priority', 5)}/10")
    click.echo()

    # Arguments
    args = chain.get("args", [])
    if args:
        click.echo(click.style("  Arguments:", bold=True))
        args_str = " ".join(str(a) for a in args)
        if len(args_str) > width - 10:
            args_str = args_str[: width - 13] + "..."
        click.echo(f"    {args_str}")
        click.echo()

    # Rule description
    rule_desc = chain.get("rule_description", "")
    if rule_desc:
        click.echo(click.style("  Triggered By:", bold=True))
        click.echo(f"    {rule_desc}")
        click.echo()

    # Timestamps
    click.echo(click.style("  Timeline:", bold=True))
    click.echo(f"    Created:    {chain.get('created_at', 'N/A')}")
    if chain.get("decided_at"):
        click.echo(f"    Decided:    {chain.get('decided_at')}")
    if chain.get("executed_at"):
        click.echo(f"    Executed:   {chain.get('executed_at')}")
    click.echo()

    # Parent job and resulting job
    click.echo(click.style("  Related Jobs:", bold=True))
    click.echo(f"    Parent Job: #{chain.get('parent_job_id', 'N/A')}")
    if chain.get("job_id"):
        click.echo(f"    Result Job: #{chain.get('job_id')}")
    click.echo()

    # Actions for pending chains
    if status == CHAIN_PENDING:
        click.echo("─" * width)
        click.echo("  [a] Approve    [r] Reject    [q] Back")
        click.echo()

        try:
            action = (
                click.prompt("Select option", default="0", show_default=False)
                .strip()
                .lower()
            )
            if action == "a":
                if approve_chain(chain_id):
                    click.echo(click.style("\n  ✓ Chain approved!", fg="green"))
                else:
                    click.echo(click.style("\n  Failed to approve chain", fg="red"))
                click.pause()
            elif action == "r":
                if reject_chain(chain_id):
                    click.echo(click.style("\n  ✗ Chain rejected", fg="yellow"))
                else:
                    click.echo(click.style("\n  Failed to reject chain", fg="red"))
                click.pause()
        except (KeyboardInterrupt, EOFError):
            pass
    else:
        click.pause()


def _approve_all_interactive(chaining: ToolChaining, engagement_id: int = None):
    """Approve all pending chains with confirmation.

    Args:
        chaining: ToolChaining instance
        engagement_id: Filter by engagement (None = show all)
    """
    stats = get_chain_stats(engagement_id)
    pending = stats["pending"]

    if pending == 0:
        click.echo(click.style("\n  No pending chains to approve!", fg="green"))
        click.pause()
        return

    click.echo()
    click.echo(
        f"  This will approve {click.style(str(pending), fg='yellow', bold=True)} pending chains."
    )
    click.echo()

    if click.confirm("  Approve all?", default=True):
        count = approve_all_pending(engagement_id)
        click.echo(click.style(f"\n  ✓ Approved {count} chains", fg="green"))

        # Offer to execute immediately
        if click.confirm("  Execute approved chains now?", default=True):
            job_ids = chaining.execute_approved_chains(engagement_id)
            click.echo(click.style(f"\n  ✓ Created {len(job_ids)} jobs", fg="green"))

    click.pause()


def _reject_all_interactive(engagement_id: int = None):
    """Reject all pending chains with confirmation.

    Args:
        engagement_id: Filter by engagement (None = show all)
    """
    stats = get_chain_stats(engagement_id)
    pending = stats["pending"]

    if pending == 0:
        click.echo(click.style("\n  No pending chains to reject!", fg="green"))
        click.pause()
        return

    click.echo()
    click.echo(
        click.style(
            f"  ⚠️  This will reject {pending} pending chains!", fg="red", bold=True
        )
    )
    click.echo()

    if click.confirm(click.style("  Are you sure?", fg="yellow"), default=False):
        count = reject_all_pending(engagement_id)
        click.echo(click.style(f"\n  ✗ Rejected {count} chains", fg="yellow"))

    click.pause()


def _execute_approved_chains(chaining: ToolChaining, engagement_id: int = None):
    """Execute all approved chains.

    Args:
        chaining: ToolChaining instance
        engagement_id: Filter by engagement (None = show all)
    """
    stats = get_chain_stats(engagement_id)
    approved = stats["approved"]

    if approved == 0:
        click.echo(click.style("\n  No approved chains to execute!", fg="yellow"))
        click.echo(
            click.style(
                "  Use option [1] to review and approve pending chains first.",
                fg="bright_black",
            )
        )
        click.pause()
        return

    click.echo()
    click.echo(
        f"  Ready to execute {click.style(str(approved), fg='green', bold=True)} approved chains."
    )
    click.echo()

    if click.confirm("  Execute now?", default=True):
        job_ids = chaining.execute_approved_chains(engagement_id)
        click.echo(click.style(f"\n  ✓ Created {len(job_ids)} jobs!", fg="green"))

        if job_ids:
            click.echo(f"  Job IDs: {', '.join(str(j) for j in job_ids[:10])}")
            if len(job_ids) > 10:
                click.echo(f"  ... and {len(job_ids) - 10} more")

    click.pause()


def _toggle_approval_mode(chaining: ToolChaining):
    """Toggle between auto and approval modes."""
    current = chaining.is_approval_mode()

    click.echo()
    if current:
        click.echo("  Current mode: " + click.style("APPROVAL", fg="yellow", bold=True))
        click.echo("  Switching to: " + click.style("AUTO", fg="green", bold=True))
        click.echo()
        click.echo("  In AUTO mode, chains execute immediately without approval.")
    else:
        click.echo("  Current mode: " + click.style("AUTO", fg="green", bold=True))
        click.echo("  Switching to: " + click.style("APPROVAL", fg="yellow", bold=True))
        click.echo()
        click.echo("  In APPROVAL mode, you'll review chains before they execute.")

    click.echo()

    if click.confirm("  Switch mode?", default=True):
        new_mode = chaining.toggle_approval_mode()
        if new_mode:
            click.echo(click.style("\n  ✓ APPROVAL MODE enabled", fg="yellow"))
            click.echo(
                click.style(
                    "    Chains will now queue for your approval.", fg="bright_black"
                )
            )
        else:
            click.echo(click.style("\n  ✓ AUTO MODE enabled", fg="green"))
            click.echo(
                click.style("    Chains will execute automatically.", fg="bright_black")
            )

    click.pause()


def _view_chain_history(engagement_id: int = None):
    """View executed and rejected chains.

    Args:
        engagement_id: Filter by engagement (None = show all)
    """
    page_size = 15
    current_page = 0
    filter_status = None  # None = all, or specific status

    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        # Get all non-pending chains
        all_chains = list_pending_chains(engagement_id=engagement_id, limit=500)
        history_chains = [c for c in all_chains if c.get("status") != CHAIN_PENDING]

        # Apply filter
        if filter_status:
            history_chains = [
                c for c in history_chains if c.get("status") == filter_status
            ]

        total = len(history_chains)

        if total == 0:
            click.echo("\n" + click.style("  No chain history yet!", fg="bright_black"))
            if filter_status:
                click.echo(
                    click.style(f"  (filtered by: {filter_status})", fg="bright_black")
                )
            click.echo()
            click.pause()
            return

        total_pages = max(1, math.ceil(total / page_size))
        current_page = min(current_page, total_pages - 1)

        # Header
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(" CHAIN HISTORY ".center(width - 2), bold=True, fg="cyan")
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Filter indicator
        filter_text = ""
        if filter_status == CHAIN_APPROVED:
            filter_text = click.style("  [Showing: Approved only]", fg="green")
        elif filter_status == CHAIN_REJECTED:
            filter_text = click.style("  [Showing: Rejected only]", fg="red")
        elif filter_status == CHAIN_EXECUTED:
            filter_text = click.style("  [Showing: Executed only]", fg="blue")

        page_info = f"Page {current_page + 1}/{total_pages} ({total} chains)"
        click.echo(
            click.style(f"📜 HISTORY ", bold=True, fg="cyan")
            + click.style(page_info, fg="bright_black")
            + filter_text
        )
        click.echo("─" * width)

        # Table header
        click.echo(
            click.style(
                f"  {'#':>4} │ {'Status':<10} │ {'Tool':<15} │ {'Target':<25} │ Decided",
                bold=True,
            )
        )
        click.echo("─" * width)

        # Calculate slice
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, total)

        for idx in range(start_idx, end_idx):
            chain = history_chains[idx]
            chain_id = chain["id"]

            # Status with color
            status = chain.get("status", "")
            if status == CHAIN_APPROVED:
                status_display = click.style("Approved", fg="green")
            elif status == CHAIN_REJECTED:
                status_display = click.style("Rejected", fg="red")
            elif status == CHAIN_EXECUTED:
                status_display = click.style("Executed", fg="blue")
            else:
                status_display = status

            tool = chain.get("tool", "")[:15]
            target = chain.get("target", "")[:25]
            decided = (
                chain.get("decided_at", "")[:10] if chain.get("decided_at") else "N/A"
            )

            click.echo(
                f"  {chain_id:>4} │ {status_display:<10} │ {tool:<15} │ {target:<25} │ {decided}"
            )

        click.echo("─" * width)
        click.echo()

        # Navigation
        nav_options = []
        if current_page > 0:
            nav_options.append("[p] Previous")
        if current_page < total_pages - 1:
            nav_options.append("[n] Next")
        nav_options.append("[q] Back")

        click.echo("  " + "  ".join(nav_options))

        # Filters
        filter_options = [
            "[a] Approved",
            "[r] Rejected",
            "[e] Executed",
            "[x] Clear filter",
        ]
        click.echo("  " + "  ".join(filter_options))
        click.echo()

        try:
            choice = (
                click.prompt("Select option", default="0", show_default=False)
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
                filter_status = CHAIN_APPROVED
                current_page = 0
            elif choice == "r":
                filter_status = CHAIN_REJECTED
                current_page = 0
            elif choice == "e":
                filter_status = CHAIN_EXECUTED
                current_page = 0
            elif choice == "x":
                filter_status = None
                current_page = 0

        except (KeyboardInterrupt, EOFError):
            return


def show_active_orchestration_help():
    """Display the Active Orchestration help guide with Rich formatting."""
    from rich import box
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    DesignSystem.clear_screen()

    # Header
    console.print()
    console.print(
        Panel(
            "[bold cyan]Active Orchestration Guide[/bold cyan]",
            box=box.DOUBLE,
            padding=(0, 2),
        )
    )
    console.print()

    # Overview section
    console.print("[bold yellow]▸ Overview[/bold yellow]")
    console.print("  " + "─" * 40)
    console.print()
    console.print("  Active Orchestration manages how auto-chained tools execute.")
    console.print("  You can review and approve chains before they run, or let them")
    console.print("  execute automatically based on your preferences.")
    console.print()

    # Modes section
    console.print("[bold yellow]▸ Execution Modes[/bold yellow]")
    console.print("  " + "─" * 40)
    console.print()
    console.print("  [bold green]AUTO MODE[/bold green]")
    console.print("    Chains execute immediately when triggered by tool results.")
    console.print("    Best for: Automated recon, CTF environments, trusted targets")
    console.print()
    console.print("  [bold yellow]APPROVAL MODE[/bold yellow]")
    console.print("    Chains queue for your review before execution.")
    console.print("    Best for: Production pentests, careful target control")
    console.print()

    # Statistics section
    console.print("[bold yellow]▸ Chain Statistics[/bold yellow]")
    console.print("  " + "─" * 40)
    console.print()
    console.print(
        "  [yellow]⏳ Pending[/yellow]   - Chains waiting for your approval/rejection"
    )
    console.print("  [green]✓ Approved[/green]  - Chains approved, ready to execute")
    console.print("  [red]✗ Rejected[/red]  - Chains you declined to run")
    console.print("  [blue]▶ Executed[/blue]  - Chains that have been run as jobs")
    console.print()

    # Actions section
    console.print("[bold yellow]▸ Available Actions[/bold yellow]")
    console.print("  " + "─" * 40)
    console.print()
    console.print(
        "  [magenta][1][/magenta] Review & Approve - Select chains individually to approve/reject"
    )
    console.print(
        "  [magenta][2][/magenta] Approve All - Approve all pending chains at once"
    )
    console.print("  [magenta][3][/magenta] Reject All - Reject all pending chains")
    console.print(
        "  [magenta][4][/magenta] Execute Approved - Run all approved chains as jobs"
    )
    console.print(
        "  [magenta][5][/magenta] Toggle Mode - Switch between AUTO and APPROVAL modes"
    )
    console.print(
        "  [magenta][6][/magenta] View History - See previously executed/rejected chains"
    )
    console.print()

    # Tips section
    console.print("[bold yellow]▸ Tips[/bold yellow]")
    console.print("  " + "─" * 40)
    console.print()
    console.print(
        "  • Review chain [bold]priority[/bold] - higher priority chains target more valuable findings"
    )
    console.print(
        "  • Check the [bold]parent job[/bold] to understand what triggered the chain"
    )
    console.print(
        "  • Use [bold]Reject All[/bold] to clear the queue if chains are stale"
    )
    console.print(
        "  • Toggle to [bold]APPROVAL MODE[/bold] before running sensitive scans"
    )
    console.print()

    # Footer
    console.print("[dim]Press any key to return...[/dim]")
    click.pause("")
