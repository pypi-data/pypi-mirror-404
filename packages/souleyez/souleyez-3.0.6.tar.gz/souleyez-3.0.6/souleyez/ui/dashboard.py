#!/usr/bin/env python3
"""
souleyez.ui.dashboard - Live dashboard with real-time updates
"""

import getpass
import os
import time
from datetime import datetime
from enum import Enum
from io import StringIO
from typing import Optional

import click
import wcwidth
from rich.console import Console
from rich.table import Table

from souleyez.config import read_config, write_config
from souleyez.engine.background import get_job, list_jobs
from souleyez.storage.credentials import CredentialsManager
from souleyez.storage.engagements import EngagementManager
from souleyez.storage.evidence import EvidenceManager
from souleyez.storage.findings import FindingsManager
from souleyez.storage.hosts import HostManager
from souleyez.ui.design_system import DesignSystem
from souleyez.ui.log_formatter import format_log_stream
from souleyez.ui.tutorial_state import TutorialStep, get_tutorial_state

# Header cache to avoid expensive recalculations on every refresh
# Format: {key: (timestamp, value)}
_header_cache: dict = {}
_HEADER_CACHE_TTL = 30  # Seconds before recalculating attack surface/correlation


def _get_cached_value(key: str, compute_fn, ttl: int = _HEADER_CACHE_TTL):
    """Get a cached value or compute it if expired."""
    now = time.time()
    if key in _header_cache:
        timestamp, value = _header_cache[key]
        if now - timestamp < ttl:
            return value
    try:
        value = compute_fn()
        _header_cache[key] = (now, value)
        return value
    except Exception:
        return None


# Dashboard state/preferences
class DashboardMode(Enum):
    """Dashboard display modes with clear purposes."""

    OVERVIEW = "overview"  # High-level intelligence and quick actions
    DATA_BROWSER = "data_browser"  # Detailed data exploration
    FOCUS = "focus"  # Intelligence-focused analysis


class DashboardState:
    def __init__(self):
        self.show_hosts = True
        self.show_ports = True
        self.show_findings = True
        self.show_redirects = True
        self.show_progress = True  # Combined data discoveries + recent activity
        self.show_credentials = True
        self.minimal_mode = False
        self.two_column_layout = True
        self.findings_severity_filter = (
            None  # None = critical/high, or 'critical', 'high', 'medium', 'low', 'info'
        )
        self.show_intelligence_summary = True  # NEW - Command Center mode
        self.show_recommendations = True  # NEW - Command Center mode
        self.detailed_view = False  # NEW - Toggle for legacy mode
        self.intelligence_focused = False  # NEW - Epic 4.7: Expand Intelligence panel
        self.mode = DashboardMode.OVERVIEW  # NEW - Clear mode tracking

    def toggle_minimal(self):
        """Toggle between minimal and full mode."""
        self.minimal_mode = not self.minimal_mode
        if self.minimal_mode:
            # Minimal: only critical info
            self.show_hosts = False
            self.show_ports = False
            self.show_findings = True
            self.show_redirects = False
            self.show_progress = False
            self.show_credentials = True
        else:
            # Full mode: everything
            self.show_hosts = True
            self.show_ports = True
            self.show_findings = True
            self.show_redirects = True
            self.show_progress = True
            self.show_credentials = True

    def toggle_detailed_view(self):
        """Toggle between Command Center and Detailed View."""
        self.detailed_view = not self.detailed_view
        if self.detailed_view:
            # Detailed: show everything (legacy mode)
            self.mode = DashboardMode.DATA_BROWSER
            self.show_hosts = True
            self.show_ports = True
            self.show_findings = True
            self.show_redirects = True
            self.show_progress = True
            self.show_credentials = True
            self.show_intelligence_summary = False
            self.show_recommendations = False
        else:
            # Command Center: streamlined
            if self.intelligence_focused:
                self.mode = DashboardMode.FOCUS
            else:
                self.mode = DashboardMode.OVERVIEW
            self.show_hosts = False
            self.show_ports = False
            self.show_findings = True  # Top 3 only
            self.show_redirects = False
            self.show_progress = False
            self.show_credentials = False
            self.show_intelligence_summary = True
            self.show_recommendations = True

    def get_mode_name(self) -> str:
        """Get the current mode's display name."""
        mode_names = {
            DashboardMode.OVERVIEW: "Command Center",
            DashboardMode.DATA_BROWSER: "Data Browser",
            DashboardMode.FOCUS: "Intelligence Focus",
        }
        return mode_names.get(self.mode, "Unknown")

    def get_mode_description(self) -> str:
        """Get the current mode's description."""
        mode_descriptions = {
            DashboardMode.OVERVIEW: "High-level intelligence, quick actions, and recommendations",
            DashboardMode.DATA_BROWSER: "Detailed data exploration - hosts, services, findings",
            DashboardMode.FOCUS: "In-depth intelligence analysis and correlation",
        }
        return mode_descriptions.get(self.mode, "")


def _render_table_to_lines(table: Table) -> list:
    """Helper to render a Rich Table to a list of strings."""
    buffer = StringIO()
    console = Console(file=buffer, width=DesignSystem.get_terminal_width())
    console.print(table)
    return buffer.getvalue().strip().split("\n")


def mask_credential(value):
    """Mask a credential value for display without decrypting."""
    if value is None or value == "" or value == "?":
        return "?"
    # Check if value looks encrypted (Fernet tokens start with 'gAAAAA')
    if isinstance(value, str) and len(value) > 20:
        return "••••••••"
    # Short values might be plaintext, mask them too
    return "••••••••"


def clear_screen():
    """Clear the terminal screen and reset scroll position."""
    DesignSystem.clear_screen()


def get_terminal_size():
    """Get terminal dimensions."""
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except BaseException:
        return 80, 24


def get_dynamic_width():
    """Get terminal width minus padding for borders."""
    width, _ = get_terminal_size()
    return max(80, width - 2)  # Minimum 80, subtract 2 for borders


def create_box(title: str, content_lines: list, icon: str = "") -> list:
    """
    Create a consistent box with dynamic width.

    Args:
        title: Box title (e.g., "INTELLIGENCE AT A GLANCE")
        content_lines: List of content lines
        icon: Optional emoji icon

    Returns:
        List of formatted lines with borders
    """
    import re

    width = get_dynamic_width()
    lines = []

    # Top border with title
    if icon:
        title_text = f" {icon} {title} "
    else:
        title_text = f" {title} "

    # Calculate visual width accounting for ANSI codes
    clean_title = re.sub(r"\x1b\[[0-9;]*m", "", str(title_text))
    title_visual_width = (
        wcwidth.wcswidth(clean_title) if clean_title else len(clean_title)
    )

    padding = max(0, width - title_visual_width - 2)
    lines.append("┌─" + title_text + "─" * padding + "┐")

    # Content lines (padded to width)
    for line in content_lines:
        # Strip ANSI color codes for length calculation
        clean_line = re.sub(r"\x1b\[[0-9;]*m", "", str(line))
        visible_length = wcwidth.wcswidth(clean_line) if clean_line else len(clean_line)

        # Pad to width
        padding = max(0, width - visible_length - 2)
        lines.append("│ " + line + " " * padding + "│")

    # Bottom border
    lines.append("└" + "─" * (width - 2) + "┘")

    return lines


def render_tutorial_hint(width: int) -> list:
    """Render tutorial hint box if tutorial is active - popup style."""
    tutorial_state = get_tutorial_state()

    if not tutorial_state.is_active():
        return []

    hint = tutorial_state.get_hint_for_dashboard()
    if not hint:
        # No hint defined for current step - show a placeholder with step info
        lines = []
        lines.append("")
        step_name = tutorial_state.current_step.name
        lines.append(
            click.style(
                f"  Tutorial active (step: {step_name}) - no dashboard hint for this step",
                fg="yellow",
            )
        )
        lines.append("")
        return lines

    lines = []

    # Fixed inner width for consistent alignment (wide enough for hint text)
    inner_width = 85

    # Left-aligned with small indent (consistent with other views)
    pad = "  "

    lines.append("")
    lines.append("")

    # Double-line border for popup effect
    lines.append(
        pad + click.style("╔" + "═" * inner_width + "╗", fg="yellow", bold=True)
    )

    # Header with background (use fixed padding, emoji is ~2 chars wide visually)
    header_text = " TUTORIAL "
    header_pad_left = (inner_width - len(header_text)) // 2
    header_pad_right = inner_width - header_pad_left - len(header_text)
    header_line = " " * header_pad_left + header_text + " " * header_pad_right
    lines.append(
        pad
        + click.style("║", fg="yellow", bold=True)
        + click.style(header_line, fg="black", bg="yellow", bold=True)
        + click.style("║", fg="yellow", bold=True)
    )

    lines.append(
        pad + click.style("╠" + "═" * inner_width + "╣", fg="yellow", bold=True)
    )

    # Helper to create a padded line
    def make_line(text="", styled_text=None):
        if styled_text is None:
            styled_text = text
        text_len = len(text)
        pad_right = inner_width - 2 - text_len  # 2 for left margin
        return (
            pad
            + click.style("║", fg="yellow", bold=True)
            + "  "
            + styled_text
            + " " * pad_right
            + click.style("║", fg="yellow", bold=True)
        )

    # Empty line for spacing
    lines.append(
        pad
        + click.style("║", fg="yellow", bold=True)
        + " " * inner_width
        + click.style("║", fg="yellow", bold=True)
    )

    # Title
    title = hint.get("title", "Tutorial")
    title_styled = click.style(title, fg="cyan", bold=True)
    lines.append(make_line(title, title_styled))

    # Empty line
    lines.append(
        pad
        + click.style("║", fg="yellow", bold=True)
        + " " * inner_width
        + click.style("║", fg="yellow", bold=True)
    )

    # Hint text (may be multiline)
    hint_text = hint.get("hint", "")
    for hint_line in hint_text.split("\n"):
        # Truncate if needed
        max_len = inner_width - 4
        if len(hint_line) > max_len:
            hint_line = hint_line[: max_len - 3] + "..."
        lines.append(make_line(hint_line))

    # Empty line before action
    lines.append(
        pad
        + click.style("║", fg="yellow", bold=True)
        + " " * inner_width
        + click.style("║", fg="yellow", bold=True)
    )

    # Action with arrow
    action = hint.get("action", "")
    if action:
        action_text = f"> {action}"
        action_styled = click.style(action_text, fg="green", bold=True)
        lines.append(make_line(action_text, action_styled))

    # Empty line
    lines.append(
        pad
        + click.style("║", fg="yellow", bold=True)
        + " " * inner_width
        + click.style("║", fg="yellow", bold=True)
    )

    # Bottom border
    lines.append(
        pad + click.style("╚" + "═" * inner_width + "╝", fg="yellow", bold=True)
    )

    lines.append("")
    lines.append("")

    return lines


def render_header(
    engagement_name: str, engagement_id: int, width: int, state: "DashboardState"
):
    """Render compact dashboard header with status bar and quick actions."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get workspace stats for header
    em = EngagementManager()
    stats = em.stats(engagement_id)

    lines = []

    # Use dynamic width
    dynamic_width = get_dynamic_width()

    # Top border
    lines.append("┌" + "─" * (dynamic_width - 2) + "┐")

    # Title line with workspace, mode, and time
    mode_name = state.get_mode_name()
    title_left = f"│ SOULEYEZ: {mode_name} │ Engagement: {engagement_name}"
    mode_indicator = " [MINIMAL]" if state.minimal_mode else ""
    title_right = f"{mode_indicator} {timestamp} │"
    padding = dynamic_width - len(title_left) - len(title_right)
    lines.append(title_left + " " * padding + title_right)

    # Mode description line
    mode_desc = state.get_mode_description()
    mode_desc_line = f"│ 💡 {mode_desc}"
    mode_desc_visual_width = wcwidth.wcswidth(mode_desc_line)
    mode_desc_padding = dynamic_width - mode_desc_visual_width - 1
    lines.append(mode_desc_line + " " * mode_desc_padding + "│")

    # Stats line with attack surface score (cached to avoid lag)
    attack_surface_text = ""

    def _compute_attack_surface():
        from souleyez.intelligence.surface_analyzer import AttackSurfaceAnalyzer

        analyzer = AttackSurfaceAnalyzer()
        return analyzer.analyze_engagement(engagement_id)

    surface = _get_cached_value(
        f"attack_surface_{engagement_id}", _compute_attack_surface
    )
    if surface and surface.get("hosts"):
        top_host = surface["hosts"][0] if surface["hosts"] else None
        if top_host:
            score = top_host.get("score", 0)
            attack_surface_text = f" │ Attack Surface: {score} pts"

    stats_content = f"│ 📊 Hosts: {stats['hosts']} │ Services: {stats['services']} │ Findings: {stats['findings']}{attack_surface_text}"
    # Calculate visual width (emoji displays as 2 columns)
    visual_width = wcwidth.wcswidth(stats_content)
    stats_padding = dynamic_width - visual_width - 1  # -1 for closing │
    lines.append(stats_content + " " * stats_padding + "│")

    # Exploitation progress line (cached to avoid lag)
    def _compute_correlation():
        from souleyez.intelligence.correlation_analyzer import CorrelationAnalyzer

        corr = CorrelationAnalyzer()
        return corr.analyze_engagement(engagement_id)

    analysis = _get_cached_value(f"correlation_{engagement_id}", _compute_correlation)
    if analysis and analysis.get("summary"):
        summary = analysis["summary"]
        exploited = summary.get("exploited_services", 0)
        total_services = summary.get("total_services", 0)
        if total_services > 0:
            pct = int((exploited / total_services) * 100)
            progress_text = f"│ 🎯 Exploitation Progress: {exploited}/{total_services} services ({pct}%)"
            visual_width = wcwidth.wcswidth(progress_text)
            progress_padding = dynamic_width - visual_width - 1
            lines.append(progress_text + " " * progress_padding + "│")

    # Bottom border
    lines.append("└" + "─" * (dynamic_width - 2) + "┘")

    # Quick actions bar - updated with new hotkeys
    lines.append("┌" + "─" * (dynamic_width - 2) + "┐")
    if state.detailed_view:
        # Detailed view: old hotkeys
        actions_text = " [?] Help [m] Menu [j] Jobs [d] Detect [s] Filter [t] Toggle [n] Minimal [q] Quit "
        actions_padding = dynamic_width - len(actions_text) - 2
        lines.append(
            "│"
            + click.style(actions_text + " " * actions_padding, bold=True, fg="cyan")
            + "│"
        )
    else:
        # Command Center: new hotkeys with numbered actions
        try:
            import sqlite3

            action_count = _get_quick_action_count(engagement_id)
        except sqlite3.OperationalError as e:
            # Database locked - show 0 actions
            action_count = 0
        except Exception as e:
            # Any other error - show 0 actions
            action_count = 0

        # Show Quick Actions with count and conditional styling
        if action_count > 0:
            qa_text = f" [1-{min(action_count, 2)}] Quick Actions ({action_count})"
            qa_styled = click.style(qa_text, bold=True, fg="green")
        else:
            qa_text = " [1-2] Quick Actions (0)"
            qa_styled = click.style(qa_text, dim=True, fg="white")

        rest_text = " [?] Help [m] Menu [i] Intel [j] Jobs [d] Detect [q] Quit "
        # Calculate padding based on plain text length
        plain_text_len = len(qa_text) + len(rest_text)
        actions_padding = dynamic_width - plain_text_len - 2

        lines.append(
            "│"
            + qa_styled
            + click.style(rest_text + " " * actions_padding, bold=True, fg="cyan")
            + "│"
        )

    lines.append("└" + "─" * (dynamic_width - 2) + "┘")

    return lines


def render_workspace_stats(engagement_id: int, width: int):
    """Render workspace statistics panel (removed - now integrated in header)."""
    # Stats are now shown in the header, so this function returns empty
    return []


def render_engagement_summary(engagement_id: int, width: int) -> list:
    """
    Render compact engagement summary - single section with key metrics.
    6 lines total for maximum clarity.
    """
    from souleyez.engine.background import list_jobs
    from souleyez.storage.credentials import CredentialsManager
    from souleyez.storage.deliverables import DeliverableManager
    from souleyez.storage.findings import FindingsManager
    from souleyez.storage.hosts import HostManager

    lines = []
    lines.extend(DesignSystem.section_header("📊", "ENGAGEMENT SUMMARY"))
    lines.append("")

    # Get data
    hm = HostManager()
    fm = FindingsManager()
    cm = CredentialsManager()
    dm = DeliverableManager()

    hosts = hm.list_hosts(engagement_id)
    findings = fm.list_findings(engagement_id)
    credentials = cm.list_credentials(engagement_id)
    deliverables = dm.list_deliverables(engagement_id)

    # Count services
    service_count = 0
    for host in hosts:
        services = hm.get_host_services(host.get("id"))
        service_count += len(services)

    # Count critical/high findings
    critical = len([f for f in findings if f.get("severity") == "critical"])
    high = len([f for f in findings if f.get("severity") == "high"])

    # Count completed deliverables
    completed = len([d for d in deliverables if d.get("status") == "completed"])
    total_deliverables = len(deliverables)
    deliverable_pct = (
        int((completed / total_deliverables) * 100) if total_deliverables > 0 else 0
    )

    # Count evidence (completed jobs)
    all_jobs = list_jobs()
    engagement_jobs = [j for j in all_jobs if j.get("engagement_id") == engagement_id]
    evidence_count = len(
        [
            j
            for j in engagement_jobs
            if j.get("status") in ("done", "no_results", "warning")
        ]
    )

    # Display in 2 columns
    lines.append(f"  Hosts: {len(hosts):<15} Services: {service_count}")
    lines.append(
        f"  Findings: {critical} critical, {high} high{' ' * (15 - len(str(critical)) - len(str(high)) - 19)}Credentials: {len(credentials)}"
    )
    lines.append(
        f"  Evidence: {evidence_count} artifacts{' ' * (15 - len(str(evidence_count)) - 10)}Deliverables: {completed}/{total_deliverables} ({deliverable_pct}%)"
    )
    lines.append("")

    return lines


def render_intelligence_summary(
    engagement_id: int, width: int, expanded: bool = False
) -> list:
    """
    Render Intelligence at-a-glance summary panel.

    Args:
        expanded: If True, show full Intelligence View with all details

    Shows:
    - Attack Surface score + top target + untested count
    - Exploit Suggestions count + top exploit
    - Evidence collection counts by phase
    - Deliverable progress by priority
    """
    # Check if user has Pro tier for advanced intelligence features
    try:
        from souleyez.auth import get_current_user
        from souleyez.auth.permissions import Tier

        current_user = get_current_user()
        is_pro = current_user and current_user.tier == Tier.PRO
    except Exception:
        is_pro = False

    lines = []

    if expanded:
        # Full Intelligence View
        lines.extend(
            DesignSystem.section_header("🎯", "INTELLIGENCE VIEW - ATTACK SURFACE")
        )
        lines.append("")
    else:
        # Compact at-a-glance view
        lines.extend(DesignSystem.section_header("🎯", "INTELLIGENCE AT A GLANCE"))
        lines.append("")

    # 1. Attack Surface Summary (Pro feature, cached to avoid lag)
    if not is_pro:
        lines.append(
            click.style("Attack Surface:        ", fg="white")
            + click.style("🔒 PRO ", fg="yellow")
            + click.style("Upgrade to see priority targeting", fg="bright_black")
        )
    else:
        try:

            def _compute_attack_surface():
                from souleyez.intelligence.surface_analyzer import AttackSurfaceAnalyzer

                analyzer = AttackSurfaceAnalyzer()
                return analyzer.analyze_engagement(engagement_id)

            surface = _get_cached_value(
                f"attack_surface_{engagement_id}", _compute_attack_surface
            )

            if surface and surface.get("hosts"):
                if expanded:
                    # Show all hosts with detailed scoring
                    lines.append(
                        click.style(
                            "🎯 PRIORITIZED ATTACK SURFACE",
                            bold=True,
                            fg="bright_magenta",
                        )
                    )
                    lines.append("")

                    hosts_to_show = (
                        surface["hosts"][:10]
                        if len(surface["hosts"]) > 10
                        else surface["hosts"]
                    )
                    for idx, host in enumerate(hosts_to_show, 1):  # Show top 10
                        score = host.get("score", 0)
                        ip = host.get("host", "Unknown")  # 'host' field contains IP
                        hostname = host.get("hostname", "")
                        display_name = f"{ip} ({hostname})" if hostname else ip

                        services = host.get("services", [])
                        exploited = len(
                            [s for s in services if s.get("status") == "exploited"]
                        )
                        total = len(services)

                        priority_color = (
                            "red" if score > 80 else "yellow" if score > 40 else "green"
                        )
                        lines.append(
                            click.style(
                                f"  {idx}. {display_name}", bold=True, fg=priority_color
                            )
                        )
                        lines.append(
                            f"     Score: {score} pts | Services: {exploited}/{total} exploited"
                        )

                        # Show reasoning
                        reasoning = host.get("reasoning", "")
                        if reasoning:
                            lines.append(f"     {reasoning[:80]}")
                        lines.append("")

                    if len(surface["hosts"]) > 10:
                        remaining = len(surface["hosts"]) - 10
                        lines.append(f"  ... and {remaining} more hosts")
                        lines.append("")
                else:
                    # Compact summary (existing code)
                    top_host = surface["hosts"][0] if surface["hosts"] else None
                    if top_host:
                        score = top_host.get("score", 0)
                        ip = top_host.get("host", "Unknown")  # 'host' field contains IP
                        hostname = top_host.get("hostname", "")
                        display_name = f"{ip} ({hostname})" if hostname else ip

                        services = top_host.get("services", [])
                        exploited_services = len(
                            [s for s in services if s.get("status") == "exploited"]
                        )
                        total_services = len(services)

                        untested_count = 0
                        for host in surface["hosts"]:
                            for svc in host.get("services", []):
                                if svc.get("status") == "not_tried":
                                    untested_count += 1

                        priority = (
                            "HIGH PRIORITY"
                            if score > 80
                            else "MEDIUM PRIORITY" if score > 40 else "LOW PRIORITY"
                        )
                        lines.append(
                            f"Attack Surface:        {score} points ({priority})"
                        )
                        lines.append(
                            f"  Top Target:          {display_name} - {exploited_services}/{total_services} exploited"
                        )

                        if untested_count > 0:
                            lines.append(
                                click.style(
                                    f"  Untested Services:   {untested_count} services ⚠️",
                                    fg="yellow",
                                )
                            )
                        else:
                            lines.append(
                                "  Untested Services:   None (all services tested)"
                            )
                    else:
                        lines.append(
                            "Attack Surface:        No data yet (run scans first)"
                        )
            else:
                lines.append("Attack Surface:        No hosts discovered yet")
        except Exception as e:
            import logging

            logging.error(f"Attack Surface error: {e}", exc_info=True)
            lines.append(f"Attack Surface:        Unable to analyze (check logs)")

    lines.append("")

    # 2. Exploit Suggestions Summary (Pro feature)
    if not is_pro:
        lines.append(
            click.style("Exploit Suggestions:   ", fg="white")
            + click.style("🔒 PRO ", fg="yellow")
            + click.style("Upgrade to see CVE/MSF recommendations", fg="bright_black")
        )
    else:
        # Uses static MSF knowledge base only (use_searchsploit=False) for fast dashboard loading
        # Full searchsploit analysis available via 'x' key or searchsploit plugin
        try:
            import sqlite3

            def _compute_exploit_suggestions():
                from souleyez.intelligence.exploit_suggestions import (
                    ExploitSuggestionEngine,
                )

                suggest_engine = ExploitSuggestionEngine(use_searchsploit=False)
                return suggest_engine.generate_suggestions(engagement_id)

            suggestions = _get_cached_value(
                f"exploit_suggestions_{engagement_id}", _compute_exploit_suggestions
            )

            if suggestions and suggestions.get("hosts"):
                total_exploits = 0
                critical_count = 0
                top_exploit = None

                for host in suggestions["hosts"]:
                    for service in host.get("services", []):
                        exploits = service.get("exploits", [])
                        total_exploits += len(exploits)
                        for exploit in exploits:
                            if exploit.get("severity") == "critical":
                                critical_count += 1
                                if not top_exploit:
                                    top_exploit = exploit

                lines.append(
                    f"Exploit Suggestions:   {total_exploits} MSF modules, {critical_count} CRITICAL"
                )

                if top_exploit:
                    title = top_exploit.get("title", "Unknown")[:50]
                    cve = top_exploit.get("cve", "")
                    lines.append(f"  Top Exploit:         {title}")
                    if cve:
                        lines.append(f"                       ({cve})")
            else:
                lines.append("Exploit Suggestions:   No MSF modules matched")
        except sqlite3.OperationalError:
            # Database locked - show fallback
            lines.append("Exploit Suggestions:   Database busy, refresh to retry")
        except Exception as e:
            import logging

            logging.error(f"Exploit Suggestions error: {e}", exc_info=True)
            lines.append(f"Exploit Suggestions:   Unable to analyze (check logs)")

    lines.append("")

    # 3. Credentials Summary (cached)
    try:

        def _get_credentials():
            from souleyez.storage.credentials import CredentialsManager

            cm = CredentialsManager()
            return cm.list_credentials(engagement_id, decrypt=False)

        creds = _get_cached_value(
            f"credentials_{engagement_id}", _get_credentials, ttl=15
        )

        if creds:
            total = len(creds)

            # Count by type/status
            valid_count = len([c for c in creds if c.get("status") == "valid"])
            hash_count = len([c for c in creds if c.get("credential_type") == "hash"])
            password_count = len(
                [c for c in creds if c.get("credential_type") == "password"]
            )
            tested_count = len(
                [c for c in creds if c.get("status") in ["valid", "invalid"]]
            )
            pending_count = total - tested_count

            # Build type string
            type_parts = []
            if valid_count > 0:
                type_parts.append(
                    click.style(f"{valid_count} VALID", fg="green", bold=True)
                )
            if hash_count > 0:
                type_parts.append(f"{hash_count} HASHES")
            if password_count > 0 and password_count != valid_count:
                type_parts.append(f"{password_count} PASSWORDS")

            type_str = ", ".join(type_parts) if type_parts else "0"

            lines.append(f"Credentials:           {total} discovered ({type_str})")

            # Show latest credential (most recent)
            sorted_creds = sorted(creds, key=lambda c: c.get("id", 0), reverse=True)
            if sorted_creds:
                latest = sorted_creds[0]
                username = latest.get("username", "?")
                password = latest.get("password", "?")
                host = latest.get("host", "?")
                port = latest.get("port", "?")
                service = latest.get("service", "?")

                # Mask password if it's a hash or too long
                if latest.get("credential_type") == "hash":
                    display_pass = (
                        f"{password[:8]}..."
                        if password and len(password) > 8
                        else password
                    )
                elif password and len(password) > 15:
                    display_pass = f"{password[:12]}..."
                else:
                    display_pass = password

                # Color code by status
                status = latest.get("status", "unknown")
                if status == "valid":
                    cred_display = click.style(f"{username}:{display_pass}", fg="green")
                elif status == "invalid":
                    cred_display = click.style(f"{username}:{display_pass}", fg="red")
                else:
                    cred_display = f"{username}:{display_pass}"

                lines.append(
                    f"  Latest:              {cred_display} @ {host}:{port} ({service})"
                )

            # Show tested vs pending
            lines.append(
                f"  Tested:              {tested_count}/{total} validated, {pending_count} pending"
            )
            lines.append(
                click.style(
                    "                       [Press 'c' to view all]", fg="bright_black"
                )
            )
        else:
            lines.append("Credentials:           No credentials discovered yet")
    except Exception as e:
        import logging

        logging.error(f"Credentials summary error: {e}", exc_info=True)
        lines.append(f"Credentials:           Unable to analyze (check logs)")

    lines.append("")

    # 4. OSINT Discoveries Summary (cached)
    try:

        def _get_osint():
            from souleyez.storage.osint import OsintManager

            om = OsintManager()
            return om.list_osint_data(engagement_id)

        all_osint = _get_cached_value(f"osint_{engagement_id}", _get_osint, ttl=30)

        if all_osint:
            # Group by type
            by_type = {}
            for item in all_osint:
                data_type = item.get("data_type", "unknown")
                if data_type not in by_type:
                    by_type[data_type] = []
                by_type[data_type].append(item)

            total_osint = len(all_osint)

            # Get top 3 types by count
            top_types = sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True)[
                :3
            ]
            type_str = ", ".join(f"{t}: {len(items)}" for t, items in top_types)

            lines.append(f"OSINT Discoveries:     {total_osint} records ({type_str})")

            # Show most common type
            if top_types:
                most_common_type, most_common_items = top_types[0]
                lines.append(
                    f"  Top Type:            {most_common_type} ({len(most_common_items)} found)"
                )

            lines.append(
                click.style(
                    "                       [Press 'o' for OSINT view]",
                    fg="bright_black",
                )
            )
        else:
            lines.append("OSINT Discoveries:     No data yet - run recon tools")
    except Exception as e:
        import logging

        logging.error(f"OSINT summary error: {e}", exc_info=True)
        lines.append(f"OSINT Discoveries:     Unable to analyze (check logs)")

    lines.append("")

    # 5. Job Queue Status (NEW!)
    try:
        from souleyez.engine.background import get_all_jobs

        all_jobs = get_all_jobs()

        # Filter to current engagement
        engagement_jobs = [
            j for j in all_jobs if j.get("engagement_id") == engagement_id
        ]

        if engagement_jobs:
            # Count by status
            pending = len([j for j in engagement_jobs if j.get("status") == "queued"])
            running = len([j for j in engagement_jobs if j.get("status") == "running"])
            completed = len(
                [
                    j
                    for j in engagement_jobs
                    if j.get("status") in ("done", "no_results", "warning")
                ]
            )
            failed = len([j for j in engagement_jobs if j.get("status") == "error"])

            # Build status string with colors
            status_parts = []
            if pending > 0:
                status_parts.append(click.style(f"{pending} pending", fg="yellow"))
            else:
                status_parts.append(f"{pending} pending")

            if running > 0:
                status_parts.append(
                    click.style(f"{running} running", fg="green", bold=True)
                )
            else:
                status_parts.append(f"{running} running")

            status_parts.append(f"{completed} completed")

            if failed > 0:
                status_parts.append(click.style(f"{failed} failed", fg="red"))

            status_str = ", ".join(status_parts)

            lines.append(f"Job Queue:             {status_str}")

            # Show next up (first queued job)
            queued_jobs = [j for j in engagement_jobs if j.get("status") == "queued"]
            if queued_jobs:
                # Sort by ID to get oldest queued (should run next)
                queued_jobs.sort(key=lambda j: j.get("id", 0))
                next_job = queued_jobs[0]

                tool = next_job.get("tool", "unknown")
                target = next_job.get("target", "?")
                args = next_job.get("args", [])

                # Format target nicely
                if len(target) > 40:
                    display_target = f"{target[:37]}..."
                else:
                    display_target = target

                # Try to extract useful info from args
                search_term = None
                if tool == "searchsploit" and args:
                    # searchsploit args are the search terms
                    search_term = (
                        " ".join(args) if isinstance(args, list) else str(args)
                    )
                    if len(search_term) > 30:
                        search_term = f"{search_term[:27]}..."

                if search_term:
                    lines.append(f"  Next Up:             {tool} @ {search_term}")
                else:
                    lines.append(f"  Next Up:             {tool} @ {display_target}")
            elif running > 0:
                # Show currently running job
                running_jobs = [
                    j for j in engagement_jobs if j.get("status") == "running"
                ]
                running_jobs.sort(key=lambda j: j.get("id", 0), reverse=True)
                current_job = running_jobs[0]

                tool = current_job.get("tool", "unknown")
                target = current_job.get("target", "?")

                if len(target) > 40:
                    display_target = f"{target[:37]}..."
                else:
                    display_target = target

                lines.append(
                    click.style(
                        f"  Running:             {tool} @ {display_target}", fg="green"
                    )
                )
            else:
                lines.append("  Queue:               Empty (all scans complete)")

            lines.append(
                click.style(
                    "                       [Press 'j' to view all]", fg="bright_black"
                )
            )

            # Show pending chains if any
            try:
                from souleyez.core.pending_chains import get_pending_count

                pending_chains = get_pending_count()
                if pending_chains > 0:
                    lines.append("")
                    lines.append(
                        click.style(f"Pending Chains:        ", fg="cyan")
                        + click.style(
                            f"{pending_chains} awaiting approval",
                            fg="yellow",
                            bold=True,
                        )
                    )
                    lines.append(
                        click.style(
                            "                       [Press 'p' to view Pending Chains]",
                            fg="bright_black",
                        )
                    )
            except:
                pass
        else:
            lines.append("Job Queue:             No jobs yet (start a scan)")
    except Exception as e:
        import logging

        logging.error(f"Job Queue summary error: {e}", exc_info=True)
        lines.append(f"Job Queue:             Unable to analyze (check logs)")

    lines.append("")

    # 5. Evidence Collection Summary
    try:
        evidence_mgr = EvidenceManager()
        phase_counts = evidence_mgr.get_evidence_count(engagement_id)

        total_artifacts = sum(phase_counts.values())

        lines.append(
            f"Evidence Collection:   {total_artifacts} artifacts across 4 phases"
        )
        lines.append(
            f"  Reconnaissance:      {phase_counts.get('reconnaissance', 0)} items"
        )
        lines.append(
            f"  Enumeration:         {phase_counts.get('enumeration', 0)} items"
        )
        lines.append(
            f"  Exploitation:        {phase_counts.get('exploitation', 0)} items"
        )
        lines.append(
            f"  Post-Exploitation:   {phase_counts.get('post_exploitation', 0)} items"
        )
    except Exception as e:
        lines.append(f"Evidence Collection:   Error loading data")

    lines.append("")

    # 6. Deliverables Progress Summary
    try:
        from souleyez.storage.deliverables import DeliverableManager

        dm = DeliverableManager()
        deliverables = dm.list_deliverables(engagement_id)

        if deliverables:
            total = len(deliverables)
            completed = len([d for d in deliverables if d.get("status") == "completed"])

            critical_total = len(
                [d for d in deliverables if d.get("priority") == "critical"]
            )
            critical_done = len(
                [
                    d
                    for d in deliverables
                    if d.get("priority") == "critical"
                    and d.get("status") == "completed"
                ]
            )

            high_total = len([d for d in deliverables if d.get("priority") == "high"])
            high_done = len(
                [
                    d
                    for d in deliverables
                    if d.get("priority") == "high" and d.get("status") == "completed"
                ]
            )

            pending = [
                d
                for d in deliverables
                if d.get("status") != "completed"
                and d.get("priority") in ["critical", "high"]
            ]

            pct = int((completed / total) * 100) if total > 0 else 0
            lines.append(
                f"Deliverables:          {completed}/{total} completed ({pct}%)"
            )

            if critical_total > 0:
                critical_status = "⚠️" if critical_done < critical_total else "✓"
                lines.append(
                    f"  Critical:            {critical_done}/{critical_total} complete {critical_status}"
                )

            if high_total > 0:
                lines.append(
                    f"  High:                {high_done}/{high_total} complete"
                )

            if pending:
                pending_title = pending[0].get("title", "Unknown")[:40]
                lines.append(f'  Pending:             "{pending_title}"')
        else:
            lines.append(
                "Deliverables:          None defined (add testing requirements)"
            )
    except Exception as e:
        import traceback

        lines.append(f"Deliverables:          Error: {str(e)}")

    lines.append("")

    # 7. Findings Summary
    try:
        from souleyez.storage.findings import FindingsManager

        fm = FindingsManager()
        findings = fm.list_findings(engagement_id)

        if findings:
            total = len(findings)

            # Count by severity
            critical_count = len(
                [f for f in findings if f.get("severity") == "critical"]
            )
            high_count = len([f for f in findings if f.get("severity") == "high"])
            medium_count = len([f for f in findings if f.get("severity") == "medium"])
            low_count = len([f for f in findings if f.get("severity") == "low"])

            # Build severity string
            severity_parts = []
            if critical_count > 0:
                severity_parts.append(
                    click.style(f"{critical_count} CRITICAL", fg="red", bold=True)
                )
            if high_count > 0:
                severity_parts.append(click.style(f"{high_count} HIGH", fg="yellow"))
            if medium_count > 0:
                severity_parts.append(f"{medium_count} MEDIUM")
            if low_count > 0:
                severity_parts.append(f"{low_count} LOW")

            severity_str = ", ".join(severity_parts) if severity_parts else "0"

            lines.append(f"Findings:              {total} findings ({severity_str})")

            # Get top finding (highest severity + most recent)
            priority_order = {
                "critical": 0,
                "high": 1,
                "medium": 2,
                "low": 3,
                "info": 4,
            }
            sorted_findings = sorted(
                findings,
                key=lambda f: (
                    priority_order.get(f.get("severity"), 99),
                    -f.get("id", 0),
                ),
            )

            if sorted_findings:
                top_finding = sorted_findings[0]
                title = top_finding.get("title", "Unknown")[:50]
                severity = top_finding.get("severity", "info").upper()
                sev_color = (
                    "red"
                    if severity == "CRITICAL"
                    else "yellow" if severity == "HIGH" else "white"
                )

                lines.append(
                    f"  Top Finding:         {title} "
                    + click.style(f"({severity})", fg=sev_color)
                )

            # Tool distribution
            tool_counts = {}
            for f in findings:
                tool = f.get("tool", "unknown")
                tool_counts[tool] = tool_counts.get(tool, 0) + 1

            # Show top 3 tools
            top_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[
                :3
            ]
            if top_tools:
                tool_str = ", ".join([f"{tool}: {count}" for tool, count in top_tools])
                lines.append(f"  Tool Distribution:   {tool_str}")

            lines.append(
                click.style(
                    "                       [Press 'f' to view all]", fg="bright_black"
                )
            )
        else:
            lines.append(
                "Findings:              No findings yet (run vulnerability scans)"
            )
    except Exception as e:
        import logging

        logging.error(f"Findings summary error: {e}", exc_info=True)
        lines.append(f"Findings:              Unable to analyze (check logs)")

    lines.append("")

    # 8. Detection Coverage Summary (SIEM Integration) - Pro feature
    if not is_pro:
        lines.append(
            click.style("Detection Coverage:    ", fg="white")
            + click.style("🔒 PRO ", fg="yellow")
            + click.style("Upgrade to see SIEM integration", fg="bright_black")
        )
    else:
        try:
            from souleyez.integrations.siem import SIEMFactory
            from souleyez.integrations.wazuh.config import WazuhConfig

            config = WazuhConfig.get_config(engagement_id)

            if config and config.get("enabled"):
                # SIEM is configured - show detection stats
                siem_type = config.get("siem_type", "wazuh")
                siem_info = SIEMFactory.get_type_info(siem_type)
                siem_name = siem_info.get("name", siem_type.title())

                from souleyez.storage.database import get_db

                db = get_db()
                conn = db.get_connection()
                cursor = conn.cursor()

                # Get detection results for this engagement
                cursor.execute(
                    """
                    SELECT detection_status, COUNT(*)
                    FROM detection_results
                    WHERE engagement_id = ?
                    GROUP BY detection_status
                """,
                    (engagement_id,),
                )

                status_counts = {row[0]: row[1] for row in cursor.fetchall()}
                detected = status_counts.get("detected", 0)
                not_detected = status_counts.get("not_detected", 0)
                total = detected + not_detected

                if total > 0:
                    coverage_pct = int((detected / total) * 100)
                    cov_color = (
                        "green"
                        if coverage_pct >= 70
                        else ("yellow" if coverage_pct >= 40 else "red")
                    )

                    lines.append(
                        f"Detection Coverage:    "
                        + click.style(f"{coverage_pct}%", fg=cov_color, bold=True)
                        + f" ({detected}/{total} detected) "
                        + click.style(f"✓ {siem_name}", fg="green")
                    )

                    if not_detected > 0:
                        lines.append(
                            click.style(
                                f"  Gaps:                {not_detected} attacks not detected",
                                fg="red",
                            )
                        )

                    # Get last validation time
                    cursor.execute(
                        """
                        SELECT MAX(checked_at) FROM detection_results WHERE engagement_id = ?
                    """,
                        (engagement_id,),
                    )
                    last_check = cursor.fetchone()[0]
                    if last_check:
                        lines.append(f"  Last Validated:      {last_check[:16]}")
                else:
                    lines.append(
                        f"Detection Coverage:    "
                        + click.style("Not validated yet", fg="yellow")
                        + " "
                        + click.style(f"✓ {siem_name}", fg="green")
                    )
                    lines.append(f"  Run attacks, then validate to see coverage")

                lines.append(
                    click.style(
                        "                       [Press 'd' for detection details]",
                        fg="bright_black",
                    )
                )
            else:
                # SIEM not configured
                lines.append(
                    f"Detection Coverage:    "
                    + click.style("⚠️ Not configured", fg="yellow")
                )
                lines.append(
                    click.style(
                        "                       [Press 'd' to set up SIEM]",
                        fg="bright_black",
                    )
                )
        except Exception as e:
            import logging

            logging.error(f"Detection Coverage error: {e}", exc_info=True)
            lines.append(f"Detection Coverage:    Unable to load (check logs)")

    lines.append("")

    # 9. AI Provider Status - Pro feature
    if not is_pro:
        lines.append(
            click.style("AI Providers:          ", fg="white")
            + click.style("🔒 PRO ", fg="yellow")
            + click.style("Upgrade to access AI-powered features", fg="bright_black")
        )
    else:
        try:
            from souleyez.ai.claude_provider import ClaudeProvider
            from souleyez.ai.ollama_provider import OllamaProvider

            config = read_config()
            current_provider = config.get("ai", {}).get("provider", "ollama")

            ollama = OllamaProvider()
            claude = ClaudeProvider()
            ollama_available = ollama.is_available()
            claude_available = claude.is_available()

            if ollama_available or claude_available:
                # Show active provider first with indicator
                if current_provider == "ollama" and ollama_available:
                    ollama_status = ollama.get_status()
                    model = ollama_status.get("configured_model", "local")
                    endpoint = ollama_status.get("endpoint", "http://localhost:11434")
                    is_vm_host = not endpoint.startswith(
                        ("http://localhost", "http://127.0.0.1")
                    )
                    location = "Network" if is_vm_host else "Local"
                    active = click.style(
                        f"Ollama {location} ({model})", fg="green", bold=True
                    ) + click.style(" ◀", fg="green")
                    other = click.style("Claude", fg="cyan") if claude_available else ""
                elif current_provider == "claude" and claude_available:
                    claude_status = claude.get_status()
                    model = claude_status.get("model", "claude-sonnet-4-20250514")
                    active = click.style(f"Claude", fg="cyan", bold=True) + click.style(
                        " ◀", fg="cyan"
                    )
                    other = (
                        click.style(f"Ollama", fg="green") if ollama_available else ""
                    )
                elif ollama_available:
                    ollama_status = ollama.get_status()
                    model = ollama_status.get("configured_model", "local")
                    endpoint = ollama_status.get("endpoint", "http://localhost:11434")
                    is_vm_host = not endpoint.startswith(
                        ("http://localhost", "http://127.0.0.1")
                    )
                    location = "Network" if is_vm_host else "Local"
                    active = click.style(f"Ollama {location} ({model})", fg="green")
                    other = click.style("Claude", fg="cyan") if claude_available else ""
                else:
                    active = click.style("Claude", fg="cyan")
                    other = ""

                provider_list = active + (", " + other if other else "")
                lines.append(
                    f"AI Providers:          {provider_list}"
                    + click.style(" ✓ Ready", fg="green")
                )
                lines.append(
                    click.style(
                        "                       [Press 'a' to toggle provider, 'x' for AI Execute]",
                        fg="bright_black",
                    )
                )
            else:
                lines.append(
                    f"AI Providers:          "
                    + click.style("⚠️ Not configured", fg="yellow")
                )
                lines.append(
                    click.style(
                        "                       [Settings → AI Settings to configure]",
                        fg="bright_black",
                    )
                )
        except Exception:
            lines.append(
                f"AI Providers:          "
                + click.style("Not available", fg="bright_black")
            )

    lines.append("")

    return lines


def render_smart_recommendations(engagement_id: int, width: int) -> list:
    """
    Generate top 3 actionable recommendations based on:
    - Attack surface gaps (untested services)
    - Critical exploit suggestions
    - Pending deliverables
    """
    lines = []
    lines.extend(DesignSystem.section_header("💡", "RECOMMENDATIONS"))

    recommendations = []

    # 1. Get untested services from Attack Surface (cached)
    try:

        def _compute_attack_surface():
            from souleyez.intelligence.surface_analyzer import AttackSurfaceAnalyzer

            analyzer = AttackSurfaceAnalyzer()
            return analyzer.analyze_engagement(engagement_id)

        surface = _get_cached_value(
            f"attack_surface_{engagement_id}", _compute_attack_surface
        )

        if surface and surface.get("hosts"):
            for host in surface["hosts"]:
                for service in host.get("services", []):
                    if service.get("status") == "not_tried":
                        port = service.get("port")
                        service_name = service.get("service")
                        ip = host.get("ip")

                        recommendations.append(
                            {
                                "priority": (
                                    "CRITICAL" if host.get("score", 0) > 80 else "HIGH"
                                ),
                                "action": f"Exploit {service_name} on {ip}:{port} (not attempted)",
                                "reason": f"{service_name.upper()} service discovered, no exploitation attempts",
                            }
                        )
    except:
        pass

    # 2. Get critical exploits from Exploit Suggestions
    try:
        from souleyez.intelligence.exploit_suggestions import ExploitSuggestionEngine

        suggest_engine = ExploitSuggestionEngine()
        suggestions = suggest_engine.generate_suggestions(engagement_id)

        if suggestions and suggestions.get("hosts"):
            for host in suggestions["hosts"]:
                for service in host.get("services", []):
                    for exploit in service.get("exploits", []):
                        if exploit.get("severity") == "critical":
                            title = exploit.get("title", "")[:50]
                            ip = host.get("ip")
                            match_type = exploit.get("match_type", "")
                            cve = exploit.get("cve", "")

                            if match_type == "exact":
                                recommendations.append(
                                    {
                                        "priority": "HIGH",
                                        "action": f"Test {title} on {ip}",
                                        "reason": f"{cve} matches exact version",
                                    }
                                )
    except:
        pass

    # 3. Get pending critical deliverables
    try:
        from souleyez.storage.deliverables import DeliverableManager

        dm = DeliverableManager()
        deliverables = dm.list_deliverables(engagement_id)

        pending = [d for d in deliverables if d.get("status") != "completed"]
        critical_pending = [d for d in pending if d.get("priority") == "critical"]

        if critical_pending:
            count = len(critical_pending)
            recommendations.append(
                {
                    "priority": "MEDIUM",
                    "action": f"Complete {count} critical deliverable(s)",
                    "reason": f"Critical testing requirements still incomplete",
                }
            )
        elif len(pending) > 0:
            pct = int((len(pending) / len(deliverables)) * 100) if deliverables else 0
            recommendations.append(
                {
                    "priority": "MEDIUM",
                    "action": f"Complete {len(pending)} pending deliverable(s)",
                    "reason": f"{pct}% of deliverables still incomplete",
                }
            )
    except:
        pass

    # Sort by priority and take top 3
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    recommendations.sort(key=lambda x: priority_order.get(x["priority"], 99))
    top_3 = recommendations[:3]

    if not top_3:
        lines.append("  No recommendations (all services tested)")
    else:
        for i, rec in enumerate(top_3, 1):
            priority_colors = {
                "CRITICAL": "red",
                "HIGH": "yellow",
                "MEDIUM": "blue",
                "LOW": "white",
            }
            color = priority_colors.get(rec["priority"], "white")

            lines.append(
                f"{i}. {click.style('[' + rec['priority'] + ']', fg=color, bold=True)} {rec['action']}"
            )
            lines.append(f"   Reason: {rec['reason']}")
            lines.append("")

    lines.append("")

    return lines


def render_new_tool_metrics(engagement_id: int, width: int):
    """Render metrics for newly added tools (WHOIS, Subfinder, WPScan, Hydra)."""
    lines = []
    lines.extend(DesignSystem.section_header("📊", "TOOL METRICS"))

    # Get data (cached to avoid lag)
    def _get_tool_metrics_data():
        from souleyez.engine.background import list_jobs
        from souleyez.storage.findings import FindingsManager
        from souleyez.storage.hosts import HostManager
        from souleyez.storage.osint import OsintManager
        from souleyez.storage.smb_shares import SMBSharesManager
        from souleyez.storage.web_paths import WebPathsManager

        hm = HostManager()
        fm = FindingsManager()
        smb_mgr = SMBSharesManager()
        wp_mgr = WebPathsManager()

        # Get web paths count via SQL
        web_paths_count = 0
        try:
            result = wp_mgr.db.execute_one(
                """
                SELECT COUNT(*) as cnt FROM web_paths wp
                JOIN hosts h ON wp.host_id = h.id
                WHERE h.engagement_id = ?
            """,
                (engagement_id,),
            )
            web_paths_count = result["cnt"] if result else 0
        except Exception:
            pass

        return {
            "jobs": list_jobs(limit=100),
            "findings": fm.list_findings(engagement_id, limit=500),
            "osint": OsintManager().list_osint_data(engagement_id),
            "hosts": hm.list_hosts(engagement_id, limit=200),
            "smb_shares": smb_mgr.list_shares(engagement_id),
            "web_paths_count": web_paths_count,
        }

    data = _get_cached_value(
        f"tool_metrics_{engagement_id}", _get_tool_metrics_data, ttl=30
    )
    if not data:
        lines.append("  Metrics temporarily unavailable")
        return lines

    jobs = data["jobs"]
    all_findings = data["findings"]
    osint_data = data["osint"]
    all_hosts = data["hosts"]

    # theHarvester: Count OSINT data (hosts, emails, IPs)
    osint_count = len(osint_data) if osint_data else 0

    # DNSRecon: Count DNS records discovered (count completed jobs)
    dnsrecon_jobs = [
        j for j in jobs if j.get("tool") == "dnsrecon" and j.get("status") == "done"
    ]
    dnsrecon_count = len(dnsrecon_jobs)

    # WHOIS: Count domains analyzed
    whois_jobs = [
        j for j in jobs if j.get("tool") == "whois" and j.get("status") == "done"
    ]
    whois_count = len(whois_jobs)

    # Nmap: Count active hosts discovered (all_hosts already from cache)
    active_hosts = (
        [h for h in all_hosts if h.get("status") == "up"] if all_hosts else []
    )
    nmap_count = len(active_hosts)

    # Enum4linux: Count SMB findings
    enum4linux_findings = [f for f in all_findings if f.get("tool") == "enum4linux"]
    enum4linux_count = len(enum4linux_findings)

    # SMBMap: Count shares discovered (from cache)
    smbmap_shares = data.get("smb_shares", [])
    smbmap_count = len(smbmap_shares) if smbmap_shares else 0

    # Nuclei: Count web vulnerabilities
    nuclei_findings = (
        [f for f in all_findings if f.get("tool") == "nuclei"] if all_findings else []
    )
    nuclei_count = len(nuclei_findings)

    # Gobuster: Count web paths (from cache)
    gobuster_count = data.get("web_paths_count", 0)

    # SQLMap: Count SQL injection findings (count completed jobs)
    sqlmap_jobs = [
        j for j in jobs if j.get("tool") == "sqlmap" and j.get("status") == "done"
    ]
    sqlmap_count = len(sqlmap_jobs)

    # WPScan: Count WordPress vulnerabilities
    wpscan_findings = (
        [f for f in all_findings if f.get("tool") == "wpscan"] if all_findings else []
    )
    wpscan_count = len(wpscan_findings)

    # Hydra: Count credentials discovered (use cached credentials)
    creds = _get_cached_value(f"credentials_{engagement_id}", lambda: None, ttl=15)
    hydra_creds = [c for c in creds if c.get("source") == "hydra"] if creds else []
    hydra_count = len(hydra_creds)

    # MSF Auxiliary: Count findings
    msf_findings = [f for f in all_findings if f.get("tool") == "msf_auxiliary"]
    msf_count = len(msf_findings)

    # Display metrics in a compact table
    metrics = [
        ("theHarvester", "OSINT Data", osint_count),
        ("DNSRecon", "DNS Scans", dnsrecon_count),
        ("WHOIS", "Domains", whois_count),
        ("Nmap", "Hosts", nmap_count),
        ("Enum4linux", "SMB Findings", enum4linux_count),
        ("SMBMap", "Shares", smbmap_count),
        ("Nuclei", "Web Vulns", nuclei_count),
        ("Gobuster", "Web Paths", gobuster_count),
        ("SQLMap", "SQL Scans", sqlmap_count),
        ("WPScan", "WP Vulns", wpscan_count),
        ("Hydra", "Credentials", hydra_count),
        ("MSF Auxiliary", "Findings", msf_count),
    ]

    # Create Rich Table
    table = DesignSystem.create_table()
    table.add_column("Tool", width=30)
    table.add_column("Data Type", width=30)
    table.add_column("Count", justify="right", width=36)

    # Add rows
    for tool, data_type, count in metrics:
        style = "cyan bold" if count > 0 else "dim"
        table.add_row(tool, data_type, str(count), style=style)

    # Render to lines
    lines.extend(_render_table_to_lines(table))

    return lines


def render_active_jobs(width: int, engagement_id: Optional[int] = None):
    """Render active jobs panel.

    Args:
        width: Terminal width
        engagement_id: If provided, used to highlight jobs from other engagements
    """
    from souleyez.engine.background import get_active_jobs

    active_jobs = get_active_jobs()

    # Filter to current engagement if specified
    if engagement_id is not None:
        active_jobs = [
            j for j in active_jobs if j.get("engagement_id") == engagement_id
        ]

    lines = []
    lines.extend(DesignSystem.section_header("⚡", "ACTIVE JOBS"))

    if not active_jobs:
        lines.append("No active jobs")
    else:
        # Show up to 3 active jobs in Command Center mode
        for job in active_jobs[:3]:
            jid = job.get("id", "?")
            tool = job.get("tool", "unknown")[:10]
            target = job.get("target", "")[:30]
            status = job.get("status", "unknown")
            job_eng_id = job.get("engagement_id")

            # Color code status
            if status == "running":
                status_str = click.style("▶ running", fg="yellow")
            elif status == "queued":
                status_str = click.style("⏸ queued", fg="cyan")
            else:
                status_str = status

            # Calculate elapsed time
            started = job.get("started_at", "")

            elapsed = ""
            if started:
                try:
                    from dateutil import parser as date_parser

                    start_time = date_parser.parse(started)
                    now = datetime.now(start_time.tzinfo)
                    delta = now - start_time
                    elapsed_secs = int(delta.total_seconds())
                    mins, secs = divmod(elapsed_secs, 60)
                    if status == "running":
                        elapsed = f"({mins}m {secs}s elapsed)"
                    else:
                        elapsed = f"({mins}m {secs}s queued)"
                except BaseException:
                    elapsed = "(?)"

            # Warn if job is from different engagement
            warning = ""
            if engagement_id is not None and job_eng_id != engagement_id:
                warning = click.style(" [!other]", fg="red")

            # Check for scope warnings
            job_warnings = job.get("metadata", {}).get("warnings", [])
            scope_warning = any("SCOPE" in w for w in job_warnings)
            scope_indicator = click.style("⚠ ", fg="yellow") if scope_warning else ""

            job_line = f"  [{jid:>3}] {scope_indicator}{tool:<10} {target:<30} {status_str:<18} {elapsed}{warning}"
            lines.append(job_line)

            # Show scope warning details on next line if present
            if scope_warning:
                for w in job_warnings:
                    if "SCOPE" in w:
                        lines.append(click.style(f"        └─ {w}", fg="yellow"))

    return lines


def render_recent_hosts(engagement_id: int, width: int):
    """Render hosts with most open ports/services."""
    hm = HostManager()
    all_hosts = hm.list_hosts(engagement_id)

    # Filter to live hosts and get service counts
    live_hosts = [h for h in all_hosts if h.get("status") == "up"]

    # Build list with service counts for sorting
    hosts_with_counts = []
    for host in live_hosts:
        services = hm.get_host_services(host.get("id"))
        svc_count = len(services) if services else 0
        # Only include hosts with at least 1 service
        if svc_count > 0:
            hosts_with_counts.append((host, svc_count))

    # Sort by service count descending (most services first), then by ID
    hosts_with_counts.sort(key=lambda x: (x[1], x[0].get("id", 0)), reverse=True)
    top_hosts = hosts_with_counts[:10]  # Show up to 10 hosts with services

    lines = []
    lines.extend(DesignSystem.section_header("🎯", "TOP HOSTS BY SERVICES"))

    if not top_hosts:
        lines.append("No live hosts discovered yet")
    else:
        # Create Rich Table
        table = DesignSystem.create_table()
        table.add_column("ID", width=8)
        table.add_column("IP Address", width=18)
        table.add_column("Description/OS", width=59)
        table.add_column("Services", justify="right", width=10)

        # Add rows
        for host, svc_count in top_hosts:
            hid = f"#{host.get('id', '?')}"
            ip = (host.get("ip_address") or "unknown")[:15]
            hostname = (host.get("hostname") or "")[:30]
            os_info = (host.get("os_name") or "")[:30]

            # Build description
            if hostname:
                desc = hostname
            elif os_info:
                desc = os_info
            else:
                desc = "new host"

            table.add_row(hid, ip, desc, str(svc_count))

        # Render to lines
        lines.extend(_render_table_to_lines(table))

    return lines


def render_ai_recommendation(engagement_id: int, width: int):
    """Render AI recommendation panel."""
    from souleyez.ai.recommender import AttackRecommender

    lines = []
    lines.append("")
    lines.append(click.style("🤖 AI RECOMMENDATION", bold=True, fg="cyan"))
    lines.append(DesignSystem.separator(width))

    # Get AI recommendation (skip on error to keep dashboard responsive)
    try:
        recommender = AttackRecommender()
        recommendation = recommender.suggest_next_step(engagement_id)

        # Handle error state
        if recommendation.get("error"):
            error_msg = recommendation["error"][: width - 4]
            lines.append(f"  ⚠️  {error_msg}")
            lines.append(f"  💡 Try: souleyez ai recommend")
            lines.append("")
            return lines

        # Extract recommendation details
        action = recommendation.get("action", "Unknown")
        target = recommendation.get("target", "Unknown")
        risk = recommendation.get("risk_level", "unknown").upper()
        rationale = recommendation.get("rationale", "")

        # Color code risk
        if risk == "LOW":
            risk_display = click.style(risk, fg="green", bold=True)
        elif risk == "MEDIUM":
            risk_display = click.style(risk, fg="yellow", bold=True)
        else:
            risk_display = click.style(risk, fg="red", bold=True)

        # Display recommendation in a box
        lines.append("  ┌" + "─" * (width - 4) + "┐")

        # Action line
        action_text = f"ACTION: {action}"
        if len(action_text) > width - 8:
            action_text = action_text[: width - 11] + "..."
        lines.append("  │ " + action_text.ljust(width - 6) + " │")

        # Target line
        target_text = f"TARGET: {target}"
        if len(target_text) > width - 8:
            target_text = target_text[: width - 11] + "..."
        lines.append("  │ " + target_text.ljust(width - 6) + " │")

        # Risk line
        lines.append("  │ " + "RISK: ".ljust(width - 6) + " │")
        lines.append(
            "  │ " + " " * 7 + risk_display + " " * (width - 13 - len(risk)) + " │"
        )

        # Separator
        lines.append("  ├" + "─" * (width - 4) + "┤")

        # Rationale (wrapped if needed)
        rationale_prefix = "WHY: "
        max_line_len = width - 8

        if len(rationale) > max_line_len - len(rationale_prefix):
            # Wrap rationale
            words = rationale.split()
            current_line = rationale_prefix

            for word in words:
                if len(current_line) + len(word) + 1 <= max_line_len:
                    if current_line == rationale_prefix:
                        current_line += word
                    else:
                        current_line += " " + word
                else:
                    lines.append("  │ " + current_line.ljust(width - 6) + " │")
                    current_line = "     " + word

            # Add final line
            if current_line.strip():
                lines.append("  │ " + current_line.ljust(width - 6) + " │")
        else:
            lines.append(
                "  │ " + (rationale_prefix + rationale).ljust(width - 6) + " │"
            )

        # Bottom with action hint
        lines.append("  ├" + "─" * (width - 4) + "┤")
        lines.append(
            "  │ "
            + click.style("Press 'x' to execute this recommendation", fg="cyan").ljust(
                width - 6 + 9
            )
            + " │"
        )
        lines.append("  └" + "─" * (width - 4) + "┘")

    except Exception as e:
        # Any error: show message and keep dashboard responsive
        lines.append(f"  ⚠️  AI unavailable - use CLI: souleyez ai recommend")
        lines.append("")

    return lines


def _quick_toggle_ai_provider():
    """Quick toggle between Ollama and Claude AI providers."""
    config = read_config()
    current = config.get("ai", {}).get("provider", "ollama")

    # Check what's available
    ollama_available = False
    claude_available = False

    try:
        from souleyez.ai.ollama_provider import OllamaProvider

        ollama = OllamaProvider()
        ollama_available = ollama.is_available()
    except Exception:
        pass

    try:
        from souleyez.ai.claude_provider import ClaudeProvider

        claude = ClaudeProvider()
        claude_available = claude.is_available()
    except Exception:
        pass

    # Toggle logic
    if current == "ollama" and claude_available:
        config.setdefault("ai", {})["provider"] = "claude"
        write_config(config)
        click.echo(click.style("\n  ✓ Switched to Claude", fg="cyan", bold=True))
        click.echo(
            click.style("    ⚠️  Data will be sent to Anthropic's API", fg="yellow")
        )
    elif current == "claude" and ollama_available:
        config.setdefault("ai", {})["provider"] = "ollama"
        write_config(config)
        click.echo(click.style("\n  ✓ Switched to Ollama", fg="green", bold=True))
        click.echo(click.style("    Data stays local on your machine", fg="green"))
    elif not ollama_available and not claude_available:
        click.echo(click.style("\n  ⚠️  No AI providers available", fg="yellow"))
        click.echo("    Configure Ollama (ollama serve) or Claude API key in Settings")
    elif current == "ollama" and not claude_available:
        click.echo(click.style("\n  ○ Claude not configured", fg="yellow"))
        click.echo("    Set up Claude API key in Settings → AI Settings")
    else:
        click.echo(click.style("\n  ○ Ollama not running", fg="yellow"))
        click.echo("    Start with: ollama serve")

    time.sleep(1.5)


def _execute_ai_recommendation(engagement_id: int):
    """Execute AI recommendation from dashboard."""
    from souleyez.ai.executor import InteractiveExecutor
    from souleyez.ai.recommender import AttackRecommender
    from souleyez.ai.safety import ApprovalMode
    from souleyez.ui.progress_indicators import with_ai_quotes

    clear_screen()
    click.echo(click.style("\n🤖 AI-DRIVEN EXECUTION\n", fg="cyan", bold=True))

    # === AI PROVIDER SELECTION ===
    click.echo(click.style("  🧠 SELECT AI PROVIDER:", bold=True, fg="cyan"))
    click.echo("  " + "─" * 60)

    # Check available providers
    try:
        from souleyez.ai.claude_provider import ClaudeProvider
        from souleyez.ai.ollama_provider import OllamaProvider

        ollama = OllamaProvider()
        claude = ClaudeProvider()
        ollama_available = ollama.is_available()
        claude_available = claude.is_available()

        ollama_status = ollama.get_status()
        claude_status = claude.get_status()
    except Exception:
        ollama_available = False
        claude_available = False
        ollama_status = {}
        claude_status = {}

    selected_provider = None

    if not ollama_available and not claude_available:
        click.echo(click.style("    ⚠ No AI providers available!", fg="red"))
        click.echo("    • Start Ollama: " + click.style("ollama serve", fg="cyan"))
        click.echo(
            "    • Or configure Claude: "
            + click.style("Settings → [8] Claude API", fg="cyan")
        )
        click.echo()
        click.echo(click.style("Press Enter to return...", fg="cyan"))
        input()
        return

    # Show available providers
    if ollama_available:
        model = ollama_status.get("configured_model", "unknown")
        click.echo(
            f"    "
            + click.style("[1]", fg="green", bold=True)
            + f" Ollama (Local)     - {model} "
            + click.style("[FREE, PRIVATE]", fg="green")
        )
    else:
        click.echo(
            f"    "
            + click.style("[1]", fg="bright_black")
            + " Ollama (Local)     - "
            + click.style("Not running", fg="yellow")
        )

    if claude_available:
        click.echo(
            f"    "
            + click.style("[2]", fg="cyan", bold=True)
            + " Claude (Anthropic) - "
            + click.style("Higher quality reasoning", fg="cyan")
            + " "
            + click.style("[CLOUD]", fg="yellow")
        )
    else:
        key_configured = claude_status.get("api_key_configured", False)
        if not key_configured:
            click.echo(
                f"    "
                + click.style("[2]", fg="bright_black")
                + " Claude (Anthropic) - "
                + click.style("API key not configured", fg="yellow")
            )
        else:
            click.echo(
                f"    "
                + click.style("[2]", fg="bright_black")
                + " Claude (Anthropic) - "
                + click.style("Package not installed", fg="yellow")
            )

    click.echo()
    click.echo(
        "    " + click.style("[q]", fg="white", bold=True) + " ← Back to dashboard"
    )
    click.echo()
    click.echo("  " + "─" * 60)

    # Get provider selection
    if ollama_available and claude_available:
        click.echo(click.style("  Select AI provider [1/2/q]: ", bold=True), nl=False)
        try:
            provider_choice = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            return

        if provider_choice == "q":
            return
        elif provider_choice == "2":
            click.echo()
            click.echo(click.style("  ⚠ PRIVACY NOTICE:", fg="yellow", bold=True))
            click.echo(
                "    Engagement data (hosts, services, credentials) will be sent to"
            )
            click.echo("    Anthropic's servers for AI processing.")
            click.echo()
            try:
                confirm = click.prompt("  Proceed with Claude?", type=str, default="y")
            except (KeyboardInterrupt, EOFError):
                return
            if confirm.lower() in ["y", "yes"]:
                selected_provider = "claude"
            else:
                click.echo(click.style("  Cancelled.", fg="yellow"))
                time.sleep(1)
                return
        else:
            selected_provider = "ollama"
    elif ollama_available:
        click.echo(click.style("  Using Ollama (only available provider)", fg="green"))
        selected_provider = "ollama"
        time.sleep(0.5)
    elif claude_available:
        click.echo(
            click.style(
                "  ⚠ PRIVACY: Data will be sent to Anthropic's servers", fg="yellow"
            )
        )
        try:
            confirm = click.prompt("  Use Claude?", type=str, default="y")
        except (KeyboardInterrupt, EOFError):
            return
        if confirm.lower() in ["y", "yes"]:
            selected_provider = "claude"
        else:
            click.echo(click.style("  Cancelled.", fg="yellow"))
            time.sleep(1)
            return

    click.echo(
        f"\n  ✓ AI Provider: {click.style(selected_provider.upper(), fg='cyan', bold=True)}"
    )
    click.echo()

    # === EXECUTE RECOMMENDATION ===
    click.echo(
        click.style("🤖 Generating AI Recommendation...\n", fg="cyan", bold=True)
    )
    click.echo(click.style("Analyzing engagement data...\n", fg="yellow"))

    # Create provider based on user selection
    if selected_provider == "claude":
        from souleyez.ai.claude_provider import ClaudeProvider

        provider = ClaudeProvider()
    else:
        from souleyez.ai.ollama_provider import OllamaProvider

        provider = OllamaProvider()

    recommender = AttackRecommender(provider=provider)
    recommendation = with_ai_quotes(recommender.suggest_next_step, engagement_id)

    # Clear the quote line and add newline
    click.echo()

    if recommendation.get("error"):
        click.echo(click.style(f"✗ Error: {recommendation['error']}", fg="red"))
        click.echo(click.style("\nPress Enter to return to dashboard...", fg="cyan"))
        input()
        return

    # Display what we're about to execute
    click.echo(f"  ACTION: {recommendation.get('action', 'Unknown')}")
    click.echo(f"  TARGET: {recommendation.get('target', 'Unknown')}")
    click.echo(f"  RISK: {recommendation.get('risk_level', 'Unknown').upper()}")
    click.echo()

    # Execute with manual approval (pass provider to maintain user's selection)
    executor = InteractiveExecutor(ApprovalMode.MANUAL, provider=provider)
    try:
        # Execute just one iteration
        result = executor.execute_loop(engagement_id, max_iterations=1, once=True)

        click.echo()
        click.echo(click.style("✓ Execution complete!", fg="green"))

    except KeyboardInterrupt:
        click.echo(click.style("\n⏹  Execution aborted", fg="yellow"))
    except Exception as e:
        click.echo(click.style(f"\n✗ Error: {e}", fg="red"))

    click.echo(click.style("\nPress Enter to return to dashboard...", fg="cyan"))
    input()


def render_critical_findings(
    engagement_id: int, width: int, severity_filter: str = None
):
    """Render critical findings with optional severity filter."""
    fm = FindingsManager()
    # hm not used currently
    findings = fm.list_findings(engagement_id)

    # Count by severity for display
    critical_count = len([f for f in findings if f.get("severity") == "critical"])
    high_count = len([f for f in findings if f.get("severity") == "high"])
    # medium_count and low_count not used currently

    # Apply severity filter if provided, otherwise show CRITICAL ONLY (changed from critical/high)
    if severity_filter:
        filtered = [f for f in findings if f.get("severity") == severity_filter]
        title = f"🔍 {severity_filter.upper()} FINDINGS"
        title_color = {
            "critical": "red",
            "high": "red",
            "medium": "yellow",
            "low": "blue",
            "info": "white",
        }.get(severity_filter, "white")
    else:
        # Default: show CRITICAL only, but keep critical & high counts in title
        filtered = [f for f in findings if f.get("severity") == "critical"]
        title = "🔍 CRITICAL FINDINGS"
        title_color = "red"

    recent = sorted(filtered, key=lambda x: x.get("id", 0), reverse=True)[
        :3
    ]  # Limit to top 3

    lines = []
    lines.append("")

    # Title with counts - ALWAYS show both critical and high counts
    lines.append(
        click.style(
            f"{title} (Critical: {critical_count} | High: {high_count})",
            bold=True,
            fg=title_color,
        )
    )

    lines.append(DesignSystem.separator())
    lines.append("")  # Add blank line after separator

    if not recent:
        if severity_filter:
            lines.append(f"No {severity_filter} findings")
        else:
            lines.append("No critical findings")
    else:
        # Create Rich Table
        table = DesignSystem.create_table()
        table.add_column("ID", width=6)
        table.add_column("Severity", width=10)
        table.add_column("Host", width=18)
        table.add_column("Tool", width=14)
        table.add_column("Finding", width=46)

        # Add rows
        for finding in recent:
            fid = str(finding.get("id", "?"))
            severity = finding.get("severity", "info")
            host_ip = finding.get("ip_address", "N/A") or "N/A"
            tool = finding.get("tool", "unknown") or "unknown"
            title = finding.get("title") or "No title"

            # Severity color mapping
            sev_colors = {
                "critical": "red bold",
                "high": "red",
                "medium": "yellow",
                "low": "blue",
                "info": "dim",
            }
            sev_style = sev_colors.get(severity, "white")

            # Add row with severity colored
            table.add_row(
                fid,
                f"[{sev_style}]{severity.upper()}[/{sev_style}]",
                host_ip,
                tool,
                title,
            )

        # Render to lines
        lines.extend(_render_table_to_lines(table))

        # Add footer spacing
        lines.append("")

    return lines


def render_top_ports(engagement_id: int, width: int):
    """Render most commonly discovered open ports with host IPs."""
    hm = HostManager()
    all_hosts = hm.list_hosts(engagement_id)

    # Track ports and which hosts have them
    port_data = {}  # key: "port/service" -> value: list of host IPs
    for host in all_hosts:
        host_ip = host.get("ip_address", "unknown")
        services = hm.get_host_services(host.get("id"))
        if services:
            for svc in services:
                port = svc.get("port")
                service_name = svc.get("service_name", "unknown")
                if port:
                    key = f"{port}/{service_name}"
                    if key not in port_data:
                        port_data[key] = []
                    port_data[key].append(host_ip)

    # Sort by host count and take top 10
    top_ports = sorted(port_data.items(), key=lambda x: len(x[1]), reverse=True)[
        :10
    ]  # Increased from 5 to 10

    lines = []
    lines.extend(DesignSystem.section_header("🔌", "TOP OPEN PORTS"))

    if not top_ports:
        lines.append("No ports discovered yet")
    else:
        # Create Rich Table
        table = DesignSystem.create_table()
        table.add_column("Port/Service", width=22)
        table.add_column("Count", justify="right", width=8)
        table.add_column("Hosts", width=66)

        # Add rows
        for port_service, host_ips in top_ports:
            count = len(host_ips)

            # Smart truncation: show first 4 IPs, then "+X more"
            if count <= 4:
                ip_list = ", ".join(host_ips)
            else:
                shown = host_ips[:4]
                remaining = count - 4
                ip_list = ", ".join(shown) + f" +{remaining} more"

            table.add_row(port_service, str(count), ip_list)

        # Render to lines
        lines.extend(_render_table_to_lines(table))

    return lines


def render_recent_findings(engagement_id: int, width: int):
    """Render recent findings/alerts."""
    fm = FindingsManager()
    findings = fm.list_findings(engagement_id)

    # Get most recent findings (by ID desc)
    recent = sorted(findings, key=lambda x: x.get("id", 0), reverse=True)[:5]

    lines = []
    lines.append("")
    lines.append(click.style("🔍 RECENT FINDINGS", bold=True, fg="red"))
    lines.append(DesignSystem.separator())

    if not recent:
        lines.append("No findings yet")
    else:
        for finding in recent:
            fid = finding.get("id", "?")
            severity = finding.get("severity", "info")
            title = (finding.get("title") or "No title")[:50]

            # Color code severity
            sev_colors = {
                "critical": "red",
                "high": "red",
                "medium": "yellow",
                "low": "blue",
                "info": "white",
            }
            sev_str = click.style(
                severity[:4].upper(), fg=sev_colors.get(severity, "white")
            )

            finding_line = f"  [{fid:>3}] {sev_str} {title}"
            lines.append(finding_line)

    return lines


def render_endpoints_and_redirects(engagement_id: int, width: int):
    """Render recent endpoints and HTTP redirects with suspicious path highlighting."""
    from urllib.parse import urlparse

    from souleyez.storage.hosts import HostManager
    from souleyez.storage.osint import OsintManager
    from souleyez.storage.web_paths import WebPathsManager

    wpm = WebPathsManager()
    hm = HostManager()
    om = OsintManager()

    def is_endpoint(url):
        """Check if URL has an actual endpoint/path."""
        try:
            parsed = urlparse(url)
            path = parsed.path.rstrip("/")
            # Has path or query parameters = endpoint
            return bool(path and path != "") or bool(parsed.query)
        except Exception:
            return False

    # Get redirects from web_paths (3xx status codes with redirect target)
    all_paths = wpm.list_web_paths(engagement_id=engagement_id)
    redirects = [
        p
        for p in all_paths
        if p.get("redirect") and str(p.get("status_code", "")).startswith("3")
    ]

    # Get endpoints from OSINT URLs
    osint_urls = om.list_osint_data(engagement_id, data_type="url")
    endpoints = [u for u in osint_urls if is_endpoint(u.get("value", ""))]

    # Combine both datasets into unified format
    combined_items = []

    # Add redirects
    for r in redirects:
        combined_items.append(
            {
                "id": r.get("id"),
                "type": "Redirect",
                "status": str(r.get("status_code", "?")),
                "url": r.get("url", ""),
                "target": r.get("redirect", ""),
                "host_id": r.get("host_id"),
                "sort_id": r.get("id", 0),
            }
        )

    # Add endpoints
    for e in endpoints:
        combined_items.append(
            {
                "id": e.get("id"),
                "type": "Endpoint",
                "status": "",
                "url": e.get("value", ""),
                "target": "",
                "host_id": None,  # OSINT URLs don't have host_id
                "sort_id": e.get("id", 0),
            }
        )

    # Sort by ID descending (most recent first), limit to 10
    recent_items = sorted(combined_items, key=lambda x: x["sort_id"], reverse=True)[:10]

    # Suspicious keywords to highlight
    suspicious_paths = [
        "admin",
        "login",
        "wp-admin",
        "phpmyadmin",
        "config",
        "backup",
        "db",
        "database",
        "sql",
        "upload",
        "uploads",
        "shell",
        "cmd",
        "console",
        "manager",
        "private",
        "secret",
        "hidden",
        ".git",
        ".env",
        "phpinfo",
        "info.php",
        "test",
        "debug",
        "api",
        "swagger",
        "auth",
        "password",
        "passwd",
        "user",
    ]

    lines = []
    lines.append("")
    lines.append(click.style("🌐 ENDPOINTS & REDIRECTS", bold=True, fg="yellow"))
    lines.append(DesignSystem.separator())

    if not recent_items:
        lines.append("  No endpoints or redirects discovered yet")
        return lines

    # Table width: 120 chars total (removed Target column)
    # Columns: ID=6, Type=10, Status=8, URL=80, Host=12
    id_width = 6
    type_width = 10
    status_width = 8
    url_width = 80
    host_width = 12

    lines.append(
        "  ┌"
        + "─" * id_width
        + "┬"
        + "─" * type_width
        + "┬"
        + "─" * status_width
        + "┬"
        + "─" * url_width
        + "┬"
        + "─" * host_width
        + "┐"
    )
    header = f"  │ {'ID':<{id_width - 2}} │ {'Type':<{type_width - 2}} │ {'Status':<{status_width - 2}} │ {'URL':<{url_width - 2}} │ {'Host':<{host_width - 2}} │"
    lines.append(click.style(header, bold=True))
    lines.append(
        "  ├"
        + "─" * id_width
        + "┼"
        + "─" * type_width
        + "┼"
        + "─" * status_width
        + "┼"
        + "─" * url_width
        + "┼"
        + "─" * host_width
        + "┤"
    )

    for item in recent_items:
        item_id = str(item["id"])
        item_type = item["type"]
        status = item["status"]
        url = item["url"]
        target = item["target"]
        host_id = item["host_id"]

        # Get host IP if available
        host_ip = ""
        if host_id:
            host_info = next(
                (h for h in hm.list_hosts(engagement_id) if h["id"] == host_id), None
            )
            if host_info:
                host_ip = host_info.get("ip_address", "")

        # For redirects, show URL → Target in single column
        if target:
            url = f"{url} → {target}"

        # Check if URL/target contains suspicious keywords
        is_suspicious = any(sus_path in url.lower() for sus_path in suspicious_paths)

        # Truncate if needed
        if len(url) > url_width - 2:
            url = url[: url_width - 5] + "..."
        if len(host_ip) > host_width - 2:
            host_ip = host_ip[: host_width - 4]

        # Build row with proper spacing
        type_text = f"{item_type:<{type_width - 2}}"
        status_text = f"{status:<{status_width - 2}}"
        url_padded = f"{url:<{url_width - 2}}"
        host_padded = f"{host_ip:<{host_width - 2}}"

        row = f"  │ {item_id:>{id_width - 2}} │ {type_text} │ {status_text} │ {url_padded} │ {host_padded} │"

        # Color code type
        if item_type == "Redirect":
            colored_type = click.style(type_text, fg="cyan")
            row = row.replace(type_text, colored_type, 1)
        else:  # Endpoint
            colored_type = click.style(type_text, fg="green")
            row = row.replace(type_text, colored_type, 1)

        # Color code status for redirects
        if status:
            if status in ("301", "308"):
                colored_status = click.style(status_text, fg="yellow")
            elif status in ("302", "303", "307"):
                colored_status = click.style(status_text, fg="cyan")
            else:
                colored_status = status_text
            row = row.replace(status_text, colored_status, 1)

        # Highlight suspicious paths in RED
        if is_suspicious:
            colored_url = click.style(url_padded, fg="red", bold=True)
            row = row.replace(url_padded, colored_url, 1)

        lines.append(row)

    lines.append(
        "  └"
        + "─" * id_width
        + "┴"
        + "─" * type_width
        + "┴"
        + "─" * status_width
        + "┴"
        + "─" * url_width
        + "┴"
        + "─" * host_width
        + "┘"
    )

    return lines


def render_progress_and_discoveries(engagement_id: int, width: int):
    """Render combined progress tracking and data discoveries - REMOVED PER USER REQUEST."""
    # This section has been removed from the dashboard
    # Recent Activity and Data Discoveries are no longer displayed
    return []


def render_identified_users(engagement_id: int, width: int):
    """Render identified users and credentials from all scans."""
    cm = CredentialsManager()

    # Get actual credentials from CredentialsManager
    credentials = cm.list_credentials(engagement_id, decrypt=False)

    all_lines = []

    # ===== DISCOVERED CREDENTIALS TABLE =====
    if credentials:
        lines = []
        lines.append("")
        lines.append(click.style("🔐 DISCOVERED CREDENTIALS", bold=True, fg="green"))
        lines.append(DesignSystem.separator())

        # Fixed table width for consistency - 102 chars total width
        # Table structure: "  ┌──┬──┬──┬──┐" means 2 spaces + 5 borders = 7 chars overhead
        # Content area = 102 - 7 = 95 chars for columns
        host_width = 18
        service_width = 14
        user_width = 22
        pass_width = 95 - host_width - service_width - user_width  # 41

        # Top border
        lines.append(
            "  ┌"
            + "─" * host_width
            + "┬"
            + "─" * service_width
            + "┬"
            + "─" * user_width
            + "┬"
            + "─" * pass_width
            + "┐"
        )

        # Table header
        header = f"  │ {'Host':<{host_width - 2}} │ {'Service':<{service_width - 2}} │ {'Username':<{user_width - 2}} │ {'Password':<{pass_width - 2}} │"
        lines.append(click.style(header, bold=True))

        # Header separator
        lines.append(
            "  ├"
            + "─" * host_width
            + "┼"
            + "─" * service_width
            + "┼"
            + "─" * user_width
            + "┼"
            + "─" * pass_width
            + "┤"
        )

        # Show up to 10 credentials
        for cred in credentials[:10]:
            host_ip = cred.get("ip_address", "N/A")
            service = cred.get("service", "unknown")
            username = mask_credential(cred.get("username", "?"))
            password = mask_credential(cred.get("password", "?"))

            # Handle None values
            if host_ip is None:
                host_ip = "N/A"
            if service is None:
                service = "unknown"

            # Truncate if needed
            if len(host_ip) > host_width - 2:
                host_ip = host_ip[: host_width - 5] + "..."
            if len(service) > service_width - 2:
                service = service[: service_width - 5] + "..."
            if len(username) > user_width - 2:
                username = username[: user_width - 5] + "..."
            if len(password) > pass_width - 2:
                password = password[: pass_width - 5] + "..."

            status = cred.get("status", "untested")
            pass_color = "green" if status == "valid" else "cyan"

            # Build line
            password_display = password if password and password != "?" else ""
            cred_line = f"  │ {host_ip:<{host_width - 2}} │ {service:<{service_width - 2}} │ {username:<{user_width - 2}} │ "
            if password_display:
                cred_line += click.style(
                    f"{password_display:<{pass_width - 2}}", fg=pass_color
                )
            else:
                cred_line += f"{'':<{pass_width - 2}}"
            cred_line += " │"
            lines.append(cred_line)

        # Bottom border
        lines.append(
            "  └"
            + "─" * host_width
            + "┴"
            + "─" * service_width
            + "┴"
            + "─" * user_width
            + "┴"
            + "─" * pass_width
            + "┘"
        )

        all_lines.extend(lines)

    return all_lines


def render_live_log(job_id: Optional[int], width: int, height: int):
    """Render live log output from a running job, or summary if completed."""
    if not job_id:
        return []

    job = get_job(job_id)
    if not job:
        return []

    # Ensure job is a dict (safety check with detailed debugging)
    if not isinstance(job, dict):
        import logging

        logging.error(f"render_live_log: job is {type(job).__name__}, value: {job}")
        return [
            click.style(
                f"Error: Invalid job data for job #{job_id} (got {type(job).__name__})",
                fg="red",
            )
        ]

    status = job.get("status", "unknown")
    tool = job.get("tool", "unknown")

    lines = []
    lines.append("")

    # If job is completed, show summary instead of raw log
    if status in ("done", "no_results", "warning", "error"):
        # Determine color based on status
        if status in ("done", "no_results"):
            title_color = "green"
        elif status == "warning":
            title_color = "yellow"
        else:
            title_color = "red"
        lines.append(
            click.style(f"📋 JOB #{job_id} SUMMARY - {tool}", bold=True, fg=title_color)
        )
        lines.append(DesignSystem.separator())

        if status == "error":
            lines.append(click.style("✗ Job failed", fg="red", bold=True))
        else:
            lines.append(
                click.style("✓ Scan completed successfully", fg="green", bold=True)
            )

        lines.append("")

        # Try to get parsed results summary
        try:
            # First check if parse_result is already stored in the job
            result = job.get("parse_result")

            # If not stored, try to parse it now (for old jobs)
            if not result:
                from souleyez.engine.result_handler import handle_job_result

                result = handle_job_result(job)

            if result and "error" not in result:
                lines.append(click.style("Results:", bold=True))

                # Show tool-specific summary
                if tool == "nmap":
                    is_discovery = result.get("is_discovery", False)
                    is_full_scan = result.get("is_full_scan", False)
                    host_details = result.get("host_details", [])
                    findings_added = result.get("findings_added", 0)
                    hosts_added = result.get("hosts_added", 0)
                    services_added = result.get("services_added", 0)

                    # Check if this is a vulnerability scan (has findings)
                    if findings_added > 0:
                        # Vulnerability scan - prioritize showing findings
                        vuln_word = (
                            "vulnerability"
                            if findings_added == 1
                            else "vulnerabilities"
                        )
                        lines.append(
                            click.style(
                                f"  🔴 {findings_added} {vuln_word} detected!",
                                fg="red",
                                bold=True,
                            )
                        )
                        host_word = "host" if hosts_added == 1 else "hosts"
                        svc_word = "service" if services_added == 1 else "services"
                        lines.append(f"  • {hosts_added} {host_word} scanned")
                        lines.append(f"  • {services_added} {svc_word} analyzed")
                        lines.append("")
                        lines.append(
                            "  View findings in Intelligence Hub or Findings menu"
                        )
                    elif is_discovery:
                        # Discovery scan - just show count
                        host_word = "host" if hosts_added == 1 else "hosts"
                        lines.append(f"  • {hosts_added} live {host_word} found")
                    elif is_full_scan:
                        # Full scan - show detailed info
                        if host_details:
                            lines.append("  Hosts discovered:")
                            for host in host_details:
                                ip = host.get("ip", "unknown")
                                hostname = host.get("hostname", "")
                                os_info = host.get("os", "")
                                service_count = host.get("service_count", 0)
                                top_ports = host.get("top_ports", [])

                                # Header: IP (hostname)
                                if hostname:
                                    lines.append(f"    • {ip} ({hostname})")
                                else:
                                    lines.append(f"    • {ip}")

                                # OS info
                                if os_info:
                                    lines.append(f"      OS: {os_info}")

                                # Service count
                                port_word = "port" if service_count == 1 else "ports"
                                lines.append(
                                    f"      Services: {service_count} open {port_word}"
                                )

                                # Top ports
                                if top_ports:
                                    lines.append(
                                        f"      Top ports: {', '.join(top_ports)}"
                                    )

                                lines.append("")  # Blank line between hosts
                        else:
                            host_word = "host" if hosts_added == 1 else "hosts"
                            lines.append(
                                f"  • {hosts_added} live {host_word} found (no services)"
                            )
                    else:
                        # Regular port scan - show each host with service count
                        if host_details:
                            lines.append("  Hosts discovered:")
                            for host in host_details:
                                ip = host.get("ip", "unknown")
                                hostname = host.get("hostname", "")
                                service_count = host.get("service_count", 0)
                                svc_word = (
                                    "service" if service_count == 1 else "services"
                                )

                                # Format: IP (hostname) - N services
                                if hostname:
                                    lines.append(
                                        f"    • {ip} ({hostname}) - {service_count} {svc_word}"
                                    )
                                else:
                                    lines.append(
                                        f"    • {ip} - {service_count} {svc_word}"
                                    )
                        else:
                            host_word = "host" if hosts_added == 1 else "hosts"
                            lines.append(
                                f"  • {hosts_added} live {host_word} found (no services)"
                            )

                elif tool == "msf_auxiliary":
                    host = result.get("host", "N/A")
                    services_added = result.get("services_added", 0)
                    findings_added = result.get("findings_added", 0)
                    lines.append(f"  • Target: {host}")
                    if services_added > 0:
                        svc_word = "service" if services_added == 1 else "services"
                        lines.append(f"  • {services_added} {svc_word} identified")
                    if findings_added > 0:
                        find_word = "finding" if findings_added == 1 else "findings"
                        lines.append(
                            click.style(
                                f"  • {findings_added} {find_word} added",
                                fg="red",
                                bold=True,
                            )
                        )

                elif tool == "gobuster":
                    paths_found = result.get("paths_found") or result.get(
                        "total_paths", 0
                    )
                    redirects_found = result.get("redirects_found", 0)
                    path_word = "path" if paths_found == 1 else "paths"
                    lines.append(f"  • {paths_found} web {path_word} discovered")
                    if redirects_found > 0:
                        redir_word = "redirect" if redirects_found == 1 else "redirects"
                        lines.append(f"  • {redirects_found} {redir_word} found")

                elif tool == "smbmap":
                    shares_added = result.get("shares_added", 0)
                    files_added = result.get("files_added", 0)
                    findings_added = result.get("findings_added", 0)
                    auth_status = result.get("status", "Unknown")
                    lines.append(f"  • Target: {result.get('host', 'N/A')}")
                    lines.append(f"  • Authentication: {auth_status}")
                    share_word = "share" if shares_added == 1 else "shares"
                    lines.append(f"  • {shares_added} SMB {share_word} discovered")
                    if files_added > 0:
                        file_word = "file" if files_added == 1 else "files"
                        lines.append(f"  • {files_added} {file_word} enumerated")
                    if findings_added > 0:
                        find_word = "finding" if findings_added == 1 else "findings"
                        lines.append(
                            click.style(
                                f"  • {findings_added} security {find_word} detected",
                                fg="red",
                                bold=True,
                            )
                        )

                elif tool == "http_fingerprint":
                    # Show fingerprint summary
                    server = result.get("server")
                    managed_hosting = result.get("managed_hosting")
                    waf = result.get("waf", [])
                    cdn = result.get("cdn", [])
                    technologies = result.get("technologies", [])
                    redirect_url = result.get("redirect_url")
                    status_code = result.get("status_code")

                    if status_code:
                        lines.append(f"  • HTTP Status: {status_code}")
                    if redirect_url:
                        lines.append(f"  • Redirects to: {redirect_url}")
                    if server:
                        lines.append(f"  • Server: {server}")
                    if managed_hosting:
                        lines.append(
                            click.style(
                                f"  • Managed Hosting: {managed_hosting}", fg="yellow"
                            )
                        )
                    if waf:
                        lines.append(
                            click.style(
                                f"  • WAF Detected: {', '.join(waf)}",
                                fg="red",
                                bold=True,
                            )
                        )
                    if cdn:
                        lines.append(f"  • CDN: {', '.join(cdn)}")
                    if technologies:
                        lines.append(f"  • Technologies: {', '.join(technologies[:5])}")

                else:
                    # Generic result display
                    for key, value in result.items():
                        if key not in ("tool", "error"):
                            lines.append(f"  • {key}: {value}")

            elif result and "error" in result:
                lines.append(
                    click.style(f"✗ Parse error: {result['error']}", fg="yellow")
                )

        except Exception as e:
            lines.append(click.style(f"Could not parse results: {e}", fg="yellow"))

        lines.append("")
        lines.append(f"View full log: souleyez jobs show {job_id}")

    else:
        # Job is still running - show live log
        lines.append(
            click.style(
                f"📡 LIVE LOG - Job #{job_id} ({tool})", bold=True, fg="magenta"
            )
        )
        lines.append(DesignSystem.separator())

        # Add rotating AI quote for running jobs
        from souleyez.ui.ai_quotes import get_random_quote

        quote = get_random_quote()
        lines.append(click.style(f"🤖 {quote}", fg="bright_black"))
        lines.append("")

        # Double-check job is still a dict (defensive)
        if not isinstance(job, dict):
            lines.append(
                click.style(
                    f"Error: Job data corrupted (is {type(job).__name__})", fg="red"
                )
            )
            return lines

        log_path = job.get("log")
        if log_path and os.path.exists(log_path):
            try:
                # Optimization: Read only the tail of large log files
                # This prevents lag when sqlmap/other tools generate huge logs
                available = max(20, height - 23)

                file_size = os.path.getsize(log_path)
                # Estimate: average line is ~100 bytes, read 2x what we need for safety
                bytes_to_read = min(file_size, available * 200)

                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    if file_size > bytes_to_read:
                        # Large file - seek to near the end
                        f.seek(file_size - bytes_to_read)
                        # Skip partial first line after seek
                        f.readline()
                        content = f.read()
                    else:
                        # Small file - read all
                        content = f.read()

                # Show last N lines (fit to screen)
                log_lines = content.split("\n")

                if len(log_lines) > available:
                    log_lines = log_lines[-available:]

                # Format JSON logs for readability
                formatted_lines = format_log_stream(log_lines, max_lines=available)

                # Track if we're in a fingerprint block to skip
                in_fingerprint_block = False

                for line in formatted_lines:
                    # Filter out noisy nmap TCP/IP fingerprint data
                    if "TCP/IP fingerprint:" in line:
                        in_fingerprint_block = True
                        continue

                    # Skip lines that are part of fingerprint block (start with OS:, SEQ:, etc.)
                    if in_fingerprint_block:
                        # Fingerprint lines typically start with known prefixes
                        if line.startswith(
                            (
                                "OS:",
                                "SEQ:",
                                "OPS:",
                                "WIN:",
                                "ECN:",
                                "T1:",
                                "T2:",
                                "T3:",
                                "T4:",
                                "T5:",
                                "T6:",
                                "T7:",
                                "U1:",
                                "IE:",
                            )
                        ):
                            continue
                        else:
                            # Empty line or new section means fingerprint block ended
                            in_fingerprint_block = False

                    # Truncate long lines
                    if len(line) > width:
                        line = line[: width - 3] + "..."
                    lines.append(line)
            except Exception as e:
                lines.append(f"Error reading log: {e}")
        else:
            lines.append("No log available")

    return lines


def render_dashboard(
    engagement_id: int,
    engagement_name: str,
    state: "DashboardState",
    follow_job_id: Optional[int] = None,
    refresh_interval: int = 5,
):
    """Render complete dashboard."""
    width, height = get_terminal_size()

    clear_screen()

    # Build all panels
    output = []

    # Header with status bar and quick actions
    output.extend(render_header(engagement_name, engagement_id, width, state))

    # Tutorial hint (if tutorial is active)
    tutorial_hint_lines = render_tutorial_hint(width)
    if tutorial_hint_lines:
        output.extend(tutorial_hint_lines)

    # Intelligence Summary (NEW - Command Center mode)
    if state.show_intelligence_summary and not state.detailed_view:
        try:
            import sqlite3

            intel_lines = render_intelligence_summary(
                engagement_id, width, expanded=state.intelligence_focused
            )
            if intel_lines and len(intel_lines) > 3:
                output.extend(intel_lines)
        except sqlite3.OperationalError:
            # Database locked - show fallback message
            output.extend(DesignSystem.section_header("🎯", "INTELLIGENCE AT A GLANCE"))
            output.append("")
            output.append(
                click.style(
                    "⏱️  Intelligence analysis in progress (database busy)", fg="yellow"
                )
            )
            output.append(
                click.style(
                    "   Dashboard will refresh automatically", fg="bright_black"
                )
            )
            output.append("")
        except Exception as e:
            # Intelligence rendering failed - show fallback
            import logging

            logging.error(f"Intelligence rendering error: {e}", exc_info=True)
            output.extend(DesignSystem.section_header("🎯", "INTELLIGENCE AT A GLANCE"))
            output.append("")
            output.append(
                click.style(
                    "⚠️  Intelligence analysis temporarily unavailable", fg="yellow"
                )
            )
            output.append(click.style(f"   ({str(e)[:60]}...)", fg="bright_black"))
            output.append("")

    # If Intelligence is focused, minimize other sections
    if state.intelligence_focused:
        # Active jobs at bottom
        output.extend(render_active_jobs(width, engagement_id))

        # Skip other sections when Intelligence is focused
    else:
        # Normal rendering - Legacy sections (only in Detailed View mode or if minimal mode)
        if state.detailed_view or state.minimal_mode:
            # Tool metrics (show if not minimal mode)
            if not state.minimal_mode:
                new_tool_lines = render_new_tool_metrics(engagement_id, width)
                if new_tool_lines and len(new_tool_lines) > 3:
                    output.extend(new_tool_lines)

            # Conditional sections based on state
            if state.show_hosts:
                host_lines = render_recent_hosts(engagement_id, width)
                if host_lines and len(host_lines) > 3:
                    output.extend(host_lines)

            # Recent redirects
            if state.show_redirects:
                redirect_lines = render_endpoints_and_redirects(engagement_id, width)
                if redirect_lines and len(redirect_lines) > 3:
                    output.extend(redirect_lines)

            # Credentials
            if state.show_credentials:
                cred_lines = render_identified_users(engagement_id, width)
                if cred_lines and len(cred_lines) > 3:
                    output.extend(cred_lines)

        # Live log - auto-follow most recent running job if not explicitly following
        if not follow_job_id:
            jobs = list_jobs(limit=20)
            running_jobs = [j for j in jobs if j.get("status") == "running"]
            if running_jobs:
                follow_job_id = running_jobs[0].get("id")

        # Active jobs (show at bottom - current running jobs)
        output.extend(render_active_jobs(width, engagement_id))

        # Job summary/live log (show at very bottom after active jobs)
        if follow_job_id:
            output.extend(render_live_log(follow_job_id, width, height))

    # Footer
    output.append("")
    output.append(DesignSystem.separator())
    mode_text = (
        "[DETAILED VIEW] "
        if state.detailed_view
        else "[COMMAND CENTER] " if not state.minimal_mode else "[MINIMAL MODE] "
    )
    if follow_job_id:
        footer_text = (
            f"{mode_text}Following Job #{follow_job_id} | Refresh: {refresh_interval}s"
        )
    else:
        footer_text = f"{mode_text}Auto-refresh: {refresh_interval}s"
    output.append(footer_text.center(get_dynamic_width()))

    # Print all lines
    for line in output:
        click.echo(line)


def run_dashboard(follow_job_id: Optional[int] = None, refresh_interval: int = 10):
    """Run the live dashboard with auto-refresh and interactive menu."""
    em = EngagementManager()
    current_ws = em.get_current()

    if not current_ws:
        click.echo(
            click.style(
                "✗ No workspace selected! Use 'souleyez workspace use <name>'", fg="red"
            )
        )
        return

    engagement_id = current_ws["id"]
    engagement_name = current_ws["name"]

    # Initialize dashboard state
    state = DashboardState()

    click.echo(
        click.style(
            f"\nStarting live dashboard for workspace '{engagement_name}'...",
            fg="green",
        )
    )

    # Check if tutorial is active
    tutorial_state = get_tutorial_state()
    if tutorial_state.is_active():
        click.echo(
            click.style(
                "📚 Tutorial mode active - follow the hints!", fg="yellow", bold=True
            )
        )
    else:
        click.echo(
            click.style(
                "Hotkeys: [?] Help  [m] Menu  [i] Intel  [j] Jobs  [d] Detect  [q] Quit",
                fg="yellow",
            )
        )
    click.echo()
    time.sleep(1)

    last_followed_job_id = None
    job_completed = False
    last_seen_job_id = None
    auto_follow_job_id = follow_job_id

    try:
        while True:
            # Check if engagement changed (user may have switched from another view)
            current_check = em.get_current()
            if current_check and current_check["id"] != engagement_id:
                # Engagement changed - update local variables
                engagement_id = current_check["id"]
                engagement_name = current_check["name"]
                # Clear any caches related to old engagement
                _header_cache.clear()

            # Check if there are any active jobs
            from souleyez.engine.background import get_active_jobs

            active_jobs = get_active_jobs()

            # Detect new jobs
            if active_jobs:
                latest_job = active_jobs[0]
                latest_job_id = latest_job.get("id")
                if latest_job_id != last_seen_job_id:
                    if latest_job.get("status") in ("queued", "running"):
                        if not follow_job_id:
                            auto_follow_job_id = latest_job_id
                            last_followed_job_id = latest_job_id
                    last_seen_job_id = latest_job_id

            # Render dashboard with current state
            if not active_jobs and not auto_follow_job_id:
                render_dashboard(
                    engagement_id, engagement_name, state, None, refresh_interval
                )
                click.echo()
                # Tutorial: show tutorial-specific message if active
                if tutorial_state.is_active():
                    click.echo(
                        click.style(
                            "  📚 Tutorial mode - follow the hints above!",
                            fg="yellow",
                            bold=True,
                        )
                    )
                else:
                    click.echo(
                        click.style(
                            "  ℹ️  No active scans running. Dashboard is in static mode.",
                            fg="yellow",
                            bold=True,
                        )
                    )
                    click.echo(
                        click.style(
                            "  💡 Launch a scan to enable auto-refresh monitoring.",
                            fg="cyan",
                        )
                    )
                click.echo()

                user_input = _wait_for_input(300)  # 5 minutes instead of 30 seconds
                # Tutorial: handle Enter key (empty string) for DASHBOARD_INTRO
                if user_input is not None and tutorial_state.is_step(
                    TutorialStep.DASHBOARD_INTRO
                ):
                    tutorial_state.set_step(TutorialStep.VIEW_JOBS)
                    clear_screen()
                    continue
                if user_input:
                    if user_input.lower()[:1] == "q":
                        break
                    elif user_input.lower() == "i":
                        state.intelligence_focused = not state.intelligence_focused
                        clear_screen()
                    elif user_input.lower() == "e":
                        from souleyez.ui.evidence_vault import view_evidence_vault

                        view_evidence_vault(engagement_id)
                        clear_screen()
                    elif user_input.lower() == "r":
                        from souleyez.ui.interactive import manage_reports_menu

                        manage_reports_menu()
                        clear_screen()
                    elif user_input.lower() == "n":
                        state.toggle_minimal()
                        clear_screen()
                    elif user_input.lower() == "t":
                        _show_toggle_menu(state)
                        clear_screen()
                    elif user_input.lower() == "x":
                        _execute_ai_recommendation(engagement_id)
                        clear_screen()
                    elif user_input.lower() == "m":
                        result = _show_dashboard_menu(engagement_id)
                        if result == "quit":
                            break  # Exit dashboard, return to main menu
                        elif result == "ai_execute":
                            _execute_ai_recommendation(engagement_id)
                        clear_screen()
                    elif user_input.lower()[:1] == "h":
                        # Tutorial: advance state when user views hosts
                        if tutorial_state.is_step(TutorialStep.VIEW_HOSTS):
                            tutorial_state.set_step(TutorialStep.IN_HOSTS_VIEW)
                        from souleyez.ui.interactive import view_hosts

                        view_hosts(engagement_id)
                        # Tutorial: after hosts view, go to job details step
                        if tutorial_state.is_step(TutorialStep.IN_HOSTS_VIEW):
                            tutorial_state.set_step(TutorialStep.VIEW_JOB_DETAILS)
                        clear_screen()
                    elif user_input.lower() == "f":
                        from souleyez.ui.interactive import view_findings

                        view_findings(engagement_id)
                        clear_screen()
                    elif user_input.lower() in [
                        "u",
                        "c",
                    ]:  # 'c' for credentials, 'u' for users
                        from souleyez.ui.interactive import view_credentials

                        view_credentials(engagement_id)
                        clear_screen()
                    elif user_input.lower()[:1] == "o":
                        # Tutorial: advance state when user views OSINT
                        if tutorial_state.is_step(TutorialStep.VIEW_OSINT):
                            tutorial_state.set_step(TutorialStep.IN_OSINT_VIEW)
                        from souleyez.ui.interactive import view_osint

                        view_osint(engagement_id)
                        # Tutorial: after OSINT view, hint to view hosts
                        if tutorial_state.is_step(TutorialStep.IN_OSINT_VIEW):
                            tutorial_state.set_step(TutorialStep.VIEW_HOSTS)
                        clear_screen()
                    elif user_input.lower()[:1] == "j":
                        # Tutorial: advance state when user views jobs
                        if tutorial_state.is_step(TutorialStep.VIEW_JOBS):
                            tutorial_state.set_step(TutorialStep.IN_JOB_QUEUE)
                        elif tutorial_state.is_step(TutorialStep.VIEW_JOB_DETAILS):
                            tutorial_state.set_step(TutorialStep.IN_JOB_DETAILS)
                        from souleyez.ui.interactive import view_jobs_menu

                        view_jobs_menu()
                        # Tutorial: after job queue, advance to next step
                        if tutorial_state.is_step(TutorialStep.IN_JOB_QUEUE):
                            tutorial_state.set_step(TutorialStep.VIEW_OSINT)
                        elif tutorial_state.is_step(TutorialStep.IN_JOB_DETAILS):
                            tutorial_state.complete()
                            break  # Exit dashboard to show completion screen
                        clear_screen()
                    elif user_input.lower() == "p":
                        from souleyez.ui.pending_chains_view import (
                            manage_pending_chains,
                        )

                        manage_pending_chains(engagement_id)
                        clear_screen()
                    elif user_input.lower() == "d":
                        from souleyez.ui.interactive import _detection_validation_menu

                        _detection_validation_menu(engagement_id)
                        clear_screen()
                    elif user_input.lower() == "a":
                        _quick_toggle_ai_provider()
                        clear_screen()
                    elif user_input in ["1", "2", "3"]:
                        _execute_numbered_action(engagement_id, int(user_input))
                        clear_screen()
                    elif user_input.lower() == "s":
                        from souleyez.ui.interactive import view_services

                        view_services(engagement_id)
                        clear_screen()
                    elif user_input.lower() in ["g", "?"]:
                        _show_help_menu()
                        clear_screen()
                continue

            # Track which job we're following
            current_follow_id = auto_follow_job_id

            # Check if currently followed job has completed
            if current_follow_id:
                followed_job = get_job(current_follow_id)
                if followed_job and followed_job.get("status") in (
                    "done",
                    "no_results",
                    "warning",
                    "error",
                ):
                    # Job completed - check if there are other running jobs to follow
                    running_jobs = [
                        j for j in active_jobs if j.get("status") == "running"
                    ]
                    if running_jobs:
                        # Switch to the next running job
                        current_follow_id = running_jobs[0].get("id")
                        auto_follow_job_id = current_follow_id
                        last_followed_job_id = current_follow_id
                    else:
                        # No running jobs - mark as completed for prompt
                        if not job_completed:
                            job_completed = True

            if not current_follow_id:
                running_jobs = [j for j in active_jobs if j.get("status") == "running"]
                if running_jobs:
                    current_follow_id = running_jobs[0].get("id")
                    last_followed_job_id = current_follow_id
                elif last_followed_job_id:
                    current_follow_id = last_followed_job_id
                    if not job_completed:
                        completed_job = get_job(last_followed_job_id)
                        if completed_job and completed_job.get("status") in (
                            "done",
                            "no_results",
                            "warning",
                            "error",
                        ):
                            job_completed = True

            render_dashboard(
                engagement_id,
                engagement_name,
                state,
                current_follow_id,
                refresh_interval,
            )

            if job_completed:
                click.echo()
                click.echo(
                    click.style(
                        "Job completed! Output preserved above.", fg="green", bold=True
                    )
                )
                # Tutorial: adjust prompt if tutorial is active
                if tutorial_state.is_active():
                    click.echo(
                        click.style(
                            "Press ENTER to continue tutorial...",
                            fg="yellow",
                            bold=True,
                        )
                    )
                else:
                    click.echo(
                        "Press ENTER to clear and continue monitoring, or Ctrl+C to exit..."
                    )
                try:
                    input()
                    # Tutorial: advance state when clearing job completion
                    if tutorial_state.is_step(TutorialStep.DASHBOARD_INTRO):
                        tutorial_state.set_step(TutorialStep.VIEW_JOBS)
                    job_completed = False
                    last_followed_job_id = None
                    auto_follow_job_id = None
                    clear_screen()
                except KeyboardInterrupt:
                    raise
            else:
                user_input = _wait_for_input(refresh_interval)
                # Tutorial: handle Enter key (empty string) for DASHBOARD_INTRO
                if user_input is not None and tutorial_state.is_step(
                    TutorialStep.DASHBOARD_INTRO
                ):
                    tutorial_state.set_step(TutorialStep.VIEW_JOBS)
                    clear_screen()
                    continue
                if user_input:
                    if user_input.lower()[:1] == "q":
                        break
                    elif user_input.lower() == "i":
                        state.intelligence_focused = not state.intelligence_focused
                        clear_screen()
                    elif user_input.lower() == "e":
                        from souleyez.ui.evidence_vault import view_evidence_vault

                        view_evidence_vault(engagement_id)
                        clear_screen()
                    elif user_input.lower() == "r":
                        from souleyez.ui.interactive import manage_reports_menu

                        manage_reports_menu()
                        clear_screen()
                    elif user_input.lower() == "n":
                        state.toggle_minimal()
                        clear_screen()
                    elif user_input.lower() == "t":
                        _show_toggle_menu(state)
                        clear_screen()
                    elif user_input.lower() == "x":
                        _execute_ai_recommendation(engagement_id)
                        clear_screen()
                    elif user_input.lower() == "m":
                        result = _show_dashboard_menu(engagement_id)
                        if result == "quit":
                            break  # Exit dashboard, return to main menu
                        elif result == "ai_execute":
                            _execute_ai_recommendation(engagement_id)
                        clear_screen()
                    elif user_input.lower()[:1] == "h":
                        # Tutorial: advance state when user views hosts
                        if tutorial_state.is_step(TutorialStep.VIEW_HOSTS):
                            tutorial_state.set_step(TutorialStep.IN_HOSTS_VIEW)
                        from souleyez.ui.interactive import view_hosts

                        view_hosts(engagement_id)
                        # Tutorial: after hosts view, go to job details step
                        if tutorial_state.is_step(TutorialStep.IN_HOSTS_VIEW):
                            tutorial_state.set_step(TutorialStep.VIEW_JOB_DETAILS)
                        clear_screen()
                    elif user_input.lower() == "f":
                        from souleyez.ui.interactive import view_findings

                        view_findings(engagement_id)
                        clear_screen()
                    elif user_input.lower() in [
                        "u",
                        "c",
                    ]:  # 'c' for credentials, 'u' for users
                        from souleyez.ui.interactive import view_credentials

                        view_credentials(engagement_id)
                        clear_screen()
                    elif user_input.lower()[:1] == "o":
                        # Tutorial: advance state when user views OSINT
                        if tutorial_state.is_step(TutorialStep.VIEW_OSINT):
                            tutorial_state.set_step(TutorialStep.IN_OSINT_VIEW)
                        from souleyez.ui.interactive import view_osint

                        view_osint(engagement_id)
                        # Tutorial: after OSINT view, hint to view hosts
                        if tutorial_state.is_step(TutorialStep.IN_OSINT_VIEW):
                            tutorial_state.set_step(TutorialStep.VIEW_HOSTS)
                        clear_screen()
                    elif user_input.lower()[:1] == "j":
                        # Tutorial: advance state when user views jobs
                        if tutorial_state.is_step(TutorialStep.VIEW_JOBS):
                            tutorial_state.set_step(TutorialStep.IN_JOB_QUEUE)
                        elif tutorial_state.is_step(TutorialStep.VIEW_JOB_DETAILS):
                            tutorial_state.set_step(TutorialStep.IN_JOB_DETAILS)
                        from souleyez.ui.interactive import view_jobs_menu

                        view_jobs_menu()
                        # Tutorial: after job queue, advance to next step
                        if tutorial_state.is_step(TutorialStep.IN_JOB_QUEUE):
                            tutorial_state.set_step(TutorialStep.VIEW_OSINT)
                        elif tutorial_state.is_step(TutorialStep.IN_JOB_DETAILS):
                            tutorial_state.complete()
                            break  # Exit dashboard to show completion screen
                        clear_screen()
                    elif user_input.lower() == "p":
                        from souleyez.ui.pending_chains_view import (
                            manage_pending_chains,
                        )

                        manage_pending_chains(engagement_id)
                        clear_screen()
                    elif user_input.lower() == "d":
                        from souleyez.ui.interactive import _detection_validation_menu

                        _detection_validation_menu(engagement_id)
                        clear_screen()
                    elif user_input.lower() == "a":
                        _quick_toggle_ai_provider()
                        clear_screen()
                    elif user_input in ["1", "2", "3"]:
                        _execute_numbered_action(engagement_id, int(user_input))
                        clear_screen()
                    elif user_input.lower() == "s":
                        from souleyez.ui.interactive import view_services

                        view_services(engagement_id)
                        clear_screen()
                    elif user_input.lower() in ["g", "?"]:
                        _show_help_menu()
                        clear_screen()

    except KeyboardInterrupt:
        click.echo("\n" + click.style("Dashboard stopped.", fg="green"))
        click.echo()


def _toggle_auto_chaining():
    """Toggle auto-chaining on/off with improved feedback."""
    from souleyez.auth import is_pro
    from souleyez.core.tool_chaining import ToolChaining
    from souleyez.ui.interactive import _show_upgrade_prompt

    if not is_pro():
        _show_upgrade_prompt("Auto-Chaining")
        return

    try:
        chaining = ToolChaining()

        # Toggle and get new state
        new_status = chaining.toggle_chaining()

        DesignSystem.clear_screen()
        click.echo("\n" + "=" * 70)
        click.echo(click.style("AUTO-CHAINING TOGGLE", bold=True, fg="cyan"))
        click.echo("=" * 70 + "\n")

        if new_status:
            click.echo(
                click.style("  ⚡ Auto-chaining is now ENABLED", fg="green", bold=True)
            )
            click.echo(
                "\n  Tools will automatically trigger follow-up scans based on their results."
            )
            click.echo("  Example: theHarvester → WHOIS → DNSRecon")
            click.echo()
            click.echo(
                click.style("  ℹ️  Note: ", fg="cyan", bold=True)
                + "New scans will be auto-chained. Existing scan results are unaffected."
            )
        else:
            click.echo(
                click.style("  ○ Auto-chaining is now DISABLED", fg="yellow", bold=True)
            )
            click.echo(
                "\n  Tools will run independently without triggering follow-up scans."
            )
            click.echo()
            click.echo(click.style("  ⏳ Clearing pending chains...", fg="yellow"))

            # Give user feedback that cleanup is happening
            # The disable_chaining() method has timeout protection
            click.echo(click.style("  ✓ Pending chains cleared", fg="green"))

        # Restart worker to apply changes
        click.echo()
        click.echo("  Restarting worker to apply changes...", nl=False)
        try:
            from souleyez.engine.worker_manager import restart_worker

            if restart_worker():
                click.echo(click.style(" ✓", fg="green", bold=True))
            else:
                click.echo(
                    click.style(" ✗ (worker may not have been running)", fg="yellow")
                )
        except Exception as e:
            click.echo(click.style(f" ✗ ({e})", fg="red"))

        click.echo()
        click.echo(
            click.style("  💡 TIP: ", fg="cyan", bold=True)
            + "Changes take effect immediately for new jobs."
        )
        click.echo(
            "  Press [?] in the dashboard to view the auto-chaining guide for details."
        )
        click.echo()

    except Exception as e:
        DesignSystem.clear_screen()
        click.echo("\n" + "=" * 70)
        click.echo(click.style("AUTO-CHAINING TOGGLE ERROR", bold=True, fg="red"))
        click.echo("=" * 70 + "\n")
        click.echo(click.style(f"  ✗ Failed to toggle auto-chaining: {e}", fg="red"))
        click.echo()
        click.echo(
            click.style("  This may happen if the worker is very busy.", fg="yellow")
        )
        click.echo(click.style("  Try again in a few seconds.", fg="yellow"))
        click.echo()

    click.pause("Press any key to return to dashboard...")


def _get_quick_action_count(engagement_id: int) -> int:
    """
    Get the count of available quick actions.

    Returns 0 if database is busy or any errors occur.
    """
    import sqlite3

    recommendations = []

    # Get untested services (cached)
    try:

        def _compute_attack_surface():
            from souleyez.intelligence.surface_analyzer import AttackSurfaceAnalyzer

            analyzer = AttackSurfaceAnalyzer()
            return analyzer.analyze_engagement(engagement_id)

        surface = _get_cached_value(
            f"attack_surface_{engagement_id}", _compute_attack_surface
        )

        if surface and surface.get("hosts"):
            for host in surface["hosts"][:3]:  # Top 3 hosts
                for service in host.get("services", []):
                    if service.get("status") == "not_tried":
                        recommendations.append({"type": "service"})
    except sqlite3.OperationalError as e:
        # Database locked - return 0
        return 0
    except Exception as e:
        # Any other error, skip
        pass

    # Get critical exploits (cached - this is the expensive call!)
    try:

        def _compute_exploit_suggestions():
            from souleyez.intelligence.exploit_suggestions import (
                ExploitSuggestionEngine,
            )

            suggest_engine = ExploitSuggestionEngine(use_searchsploit=False)
            return suggest_engine.generate_suggestions(engagement_id)

        suggestions = _get_cached_value(
            f"exploit_suggestions_{engagement_id}", _compute_exploit_suggestions
        )

        if suggestions and suggestions.get("hosts"):
            for host in suggestions["hosts"][:2]:  # Top 2 hosts
                for service in host.get("services", []):
                    for exploit in service.get("exploits", [])[
                        :1
                    ]:  # Top exploit per service
                        if exploit.get("severity") == "critical":
                            recommendations.append({"type": "exploit"})
    except sqlite3.OperationalError:
        # Database locked - return current count
        return len(recommendations)
    except Exception:
        # Any other error, skip
        pass

    return len(recommendations)


def _execute_numbered_action(engagement_id: int, action_num: int):
    """Execute a numbered action from Smart Recommendations."""
    DesignSystem.clear_screen()
    click.echo("\n" + "=" * 70)
    click.echo(click.style(f"EXECUTING ACTION #{action_num}", bold=True, fg="cyan"))
    click.echo("=" * 70 + "\n")

    # Get recommendations
    recommendations = []

    # Get untested services (cached)
    try:

        def _compute_attack_surface():
            from souleyez.intelligence.surface_analyzer import AttackSurfaceAnalyzer

            analyzer = AttackSurfaceAnalyzer()
            return analyzer.analyze_engagement(engagement_id)

        surface = _get_cached_value(
            f"attack_surface_{engagement_id}", _compute_attack_surface
        )

        if surface and surface.get("hosts"):
            for host in surface["hosts"][:3]:  # Top 3 hosts
                for service in host.get("services", []):
                    if service.get("status") == "not_tried":
                        port = service.get("port")
                        service_name = service.get("service")
                        ip = host.get("host")

                        recommendations.append(
                            {
                                "priority": (
                                    "CRITICAL" if host.get("score", 0) > 80 else "HIGH"
                                ),
                                "action": f"Exploit {service_name} on {ip}:{port}",
                                "target": ip,
                                "port": port,
                                "service": service_name,
                            }
                        )
    except Exception as e:
        pass

    # Get critical exploits
    try:
        from souleyez.intelligence.exploit_suggestions import ExploitSuggestionEngine

        suggest_engine = ExploitSuggestionEngine()
        suggestions = suggest_engine.generate_suggestions(engagement_id)

        if suggestions and suggestions.get("hosts"):
            for host in suggestions["hosts"][:2]:  # Top 2 hosts
                for service in host.get("services", []):
                    for exploit in service.get("exploits", [])[
                        :1
                    ]:  # Top exploit per service
                        if exploit.get("severity") == "critical":
                            title = exploit.get("title", "")
                            ip = host.get("ip")
                            msf_module = exploit.get("msf_module", "")

                            recommendations.append(
                                {
                                    "priority": "HIGH",
                                    "action": f"Test {title} on {ip}",
                                    "target": ip,
                                    "msf_module": msf_module,
                                }
                            )
    except Exception as e:
        pass

    # Sort and select action
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
    recommendations.sort(key=lambda x: priority_order.get(x["priority"], 99))

    # Show helpful message if no actions available
    if len(recommendations) == 0:
        click.echo(click.style("  No Quick Actions available", fg="yellow", bold=True))
        click.echo()
        click.echo("  Quick Actions are automatically generated based on:")
        click.echo("    • Untested services discovered in scans")
        click.echo("    • Critical exploits matching your environment")
        click.echo()
        click.echo(
            click.style("  💡 Try running a port scan to discover services!", fg="cyan")
        )
        click.pause("\nPress any key to continue...")
        return

    if action_num > len(recommendations):
        click.echo(click.style(f"  Action #{action_num} not available", fg="red"))
        click.echo(f"  Only {len(recommendations)} Quick Action(s) currently available")
        click.pause("\nPress any key to continue...")
        return

    action = recommendations[action_num - 1]

    click.echo(f"  Action:   {action['action']}")
    click.echo(f"  Priority: {action['priority']}")
    click.echo(f"  Target:   {action.get('target', 'N/A')}")

    if action.get("msf_module"):
        click.echo(f"  Module:   {action['msf_module']}")

    click.echo()

    # Ask for confirmation
    if not click.confirm("Execute this action?", default=True):
        click.echo(click.style("\n  Cancelled", fg="yellow"))
        click.pause("\nPress any key to continue...")
        return

    # Execute action based on type
    click.echo()

    target = action.get("target", "")
    port = action.get("port", "")
    service = action.get("service", "")
    msf_module = action.get("msf_module", "")

    if msf_module:
        # MSF module action - guide to MSF integration
        click.echo(click.style("  📋 MSF MODULE DETECTED", bold=True, fg="cyan"))
        click.echo(f"     Module: {msf_module}")
        click.echo(f"     Target: {target}")
        click.echo()
        click.echo("  To execute this exploit:")
        click.echo("    1. Open MSF Integration from main menu [m → MSF]")
        click.echo("    2. Generate resource script for this module")
        click.echo(f"    3. Run: msfconsole -r <script.rc>")
        click.echo()
        click.echo(click.style(f"  💡 Quick command:", fg="yellow"))
        click.echo(f"     msfconsole -x 'use {msf_module}; set RHOSTS {target}; run'")

    elif service and target:
        # Service exploitation - suggest and optionally run tool
        click.echo(click.style("  🔧 SERVICE ENUMERATION", bold=True, fg="cyan"))

        # Map services to recommended tools
        service_tools = {
            "http": ["gobuster", "wpscan", "nuclei"],
            "https": ["gobuster", "nuclei", "sslscan"],
            "ssh": ["hydra"],
            "smb": ["enum4linux", "smbmap", "smbclient"],
            "ftp": ["hydra", "nmap"],
            "mysql": ["hydra", "nmap"],
            "mssql": ["hydra", "nmap"],
            "rdp": ["hydra", "nmap"],
            "telnet": ["hydra"],
            "dns": ["dnsrecon"],
        }

        service_lower = service.lower()
        recommended = service_tools.get(service_lower, ["nmap"])

        click.echo(f"     Service: {service} on {target}:{port}")
        click.echo(f"     Recommended tools: {', '.join(recommended)}")
        click.echo()

        if click.confirm(
            f"  Queue {recommended[0]} scan against {target}?", default=True
        ):
            try:
                from souleyez.storage.job_queue import JobQueue

                jq = JobQueue()

                # Build appropriate arguments
                tool = recommended[0]
                if tool == "gobuster":
                    args = f"dir -u http://{target}:{port} -w data/wordlists/web_dirs_common.txt"
                elif tool == "enum4linux":
                    args = f"-a {target}"
                elif tool == "smbmap":
                    args = f"-H {target}"
                elif tool == "hydra":
                    args = f"-L data/wordlists/usernames_common.txt -P data/wordlists/passwords_brute.txt {service_lower}://{target}"
                elif tool == "nuclei":
                    args = f"-u http://{target}:{port} -t cves/"
                else:
                    args = f"-sV -p {port} {target}"

                jq.push(
                    tool=tool,
                    target=target,
                    args=args,
                    label=f"Quick Action: {service}",
                )
                click.echo(
                    click.style(
                        f"\n  ✓ Queued {tool} scan against {target}", fg="green"
                    )
                )
                click.echo("    Check Jobs menu to monitor progress.")
            except Exception as e:
                click.echo(click.style(f"\n  ✗ Failed to queue job: {e}", fg="red"))
        else:
            click.echo()
            click.echo(click.style("  💡 Manual command:", fg="yellow"))
            click.echo(f"     {recommended[0]} {target}")

    else:
        # Generic action - show guidance
        click.echo(click.style("  ℹ️  ACTION GUIDANCE", bold=True, fg="cyan"))
        click.echo(f"     {action['action']}")
        click.echo()
        click.echo("  This action requires manual intervention.")
        click.echo("  Use the appropriate menu to complete this task.")

    click.pause("\nPress any key to continue...")


def _view_auto_chaining_guide():
    """Display the auto-chaining guide."""
    import os

    guide_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "AUTO_CHAINING_GUIDE.md",
    )

    DesignSystem.clear_screen()
    click.echo("\n" + "=" * 70)
    click.echo(click.style("AUTO-CHAINING GUIDE", bold=True, fg="cyan"))
    click.echo("=" * 70 + "\n")

    if os.path.exists(guide_path):
        try:
            with open(guide_path, "r") as f:
                content = f.read()
            click.echo_via_pager(content)
        except Exception as e:
            click.echo(click.style(f"  ✗ Error reading guide: {e}", fg="red"))
    else:
        click.echo(click.style(f"  ✗ Guide not found at: {guide_path}", fg="red"))
        click.echo("\n  The auto-chaining guide should be located at the project root.")

    click.echo()
    click.pause("Press any key to return to dashboard...")


def _view_security_guide():
    """Display the security guide."""
    import os

    guide_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "SECURITY.md"
    )

    DesignSystem.clear_screen()
    click.echo("\n" + "=" * 70)
    click.echo(click.style("🔐 SECURITY GUIDE", bold=True, fg="green"))
    click.echo("=" * 70 + "\n")

    if os.path.exists(guide_path):
        try:
            with open(guide_path, "r") as f:
                content = f.read()
            click.echo_via_pager(content)
        except Exception as e:
            click.echo(click.style(f"  ✗ Error reading guide: {e}", fg="red"))
    else:
        click.echo(
            click.style(f"  ✗ Security guide not found at: {guide_path}", fg="red")
        )
        click.echo("\n  The security guide should be located at the project root.")

    click.echo()
    click.pause("Press any key to return...")


def _show_help_menu():
    """Show help menu with available guides."""
    from souleyez.ui.help_system import HelpContext, show_help

    show_help(HelpContext.DASHBOARD)


def _show_toggle_menu(state: "DashboardState"):
    """Show interactive menu to toggle dashboard sections."""
    DesignSystem.clear_screen()
    click.echo("\n" + "=" * 70)
    click.echo(click.style("DASHBOARD SECTION TOGGLES", bold=True, fg="cyan"))
    click.echo("=" * 70 + "\n")

    def status_icon(enabled):
        return click.style("✓", fg="green") if enabled else click.style("✗", fg="red")

    click.echo(f"  [1] {status_icon(state.show_hosts)} Top Hosts by Services")
    click.echo(f"  [2] {status_icon(state.show_ports)} Top Open Ports")
    click.echo(f"  [3] {status_icon(state.show_findings)} Critical/High Findings")
    click.echo(f"  [4] {status_icon(state.show_progress)} Progress & Discoveries")
    click.echo(
        f"  [5] {status_icon(state.show_credentials)} Credentials & Authentication"
    )
    click.echo()
    click.echo(
        f"  [9] Toggle Minimal Mode (currently: {'ON' if state.minimal_mode else 'OFF'})"
    )
    click.echo()
    click.echo("  [q] Back to Dashboard")
    click.echo()

    try:
        choice = click.prompt("Toggle section", type=int, default=0)

        if choice == 1:
            state.show_hosts = not state.show_hosts
        elif choice == 2:
            state.show_ports = not state.show_ports
        elif choice == 3:
            state.show_findings = not state.show_findings
        elif choice == 4:
            state.show_progress = not state.show_progress
        elif choice == 5:
            state.show_credentials = not state.show_credentials
        elif choice == 9:
            state.toggle_minimal()

        if choice != 0:
            _show_toggle_menu(state)  # Show menu again after toggle

    except (KeyboardInterrupt, click.Abort):
        return


def _wait_for_input(timeout: int) -> Optional[str]:
    """Wait for keyboard input with timeout. Returns input or None."""
    import select
    import sys

    try:
        # Check if input is available (Unix-like systems)
        if hasattr(select, "select"):
            rlist, _, _ = select.select([sys.stdin], [], [], timeout)
            if rlist:
                return sys.stdin.readline().strip()
        else:
            # Fallback for systems without select (just sleep)
            time.sleep(timeout)
        return None
    except Exception:
        time.sleep(timeout)
        return None


def _show_dashboard_menu(engagement_id: int) -> str:
    """
    Show interactive dashboard menu with clear instructions.

    Returns:
        'quit' - Exit to main menu
        'dashboard' - Return to Command Center
    """
    from souleyez.core.tool_chaining import ToolChaining

    while True:  # Loop - menu re-displays after sub-views exit
        DesignSystem.clear_screen()

        # Header
        width = DesignSystem.get_terminal_width()
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " SOULEYEZ COMMAND CENTER NAVIGATION ".center(width - 2),
                bold=True,
                fg="cyan",
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Instructions
        click.echo(
            click.style("  💡 TIP: ", fg="yellow", bold=True)
            + "These shortcuts work directly from the Command Center"
        )
        click.echo()

        # Intelligence & Actions section
        click.echo(
            click.style("  🧠 INTELLIGENCE & ACTIONS", bold=True, fg="bright_magenta")
        )
        click.echo("  " + "─" * 76)

        # Check user tier for Pro features
        from souleyez.auth import Tier, get_current_user

        current_user = get_current_user()
        is_pro_user = current_user and current_user.tier == Tier.PRO

        # Pro badge: 💎 for PRO users, 🔒 for FREE users
        pro_badge = (
            click.style("💎", fg="bright_magenta")
            if is_pro_user
            else click.style("🔒 PRO", fg="yellow")
        )

        # Intelligence Hub - Pro feature
        click.echo(
            "    "
            + click.style("[i]", fg="bright_magenta", bold=True)
            + "  🎯 Intelligence Hub     "
            + pro_badge
            + " - Attack surface & correlation"
        )

        # Show all Pro features with appropriate badge
        click.echo(
            "    "
            + click.style("[e]", fg="bright_magenta", bold=True)
            + "  🤖 AI Execute           "
            + pro_badge
            + " - AI-driven autonomous execution"
        )
        click.echo(
            "    "
            + click.style("[a]", fg="bright_magenta", bold=True)
            + "  🔗 Automation           "
            + pro_badge
            + " - Chain rules & settings"
        )
        click.echo(
            "    "
            + click.style("[m]", fg="bright_magenta", bold=True)
            + "  🔧 Metasploit           "
            + pro_badge
            + " - Generate exploits, launch msfconsole"
        )
        click.echo()

        # Data Management section
        click.echo(click.style("  📊 DATA MANAGEMENT", bold=True, fg="cyan"))
        click.echo("  " + "─" * 76)
        click.echo(
            "    "
            + click.style("[h]", fg="cyan", bold=True)
            + "  🎯 Hosts             - Discovered hosts, tags, filtering"
        )
        click.echo(
            "    "
            + click.style("[s]", fg="cyan", bold=True)
            + "  🔌 Services          - Open ports, service enumeration"
        )
        click.echo(
            "    "
            + click.style("[f]", fg="cyan", bold=True)
            + "  🔍 Findings          - All vulnerabilities (detailed view)"
        )
        click.echo(
            "    "
            + click.style("[c]", fg="cyan", bold=True)
            + "  🔑 Credentials       - Discovered users, passwords, hashes"
        )
        click.echo()
        click.echo(
            "    "
            + click.style("[w]", fg="cyan", bold=True)
            + "  🌐 Web Paths         - Directory enumeration results"
        )
        click.echo(
            "    "
            + click.style("[b]", fg="cyan", bold=True)
            + "  📁 SMB Shares        - SMB enumeration, accessible shares"
        )
        click.echo(
            "    "
            + click.style("[l]", fg="cyan", bold=True)
            + "  💉 SQLMap            - SQL injection discoveries"
        )
        click.echo(
            "    "
            + click.style("[p]", fg="cyan", bold=True)
            + "  🔌 WordPress         - WPScan vulnerabilities"
        )
        click.echo(
            "    "
            + click.style("[x]", fg="cyan", bold=True)
            + "  💣 Exploits          - SearchSploit exploit database"
        )
        click.echo(
            "    "
            + click.style("[o]", fg="cyan", bold=True)
            + "  🔍 OSINT             - DNS, WHOIS, emails, infrastructure"
        )
        click.echo()

        # Documentation section
        click.echo(click.style("  📋 DOCUMENTATION", bold=True, fg="yellow"))
        click.echo("  " + "─" * 76)
        click.echo(
            "    "
            + click.style("[v]", fg="yellow", bold=True)
            + "  📦 Evidence Vault        - Screenshots, files, exports"
        )
        click.echo(
            "    "
            + click.style("[d]", fg="yellow", bold=True)
            + "  ✅ Deliverables          - Progress tracking, checklists"
        )

        # Reports - Pro feature (show to all with appropriate badge)
        pro_badge_yellow = (
            click.style("💎", fg="yellow")
            if is_pro_user
            else click.style("🔒 PRO", fg="yellow")
        )
        click.echo(
            "    "
            + click.style("[g]", fg="yellow", bold=True)
            + "  📄 Generate Reports      "
            + pro_badge_yellow
            + " - Generate & export reports"
        )
        click.echo()

        click.echo(
            "    "
            + click.style("[q]", fg="red", bold=True)
            + "  ← Return to Command Center"
        )
        click.echo()

        # Footer instructions
        click.echo("  " + "─" * 76)
        click.echo(click.style("  Select option: ", bold=True), nl=False)

        try:
            choice = input().strip().lower()

            # Map letters to actions
            choice_map = {
                # Intelligence & Actions
                "i": "intelligence_hub",
                "e": "ai_execute",
                "a": "automation",
                "m": "msf",
                # Documentation
                "v": "evidence",
                "d": "deliverables",
                "g": "reports",
                # Data Management
                "h": "hosts",
                "s": "services",
                "f": "findings",
                "c": "credentials",
                "w": "web_paths",
                "b": "smb_shares",
                "l": "sqlmap",
                "p": "wordpress",
                "x": "exploits_db",
                "o": "osint",
                # Exit
                "q": "quit",
            }

            action = choice_map.get(choice, None)

            if action == "quit":
                return "dashboard"  # Exit navigation menu, return to Command Center

            # Intelligence Section (Consolidated - 3 items)
            elif action == "intelligence_hub":
                # Pro feature - check tier
                if not is_pro_user:
                    from souleyez.ui.interactive import _show_upgrade_prompt

                    _show_upgrade_prompt("Intelligence Hub")
                    continue
                # Unified Intelligence Hub (was Attack Correlation)
                from souleyez.ui.attack_surface import view_attack_surface

                view_attack_surface(engagement_id)
            elif action == "evidence":
                # Evidence & Artifacts (merged Evidence Vault + Screenshots)
                from souleyez.ui.evidence_vault import view_evidence_vault

                view_evidence_vault(engagement_id)
            elif action == "deliverables":
                from souleyez.ui.deliverables_view import show_deliverables_dashboard

                show_deliverables_dashboard(engagement_id)
            elif action == "ai_execute":
                # Pro feature - check tier
                if not is_pro_user:
                    from souleyez.ui.interactive import _show_upgrade_prompt

                    _show_upgrade_prompt("AI Execute")
                    continue
                # Return to Command Center with ai_execute action
                return "ai_execute"
            elif action == "automation":
                # Pro feature - check tier
                if not is_pro_user:
                    from souleyez.ui.interactive import _show_upgrade_prompt

                    _show_upgrade_prompt("Automation")
                    continue
                from souleyez.ui.interactive import _automation_submenu

                _automation_submenu()

            # Data Management Section
            elif action == "hosts":
                from souleyez.ui.interactive import view_hosts

                view_hosts(engagement_id)
            elif action == "services":
                from souleyez.ui.interactive import view_services

                view_services(engagement_id)
            elif action == "findings":
                from souleyez.ui.interactive import view_findings

                view_findings(engagement_id)
            elif action == "credentials":
                from souleyez.ui.interactive import view_credentials

                view_credentials(engagement_id)
            elif action == "web_paths":
                from souleyez.ui.interactive import view_web_paths

                view_web_paths(engagement_id)
            elif action == "smb_shares":
                from souleyez.ui.interactive import view_smb_shares

                view_smb_shares(engagement_id)
            elif action == "sqlmap":
                from souleyez.ui.interactive import view_sqlmap_data

                view_sqlmap_data(engagement_id)
            elif action == "wordpress":
                from souleyez.ui.interactive import view_wordpress_data

                view_wordpress_data(engagement_id)
            elif action == "osint":
                from souleyez.ui.interactive import view_osint

                view_osint(engagement_id)
            elif action == "exploits_db":
                from souleyez.ui.interactive import view_exploits_menu

                view_exploits_menu(engagement_id)

            # Operations Section
            elif action == "jobs":
                from souleyez.ui.interactive import view_jobs_menu

                view_jobs_menu()
            elif action == "toggle_chain":
                # Toggle auto-chaining
                chaining = ToolChaining()
                current_status = chaining.is_enabled()
                if current_status:
                    chaining.disable_chaining()
                    click.echo()
                    click.echo(
                        click.style(
                            "  ✓ Auto-chaining DISABLED", fg="yellow", bold=True
                        )
                    )
                else:
                    chaining.enable_chaining()
                    click.echo()
                    click.echo(
                        click.style("  ✓ Auto-chaining ENABLED", fg="green", bold=True)
                    )

                # Restart worker to apply changes
                click.echo()
                click.echo("  Restarting worker to apply changes...", nl=False)
                try:
                    from souleyez.engine.worker_manager import restart_worker

                    if restart_worker():
                        click.echo(click.style(" ✓", fg="green", bold=True))
                    else:
                        click.echo(
                            click.style(
                                " ✗ (worker may not have been running)", fg="yellow"
                            )
                        )
                except Exception as e:
                    click.echo(click.style(f" ✗ ({e})", fg="red"))

                click.echo()
                click.echo(
                    click.style("  💡 TIP: ", fg="cyan", bold=True)
                    + "Changes take effect immediately for new jobs."
                )
                click.pause("\nPress any key to return...")
            elif action == "toggle_mode":
                # Toggle chain mode (AUTO ↔ APPROVAL)
                chaining = ToolChaining()
                current = "APPROVAL" if chaining.is_approval_mode() else "AUTO"
                new_mode = chaining.toggle_approval_mode()
                new_text = "APPROVAL" if new_mode else "AUTO"

                click.echo()
                click.echo(
                    click.style(f"  Chain mode: {current} → {new_text}", bold=True)
                )
                if new_mode:
                    click.echo(
                        click.style(
                            "  ⏳ Chains will queue for your approval before executing.",
                            fg="yellow",
                        )
                    )
                else:
                    click.echo(
                        click.style(
                            "  ⚡ Chains will execute automatically.", fg="green"
                        )
                    )
                click.pause("\nPress any key to return...")
            elif action == "msf":
                # Pro feature - check tier
                if not is_pro_user:
                    from souleyez.ui.interactive import _show_upgrade_prompt

                    _show_upgrade_prompt("Metasploit")
                    continue
                from souleyez.ui.interactive import msf_integration_menu

                msf_integration_menu()
            elif action == "reports":
                # Pro feature - check tier
                if not is_pro_user:
                    from souleyez.ui.interactive import _show_upgrade_prompt

                    _show_upgrade_prompt("Reports & Export")
                    continue
                from souleyez.ui.interactive import manage_reports_menu

                manage_reports_menu()
            else:
                # Invalid choice - just loop again
                continue

        except (KeyboardInterrupt, EOFError):
            return "dashboard"  # Exit on Ctrl+C


def view_credentials(engagement_id: int, show_all: bool = False):
    """View all discovered credentials (similar to MSF's creds command)."""
    from souleyez.storage.credentials import CredentialsManager

    # from souleyez.storage.engagements import EngagementManager  # not used

    click.echo("📊 " + click.style("SUMMARY", bold=True, fg="cyan"))
    click.echo(DesignSystem.separator())
    cm = CredentialsManager()
    creds = cm.list_credentials(engagement_id, decrypt=False)
    stats = cm.get_stats(engagement_id)
    show_all = False
    click.echo(
        f"  Total: {stats['total']}  |  "
        + click.style(f"Valid: {stats['valid']}", fg="green", bold=True)
        + f"  |  Usernames: {stats.get('users_only', 0)}  |  Credential Pairs: {stats.get('pairs', 0)}"
    )
    click.echo()

    DesignSystem.clear_screen()

    cm = CredentialsManager()
    creds = cm.list_credentials(engagement_id, decrypt=False)

    # Summary stats in dashboard-style table at top
    stats = cm.get_stats(engagement_id)

    click.echo()
    width = DesignSystem.get_terminal_width()
    click.echo("┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" CREDENTIALS ".center(width - 2), bold=True, fg="green")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    click.echo()

    click.echo("📊 " + click.style("SUMMARY", bold=True, fg="cyan"))
    click.echo(DesignSystem.separator())
    click.echo(
        f"  Total: {stats['total']}  |  "
        + click.style(f"Valid: {stats['valid']}", fg="green", bold=True)
        + f"  |  Usernames: {stats['users_only']}  |  Credential Pairs: {stats['pairs']}"
    )
    click.echo()

    if not creds:
        click.echo(click.style("No credentials found yet.", fg="yellow"))
        click.echo()
        click.echo("💡 Credentials will appear here when discovered by:")
        click.echo("   • MSF auxiliary modules (ssh_enumusers, ssh_login, etc.)")
        click.echo("   • Brute force scans")
        click.echo("   • User enumeration modules")
        click.echo()
    else:
        # Separate valid and untested credentials
        valid_creds = [c for c in creds if c.get("status") == "valid"]
        untested_creds = [c for c in creds if c.get("status") != "valid"]

        # Credentials table with proper width (102 chars to match separator)
        # Columns: Status=10, Username=18, Password=18, Service=14, Host=18, Tool=16 (plus borders = 102)
        status_width = 10
        user_width = 18
        pass_width = 18
        service_width = 14
        host_width = 18
        tool_width = 16

        click.echo(click.style("🔐 CREDENTIALS", bold=True, fg="green"))
        click.echo(DesignSystem.separator())

        # Top border
        click.echo(
            "  ┌"
            + "─" * status_width
            + "┬"
            + "─" * user_width
            + "┬"
            + "─" * pass_width
            + "┬"
            + "─" * service_width
            + "┬"
            + "─" * host_width
            + "┬"
            + "─" * tool_width
            + "┐"
        )

        # Header
        header = f"  │ {'Status':<{status_width - 2}} │ {'Username':<{user_width - 2}} │ {'Password':<{pass_width - 2}} │ {'Service':<{service_width - 2}} │ {'Host':<{host_width - 2}} │ {'Tool':<{tool_width - 2}} │"
        click.echo(click.style(header, bold=True))

        # Header separator
        click.echo(
            "  ├"
            + "─" * status_width
            + "┼"
            + "─" * user_width
            + "┼"
            + "─" * pass_width
            + "┼"
            + "─" * service_width
            + "┼"
            + "─" * host_width
            + "┼"
            + "─" * tool_width
            + "┤"
        )

        # Show valid credentials first
        if valid_creds:
            for cred in valid_creds:
                username = mask_credential(cred.get("username", ""))
                password = mask_credential(cred.get("password", ""))
                service = cred.get("service", "N/A") or "N/A"
                host = cred.get("ip_address", "N/A") or "N/A"
                tool = cred.get("tool", "N/A") or "N/A"

                # Truncate if needed
                if len(username) > user_width - 2:
                    username = username[: user_width - 5] + "..."
                if len(password) > pass_width - 2:
                    password = password[: pass_width - 5] + "..."
                if len(service) > service_width - 2:
                    service = service[: service_width - 5] + "..."
                if len(host) > host_width - 2:
                    host = host[: host_width - 4]
                if len(tool) > tool_width - 2:
                    tool = tool[: tool_width - 5] + "..."

                # Build row with proper spacing
                status_text = f"{'✓ Valid':<{status_width - 2}}"
                row = f"  │ {status_text} │ {username:<{user_width - 2}} │ {password:<{pass_width - 2}} │ {service:<{service_width - 2}} │ {host:<{host_width - 2}} │ {tool:<{tool_width - 2}} │"

                # Color the status and credentials
                colored_status = click.style(status_text, fg="green", bold=True)
                colored_user = click.style(f"{username:<{user_width - 2}}", fg="green")
                colored_pass = click.style(f"{password:<{pass_width - 2}}", fg="green")

                row = row.replace(status_text, colored_status, 1)
                row = row.replace(
                    f" {username:<{user_width - 2}} ", f" {colored_user} ", 1
                )
                row = row.replace(
                    f" {password:<{pass_width - 2}} ", f" {colored_pass} ", 1
                )

                click.echo(row)

        # Show untested credentials if toggle is on
        if show_all and untested_creds:
            # Limit display to prevent overwhelming output
            display_limit = 20
            for cred in untested_creds[:display_limit]:
                username = mask_credential(cred.get("username", ""))
                password = (
                    mask_credential(cred.get("password", ""))
                    if cred.get("password")
                    else ""
                )
                service = cred.get("service", "N/A") or "N/A"
                host = cred.get("ip_address", "N/A") or "N/A"
                tool = cred.get("tool", "N/A") or "N/A"

                # Truncate if needed
                if len(username) > user_width - 2:
                    username = username[: user_width - 5] + "..."
                if password and len(password) > pass_width - 2:
                    password = password[: pass_width - 5] + "..."
                if len(service) > service_width - 2:
                    service = service[: service_width - 5] + "..."
                if len(host) > host_width - 2:
                    host = host[: host_width - 4]
                if len(tool) > tool_width - 2:
                    tool = tool[: tool_width - 5] + "..."

                # Build row
                status_text = f"{'○ Untest':<{status_width - 2}}"
                row = f"  │ {status_text} │ {username:<{user_width - 2}} │ {password:<{pass_width - 2}} │ {service:<{service_width - 2}} │ {host:<{host_width - 2}} │ {tool:<{tool_width - 2}} │"

                # Color the status
                colored_status = click.style(status_text, fg="cyan")
                row = row.replace(status_text, colored_status, 1)

                click.echo(row)

            if len(untested_creds) > display_limit:
                remaining = len(untested_creds) - display_limit
                click.echo(f"      ... and {remaining} more untested credentials")

        # Bottom border
        click.echo(
            "  └"
            + "─" * status_width
            + "┴"
            + "─" * user_width
            + "┴"
            + "─" * pass_width
            + "┴"
            + "─" * service_width
            + "┴"
            + "─" * host_width
            + "┴"
            + "─" * tool_width
            + "┘"
        )

        # Show message below table if untested are hidden
        if not show_all and untested_creds:
            click.echo()
            click.echo(
                click.style(
                    f"  ... {len(untested_creds)} untested usernames hidden (press [1] to show all)",
                    fg="bright_black",
                )
            )

        click.echo()

        # Menu
        from souleyez.ui.menu_components import StandardMenu

        options = [
            {
                "number": 1,
                "label": "Hide Untested" if show_all else "Show All",
                "description": "Toggle display of untested credentials",
            },
            {
                "number": 2,
                "label": "Decrypt & View",
                "description": "View passwords in cleartext",
            },
            {"number": 3, "label": "Export", "description": "Export usernames to file"},
        ]

        try:
            choice = StandardMenu.render(options)

            if choice == 0:
                return
            elif choice == 1:
                view_credentials(engagement_id, show_all=not show_all)
            elif choice == 2:
                view_credentials_decrypted(engagement_id)
            elif choice == 3:
                all_creds = cm.list_credentials(engagement_id, decrypt=False)
                untested_only = [
                    c
                    for c in all_creds
                    if c.get("status") != "valid" and c.get("username")
                ]
                if untested_only:
                    export_usernames_to_file(engagement_id, untested_only)
                    click.echo()
                    click.echo(
                        click.style("  Press ENTER to continue...", fg="cyan"), nl=False
                    )
                    input()
                    view_credentials(engagement_id, show_all)
        except (KeyboardInterrupt, EOFError):
            pass


def view_credentials_decrypted(
    engagement_id: int,
    page: int = 0,
    already_unlocked: bool = False,
    expand: bool = False,
):
    """View credentials with decryption (requires password). Paginated 10 per page."""
    from souleyez.storage.credentials import CredentialsManager

    #     from souleyez.storage.engagements import EngagementManager
    from souleyez.storage.crypto import get_crypto_manager

    crypto = get_crypto_manager()

    # Pagination settings
    ITEMS_PER_PAGE = 10

    # Check if encryption is enabled (should always be true now due to startup check)
    if not crypto.is_encryption_enabled():
        DesignSystem.clear_screen()
        click.echo()
        click.echo(click.style("⚠️  Encryption is not enabled!", fg="red"))
        click.echo("This should have been set up at startup.")
        click.echo("Please restart SoulEyez to enable encryption.")
        click.echo()
        click.pause("Press any key to return...")
        return

    # Only prompt for password if not already unlocked
    if not already_unlocked:
        # If we get here, encryption is enabled - prompt for password to unlock
        DesignSystem.clear_screen()
        click.echo()
        click.echo(click.style("🔓 DECRYPT CREDENTIALS", bold=True, fg="cyan"))
        click.echo("=" * 70)
        click.echo()

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                password = getpass.getpass("Enter master password: ")
                if crypto.unlock(password):
                    click.echo(click.style("✅ Unlocked successfully!", fg="green"))
                    break
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
                        click.echo()
                        click.pause("Press any key to return...")
                        return
            except KeyboardInterrupt:
                click.echo("\n❌ Cancelled by user.")
                return

    # Now display decrypted credentials
    # em = EngagementManager()  # not used currently

    DesignSystem.clear_screen()
    click.echo()
    width = DesignSystem.get_terminal_width()
    click.echo("┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" DECRYPTED CREDENTIALS ".center(width - 2), bold=True, fg="red")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    cm = CredentialsManager()
    creds = cm.list_credentials(engagement_id, decrypt=True)  # DECRYPT!

    if not creds:
        click.echo(click.style("No credentials found.", fg="yellow"))
    else:
        # Show stats
        stats = cm.get_stats(engagement_id)
        click.echo()
        click.echo(
            f"  Total: {stats['total']}  |  "
            + click.style(f"Valid: {stats['valid']}", fg="green", bold=True)
            + f"  |  Usernames: {stats['users_only']}  |  Credential Pairs: {stats['pairs']}"
        )
        click.echo()
        click.echo()

        # Display decrypted credentials - simple clean table
        # Dynamic column widths based on expand mode
        if expand:
            # Expanded view - much wider columns, may wrap
            status_width = 12
            user_width = 50
            pass_width = 80
            service_width = 16
            host_width = 25
            tool_width = 20
        else:
            status_width = 12
            user_width = 30
            pass_width = 50
            service_width = 16
            host_width = 20
            tool_width = 20

        # Header
        header = f"  {'Status':<{status_width}}{'Username':<{user_width}}{'Password':<{pass_width}}{'Service':<{service_width}}{'Host':<{host_width}}{'Tool':<{tool_width}}"
        click.echo(click.style(header, bold=True))

        # Header separator
        click.echo(
            " "
            + "─"
            * (
                1
                + status_width
                + user_width
                + pass_width
                + service_width
                + host_width
                + tool_width
            )
        )

        # Combine and paginate all credentials (valid first, then untested)
        valid_creds = [c for c in creds if c.get("status") == "valid"]
        untested_creds = [c for c in creds if c.get("status") != "valid"]
        all_creds = valid_creds + untested_creds

        # Calculate pagination
        total_creds = len(all_creds)
        total_pages = (total_creds + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        page = max(0, min(page, total_pages - 1))  # Clamp page to valid range
        start_idx = page * ITEMS_PER_PAGE
        end_idx = min(start_idx + ITEMS_PER_PAGE, total_creds)
        page_creds = all_creds[start_idx:end_idx]

        # Display credentials for current page
        for cred in page_creds:
            is_valid = cred.get("status") == "valid"
            username = cred.get("username", "") or ""
            password = (cred.get("password", "") or "") if cred.get("password") else ""
            service = cred.get("service", "-") or "-"
            host = cred.get("ip_address", "-") or "-"
            tool = cred.get("tool", "-") or "-"

            # Display <blank> for empty usernames
            if not username or username.strip() == "":
                username = "<blank>"

            # Truncate if needed (skip if expand mode)
            if not expand:
                if len(username) > user_width - 1:
                    username = username[: user_width - 4] + "..."
                if password and len(password) > pass_width - 1:
                    password = password[: pass_width - 4] + "..."
                if len(service) > service_width - 1:
                    service = service[: service_width - 4] + "..."
                if len(host) > host_width - 1:
                    host = host[: host_width - 1]
                if len(tool) > tool_width - 1:
                    tool = tool[: tool_width - 4] + "..."

            # Build row - pad BEFORE styling
            if is_valid:
                status_padded = f"{'✓ Valid':<{status_width}}"
                username_padded = f"{username:<{user_width}}"
                password_padded = f"{password:<{pass_width}}"
                service_padded = f"{service:<{service_width}}"
                host_padded = f"{host:<{host_width}}"
                tool_padded = f"{tool:<{tool_width}}"
                row = f"  {click.style(status_padded, fg='green', bold=True)}{click.style(username_padded, fg='green')}{click.style(password_padded, fg='green')}{service_padded}{host_padded}{tool_padded}"
            else:
                status_padded = f"{'○ Untested':<{status_width}}"
                username_padded = f"{username:<{user_width}}"
                password_padded = f"{password:<{pass_width}}"
                service_padded = f"{service:<{service_width}}"
                host_padded = f"{host:<{host_width}}"
                tool_padded = f"{tool:<{tool_width}}"
                row = f"  {status_padded}{username_padded}{password_padded}{service_padded}{host_padded}{tool_padded}"

            click.echo(row)

    click.echo()
    click.echo()

    # Pagination controls
    if total_pages > 1:
        click.echo(
            f"  Page {page + 1} of {total_pages}  |  Showing {start_idx + 1}-{end_idx} of {total_creds}"
        )
        click.echo()
        nav_options = []
        if page > 0:
            nav_options.append("[p] Previous")
        if page < total_pages - 1:
            nav_options.append("[n] Next")
        # Expand option
        expand_text = "Collapse" if expand else "Expand full values"
        nav_options.append(f"[x] {expand_text}")
        nav_options.append("[q] Back")
        click.echo("  " + "  |  ".join(nav_options))
    else:
        # Still show expand option even for single page
        expand_text = "Collapse" if expand else "Expand full values"
        click.echo(f"  [x] {expand_text}  |  [q] Back")

    click.echo()
    click.echo(
        click.style(
            "⚠️  WARNING: Credentials are displayed in plaintext!", fg="red", bold=True
        )
    )
    click.echo()

    # Get user input for navigation
    choice = click.prompt("", type=str, default="q", show_default=False)

    if choice.lower() == "n" and page < total_pages - 1:
        # Keep session unlocked for next page
        view_credentials_decrypted(
            engagement_id, page + 1, already_unlocked=True, expand=expand
        )
        return
    elif choice.lower() == "p" and page > 0:
        # Keep session unlocked for previous page
        view_credentials_decrypted(
            engagement_id, page - 1, already_unlocked=True, expand=expand
        )
        return
    elif choice.lower() == "x":
        # Toggle expand mode
        view_credentials_decrypted(
            engagement_id, page, already_unlocked=True, expand=not expand
        )
        return
    elif choice.lower() == "q":
        crypto.lock()
        return
    else:
        # Invalid input, just return
        crypto.lock()
        return


def view_untested_usernames(engagement_id: int):
    """View and manage untested usernames."""
    from souleyez.storage.credentials import CredentialsManager
    from souleyez.storage.engagements import EngagementManager

    em = EngagementManager()
    engagement = em.get_by_id(engagement_id)
    engagement_name = engagement["name"] if engagement else "Unknown"

    DesignSystem.clear_screen()

    # Header
    click.echo("\n┌" + "─" * 78 + "┐")
    click.echo(
        "│"
        + click.style(
            f" DISCOVERED USERNAMES - {engagement_name} ".center(78),
            bold=True,
            fg="cyan",
        )
        + "│"
    )
    click.echo("└" + "─" * 78 + "┘")
    click.echo()

    cm = CredentialsManager()
    all_creds = cm.list_credentials(engagement_id, decrypt=False)
    untested = [
        c for c in all_creds if c.get("status") != "valid" and c.get("username")
    ]

    if not untested:
        click.echo(click.style("  No untested usernames found.", fg="yellow"))
        click.echo()
    else:
        # Group by service
        by_service = {}
        for cred in untested:
            service = cred.get("service", "unknown")
            if service not in by_service:
                by_service[service] = []
            by_service[service].append(cred.get("username", ""))

        # Show each service with expandable view
        for service, usernames in sorted(by_service.items()):
            click.echo(
                click.style(
                    f"  {service.upper()} ({len(usernames)} users)",
                    bold=True,
                    fg="cyan",
                )
            )
            click.echo("  " + "─" * 76)

            # Show usernames in columns
            sorted_users = sorted(usernames)
            cols = 4
            col_width = 18

            for i in range(0, len(sorted_users), cols):
                row = sorted_users[i : i + cols]
                formatted_row = "".join([f"{u[:17]:<{col_width}}" for u in row])
                click.echo(f"    {formatted_row}")

            click.echo()

    click.echo("  " + "─" * 76)
    click.echo(click.style("  Options:", bold=True))
    click.echo("    [1] Export to file")
    click.echo("    [2] Launch brute force attack with these users")
    click.echo("    [q] Back")
    click.echo()
    click.echo(click.style("  Select option: ", fg="cyan"), nl=False)

    try:
        choice = input().strip().lower()

        if choice in ("q", ""):
            return

        if choice == "1":
            # Export to file
            export_usernames_to_file(engagement_id, untested)
            click.echo()
            click.echo(click.style("  Press ENTER to continue...", fg="cyan"), nl=False)
            input()

        elif choice == "2":
            # Launch brute force
            click.echo()
            click.echo(
                click.style(
                    "  Feature coming soon: Quick launch brute force", fg="yellow"
                )
            )
            click.echo(
                click.style(
                    "  For now, use: souleyez interactive > MSF Auxiliary > SSH Brute Force",
                    fg="cyan",
                )
            )
            click.echo()
            click.echo(click.style("  Press ENTER to continue...", fg="cyan"), nl=False)
            input()

    except (KeyboardInterrupt, EOFError):
        pass


def export_usernames_to_file(engagement_id: int, untested_creds: list):
    """Export untested usernames to a file."""
    import os

    from souleyez.storage.engagements import EngagementManager

    em = EngagementManager()
    engagement = em.get_by_id(engagement_id)
    engagement_name = engagement["name"] if engagement else "unknown"

    # Group by service
    by_service = {}
    for cred in untested_creds:
        service = cred.get("service", "unknown")
        if service not in by_service:
            by_service[service] = []
        by_service[service].append(cred.get("username", ""))

    # Create filename
    filename = f"usernames_{engagement_name}_{int(time.time())}.txt"
    filepath = os.path.join(os.getcwd(), filename)

    try:
        with open(filepath, "w") as f:
            for service, usernames in sorted(by_service.items()):
                f.write(f"# {service.upper()} ({len(usernames)} users)\n")
                for username in sorted(usernames):
                    f.write(f"{username}\n")
                f.write("\n")

        click.echo()
        click.echo(
            click.style(f"  ✓ Exported {len(untested_creds)} usernames to:", fg="green")
        )
        click.echo(f"    {filepath}")

    except Exception as e:
        click.echo()
        click.echo(click.style(f"  ✗ Error exporting: {e}", fg="red"))
