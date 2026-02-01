"""
CLI commands for authentication.

Commands:
- souleyez login     - Log in to SoulEyez
- souleyez logout    - Log out of current session
- souleyez whoami    - Show current user info
"""

import getpass

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from souleyez.auth import (
    Tier,
    UserManager,
    get_current_user,
    get_session_manager,
    init_auth,
    is_logged_in,
)
from souleyez.storage.database import get_db

console = Console()


def _ensure_auth_initialized():
    """Initialize auth system if not already done."""
    try:
        get_session_manager()
    except RuntimeError:
        init_auth(get_db().db_path)


@click.command()
def login():
    """Log in to SoulEyez."""
    _ensure_auth_initialized()

    session_mgr = get_session_manager()

    # Check if already logged in
    if is_logged_in():
        user = get_current_user()
        console.print(f"[yellow]Already logged in as {user.username}[/yellow]")
        if not click.confirm("Log out and log in as a different user?"):
            return
        session_mgr.logout()

    # Check for first-run (no users exist)
    user_mgr = UserManager(get_db().db_path)
    if user_mgr.get_user_count() == 0:
        console.print(
            "[yellow]No users found. Creating default admin account...[/yellow]"
        )
        created, password = user_mgr.ensure_default_admin()
        if created:
            console.print(
                Panel(
                    f"[green]Default admin account created![/green]\n\n"
                    f"Username: [bold]admin[/bold]\n"
                    f"Password: [bold]{password}[/bold]\n\n"
                    f"[red]⚠️  Save this password! It will not be shown again.[/red]",
                    title="🔐 First Run Setup",
                    border_style="green",
                )
            )

    # Prompt for credentials
    console.print("\n[bold]🔐 SoulEyez Login[/bold]\n")

    username = click.prompt("Username")
    password = getpass.getpass("Password: ")

    # Authenticate
    user, error = user_mgr.authenticate(username, password)

    if user is None:
        console.print(f"[red]❌ {error}[/red]")
        return

    # Create session
    session = session_mgr.create_session(user)
    session_mgr.set_current_user(user)

    # Log the login
    _log_audit("user.login", user.id, user.username)

    # Show success
    tier_badge = "💎 PRO" if user.tier == Tier.PRO else "FREE"
    console.print(f"\n[green]✅ Welcome, {user.username}![/green]")
    console.print(f"   Role: [cyan]{user.role.value.upper()}[/cyan]")
    console.print(f"   Tier: [magenta]{tier_badge}[/magenta]")
    console.print(
        f"   Session expires: {session.expires_at.strftime('%Y-%m-%d %H:%M')}\n"
    )


@click.command()
def logout():
    """Log out of current session."""
    _ensure_auth_initialized()

    session_mgr = get_session_manager()
    user = get_current_user()

    if user is None:
        console.print("[yellow]Not logged in.[/yellow]")
        return

    username = user.username
    session_mgr.logout()

    _log_audit("user.logout", user.id, username)

    console.print(f"[green]✅ Logged out. Goodbye, {username}![/green]")


@click.command()
def whoami():
    """Show current user information."""
    _ensure_auth_initialized()

    user = get_current_user()

    if user is None:
        console.print("[yellow]Not logged in.[/yellow]")
        console.print("Run [cyan]souleyez login[/cyan] to authenticate.")
        return

    # Build info table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="dim")
    table.add_column("Value")

    tier_badge = "💎 PRO" if user.tier == Tier.PRO else "FREE"

    table.add_row("Username", f"[bold]{user.username}[/bold]")
    table.add_row("Role", f"[cyan]{user.role.value.upper()}[/cyan]")
    table.add_row("Tier", f"[magenta]{tier_badge}[/magenta]")
    table.add_row("Email", user.email or "[dim]Not set[/dim]")
    table.add_row(
        "Last Login",
        (
            user.last_login.strftime("%Y-%m-%d %H:%M")
            if user.last_login
            else "[dim]Never[/dim]"
        ),
    )
    table.add_row(
        "Account Status",
        "[green]Active[/green]" if user.is_active else "[red]Disabled[/red]",
    )

    if user.license_expires_at:
        table.add_row("License Expires", user.license_expires_at.strftime("%Y-%m-%d"))

    console.print(Panel(table, title="👤 Current User", border_style="blue"))


def _log_audit(action: str, user_id: str, username: str, details: str = None):
    """Log an audit event."""
    import sqlite3
    from datetime import datetime

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
        pass  # Don't fail if audit logging fails
