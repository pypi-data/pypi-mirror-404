"""
CLI commands for viewing audit logs.

Commands:
- souleyez audit list           - List recent audit events
- souleyez audit search         - Search audit logs
- souleyez audit stats          - Show audit statistics
- souleyez audit export         - Export audit logs
"""

import json
from datetime import datetime

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from souleyez.auth import Role
from souleyez.auth.audit import get_audit_logger
from souleyez.auth.permissions import requires_role
from souleyez.security import require_login

console = Console()


@click.group()
def audit():
    """View and search audit logs."""
    pass


@audit.command("list")
@require_login
@requires_role(Role.LEAD)
@click.option("--limit", "-n", default=50, help="Number of entries to show")
@click.option("--user", "-u", help="Filter by username")
@click.option("--action", "-a", help="Filter by action (e.g., 'scan', 'user.login')")
def audit_list(limit, user, action):
    """List recent audit log entries."""
    logger = get_audit_logger()

    entries = logger.query(username=user, action=action, limit=limit)

    if not entries:
        console.print("[yellow]No audit entries found[/yellow]")
        return

    table = Table(title=f"📋 Audit Log (Last {len(entries)} entries)")
    table.add_column("Time", style="dim", width=19)
    table.add_column("User", width=12)
    table.add_column("Action", width=25)
    table.add_column("Resource", width=15)
    table.add_column("Details", width=30)
    table.add_column("✓", width=3)

    for e in entries:
        # Parse timestamp
        ts = e["timestamp"][:19].replace("T", " ")

        # Format resource
        resource = ""
        if e["resource_type"]:
            resource = f"{e['resource_type']}"
            if e["resource_id"]:
                resource += f":{e['resource_id']}"

        # Format details (truncate if long)
        details = ""
        if e["details"]:
            try:
                d = json.loads(e["details"])
                details = str(d)[:30]
            except:
                details = e["details"][:30]

        # Success indicator
        success = "[green]✓[/green]" if e["success"] else "[red]✗[/red]"

        # Color action by category
        action_str = e["action"]
        if action_str.startswith("auth.") or action_str.startswith("permission."):
            action_str = f"[red]{action_str}[/red]"
        elif action_str.startswith("user."):
            action_str = f"[cyan]{action_str}[/cyan]"
        elif action_str.startswith("scan."):
            action_str = f"[yellow]{action_str}[/yellow]"
        elif action_str.startswith("engagement."):
            action_str = f"[green]{action_str}[/green]"

        table.add_row(
            ts,
            e["username"] or "-",
            action_str,
            resource or "-",
            details or "-",
            success,
        )

    console.print(table)


@audit.command("search")
@require_login
@requires_role(Role.LEAD)
@click.option("--user", "-u", help="Filter by username")
@click.option("--action", "-a", help="Filter by action pattern")
@click.option("--resource", "-r", help="Filter by resource type")
@click.option("--start", "-s", help="Start date (YYYY-MM-DD)")
@click.option("--end", "-e", help="End date (YYYY-MM-DD)")
@click.option("--failed", is_flag=True, help="Show only failed actions")
@click.option("--limit", "-n", default=100, help="Max results")
def audit_search(user, action, resource, start, end, failed, limit):
    """Search audit logs with filters."""
    logger = get_audit_logger()

    start_date = datetime.fromisoformat(start) if start else None
    end_date = datetime.fromisoformat(end) if end else None

    entries = logger.query(
        username=user,
        action=action,
        resource_type=resource,
        start_date=start_date,
        end_date=end_date,
        success_only=not failed,
        limit=limit,
    )

    if not entries:
        console.print("[yellow]No matching entries found[/yellow]")
        return

    console.print(f"[green]Found {len(entries)} entries[/green]\n")

    for e in entries:
        ts = e["timestamp"][:19].replace("T", " ")
        success = "✓" if e["success"] else "✗"

        console.print(f"[dim]{ts}[/dim] [{success}] [bold]{e['action']}[/bold]")
        console.print(f"  User: {e['username'] or 'system'}")

        if e["resource_type"]:
            console.print(f"  Resource: {e['resource_type']}:{e['resource_id'] or ''}")

        if e["details"]:
            try:
                details = json.loads(e["details"])
                console.print(f"  Details: {details}")
            except:
                console.print(f"  Details: {e['details']}")

        console.print()


@audit.command("stats")
@require_login
@requires_role(Role.LEAD)
@click.option("--days", "-d", default=30, help="Number of days to analyze")
def audit_stats(days):
    """Show audit log statistics."""
    logger = get_audit_logger()
    stats = logger.get_stats(days)

    console.print(
        Panel(
            f"[bold]Period:[/bold] Last {stats['period_days']} days\n"
            f"[bold]Total Events:[/bold] {stats['total_events']}\n"
            f"[bold]Failed Events:[/bold] [red]{stats['failed_events']}[/red]\n"
            f"[bold]Unique Users:[/bold] {stats['unique_users']}",
            title="📊 Audit Statistics",
            border_style="blue",
        )
    )

    if stats["by_category"]:
        console.print("\n[bold]Events by Category:[/bold]")
        table = Table(show_header=False, box=None)
        table.add_column("Category", width=20)
        table.add_column("Count", justify="right")

        for cat, count in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
            bar = "█" * min(count // 10, 30)
            table.add_row(cat, f"{count} {bar}")

        console.print(table)


@audit.command("export")
@require_login
@requires_role(Role.ADMIN)
@click.option("--start", "-s", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end", "-e", help="End date (YYYY-MM-DD, default: today)")
@click.option("--format", "-f", type=click.Choice(["json", "csv"]), default="json")
@click.option("--output", "-o", help="Output file path")
def audit_export(start, end, format, output):
    """Export audit logs to file."""
    import csv

    logger = get_audit_logger()

    start_date = datetime.fromisoformat(start)
    end_date = datetime.fromisoformat(end) if end else datetime.now()

    entries = logger.query(
        start_date=start_date, end_date=end_date, limit=10000  # Large limit for export
    )

    if not entries:
        console.print("[yellow]No entries found for the specified period[/yellow]")
        return

    # Generate filename if not provided
    if not output:
        date_str = start_date.strftime("%Y%m%d")
        output = f"audit_log_{date_str}.{format}"

    if format == "json":
        with open(output, "w") as f:
            json.dump(entries, f, indent=2, default=str)
    else:
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=entries[0].keys())
            writer.writeheader()
            writer.writerows(entries)

    console.print(f"[green]✅ Exported {len(entries)} entries to {output}[/green]")
