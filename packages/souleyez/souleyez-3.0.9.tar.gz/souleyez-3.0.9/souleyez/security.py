#!/usr/bin/env python3
"""
Security utilities for password protection and authentication.
"""

import functools
import getpass
import sys

import click

from souleyez.storage.crypto import get_crypto_manager


def unlock_credentials_if_needed():
    """
    Prompt for master password if credentials are encrypted and locked.

    Returns:
        bool: True if unlocked successfully, False otherwise
    """
    crypto = get_crypto_manager()

    if not crypto.is_encryption_enabled():
        # Encryption not enabled, no unlock needed
        return True

    if crypto.is_unlocked():
        # Already unlocked
        return True

    # Need to unlock
    click.echo(click.style("🔒 Credentials are encrypted.", fg="yellow"))

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            password = getpass.getpass("Enter master password: ")
            if crypto.unlock(password):
                click.echo(click.style("✅ Unlocked successfully!", fg="green"))
                return True
            else:
                remaining = max_attempts - attempt - 1
                if remaining > 0:
                    click.echo(
                        click.style(
                            f"❌ Incorrect password. {remaining} attempts remaining.",
                            fg="red",
                        )
                    )
                else:
                    click.echo(click.style("❌ Access denied.", fg="red"))
        except KeyboardInterrupt:
            click.echo("\n❌ Cancelled by user.")
            return False

    return False


def require_password(f):
    """
    Decorator to require password authentication for sensitive commands.

    This decorator protects commands that access sensitive data such as:
    - Credentials
    - Findings/vulnerabilities
    - Reports
    - OSINT data
    - Screenshots (may contain sensitive information)
    - Deliverables
    - Dashboard (live view of all data)

    Usage:
        @cli.group()
        @require_password
        def findings():
            ...

    Args:
        f: The function to wrap

    Returns:
        The wrapped function that requires authentication
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not unlock_credentials_if_needed():
            click.echo(
                click.style(
                    "\n⚠️  Authentication required to access this command.", fg="yellow"
                )
            )
            click.echo(
                click.style(
                    "   This command accesses sensitive data and requires master password.",
                    fg="yellow",
                )
            )
            sys.exit(1)
        return f(*args, **kwargs)

    return wrapper
