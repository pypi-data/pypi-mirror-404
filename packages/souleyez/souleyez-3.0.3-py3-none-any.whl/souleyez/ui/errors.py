#!/usr/bin/env python3
"""
souleyez.ui.errors - User-friendly error messages with fix suggestions

This module provides consistent, helpful error messages that guide users
toward solutions rather than just reporting problems.
"""

from typing import List, Optional

import click


class ErrorHelper:
    """
    Helper for displaying user-friendly error messages with fix suggestions.

    Usage:
        from souleyez.ui.errors import error_msg, ErrorType

        # Simple usage
        error_msg(ErrorType.ENGAGEMENT_NOT_FOUND)

        # With context
        error_msg(ErrorType.TOOL_NOT_FOUND, tool_name="nmap")

        # Custom error with suggestions
        error_msg(ErrorType.CUSTOM, message="Something went wrong",
                  suggestions=["Try this", "Or this"])
    """

    pass


class ErrorType:
    """Enum-like class for error types."""

    ENGAGEMENT_NOT_FOUND = "engagement_not_found"
    TOOL_NOT_FOUND = "tool_not_found"
    DATABASE_ERROR = "database_error"
    PERMISSION_DENIED = "permission_denied"
    CONFIG_ERROR = "config_error"
    NETWORK_ERROR = "network_error"
    AUTH_REQUIRED = "auth_required"
    SESSION_EXPIRED = "session_expired"
    NO_CURRENT_ENGAGEMENT = "no_current_engagement"
    METASPLOIT_ERROR = "metasploit_error"
    ENCRYPTION_ERROR = "encryption_error"
    IMPORT_ERROR = "import_error"
    CUSTOM = "custom"


# Error definitions with messages and suggestions
ERROR_DEFINITIONS = {
    ErrorType.ENGAGEMENT_NOT_FOUND: {
        "message": "Engagement not found",
        "suggestions": [
            "Run 'souleyez interactive' to create or select an engagement",
            "Use '[+] Create New' in the engagement menu",
            "Check the engagement ID is correct",
        ],
        "help_cmd": "souleyez interactive",
    },
    ErrorType.NO_CURRENT_ENGAGEMENT: {
        "message": "No engagement selected",
        "suggestions": [
            "Select an engagement first in the interactive menu",
            "Create a new engagement with '[+] Create New'",
            "Run 'souleyez interactive' to get started",
        ],
        "help_cmd": "souleyez interactive",
    },
    ErrorType.TOOL_NOT_FOUND: {
        "message": "Tool not installed or not found in PATH",
        "suggestions": [
            "Run 'souleyez setup' to install pentesting tools",
            "Check if the tool is installed: 'which {tool_name}'",
            "Run 'souleyez doctor' to diagnose installation issues",
        ],
        "help_cmd": "souleyez setup",
    },
    ErrorType.DATABASE_ERROR: {
        "message": "Database error occurred",
        "suggestions": [
            "Run 'souleyez doctor' to check database health",
            "Check ~/.souleyez/souleyez.db file permissions",
            "Try backing up and recreating the database",
        ],
        "help_cmd": "souleyez doctor",
    },
    ErrorType.PERMISSION_DENIED: {
        "message": "Permission denied",
        "suggestions": [
            "Check file/directory permissions",
            "Some tools require sudo - try running with elevated privileges",
            "Run 'souleyez doctor' to check for permission issues",
        ],
        "help_cmd": "souleyez doctor",
    },
    ErrorType.CONFIG_ERROR: {
        "message": "Configuration error",
        "suggestions": [
            "Check ~/.souleyez/config.json for syntax errors",
            "Run 'souleyez doctor' to validate configuration",
            "Delete config file to reset to defaults: rm ~/.souleyez/config.json",
        ],
        "help_cmd": "cat ~/.souleyez/config.json",
    },
    ErrorType.NETWORK_ERROR: {
        "message": "Network connection error",
        "suggestions": [
            "Check your internet connection",
            "Verify the target is reachable: ping {target}",
            "Check if a firewall is blocking the connection",
            "Try using a proxy if configured",
        ],
        "help_cmd": None,
    },
    ErrorType.AUTH_REQUIRED: {
        "message": "Authentication required",
        "suggestions": [
            "Log in with 'souleyez login'",
            "Create an account if you don't have one",
            "Check that your session hasn't expired",
        ],
        "help_cmd": "souleyez login",
    },
    ErrorType.SESSION_EXPIRED: {
        "message": "Session expired",
        "suggestions": [
            "Log in again with 'souleyez login'",
            "Increase session timeout in config if needed",
            "Check security.session_timeout_minutes in config",
        ],
        "help_cmd": "souleyez login",
    },
    ErrorType.METASPLOIT_ERROR: {
        "message": "Metasploit error",
        "suggestions": [
            "Check if Metasploit is installed: 'msfconsole -v'",
            "Initialize the MSF database: 'msfdb init'",
            "Run 'souleyez doctor --verbose' for MSF diagnostics",
            "Try running msfconsole directly to see errors",
        ],
        "help_cmd": "souleyez doctor --verbose",
    },
    ErrorType.ENCRYPTION_ERROR: {
        "message": "Encryption/decryption error",
        "suggestions": [
            "Make sure you're using the correct master password",
            "The credential vault may be locked - unlock it first",
            "If you forgot your password, credentials cannot be recovered",
        ],
        "help_cmd": None,
    },
    ErrorType.IMPORT_ERROR: {
        "message": "Failed to import required module",
        "suggestions": [
            "Run 'pip install souleyez' or 'pip install -e .' to install dependencies",
            "Check that all requirements are installed",
            "Run 'souleyez doctor' to check for missing packages",
        ],
        "help_cmd": "souleyez doctor",
    },
    ErrorType.CUSTOM: {
        "message": "An error occurred",
        "suggestions": [],
        "help_cmd": "souleyez doctor",
    },
}


def error_msg(
    error_type: str,
    message: Optional[str] = None,
    suggestions: Optional[List[str]] = None,
    show_help: bool = True,
    **context,
) -> None:
    """
    Display a user-friendly error message with fix suggestions.

    Args:
        error_type: One of ErrorType constants
        message: Override the default message
        suggestions: Override or add to default suggestions
        show_help: Whether to show the help command
        **context: Variables to substitute in messages (e.g., tool_name="nmap")
    """
    # Get error definition
    error_def = ERROR_DEFINITIONS.get(error_type, ERROR_DEFINITIONS[ErrorType.CUSTOM])

    # Determine message
    final_message = message or error_def["message"]

    # Substitute context variables in message
    for key, value in context.items():
        final_message = final_message.replace(f"{{{key}}}", str(value))

    # Display error
    click.echo()
    click.echo(click.style(f"  ✗ {final_message}", fg="red", bold=True))

    # Get and display suggestions
    final_suggestions = suggestions or error_def["suggestions"]
    if final_suggestions:
        click.echo()
        click.echo(click.style("  How to fix:", fg="yellow"))
        for i, suggestion in enumerate(final_suggestions[:4], 1):
            # Substitute context variables in suggestion
            for key, value in context.items():
                suggestion = suggestion.replace(f"{{{key}}}", str(value))
            click.echo(f"    {i}. {suggestion}")

    # Show help command
    help_cmd = error_def.get("help_cmd")
    if show_help and help_cmd:
        # Substitute context variables
        for key, value in context.items():
            help_cmd = help_cmd.replace(f"{{{key}}}", str(value))
        click.echo()
        click.echo(
            click.style(f"  Quick fix: ", fg="cyan")
            + click.style(help_cmd, fg="white", bold=True)
        )

    click.echo()


def warn_msg(message: str, suggestions: Optional[List[str]] = None) -> None:
    """
    Display a warning message with optional suggestions.

    Args:
        message: The warning message
        suggestions: Optional list of suggestions
    """
    click.echo()
    click.echo(click.style(f"  ⚠ {message}", fg="yellow", bold=True))

    if suggestions:
        click.echo()
        for suggestion in suggestions[:3]:
            click.echo(f"    - {suggestion}")

    click.echo()


def success_msg(message: str, next_steps: Optional[List[str]] = None) -> None:
    """
    Display a success message with optional next steps.

    Args:
        message: The success message
        next_steps: Optional list of next steps
    """
    click.echo()
    click.echo(click.style(f"  ✓ {message}", fg="green", bold=True))

    if next_steps:
        click.echo()
        click.echo(click.style("  Next steps:", fg="cyan"))
        for i, step in enumerate(next_steps[:3], 1):
            click.echo(f"    {i}. {step}")

    click.echo()


def info_msg(message: str, details: Optional[List[str]] = None) -> None:
    """
    Display an info message with optional details.

    Args:
        message: The info message
        details: Optional list of details
    """
    click.echo()
    click.echo(click.style(f"  ℹ {message}", fg="cyan"))

    if details:
        for detail in details[:5]:
            click.echo(f"    {detail}")

    click.echo()


# Convenience functions for common errors
def engagement_not_found(engagement_id: Optional[int] = None) -> None:
    """Show engagement not found error with fix suggestions."""
    msg = (
        f"Engagement ID {engagement_id} not found"
        if engagement_id
        else "Engagement not found"
    )
    error_msg(ErrorType.ENGAGEMENT_NOT_FOUND, message=msg)


def tool_not_found(tool_name: str) -> None:
    """Show tool not found error with fix suggestions."""
    error_msg(
        ErrorType.TOOL_NOT_FOUND,
        tool_name=tool_name,
        message=f"Tool '{tool_name}' not installed or not found in PATH",
    )


def no_engagement_selected() -> None:
    """Show no engagement selected error with fix suggestions."""
    error_msg(ErrorType.NO_CURRENT_ENGAGEMENT)


def database_error(error: Optional[Exception] = None) -> None:
    """Show database error with fix suggestions."""
    msg = f"Database error: {error}" if error else None
    error_msg(ErrorType.DATABASE_ERROR, message=msg)


def permission_error(path: Optional[str] = None) -> None:
    """Show permission error with fix suggestions."""
    msg = f"Permission denied: {path}" if path else None
    error_msg(ErrorType.PERMISSION_DENIED, message=msg)


def metasploit_error(error: Optional[str] = None) -> None:
    """Show Metasploit error with fix suggestions."""
    msg = f"Metasploit error: {error}" if error else None
    error_msg(ErrorType.METASPLOIT_ERROR, message=msg)
