#!/usr/bin/env python3
"""
souleyez.ui.chain_rules_view

Chain rule management interface for auto-chaining configuration.
"""

import math
from typing import List

import click

from souleyez.core.tool_chaining import CATEGORY_ICONS, ChainRule, ToolChaining
from souleyez.ui.design_system import DesignSystem
from souleyez.ui.menu_components import StandardMenu


def manage_chain_rules():
    """Main interface for managing chain rules."""
    from souleyez.core.tool_chaining import ToolChaining

    chaining = ToolChaining()
    selected_tools = set()

    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        # Header
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " CHAIN RULE MANAGEMENT ".center(width - 2), bold=True, fg="cyan"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Stats
        total_rules = len(chaining.rules)
        enabled_rules = sum(1 for r in chaining.rules if r.enabled)
        disabled_rules = total_rules - enabled_rules

        # Group rules by trigger tool
        rules_by_tool = {}
        for rule in chaining.rules:
            if rule.trigger_tool not in rules_by_tool:
                rules_by_tool[rule.trigger_tool] = []
            rules_by_tool[rule.trigger_tool].append(rule)

        tool_list = sorted(rules_by_tool.keys())

        # Page info
        click.echo(
            f"  Total Rules: {total_rules}  │  ✓ Enabled: {enabled_rules}  │  ✗ Disabled: {disabled_rules}"
        )
        click.echo()

        # Table header with checkbox and category columns
        click.echo(
            click.style(
                f"    ○   {'Tool':<20} │ Enabled │ Disabled │ Total │  🎯  │  🏢  │  ⚙️  │ Status",
                bold=True,
            )
        )
        click.echo(" " + "─" * (width - 2))

        # Display tool groups
        for tool in tool_list:
            rules = rules_by_tool[tool]
            tool_enabled = sum(1 for r in rules if r.enabled)
            tool_disabled = len(rules) - tool_enabled
            total = len(rules)

            # Category counts
            ctf_count = sum(1 for r in rules if r.category == "ctf")
            enterprise_count = sum(1 for r in rules if r.category == "enterprise")
            general_count = sum(1 for r in rules if r.category == "general")

            # Checkbox for multi-select
            checkbox = "●" if tool in selected_tools else "○"

            # Icon based on status
            if tool_disabled == 0:
                icon = click.style("✓", fg="green", bold=True)
            elif tool_enabled == 0:
                icon = click.style("✗", fg="red")
            else:
                icon = click.style("◐", fg="yellow")

            # Tool name
            tool_display = f"{tool.upper():<20}"
            on_display = click.style(f"{tool_enabled:>7}", fg="green")
            off_display = (
                click.style(f"{tool_disabled:>8}", fg="yellow")
                if tool_disabled > 0
                else f"{tool_disabled:>8}"
            )

            # Category displays (dim if 0)
            ctf_display = (
                click.style(f"{ctf_count:>4}", fg="bright_black")
                if ctf_count == 0
                else f"{ctf_count:>4}"
            )
            ent_display = (
                click.style(f"{enterprise_count:>4}", fg="bright_black")
                if enterprise_count == 0
                else f"{enterprise_count:>4}"
            )
            gen_display = (
                click.style(f"{general_count:>4}", fg="bright_black")
                if general_count == 0
                else f"{general_count:>4}"
            )

            click.echo(
                f"    {checkbox}   {click.style(tool_display, fg='cyan')} │ {on_display} │ {off_display} │ {total:>5} │ {ctf_display} │ {ent_display} │ {gen_display} │   {icon}"
            )

        click.echo()

        # TIP line
        click.echo("  💡 TIP: Press 'i' for interactive mode")
        click.echo()

        # Brute-force warning
        brute_force_enabled = sum(
            1 for r in chaining.rules if r.target_tool == "hydra" and r.enabled
        )
        if brute_force_enabled > 0:
            click.echo(
                click.style(
                    f"  ⚠️  WARNING: {brute_force_enabled} brute-force rules are ACTIVE!",
                    fg="red",
                    bold=True,
                )
            )
            click.echo()

        # Separator + inline menu
        click.echo("─" * width)
        click.echo()
        click.echo("  [t] Toggle Rule - Enable or disable individual rules")
        click.echo("  [v] View Details - Deep dive into a specific rule")
        click.echo("  [f] Filter Status - Show only enabled or disabled rules")
        click.echo("  [e] Enable All - Turn on all chain rules")
        click.echo("  [d] Disable All - Safely disable all automatic chains")
        click.echo("  [r] Reset Defaults - Restore code-defined defaults")
        click.echo("  [?] Help - View help guide")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = (
                click.prompt("Select option", default="0", show_default=False)
                .strip()
                .lower()
            )

            if choice == "?":
                # Show auto-chaining help guide
                from souleyez.ui.interactive import show_auto_chaining_help

                show_auto_chaining_help()
                continue
            elif choice == "q":
                return
            elif choice == "i":
                # Interactive multi-select mode for tool groups
                _run_tool_groups_interactive(chaining, rules_by_tool, selected_tools)
            elif choice == "t":
                _toggle_rule_interactive(chaining)
            elif choice == "v":
                _view_rule_details(chaining)
            elif choice == "f":
                _filter_by_status(chaining)
            elif choice == "e":
                _enable_all_rules(chaining)
            elif choice == "d":
                _disable_all_rules(chaining)
            elif choice == "r":
                _reset_to_defaults(chaining)

        except (KeyboardInterrupt, EOFError):
            return


def _toggle_single_rule(chaining, rule_idx: int):
    """Toggle a single rule with safety warning for brute-force."""
    rule = chaining.rules[rule_idx]

    # Safety warning for enabling brute-force rules
    if not rule.enabled and rule.target_tool == "hydra":
        click.echo()
        click.echo(
            click.style(
                "⚠️  WARNING: You are about to enable a BRUTE-FORCE rule!",
                fg="red",
                bold=True,
            )
        )
        click.echo(
            click.style(
                "   This may cause account lockouts or trigger security alerts.",
                fg="red",
            )
        )
        click.echo()
        click.echo(f"   Rule: {rule.trigger_tool}→{rule.target_tool}")
        click.echo(f"   Description: {rule.description}")
        click.echo()

        if not click.confirm(
            click.style(
                "Are you sure you want to enable this rule?", fg="yellow", bold=True
            ),
            default=False,
        ):
            click.echo(click.style("\n✓ Rule toggle cancelled", fg="green"))
            click.pause()
            return

    # Toggle the rule
    rule.enabled = not rule.enabled
    chaining.save_rules()

    status = "ENABLED" if rule.enabled else "DISABLED"
    status_color = "green" if rule.enabled else "yellow"

    click.echo()
    click.echo(
        click.style(
            f"✓ Rule {status}: {rule.trigger_tool}→{rule.target_tool}",
            fg=status_color,
            bold=True,
        )
    )
    click.pause()


def _run_tool_groups_interactive(chaining, rules_by_tool: dict, selected_tools: set):
    """Run interactive selector for tool groups."""
    from souleyez.ui.interactive_selector import interactive_select

    # Convert tool groups to dicts for selector
    tool_items = []
    for tool in sorted(rules_by_tool.keys()):
        rules = rules_by_tool[tool]
        tool_enabled = sum(1 for r in rules if r.enabled)
        tool_disabled = len(rules) - tool_enabled

        # Status
        if tool_disabled == 0:
            status = "✓"
        elif tool_enabled == 0:
            status = "✗"
        else:
            status = "◐"

        tool_items.append(
            {
                "tool": tool,
                "enabled": tool_enabled,
                "disabled": tool_disabled,
                "total": len(rules),
                "status": status,
            }
        )

    columns = [
        {"name": "Tool", "width": 20, "key": "tool"},
        {"name": "Enabled", "width": 8, "key": "enabled", "justify": "right"},
        {"name": "Disabled", "width": 9, "key": "disabled", "justify": "right"},
        {"name": "Total", "width": 6, "key": "total", "justify": "right"},
        {"name": "Status", "width": 8, "key": "status"},
    ]

    def format_tool_cell(item: dict, key: str) -> str:
        value = item.get(key)
        if key == "tool":
            return value.upper()
        if key == "enabled":
            return f"[green]{value}[/green]"
        if key == "disabled":
            return f"[yellow]{value}[/yellow]" if value > 0 else str(value)
        if key == "status":
            if value == "✓":
                return "[green]✓[/green]"
            elif value == "✗":
                return "[red]✗[/red]"
            else:
                return "[yellow]◐[/yellow]"
        return str(value) if value is not None else "-"

    while True:
        interactive_select(
            items=tool_items,
            columns=columns,
            selected_ids=selected_tools,
            get_id=lambda t: t.get("tool"),
            title="SELECT TOOL GROUPS",
            format_cell=format_tool_cell,
        )

        if not selected_tools:
            return

        result = _tool_groups_bulk_action_menu(chaining, rules_by_tool, selected_tools)
        if result == "back":
            return
        elif result == "clear":
            selected_tools.clear()


def _tool_groups_bulk_action_menu(
    chaining, rules_by_tool: dict, selected_tools: set
) -> str:
    """Show bulk action menu for selected tool groups."""
    from rich.console import Console

    console = Console()

    if not selected_tools:
        return "continue"

    # Count rules in selected groups
    total_rules = sum(len(rules_by_tool.get(tool, [])) for tool in selected_tools)

    console.print()
    console.print(
        f"  [bold]Selected: {len(selected_tools)} tool group(s) ({total_rules} rules)[/bold]"
    )
    console.print("    \\[v] View All Rules")
    console.print("    \\[e] Enable All Rules")
    console.print("    \\[d] Disable All Rules")
    console.print("    \\[q] Back")
    console.print()

    try:
        action = (
            click.prompt("  Select option", default="0", show_default=False)
            .strip()
            .lower()
        )

        if action == "q":
            return "back"
        elif action == "v":
            # View all rules in selected groups
            DesignSystem.clear_screen()
            width = DesignSystem.get_terminal_width()

            click.echo("\n┌" + "─" * (width - 2) + "┐")
            click.echo(
                "│"
                + click.style(
                    " SELECTED TOOL GROUPS ".center(width - 2), bold=True, fg="cyan"
                )
                + "│"
            )
            click.echo("└" + "─" * (width - 2) + "┘")
            click.echo()

            for tool in sorted(selected_tools):
                rules = rules_by_tool.get(tool, [])
                click.echo(
                    click.style(
                        f"  {tool.upper()} ({len(rules)} rules)", bold=True, fg="cyan"
                    )
                )

                for rule in rules:
                    status = (
                        click.style("ON", fg="green")
                        if rule.enabled
                        else click.style("OFF", fg="red")
                    )
                    warning = (
                        click.style(" ⚠️", fg="red")
                        if rule.target_tool == "hydra"
                        else ""
                    )
                    click.echo(
                        f"    → {rule.target_tool}{warning} | {rule.trigger_condition} | {status}"
                    )

                click.echo()

            click.pause()
            return "continue"
        elif action == "e":
            # Enable all rules in selected groups
            enabled = 0
            for tool in selected_tools:
                for rule in rules_by_tool.get(tool, []):
                    if not rule.enabled:
                        rule.enabled = True
                        enabled += 1

            chaining.save_rules()
            click.echo(
                click.style(
                    f"\n✓ Enabled {enabled} rule(s) in {len(selected_tools)} group(s)",
                    fg="green",
                )
            )
            click.pause()
            return "clear"
        elif action == "d":
            # Disable all rules in selected groups
            disabled = 0
            for tool in selected_tools:
                for rule in rules_by_tool.get(tool, []):
                    if rule.enabled:
                        rule.enabled = False
                        disabled += 1

            chaining.save_rules()
            click.echo(
                click.style(
                    f"\n✓ Disabled {disabled} rule(s) in {len(selected_tools)} group(s)",
                    fg="yellow",
                )
            )
            click.pause()
            return "clear"

    except (KeyboardInterrupt, EOFError):
        pass

    return "continue"


def _display_rules_dashboard(chaining: ToolChaining):
    """Display main dashboard with collapsed tool summary."""
    DesignSystem.clear_screen()

    width = DesignSystem.get_terminal_width()

    # Header
    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" CHAIN RULE MANAGEMENT ".center(width - 2), bold=True, fg="cyan")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    # Stats
    total_rules = len(chaining.rules)
    enabled_rules = sum(1 for r in chaining.rules if r.enabled)
    disabled_rules = total_rules - enabled_rules

    # Categorize rules
    brute_force_rules = [r for r in chaining.rules if r.target_tool == "hydra"]
    brute_force_disabled = [r for r in brute_force_rules if not r.enabled]
    brute_force_enabled = len(brute_force_rules) - len(brute_force_disabled)

    click.echo(click.style("📊 OVERVIEW", bold=True, fg="cyan"))
    click.echo("─" * width)
    click.echo(f"  Total Rules:     {total_rules}")
    click.echo(
        f"  ✓ Enabled:       {click.style(str(enabled_rules), fg='green', bold=True)}"
    )
    click.echo(f"  ✗ Disabled:      {click.style(str(disabled_rules), fg='yellow')}")
    click.echo()

    # Group rules by trigger tool
    rules_by_tool = {}
    for rule in chaining.rules:
        if rule.trigger_tool not in rules_by_tool:
            rules_by_tool[rule.trigger_tool] = []
        rules_by_tool[rule.trigger_tool].append(rule)

    # Display collapsed tool summary as table (FIRST)
    click.echo(
        click.style("⚡ TOOL GROUPS", bold=True, fg="cyan")
        + click.style("  Use option [3] to expand", fg="bright_black")
    )
    click.echo("─" * width)
    click.echo(
        click.style(
            f"     {'Tool':<20} │ Enabled │ Disabled │ Total │  🎯  │  🏢  │  ⚙️  │ Status",
            bold=True,
        )
    )
    click.echo("─" * width)

    for tool in sorted(rules_by_tool.keys()):
        rules = rules_by_tool[tool]
        tool_enabled = sum(1 for r in rules if r.enabled)
        tool_disabled = len(rules) - tool_enabled
        total = len(rules)

        # Category counts
        ctf_count = sum(1 for r in rules if r.category == "ctf")
        enterprise_count = sum(1 for r in rules if r.category == "enterprise")
        general_count = sum(1 for r in rules if r.category == "general")

        # Icon based on status
        if tool_disabled == 0:
            icon = click.style("✓", fg="green", bold=True)
        elif tool_enabled == 0:
            icon = click.style("✗", fg="red")
        else:
            icon = click.style("◐", fg="yellow")  # Partial

        # Tool name
        tool_display = f"{tool.upper():<20}"
        on_display = click.style(f"{tool_enabled:>7}", fg="green")
        off_display = (
            click.style(f"{tool_disabled:>8}", fg="yellow")
            if tool_disabled > 0
            else f"{tool_disabled:>8}"
        )

        # Category displays (dim if 0)
        ctf_display = (
            click.style(f"{ctf_count:>4}", fg="bright_black")
            if ctf_count == 0
            else f"{ctf_count:>4}"
        )
        ent_display = (
            click.style(f"{enterprise_count:>4}", fg="bright_black")
            if enterprise_count == 0
            else f"{enterprise_count:>4}"
        )
        gen_display = (
            click.style(f"{general_count:>4}", fg="bright_black")
            if general_count == 0
            else f"{general_count:>4}"
        )

        click.echo(
            f"     {click.style(tool_display, fg='cyan')} │ {on_display} │ {off_display} │ {total:>5} │ {ctf_display} │ {ent_display} │ {gen_display} │   {icon}"
        )

    click.echo("─" * width)
    click.echo()

    # Highlight disabled security-sensitive rules (AFTER Tool Groups)
    if brute_force_disabled:
        click.echo(
            click.style(
                "🔐 BRUTE-FORCE RULES (Disabled by default for safety)",
                bold=True,
                fg="yellow",
            )
        )
        click.echo("─" * width)
        for rule in brute_force_disabled:
            click.echo(
                f"  ✗ {click.style(rule.trigger_tool.upper(), fg='cyan')} → "
                f"{click.style('Hydra', fg='magenta')} | {rule.trigger_condition}"
            )
            click.echo(click.style(f"    {rule.description}", fg="bright_black"))
        click.echo()

    if brute_force_enabled > 0:
        click.echo(
            click.style(
                f"⚠️  WARNING: {brute_force_enabled} brute-force rules are ACTIVE!",
                fg="red",
                bold=True,
            )
        )
        click.echo(
            click.style(
                "   These may trigger account lockouts. Review option [1] to disable.",
                fg="red",
            )
        )
        click.echo()


def _rules_bulk_action_menu(chaining, selected_ids: set) -> str:
    """Show bulk action menu for selected rules."""
    from rich.console import Console

    console = Console()

    selected_rules = [
        (idx, chaining.rules[idx]) for idx in selected_ids if idx < len(chaining.rules)
    ]

    if not selected_rules:
        return "continue"

    # Check for brute-force rules in selection
    has_hydra = any(rule.target_tool == "hydra" for _, rule in selected_rules)
    hydra_warning = " ⚠️" if has_hydra else ""

    console.print()
    console.print(
        f"  [bold]Selected: {len(selected_rules)} rule(s){hydra_warning}[/bold]"
    )
    console.print("    \\[v] View All Rules")
    console.print("    \\[e] Enable All Rules")
    console.print("    \\[d] Disable All Rules")
    console.print("    \\[q] Back")
    console.print()

    try:
        action = (
            click.prompt("  Select option", default="0", show_default=False)
            .strip()
            .lower()
        )

        if action == "q":
            return "back"
        elif action == "v":
            # View all selected rules (show details)
            DesignSystem.clear_screen()
            width = DesignSystem.get_terminal_width()

            click.echo("\n┌" + "─" * (width - 2) + "┐")
            click.echo(
                "│"
                + click.style(
                    " SELECTED RULES ".center(width - 2), bold=True, fg="cyan"
                )
                + "│"
            )
            click.echo("└" + "─" * (width - 2) + "┘")
            click.echo()

            for idx, rule in selected_rules:
                status = (
                    click.style("ON", fg="green")
                    if rule.enabled
                    else click.style("OFF", fg="red")
                )
                warning = (
                    click.style(" ⚠️", fg="red") if rule.target_tool == "hydra" else ""
                )
                cat_icon = CATEGORY_ICONS.get(rule.category, "⚙️")

                click.echo(
                    f"  [{idx + 1}] {rule.trigger_tool} → {rule.target_tool}{warning}"
                )
                click.echo(f"      Condition: {rule.trigger_condition}")
                click.echo(
                    f"      Priority: {rule.priority}  Category: {cat_icon}  Status: {status}"
                )
                if rule.description:
                    click.echo(
                        click.style(f"      {rule.description}", fg="bright_black")
                    )
                click.echo()

            click.pause()
            return "continue"
        elif action == "e":
            # Enable selected - warn about brute-force
            enabling_hydra = any(
                not chaining.rules[idx].enabled
                and chaining.rules[idx].target_tool == "hydra"
                for idx in selected_ids
            )

            if enabling_hydra:
                click.echo()
                click.echo(
                    click.style(
                        "⚠️  WARNING: Selection includes BRUTE-FORCE rules!",
                        fg="red",
                        bold=True,
                    )
                )
                if not click.confirm(
                    click.style("Proceed with enabling?", fg="yellow"), default=False
                ):
                    click.echo(click.style("\n✓ Enable cancelled", fg="green"))
                    click.pause()
                    return "continue"

            enabled = 0
            for idx in selected_ids:
                if not chaining.rules[idx].enabled:
                    chaining.rules[idx].enabled = True
                    enabled += 1

            chaining.save_rules()
            click.echo(click.style(f"\n✓ Enabled {enabled} rule(s)", fg="green"))
            click.pause()
            return "clear"
        elif action == "d":
            # Disable selected
            disabled = 0
            for idx in selected_ids:
                if chaining.rules[idx].enabled:
                    chaining.rules[idx].enabled = False
                    disabled += 1

            chaining.save_rules()
            click.echo(click.style(f"\n✓ Disabled {disabled} rule(s)", fg="yellow"))
            click.pause()
            return "clear"

    except (KeyboardInterrupt, EOFError):
        pass

    return "continue"


def _toggle_rule_interactive(chaining: ToolChaining):
    """Interactive rule toggle with paginated table view."""
    from souleyez.core.tool_chaining import (
        CATEGORY_CTF,
        CATEGORY_ENTERPRISE,
        CATEGORY_GENERAL,
    )

    page_size = 20
    current_page = 0
    filter_status = None  # None=all, True=enabled only, False=disabled only
    filter_category = None  # None=all, or specific category string
    selected_rule_ids = set()  # Track selected rules for multi-select

    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        # Apply filters
        filtered_rules = list(enumerate(chaining.rules))  # (original_idx, rule)
        if filter_status is not None:
            if filter_status:
                filtered_rules = [(i, r) for i, r in filtered_rules if r.enabled]
            else:
                filtered_rules = [(i, r) for i, r in filtered_rules if not r.enabled]
        if filter_category is not None:
            filtered_rules = [
                (i, r) for i, r in filtered_rules if r.category == filter_category
            ]

        total_filtered = len(filtered_rules)
        total_pages = max(1, math.ceil(total_filtered / page_size))
        current_page = min(
            current_page, total_pages - 1
        )  # Adjust if filter reduced pages

        # Header box
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(" TOGGLE CHAIN RULE ".center(width - 2), bold=True, fg="cyan")
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Overview stats
        total_rules = len(chaining.rules)
        enabled_rules = sum(1 for r in chaining.rules if r.enabled)
        disabled_rules = total_rules - enabled_rules
        brute_force_rules = sum(1 for r in chaining.rules if r.target_tool == "hydra")
        ctf_rules = sum(1 for r in chaining.rules if r.category == CATEGORY_CTF)
        enterprise_rules = sum(
            1 for r in chaining.rules if r.category == CATEGORY_ENTERPRISE
        )
        general_rules = sum(1 for r in chaining.rules if r.category == CATEGORY_GENERAL)

        click.echo(click.style("📊 OVERVIEW", bold=True, fg="cyan"))
        click.echo("─" * width)
        click.echo(
            f"  Total: {total_rules}  │  {click.style(str(enabled_rules), fg='green')} enabled  │  {click.style(str(disabled_rules), fg='yellow')} disabled  │  {click.style(str(brute_force_rules), fg='red')} brute-force  │  🎯 {ctf_rules}  🏢 {enterprise_rules}  ⚙️ {general_rules}"
        )
        click.echo()

        # Page info with filter indicator
        filter_parts = []
        if filter_status is True:
            filter_parts.append(click.style("Enabled", fg="green"))
        elif filter_status is False:
            filter_parts.append(click.style("Disabled", fg="yellow"))
        if filter_category is not None:
            cat_icon = CATEGORY_ICONS.get(filter_category, "⚙️")
            cat_name = {
                "ctf": "CTF",
                "enterprise": "Enterprise",
                "general": "General",
            }.get(filter_category, filter_category)
            filter_parts.append(f"{cat_icon} {cat_name}")
        filter_text = (
            click.style(f"  [Filter: {', '.join(filter_parts)}]", fg="bright_black")
            if filter_parts
            else ""
        )
        page_info = f"Page {current_page + 1}/{total_pages}"
        click.echo(
            click.style(f"📋 RULES ", bold=True, fg="cyan")
            + click.style(page_info, fg="bright_black")
            + filter_text
        )
        click.echo("─" * width)

        # Table header - with checkbox column and Fired column
        click.echo(
            click.style(
                f"  ○ │    # │ {'Trigger':<22} │ {'Target':<22} │ {'Condition':<30} │ Priority │ Category │ Status │ Fired",
                bold=True,
            )
        )
        click.echo("─" * width)

        # Calculate slice for current page
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, total_filtered)

        # Display rules for current page
        for idx in range(start_idx, end_idx):
            original_idx, rule = filtered_rules[idx]
            rule_num = original_idx + 1  # Show original rule number for toggling

            # Checkbox for multi-select
            checkbox = "●" if original_idx in selected_rule_ids else "○"

            # Use full names (no truncation)
            trigger = (
                rule.trigger_tool[:22]
                if len(rule.trigger_tool) <= 22
                else rule.trigger_tool[:19] + "..."
            )
            target = (
                rule.target_tool[:22]
                if len(rule.target_tool) <= 22
                else rule.target_tool[:19] + "..."
            )
            condition = (
                rule.trigger_condition[:30]
                if len(rule.trigger_condition) <= 30
                else rule.trigger_condition[:27] + "..."
            )

            # Status with color and brute-force warning
            if rule.target_tool == "hydra":
                status = (
                    click.style(" ON", fg="green") + click.style(" ⚠️", fg="red")
                    if rule.enabled
                    else click.style("OFF", fg="red") + click.style(" ⚠️", fg="red")
                )
            else:
                status = (
                    click.style(" ON", fg="green")
                    if rule.enabled
                    else click.style("OFF", fg="red")
                )

            # Priority with color (8-char width to match "Priority" header)
            pri_color = (
                "green"
                if rule.priority >= 8
                else "yellow" if rule.priority >= 5 else "white"
            )
            priority = click.style(f"{rule.priority:>8}", fg=pri_color)

            # Category icon (8-char width to match "Category" header)
            cat_icon = CATEGORY_ICONS.get(rule.category, "⚙️")

            # Trigger count with color
            fired_count = rule.trigger_count if hasattr(rule, "trigger_count") else 0
            fired_display = (
                click.style(f"{fired_count:>5}", fg="green")
                if fired_count > 0
                else click.style(f"{fired_count:>5}", fg="bright_black")
            )

            click.echo(
                f"  {checkbox} │ {rule_num:>4} │ {trigger:<22} │ {target:<22} │ {condition:<30} │ {priority} │    {cat_icon}    │ {status} │ {fired_display}"
            )

        click.echo("─" * width)
        click.echo()

        # TIP line (matching pattern from other views)
        click.echo("  💡 TIP: Press 'i' for interactive mode")
        if total_pages > 1:
            click.echo("  n/p: Next/Previous page")
        click.echo()

        # Separator + inline menu
        click.echo("─" * width)
        click.echo()
        click.echo("  [#] Toggle rule")
        click.echo("  [e] Enabled only - Filter by enabled rules")
        click.echo("  [d] Disabled only - Filter by disabled rules")
        click.echo("  [c] Category - Filter by category")
        if filter_status is not None or filter_category is not None:
            click.echo("  [a] Clear filters")
        click.echo("  [q] Back")
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
            elif choice == "e":
                filter_status = True
                current_page = 0
            elif choice == "d":
                filter_status = False
                current_page = 0
            elif choice == "a":
                filter_status = None
                filter_category = None
                current_page = 0
            elif choice == "c":
                # Category filter submenu
                click.echo()
                click.echo(click.style("  Select category:", bold=True))
                click.echo(f"    [1] 🎯 CTF - Lab/learning scenarios")
                click.echo(f"    [2] 🏢 Enterprise - Real-world testing")
                click.echo(f"    [3] ⚙️  General - Standard recon")
                click.echo(f"    [q] Cancel")
                cat_choice = click.prompt(
                    "  Select option", default="0", show_default=False
                ).strip()
                if cat_choice == "1":
                    filter_category = CATEGORY_CTF
                    current_page = 0
                elif cat_choice == "2":
                    filter_category = CATEGORY_ENTERPRISE
                    current_page = 0
                elif cat_choice == "3":
                    filter_category = CATEGORY_GENERAL
                    current_page = 0
            elif choice.isdigit():
                rule_idx = int(choice) - 1
                if 0 <= rule_idx < len(chaining.rules):
                    rule = chaining.rules[rule_idx]

                    # Safety warning for enabling brute-force rules
                    if not rule.enabled and rule.target_tool == "hydra":
                        click.echo()
                        click.echo(
                            click.style(
                                "⚠️  WARNING: You are about to enable a BRUTE-FORCE rule!",
                                fg="red",
                                bold=True,
                            )
                        )
                        click.echo(
                            click.style(
                                "   This may cause account lockouts or trigger security alerts.",
                                fg="red",
                            )
                        )
                        click.echo()
                        click.echo(f"   Rule: {rule.trigger_tool}→{rule.target_tool}")
                        click.echo(f"   Description: {rule.description}")
                        click.echo()

                        if not click.confirm(
                            click.style(
                                "Are you sure you want to enable this rule?",
                                fg="yellow",
                                bold=True,
                            ),
                            default=False,
                        ):
                            click.echo(
                                click.style("\n✓ Rule toggle cancelled", fg="green")
                            )
                            click.pause()
                            continue

                    # Toggle the rule
                    rule.enabled = not rule.enabled
                    chaining.save_rules()  # Persist the change

                    status = "ENABLED" if rule.enabled else "DISABLED"
                    status_color = "green" if rule.enabled else "yellow"

                    click.echo()
                    click.echo(
                        click.style(
                            f"✓ Rule {status}: {rule.trigger_tool}→{rule.target_tool}",
                            fg=status_color,
                            bold=True,
                        )
                    )

                    if rule.enabled:
                        click.echo(
                            click.style(
                                "  Note: Worker will apply changes on next job completion",
                                fg="bright_black",
                            )
                        )

                    click.pause()
                else:
                    click.echo(click.style("\n✗ Invalid rule number", fg="red"))
                    click.pause()
            elif choice == "i":
                # Interactive multi-select mode (respects current filters)
                from souleyez.ui.interactive_selector import interactive_select

                while True:
                    # Convert FILTERED rules to dicts for selector
                    rule_items = []
                    for original_idx, rule in filtered_rules:
                        rule_items.append(
                            {
                                "idx": original_idx,
                                "trigger_tool": rule.trigger_tool,
                                "target_tool": rule.target_tool,
                                "condition": rule.trigger_condition,
                                "enabled": rule.enabled,
                                "priority": rule.priority,
                                "category": rule.category,
                            }
                        )

                    columns = [
                        {"name": "#", "width": 5, "key": "idx", "justify": "right"},
                        {"name": "Trigger", "width": 18, "key": "trigger_tool"},
                        {"name": "Target", "width": 18, "key": "target_tool"},
                        {"name": "Condition", "width": 25, "key": "condition"},
                        {"name": "Cat", "width": 5, "key": "category"},
                        {"name": "Status", "width": 8, "key": "enabled"},
                    ]

                    def format_rule_cell(item: dict, key: str) -> str:
                        value = item.get(key)
                        if key == "enabled":
                            return "[green]ON[/green]" if value else "[red]OFF[/red]"
                        if key == "idx":
                            return str(value + 1)  # 1-indexed for display
                        if key == "category":
                            return CATEGORY_ICONS.get(value, "⚙️")
                        return str(value) if value else "-"

                    # Build title with filter info
                    title = "SELECT RULES"
                    if filter_category or filter_status is not None:
                        filter_info = []
                        if filter_category:
                            cat_name = {
                                "ctf": "CTF",
                                "enterprise": "Enterprise",
                                "general": "General",
                            }.get(filter_category, "")
                            filter_info.append(
                                f"{CATEGORY_ICONS.get(filter_category, '')} {cat_name}"
                            )
                        if filter_status is True:
                            filter_info.append("Enabled")
                        elif filter_status is False:
                            filter_info.append("Disabled")
                        title = f'SELECT RULES ({", ".join(filter_info)})'

                    interactive_select(
                        items=rule_items,
                        columns=columns,
                        selected_ids=selected_rule_ids,
                        get_id=lambda r: r.get("idx"),
                        title=title,
                        format_cell=format_rule_cell,
                    )

                    if not selected_rule_ids:
                        break

                    result = _rules_bulk_action_menu(chaining, selected_rule_ids)
                    if result == "back":
                        break
                    elif result == "clear":
                        selected_rule_ids.clear()
        except (KeyboardInterrupt, EOFError):
            return


def _view_rule_details(chaining: ToolChaining):
    """Display detailed information about a rule with paginated table view."""
    from souleyez.core.tool_chaining import (
        CATEGORY_CTF,
        CATEGORY_ENTERPRISE,
        CATEGORY_GENERAL,
    )

    page_size = 20
    current_page = 0
    filter_status = None  # None=all, True=enabled only, False=disabled only
    filter_category = None  # None=all, or specific category string
    selected_rule_ids = set()  # Track selected rules for multi-select

    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        # Apply filters
        filtered_rules = list(enumerate(chaining.rules))  # (original_idx, rule)
        if filter_status is not None:
            if filter_status:
                filtered_rules = [(i, r) for i, r in filtered_rules if r.enabled]
            else:
                filtered_rules = [(i, r) for i, r in filtered_rules if not r.enabled]
        if filter_category is not None:
            filtered_rules = [
                (i, r) for i, r in filtered_rules if r.category == filter_category
            ]

        total_filtered = len(filtered_rules)
        total_pages = max(1, math.ceil(total_filtered / page_size))
        current_page = min(
            current_page, total_pages - 1
        )  # Adjust if filter reduced pages

        # Header box
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(" VIEW RULE DETAILS ".center(width - 2), bold=True, fg="cyan")
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Overview stats
        total_rules = len(chaining.rules)
        enabled_rules = sum(1 for r in chaining.rules if r.enabled)
        disabled_rules = total_rules - enabled_rules
        brute_force_rules = sum(1 for r in chaining.rules if r.target_tool == "hydra")
        ctf_rules = sum(1 for r in chaining.rules if r.category == CATEGORY_CTF)
        enterprise_rules = sum(
            1 for r in chaining.rules if r.category == CATEGORY_ENTERPRISE
        )
        general_rules = sum(1 for r in chaining.rules if r.category == CATEGORY_GENERAL)

        click.echo(click.style("📊 OVERVIEW", bold=True, fg="cyan"))
        click.echo("─" * width)
        click.echo(
            f"  Total: {total_rules}  │  {click.style(str(enabled_rules), fg='green')} enabled  │  {click.style(str(disabled_rules), fg='yellow')} disabled  │  {click.style(str(brute_force_rules), fg='red')} brute-force  │  🎯 {ctf_rules}  🏢 {enterprise_rules}  ⚙️ {general_rules}"
        )
        click.echo()

        # Page info with filter indicator
        filter_parts = []
        if filter_status is True:
            filter_parts.append(click.style("Enabled", fg="green"))
        elif filter_status is False:
            filter_parts.append(click.style("Disabled", fg="yellow"))
        if filter_category is not None:
            cat_icon = CATEGORY_ICONS.get(filter_category, "⚙️")
            cat_name = {
                "ctf": "CTF",
                "enterprise": "Enterprise",
                "general": "General",
            }.get(filter_category, filter_category)
            filter_parts.append(f"{cat_icon} {cat_name}")
        filter_text = (
            click.style(f"  [Filter: {', '.join(filter_parts)}]", fg="bright_black")
            if filter_parts
            else ""
        )
        page_info = f"Page {current_page + 1}/{total_pages}"
        click.echo(
            click.style(f"📋 RULES ", bold=True, fg="cyan")
            + click.style(page_info, fg="bright_black")
            + filter_text
        )
        click.echo("─" * width)

        # Table header - with checkbox column and Fired column
        click.echo(
            click.style(
                f"  ○ │    # │ {'Trigger':<22} │ {'Target':<22} │ {'Condition':<30} │ Priority │ Category │ Status │ Fired",
                bold=True,
            )
        )
        click.echo("─" * width)

        # Calculate slice for current page
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, total_filtered)

        # Display rules for current page
        for idx in range(start_idx, end_idx):
            original_idx, rule = filtered_rules[idx]
            rule_num = original_idx + 1  # Show original rule number

            # Checkbox for multi-select
            checkbox = "●" if original_idx in selected_rule_ids else "○"

            # Use full names (no truncation)
            trigger = (
                rule.trigger_tool[:22]
                if len(rule.trigger_tool) <= 22
                else rule.trigger_tool[:19] + "..."
            )
            target = (
                rule.target_tool[:22]
                if len(rule.target_tool) <= 22
                else rule.target_tool[:19] + "..."
            )
            condition = (
                rule.trigger_condition[:30]
                if len(rule.trigger_condition) <= 30
                else rule.trigger_condition[:27] + "..."
            )

            # Status with color
            status = (
                click.style(" ON", fg="green")
                if rule.enabled
                else click.style("OFF", fg="red")
            )

            # Priority with color (8-char width to match "Priority" header)
            pri_color = (
                "green"
                if rule.priority >= 8
                else "yellow" if rule.priority >= 5 else "white"
            )
            priority = click.style(f"{rule.priority:>8}", fg=pri_color)

            # Category icon (8-char width to match "Category" header)
            cat_icon = CATEGORY_ICONS.get(rule.category, "⚙️")

            # Trigger count with color
            fired_count = rule.trigger_count if hasattr(rule, "trigger_count") else 0
            fired_display = (
                click.style(f"{fired_count:>5}", fg="green")
                if fired_count > 0
                else click.style(f"{fired_count:>5}", fg="bright_black")
            )

            click.echo(
                f"  {checkbox} │ {rule_num:>4} │ {trigger:<22} │ {target:<22} │ {condition:<30} │ {priority} │    {cat_icon}    │ {status} │ {fired_display}"
            )

        click.echo("─" * width)
        click.echo()

        # TIP line (matching pattern from other views)
        click.echo("  💡 TIP: Press 'i' for interactive mode")
        if total_pages > 1:
            click.echo("  n/p: Next/Previous page")
        click.echo()

        # Separator + inline menu
        click.echo("─" * width)
        click.echo()
        click.echo("  [#] View rule details")
        click.echo("  [e] Enabled only - Filter by enabled rules")
        click.echo("  [d] Disabled only - Filter by disabled rules")
        click.echo("  [c] Category - Filter by category")
        if filter_status is not None or filter_category is not None:
            click.echo("  [a] Clear filters")
        click.echo("  [q] Back")
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
            elif choice == "e":
                filter_status = True
                current_page = 0
            elif choice == "d":
                filter_status = False
                current_page = 0
            elif choice == "a":
                filter_status = None
                filter_category = None
                current_page = 0
            elif choice == "c":
                # Category filter submenu
                click.echo()
                click.echo(click.style("  Select category:", bold=True))
                click.echo(f"    [1] 🎯 CTF - Lab/learning scenarios")
                click.echo(f"    [2] 🏢 Enterprise - Real-world testing")
                click.echo(f"    [3] ⚙️  General - Standard recon")
                click.echo(f"    [q] Cancel")
                cat_choice = click.prompt(
                    "  Select option", default="0", show_default=False
                ).strip()
                if cat_choice == "1":
                    filter_category = CATEGORY_CTF
                    current_page = 0
                elif cat_choice == "2":
                    filter_category = CATEGORY_ENTERPRISE
                    current_page = 0
                elif cat_choice == "3":
                    filter_category = CATEGORY_GENERAL
                    current_page = 0
            elif choice.isdigit():
                # View rule details by number
                rule_idx = int(choice) - 1
                if 0 <= rule_idx < len(chaining.rules):
                    _show_single_rule_details(chaining.rules[rule_idx], width, chaining)
                else:
                    click.echo(click.style("\n✗ Invalid rule number", fg="red"))
                    click.pause()
            elif choice == "i":
                # Interactive multi-select mode (respects current filters)
                from souleyez.ui.interactive_selector import interactive_select

                while True:
                    # Convert FILTERED rules to dicts for selector
                    rule_items = []
                    for original_idx, rule in filtered_rules:
                        rule_items.append(
                            {
                                "idx": original_idx,
                                "trigger_tool": rule.trigger_tool,
                                "target_tool": rule.target_tool,
                                "condition": rule.trigger_condition,
                                "enabled": rule.enabled,
                                "priority": rule.priority,
                                "category": rule.category,
                            }
                        )

                    columns = [
                        {"name": "#", "width": 5, "key": "idx", "justify": "right"},
                        {"name": "Trigger", "width": 18, "key": "trigger_tool"},
                        {"name": "Target", "width": 18, "key": "target_tool"},
                        {"name": "Condition", "width": 25, "key": "condition"},
                        {"name": "Cat", "width": 5, "key": "category"},
                        {"name": "Status", "width": 8, "key": "enabled"},
                    ]

                    def format_rule_cell(item: dict, key: str) -> str:
                        value = item.get(key)
                        if key == "enabled":
                            return "[green]ON[/green]" if value else "[red]OFF[/red]"
                        if key == "idx":
                            return str(value + 1)  # 1-indexed for display
                        if key == "category":
                            return CATEGORY_ICONS.get(value, "⚙️")
                        return str(value) if value else "-"

                    # Build title with filter info
                    title = "SELECT RULE TO VIEW"
                    if filter_category or filter_status is not None:
                        filter_info = []
                        if filter_category:
                            cat_name = {
                                "ctf": "CTF",
                                "enterprise": "Enterprise",
                                "general": "General",
                            }.get(filter_category, "")
                            filter_info.append(
                                f"{CATEGORY_ICONS.get(filter_category, '')} {cat_name}"
                            )
                        if filter_status is True:
                            filter_info.append("Enabled")
                        elif filter_status is False:
                            filter_info.append("Disabled")
                        title = f'SELECT RULE TO VIEW ({", ".join(filter_info)})'

                    interactive_select(
                        items=rule_items,
                        columns=columns,
                        selected_ids=selected_rule_ids,
                        get_id=lambda r: r.get("idx"),
                        title=title,
                        format_cell=format_rule_cell,
                    )

                    if not selected_rule_ids:
                        break

                    # View the first selected rule
                    rule_idx = next(iter(selected_rule_ids))
                    if 0 <= rule_idx < len(chaining.rules):
                        _show_single_rule_details(
                            chaining.rules[rule_idx], width, chaining
                        )
                    selected_rule_ids.clear()
        except (KeyboardInterrupt, EOFError):
            return


def _show_single_rule_details(
    rule: ChainRule, width: int, chaining: ToolChaining = None
):
    """Display detailed view for a single rule with toggle for raw definition."""
    show_raw = False

    while True:
        DesignSystem.clear_screen()

        # Header
        click.echo("\n" + "═" * width)
        click.echo(
            click.style(
                f"  {rule.trigger_tool.upper()} → {rule.target_tool.upper()}",
                bold=True,
                fg="cyan",
            )
        )
        click.echo("═" * width)
        click.echo()

        # Status
        if rule.enabled:
            status_display = click.style("✓ ENABLED", fg="green", bold=True)
        else:
            status_display = click.style("✗ DISABLED", fg="red", bold=True)

        click.echo(f"Status:       {status_display}")

        # Priority
        priority_color = (
            "green"
            if rule.priority >= 8
            else "yellow" if rule.priority >= 5 else "white"
        )
        click.echo(
            f"Priority:     {click.style(str(rule.priority), fg=priority_color, bold=True)}/10"
        )

        # Trigger count
        fired_count = rule.trigger_count if hasattr(rule, "trigger_count") else 0
        if fired_count > 0:
            click.echo(
                f"Triggered:    {click.style(str(fired_count), fg='green', bold=True)} times"
            )
        else:
            click.echo(f"Triggered:    {click.style('Never', fg='bright_black')}")

        click.echo()

        # Rule Logic (human-readable)
        click.echo(click.style("Rule Logic:", bold=True))
        click.echo(
            f"  IF {rule.trigger_tool} finds {rule.trigger_condition} → THEN run {rule.target_tool}"
        )
        click.echo()

        # Description
        if rule.description:
            click.echo(click.style("Description:", bold=True))
            click.echo(f"  {rule.description}")
            click.echo()

        # Command Template
        click.echo(click.style("Command Template:", bold=True))
        if rule.args_template:
            click.echo(
                f"  {rule.target_tool} "
                + " ".join(str(arg) for arg in rule.args_template)
            )
        else:
            click.echo(
                click.style("  (uses default tool arguments)", fg="bright_black")
            )
        click.echo()

        # Safety warnings for hydra
        if rule.target_tool == "hydra":
            click.echo(click.style("⚠️  SAFETY INFORMATION:", fg="red", bold=True))
            click.echo(click.style("  • This is a BRUTE-FORCE rule", fg="red"))
            click.echo(click.style("  • May trigger account lockouts", fg="red"))
            click.echo(click.style("  • May trigger security alerts", fg="red"))
            click.echo(click.style("  • Enabled by default: NO (safety)", fg="green"))
            click.echo()

        # Raw rule definition (toggleable)
        if show_raw:
            click.echo("─── Raw Rule Definition " + "─" * (width - 24))
            click.echo(click.style("ChainRule(", fg="cyan"))
            click.echo(
                click.style(f"    trigger_tool='{rule.trigger_tool}',", fg="cyan")
            )
            click.echo(
                click.style(
                    f"    trigger_condition='{rule.trigger_condition}',", fg="cyan"
                )
            )
            click.echo(click.style(f"    target_tool='{rule.target_tool}',", fg="cyan"))
            click.echo(click.style(f"    priority={rule.priority},", fg="cyan"))
            if rule.args_template:
                args_str = str(rule.args_template)
                click.echo(click.style(f"    args_template={args_str},", fg="cyan"))
            click.echo(click.style(f"    enabled={rule.enabled}", fg="cyan"))
            click.echo(click.style(")", fg="cyan"))
            click.echo("─" * width)
            click.echo()

        # Options
        toggle_text = "[r] Hide raw rule" if show_raw else "[r] Show raw rule"
        click.echo(f"  {toggle_text}    [e] Edit rule    [q] Back")
        click.echo()

        try:
            choice = (
                click.prompt("Select option", default="0", show_default=False)
                .strip()
                .lower()
            )

            if choice == "q":
                return
            elif choice == "r":
                show_raw = not show_raw
            elif choice == "e":
                _edit_rule(rule, chaining)
        except (KeyboardInterrupt, EOFError):
            return


def _edit_rule(rule: ChainRule, chaining: ToolChaining):
    """Edit a chain rule's args_template and priority with interactive display."""
    width = DesignSystem.get_terminal_width()

    while True:
        DesignSystem.clear_screen()

        # Header
        click.echo("\n" + "═" * width)
        click.echo(
            click.style(
                f"  EDIT RULE: {rule.trigger_tool.upper()} → {rule.target_tool.upper()}",
                bold=True,
                fg="yellow",
            )
        )
        click.echo("═" * width)
        click.echo()

        # Show raw rule definition with editable fields highlighted
        click.echo("─── Rule Definition " + "─" * (width - 20))
        click.echo(click.style("ChainRule(", fg="cyan"))
        click.echo(
            click.style(f"    trigger_tool='{rule.trigger_tool}',", fg="bright_black")
        )
        click.echo(
            click.style(
                f"    trigger_condition='{rule.trigger_condition}',", fg="bright_black"
            )
        )
        click.echo(
            click.style(f"    target_tool='{rule.target_tool}',", fg="bright_black")
        )

        # Editable: priority (highlighted)
        click.echo(
            click.style("    priority=", fg="cyan")
            + click.style(f"{rule.priority}", fg="yellow", bold=True)
            + click.style(",", fg="cyan")
            + click.style("  ← [p] edit", fg="green")
        )

        # Editable: args_template (highlighted)
        if rule.args_template:
            args_str = str(rule.args_template)
            click.echo(
                click.style("    args_template=", fg="cyan")
                + click.style(f"{args_str}", fg="yellow", bold=True)
                + click.style(",", fg="cyan")
                + click.style("  ← [a] edit", fg="green")
            )
        else:
            click.echo(
                click.style("    args_template=", fg="cyan")
                + click.style("[]", fg="yellow", bold=True)
                + click.style(",", fg="cyan")
                + click.style("  ← [a] edit", fg="green")
            )

        click.echo(click.style(f"    enabled={rule.enabled},", fg="bright_black"))
        click.echo(
            click.style(f"    description='{rule.description}',", fg="bright_black")
        )
        click.echo(click.style(f"    category='{rule.category}'", fg="bright_black"))
        click.echo(click.style(")", fg="cyan"))
        click.echo("─" * width)
        click.echo()

        # Menu
        click.echo(
            click.style("  [p]", fg="green", bold=True)
            + " Edit priority    "
            + click.style("[a]", fg="green", bold=True)
            + " Edit args    "
            + click.style("[c]", fg="yellow", bold=True)
            + " Clear args    "
            + click.style("[s]", fg="cyan", bold=True)
            + " Save    "
            + click.style("[q]", fg="red", bold=True)
            + " Cancel"
        )
        click.echo()

        try:
            choice = (
                click.prompt("Select option", default="s", show_default=False)
                .strip()
                .lower()
            )

            if choice == "q":
                return
            elif choice == "s":
                # Save changes
                chaining.save_rules()
                click.echo(click.style("\n✓ Rule saved!", fg="green"))
                click.pause()
                return
            elif choice == "p":
                # Edit priority
                click.echo()
                try:
                    new_priority = click.prompt(
                        "  New priority (1-10)", type=int, default=rule.priority
                    )
                    if 1 <= new_priority <= 10:
                        rule.priority = new_priority
                        click.echo(
                            click.style(
                                f"  ✓ Priority set to {new_priority}", fg="green"
                            )
                        )
                    else:
                        click.echo(
                            click.style(
                                "  ✗ Priority must be between 1 and 10", fg="red"
                            )
                        )
                except (ValueError, click.Abort):
                    pass
            elif choice == "a":
                # Edit args template
                click.echo()
                current_args = (
                    " ".join(rule.args_template) if rule.args_template else ""
                )
                try:
                    new_args = click.prompt(
                        "  Args (space-separated)", default=current_args
                    ).strip()
                    if new_args:
                        # Parse args - handle quoted strings
                        import shlex

                        try:
                            rule.args_template = shlex.split(new_args)
                            click.echo(click.style(f"  ✓ Args updated", fg="green"))
                        except ValueError as e:
                            click.echo(
                                click.style(f"  ✗ Invalid args format: {e}", fg="red")
                            )
                    else:
                        rule.args_template = []
                        click.echo(click.style("  ✓ Args cleared", fg="green"))
                except click.Abort:
                    pass
            elif choice == "c":
                # Clear args
                rule.args_template = []
                click.echo(click.style("\n✓ Args cleared", fg="green"))
        except (KeyboardInterrupt, EOFError):
            return


def _filter_by_tool(chaining: ToolChaining):
    """Filter and display rules for a specific tool (expanded view)."""
    DesignSystem.clear_screen()

    width = DesignSystem.get_terminal_width()

    # Get unique trigger tools with stats
    tools = sorted(set(r.trigger_tool for r in chaining.rules))

    click.echo("\n" + click.style("EXPAND TOOL GROUP", bold=True, fg="cyan"))
    click.echo("─" * width)
    click.echo(
        click.style(
            "  Select a tool to see all its chain rules in detail", fg="bright_black"
        )
    )
    click.echo()

    for idx, tool in enumerate(tools, 1):
        rules_for_tool = [r for r in chaining.rules if r.trigger_tool == tool]
        enabled_count = sum(1 for r in rules_for_tool if r.enabled)
        rule_count = len(rules_for_tool)

        # Status icon
        if enabled_count == rule_count:
            icon = click.style("✓", fg="green", bold=True)
        elif enabled_count == 0:
            icon = click.style("✗", fg="red")
        else:
            icon = click.style("◐", fg="yellow")

        # Highlight brute-force
        has_hydra = any(r.target_tool == "hydra" for r in rules_for_tool)
        warning = click.style(" ⚠️ ", fg="red") if has_hydra else "   "

        tool_padded = f"{tool.upper():<20}"
        click.echo(
            f"{warning}[{idx:2}] {icon} {click.style(tool_padded, fg='cyan')} "
            f"[{click.style(str(enabled_count), fg='green')}/{rule_count}]"
        )

    click.echo()
    click.echo("  [q] ← Back")
    click.echo()

    try:
        choice = click.prompt("Select option", type=int, default=0, show_default=False)

        if choice == 0 or choice < 1 or choice > len(tools):
            return

        selected_tool = tools[choice - 1]
        filtered_rules = [r for r in chaining.rules if r.trigger_tool == selected_tool]

        DesignSystem.clear_screen()

        # Header
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                f" {selected_tool.upper()} CHAIN RULES ".center(width - 2),
                bold=True,
                fg="cyan",
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Summary
        enabled_count = sum(1 for r in filtered_rules if r.enabled)
        click.echo(
            f"Total Rules: {len(filtered_rules)}  |  "
            f"{click.style(str(enabled_count), fg='green')} enabled, "
            f"{click.style(str(len(filtered_rules) - enabled_count), fg='yellow')} disabled"
        )
        click.echo()

        # Display detailed rules
        for idx, rule in enumerate(
            sorted(filtered_rules, key=lambda r: (-r.priority, r.target_tool)), 1
        ):
            # Status
            status_icon = (
                click.style("✓", fg="green", bold=True)
                if rule.enabled
                else click.style("✗", fg="red")
            )

            # Priority color
            if rule.priority >= 8:
                priority_color = "green"
            elif rule.priority >= 5:
                priority_color = "yellow"
            else:
                priority_color = "white"

            # Target tool with warning
            target = click.style(rule.target_tool, fg="magenta", bold=True)
            warning = (
                click.style(" ⚠️  BRUTE-FORCE", fg="red")
                if rule.target_tool == "hydra"
                else ""
            )

            # Rule header
            click.echo(
                f"  {status_icon} [{idx}] {selected_tool.upper()} → {target}  "
                f"Priority: {click.style(str(rule.priority), fg=priority_color)}{warning}"
            )

            # Condition
            click.echo(
                click.style(
                    f"      Trigger: {rule.trigger_condition}", fg="bright_black"
                )
            )

            # Description
            if rule.description:
                desc_color = "red" if rule.target_tool == "hydra" else "bright_black"
                click.echo(click.style(f"      {rule.description}", fg=desc_color))

            click.echo()

        click.echo("─" * width)
        click.echo(
            click.style(
                "💡 Use option [1] from main menu to toggle individual rules",
                fg="bright_black",
            )
        )
        click.pause()

    except (ValueError, KeyboardInterrupt, EOFError):
        return


def _filter_by_status(chaining: ToolChaining):
    """Filter rules by enabled/disabled status."""
    DesignSystem.clear_screen()

    click.echo("\n" + click.style("FILTER BY STATUS", bold=True, fg="cyan"))
    click.echo("─" * 70)
    click.echo()
    click.echo("  [1] Show ENABLED rules only")
    click.echo("  [2] Show DISABLED rules only")
    click.echo("  [q] Cancel")
    click.echo()

    try:
        choice = click.prompt("Select option", type=int, default=0, show_default=False)

        if choice == 0:
            return

        show_enabled = choice == 1
        filtered_rules = [r for r in chaining.rules if r.enabled == show_enabled]

        status_text = "ENABLED" if show_enabled else "DISABLED"

        DesignSystem.clear_screen()
        click.echo("\n" + click.style(f"{status_text} RULES", bold=True, fg="cyan"))
        click.echo("─" * 70)
        click.echo(f"\nShowing {len(filtered_rules)} rules\n")

        for rule in sorted(filtered_rules, key=lambda r: (-r.priority, r.trigger_tool)):
            warning = (
                click.style(" ⚠️  BRUTE-FORCE", fg="red")
                if rule.target_tool == "hydra"
                else ""
            )
            click.echo(f"  {rule.trigger_tool}→{rule.target_tool}{warning}")
            click.echo(click.style(f"    {rule.description}", fg="bright_black"))
            click.echo()

        click.pause()

    except (ValueError, KeyboardInterrupt, EOFError):
        return


def _enable_all_rules(chaining: ToolChaining):
    """Enable all chain rules with safety confirmation."""
    click.echo()
    click.echo(click.style("⚠️  WARNING: Enable ALL Chain Rules", fg="red", bold=True))
    click.echo(click.style("─" * 70, fg="red"))
    click.echo()

    brute_force_count = sum(1 for r in chaining.rules if r.target_tool == "hydra")

    if brute_force_count > 0:
        click.echo(
            click.style(
                f"  This will enable {brute_force_count} BRUTE-FORCE rules!",
                fg="red",
                bold=True,
            )
        )
        click.echo(
            click.style(
                "  These rules may cause account lockouts and security alerts.",
                fg="red",
            )
        )
        click.echo()

    click.echo(
        f"  Total rules to enable: {sum(1 for r in chaining.rules if not r.enabled)}"
    )
    click.echo()

    if not click.confirm(
        click.style("Are you ABSOLUTELY SURE?", fg="yellow", bold=True), default=False
    ):
        click.echo(click.style("\n✓ Operation cancelled", fg="green"))
        click.pause()
        return

    # Enable all rules
    for rule in chaining.rules:
        rule.enabled = True

    chaining.save_rules()

    click.echo()
    click.echo(
        click.style(f"✓ All {len(chaining.rules)} rules ENABLED", fg="green", bold=True)
    )
    click.pause()


def _disable_all_rules(chaining: ToolChaining):
    """Disable all chain rules."""
    click.echo()

    if not click.confirm("Disable all chain rules?", default=False):
        return

    for rule in chaining.rules:
        rule.enabled = False

    chaining.save_rules()

    click.echo()
    click.echo(
        click.style(
            f"✓ All {len(chaining.rules)} rules DISABLED", fg="yellow", bold=True
        )
    )
    click.pause()


def _reset_to_defaults(chaining: ToolChaining):
    """Reset all rules to their default enabled/disabled state."""
    import os
    from pathlib import Path

    click.echo()

    if not click.confirm("Reset all rules to default state?", default=False):
        return

    # Delete the saved state file
    rules_file = Path.home() / ".souleyez" / "chain_rules_state.json"
    if rules_file.exists():
        os.remove(rules_file)

    # Clear existing rules and reinitialize with code defaults
    chaining.rules.clear()
    chaining._init_default_rules()

    click.echo()
    click.echo(click.style("✓ Rules reset to defaults", fg="green", bold=True))
    click.echo(
        click.style("  Note: Brute-force rules are DISABLED by default", fg="yellow")
    )
    click.pause()
