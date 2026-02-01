#!/usr/bin/env python3
"""
souleyez.ui.wordlist_browser - Interactive wordlist browser with keyboard navigation

Discovers wordlists from common directories (SecLists, Kali, etc.) and provides
an interactive browser for selection.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
from rich.console import Console
from rich.table import Table

from souleyez.ui.design_system import DesignSystem
from souleyez.ui.interactive_selector import (
    KEY_DOWN,
    KEY_ENTER,
    KEY_ESCAPE,
    KEY_UP,
    _get_key,
)

# Common wordlist directories to scan
WORDLIST_DIRECTORIES: List[Tuple[str, str]] = [
    # SoulEyez built-in (highest priority) - self-contained wordlists
    ("SoulEyez", "~/.souleyez/data/wordlists"),
    # Package bundled wordlists (for installed package)
    ("SoulEyez-pkg", str(Path(__file__).parent.parent / "data" / "wordlists")),
    # Dirbuster
    ("Dirbuster", "/usr/share/dirbuster/wordlists"),
]

# Category detection patterns - ORDER MATTERS (more specific first)
# Each pattern is checked against the full path + filename
CATEGORY_PATTERNS = {
    # DNS/Subdomain - check first since "subdomain" is specific
    "dns": ["subdomain", "dns", "vhost", "hostname"],
    # Extensions
    "extensions": ["extension", "ext.", "suffix", "filetype"],
    # Fuzzing
    "fuzzing": ["fuzz", "injection", "xss", "sqli", "lfi", "rfi", "traversal"],
    # Users - be specific to avoid matching "username" in paths
    "users": [
        "users.txt",
        "usernames",
        "user_",
        "_user",
        "logins",
        "accounts",
        "/users/",
        "/usernames/",
    ],
    # Passwords - check before dirs
    "passwords": [
        "password",
        "pass.txt",
        "passwd",
        "credential",
        "rockyou",
        "darkweb",
        "leaked",
        "/passwords/",
    ],
    # Directories - last since patterns are more generic
    "dirs": [
        "directory",
        "dirs",
        "dir-",
        "web-content",
        "web_content",
        "dirbuster",
        "/dirb/",
        "raft-",
        "apache.txt",
        "iis.txt",
    ],
}


def detect_category(path: str, name: str) -> str:
    """
    Detect wordlist category from path and filename.

    Args:
        path: Full path to wordlist
        name: Filename

    Returns:
        Category string: 'dirs', 'dns', 'passwords', 'users', 'fuzzing', 'extensions', or 'other'
    """
    path_lower = path.lower()
    name_lower = name.lower()
    combined = f"{path_lower}/{name_lower}"

    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if pattern in combined:
                return category

    return "other"


def count_lines(filepath: str, max_count: int = 1000000) -> int:
    """
    Count lines in a file efficiently.

    Args:
        filepath: Path to file
        max_count: Stop counting after this many lines

    Returns:
        Line count (or max_count if exceeded)
    """
    try:
        count = 0
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for _ in f:
                count += 1
                if count >= max_count:
                    return max_count
        return count
    except Exception:
        return 0


def discover_all_wordlists(
    category_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Discover all wordlists from known directories.

    Args:
        category_filter: Optional category to filter by ('dirs', 'dns', 'passwords', etc.)

    Returns:
        List of wordlist dicts with: path, name, source, category, entries, size_mb
    """
    wordlists = []
    seen_paths = set()

    for source, directory in WORDLIST_DIRECTORIES:
        dir_path = os.path.expanduser(directory)

        if not os.path.isdir(dir_path):
            continue

        # Walk directory tree
        for root, _, files in os.walk(dir_path):
            for filename in files:
                # Skip non-text files
                if not filename.endswith((".txt", ".lst", ".dic", ".wordlist")):
                    # Also include files without extension if they look like wordlists
                    if "." in filename:
                        continue

                filepath = os.path.join(root, filename)

                # Skip if already seen (handles duplicate paths)
                if filepath in seen_paths:
                    continue
                seen_paths.add(filepath)

                # Get relative path from source directory for display
                rel_path = os.path.relpath(filepath, dir_path)

                # Detect category
                category = detect_category(filepath, filename)

                # Apply category filter
                if category_filter and category != category_filter:
                    # Also check if filter matches 'other' for unmatched
                    if category_filter != "all":
                        continue

                # Get file stats
                try:
                    stat = os.stat(filepath)
                    size_mb = stat.st_size / (1024 * 1024)
                except Exception:
                    size_mb = 0

                # Count entries (limit to avoid slow scans on huge files)
                if size_mb < 50:  # Only count for files under 50MB
                    entries = count_lines(filepath)
                else:
                    entries = -1  # Will display as "large"

                wordlists.append(
                    {
                        "path": filepath,
                        "name": filename,
                        "rel_path": rel_path,
                        "source": source,
                        "category": category,
                        "entries": entries,
                        "size_mb": size_mb,
                    }
                )

    # Sort: SoulEyez first, then by source, then by name
    def sort_key(w):
        source_order = {
            "SoulEyez": 0,
            "SecLists": 1,
            "System": 2,
            "Dirb": 3,
            "Dirbuster": 4,
            "Metasploit": 5,
        }
        return (source_order.get(w["source"], 99), w["name"].lower())

    wordlists.sort(key=sort_key)

    return wordlists


class WordlistBrowser:
    """
    Interactive single-select browser for wordlists.

    Based on InteractiveSelector but for single selection:
    - Enter selects highlighted item (no checkboxes)
    - Tab cycles category filter
    - / starts search mode
    - s enters single value mode (optional)
    - c enters custom path mode (optional)
    """

    CURSOR = ">"
    CATEGORIES = ["all", "dirs", "dns", "passwords", "users", "fuzzing", "other"]

    def __init__(
        self,
        category_filter: Optional[str] = None,
        title: str = "WORDLIST BROWSER",
        recommended_paths: Optional[List[str]] = None,
        allow_single_value: bool = False,
        allow_custom_path: bool = False,
        single_value_label: str = "value",
    ):
        """
        Initialize the wordlist browser.

        Args:
            category_filter: Initial category filter
            title: Title to display
            recommended_paths: List of recommended wordlist paths to highlight with ★
            allow_single_value: If True, 's' key allows entering a single value
            allow_custom_path: If True, 'c' key allows entering a custom path
            single_value_label: Label for single value entry (e.g., 'username', 'password')
        """
        self.title = title
        self.suggested_category = category_filter  # Remember suggested filter
        self.category_idx = 0  # Start with 'all' so users see everything
        self.recommended_paths = set(recommended_paths or [])
        self.allow_single_value = allow_single_value
        self.allow_custom_path = allow_custom_path
        self.single_value_label = single_value_label

        self.search_query = ""
        self.search_mode = False
        self.all_wordlists = discover_all_wordlists()
        self.filtered = self._apply_filter()
        self.cursor_pos = 0
        self.page_start = 0
        self.page_size = 15
        self.console = Console()
        self.running = True

    def _apply_filter(self) -> List[Dict[str, Any]]:
        """Apply current category filter and search query."""
        category = self.CATEGORIES[self.category_idx]
        filtered = self.all_wordlists

        # Apply category filter
        if category != "all":
            filtered = [w for w in filtered if w["category"] == category]

        # Apply search query
        if self.search_query:
            query = self.search_query.lower()
            filtered = [
                w
                for w in filtered
                if query in w["name"].lower() or query in w["rel_path"].lower()
            ]

        # Sort recommended wordlists to top (preserving order within each group)
        if self.recommended_paths:
            recommended = [w for w in filtered if w["path"] in self.recommended_paths]
            others = [w for w in filtered if w["path"] not in self.recommended_paths]
            filtered = recommended + others

        return filtered

    def run(self) -> Optional[str]:
        """
        Run the interactive browser.

        Returns:
            Selected wordlist path or None if cancelled
        """
        if not self.all_wordlists:
            click.echo(
                click.style("  No wordlists found in common directories.", fg="yellow")
            )
            click.pause()
            return None

        self.running = True

        while self.running:
            self._render()
            key = _get_key()
            result = self._handle_key(key)
            if result is not None:
                return result

        return None

    def _render(self):
        """Render the browser UI."""
        from rich import box
        from rich.table import Table

        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        # Title bar - box style like InteractiveSelector
        click.echo()
        click.echo("┌" + "─" * (width - 2) + "┐")
        category = self.CATEGORIES[self.category_idx]
        filter_text = f"Filter: {category}"
        title_text = f" {self.title} "
        padding = width - len(title_text) - len(filter_text) - 4
        left_pad = padding // 2
        right_pad = padding - left_pad
        click.echo(
            "│"
            + " " * left_pad
            + click.style(title_text, bold=True, fg="cyan")
            + " " * right_pad
            + click.style(filter_text, fg="yellow")
            + " │"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Search bar
        if self.search_mode:
            click.echo(f"  Search: {click.style(self.search_query + '_', fg='cyan')}")
        elif self.search_query:
            click.echo(
                f"  Search: {click.style(self.search_query, fg='cyan')} (press / to edit)"
            )

        # Stats
        total = len(self.filtered)
        click.echo(f"  {click.style('Total:', bold=True)} {total} wordlists")
        click.echo()

        if not self.filtered:
            click.echo(click.style("  No wordlists match current filter.", fg="yellow"))
            click.echo()
        else:
            # Calculate visible items
            page_end = min(self.page_start + self.page_size, len(self.filtered))
            visible = self.filtered[self.page_start : page_end]

            # Create table like InteractiveSelector
            table = Table(
                show_header=True,
                header_style="bold cyan",
                box=DesignSystem.TABLE_BOX,
                padding=(0, 1),
                expand=True,
            )

            # Add columns
            table.add_column(" ", width=2, justify="center", no_wrap=True)  # Cursor
            table.add_column("Name", no_wrap=True)
            table.add_column("Entries", width=12, justify="right")
            table.add_column("Source", width=12)
            table.add_column("Category", width=12)

            # Add rows
            for idx, wordlist in enumerate(visible):
                absolute_idx = self.page_start + idx
                is_cursor = absolute_idx == self.cursor_pos
                is_recommended = wordlist["path"] in self.recommended_paths

                # Cursor indicator with recommended star
                if is_cursor:
                    cursor = "▶"
                elif is_recommended:
                    cursor = "★"
                else:
                    cursor = " "

                # Name - use rel_path if it has subdirs
                name = (
                    wordlist["rel_path"]
                    if "/" in wordlist["rel_path"]
                    else wordlist["name"]
                )
                if len(name) > 45:
                    name = "..." + name[-42:]

                # Entry count
                if wordlist["entries"] == -1:
                    entries_str = "large"
                elif wordlist["entries"] >= 1000000:
                    entries_str = f"{wordlist['entries'] / 1000000:.1f}M"
                elif wordlist["entries"] >= 1000:
                    entries_str = f"{wordlist['entries'] / 1000:.1f}K"
                else:
                    entries_str = str(wordlist["entries"])

                # Source color
                source = wordlist["source"]

                # Category
                cat = wordlist["category"]

                # Add row with highlight for cursor, yellow for recommended
                if is_cursor:
                    table.add_row(
                        cursor, name, entries_str, source, cat, style="reverse"
                    )
                elif is_recommended:
                    table.add_row(
                        f"[yellow]{cursor}[/yellow]",
                        f"[yellow]{name}[/yellow]",
                        f"[yellow]{entries_str}[/yellow]",
                        f"[yellow]{source}[/yellow]",
                        f"[yellow]{cat}[/yellow]",
                    )
                else:
                    table.add_row(cursor, name, entries_str, source, cat)

            self.console.print(table)

            # Pagination
            if len(self.filtered) > self.page_size:
                page_num = (self.page_start // self.page_size) + 1
                total_pages = (
                    len(self.filtered) + self.page_size - 1
                ) // self.page_size
                click.echo()
                click.echo(f"  Page {page_num}/{total_pages}")

        # Help bar
        click.echo()
        click.echo(DesignSystem.separator())
        help_parts = [
            f"{click.style('↑↓/jk:', bold=True)} Navigate",
            f"{click.style('Enter:', bold=True)} Select",
            f"{click.style('/:', bold=True)} Search",
            f"{click.style('Tab:', bold=True)} Filter",
        ]
        if self.allow_single_value:
            help_parts.append(
                f"{click.style('s:', bold=True)} Single {self.single_value_label}"
            )
        if self.allow_custom_path:
            help_parts.append(f"{click.style('c:', bold=True)} Custom path")
        help_parts.append(f"{click.style('q:', bold=True)} Back")
        help_text = "  " + "  |  ".join(help_parts)
        click.echo(help_text)
        # Show recommended legend if there are recommended wordlists
        if self.recommended_paths:
            click.echo(
                f"  {click.style('★', fg='yellow')} = Recommended for this tool/category"
            )
        click.echo(DesignSystem.separator())

    def _handle_key(self, key: str) -> Optional[Any]:
        """
        Handle a keypress.

        Returns:
            - Selected path (str) if Enter pressed
            - ('single', value) tuple if single value entered
            - None otherwise
        """
        # Search mode - capture text
        if self.search_mode:
            if key == KEY_ENTER or key == "\r" or key == "\n":
                self.search_mode = False
                self.filtered = self._apply_filter()
                self.cursor_pos = 0
                self.page_start = 0
            elif key == KEY_ESCAPE:
                self.search_mode = False
                self.search_query = ""
                self.filtered = self._apply_filter()
                self.cursor_pos = 0
                self.page_start = 0
            elif key in ("\x7f", "\x08"):  # Backspace
                self.search_query = self.search_query[:-1]
                self.filtered = self._apply_filter()
                self.cursor_pos = 0
                self.page_start = 0
            elif len(key) == 1 and key.isprintable():
                self.search_query += key
                self.filtered = self._apply_filter()
                self.cursor_pos = 0
                self.page_start = 0
            return None

        # Navigation - Up
        if key in (KEY_UP, "k"):
            if self.cursor_pos > 0:
                self.cursor_pos -= 1
                if self.cursor_pos < self.page_start:
                    self.page_start = max(0, self.page_start - self.page_size)

        # Navigation - Down
        elif key in (KEY_DOWN, "j"):
            if self.filtered and self.cursor_pos < len(self.filtered) - 1:
                self.cursor_pos += 1
                if self.cursor_pos >= self.page_start + self.page_size:
                    self.page_start += self.page_size

        # Select - Enter
        elif key in (KEY_ENTER, "\r", "\n"):
            if self.filtered:
                return self.filtered[self.cursor_pos]["path"]

        # Search mode
        elif key == "/":
            self.search_mode = True

        # Cycle category filter - Tab
        elif key == "\t":
            self.category_idx = (self.category_idx + 1) % len(self.CATEGORIES)
            self.filtered = self._apply_filter()
            self.cursor_pos = 0
            self.page_start = 0

        # Single value entry - 's'
        elif key == "s" and self.allow_single_value:
            # Clear screen and prompt for single value
            DesignSystem.clear_screen()
            click.echo()
            click.echo(
                click.style(
                    f"  Enter single {self.single_value_label}", bold=True, fg="cyan"
                )
            )
            click.echo()
            try:
                value = click.prompt(
                    f"  {self.single_value_label.capitalize()}", type=str
                )
                if value.strip():
                    return ("single", value.strip())
            except (KeyboardInterrupt, click.Abort):
                pass
            return None

        # Custom path entry - 'c'
        elif key == "c" and self.allow_custom_path:
            # Clear screen and prompt for custom path
            DesignSystem.clear_screen()
            click.echo()
            click.echo(
                click.style("  Enter custom wordlist path", bold=True, fg="cyan")
            )
            click.echo()
            try:
                import os

                custom = click.prompt("  Path", type=str)
                if os.path.exists(custom):
                    return custom
                else:
                    click.echo(click.style(f"  File not found: {custom}", fg="red"))
                    click.pause()
            except (KeyboardInterrupt, click.Abort):
                pass
            return None

        # Exit
        elif key in (KEY_ESCAPE, "q", "\x03"):  # \x03 is Ctrl+C
            self.running = False

        return None


def browse_wordlists(
    category_filter: Optional[str] = None,
    title: str = "WORDLIST BROWSER",
    recommended_paths: Optional[List[str]] = None,
    allow_single_value: bool = False,
    allow_custom_path: bool = False,
    single_value_label: str = "value",
) -> Optional[Any]:
    """
    Launch the interactive wordlist browser.

    Args:
        category_filter: Optional initial category filter
        title: Browser title
        recommended_paths: List of recommended wordlist paths to highlight with ★
        allow_single_value: If True, 's' key allows entering a single value
        allow_custom_path: If True, 'c' key allows entering a custom path
        single_value_label: Label for single value entry (e.g., 'username', 'password')

    Returns:
        - Selected wordlist path (str)
        - ('single', value) tuple if single value entered
        - None if cancelled
    """
    browser = WordlistBrowser(
        category_filter=category_filter,
        title=title,
        recommended_paths=recommended_paths,
        allow_single_value=allow_single_value,
        allow_custom_path=allow_custom_path,
        single_value_label=single_value_label,
    )
    return browser.run()


# Convenience export
__all__ = [
    "browse_wordlists",
    "discover_all_wordlists",
    "WordlistBrowser",
    "WORDLIST_DIRECTORIES",
]
