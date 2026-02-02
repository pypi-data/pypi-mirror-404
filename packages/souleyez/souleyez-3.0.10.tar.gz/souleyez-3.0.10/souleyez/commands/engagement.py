"""
CLI commands for engagement team management.

Commands:
- souleyez engagement team list <name>           - List team members
- souleyez engagement team add <name> <user>     - Add team member
- souleyez engagement team remove <name> <user>  - Remove team member
- souleyez engagement team transfer <name> <user> - Transfer ownership
"""

import click
from rich.console import Console
from rich.table import Table

from souleyez.auth import Role, UserManager, get_current_user
from souleyez.auth.engagement_access import (
    EngagementAccessManager,
    EngagementPermission,
)
from souleyez.security import require_login
from souleyez.storage.database import get_db
from souleyez.storage.engagements import EngagementManager

console = Console()


@click.group()
def team():
    """Manage engagement team members."""
    pass


@team.command("list")
@require_login
@click.argument("engagement_name")
def team_list(engagement_name):
    """List team members for an engagement."""
    em = EngagementManager()
    eng = em.get(engagement_name)

    if not eng:
        console.print(f"[red]❌ Engagement '{engagement_name}' not found[/red]")
        return

    # Check access
    if not em.can_access(eng["id"]):
        console.print("[red]❌ You don't have access to this engagement[/red]")
        return

    access_mgr = EngagementAccessManager(get_db().db_path)
    members = access_mgr.get_team_members(eng["id"])

    if not members:
        console.print(f"[yellow]No team members found for '{engagement_name}'[/yellow]")
        return

    table = Table(title=f"👥 Team: {engagement_name}")
    table.add_column("Username", style="bold")
    table.add_column("Email")
    table.add_column("Role")
    table.add_column("Added")

    for m in members:
        role_style = {"owner": "green bold", "editor": "cyan", "viewer": "dim"}.get(
            m["permission_level"], "white"
        )

        table.add_row(
            m["username"],
            m["email"] or "-",
            f"[{role_style}]{m['permission_level'].upper()}[/{role_style}]",
            m["granted_at"][:10] if m["granted_at"] else "-",
        )

    console.print(table)
    console.print(f"\nTotal: {len(members)} member(s)")


@team.command("add")
@require_login
@click.argument("engagement_name")
@click.argument("username")
@click.option(
    "--role",
    "-r",
    type=click.Choice(["editor", "viewer"]),
    default="viewer",
    help="Permission level (default: viewer)",
)
def team_add(engagement_name, username, role):
    """Add a user to an engagement's team."""
    em = EngagementManager()
    eng = em.get(engagement_name)

    if not eng:
        console.print(f"[red]❌ Engagement '{engagement_name}' not found[/red]")
        return

    # Check if user can manage team
    access_mgr = EngagementAccessManager(get_db().db_path)
    user = get_current_user()

    if not access_mgr.can_manage_team(eng["id"], user.id, user.role):
        console.print(
            "[red]❌ Only the engagement owner or admin can manage team members[/red]"
        )
        return

    # Find target user
    user_mgr = UserManager(get_db().db_path)
    target = user_mgr.get_user_by_username(username)

    if not target:
        console.print(f"[red]❌ User '{username}' not found[/red]")
        return

    # Add team member
    perm = (
        EngagementPermission.EDITOR if role == "editor" else EngagementPermission.VIEWER
    )
    success, error = access_mgr.add_team_member(eng["id"], target.id, perm, user.id)

    if success:
        console.print(
            f"[green]✅ Added {username} as {role} to '{engagement_name}'[/green]"
        )
    else:
        console.print(f"[red]❌ Failed: {error}[/red]")


@team.command("remove")
@require_login
@click.argument("engagement_name")
@click.argument("username")
def team_remove(engagement_name, username):
    """Remove a user from an engagement's team."""
    em = EngagementManager()
    eng = em.get(engagement_name)

    if not eng:
        console.print(f"[red]❌ Engagement '{engagement_name}' not found[/red]")
        return

    access_mgr = EngagementAccessManager(get_db().db_path)
    user = get_current_user()

    if not access_mgr.can_manage_team(eng["id"], user.id, user.role):
        console.print(
            "[red]❌ Only the engagement owner or admin can manage team members[/red]"
        )
        return

    user_mgr = UserManager(get_db().db_path)
    target = user_mgr.get_user_by_username(username)

    if not target:
        console.print(f"[red]❌ User '{username}' not found[/red]")
        return

    success, error = access_mgr.remove_team_member(eng["id"], target.id)

    if success:
        console.print(f"[green]✅ Removed {username} from '{engagement_name}'[/green]")
    else:
        console.print(f"[red]❌ Failed: {error}[/red]")


@team.command("transfer")
@require_login
@click.argument("engagement_name")
@click.argument("new_owner_username")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def team_transfer(engagement_name, new_owner_username, force):
    """Transfer engagement ownership to another user."""
    em = EngagementManager()
    eng = em.get(engagement_name)

    if not eng:
        console.print(f"[red]❌ Engagement '{engagement_name}' not found[/red]")
        return

    access_mgr = EngagementAccessManager(get_db().db_path)
    user = get_current_user()

    # Only owner or admin can transfer
    if not access_mgr.can_manage_team(eng["id"], user.id, user.role):
        console.print(
            "[red]❌ Only the engagement owner or admin can transfer ownership[/red]"
        )
        return

    user_mgr = UserManager(get_db().db_path)
    new_owner = user_mgr.get_user_by_username(new_owner_username)

    if not new_owner:
        console.print(f"[red]❌ User '{new_owner_username}' not found[/red]")
        return

    if not force:
        if not click.confirm(
            f"Transfer ownership of '{engagement_name}' to {new_owner_username}?"
        ):
            console.print("[yellow]Cancelled[/yellow]")
            return

    success, error = access_mgr.transfer_ownership(eng["id"], new_owner.id, user.id)

    if success:
        console.print(
            f"[green]✅ Ownership transferred to {new_owner_username}[/green]"
        )
        console.print(f"   You have been added as an editor.")
    else:
        console.print(f"[red]❌ Failed: {error}[/red]")
