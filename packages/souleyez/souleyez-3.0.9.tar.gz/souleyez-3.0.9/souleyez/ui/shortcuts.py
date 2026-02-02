"""
Centralized Keyboard Shortcut Manager for SoulEyez Interactive UI

This module provides a unified system for managing keyboard shortcuts
across all views to prevent conflicts and improve consistency.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Optional


class ShortcutContext(Enum):
    """Context where shortcuts are available."""

    GLOBAL = "global"  # Available everywhere
    DASHBOARD = "dashboard"  # Dashboard/Command Center
    DETAILED_VIEW = "detailed"  # Detailed view mode
    MENU = "menu"  # Interactive menus
    VIEW = "view"  # Specific views (hosts, findings, etc.)


@dataclass
class Shortcut:
    """Represents a keyboard shortcut."""

    key: str
    description: str
    context: ShortcutContext
    action: Optional[str] = None  # Action identifier
    conflicts_with: Optional[str] = None


class ShortcutManager:
    """
    Centralized keyboard shortcut registry.

    Resolves conflicts and provides consistent shortcuts across the UI.
    Decisions:
    - 'c' = Command Center (main navigation)
    - 'u' = User Credentials (data access)
    """

    # Global shortcuts registry
    _shortcuts: Dict[str, Shortcut] = {}

    @classmethod
    def initialize(cls):
        """Initialize all keyboard shortcuts."""

        # ═══════════════════════════════════════════════════════════
        # GLOBAL SHORTCUTS - Available everywhere
        # ═══════════════════════════════════════════════════════════

        cls.register(
            Shortcut(
                key="q",
                description="Quit/Exit",
                context=ShortcutContext.GLOBAL,
                action="quit",
            )
        )

        cls.register(
            Shortcut(
                key="?",
                description="Help",
                context=ShortcutContext.GLOBAL,
                action="help",
            )
        )

        cls.register(
            Shortcut(
                key="m",
                description="Menu",
                context=ShortcutContext.GLOBAL,
                action="menu",
            )
        )

        # ═══════════════════════════════════════════════════════════
        # DASHBOARD / COMMAND CENTER SHORTCUTS
        # ═══════════════════════════════════════════════════════════

        cls.register(
            Shortcut(
                key="c",
                description="Command Center",
                context=ShortcutContext.DASHBOARD,
                action="command_center",
            )
        )

        cls.register(
            Shortcut(
                key="o",
                description="OSINT/Discovery View",
                context=ShortcutContext.DASHBOARD,
                action="osint_discovery",
            )
        )

        cls.register(
            Shortcut(
                key="v",
                description="Toggle View (Command Center ↔ Detailed)",
                context=ShortcutContext.DASHBOARD,
                action="toggle_view",
            )
        )

        cls.register(
            Shortcut(
                key="i",
                description="Intelligence Dashboard",
                context=ShortcutContext.DASHBOARD,
                action="intelligence",
            )
        )

        cls.register(
            Shortcut(
                key="e",
                description="Evidence Vault",
                context=ShortcutContext.DASHBOARD,
                action="evidence",
            )
        )

        cls.register(
            Shortcut(
                key="r",
                description="Reports & Deliverables",
                context=ShortcutContext.DASHBOARD,
                action="reports",
            )
        )

        cls.register(
            Shortcut(
                key="a",
                description="Auto-chaining Toggle",
                context=ShortcutContext.DASHBOARD,
                action="auto_chain",
            )
        )

        cls.register(
            Shortcut(
                key="x",
                description="Execute AI Recommendation",
                context=ShortcutContext.DASHBOARD,
                action="ai_execute",
            )
        )

        cls.register(
            Shortcut(
                key="1",
                description="Quick Action #1",
                context=ShortcutContext.DASHBOARD,
                action="quick_action_1",
            )
        )

        cls.register(
            Shortcut(
                key="2",
                description="Quick Action #2",
                context=ShortcutContext.DASHBOARD,
                action="quick_action_2",
            )
        )

        cls.register(
            Shortcut(
                key="3",
                description="Quick Action #3",
                context=ShortcutContext.DASHBOARD,
                action="quick_action_3",
            )
        )

        # ═══════════════════════════════════════════════════════════
        # DATA ACCESS SHORTCUTS
        # ═══════════════════════════════════════════════════════════

        cls.register(
            Shortcut(
                key="h",
                description="Hosts",
                context=ShortcutContext.DASHBOARD,
                action="hosts",
            )
        )

        cls.register(
            Shortcut(
                key="f",
                description="Findings",
                context=ShortcutContext.DASHBOARD,
                action="findings",
            )
        )

        cls.register(
            Shortcut(
                key="u",
                description="User Credentials",
                context=ShortcutContext.DASHBOARD,
                action="credentials",
            )
        )

        cls.register(
            Shortcut(
                key="j",
                description="Jobs",
                context=ShortcutContext.DASHBOARD,
                action="jobs",
            )
        )

        # ═══════════════════════════════════════════════════════════
        # DETAILED VIEW SHORTCUTS
        # ═══════════════════════════════════════════════════════════

        cls.register(
            Shortcut(
                key="n",
                description="Minimal Mode Toggle",
                context=ShortcutContext.DETAILED_VIEW,
                action="minimal",
            )
        )

        cls.register(
            Shortcut(
                key="s",
                description="Filter Severity",
                context=ShortcutContext.DETAILED_VIEW,
                action="filter_severity",
            )
        )

        cls.register(
            Shortcut(
                key="t",
                description="Toggle Options",
                context=ShortcutContext.DETAILED_VIEW,
                action="toggle_menu",
            )
        )

        # ═══════════════════════════════════════════════════════════
        # VIEW-SPECIFIC SHORTCUTS
        # ═══════════════════════════════════════════════════════════

        cls.register(
            Shortcut(
                key="0",
                description="Back/Return",
                context=ShortcutContext.VIEW,
                action="back",
            )
        )

        cls.register(
            Shortcut(
                key="b",
                description="Back/Return",
                context=ShortcutContext.VIEW,
                action="back",
            )
        )

    @classmethod
    def register(cls, shortcut: Shortcut):
        """Register a keyboard shortcut."""
        key = f"{shortcut.context.value}:{shortcut.key}"
        cls._shortcuts[key] = shortcut

    @classmethod
    def get(cls, key: str, context: ShortcutContext) -> Optional[Shortcut]:
        """Get a shortcut by key and context."""
        lookup_key = f"{context.value}:{key}"
        return cls._shortcuts.get(lookup_key)

    @classmethod
    def get_all_for_context(cls, context: ShortcutContext) -> Dict[str, Shortcut]:
        """Get all shortcuts for a specific context."""
        prefix = f"{context.value}:"
        return {
            key.split(":", 1)[1]: shortcut
            for key, shortcut in cls._shortcuts.items()
            if key.startswith(prefix)
        }

    @classmethod
    def get_global_shortcuts(cls) -> Dict[str, Shortcut]:
        """Get all global shortcuts."""
        return cls.get_all_for_context(ShortcutContext.GLOBAL)

    @classmethod
    def format_shortcut_help(
        cls, context: ShortcutContext, include_global: bool = True
    ) -> str:
        """
        Format shortcuts for display in help text.

        Args:
            context: The context to show shortcuts for
            include_global: Whether to include global shortcuts

        Returns:
            Formatted help text
        """
        lines = []

        # Get context-specific shortcuts
        context_shortcuts = cls.get_all_for_context(context)
        if context_shortcuts:
            lines.append(f"\n{context.value.upper()} SHORTCUTS:")
            lines.append("─" * 60)
            for key, shortcut in sorted(context_shortcuts.items()):
                lines.append(f"  [{key}]  {shortcut.description}")

        # Add global shortcuts
        if include_global:
            global_shortcuts = cls.get_global_shortcuts()
            if global_shortcuts:
                lines.append("\nGLOBAL SHORTCUTS:")
                lines.append("─" * 60)
                for key, shortcut in sorted(global_shortcuts.items()):
                    lines.append(f"  [{key}]  {shortcut.description}")

        return "\n".join(lines)

    @classmethod
    def get_compact_help(cls, *contexts: ShortcutContext) -> str:
        """
        Get compact one-line help for header bars.

        Args:
            *contexts: Contexts to include shortcuts from

        Returns:
            Compact help string like "[q] Quit [m] Menu [?] Help"
        """
        shortcuts = []

        # Collect shortcuts from all specified contexts
        for context in contexts:
            ctx_shortcuts = cls.get_all_for_context(context)
            shortcuts.extend(ctx_shortcuts.items())

        # Add global shortcuts
        shortcuts.extend(cls.get_global_shortcuts().items())

        # Remove duplicates by key
        seen = set()
        unique_shortcuts = []
        for key, shortcut in shortcuts:
            if key not in seen:
                seen.add(key)
                unique_shortcuts.append((key, shortcut))

        # Format compactly
        formatted = [
            f"[{key}] {shortcut.description.split()[0]}"
            for key, shortcut in sorted(unique_shortcuts)
        ]

        return " ".join(formatted)


# Initialize shortcuts on module import
ShortcutManager.initialize()
