#!/usr/bin/env python3
"""
souleyez.ui.design_system - Centralized design system for consistent UI
"""

import os
from typing import List

from rich import box
from rich.console import Console
from rich.table import Table

# Shared console instance
_console = None


class DesignSystem:
    """Centralized design system for SoulEyez UI."""

    # Box Styles
    HEADER_BOX = box.DOUBLE  # ╔═╗ - App header only
    TABLE_BOX = box.SIMPLE  # ─── - All tables

    # Widths
    DEFAULT_WIDTH = 100  # Default terminal width
    MIN_WIDTH = 80  # Minimum supported width

    # Separators
    SECTION_SEP = "─"  # Section separator character

    # Spacing
    SECTION_SPACING = 2  # Blank lines between sections
    CONTENT_SPACING = 1  # Blank lines after separator

    @staticmethod
    def get_terminal_width() -> int:
        """Get current terminal width, fallback to DEFAULT_WIDTH."""
        try:
            width = os.get_terminal_size().columns
            return max(width, DesignSystem.MIN_WIDTH)
        except:
            return DesignSystem.DEFAULT_WIDTH

    @staticmethod
    def separator(width: int = None) -> str:
        """Generate section separator line."""
        w = width or DesignSystem.get_terminal_width()
        return DesignSystem.SECTION_SEP * w

    @staticmethod
    def clear_screen():
        """
        Clear screen and reset scroll position to top.

        Uses system 'clear' command for maximum compatibility with all terminals
        including iTerm2, which properly resets scroll buffer and cursor position.
        """
        import os
        import sys

        # Use system clear command - most reliable across all terminals
        if os.name == "posix":
            os.system("clear")
        else:
            os.system("cls")

    @staticmethod
    def create_table(expand: bool = True, **kwargs) -> Table:
        """
        Create a Rich Table with consistent styling.

        Args:
            expand: Fill terminal width (default: True)
            **kwargs: Additional Table() arguments

        Returns:
            Configured Rich Table instance
        """
        return Table(
            box=DesignSystem.TABLE_BOX,
            expand=expand,
            padding=(0, 1),
            show_header=True,
            header_style="bold",
            **kwargs,
        )

    @staticmethod
    def section_header(emoji: str, title: str, width: int = None) -> List[str]:
        """
        Render a section header with emoji and separator.

        Args:
            emoji: Section emoji (📊, 🎯, etc.)
            title: Section title (e.g., "TOOL METRICS")
            width: Terminal width (auto-detected if None)

        Returns:
            List of formatted lines
        """
        w = width or DesignSystem.get_terminal_width()
        lines = [
            f"{emoji} {title}",
            DesignSystem.SECTION_SEP * w,
            "",  # Blank line after separator
        ]
        return lines

    @staticmethod
    def blank_lines(count: int = 1) -> List[str]:
        """Generate blank lines for spacing."""
        return [""] * count

    @staticmethod
    def get_console() -> Console:
        """Get shared Rich Console instance."""
        global _console
        if _console is None:
            _console = Console()
        return _console
