"""Export deliverables UI."""

import os

import click

from souleyez.storage.deliverable_exporter import DeliverableExporter
from souleyez.storage.engagements import EngagementManager
from souleyez.ui.design_system import DesignSystem
from souleyez.ui.errors import engagement_not_found


def show_export_view(engagement_id: int):
    """
    Display export options for deliverables.

    Supports:
    - CSV export (Excel-compatible)
    - JSON export (API integration)
    - Markdown export (documentation)
    """
    exporter = DeliverableExporter()
    em = EngagementManager()

    engagement = em.get_by_id(engagement_id)
    if not engagement:
        engagement_not_found(engagement_id)
        click.pause()
        return

    while True:
        DesignSystem.clear_screen()

        width = DesignSystem.get_terminal_width()

        # Header
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " 📤 EXPORT DELIVERABLES ".center(width - 2), bold=True, fg="cyan"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        click.echo(
            f"  Engagement: {click.style(engagement['name'], bold=True, fg='cyan')}"
        )
        click.echo()

        # Export format selection
        click.echo(click.style("  📋 EXPORT FORMATS", bold=True, fg="cyan"))
        click.echo("  " + "─" * (width - 4))
        click.echo()

        click.echo("  [1] 📊 CSV Export")
        click.echo("      Excel-compatible spreadsheet format")
        click.echo("      Ideal for: Data analysis, reporting, pivot tables")
        click.echo()

        click.echo("  [2] 🔗 JSON Export")
        click.echo("      Machine-readable structured data")
        click.echo("      Ideal for: API integration, automation, archiving")
        click.echo()

        click.echo("  [3] 📄 Markdown Export")
        click.echo("      Human-readable documentation format")
        click.echo("      Ideal for: Reports, GitHub/GitLab, wikis")
        click.echo()

        click.echo("  [4] 📦 Export All Formats")
        click.echo("      Creates CSV, JSON, and Markdown files")
        click.echo()

        click.echo("  [q] ← Back")
        click.echo()

        choice = click.prompt(
            "Select option", type=str, default="q", show_default=False
        ).strip()

        if choice == "q":
            break
        elif choice in ["1", "2", "3", "4"]:
            _perform_export(engagement, choice, exporter)
        else:
            click.echo(click.style("  Invalid choice", fg="yellow"))
            click.pause()


def _perform_export(
    engagement: dict, format_choice: str, exporter: DeliverableExporter
):
    """Perform the export operation."""
    from datetime import datetime

    engagement_id = engagement["id"]
    engagement_name = engagement["name"].replace(" ", "_").replace("/", "_")

    # Generate timestamp
    try:
        ctx = click.get_current_context()
        timestamp = (
            ctx.obj.get("timestamp")
            if ctx and hasattr(ctx, "obj") and ctx.obj
            else datetime.now().strftime("%Y%m%d_%H%M%S")
        )
    except (RuntimeError, AttributeError):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    click.echo()

    # Ask for evidence inclusion
    include_evidence = click.confirm("  Include evidence details?", default=True)
    click.echo()

    # Get output directory
    default_dir = os.path.expanduser("~/Downloads")
    if not os.path.exists(default_dir):
        default_dir = os.path.expanduser("~")

    output_dir = click.prompt("  Output directory", type=str, default=default_dir)

    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)

    click.echo()
    click.echo(click.style("  Exporting...", fg="cyan"))

    success_count = 0
    failed_count = 0

    formats_to_export = []

    if format_choice == "1":
        formats_to_export = [("csv", "CSV")]
    elif format_choice == "2":
        formats_to_export = [("json", "JSON")]
    elif format_choice == "3":
        formats_to_export = [("md", "Markdown")]
    elif format_choice == "4":
        formats_to_export = [("csv", "CSV"), ("json", "JSON"), ("md", "Markdown")]

    for ext, name in formats_to_export:
        filename = f"deliverables_{engagement_name}.{ext}"
        output_path = os.path.join(output_dir, filename)

        try:
            if ext == "csv":
                success = exporter.export_csv(
                    engagement_id, output_path, include_evidence
                )
            elif ext == "json":
                success = exporter.export_json(
                    engagement_id, output_path, include_evidence
                )
            elif ext == "md":
                success = exporter.export_markdown(
                    engagement_id, output_path, include_evidence
                )
            else:
                success = False

            if success:
                click.echo(
                    click.style(f"  ✅ {name} exported: {output_path}", fg="green")
                )
                success_count += 1
            else:
                click.echo(
                    click.style(
                        f"  ❌ {name} export failed (no deliverables?)", fg="red"
                    )
                )
                failed_count += 1

        except Exception as e:
            click.echo(click.style(f"  ❌ {name} export failed: {str(e)}", fg="red"))
            failed_count += 1

    click.echo()

    if success_count > 0:
        click.echo(
            click.style(
                f"  ✅ Successfully exported {success_count} file(s)", fg="green"
            )
        )
        click.echo(f"  Location: {output_dir}")

        # Show file sizes
        click.echo()
        click.echo(click.style("  📁 Generated Files:", fg="cyan"))
        for ext, name in formats_to_export:
            filename = f"deliverables_{engagement_name}.{ext}"
            filepath = os.path.join(output_dir, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                size_kb = size / 1024
                click.echo(f"     • {filename} ({size_kb:.1f} KB)")

        click.echo()
        click.echo(click.style("  💡 Next Steps:", fg="cyan"))
        click.echo("     • Open CSV in Excel/LibreOffice for analysis")
        click.echo("     • Use JSON for API integration or automation")
        click.echo("     • Share Markdown in documentation/reports")

    if failed_count > 0:
        click.echo(click.style(f"  ⚠️  {failed_count} export(s) failed", fg="yellow"))

    click.pause()
