#!/usr/bin/env python3
"""
souleyez.ui.help_system - In-app help and tooltips system

Provides context-sensitive help throughout the application.
"""

from typing import Dict, List, Optional

import click


class HelpContext:
    """Enum-like class for help contexts."""

    MAIN_MENU = "main_menu"
    ENGAGEMENT_MENU = "engagement_menu"
    TOOLS_MENU = "tools_menu"
    DASHBOARD = "dashboard"
    CREDENTIALS = "credentials"
    FINDINGS = "findings"
    HOSTS = "hosts"
    METASPLOIT = "metasploit"
    CHAIN_RULES = "chain_rules"
    EVIDENCE = "evidence"
    EXPORT = "export"
    GENERAL = "general"


# Context-specific help content
HELP_CONTENT: Dict[str, Dict] = {
    HelpContext.MAIN_MENU: {
        "title": "Main Menu Help",
        "description": "The main menu is your starting point for all operations.",
        "shortcuts": {
            "1-9": "Select a menu option",
            "q": "Quit / Go back",
            "?": "Show this help",
        },
        "tips": [
            "Start by creating or selecting an engagement",
            "Use 'Run Tools' to queue scans against your target",
            "Check 'Dashboard' to monitor active scans",
            "View 'Findings' to see discovered vulnerabilities",
        ],
    },
    HelpContext.ENGAGEMENT_MENU: {
        "title": "Engagement Management Help",
        "description": "Engagements keep your pentest data organized and isolated.",
        "shortcuts": {
            "1-9": "Select an engagement",
            "+": "Create new engagement",
            "-": "Delete an engagement",
            "q": "Go back",
        },
        "tips": [
            "Each engagement is like a project folder",
            "All hosts, findings, and credentials are scoped to the engagement",
            "Use presets for quick setup (Web, Network, AD)",
            "You can have multiple engagements active",
        ],
    },
    HelpContext.TOOLS_MENU: {
        "title": "Tools Menu Help",
        "description": "Run pentesting tools against your targets.",
        "shortcuts": {
            "1-9": "Select a tool category",
            "s": "Search for a tool",
            "q": "Go back",
        },
        "tips": [
            "Tools are organized by category (Recon, Enum, Exploit, etc.)",
            "Tool chaining automatically queues follow-up scans",
            "Check 'souleyez setup' if tools are missing",
            "View tool output in the Dashboard",
        ],
        "tool_categories": {
            "Reconnaissance": "nmap, masscan, whatweb - Discover hosts and services",
            "Enumeration": "enum4linux, smbclient, snmpwalk - Gather details",
            "Web Testing": "nikto, gobuster, sqlmap - Web vulnerabilities",
            "Exploitation": "metasploit, searchsploit - Exploit vulns",
            "Password Attacks": "hydra, john, hashcat - Crack credentials",
        },
    },
    HelpContext.DASHBOARD: {
        "title": "Dashboard Help",
        "description": "Real-time monitoring of scans and results.",
        "shortcuts": {
            "j": "Jobs view - See running scans",
            "h": "Hosts view - See discovered hosts",
            "f": "Findings view - See vulnerabilities",
            "l": "Logs view - See tool output",
            "r": "Refresh data",
            "q": "Quit dashboard",
        },
        "tips": [
            "Dashboard auto-refreshes every few seconds",
            "Jobs show real-time progress of running scans",
            "Findings are color-coded by severity",
            "Use 'l' to see raw tool output for debugging",
        ],
    },
    HelpContext.CREDENTIALS: {
        "title": "Credential Vault Help",
        "description": "Securely store discovered credentials.",
        "shortcuts": {
            "+": "Add a credential",
            "-": "Delete a credential",
            "e": "Export credentials",
            "q": "Go back",
        },
        "tips": [
            "Credentials are encrypted with AES-256-GCM",
            "Each credential is scoped to its engagement",
            "Test credentials with 'hydra' or 'crackmapexec'",
            "Export to use with other tools",
        ],
        "security": [
            "Never store production credentials in test environments",
            "Use strong master password for encryption",
            "Credentials cannot be recovered if password is lost",
        ],
    },
    HelpContext.FINDINGS: {
        "title": "Findings Help",
        "description": "View and manage discovered vulnerabilities.",
        "shortcuts": {
            "1-9": "Select a finding",
            "c": "Change severity",
            "n": "Add notes",
            "e": "Export findings",
            "q": "Go back",
        },
        "severity_levels": {
            "Critical": "Immediate exploitation risk (CVSS 9.0-10.0)",
            "High": "Significant vulnerability (CVSS 7.0-8.9)",
            "Medium": "Moderate risk (CVSS 4.0-6.9)",
            "Low": "Minor issue (CVSS 0.1-3.9)",
            "Info": "Informational finding",
        },
        "tips": [
            "Verify findings manually before reporting",
            "Add notes with reproduction steps",
            "Link findings to evidence screenshots",
            "Export to include in final report",
        ],
    },
    HelpContext.HOSTS: {
        "title": "Hosts Help",
        "description": "View discovered hosts and their services.",
        "shortcuts": {
            "1-9": "Select a host",
            "s": "Show services for host",
            "n": "Add notes",
            "q": "Go back",
        },
        "tips": [
            "Hosts are discovered by nmap and other recon tools",
            "Each host shows open ports and services",
            "Click on a host to see detailed information",
            "Services link to potential vulnerabilities",
        ],
    },
    HelpContext.METASPLOIT: {
        "title": "Metasploit Integration Help",
        "description": "Use Metasploit Framework for exploitation.",
        "shortcuts": {
            "1-9": "Select an option",
            "c": "Open msfconsole",
            "q": "Go back",
        },
        "tips": [
            "Database is shared between SoulEyez and MSF",
            "Hosts and services sync automatically",
            "Use 'search' in msfconsole to find exploits",
            "Run 'db_nmap' to import nmap results",
        ],
        "common_commands": {
            "search": "Find modules (search type:exploit name:smb)",
            "use": "Select a module (use exploit/windows/smb/ms17_010_eternalblue)",
            "set": "Set options (set RHOSTS 192.168.1.1)",
            "run": "Execute the module",
            "sessions": "List active sessions",
        },
    },
    HelpContext.CHAIN_RULES: {
        "title": "Tool Chaining Help",
        "description": "Automatic follow-up scans based on discoveries.",
        "shortcuts": {
            "+": "Create new rule",
            "-": "Delete a rule",
            "t": "Toggle rule on/off",
            "q": "Go back",
        },
        "tips": [
            "Rules trigger when specific conditions are met",
            "Example: HTTP found -> auto-queue nikto scan",
            "Priorities control which rules run first",
            "Disable rules to prevent unwanted scans",
        ],
        "examples": [
            "nmap finds HTTP (80/443) -> nikto, gobuster",
            "nmap finds SMB (445) -> enum4linux",
            "nmap finds MySQL (3306) -> hydra with mysql module",
        ],
    },
    HelpContext.EVIDENCE: {
        "title": "Evidence & Artifacts Help",
        "description": "Collect screenshots and artifacts for reporting.",
        "shortcuts": {
            "+": "Add evidence",
            "s": "Take screenshot",
            "e": "Export evidence",
            "q": "Go back",
        },
        "tips": [
            "Screenshots are organized by pentesting phase",
            "Add descriptions for context in reports",
            "Link evidence to specific findings",
            "Export includes all metadata",
        ],
    },
    HelpContext.EXPORT: {
        "title": "Export Help",
        "description": "Export data for reporting and integration.",
        "formats": {
            "CSV": "Excel-compatible, good for data analysis",
            "JSON": "API integration, programmatic access",
            "Markdown": "Documentation, reports",
            "HTML": "Standalone report viewing",
        },
        "tips": [
            "CSV is best for importing into other tools",
            "JSON preserves all data fields",
            "Markdown is great for including in reports",
        ],
    },
    HelpContext.GENERAL: {
        "title": "SoulEyez Help",
        "description": "AI-Powered Penetration Testing Platform",
        "quick_commands": {
            "souleyez interactive": "Menu-driven interface",
            "souleyez dashboard": "Real-time monitoring",
            "souleyez setup": "Install pentesting tools",
            "souleyez doctor": "Diagnose issues",
            "souleyez tutorial": "Guided walkthrough",
            "souleyez run <tool>": "Run a specific tool",
        },
        "tips": [
            "Start with 'souleyez tutorial' if you're new",
            "Use 'souleyez doctor' to fix common issues",
            "Press '?' in any menu for context help",
        ],
        "resources": [
            "Docs: https://github.com/cyber-soul-security/SoulEyez",
            "Issues: https://github.com/cyber-soul-security/SoulEyez/issues",
        ],
    },
}


def get_template_tips(engagement_type: Optional[str] = None) -> List[str]:
    """
    Get tips from the current engagement's preset.

    Args:
        engagement_type: The engagement preset type (webapp, network, ctf, etc.)

    Returns:
        List of preset-specific tips
    """
    if not engagement_type or engagement_type == "custom":
        return []

    try:
        from souleyez.core.templates import get_template

        template = get_template(engagement_type)
        if template and template.tips:
            return template.tips
    except Exception:
        pass
    return []


def show_help(
    context: str = HelpContext.GENERAL,
    clear_screen: bool = True,
    engagement_type: Optional[str] = None,
) -> None:
    """
    Display context-sensitive help.

    Args:
        context: The help context to display
        clear_screen: Whether to clear screen before showing help
        engagement_type: Optional engagement preset type for preset-specific tips
    """
    import shutil

    from souleyez.ui.design_system import DesignSystem

    help_data = HELP_CONTENT.get(context, HELP_CONTENT[HelpContext.GENERAL])
    width = shutil.get_terminal_size().columns

    if clear_screen:
        DesignSystem.clear_screen()

    # Header box (like docs menu)
    click.echo()
    click.echo("┌" + "─" * (width - 2) + "┐")
    title = help_data["title"].upper()
    padding = (width - len(title) - 2) // 2
    click.echo(
        "│"
        + " " * padding
        + click.style(title, bold=True, fg="cyan")
        + " " * (width - len(title) - padding - 2)
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    # Description
    click.echo(click.style(f"  {help_data['description']}", fg="white"))
    click.echo()
    click.echo("  " + "─" * (width - 4))
    click.echo()

    # Keyboard shortcuts
    if "shortcuts" in help_data:
        click.echo(click.style("  Keyboard Shortcuts:", fg="yellow", bold=True))
        for key, desc in help_data["shortcuts"].items():
            click.echo(f"    [{click.style(key, fg='cyan')}] {desc}")
        click.echo()

    # Tips
    if "tips" in help_data:
        click.echo(click.style("  Tips:", fg="yellow", bold=True))
        for tip in help_data["tips"]:
            click.echo(f"    - {tip}")
        click.echo()

    # Preset-specific tips (if engagement type is provided)
    template_tips = get_template_tips(engagement_type)
    if template_tips:
        try:
            from souleyez.core.templates import get_template

            template = get_template(engagement_type)
            template_name = template.name if template else engagement_type
        except Exception:
            template_name = engagement_type

        click.echo(click.style(f"  {template_name} Tips:", fg="magenta", bold=True))
        for tip in template_tips[:5]:  # Show up to 5 preset tips
            click.echo(f"    - {tip}")
        click.echo()

    # Tool categories (for tools menu)
    if "tool_categories" in help_data:
        click.echo(click.style("  Tool Categories:", fg="yellow", bold=True))
        for category, tools in help_data["tool_categories"].items():
            click.echo(f"    {click.style(category, fg='green')}: {tools}")
        click.echo()

    # Severity levels (for findings)
    if "severity_levels" in help_data:
        click.echo(click.style("  Severity Levels:", fg="yellow", bold=True))
        colors = {
            "Critical": "red",
            "High": "red",
            "Medium": "yellow",
            "Low": "blue",
            "Info": "white",
        }
        for level, desc in help_data["severity_levels"].items():
            color = colors.get(level, "white")
            click.echo(f"    {click.style(level, fg=color, bold=True)}: {desc}")
        click.echo()

    # Common commands (for MSF)
    if "common_commands" in help_data:
        click.echo(click.style("  Common Commands:", fg="yellow", bold=True))
        for cmd, desc in help_data["common_commands"].items():
            click.echo(f"    {click.style(cmd, fg='green')}: {desc}")
        click.echo()

    # Examples (for chain rules)
    if "examples" in help_data:
        click.echo(click.style("  Examples:", fg="yellow", bold=True))
        for example in help_data["examples"]:
            click.echo(f"    {example}")
        click.echo()

    # Export formats
    if "formats" in help_data:
        click.echo(click.style("  Export Formats:", fg="yellow", bold=True))
        for fmt, desc in help_data["formats"].items():
            click.echo(f"    {click.style(fmt, fg='green')}: {desc}")
        click.echo()

    # Quick commands (for general)
    if "quick_commands" in help_data:
        click.echo(click.style("  Quick Commands:", fg="yellow", bold=True))
        for cmd, desc in help_data["quick_commands"].items():
            click.echo(f"    {click.style(cmd, fg='green')}: {desc}")
        click.echo()

    # Resources (for general)
    if "resources" in help_data:
        click.echo(click.style("  Resources:", fg="yellow", bold=True))
        for resource in help_data["resources"]:
            click.echo(f"    {resource}")
        click.echo()

    # Security notes
    if "security" in help_data:
        click.echo(click.style("  Security Notes:", fg="red", bold=True))
        for note in help_data["security"]:
            click.echo(f"    ! {note}")
        click.echo()

    # Footer (like docs menu)
    click.echo("  " + "─" * (width - 4))
    click.echo()
    click.echo(click.style("    [q] ← Back", fg="bright_black"))
    click.echo()
    click.echo("  " + "─" * (width - 4))


def show_tooltip(key: str, context: str = HelpContext.GENERAL) -> Optional[str]:
    """
    Get a tooltip for a specific key in a context.

    Args:
        key: The key/option to get tooltip for
        context: The help context

    Returns:
        Tooltip string or None if not found
    """
    help_data = HELP_CONTENT.get(context, {})
    shortcuts = help_data.get("shortcuts", {})
    return shortcuts.get(key)


def show_quick_help() -> None:
    """Show a quick help overlay (minimal version)."""
    click.echo()
    click.echo(click.style("  Quick Help:", fg="cyan", bold=True))
    click.echo("    [?] Show full help")
    click.echo("    [q] Go back / Quit")
    click.echo("    [1-9] Select option")
    click.echo()


def get_feature_tip(feature: str) -> str:
    """
    Get a tip for a feature.

    Args:
        feature: Feature name

    Returns:
        Tip string
    """
    feature_tips = {
        "engagement": "Tip: Use presets for quick setup of Web, Network, or AD engagements",
        "scan": "Tip: Tool chaining automatically queues follow-up scans based on discoveries",
        "credentials": "Tip: Credentials are encrypted - never store production creds in test DBs",
        "dashboard": "Tip: Press 'j' for jobs, 'h' for hosts, 'f' for findings",
        "metasploit": "Tip: Use 'db_nmap' in msfconsole to import scan results",
        "export": "Tip: CSV format works great with Excel and other analysis tools",
    }
    return feature_tips.get(feature, "Tip: Press '?' for help in any menu")
