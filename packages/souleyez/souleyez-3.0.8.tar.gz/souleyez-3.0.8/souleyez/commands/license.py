"""
License management CLI commands.

souleyez license activate <key>   - Activate a license
souleyez license status           - Show license status
souleyez license deactivate       - Remove license
souleyez license machine-id       - Show machine ID for hardware-bound licenses
"""

from datetime import datetime

import click


@click.group()
def license():
    """Manage your SoulEyez license."""
    pass


@license.command()
@click.argument("license_key")
def activate(license_key: str):
    """Activate a Pro license key."""
    from souleyez.licensing import activate_license, validate_license

    click.echo()
    click.echo(click.style("  Activating license...", fg="cyan"))

    # Validate and save
    success, message = activate_license(license_key)

    if success:
        info = validate_license(license_key)
        click.echo()
        click.echo(
            click.style("  License activated successfully!", fg="green", bold=True)
        )
        click.echo()
        click.echo(f"  Email:   {info.email}")
        click.echo(f"  Tier:    {click.style(info.tier, fg='magenta', bold=True)}")

        if info.expires_at:
            days = info.days_remaining
            if days > 30:
                color = "green"
            elif days > 7:
                color = "yellow"
            else:
                color = "red"
            click.echo(
                f"  Expires: {info.expires_at.strftime('%Y-%m-%d')} ({click.style(f'{days} days', fg=color)})"
            )
        else:
            click.echo(f"  Expires: {click.style('Never (perpetual)', fg='green')}")

        click.echo()
        click.echo(click.style("  Pro features are now unlocked!", fg="cyan"))
        click.echo()

        # Update user tier if auth system is in use
        try:
            from souleyez.auth import UserManager, get_current_user
            from souleyez.auth.permissions import Tier
            from souleyez.storage.database import get_db

            user = get_current_user()
            if user:
                user_mgr = UserManager(get_db().db_path)
                user_mgr.set_user_tier(
                    user.id,
                    Tier.PRO,
                    license_key=license_key[:20]
                    + "...",  # Store truncated key as reference
                    expires_at=info.expires_at,
                    _bypass_validation=True,  # Already validated by licensing module
                )
        except Exception:
            pass  # Auth system not in use

    else:
        click.echo()
        click.echo(click.style(f"  License activation failed: {message}", fg="red"))
        click.echo()
        click.echo("  Please check your license key and try again.")
        click.echo("  Contact support if the problem persists.")
        click.echo()


@license.command()
def status():
    """Show current license status."""
    from souleyez.licensing import get_active_license

    click.echo()
    info = get_active_license()

    if info is None:
        click.echo(click.style("  No active license", fg="yellow"))
        click.echo()
        click.echo("  You are using the FREE tier.")
        click.echo("  Upgrade to Pro: https://www.cybersoulsecurity.com/souleyez")
        click.echo()
        click.echo("  Activate with: souleyez license activate <key>")
        click.echo()
        return

    if not info.is_valid:
        click.echo(click.style(f"  License invalid: {info.error}", fg="red"))
        click.echo()
        click.echo("  Please reactivate or contact support.")
        click.echo()
        return

    # Valid license
    click.echo(click.style("  License Status: ACTIVE", fg="green", bold=True))
    click.echo()
    click.echo(f"  Email:   {info.email}")
    click.echo(f"  Tier:    {click.style(info.tier, fg='magenta', bold=True)}")

    if info.expires_at:
        days = info.days_remaining
        if days > 30:
            color = "green"
        elif days > 7:
            color = "yellow"
        else:
            color = "red"
        click.echo(
            f"  Expires: {info.expires_at.strftime('%Y-%m-%d')} ({click.style(f'{days} days remaining', fg=color)})"
        )
    else:
        click.echo(f"  Expires: {click.style('Never (perpetual)', fg='green')}")

    if info.machine_id:
        click.echo(f"  Bound:   Machine-specific license")

    click.echo()


@license.command()
def deactivate():
    """Remove your license (revert to FREE tier)."""
    from souleyez.licensing import deactivate_license, get_active_license

    info = get_active_license()
    if info is None:
        click.echo()
        click.echo(click.style("  No active license to remove.", fg="yellow"))
        click.echo()
        return

    # Confirm
    click.echo()
    click.echo(
        click.style("  Warning: This will remove your Pro license.", fg="yellow")
    )
    click.echo(f"  License: {info.email}")
    click.echo()

    if not click.confirm("  Are you sure?"):
        click.echo("  Cancelled.")
        return

    if deactivate_license():
        click.echo()
        click.echo(click.style("  License removed.", fg="green"))
        click.echo("  You are now on the FREE tier.")
        click.echo()

        # Reset ALL users with PRO tier to FREE
        try:
            from souleyez.auth import UserManager
            from souleyez.storage.database import get_db

            user_mgr = UserManager(get_db().db_path)
            count, _ = user_mgr.reset_all_pro_tiers()
            if count > 0:
                click.echo(f"  Reset {count} user(s) to FREE tier.")
        except Exception:
            pass  # Auth system not in use
    else:
        click.echo()
        click.echo(click.style("  Failed to remove license.", fg="red"))
        click.echo()


@license.command("machine-id")
def machine_id():
    """Show this machine's ID for hardware-bound licenses."""
    from souleyez.licensing.validator import get_machine_id

    mid = get_machine_id()

    click.echo()
    click.echo("  Machine ID (for hardware-bound licenses):")
    click.echo()
    click.echo(f"    {mid}")
    click.echo()
    click.echo("  Provide this to get a machine-specific license.")
    click.echo()
