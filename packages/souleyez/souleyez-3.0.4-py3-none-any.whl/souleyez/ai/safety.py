#!/usr/bin/env python3
"""
souleyez.ai.safety - Safety framework for AI-driven command execution
"""

from enum import Enum
from typing import Dict, Optional

import click

from souleyez.ui.design_system import DesignSystem


class RiskLevel(Enum):
    """Risk levels for actions."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ApprovalMode(Enum):
    """Approval modes."""

    MANUAL = "manual"  # Ask for every action
    AUTO_LOW = "auto_low"  # Auto-approve LOW only
    AUTO_MEDIUM = "auto_medium"  # Auto-approve LOW + MEDIUM
    DRY_RUN = "dry_run"  # Show but don't execute


class SafetyFramework:
    """
    Safety framework for command execution.

    Handles risk assessment and approval prompts.
    """

    def __init__(self, approval_mode: ApprovalMode = ApprovalMode.MANUAL):
        """
        Initialize safety framework.

        Args:
            approval_mode: How to handle approvals
        """
        self.approval_mode = approval_mode

    def assess_risk(self, action: str, command: str) -> RiskLevel:
        """
        Assess risk level of an action.

        Args:
            action: AI recommendation action text
            command: Actual command to execute

        Returns:
            RiskLevel enum
        """
        # Simple heuristic-based risk assessment
        # In the future, this could use AI or more sophisticated rules

        action_lower = action.lower()
        command_lower = command.lower()

        # HIGH risk patterns
        high_risk_patterns = [
            "rm ",
            "delete",
            "drop",
            "exploit",
            "payload",
            "shell",
            "reverse",
            "meterpreter",
            "privilege",
            "escalat",
            "root",
            "admin",
            "sudo",
            "persistence",
        ]

        for pattern in high_risk_patterns:
            if pattern in action_lower or pattern in command_lower:
                return RiskLevel.HIGH

        # MEDIUM risk patterns
        medium_risk_patterns = [
            "password",
            "credential",
            "login",
            "auth",
            "brute",
            "test",
            "try",
            "attempt",
        ]

        for pattern in medium_risk_patterns:
            if pattern in action_lower or pattern in command_lower:
                return RiskLevel.MEDIUM

        # Everything else is LOW (enumeration, scanning)
        return RiskLevel.LOW

    def require_approval(
        self, action: str, target: str, command: str, risk_level: RiskLevel
    ) -> bool:
        """
        Check if action requires approval and prompt user if needed.

        Args:
            action: Human-readable action description
            target: Target of the action
            command: Actual command to execute
            risk_level: Assessed risk level

        Returns:
            True if approved (execute), False if rejected
        """
        # Dry-run mode: never execute
        if self.approval_mode == ApprovalMode.DRY_RUN:
            click.echo(
                click.style("\n[DRY-RUN] Would execute but skipping", fg="yellow")
            )
            return False

        # Auto-approval logic
        if self.approval_mode == ApprovalMode.AUTO_MEDIUM:
            if risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
                click.echo(
                    click.style(
                        f"\n✅ {risk_level.value} risk - Auto-approved\n", fg="green"
                    )
                )
                return True

        if self.approval_mode == ApprovalMode.AUTO_LOW:
            if risk_level == RiskLevel.LOW:
                click.echo(
                    click.style(
                        f"\n✅ {risk_level.value} risk - Auto-approved\n", fg="green"
                    )
                )
                return True

        # Manual approval required
        self._show_approval_prompt(action, target, command, risk_level)

        while True:
            choice = click.prompt(
                click.style("\nExecute this command?", fg="yellow"),
                type=click.Choice(["y", "n", "skip", "abort"], case_sensitive=False),
                show_choices=True,
            )

            if choice == "y":
                return True
            elif choice == "n" or choice == "skip":
                click.echo(click.style("⏭  Skipped", fg="yellow"))
                return False
            elif choice == "abort":
                click.echo(click.style("\n🛑 Execution aborted by user", fg="red"))
                raise KeyboardInterrupt("User aborted execution")

    def _show_approval_prompt(
        self, action: str, target: str, command: str, risk_level: RiskLevel
    ):
        """Show formatted approval prompt."""
        # Risk indicator
        if risk_level == RiskLevel.HIGH:
            risk_color = "red"
            risk_icon = "🚨"
        elif risk_level == RiskLevel.MEDIUM:
            risk_color = "yellow"
            risk_icon = "⚠️ "
        else:
            risk_color = "green"
            risk_icon = "ℹ️ "

        click.echo()
        click.echo(DesignSystem.separator(60))
        click.echo(
            f"{risk_icon} {click.style(f'{risk_level.value} RISK', fg=risk_color, bold=True)} - Approval Required"
        )
        click.echo(DesignSystem.separator(60))
        click.echo(f"ACTION: {action}")
        click.echo(f"TARGET: {target}")
        click.echo(f"\n📋 Command to execute:")
        click.echo(click.style(f"   {command}", fg="cyan", bold=True))
        click.echo(DesignSystem.separator(60))
