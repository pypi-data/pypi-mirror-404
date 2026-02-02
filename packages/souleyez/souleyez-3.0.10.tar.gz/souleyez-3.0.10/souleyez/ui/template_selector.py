"""Template selection interface for deliverables - Interactive table style."""

from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table

from souleyez.storage.deliverable_templates import TemplateManager
from souleyez.ui.design_system import DesignSystem

# Key codes
try:
    import readchar

    KEY_UP = readchar.key.UP
    KEY_DOWN = readchar.key.DOWN
    KEY_PAGE_UP = readchar.key.PAGE_UP
    KEY_PAGE_DOWN = readchar.key.PAGE_DOWN
    KEY_ESCAPE = readchar.key.ESC
    KEY_ENTER = readchar.key.ENTER
    KEY_SPACE = readchar.key.SPACE
except (ImportError, AttributeError):
    KEY_UP = "\x1b[A"
    KEY_DOWN = "\x1b[B"
    KEY_PAGE_UP = "\x1b[5~"
    KEY_PAGE_DOWN = "\x1b[6~"
    KEY_ESCAPE = "\x1b"
    KEY_ENTER = "\r"
    KEY_SPACE = " "


def _get_key() -> str:
    """Read a single keypress."""
    try:
        import readchar

        return readchar.readkey()
    except ImportError:
        pass

    try:
        ch = click.getchar()
        if ch == "\x1b" or (len(ch) > 1 and ch.startswith("\x1b")):
            if len(ch) >= 3:
                if ch == "\x1b[A":
                    return KEY_UP
                elif ch == "\x1b[B":
                    return KEY_DOWN
                elif ch in ("\x1b[5~", "\x1b[5"):
                    return KEY_PAGE_UP
                elif ch in ("\x1b[6~", "\x1b[6"):
                    return KEY_PAGE_DOWN
            elif ch == "\x1b":
                try:
                    ch2 = click.getchar()
                    if ch2 == "[":
                        ch3 = click.getchar()
                        if ch3 == "A":
                            return KEY_UP
                        elif ch3 == "B":
                            return KEY_DOWN
                        elif ch3 in ("5", "6"):
                            click.getchar()
                            return KEY_PAGE_UP if ch3 == "5" else KEY_PAGE_DOWN
                    return ""
                except Exception:
                    return KEY_ESCAPE
            return ""
        return ch
    except Exception:
        return KEY_ESCAPE


class TemplateSelector:
    """Interactive template selector with keyboard navigation."""

    CURSOR = "▶"
    NO_CURSOR = " "
    RADIO_EMPTY = "○"
    RADIO_SELECTED = "●"

    # Category filters
    CATEGORIES = [
        ("all", "All", None),
        (
            "compliance",
            "🏛️ Compliance",
            [
                "hipaa",
                "pci-dss",
                "nist",
                "owasp",
                "soc2",
                "iso27001",
                "cis",
                "cmmc",
                "gdpr",
                "glba",
            ],
        ),
        (
            "pentest",
            "🎯 Pentest",
            ["ptes", "internal", "external", "webapp", "redteam", "cloud", "ad"],
        ),
        ("industry", "🏭 Industry", ["nerc-cip", "hitrust", "ffiec"]),
    ]

    def __init__(self, templates: List[Dict], engagement_id: int):
        self.all_templates = templates
        self.templates = templates  # Filtered view
        self.engagement_id = engagement_id
        self.cursor_pos = 0
        self.page_start = 0
        self.page_size = 20
        self.console = Console()
        self.running = True
        self.selected_template = None
        self.selected_idx = None  # Currently selected row (for inline options)
        self.show_inline_options = False
        self.current_filter = "all"

    def run(self) -> Optional[Dict]:
        """Run the interactive selector. Returns selected template or None."""
        if not self.templates:
            click.echo(click.style("  No templates available.", fg="yellow"))
            click.pause()
            return None

        self.running = True

        while self.running:
            self._render()
            key = _get_key()
            self._handle_key(key)

        return self.selected_template

    def _apply_filter(self, filter_key: str):
        """Apply category filter."""
        self.current_filter = filter_key
        self.cursor_pos = 0
        self.page_start = 0
        self.selected_idx = None
        self.show_inline_options = False

        if filter_key == "all":
            self.templates = self.all_templates
        else:
            # Find the filter
            for key, label, frameworks in self.CATEGORIES:
                if key == filter_key and frameworks:
                    self.templates = [
                        t
                        for t in self.all_templates
                        if t.get("framework") in frameworks
                    ]
                    break

    def _get_category(self, template: Dict) -> str:
        """Get display category for template."""
        framework = template.get("framework", "")
        compliance = [
            "hipaa",
            "pci-dss",
            "nist",
            "owasp",
            "soc2",
            "iso27001",
            "cis",
            "cmmc",
            "gdpr",
            "glba",
        ]
        pentest = ["ptes", "internal", "external", "webapp", "redteam", "cloud", "ad"]
        industry = ["nerc-cip", "hitrust", "ffiec"]

        if framework in compliance:
            return "🏛️"
        elif framework in pentest:
            return "🎯"
        elif framework in industry:
            return "🏭"
        return "📋"

    def _render(self):
        """Render the table."""
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        # Title
        click.echo()
        click.echo("┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " 🎯 INITIALIZE DELIVERABLES FROM TEMPLATE ".center(width - 2),
                bold=True,
                fg="cyan",
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Filter tabs
        filter_parts = []
        for idx, (key, label, _) in enumerate(self.CATEGORIES):
            if key == self.current_filter:
                filter_parts.append(
                    click.style(f"[{idx+1}] {label}", fg="cyan", bold=True)
                )
            else:
                filter_parts.append(f"[{idx+1}] {label}")
        click.echo("  " + "  |  ".join(filter_parts))
        click.echo()

        # Stats
        total = len(self.templates)
        selected_info = ""
        if self.selected_idx is not None:
            selected_info = f"  |  {click.style('Selected:', bold=True, fg='green')} 1"
        click.echo(
            f"  {click.style('Total:', bold=True)} {total} templates{selected_info}"
        )
        click.echo()

        # Calculate visible items
        page_end = min(self.page_start + self.page_size, len(self.templates))
        visible_templates = self.templates[self.page_start : page_end]

        # Create table
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=DesignSystem.TABLE_BOX,
            padding=(0, 1),
            expand=True,
        )

        table.add_column(" ", width=2, justify="center", no_wrap=True)
        table.add_column(self.RADIO_EMPTY, width=3, justify="center", no_wrap=True)
        table.add_column("#", width=4, justify="right", no_wrap=True)
        table.add_column("Template Name", width=28, no_wrap=True)
        table.add_column("Items", width=6, justify="center", no_wrap=True)
        table.add_column("Category", width=10, justify="center", no_wrap=True)
        table.add_column("Framework", width=12, justify="center", no_wrap=True)

        for idx, template in enumerate(visible_templates):
            absolute_idx = self.page_start + idx
            is_cursor = absolute_idx == self.cursor_pos
            is_selected = absolute_idx == self.selected_idx

            cursor = self.CURSOR if is_cursor else self.NO_CURSOR
            radio = self.RADIO_SELECTED if is_selected else self.RADIO_EMPTY

            category_icon = self._get_category(template)
            deliverable_count = len(template.get("deliverables", []))
            framework = (template.get("framework") or "").upper()

            row = [
                cursor,
                radio,
                str(absolute_idx + 1),
                template["name"],
                str(deliverable_count),
                category_icon,
                framework,
            ]

            if is_cursor:
                table.add_row(*row, style="reverse")
            else:
                table.add_row(*row)

        self.console.print(table)

        # Pagination info
        if len(self.templates) > self.page_size:
            page_num = (self.page_start // self.page_size) + 1
            total_pages = (len(self.templates) + self.page_size - 1) // self.page_size
            click.echo(f"\n  Page {page_num}/{total_pages}")

        # Navigation tip (above separator)
        click.echo()
        click.echo("  n/p: Next/Previous page")

        # Menu options or inline options
        click.echo()
        click.echo(DesignSystem.separator())
        click.echo()

        if self.show_inline_options and self.selected_idx is not None:
            # Inline options when template is selected
            template = self.templates[self.selected_idx]
            click.echo(
                f"  {click.style('Selected:', bold=True, fg='green')} {template['name']} ({len(template.get('deliverables', []))} deliverables)"
            )
            click.echo()
            click.echo(f"  [v] Preview - View template details")
            click.echo(f"  [l] Load - Load this template")
            click.echo(f"  [b] Back - Deselect template")
            click.echo()
            click.echo(f"  Select option: ", nl=False)
        else:
            # Normal menu options
            click.echo(f"  [Space] Select - Select template for options")
            click.echo(f"  [Enter] Load - Quick load selected template")
            click.echo(f"  [v] Preview - View template details")
            click.echo(f"  [1-4] Filter - Filter by category")
            click.echo(f"  [i] Import - Import template from file")
            click.echo(f"  [q] Back")
            click.echo()
            click.echo(f"  Choice [q]: ", nl=False)

    def _handle_key(self, key: str):
        """Handle keypress."""
        # Handle inline options mode first
        if self.show_inline_options and self.selected_idx is not None:
            if key == "v":
                # Preview selected template
                self._preview_template(self.selected_idx)
                return
            elif key == "l":
                # Load selected template
                self.selected_template = self.templates[self.selected_idx]
                self.running = False
                return
            elif key in ("b", KEY_ESCAPE):
                # Back - deselect
                self.selected_idx = None
                self.show_inline_options = False
                return
            # Any other key exits inline mode
            self.selected_idx = None
            self.show_inline_options = False

        # Filter keys (1-4)
        if key == "1":
            self._apply_filter("all")
            return
        elif key == "2":
            self._apply_filter("compliance")
            return
        elif key == "3":
            self._apply_filter("pentest")
            return
        elif key == "4":
            self._apply_filter("industry")
            return

        # Navigation - Up
        if key in (KEY_UP, "k"):
            if self.cursor_pos > 0:
                self.cursor_pos -= 1
                if self.cursor_pos < self.page_start:
                    self.page_start = max(0, self.page_start - self.page_size)

        # Navigation - Down
        elif key in (KEY_DOWN, "j"):
            if self.cursor_pos < len(self.templates) - 1:
                self.cursor_pos += 1
                if self.cursor_pos >= self.page_start + self.page_size:
                    self.page_start += self.page_size

        # Page Up / Previous Page
        elif key in (KEY_PAGE_UP, "p", "[", "<"):
            current_page = self.page_start // self.page_size
            if current_page > 0:
                self.page_start = (current_page - 1) * self.page_size
                self.cursor_pos = self.page_start

        # Page Down / Next Page
        elif key in (KEY_PAGE_DOWN, "n", "]", ">"):
            total_pages = (len(self.templates) + self.page_size - 1) // self.page_size
            current_page = self.page_start // self.page_size
            if current_page < total_pages - 1:
                self.page_start = (current_page + 1) * self.page_size
                self.cursor_pos = self.page_start

        # Preview (v key)
        elif key == "v":
            self._preview_template()

        # Import
        elif key == "i":
            self._import_template()

        # Space - Select/toggle template and show inline options
        elif key in (KEY_SPACE, " "):
            if self.selected_idx == self.cursor_pos:
                # Deselect if same item
                self.selected_idx = None
                self.show_inline_options = False
            else:
                # Select current item
                self.selected_idx = self.cursor_pos
                self.show_inline_options = True

        # Enter - Quick load (bypass inline options)
        elif key in (KEY_ENTER, "\r", "\n"):
            self.selected_template = self.templates[self.cursor_pos]
            self.running = False

        # Cancel - q or Escape
        elif key in (KEY_ESCAPE, "q", "\x03"):
            self.selected_template = None
            self.running = False

    def _preview_template(self, idx: int = None):
        """Show template preview."""
        if idx is None:
            idx = self.cursor_pos
        template = self.templates[idx]
        _show_template_preview(template)
        click.pause("Press any key to continue...")

    def _import_template(self):
        """Import a template from JSON file."""
        DesignSystem.clear_screen()
        click.echo()
        click.echo(click.style("  📦 IMPORT TEMPLATE", bold=True, fg="cyan"))
        click.echo()

        file_path = click.prompt(
            "  Enter path to template JSON file", type=str, default=""
        )
        if not file_path:
            return

        try:
            tm = TemplateManager()
            with open(file_path, "r") as f:
                json_data = f.read()
            template_id = tm.import_template(json_data)
            template = tm.get_template(template_id)
            click.echo()
            click.echo(click.style(f"  ✅ Imported: {template['name']}", fg="green"))
            click.pause()
            # Refresh templates list
            self.templates = tm.list_templates()
        except Exception as e:
            click.echo(click.style(f"  ❌ Import failed: {e}", fg="red"))
            click.pause()


def show_template_selector(engagement_id: int) -> bool:
    """
    Display template selector and load selected template.

    Returns:
        True if template was loaded, False if cancelled
    """
    tm = TemplateManager()

    # Get all templates
    all_templates = tm.list_templates()

    # Sort by category then name
    def sort_key(t):
        framework = t.get("framework", "") or ""
        compliance = [
            "hipaa",
            "pci-dss",
            "nist",
            "owasp",
            "soc2",
            "iso27001",
            "cis",
            "cmmc",
            "gdpr",
            "glba",
        ]
        pentest = ["ptes", "internal", "external", "webapp", "redteam", "cloud", "ad"]
        industry = ["nerc-cip", "hitrust", "ffiec"]

        if framework in compliance:
            cat = 0
        elif framework in pentest:
            cat = 1
        elif framework in industry:
            cat = 2
        else:
            cat = 3
        return (cat, t["name"])

    all_templates.sort(key=sort_key)

    # Loop until user confirms a template or quits
    while True:
        # Run interactive selector (fresh instance each iteration)
        selector = TemplateSelector(all_templates, engagement_id)
        selected = selector.run()

        if not selected:
            # User pressed 'q' to quit selector
            return False

        # Confirm and load
        DesignSystem.clear_screen()
        click.echo()
        click.echo(f"  Selected: {click.style(selected['name'], bold=True, fg='cyan')}")
        click.echo(f"  This will create {len(selected['deliverables'])} deliverables")
        click.echo()

        if not click.confirm("  Load this template?", default=True):
            # User said 'n' - go back to selector
            continue

        try:
            count = tm.apply_template(selected["id"], engagement_id)
            click.echo()
            click.echo(
                click.style(
                    f"  ✅ Loaded {count} deliverables from template", fg="green"
                )
            )

            auto_val_count = sum(
                1 for d in selected["deliverables"] if d.get("auto_validate")
            )
            if auto_val_count > 0:
                click.echo(
                    click.style(
                        f"  ✅ {auto_val_count} deliverables have auto-validation enabled",
                        fg="green",
                    )
                )

            click.echo()
            click.echo(click.style("  💡 Next steps:", fg="cyan"))
            click.echo("     • Press [V] to validate and see current progress")
            click.echo("     • Start testing and link evidence as you go")
            click.echo("     • Export report when complete")
            click.pause()
            return True
        except Exception as e:
            click.echo(click.style(f"  ❌ Failed to load template: {e}", fg="red"))
            click.pause()
            return False


def _show_template_preview(template: dict):
    """Show detailed template preview."""
    DesignSystem.clear_screen()
    width = DesignSystem.get_terminal_width()

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" 📋 TEMPLATE PREVIEW ".center(width - 2), bold=True, fg="cyan")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    click.echo(f"  Name: {click.style(template['name'], bold=True)}")
    if template.get("description"):
        click.echo(f"  Description: {template['description']}")
    if template.get("framework"):
        click.echo(f"  Framework: {template['framework'].upper()}")
    click.echo(f"  Total Deliverables: {len(template.get('deliverables', []))}")

    auto_val_count = sum(
        1 for d in template.get("deliverables", []) if d.get("auto_validate")
    )
    click.echo(
        f"  Auto-validation: {auto_val_count}/{len(template.get('deliverables', []))} deliverables"
    )

    click.echo()
    click.echo(click.style("  DELIVERABLES", bold=True, fg="cyan"))
    click.echo("  " + "═" * (width - 4))
    click.echo()

    # Group by category
    categories = {}
    for d in template.get("deliverables", []):
        cat = d.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(d)

    for category, deliverables in categories.items():
        click.echo(
            click.style(f"  {category.upper().replace('_', ' ')}", bold=True, fg="cyan")
        )
        click.echo("  " + "─" * (width - 4))

        for d in deliverables:
            priority_color = {
                "critical": "red",
                "high": "yellow",
                "medium": "white",
                "low": "bright_black",
            }.get(d.get("priority", "medium"), "white")

            auto_val_icon = "✓" if d.get("auto_validate") else " "
            click.echo(
                f"  [{auto_val_icon}] "
                + click.style(
                    f"[{d.get('priority', 'medium').upper()}]", fg=priority_color
                )
                + f" {d['title']}"
            )

        click.echo()
