"""Timeline and velocity tracking UI for deliverables."""

import click

from souleyez.storage.deliverables import DeliverableManager
from souleyez.storage.engagements import EngagementManager
from souleyez.storage.timeline_tracker import TimelineTracker
from souleyez.ui.design_system import DesignSystem


def show_timeline_view(engagement_id: int):
    """
    Display timeline and velocity metrics for an engagement.

    Shows:
    - Phase breakdown (time per PTES phase)
    - Velocity (deliverables per hour)
    - Completion projection
    - Current blockers
    - In-progress items
    """
    tt = TimelineTracker()
    dm = DeliverableManager()
    em = EngagementManager()

    engagement = em.get_by_id(engagement_id)
    if not engagement:
        click.echo(click.style("  Error: Engagement not found", fg="red"))
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
                " ⏱️  TIMELINE & VELOCITY TRACKING ".center(width - 2),
                bold=True,
                fg="cyan",
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        click.echo(
            f"  Engagement: {click.style(engagement['name'], bold=True, fg='cyan')}"
        )
        click.echo()

        # Get timeline summary
        summary = tt.get_timeline_summary(engagement_id)

        # Phase Breakdown
        click.echo(click.style("  📊 PHASE BREAKDOWN", bold=True, fg="cyan"))
        click.echo("  " + "─" * (width - 4))
        click.echo()

        phase_names = {
            "reconnaissance": "🔭 Reconnaissance",
            "enumeration": "🔍 Enumeration",
            "exploitation": "💥 Exploitation",
            "post_exploitation": "🎯 Post-Exploitation",
            "techniques": "🛠️  Techniques",
        }

        for phase, stats in summary["phase_breakdown"].items():
            if stats["total"] == 0:
                continue

            phase_name = phase_names.get(phase, phase)
            completion = stats["completion_rate"]

            # Progress bar
            bar_width = 20
            filled = int((completion / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)

            click.echo(f"  {phase_name}")
            click.echo(f"    Progress: [{bar}] {completion:.0f}%")
            click.echo(f"    Deliverables: {stats['completed']}/{stats['total']}")

            if stats["actual_hours"] > 0:
                click.echo(f"    Time Spent: {stats['actual_hours']:.1f}h")
                if stats["estimated_hours"] > 0:
                    time_var = stats["actual_hours"] - stats["estimated_hours"]
                    if time_var > 0:
                        click.echo(
                            click.style(
                                f"    Over estimate by: {time_var:.1f}h", fg="yellow"
                            )
                        )
                    else:
                        click.echo(
                            click.style(
                                f"    Under estimate by: {abs(time_var):.1f}h",
                                fg="green",
                            )
                        )

            click.echo()

        # Velocity Metrics
        click.echo(click.style("  🚀 VELOCITY METRICS", bold=True, fg="cyan"))
        click.echo("  " + "─" * (width - 4))
        click.echo()

        velocity = summary["velocity"]

        if velocity["completed_deliverables"] > 0:
            click.echo(
                f"  Completed: {velocity['completed_deliverables']} deliverables"
            )
            click.echo(f"  Total Time: {velocity['total_hours']:.1f} hours")
            click.echo(
                f"  Average: {velocity['avg_hours_per_deliverable']:.1f}h per deliverable"
            )
            click.echo(f"  Velocity: {velocity['velocity']:.2f} deliverables/hour")
        else:
            click.echo(
                click.style(
                    "  No completed deliverables yet (velocity unknown)", fg="yellow"
                )
            )

        click.echo()

        # Completion Projection
        click.echo(click.style("  🎯 COMPLETION PROJECTION", bold=True, fg="cyan"))
        click.echo("  " + "─" * (width - 4))
        click.echo()

        projection = summary["projection"]

        if projection["status"] == "complete":
            click.echo(click.style("  ✅ All deliverables completed!", fg="green"))
        else:
            click.echo(
                f"  Remaining: {projection['remaining_deliverables']} deliverables"
            )
            click.echo(
                f"  Estimated Time: {projection['projected_hours']}h ({projection['projected_days']} work days)"
            )
            click.echo(
                f"  Projected Completion: {click.style(projection['projected_date'], bold=True, fg='yellow')}"
            )

            if projection.get("velocity", 0) > 0:
                click.echo(
                    click.style(
                        f"  (Based on current velocity: {projection['velocity']} deliverables/h)",
                        fg="bright_black",
                    )
                )
            else:
                click.echo(
                    click.style(
                        "  (Based on 2h/deliverable estimate)", fg="bright_black"
                    )
                )

        click.echo()

        # Blockers
        blockers = summary["blockers"]
        if blockers:
            click.echo(
                click.style(f"  ⚠️  BLOCKERS ({len(blockers)})", bold=True, fg="red")
            )
            click.echo("  " + "─" * (width - 4))
            click.echo()

            for b in blockers[:5]:
                priority_color = {
                    "critical": "red",
                    "high": "yellow",
                    "medium": "white",
                    "low": "bright_black",
                }.get(b.get("priority", "medium"), "white")

                click.echo(
                    f"  • [{click.style(b.get('priority', 'N/A').upper(), fg=priority_color)}] "
                    f"#{b['id']} {b['title'][:50]}"
                )
                click.echo(click.style(f"    Blocker: {b['blocker']}", fg="yellow"))

            if len(blockers) > 5:
                click.echo(
                    click.style(
                        f"    ... and {len(blockers) - 5} more", fg="bright_black"
                    )
                )

            click.echo()

        # In Progress
        in_progress = summary["in_progress"]
        if in_progress:
            click.echo(
                click.style(
                    f"  🔄 IN PROGRESS ({len(in_progress)})", bold=True, fg="cyan"
                )
            )
            click.echo("  " + "─" * (width - 4))
            click.echo()

            for item in in_progress[:5]:
                click.echo(f"  • #{item['id']} {item['title'][:50]}")

                if item["started_at"]:
                    click.echo(f"    Started: {item['started_at']}")

                if item["estimated_hours"]:
                    click.echo(f"    Estimated: {item['estimated_hours']:.1f}h")

            if len(in_progress) > 5:
                click.echo(
                    click.style(
                        f"    ... and {len(in_progress) - 5} more", fg="bright_black"
                    )
                )

            click.echo()

        # Menu
        click.echo(click.style("  ⚙️  ACTIONS", bold=True, fg="cyan"))
        click.echo("  " + "─" * (width - 4))
        click.echo()
        click.echo("  [S] Start Deliverable")
        click.echo("  [C] Complete Deliverable")
        click.echo("  [B] Set/Clear Blocker")
        click.echo("  [R] Refresh")
        click.echo()
        click.echo("  [q] ← Back")
        click.echo()

        choice = (
            click.prompt("Select option", type=str, default="q", show_default=False)
            .strip()
            .lower()
        )

        if choice == "q":
            break
        elif choice == "s":
            _start_deliverable(engagement_id, tt)
        elif choice == "c":
            _complete_deliverable(engagement_id, tt)
        elif choice == "b":
            _manage_blocker(engagement_id, tt)
        elif choice == "r":
            continue


def _start_deliverable(engagement_id: int, tt: TimelineTracker):
    """Start a deliverable (sets started_at timestamp)."""
    dm = DeliverableManager()

    click.echo()
    deliverable_id = click.prompt("  Enter deliverable ID to start", type=int)

    deliverable = dm.get_deliverable(deliverable_id)
    if not deliverable:
        click.echo(click.style("  Deliverable not found", fg="red"))
        click.pause()
        return

    if deliverable["engagement_id"] != engagement_id:
        click.echo(
            click.style("  Deliverable belongs to different engagement", fg="red")
        )
        click.pause()
        return

    tt.start_deliverable(deliverable_id)
    click.echo(click.style(f"  ✅ Started: {deliverable['title']}", fg="green"))
    click.pause()


def _complete_deliverable(engagement_id: int, tt: TimelineTracker):
    """Complete a deliverable with optional time entry."""
    dm = DeliverableManager()

    click.echo()
    deliverable_id = click.prompt("  Enter deliverable ID to complete", type=int)

    deliverable = dm.get_deliverable(deliverable_id)
    if not deliverable:
        click.echo(click.style("  Deliverable not found", fg="red"))
        click.pause()
        return

    if deliverable["engagement_id"] != engagement_id:
        click.echo(
            click.style("  Deliverable belongs to different engagement", fg="red")
        )
        click.pause()
        return

    click.echo()
    manual_time = click.confirm("  Enter time manually?", default=False)

    if manual_time:
        hours = click.prompt("  Hours spent", type=float)
        tt.complete_deliverable(deliverable_id, actual_hours=hours)
    else:
        tt.complete_deliverable(deliverable_id)

    # Update engagement total hours
    tt.update_engagement_hours(engagement_id)

    click.echo(click.style(f"  ✅ Completed: {deliverable['title']}", fg="green"))
    click.pause()


def _manage_blocker(engagement_id: int, tt: TimelineTracker):
    """Set or clear a blocker."""
    dm = DeliverableManager()

    click.echo()
    deliverable_id = click.prompt("  Enter deliverable ID", type=int)

    deliverable = dm.get_deliverable(deliverable_id)
    if not deliverable:
        click.echo(click.style("  Deliverable not found", fg="red"))
        click.pause()
        return

    if deliverable["engagement_id"] != engagement_id:
        click.echo(
            click.style("  Deliverable belongs to different engagement", fg="red")
        )
        click.pause()
        return

    click.echo()

    if deliverable.get("blocker"):
        click.echo(
            f"  Current blocker: {click.style(deliverable['blocker'], fg='yellow')}"
        )
        click.echo()
        if click.confirm("  Clear blocker?", default=True):
            tt.clear_blocker(deliverable_id)
            click.echo(click.style("  ✅ Blocker cleared", fg="green"))
        else:
            blocker = click.prompt("  New blocker description", type=str)
            tt.set_blocker(deliverable_id, blocker)
            click.echo(click.style("  ✅ Blocker updated", fg="yellow"))
    else:
        blocker = click.prompt("  Blocker description", type=str)
        tt.set_blocker(deliverable_id, blocker)
        click.echo(click.style("  ⚠️  Blocker set", fg="yellow"))

    click.pause()
