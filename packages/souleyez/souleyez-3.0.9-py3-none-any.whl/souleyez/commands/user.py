"""
CLI commands for user management.

Commands (admin only):
- souleyez user create <username>   - Create new user
- souleyez user list                - List all users
- souleyez user update <username>   - Update user role/tier
- souleyez user delete <username>   - Delete user
- souleyez user passwd [username]   - Change password
"""

import getpass

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from souleyez.auth import (
    Role,
    Tier,
    UserManager,
    get_current_user,
    init_auth,
    is_logged_in,
)
from souleyez.licensing.validator import get_active_license
from souleyez.security import require_admin, require_login
from souleyez.storage.database import get_db

console = Console()


def _get_user_manager() -> UserManager:
    """Get user manager instance."""
    return UserManager(get_db().db_path)


@click.group()
def user():
    """User management commands."""
    pass


@user.command("create")
@require_login
@require_admin
@click.argument("username")
@click.option("--email", "-e", help="User email address")
@click.option(
    "--role",
    "-r",
    type=click.Choice(["admin", "lead", "analyst", "viewer"]),
    default="analyst",
    help="User role (default: analyst)",
)
@click.option(
    "--tier",
    "-t",
    type=click.Choice(["FREE", "PRO"]),
    default=None,
    help="License tier (auto-detects from active license)",
)
def user_create(username, email, role, tier):
    """Create a new user account."""
    import secrets

    user_mgr = _get_user_manager()

    # Determine tier: if not specified, check for active license
    if tier is None:
        active_license = get_active_license()
        if active_license and active_license.is_valid:
            tier = "PRO"
        else:
            tier = "FREE"

    # Generate a secure random password
    password = secrets.token_urlsafe(16)

    # Create user
    new_user, error = user_mgr.create_user(
        username=username,
        password=password,
        email=email,
        role=Role(role),
        tier=Tier(tier),
        skip_password_validation=True,  # Generated password is secure
    )

    if new_user is None:
        console.print(f"[red]❌ {error}[/red]")
        return

    # Log the action
    current = get_current_user()
    _log_audit(
        "user.created",
        current.id,
        current.username,
        f"Created user: {username} (role={role}, tier={tier})",
    )

    # Display credentials in a nice panel
    tier_display = "💎 PRO" if tier == "PRO" else "FREE"
    panel_content = (
        f"User account created successfully!\n\n"
        f"Username: {username}\n"
        f"Password: {password}\n"
        f"Role: {role.upper()}\n"
        f"Tier: {tier_display}\n\n"
        f"[yellow]⚠️  Save this password! It will not be shown again.[/yellow]\n\n"
        f"[dim]To change password after login:[/dim]\n"
        f"[dim]  • souleyez user passwd {username}[/dim]"
    )
    console.print(
        Panel(panel_content, title="🔐 New User Created", border_style="green")
    )


@user.command("list")
@require_login
@require_admin
@click.option("--all", "-a", "show_all", is_flag=True, help="Include inactive users")
def user_list(show_all):
    """List all users."""
    user_mgr = _get_user_manager()
    users = user_mgr.list_users(include_inactive=show_all)

    if not users:
        console.print("[yellow]No users found.[/yellow]")
        return

    table = Table(title="👥 Users")
    table.add_column("Username", style="bold")
    table.add_column("Role")
    table.add_column("Tier")
    table.add_column("Email")
    table.add_column("Status")
    table.add_column("Last Login")

    for u in users:
        tier_badge = "💎 PRO" if u.tier == Tier.PRO else "FREE"
        status = "[green]Active[/green]" if u.is_active else "[red]Disabled[/red]"
        if u.is_locked:
            status = "[yellow]Locked[/yellow]"
        last_login = (
            u.last_login.strftime("%Y-%m-%d %H:%M")
            if u.last_login
            else "[dim]Never[/dim]"
        )

        table.add_row(
            u.username,
            u.role.value.upper(),
            tier_badge,
            u.email or "[dim]-[/dim]",
            status,
            last_login,
        )

    console.print(table)
    console.print(f"\nTotal: {len(users)} user(s)")


@user.command("update")
@require_login
@require_admin
@click.argument("username")
@click.option(
    "--role",
    "-r",
    type=click.Choice(["admin", "lead", "analyst", "viewer"]),
    help="New role",
)
@click.option("--tier", "-t", type=click.Choice(["FREE", "PRO"]), help="New tier")
@click.option("--email", "-e", help="New email")
@click.option(
    "--activate/--deactivate", default=None, help="Activate or deactivate account"
)
def user_update(username, role, tier, email, activate):
    """Update a user's role, tier, or status."""
    user_mgr = _get_user_manager()

    target = user_mgr.get_user_by_username(username)
    if target is None:
        console.print(f"[red]❌ User '{username}' not found[/red]")
        return

    # Build update params
    updates = {}
    if role:
        updates["role"] = Role(role)
    if tier:
        updates["tier"] = Tier(tier)
    if email:
        updates["email"] = email
    if activate is not None:
        updates["is_active"] = activate

    if not updates:
        console.print(
            "[yellow]No changes specified. Use --role, --tier, --email, or --activate/--deactivate[/yellow]"
        )
        return

    success, error = user_mgr.update_user(target.id, **updates)

    if not success:
        console.print(f"[red]❌ {error}[/red]")
        return

    # Log the action
    current = get_current_user()
    _log_audit(
        "user.updated",
        current.id,
        current.username,
        f"Updated user: {username} ({updates})",
    )

    console.print(f"[green]✅ User '{username}' updated successfully![/green]")


@user.command("delete")
@require_login
@require_admin
@click.argument("username")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def user_delete(username, force):
    """Delete a user account."""
    user_mgr = _get_user_manager()
    current = get_current_user()

    # Prevent self-deletion
    if username.lower() == current.username.lower():
        console.print("[red]❌ Cannot delete your own account[/red]")
        return

    target = user_mgr.get_user_by_username(username)
    if target is None:
        console.print(f"[red]❌ User '{username}' not found[/red]")
        return

    # Confirm deletion
    if not force:
        if not click.confirm(f"Delete user '{username}'? This cannot be undone"):
            console.print("[yellow]Cancelled[/yellow]")
            return

    success, error = user_mgr.delete_user(target.id)

    if not success:
        console.print(f"[red]❌ {error}[/red]")
        return

    _log_audit(
        "user.deleted", current.id, current.username, f"Deleted user: {username}"
    )

    console.print(f"[green]✅ User '{username}' deleted[/green]")


@user.command("passwd")
@require_login
@click.argument("username", required=False)
def user_passwd(username):
    """Change password (own or another user's if admin)."""
    user_mgr = _get_user_manager()
    current = get_current_user()

    # Determine target user
    if username:
        # Changing another user's password - requires admin
        if current.role != Role.ADMIN:
            console.print(
                "[red]❌ Admin privileges required to change another user's password[/red]"
            )
            return
        target = user_mgr.get_user_by_username(username)
        if target is None:
            console.print(f"[red]❌ User '{username}' not found[/red]")
            return
        changing_own = False
    else:
        # Changing own password
        target = current
        username = current.username
        changing_own = True

    console.print(f"\nChanging password for: [bold]{username}[/bold]")

    # If changing own password, verify current password first
    if changing_own:
        current_pwd = getpass.getpass("Current password: ")
        user, _ = user_mgr.authenticate(current.username, current_pwd)
        if user is None:
            console.print("[red]❌ Current password is incorrect[/red]")
            return

    # Get new password
    console.print("[dim]Requirements: 8+ chars, upper, lower, digit, special[/dim]\n")
    new_password = getpass.getpass("New password: ")
    confirm = getpass.getpass("Confirm new password: ")

    if new_password != confirm:
        console.print("[red]❌ Passwords do not match[/red]")
        return

    success, error = user_mgr.change_password(target.id, new_password)

    if not success:
        console.print(f"[red]❌ {error}[/red]")
        return

    _log_audit(
        "user.password_changed",
        current.id,
        current.username,
        f"Password changed for: {username}",
    )

    console.print(f"[green]✅ Password changed successfully![/green]")


@user.command("upgrade")
@require_login
@require_admin
@click.argument("username")
@click.option("--reason", "-r", default="Admin action", help="Reason for upgrade")
def user_upgrade(username, reason):
    """Upgrade a user to Pro tier (Admin only)."""
    user_mgr = _get_user_manager()
    current = get_current_user()

    target = user_mgr.get_user_by_username(username)
    if target is None:
        console.print(f"[red]❌ User '{username}' not found[/red]")
        return

    if target.tier == Tier.PRO:
        console.print(f"[yellow]ℹ️  User '{username}' is already Pro tier[/yellow]")
        return

    # Upgrade to Pro
    success, error = user_mgr.set_user_tier(target.id, Tier.PRO)

    if not success:
        console.print(f"[red]❌ {error}[/red]")
        return

    _log_audit(
        "user.tier_upgraded",
        current.id,
        current.username,
        f"Upgraded '{username}' to PRO. Reason: {reason}",
    )

    console.print(f"[green]✅ User '{username}' upgraded to 💎 PRO[/green]")
    console.print(f"   Reason: {reason}")


@user.command("downgrade")
@require_login
@require_admin
@click.argument("username")
@click.option("--reason", "-r", default="Admin action", help="Reason for downgrade")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def user_downgrade(username, reason, force):
    """Downgrade a user to Free tier (Admin only)."""
    user_mgr = _get_user_manager()
    current = get_current_user()

    target = user_mgr.get_user_by_username(username)
    if target is None:
        console.print(f"[red]❌ User '{username}' not found[/red]")
        return

    if target.tier == Tier.FREE:
        console.print(f"[yellow]ℹ️  User '{username}' is already Free tier[/yellow]")
        return

    # Confirm downgrade
    if not force:
        console.print(
            f"\n[yellow]⚠️  This will remove Pro features for '{username}'[/yellow]"
        )
        if not click.confirm("Continue?"):
            console.print("[dim]Cancelled[/dim]")
            return

    # Downgrade to Free
    success, error = user_mgr.set_user_tier(target.id, Tier.FREE)

    if not success:
        console.print(f"[red]❌ {error}[/red]")
        return

    _log_audit(
        "user.tier_downgraded",
        current.id,
        current.username,
        f"Downgraded '{username}' to FREE. Reason: {reason}",
    )

    console.print(f"[green]✅ User '{username}' downgraded to FREE[/green]")
    console.print(f"   Reason: {reason}")


def _log_audit(action: str, user_id: str, username: str, details: str = None):
    """Log an audit event."""
    import sqlite3
    from datetime import datetime

    from souleyez.storage.database import get_db

    try:
        conn = sqlite3.connect(get_db().db_path)
        conn.execute(
            """
            INSERT INTO audit_log (user_id, username, action, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """,
            (user_id, username, action, details, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
