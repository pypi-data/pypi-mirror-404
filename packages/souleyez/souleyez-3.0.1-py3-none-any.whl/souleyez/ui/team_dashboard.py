"""Team collaboration dashboard."""

from typing import Dict, List, Optional

import click

from souleyez.storage.deliverables import DeliverableManager
from souleyez.storage.engagements import EngagementManager
from souleyez.storage.team_collaboration import TeamCollaboration
from souleyez.ui.design_system import DesignSystem
from souleyez.ui.interactive_selector import (
    KEY_DOWN,
    KEY_ENTER,
    KEY_ESCAPE,
    KEY_UP,
    _get_key,
)


def _get_all_users_with_workload(
    engagement_id: int, tc: TeamCollaboration
) -> List[Dict]:
    """
    Get all active users with their workload data.

    Returns all users from UserManager, merged with workload from deliverables.
    """
    from souleyez.auth import UserManager
    from souleyez.storage.database import get_db

    user_mgr = UserManager(get_db().db_path)
    all_users = user_mgr.list_users(include_inactive=False)

    # Get existing workload data
    workload_data = tc.get_user_workload(engagement_id)
    workload_map = {w["user"]: w for w in workload_data}

    # Build complete user list with workload
    result = []
    for user in all_users:
        if user.username in workload_map:
            result.append(workload_map[user.username])
        else:
            result.append(
                {
                    "user": user.username,
                    "total_assigned": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "pending": 0,
                    "blocked": 0,
                }
            )

    return result


def _select_user_interactive(
    users: List[Dict], title: str = "SELECT USER", include_round_robin: bool = False
) -> Optional[str]:
    """
    Interactive user selection with arrow key navigation.

    Returns:
        Selected username, 'ROUND_ROBIN' for round-robin, or None if cancelled
    """
    from rich.console import Console

    if not users:
        click.echo(click.style("  ⚠️  No users available.", fg="yellow"))
        click.pause()
        return None

    console = Console()
    cursor = 0
    options = []

    if include_round_robin:
        options.append(
            {
                "label": "Round-robin (distribute evenly)",
                "value": "ROUND_ROBIN",
                "workload": None,
            }
        )

    for u in users:
        options.append(
            {"label": u["user"], "value": u["user"], "workload": u.get("pending", 0)}
        )

    while True:
        DesignSystem.clear_screen()
        click.echo()
        click.echo(click.style(f"  {title}", bold=True, fg="cyan"))
        click.echo("  " + "─" * 50)
        click.echo()

        for idx, opt in enumerate(options):
            prefix = "▶ " if idx == cursor else "  "
            if idx == cursor:
                style = "reverse"
            else:
                style = None

            if opt["workload"] is not None:
                line = (
                    f"{prefix}{opt['label']:<25} (workload: {opt['workload']} pending)"
                )
            else:
                line = f"{prefix}{opt['label']}"

            if idx == cursor:
                click.echo(click.style(f"  {line}", fg="cyan", bold=True))
            else:
                click.echo(f"  {line}")

        click.echo()
        click.echo(
            click.style("  ↑↓ Navigate  Enter Select  q Cancel", fg="bright_black")
        )

        key = _get_key()

        if key in (KEY_UP, "k"):
            cursor = (cursor - 1) % len(options)
        elif key in (KEY_DOWN, "j"):
            cursor = (cursor + 1) % len(options)
        elif key in (KEY_ENTER, "\r", "\n"):
            return options[cursor]["value"]
        elif key in ("q", KEY_ESCAPE):
            return None


def show_team_dashboard(engagement_id: int):
    """
    Display team collaboration dashboard.

    Shows:
    - Activity feed
    - User workload
    - Team summary
    - Assignment management
    """
    tc = TeamCollaboration()
    em = EngagementManager()
    dm = DeliverableManager()

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
                " 👥 TEAM COLLABORATION ".center(width - 2), bold=True, fg="cyan"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        click.echo(
            f"  Engagement: {click.style(engagement['name'], bold=True, fg='cyan')}"
        )
        click.echo()

        # Get data
        team_summary = tc.get_team_summary(engagement_id)
        workload = tc.get_user_workload(engagement_id)
        activity_feed = tc.get_recent_activity_feed(engagement_id, limit=10)

        # Team Summary
        if team_summary["total_users"] > 0:
            click.echo(click.style("  👥 TEAM MEMBERS", bold=True, fg="cyan"))
            click.echo("  " + "─" * (width - 4))
            click.echo()

            for user in sorted(team_summary["users"]):
                stats = team_summary["user_activity"][user]
                click.echo(f"  • {click.style(user, bold=True)}")
                click.echo(
                    f"    Assigned: {stats['assigned_count']} | "
                    f"Completed: {stats['completed_count']} | "
                    f"Activity: {stats['activity_count']}"
                )

            click.echo()

        # Workload Distribution
        if workload:
            click.echo(click.style("  📊 WORKLOAD DISTRIBUTION", bold=True, fg="cyan"))
            click.echo("  " + "─" * (width - 4))
            click.echo()

            for user_stats in workload:
                user = user_stats["user"]
                total = user_stats["total_assigned"]
                completed = user_stats["completed"]
                in_progress = user_stats["in_progress"]
                pending = user_stats["pending"]
                blocked = user_stats["blocked"]

                completion_rate = (completed / total * 100) if total > 0 else 0

                # Color code by workload
                if blocked > 0:
                    user_color = "red"
                elif in_progress > 5:
                    user_color = "yellow"
                else:
                    user_color = "green"

                click.echo(f"  {click.style(user, fg=user_color, bold=True)}")
                click.echo(
                    f"    Total: {total} | ✅ {completed} | 🔄 {in_progress} | ⏳ {pending} | 🚧 {blocked}"
                )

                # Progress bar
                if total > 0:
                    bar_width = 30
                    filled = int(completion_rate / 100 * bar_width)
                    bar = "█" * filled + "░" * (bar_width - filled)
                    click.echo(f"    [{bar}] {completion_rate:.0f}%")

                click.echo()
        else:
            click.echo(click.style("  No assignments yet", fg="yellow"))
            click.echo()

        # Recent Activity Feed
        if activity_feed:
            click.echo(click.style("  📰 RECENT ACTIVITY", bold=True, fg="cyan"))
            click.echo("  " + "─" * (width - 4))
            click.echo()

            for item in activity_feed[:8]:
                # Format timestamp
                created_at = item["created_at"]
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    time_str = dt.strftime("%m/%d %H:%M")
                except:
                    time_str = created_at[:16] if len(created_at) > 16 else created_at

                # Action color
                action_colors = {
                    "started": "cyan",
                    "completed": "green",
                    "updated": "yellow",
                    "assigned": "blue",
                    "blocker_set": "red",
                }
                color = action_colors.get(item["action"], "white")

                click.echo(
                    f"  [{click.style(time_str, fg='bright_black')}] "
                    f"{click.style(item['message'], fg=color)}"
                )

            if len(activity_feed) > 8:
                click.echo()
                click.echo(
                    click.style(
                        f"  ... and {len(activity_feed) - 8} more activities",
                        fg="bright_black",
                    )
                )

            click.echo()
        else:
            click.echo(click.style("  No recent activity", fg="yellow"))
            click.echo()

        # Menu
        click.echo(click.style("  ⚙️  ACTIONS", bold=True, fg="cyan"))
        click.echo("  " + "─" * (width - 4))
        click.echo()
        click.echo("  [A] Assign Deliverables")
        click.echo("  [U] Reassign/Unassign Deliverable")
        click.echo("  [X] Reassign All Deliverables")
        click.echo("  [C] View Comments")
        click.echo("  [F] Full Activity Log")
        click.echo("  [W] Workload Report")
        click.echo()
        click.echo("  [R] Refresh")
        click.echo("  [q] ← Back")
        click.echo()

        choice = (
            click.prompt("Select option", type=str, default="q", show_default=False)
            .strip()
            .lower()
        )

        if choice == "q":
            break
        elif choice == "a":
            _assign_deliverables(engagement_id, tc, dm)
        elif choice == "u":
            _reassign_deliverable(engagement_id, tc, dm)
        elif choice == "x":
            _reassign_all_deliverables(engagement_id, tc, dm)
        elif choice == "c":
            _view_comments(engagement_id, tc, dm)
        elif choice == "f":
            _full_activity_log(engagement_id, tc)
        elif choice == "w":
            _workload_report(engagement_id, tc)
        elif choice == "r":
            continue


def _assign_deliverables(
    engagement_id: int, tc: TeamCollaboration, dm: DeliverableManager
):
    """Assign deliverables to users."""
    DesignSystem.clear_screen()

    width = DesignSystem.get_terminal_width()

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" ASSIGN DELIVERABLES ".center(width - 2), bold=True, fg="cyan")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    # Get unassigned or pending deliverables
    deliverables = dm.list_deliverables(engagement_id)
    unassigned = [
        d
        for d in deliverables
        if not d.get("assigned_to") and d["status"] != "completed"
    ]

    if not unassigned:
        click.echo(click.style("  No unassigned deliverables", fg="green"))
        click.pause()
        return

    click.echo(click.style("  UNASSIGNED DELIVERABLES", bold=True, fg="cyan"))
    click.echo("  " + "─" * (width - 4))
    click.echo()

    for idx, d in enumerate(unassigned[:10], 1):
        priority_color = {
            "critical": "red",
            "high": "yellow",
            "medium": "white",
            "low": "bright_black",
        }.get(d.get("priority", "medium"), "white")

        click.echo(
            f"  [{idx}] [{click.style(d.get('priority', 'medium').upper(), fg=priority_color)}] {d['title'][:60]}"
        )

    if len(unassigned) > 10:
        click.echo(f"  ... and {len(unassigned) - 10} more")

    click.echo()
    click.echo(f"  [A] Assign All ({len(unassigned)} deliverables)")
    click.echo()

    # Get deliverable ID or 'A' for all
    choice = click.prompt(
        "Select option", type=str, default="q", show_default=False
    ).strip()

    if choice.upper() == "A":
        # Assign all unassigned deliverables - interactive selection
        users = _get_all_users_with_workload(engagement_id, tc)

        if not users:
            click.echo(click.style("  ⚠️  No team members found.", fg="yellow"))
            click.pause()
            return

        selected = _select_user_interactive(
            users,
            title=f"ASSIGN ALL {len(unassigned)} DELIVERABLES TO",
            include_round_robin=True,
        )

        if selected is None:
            return

        if selected == "ROUND_ROBIN":
            # Round-robin assignment
            usernames = [u["user"] for u in users]
            assigned_count = 0
            user_idx = 0

            for deliv in unassigned:
                assignee = usernames[user_idx % len(usernames)]
                tc.assign_deliverable(
                    deliverable_id=deliv["id"],
                    engagement_id=engagement_id,
                    assigned_to=assignee,
                )
                assigned_count += 1
                user_idx += 1

            click.echo()
            click.echo(
                click.style(
                    f"  ✅ Assigned {assigned_count} deliverables across {len(usernames)} members (round-robin)",
                    fg="green",
                )
            )
        else:
            # Assign all to one person
            assigned_count = 0
            for deliv in unassigned:
                tc.assign_deliverable(
                    deliverable_id=deliv["id"],
                    engagement_id=engagement_id,
                    assigned_to=selected,
                )
                assigned_count += 1

            click.echo()
            click.echo(
                click.style(
                    f"  ✅ Assigned {assigned_count} deliverables to {selected}",
                    fg="green",
                )
            )

        click.pause()
        return

    try:
        deliverable_num = int(choice)
    except ValueError:
        return

    if deliverable_num < 1 or deliverable_num > len(unassigned):
        return

    selected_deliverable = unassigned[deliverable_num - 1]

    # Interactive user selection
    users = _get_all_users_with_workload(engagement_id, tc)

    if not users:
        click.echo(click.style("  ⚠️  No team members found.", fg="yellow"))
        click.pause()
        return

    # Truncate title for display
    title_display = selected_deliverable["title"][:40]
    if len(selected_deliverable["title"]) > 40:
        title_display += "..."

    selected_user = _select_user_interactive(
        users, title=f"ASSIGN '{title_display}' TO"
    )

    if selected_user is None:
        return

    tc.assign_deliverable(
        deliverable_id=selected_deliverable["id"],
        engagement_id=engagement_id,
        assigned_to=selected_user,
    )

    click.echo()
    click.echo(
        click.style(
            f"  ✅ Assigned '{selected_deliverable['title']}' to {selected_user}",
            fg="green",
        )
    )
    click.pause()


def _reassign_deliverable(
    engagement_id: int, tc: TeamCollaboration, dm: DeliverableManager
):
    """Reassign or unassign a specific deliverable."""
    DesignSystem.clear_screen()

    width = DesignSystem.get_terminal_width()

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            " REASSIGN/UNASSIGN DELIVERABLE ".center(width - 2), bold=True, fg="cyan"
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    # Get all deliverables
    deliverables = dm.list_deliverables(engagement_id)

    if not deliverables:
        click.echo(click.style("  No deliverables found", fg="yellow"))
        click.pause()
        return

    click.echo(click.style("  ALL DELIVERABLES", bold=True, fg="cyan"))
    click.echo("  " + "─" * (width - 4))
    click.echo()

    # Show all deliverables with assignment status
    for idx, d in enumerate(deliverables, 1):
        priority_color = {
            "critical": "red",
            "high": "yellow",
            "medium": "white",
            "low": "bright_black",
        }.get(d.get("priority", "medium"), "white")

        assigned_to = d.get("assigned_to", "Unassigned")
        assignment_color = "green" if assigned_to != "Unassigned" else "bright_black"

        click.echo(
            f"  {idx:2d}. [{click.style(d.get('priority', 'medium')[:4].upper(), fg=priority_color)}] "
            f"{d['title'][:50]:<50} "
            f"→ {click.style(assigned_to, fg=assignment_color)}"
        )

    click.echo()
    click.echo("  [q] Cancel")
    click.echo()

    # Select deliverable
    try:
        choice = click.prompt("Select option", type=int, default=0, show_default=False)
        if choice == 0 or choice < 1 or choice > len(deliverables):
            return
    except:
        return

    selected = deliverables[choice - 1]

    click.echo()
    click.echo(click.style(f"  Selected: {selected['title']}", bold=True))
    click.echo(
        f"  Currently assigned to: {click.style(selected.get('assigned_to', 'Unassigned'), fg='cyan')}"
    )
    click.echo()

    # Get all team members
    users = _get_all_users_with_workload(engagement_id, tc)

    if not users:
        click.echo(click.style("  ⚠️  No team members found.", fg="yellow"))
        click.pause()
        return

    # Interactive selection with unassign option
    title_display = selected["title"][:35]
    if len(selected["title"]) > 35:
        title_display += "..."

    # Build options with unassign
    options = [
        {"label": "Unassign (remove assignment)", "value": "UNASSIGN", "workload": None}
    ]
    for u in users:
        options.append(
            {"label": u["user"], "value": u["user"], "workload": u.get("pending", 0)}
        )

    cursor = 0
    while True:
        DesignSystem.clear_screen()
        click.echo()
        click.echo(click.style(f"  REASSIGN '{title_display}'", bold=True, fg="cyan"))
        click.echo("  " + "─" * 50)
        click.echo()

        for idx, opt in enumerate(options):
            prefix = "▶ " if idx == cursor else "  "

            if opt["workload"] is not None:
                line = (
                    f"{prefix}{opt['label']:<25} (workload: {opt['workload']} pending)"
                )
            else:
                line = f"{prefix}{opt['label']}"

            if idx == cursor:
                click.echo(click.style(f"  {line}", fg="cyan", bold=True))
            else:
                click.echo(f"  {line}")

        click.echo()
        click.echo(
            click.style("  ↑↓ Navigate  Enter Select  q Cancel", fg="bright_black")
        )

        key = _get_key()

        if key in (KEY_UP, "k"):
            cursor = (cursor - 1) % len(options)
        elif key in (KEY_DOWN, "j"):
            cursor = (cursor + 1) % len(options)
        elif key in (KEY_ENTER, "\r", "\n"):
            selected_value = options[cursor]["value"]
            break
        elif key in ("q", KEY_ESCAPE):
            return

    if selected_value == "UNASSIGN":
        # Unassign
        dm.update_deliverable(selected["id"], assigned_to=None)
        tc.log_activity(
            engagement_id=engagement_id,
            activity_type="deliverable_unassigned",
            description=f"Deliverable unassigned: {selected['title']}",
            username=tc.current_user,
        )
        click.echo()
        click.echo(click.style(f"  ✓ Deliverable unassigned", fg="green"))
    else:
        # Reassign
        dm.update_deliverable(selected["id"], assigned_to=selected_value)
        tc.log_activity(
            engagement_id=engagement_id,
            activity_type="deliverable_reassigned",
            description=f"Deliverable '{selected['title']}' reassigned to {selected_value}",
            username=tc.current_user,
        )
        click.echo()
        click.echo(
            click.style(f"  ✓ Deliverable assigned to {selected_value}", fg="green")
        )

    click.pause()


def _reassign_all_deliverables(
    engagement_id: int, tc: TeamCollaboration, dm: DeliverableManager
):
    """Bulk reassign all deliverables to balance workload."""
    DesignSystem.clear_screen()

    width = DesignSystem.get_terminal_width()

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            " REASSIGN ALL DELIVERABLES ".center(width - 2), bold=True, fg="cyan"
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    # Get deliverables and all team members
    deliverables = dm.list_deliverables(engagement_id)
    workload_data = _get_all_users_with_workload(engagement_id, tc)

    if not deliverables:
        click.echo(click.style("  No deliverables found", fg="yellow"))
        click.pause()
        return

    if not workload_data:
        click.echo(click.style("  No team members found", fg="yellow"))
        click.pause()
        return

    # Show current assignment distribution
    click.echo(click.style("  CURRENT ASSIGNMENT DISTRIBUTION", bold=True, fg="cyan"))
    click.echo("  " + "─" * (width - 4))
    click.echo()

    for user_workload in workload_data:
        username = user_workload["user"]
        pending = user_workload.get("pending", 0)
        click.echo(f"  {username:<20} {pending:2d} pending deliverables")

    unassigned = len([d for d in deliverables if not d.get("assigned_to")])
    if unassigned:
        click.echo(f"  {'Unassigned':<20} {unassigned:2d} deliverables")

    click.echo()
    click.echo(click.style(f"  Total deliverables: {len(deliverables)}", bold=True))
    click.echo()

    # Reassignment options
    click.echo(click.style("  REASSIGNMENT METHOD", bold=True, fg="cyan"))
    click.echo("  " + "─" * (width - 4))
    click.echo()
    click.echo("  [1] Round-robin (distribute evenly)")
    click.echo("  [2] Reassign only unassigned")
    click.echo("  [3] Unassign all")
    click.echo("  [q] Cancel")
    click.echo()

    try:
        choice_input = (
            click.prompt("Select option", type=str, default="q", show_default=False)
            .strip()
            .lower()
        )

        if choice_input == "q":
            return

        choice = int(choice_input) if choice_input.isdigit() else 0

        if choice == 0:
            return
        elif choice == 1:
            # Round-robin: Reassign ALL deliverables evenly
            click.echo()
            if not click.confirm(
                click.style(
                    f"  ⚠️  This will reassign ALL {len(deliverables)} deliverables. Continue?",
                    fg="yellow",
                )
            ):
                return

            # Get list of unique users from workload
            users = [u["user"] for u in workload_data]

            if not users:
                click.echo(
                    click.style("  No users available for assignment", fg="yellow")
                )
                click.pause()
                return

            member_idx = 0
            reassigned_count = 0

            for deliv in deliverables:
                if deliv["status"] == "completed":
                    continue  # Don't reassign completed ones

                assignee = users[member_idx % len(users)]
                dm.update_deliverable(deliv["id"], assigned_to=assignee)
                member_idx += 1
                reassigned_count += 1

            tc.log_activity(
                engagement_id=engagement_id,
                activity_type="bulk_reassignment",
                description=f"Bulk reassignment: {reassigned_count} deliverables redistributed (round-robin)",
                username=tc.current_user,
            )

            click.echo()
            click.echo(
                click.style(
                    f"  ✓ Reassigned {reassigned_count} deliverables across {len(users)} members",
                    fg="green",
                )
            )

        elif choice == 2:
            # Reassign only unassigned
            unassigned_delivs = [
                d
                for d in deliverables
                if not d.get("assigned_to") and d["status"] != "completed"
            ]

            if not unassigned_delivs:
                click.echo()
                click.echo(
                    click.style("  No unassigned deliverables to reassign", fg="yellow")
                )
                click.pause()
                return

            click.echo()
            if not click.confirm(
                click.style(
                    f"  Reassign {len(unassigned_delivs)} unassigned deliverables?",
                    fg="yellow",
                )
            ):
                return

            # Get list of unique users from workload
            users = [u["user"] for u in workload_data]

            if not users:
                click.echo(
                    click.style("  No users available for assignment", fg="yellow")
                )
                click.pause()
                return

            member_idx = 0

            for deliv in unassigned_delivs:
                assignee = users[member_idx % len(users)]
                dm.update_deliverable(deliv["id"], assigned_to=assignee)
                member_idx += 1

            tc.log_activity(
                engagement_id=engagement_id,
                activity_type="bulk_assignment",
                description=f"Bulk assignment: {len(unassigned_delivs)} unassigned deliverables distributed",
                username=tc.current_user,
            )

            click.echo()
            click.echo(
                click.style(
                    f"  ✓ Assigned {len(unassigned_delivs)} deliverables", fg="green"
                )
            )

        elif choice == 3:
            # Unassign all
            click.echo()
            if not click.confirm(
                click.style(
                    f"  ⚠️  This will unassign ALL {len(deliverables)} deliverables. Continue?",
                    fg="red",
                )
            ):
                return

            unassigned_count = 0

            for deliv in deliverables:
                if deliv.get("assigned_to"):
                    dm.update_deliverable(deliv["id"], assigned_to=None)
                    unassigned_count += 1

            tc.log_activity(
                engagement_id=engagement_id,
                activity_type="bulk_unassignment",
                description=f"Bulk unassignment: {unassigned_count} deliverables unassigned",
                username=tc.current_user,
            )

            click.echo()
            click.echo(
                click.style(
                    f"  ✓ Unassigned {unassigned_count} deliverables", fg="green"
                )
            )

    except:
        pass

    click.pause()


def _view_comments(engagement_id: int, tc: TeamCollaboration, dm: DeliverableManager):
    """View and add comments on deliverables."""
    DesignSystem.clear_screen()

    width = DesignSystem.get_terminal_width()

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" DELIVERABLE COMMENTS ".center(width - 2), bold=True, fg="cyan")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    # Get deliverable ID
    deliverable_id = click.prompt("Enter deliverable ID", type=int)

    # Get deliverable
    deliverable = dm.get_deliverable(deliverable_id)
    if not deliverable or deliverable["engagement_id"] != engagement_id:
        click.echo(click.style("  Deliverable not found", fg="red"))
        click.pause()
        return

    click.echo()
    click.echo(f"  Deliverable: {click.style(deliverable['title'], bold=True)}")
    click.echo()

    # Get comments
    comments = tc.get_comments(deliverable_id)

    if comments:
        click.echo(click.style("  COMMENTS", bold=True, fg="cyan"))
        click.echo("  " + "─" * (width - 4))
        click.echo()

        for comment in comments:
            created_at = (
                comment["created_at"][:16]
                if len(comment["created_at"]) > 16
                else comment["created_at"]
            )

            click.echo(
                f"  [{click.style(created_at, fg='bright_black')}] "
                f"{click.style(comment['user'], bold=True)}"
            )
            click.echo(f"  {comment['comment']}")
            click.echo()
    else:
        click.echo(click.style("  No comments yet", fg="yellow"))
        click.echo()

    # Add comment
    if click.confirm("Add a comment?", default=False):
        click.echo()
        comment_text = click.prompt("Comment", type=str)

        if comment_text:
            tc.add_comment(deliverable_id, comment_text)
            tc.log_activity(
                deliverable_id=deliverable_id,
                engagement_id=engagement_id,
                action="commented",
                details=comment_text[:50],
            )

            click.echo()
            click.echo(click.style("  ✅ Comment added", fg="green"))

    click.pause()


def _full_activity_log(engagement_id: int, tc: TeamCollaboration):
    """Show full activity log."""
    DesignSystem.clear_screen()

    width = DesignSystem.get_terminal_width()

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" FULL ACTIVITY LOG ".center(width - 2), bold=True, fg="cyan")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    activity_feed = tc.get_recent_activity_feed(engagement_id, limit=50)

    if not activity_feed:
        click.echo(click.style("  No activity", fg="yellow"))
        click.pause()
        return

    for item in activity_feed:
        created_at = (
            item["created_at"][:19]
            if len(item["created_at"]) > 19
            else item["created_at"]
        )

        action_colors = {
            "started": "cyan",
            "completed": "green",
            "updated": "yellow",
            "assigned": "blue",
            "blocker_set": "red",
        }
        color = action_colors.get(item["action"], "white")

        click.echo(
            f"  [{click.style(created_at, fg='bright_black')}] "
            f"{click.style(item['message'], fg=color)}"
        )

    click.echo()
    click.pause()


def _workload_report(engagement_id: int, tc: TeamCollaboration):
    """Show detailed workload report."""
    DesignSystem.clear_screen()

    width = DesignSystem.get_terminal_width()

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" WORKLOAD REPORT ".center(width - 2), bold=True, fg="cyan")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    workload = tc.get_user_workload(engagement_id)

    if not workload:
        click.echo(click.style("  No assignments", fg="yellow"))
        click.pause()
        return

    for user_stats in workload:
        user = user_stats["user"]
        total = user_stats["total_assigned"]
        completed = user_stats["completed"]
        in_progress = user_stats["in_progress"]
        pending = user_stats["pending"]
        blocked = user_stats["blocked"]

        completion_rate = (completed / total * 100) if total > 0 else 0

        click.echo(click.style(f"  {user}", bold=True, fg="cyan"))
        click.echo("  " + "─" * (width - 4))
        click.echo()
        click.echo(f"  Total Assigned: {total}")
        click.echo(
            f"  Completed: {click.style(str(completed), fg='green')} ({completion_rate:.1f}%)"
        )
        click.echo(f"  In Progress: {click.style(str(in_progress), fg='cyan')}")
        click.echo(f"  Pending: {click.style(str(pending), fg='yellow')}")

        if blocked > 0:
            click.echo(f"  Blocked: {click.style(str(blocked), fg='red')}")

        click.echo()

    click.pause()
