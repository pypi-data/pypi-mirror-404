"""Deliverables dashboard view for interactive UI."""

import click
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

try:
    from rich.progress import TaskProgressColumn
except ImportError:
    TaskProgressColumn = None  # Not available in older rich versions
from souleyez.storage.deliverables import DeliverableManager
from souleyez.storage.engagements import EngagementManager
from souleyez.ui.design_system import DesignSystem
from souleyez.ui.errors import engagement_not_found

console = Console()


def show_deliverables_dashboard(engagement_id):
    """Display deliverables dashboard."""
    em = EngagementManager()
    dm = DeliverableManager()

    current = em.get_by_id(engagement_id)
    if not current:
        engagement_not_found(engagement_id)
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
                " DELIVERABLES & ACCEPTANCE CRITERIA ".center(width - 2),
                bold=True,
                fg="cyan",
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Summary
        summary = dm.get_summary(engagement_id)

        if summary["total"] == 0:
            # Go directly to template selector when no deliverables exist
            from souleyez.ui.template_selector import show_template_selector

            loaded = show_template_selector(engagement_id)
            if loaded:
                continue  # Reload deliverables view
            break  # Back if cancelled

        click.echo(f"  Engagement: {current['name']}")
        click.echo(
            f"  Overall Progress: {summary['completed']}/{summary['total']} deliverables ({summary['completion_rate']*100:.0f}%)"
        )
        click.echo()

        # Progress bar
        bar_width = min(50, width - 30)
        completed = summary["completed"]
        total = summary["total"] if summary["total"] > 0 else 1
        filled = int((completed / total) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)

        click.echo(f"  Progress: [{bar}] {completed}/{total}")
        click.echo()

        # Deliverables by category
        deliverables = dm.list_deliverables(engagement_id)

        categories = [
            "reconnaissance",
            "enumeration",
            "exploitation",
            "post_exploitation",
            "techniques",
        ]

        for category in categories:
            cat_deliverables = [d for d in deliverables if d["category"] == category]

            if not cat_deliverables:
                continue

            click.echo(
                click.style(
                    f"\n  {category.upper().replace('_', ' ')}", bold=True, fg="cyan"
                )
            )
            click.echo("  " + "─" * (width - 4))

            for d in cat_deliverables:
                # Status icon
                status_icon = {
                    "completed": "✅",
                    "in_progress": "🔄",
                    "pending": "⚠️",
                    "failed": "❌",
                }.get(d["status"], "?")

                # Progress
                if d["target_type"] == "count":
                    current_val = d["current_value"] or 0
                    target_val = d["target_value"]
                    progress_str = f"[{current_val}/{target_val}]"
                elif d["target_type"] == "boolean":
                    progress_str = "[✓]" if d["status"] == "completed" else "[✗]"
                else:
                    progress_str = "[Manual]"

                # Priority color
                priority_styles = {
                    "critical": "red",
                    "high": "yellow",
                    "medium": "white",
                    "low": "bright_black",
                }
                priority_color = priority_styles.get(d["priority"], "white")

                title_line = (
                    f"    {status_icon} [{d['id']}] {d['title']} {progress_str}"
                )
                if d["priority"] in ["critical", "high"]:
                    title_line = click.style(title_line, fg=priority_color)

                click.echo(title_line)

                if d["description"] and d["status"] != "completed":
                    click.echo(
                        click.style(f"       {d['description']}", fg="bright_black")
                    )

        # Menu with standardized numbered options
        from souleyez.ui.menu_components import StandardMenu

        options = [
            {
                "number": 1,
                "label": "Validate All Deliverables",
                "description": "Auto-validate all deliverables based on evidence",
            },
            {
                "number": 2,
                "label": "Mark as Complete",
                "description": "Mark specific deliverable as complete",
            },
            {
                "number": 3,
                "label": "Link Evidence",
                "description": "Associate evidence with deliverable",
            },
            {
                "number": 4,
                "label": "View Timeline",
                "description": "Display timeline and velocity metrics",
            },
            {
                "number": 5,
                "label": "Export Deliverables",
                "description": "Generate deliverables report",
            },
            {
                "number": 6,
                "label": "Smart Recommendations",
                "description": "View AI-powered recommendations",
            },
            {
                "number": 7,
                "label": "Team Collaboration",
                "description": "Manage team assignments and status",
            },
            {
                "number": 8,
                "label": "Refresh View",
                "description": "Reload deliverables data",
            },
        ]

        choice = StandardMenu.render(options)

        if choice == 0:
            break
        elif choice == 1:
            # Validate
            click.echo()
            click.echo(click.style("  Validating all deliverables...", fg="cyan"))
            stats = dm.validate_all(engagement_id)
            click.echo(
                click.style(f"  ✓ Updated {stats['updated']} deliverables", fg="green")
            )
            click.echo(f"    Completed: {stats['completed']}")
            click.echo(f"    In Progress: {stats['in_progress']}")
            click.pause()
        elif choice == 2:
            # Mark as complete using interactive selector
            from souleyez.ui.interactive_selector import interactive_select

            # Get incomplete deliverables
            incomplete = [d for d in deliverables if d["status"] != "completed"]

            if not incomplete:
                click.echo(
                    click.style(
                        "\n  All deliverables are already completed!", fg="green"
                    )
                )
                click.pause()
                continue

            selected_ids = set()
            columns = [
                {"name": "ID", "width": 6, "key": "id", "justify": "right"},
                {"name": "Category", "width": 15, "key": "category"},
                {"name": "Status", "width": 12, "key": "status"},
                {"name": "Priority", "width": 10, "key": "priority"},
                {"name": "Title", "key": "title"},
            ]

            def format_deliverable_cell(item: dict, key: str) -> str:
                value = item.get(key)
                if value is None:
                    return "-"
                if key == "status":
                    colors = {
                        "pending": "yellow",
                        "in_progress": "cyan",
                        "failed": "red",
                    }
                    color = colors.get(value, "white")
                    return f"[{color}]{value}[/{color}]"
                if key == "priority":
                    colors = {
                        "critical": "red",
                        "high": "yellow",
                        "medium": "white",
                        "low": "dim",
                    }
                    color = colors.get(value, "white")
                    return f"[{color}]{value}[/{color}]"
                return str(value) if value else "-"

            interactive_select(
                items=incomplete,
                columns=columns,
                selected_ids=selected_ids,
                get_id=lambda d: d.get("id"),
                title="SELECT DELIVERABLES TO MARK COMPLETE",
                format_cell=format_deliverable_cell,
            )

            if selected_ids:
                for did in selected_ids:
                    dm.mark_complete(did)
                click.echo(
                    click.style(
                        f"\n  ✓ Marked {len(selected_ids)} deliverable(s) as completed",
                        fg="green",
                    )
                )
            else:
                click.echo("\n  No deliverables selected.")
            click.pause()
        elif choice == 3:
            # Link evidence to deliverable
            deliverable_id = click.prompt("  Enter deliverable ID", type=int)
            deliverable = dm.get_deliverable(deliverable_id)
            if deliverable:
                from souleyez.ui.evidence_linking_view import show_evidence_linking_view

                show_evidence_linking_view(deliverable_id)
            else:
                click.echo(
                    click.style(f"  Deliverable {deliverable_id} not found", fg="red")
                )
                click.pause()
        elif choice == 4:
            # View timeline and velocity
            from souleyez.ui.timeline_view import show_timeline_view

            show_timeline_view(engagement_id)
        elif choice == 5:
            # Export deliverables
            from souleyez.ui.export_view import show_export_view

            show_export_view(engagement_id)
        elif choice == 6:
            # Smart recommendations
            from souleyez.ui.recommendations_view import show_recommendations_dashboard

            show_recommendations_dashboard(engagement_id)
        elif choice == 7:
            # Team collaboration
            from souleyez.ui.team_dashboard import show_team_dashboard

            show_team_dashboard(engagement_id)
        elif choice == 8:
            # Refresh
            continue
        else:
            click.echo(click.style("  Invalid choice", fg="yellow"))
            click.pause()
