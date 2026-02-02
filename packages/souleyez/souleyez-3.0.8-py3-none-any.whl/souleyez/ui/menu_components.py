"""
Reusable menu UI components for consistent layouts.
"""

from typing import Dict, List

import click

from souleyez.ui.design_system import DesignSystem


class StandardMenu:
    """Standard menu renderer with consistent formatting."""

    @staticmethod
    def render(
        options: List[Dict[str, str]],
        show_back: bool = True,
        shortcuts: Dict[str, int] = None,
        show_shortcuts: bool = True,
        tip: str = None,
    ):
        """
        Render a standardized menu with single OPTIONS section.

        Args:
            options: List of dicts with 'number', 'label', 'description'
                    [{'number': 1, 'label': 'View Details', 'description': 'Select and view item'}]
            show_back: Whether to show [q] ← Back to Main Menu
            shortcuts: Optional dict mapping keyboard shortcuts to option numbers
                      e.g., {'n': 8, 'p': 9} for next/previous page
            show_shortcuts: Whether to display the shortcuts hint line (default True)
            tip: Optional tip text to display at the bottom before the prompt

        Returns:
            int: User's choice
        """
        width = DesignSystem.get_terminal_width()

        click.echo()
        click.echo(click.style("⚙️  OPTIONS", bold=True, fg="cyan"))
        click.echo("─" * width)
        click.echo()

        for opt in options:
            number = opt["number"]
            label = opt["label"]
            desc = opt.get("description", "")

            if desc:
                click.echo(f"  [{number}] {label} - {desc}")
            else:
                click.echo(f"  [{number}] {label}")

        click.echo()
        click.echo("─" * width)

        if show_back:
            click.echo()
            click.echo("  [q] ← Back to Main Menu")

        # Show shortcuts if provided and show_shortcuts is True
        if shortcuts and show_shortcuts:
            click.echo()
            shortcut_hints = []
            for key, option_num in shortcuts.items():
                # Map common shortcuts to their actions
                if key == "n":
                    shortcut_hints.append(f"'{key}' = Next Page")
                elif key == "p":
                    shortcut_hints.append(f"'{key}' = Previous Page")
                elif key == ">":
                    shortcut_hints.append("'>' = Next Page")
                elif key == "<":
                    shortcut_hints.append("'<' = Previous Page")
                elif key == "?":
                    shortcut_hints.append("'?' = Help")
                else:
                    # For other shortcuts, try to find the label
                    for opt in options:
                        if opt["number"] == option_num:
                            shortcut_hints.append(f"'{key}' = {opt['label']}")
                            break
            if shortcut_hints:
                click.echo("  Shortcuts: " + ", ".join(shortcut_hints))

        # Show tip if provided
        if tip:
            click.echo()
            click.echo("  " + click.style("💡 TIP:", fg="cyan", bold=True) + " " + tip)

        click.echo()

        try:
            choice_input = click.prompt(
                "Select option", type=str, default="0", show_default=False
            )

            # Handle keyboard shortcuts
            if shortcuts and choice_input.lower() in shortcuts:
                return shortcuts[choice_input.lower()]

            # Otherwise parse as integer
            return int(choice_input)
        except (ValueError, click.Abort):
            return 0
