"""
CLI commands for screenshot management.
"""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from souleyez.security import require_password
from souleyez.storage.engagements import EngagementManager
from souleyez.storage.screenshots import ScreenshotManager

console = Console()


@click.group()
@require_password
def screenshots():
    """Manage screenshots for engagements."""
    pass


@screenshots.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("--title", "-t", help="Screenshot title")
@click.option("--description", "-d", help="Screenshot description")
@click.option("--host", "-h", type=int, help="Link to host ID")
@click.option("--finding", "-f", type=int, help="Link to finding ID")
@click.option("--job", "-j", type=int, help="Link to job ID")
def add(source, title, description, host, finding, job):
    """Add a screenshot to current engagement."""
    em = EngagementManager()
    sm = ScreenshotManager()

    current = em.get_current()
    if not current:
        console.print("[red]No active engagement[/red]")
        return

    try:
        screenshot_id = sm.add_screenshot(
            engagement_id=current["id"],
            source_path=source,
            title=title,
            description=description,
            host_id=host,
            finding_id=finding,
            job_id=job,
        )

        console.print(f"[green]✓ Screenshot added: ID {screenshot_id}[/green]")

        if title:
            console.print(f"  Title: {title}")
        if host:
            console.print(f"  Linked to host ID: {host}")
        if finding:
            console.print(f"  Linked to finding ID: {finding}")
        if job:
            console.print(f"  Linked to job ID: {job}")

    except Exception as e:
        console.print(f"[red]Error adding screenshot: {e}[/red]")


@screenshots.command()
@click.option("--host", "-h", type=int, help="Filter by host ID")
@click.option("--finding", "-f", type=int, help="Filter by finding ID")
@click.option("--job", "-j", type=int, help="Filter by job ID")
def list(host, finding, job):
    """List screenshots for current engagement."""
    em = EngagementManager()
    sm = ScreenshotManager()

    current = em.get_current()
    if not current:
        console.print("[red]No active engagement[/red]")
        return

    screenshots = sm.list_screenshots(
        engagement_id=current["id"], host_id=host, finding_id=finding, job_id=job
    )

    if not screenshots:
        console.print("[yellow]No screenshots found[/yellow]")
        return

    table = Table(title=f"Screenshots - {current['name']}")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Filename", style="dim")
    table.add_column("Size", style="green")
    table.add_column("Links", style="yellow")
    table.add_column("Created", style="blue")

    for s in screenshots:
        size = s["file_size"]
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"

        links = []
        if s["host_id"]:
            links.append(f"Host:{s['host_id']}")
        if s["finding_id"]:
            links.append(f"Finding:{s['finding_id']}")
        if s["job_id"]:
            links.append(f"Job:{s['job_id']}")
        links_str = ", ".join(links) if links else "None"

        table.add_row(
            str(s["id"]),
            s["title"] or s["filename"],
            s["filename"][:30] + "..." if len(s["filename"]) > 30 else s["filename"],
            size_str,
            links_str,
            s["created_at"][:10],
        )

    console.print(table)
    console.print(f"\nTotal: {len(screenshots)} screenshots")


@screenshots.command()
@click.argument("screenshot_id", type=int)
@click.option("--host", "-h", type=int, help="Link to host ID")
@click.option("--finding", "-f", type=int, help="Link to finding ID")
@click.option("--job", "-j", type=int, help="Link to job ID")
def link(screenshot_id, host, finding, job):
    """Link screenshot to host/finding/job."""
    sm = ScreenshotManager()

    if host:
        sm.link_to_host(screenshot_id, host)
        console.print(
            f"[green]✓ Linked screenshot {screenshot_id} to host {host}[/green]"
        )

    if finding:
        sm.link_to_finding(screenshot_id, finding)
        console.print(
            f"[green]✓ Linked screenshot {screenshot_id} to finding {finding}[/green]"
        )

    if job:
        sm.link_to_job(screenshot_id, job)
        console.print(
            f"[green]✓ Linked screenshot {screenshot_id} to job {job}[/green]"
        )


@screenshots.command()
@click.argument("screenshot_id", type=int)
@click.confirmation_option(prompt="Are you sure you want to delete this screenshot?")
def delete(screenshot_id):
    """Delete a screenshot."""
    sm = ScreenshotManager()

    if sm.delete_screenshot(screenshot_id):
        console.print(f"[green]✓ Screenshot {screenshot_id} deleted[/green]")
    else:
        console.print(f"[red]Screenshot {screenshot_id} not found[/red]")
