"""
CLI commands for deliverable tracking.
"""

import click
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

try:
    from rich.progress import TaskProgressColumn
except ImportError:
    TaskProgressColumn = None  # Not available in older rich versions
from souleyez.security import require_password
from souleyez.storage.deliverables import DeliverableManager
from souleyez.storage.engagements import EngagementManager

console = Console()


@click.group()
@require_password
def deliverables():
    """Manage engagement deliverables and acceptance criteria."""
    pass


@deliverables.command()
@click.option("--defaults", is_flag=True, help="Create default deliverables")
def init(defaults):
    """Initialize deliverables for current engagement."""
    em = EngagementManager()
    dm = DeliverableManager()

    current = em.get_current()
    if not current:
        console.print("[red]No active engagement[/red]")
        return

    if defaults:
        count = dm.create_default_deliverables(current["id"])
        console.print(f"[green]✓ Created {count} default deliverables[/green]")
    else:
        console.print("[yellow]Use --defaults to create default deliverables[/yellow]")


@deliverables.command()
@click.option("--category", "-c", help="Filter by category")
@click.option("--status", "-s", help="Filter by status")
def list(category, status):
    """List deliverables for current engagement."""
    em = EngagementManager()
    dm = DeliverableManager()

    current = em.get_current()
    if not current:
        console.print("[red]No active engagement[/red]")
        return

    deliverables = dm.list_deliverables(current["id"], category=category, status=status)

    if not deliverables:
        console.print("[yellow]No deliverables found[/yellow]")
        console.print(
            "\nTip: Run 'souleyez deliverables init --defaults' to create default deliverables"
        )
        return

    summary = dm.get_summary(current["id"])

    console.print(f"\n[bold cyan]Deliverables - {current['name']}[/bold cyan]")
    console.print(
        f"Completion: {summary['completed']}/{summary['total']} ({summary['completion_rate']*100:.0f}%)\n"
    )

    table = Table()
    table.add_column("ID", style="cyan")
    table.add_column("Category", style="yellow")
    table.add_column("Title", style="white")
    table.add_column("Progress", style="green")
    table.add_column("Status", style="blue")
    table.add_column("Priority", style="red")

    for d in deliverables:
        if d["target_type"] == "count":
            current_val = d["current_value"] or 0
            target_val = d["target_value"]
            progress = f"{current_val}/{target_val}"
        elif d["target_type"] == "boolean":
            progress = "✓" if d["status"] == "completed" else "✗"
        else:
            progress = "Manual"

        status_emoji = {
            "completed": "✅",
            "in_progress": "🔄",
            "pending": "⚠️",
            "failed": "❌",
        }
        status_str = f"{status_emoji.get(d['status'], '?')} {d['status']}"

        priority_color = {
            "critical": "[red]",
            "high": "[yellow]",
            "medium": "[blue]",
            "low": "[dim]",
        }
        priority_str = f"{priority_color.get(d['priority'], '')}{ d['priority']}[/]"

        table.add_row(
            str(d["id"]), d["category"], d["title"], progress, status_str, priority_str
        )

    console.print(table)
    console.print(f"\nTotal: {len(deliverables)} deliverables")


@deliverables.command()
def validate():
    """Validate all auto-validated deliverables."""
    em = EngagementManager()
    dm = DeliverableManager()

    current = em.get_current()
    if not current:
        console.print("[red]No active engagement[/red]")
        return

    console.print("[cyan]Validating deliverables...[/cyan]")

    stats = dm.validate_all(current["id"])

    console.print(f"[green]✓ Validated {stats['updated']} deliverables[/green]")
    console.print(f"  Completed: {stats['completed']}")
    console.print(f"  In Progress: {stats['in_progress']}")
    console.print(f"  Failed: {stats['failed']}")


@deliverables.command()
@click.argument("deliverable_id", type=int)
def complete(deliverable_id):
    """Mark a deliverable as completed (manual deliverables)."""
    dm = DeliverableManager()

    deliverable = dm.get_deliverable(deliverable_id)
    if not deliverable:
        console.print(f"[red]Deliverable {deliverable_id} not found[/red]")
        return

    dm.mark_complete(deliverable_id)
    console.print(f"[green]✓ Deliverable {deliverable_id} marked as completed[/green]")
    console.print(f"  {deliverable['title']}")


@deliverables.command()
@click.argument("category")
@click.argument("title")
@click.option(
    "--target-type", "-t", default="manual", help="Target type (count, boolean, manual)"
)
@click.option("--target-value", "-v", type=int, help="Target value (for count types)")
@click.option(
    "--priority", "-p", default="medium", help="Priority (critical, high, medium, low)"
)
def add(category, title, target_type, target_value, priority):
    """Add a custom deliverable."""
    em = EngagementManager()
    dm = DeliverableManager()

    current = em.get_current()
    if not current:
        console.print("[red]No active engagement[/red]")
        return

    deliverable_id = dm.add_deliverable(
        engagement_id=current["id"],
        category=category,
        title=title,
        target_type=target_type,
        target_value=target_value,
        priority=priority,
    )

    console.print(f"[green]✓ Deliverable added: ID {deliverable_id}[/green]")
    console.print(f"  {title}")


@deliverables.command()
@click.argument("deliverable_id", type=int)
@click.confirmation_option(prompt="Are you sure you want to delete this deliverable?")
def delete(deliverable_id):
    """Delete a deliverable."""
    dm = DeliverableManager()

    if dm.delete_deliverable(deliverable_id):
        console.print(f"[green]✓ Deliverable {deliverable_id} deleted[/green]")
    else:
        console.print(f"[red]Deliverable {deliverable_id} not found[/red]")


@deliverables.command()
def summary():
    """Show deliverable summary with progress bars."""
    em = EngagementManager()
    dm = DeliverableManager()

    current = em.get_current()
    if not current:
        console.print("[red]No active engagement[/red]")
        return

    summary = dm.get_summary(current["id"])

    console.print(f"\n[bold cyan]Deliverable Summary - {current['name']}[/bold cyan]\n")

    console.print(
        f"[bold]Overall Progress:[/bold] {summary['completed']}/{summary['total']} ({summary['completion_rate']*100:.0f}%)"
    )

    columns = [
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
    ]
    if TaskProgressColumn:
        columns.append(TaskProgressColumn())
    progress = Progress(*columns)

    with progress:
        task = progress.add_task(
            "Completion", total=summary["total"], completed=summary["completed"]
        )

    console.print("\n[bold]By Category:[/bold]\n")

    for category, stats in summary["by_category"].items():
        completion_rate = (
            stats["completed"] / stats["total"] if stats["total"] > 0 else 0
        )

        console.print(
            f"  {category.title()}: {stats['completed']}/{stats['total']} ({completion_rate*100:.0f}%)"
        )
        console.print(f"    ✅ Completed: {stats['completed']}")
        console.print(f"    🔄 In Progress: {stats['in_progress']}")
        console.print(f"    ⚠️ Pending: {stats['pending']}")
        console.print()
