#!/usr/bin/env python3
"""
souleyez.ui.interactive_selector - Reusable interactive row selector with keyboard navigation

Provides arrow-key/vim-style navigation for selecting items from tables.
"""

import sys
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import click
from rich import box
from rich.console import Console
from rich.table import Table

from souleyez.ui.design_system import DesignSystem

# Key codes - using readchar constants when available
try:
    import readchar

    KEY_UP = readchar.key.UP
    KEY_DOWN = readchar.key.DOWN
    KEY_LEFT = readchar.key.LEFT
    KEY_RIGHT = readchar.key.RIGHT
    KEY_PAGE_UP = readchar.key.PAGE_UP
    KEY_PAGE_DOWN = readchar.key.PAGE_DOWN
    KEY_ESCAPE = readchar.key.ESC
    KEY_ENTER = readchar.key.ENTER
    KEY_SPACE = readchar.key.SPACE
except (ImportError, AttributeError):
    # Fallback to raw codes
    KEY_UP = "\x1b[A"
    KEY_DOWN = "\x1b[B"
    KEY_LEFT = "\x1b[D"
    KEY_RIGHT = "\x1b[C"
    KEY_PAGE_UP = "\x1b[5~"
    KEY_PAGE_DOWN = "\x1b[6~"
    KEY_ESCAPE = "\x1b"
    KEY_ENTER = "\r"
    KEY_SPACE = " "


def _get_key() -> str:
    """
    Read a single keypress, handling escape sequences for arrow keys.

    Returns:
        Key character or escape sequence string
    """
    try:
        import readchar

        key = readchar.readkey()
        return key
    except ImportError:
        pass

    # Use click.getchar() which handles raw input well
    try:
        ch = click.getchar()

        # Handle escape sequences (arrow keys send \x1b[A, \x1b[B, etc.)
        if ch == "\x1b" or (len(ch) > 1 and ch.startswith("\x1b")):
            # click.getchar() may return the full sequence or just escape
            if len(ch) >= 3:
                if ch == "\x1b[A":
                    return KEY_UP
                elif ch == "\x1b[B":
                    return KEY_DOWN
                elif ch == "\x1b[C":
                    return KEY_RIGHT
                elif ch == "\x1b[D":
                    return KEY_LEFT
                elif ch in ("\x1b[5~", "\x1b[5"):
                    return KEY_PAGE_UP
                elif ch in ("\x1b[6~", "\x1b[6"):
                    return KEY_PAGE_DOWN
            elif ch == "\x1b":
                # Got just escape - try to read more (arrow key sequence)
                try:
                    ch2 = click.getchar()
                    if ch2 == "[":
                        ch3 = click.getchar()
                        if ch3 == "A":
                            return KEY_UP
                        elif ch3 == "B":
                            return KEY_DOWN
                        elif ch3 == "C":
                            return KEY_RIGHT
                        elif ch3 == "D":
                            return KEY_LEFT
                        elif ch3 in ("5", "6"):
                            click.getchar()  # consume ~
                            return KEY_PAGE_UP if ch3 == "5" else KEY_PAGE_DOWN
                    # Unknown sequence, ignore it
                    return ""  # Return empty to ignore
                except Exception:
                    return KEY_ESCAPE
            # Unknown escape sequence, ignore
            return ""
        return ch
    except Exception:
        pass

    # Fallback: use termios on Unix-like systems
    try:
        import select
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)

            # Handle escape sequences (arrow keys, etc.)
            if ch == "\x1b":
                # Check if more characters are available (escape sequence)
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    ch2 = sys.stdin.read(1)
                    if ch2 == "[":
                        # CSI sequence - read the final byte
                        if select.select([sys.stdin], [], [], 0.05)[0]:
                            ch3 = sys.stdin.read(1)
                            # Map to our key constants
                            if ch3 == "A":
                                return KEY_UP
                            elif ch3 == "B":
                                return KEY_DOWN
                            elif ch3 == "C":
                                return KEY_RIGHT
                            elif ch3 == "D":
                                return KEY_LEFT
                            elif ch3 == "5":
                                # Page Up - consume the ~
                                if select.select([sys.stdin], [], [], 0.05)[0]:
                                    sys.stdin.read(1)
                                return KEY_PAGE_UP
                            elif ch3 == "6":
                                # Page Down - consume the ~
                                if select.select([sys.stdin], [], [], 0.05)[0]:
                                    sys.stdin.read(1)
                                return KEY_PAGE_DOWN
                            return ch + ch2 + ch3
                        return ch + ch2
                    return ch + ch2
                # Just escape key pressed
                return KEY_ESCAPE
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except (ImportError, termios.error, AttributeError):
        # Last resort fallback - requires Enter
        return input() or KEY_ESCAPE


class InteractiveSelector:
    """
    Reusable interactive row selector with keyboard navigation.

    Features:
    - Arrow keys (↑/↓) and vim-style (j/k) navigation
    - Space/Enter to toggle selection
    - 'a' to select all, 'n' to select none
    - 'q' or Escape to exit
    - Visual highlighting of current row
    - Checkbox display (☐/☑)
    - Pagination for large lists

    Example:
        selector = InteractiveSelector(
            items=hosts,
            columns=[
                {'name': 'ID', 'width': 8, 'key': 'id'},
                {'name': 'IP', 'width': 20, 'key': 'ip_address'},
            ],
            selected_ids=selected_hosts,
            get_id=lambda h: h.get('id'),
            title='HOST MANAGEMENT'
        )
        selector.run()  # Modifies selected_hosts in-place
    """

    # Checkbox characters (using larger circles for visibility)
    CHECKBOX_EMPTY = "○"
    CHECKBOX_CHECKED = "●"

    # Cursor indicator
    CURSOR = "▶"
    NO_CURSOR = " "

    def __init__(
        self,
        items: List[Dict[str, Any]],
        columns: List[Dict[str, Any]],
        selected_ids: Set[Any],
        get_id: Callable[[Dict], Any],
        title: str = "SELECT ITEMS",
        page_size: int = 20,
        format_cell: Optional[Callable[[Dict, str], str]] = None,
        show_header_info: Optional[Callable[[], str]] = None,
        extra_actions: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the interactive selector.

        Args:
            items: List of item dicts to display
            columns: List of column definitions, each with:
                - 'name': Column header text
                - 'width': Column width (optional)
                - 'key': Dict key to extract value
                - 'format': Optional format function (value -> str)
                - 'style': Optional Rich style string
            selected_ids: Set of selected item IDs (modified in-place)
            get_id: Function to extract ID from item dict
            title: Title to display above table
            page_size: Number of items per page
            format_cell: Optional function(item, key) -> formatted string
            show_header_info: Optional function to show info above table
            extra_actions: Optional dict of {key: label} for additional exit actions
        """
        self.items = items
        self.columns = columns
        self.selected_ids = selected_ids
        self.get_id = get_id
        self.title = title
        self.page_size = page_size
        self.format_cell = format_cell
        self.show_header_info = show_header_info
        self.extra_actions = extra_actions or {}

        # State
        self.cursor_pos = 0
        self.page_start = 0
        self.console = Console()
        self.running = True
        self.exit_key = None  # Track which key caused exit

    def run(self) -> Set[Any]:
        """
        Run the interactive selector loop.

        Returns:
            The modified selected_ids set
        """
        if not self.items:
            click.echo(click.style("  No items to select.", fg="yellow"))
            click.pause()
            return self.selected_ids

        self.running = True

        while self.running:
            self._render()
            key = _get_key()
            self._handle_key(key)

        return self.selected_ids

    def _render(self):
        """Render the table with current selection state."""
        DesignSystem.clear_screen()

        width = DesignSystem.get_terminal_width()

        # Title
        click.echo()
        click.echo("┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(f" {self.title} ".center(width - 2), bold=True, fg="cyan")
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Optional header info
        if self.show_header_info:
            info = self.show_header_info()
            if info:
                click.echo(f"  {info}")
                click.echo()

        # Stats
        total = len(self.items)
        selected_count = len(self.selected_ids)
        click.echo(
            f"  {click.style('Total:', bold=True)} {total} items  |  "
            f"{click.style('Selected:', bold=True, fg='cyan')} {selected_count}"
        )
        click.echo()

        # Calculate visible items
        page_end = min(self.page_start + self.page_size, len(self.items))
        visible_items = self.items[self.page_start : page_end]

        # Create table
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=DesignSystem.TABLE_BOX,
            padding=(0, 1),
            expand=True,
        )

        # Add cursor column
        table.add_column(" ", width=2, justify="center", no_wrap=True)
        # Add checkbox column
        table.add_column(self.CHECKBOX_EMPTY, width=3, justify="center", no_wrap=True)

        # Add user-defined columns
        for col in self.columns:
            table.add_column(
                col["name"],
                width=col.get("width"),
                justify=col.get("justify", "left"),
                no_wrap=col.get("no_wrap", False),
                style=col.get("style"),
            )

        # Add rows
        for idx, item in enumerate(visible_items):
            absolute_idx = self.page_start + idx
            item_id = self.get_id(item)

            # Cursor indicator
            is_cursor = absolute_idx == self.cursor_pos
            cursor = self.CURSOR if is_cursor else self.NO_CURSOR

            # Checkbox
            is_selected = item_id in self.selected_ids
            checkbox = self.CHECKBOX_CHECKED if is_selected else self.CHECKBOX_EMPTY

            # Build row values
            row_values = [cursor, checkbox]

            for col in self.columns:
                key = col["key"]
                if self.format_cell:
                    value = self.format_cell(item, key)
                elif "format" in col:
                    value = col["format"](item.get(key, ""))
                else:
                    value = str(item.get(key, "-") or "-")
                row_values.append(value)

            # Apply highlight style for cursor row
            if is_cursor:
                table.add_row(*row_values, style="reverse")
            else:
                table.add_row(*row_values)

        self.console.print(table)

        # Pagination info
        if len(self.items) > self.page_size:
            page_num = (self.page_start // self.page_size) + 1
            total_pages = (len(self.items) + self.page_size - 1) // self.page_size
            click.echo(f"\n  Page {page_num}/{total_pages}  |  " f"p/n: Prev/Next page")

        # Help bar
        click.echo()
        click.echo(DesignSystem.separator())
        help_text = (
            f"  {click.style('↑↓/jk:', bold=True)} Navigate  |  "
            f"{click.style('Space:', bold=True)} Toggle  |  "
            f"{click.style('a:', bold=True)} All  |  "
            f"{click.style('u:', bold=True)} Unselect  |  "
            f"{click.style('q/Enter:', bold=True)} Done"
        )
        click.echo(help_text)

        # Show extra actions if any
        if self.extra_actions:
            for key, label in self.extra_actions.items():
                click.echo(f"    [{key}] {label}")

        click.echo(DesignSystem.separator())

    def _handle_key(self, key: str):
        """Handle a keypress."""
        # Navigation - Up
        if key in (KEY_UP, "k"):
            if self.cursor_pos > 0:
                self.cursor_pos -= 1
                # Scroll up if needed
                if self.cursor_pos < self.page_start:
                    self.page_start = max(0, self.page_start - self.page_size)

        # Navigation - Down
        elif key in (KEY_DOWN, "j"):
            if self.cursor_pos < len(self.items) - 1:
                self.cursor_pos += 1
                # Scroll down if needed
                if self.cursor_pos >= self.page_start + self.page_size:
                    self.page_start += self.page_size

        # Page Up / Previous page
        elif key in (KEY_PAGE_UP, "p", "[", "<"):
            current_page = self.page_start // self.page_size
            if current_page > 0:
                self.page_start = (current_page - 1) * self.page_size
                self.cursor_pos = self.page_start

        # Page Down / Next page
        elif key in (KEY_PAGE_DOWN, "n", "]", ">"):
            total_pages = (len(self.items) + self.page_size - 1) // self.page_size
            current_page = self.page_start // self.page_size
            if current_page < total_pages - 1:
                self.page_start = (current_page + 1) * self.page_size
                self.cursor_pos = self.page_start

        # Left/Right arrows - ignore (don't exit)
        elif key in (KEY_LEFT, KEY_RIGHT):
            pass  # Do nothing, just don't exit

        # Toggle selection - Space
        elif key == KEY_SPACE:
            if self.items:
                item = self.items[self.cursor_pos]
                item_id = self.get_id(item)
                if item_id in self.selected_ids:
                    self.selected_ids.discard(item_id)
                else:
                    self.selected_ids.add(item_id)

        # Select all
        elif key == "a":
            for item in self.items:
                self.selected_ids.add(self.get_id(item))

        # Select none / Unselect all
        elif key == "u":
            # Only clear items that are in current list
            current_ids = {self.get_id(item) for item in self.items}
            self.selected_ids -= current_ids

        # Exit - q, Enter, or Escape
        elif key in (KEY_ESCAPE, KEY_ENTER, "q", "\x03", "\r", "\n"):  # \x03 is Ctrl+C
            self.exit_key = key
            self.running = False

        # Extra action keys (also exit)
        elif key in self.extra_actions:
            self.exit_key = key
            self.running = False


def interactive_select(
    items: List[Dict[str, Any]],
    columns: List[Dict[str, Any]],
    selected_ids: Set[Any],
    get_id: Callable[[Dict], Any],
    title: str = "SELECT ITEMS",
    **kwargs,
) -> Set[Any]:
    """
    Convenience function to run an interactive selector.

    Args:
        items: List of item dicts to display
        columns: List of column definitions
        selected_ids: Set of selected item IDs (modified in-place)
        get_id: Function to extract ID from item dict
        title: Title to display
        **kwargs: Additional InteractiveSelector arguments

    Returns:
        The modified selected_ids set
    """
    selector = InteractiveSelector(
        items=items,
        columns=columns,
        selected_ids=selected_ids,
        get_id=get_id,
        title=title,
        **kwargs,
    )
    return selector.run()
