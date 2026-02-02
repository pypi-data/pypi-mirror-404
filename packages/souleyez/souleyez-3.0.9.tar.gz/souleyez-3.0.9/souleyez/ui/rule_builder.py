#!/usr/bin/env python3
"""
souleyez.ui.rule_builder - Interactive chain rule builder for custom automation
"""

from typing import Any, Dict, List, Optional

import click

from souleyez.ui.design_system import DesignSystem


def show_rule_builder(mode: str = "simple") -> Optional[Dict[str, Any]]:
    """
    Show chain rule builder interface.

    Args:
        mode: 'simple' or 'advanced'

    Returns:
        Dict with rule definition or None if cancelled
    """
    if mode == "simple":
        return _simple_mode_builder()
    else:
        return _advanced_mode_builder()


def _simple_mode_builder() -> Optional[Dict[str, Any]]:
    """Guided step-by-step rule builder (simple mode)."""
    DesignSystem.clear_screen()
    width = 60

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" CREATE CHAIN RULE ".center(width - 2), bold=True, fg="cyan")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()
    click.echo(
        "  " + click.style("Simple Mode", fg="yellow") + " - Guided step-by-step"
    )
    click.echo("  Press 'q' at any step to cancel")
    click.echo()

    try:
        # Step 1: Select trigger tool
        trigger_tool = _select_trigger_tool()
        if not trigger_tool:
            return None

        # Step 2: Select condition
        condition = _select_condition_simple(trigger_tool)
        if not condition:
            return None

        # Step 3: Select target tool
        target_tool = _select_target_tool()
        if not target_tool:
            return None

        # Step 4: Select args template
        args_template = _select_args_template(target_tool)

        # Step 5: Rule settings
        rule_settings = _configure_rule_settings()
        if not rule_settings:
            return None

        # Build rule
        rule = {
            "trigger_tool": trigger_tool,
            "condition": condition,
            "target_tool": target_tool,
            "args": args_template,
            "priority": rule_settings["priority"],
            "category": rule_settings["category"],
            "enabled": rule_settings["enabled"],
            "description": rule_settings.get("description", ""),
        }

        # Show summary and confirm
        if _confirm_rule(rule):
            return rule

        return None

    except (KeyboardInterrupt, click.Abort):
        click.echo(click.style("\n  Rule creation cancelled", fg="yellow"))
        return None


def _select_trigger_tool() -> Optional[str]:
    """Step 1: Select trigger tool."""
    DesignSystem.clear_screen()
    width = 60

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" STEP 1: TRIGGER TOOL ".center(width - 2), bold=True, fg="cyan")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()
    click.echo("  When this tool completes...")
    click.echo()

    # Get all available tools from plugins
    tools = [
        ("nmap", "Network scanner"),
        ("theHarvester", "OSINT gathering"),
        ("whois", "Domain information"),
        ("dnsrecon", "DNS reconnaissance"),
        ("gobuster", "Directory brute-force"),
        ("ffuf", "Web fuzzing"),
        ("nuclei", "Vulnerability scanner"),
        ("wpscan", "WordPress scanner"),
        ("sqlmap", "SQL injection tool"),
        ("hydra", "Credential brute-force"),
        ("crackmapexec", "Windows/AD testing"),
        ("smbmap", "SMB enumeration"),
        ("enum4linux", "SMB/Samba enum"),
        ("bloodhound", "AD attack paths"),
        ("responder", "LLMNR poisoning"),
        ("searchsploit", "Exploit search"),
        ("hashcat", "Hash cracking"),
        ("john", "Password cracking"),
        ("custom", "Enter custom tool name"),
    ]

    for idx, (tool, desc) in enumerate(tools, 1):
        click.echo(f"    [{idx}] {tool:<15} - {desc}")

    click.echo()
    click.echo("    [q] Cancel")
    click.echo()

    try:
        choice = (
            click.prompt("  Select option", type=str, show_default=False)
            .strip()
            .lower()
        )

        if choice == "q":
            return None

        try:
            idx = int(choice)
            if 1 <= idx <= len(tools):
                tool_name = tools[idx - 1][0]
                if tool_name == "custom":
                    tool_name = click.prompt("  Enter tool name", type=str)
                return tool_name
        except ValueError:
            pass

        click.echo(click.style("  Invalid selection", fg="red"))
        click.pause()
        return None

    except (KeyboardInterrupt, click.Abort):
        return None


def _select_condition_simple(trigger_tool: str) -> Optional[str]:
    """Step 2: Select condition (simple mode)."""
    DesignSystem.clear_screen()
    width = 60

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" STEP 2: CONDITION ".center(width - 2), bold=True, fg="cyan")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()
    click.echo(f"  When {click.style(trigger_tool, fg='yellow')} finds...")
    click.echo()

    # Context-aware conditions based on trigger tool
    if trigger_tool in ["nmap"]:
        conditions = [
            ("service:http", "HTTP service discovered (port 80/443/8080)"),
            ("service:https", "HTTPS service discovered"),
            ("service:smb", "SMB service discovered (port 445)"),
            ("service:ssh", "SSH service discovered (port 22)"),
            ("service:ftp", "FTP service discovered (port 21)"),
            ("service:mysql", "MySQL service discovered (port 3306)"),
            ("service:mssql", "MSSQL service discovered (port 1433)"),
            ("service:rdp", "RDP service discovered (port 3389)"),
            ("port:*", "Any open port discovered"),
            ("custom", "Enter custom condition"),
        ]
    elif trigger_tool in ["theHarvester", "whois", "dnsrecon"]:
        conditions = [
            ("has:domains", "Domain/subdomain discovered"),
            ("has:emails", "Email addresses found"),
            ("has:hosts", "Host records found"),
            ("has:ips", "IP addresses found"),
            ("custom", "Enter custom condition"),
        ]
    elif trigger_tool in ["gobuster", "ffuf", "nuclei"]:
        conditions = [
            ("has:urls", "URLs/paths discovered"),
            ("finding:vulnerability", "Vulnerability found"),
            ("finding:cve", "CVE detected"),
            ("custom", "Enter custom condition"),
        ]
    elif trigger_tool in ["sqlmap"]:
        conditions = [
            ("sqli_confirmed", "SQL injection confirmed"),
            ("has:databases", "Databases enumerated"),
            ("has:tables", "Tables enumerated"),
            ("has:columns", "Columns enumerated"),
            ("custom", "Enter custom condition"),
        ]
    else:
        # Generic conditions for other tools
        conditions = [
            ("service:http", "HTTP service found"),
            ("service:smb", "SMB service found"),
            ("has:domains", "Domain/subdomain discovered"),
            ("has:databases", "Database found"),
            ("finding:vulnerability", "Vulnerability detected"),
            ("port:*", "Any open port"),
            ("custom", "Enter custom condition"),
        ]

    for idx, (cond, desc) in enumerate(conditions, 1):
        click.echo(f"    [{idx}] {desc}")

    click.echo()
    click.echo("    [q] Cancel")
    click.echo()

    try:
        choice = (
            click.prompt("  Select option", type=str, show_default=False)
            .strip()
            .lower()
        )

        if choice == "q":
            return None

        try:
            idx = int(choice)
            if 1 <= idx <= len(conditions):
                condition = conditions[idx - 1][0]
                if condition == "custom":
                    click.echo()
                    click.echo("  " + click.style("Examples:", fg="yellow"))
                    click.echo("    service:ftp, port:8080, has:tables, finding:xss")
                    condition = click.prompt("  Enter condition", type=str)
                elif condition == "port:*":
                    port = click.prompt(
                        "  Enter specific port (or * for any)", default="*"
                    )
                    if port != "*":
                        condition = f"port:{port}"
                return condition
        except ValueError:
            pass

        click.echo(click.style("  Invalid selection", fg="red"))
        click.pause()
        return None

    except (KeyboardInterrupt, click.Abort):
        return None


def _select_target_tool() -> Optional[str]:
    """Step 3: Select target tool."""
    DesignSystem.clear_screen()
    width = 60

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" STEP 3: TARGET TOOL ".center(width - 2), bold=True, fg="cyan")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()
    click.echo("  Then run...")
    click.echo()

    # Comprehensive list of target tools
    tools = [
        ("gobuster", "Directory brute-force"),
        ("ffuf", "Web fuzzing"),
        ("nuclei", "Vulnerability scanning"),
        ("wpscan", "WordPress scanning"),
        ("sqlmap", "SQL injection testing"),
        ("hydra", "Credential brute-force"),
        ("crackmapexec", "Windows/AD testing"),
        ("smbmap", "SMB share mapping"),
        ("enum4linux", "SMB/Samba enumeration"),
        ("bloodhound", "AD attack path mapping"),
        ("impacket-secretsdump", "Credential dumping"),
        ("impacket-getnpusers", "AS-REP roasting"),
        ("responder", "LLMNR poisoning"),
        ("searchsploit", "Exploit database search"),
        ("hashcat", "Hash cracking"),
        ("john", "Password cracking"),
        ("custom", "Enter custom tool name"),
    ]

    for idx, (tool, desc) in enumerate(tools, 1):
        click.echo(f"    [{idx}] {tool:<15} - {desc}")

    click.echo()
    click.echo("    [q] Cancel")
    click.echo()

    try:
        choice = (
            click.prompt("  Select option", type=str, show_default=False)
            .strip()
            .lower()
        )

        if choice == "q":
            return None

        try:
            idx = int(choice)
            if 1 <= idx <= len(tools):
                tool_name = tools[idx - 1][0]
                if tool_name == "custom":
                    tool_name = click.prompt("  Enter tool name", type=str)
                return tool_name
        except ValueError:
            pass

        click.echo(click.style("  Invalid selection", fg="red"))
        click.pause()
        return None

    except (KeyboardInterrupt, click.Abort):
        return None


def _select_args_template(tool: str) -> List[str]:
    """Step 4: Select args template."""
    DesignSystem.clear_screen()
    width = 60

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" STEP 4: ARGUMENTS ".center(width - 2), bold=True, fg="cyan")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()
    click.echo(f"  Arguments for {click.style(tool, fg='yellow')} (optional)")
    click.echo()

    # Tool-specific presets with common use cases
    presets = {
        "gobuster": [
            (
                ["dir", "-u", "{target}", "-w", "data/wordlists/web_dirs_common.txt"],
                "Default - web_dirs_common.txt",
            ),
            (
                ["dir", "-u", "{target}", "-w", "data/wordlists/web_dirs_large.txt"],
                "Large - web_dirs_large.txt",
            ),
        ],
        "ffuf": [
            (
                ["-u", "{target}/FUZZ", "-w", "data/wordlists/web_dirs_common.txt"],
                "Directory fuzzing",
            ),
            (
                [
                    "-u",
                    "{target}?FUZZ=value",
                    "-w",
                    "data/wordlists/web_files_common.txt",
                ],
                "Parameter fuzzing",
            ),
        ],
        "nuclei": [
            (
                ["-u", "{target}", "-severity", "critical,high"],
                "Critical/High severity only",
            ),
            (["-u", "{target}", "-tags", "cve"], "CVE templates only"),
            (["-u", "{target}"], "All templates (default)"),
        ],
        "sqlmap": [
            (["-u", "{target}", "--batch", "--dbs"], "Enumerate databases"),
            (
                ["-u", "{target}", "--batch", "--forms", "--crawl=2"],
                "Form-based with crawling",
            ),
        ],
        "hydra": [
            (
                [
                    "-L",
                    "data/wordlists/usernames_common.txt",
                    "-P",
                    "data/wordlists/passwords_brute.txt",
                    "{target}",
                    "ssh",
                ],
                "SSH brute-force",
            ),
            (
                [
                    "-L",
                    "data/wordlists/usernames_common.txt",
                    "-P",
                    "data/wordlists/passwords_brute.txt",
                    "{target}",
                    "ftp",
                ],
                "FTP brute-force",
            ),
        ],
        "wpscan": [
            (
                ["--url", "{target}", "--enumerate", "vp,vt,u"],
                "Enumerate plugins, themes, users",
            ),
        ],
        "crackmapexec": [
            (
                ["smb", "{target}", "-u", "Administrator", "-p", "password"],
                "SMB authentication",
            ),
            (["smb", "{target}", "--shares"], "Enumerate SMB shares"),
        ],
    }

    if tool in presets:
        click.echo("  " + click.style("Common presets:", fg="yellow"))
        for idx, (args, desc) in enumerate(presets[tool], 1):
            click.echo(f"    [{idx}] {desc}")
        click.echo(f"    [{len(presets[tool]) + 1}] Custom args...")
        click.echo("    [ENTER] Skip (no args)")
        click.echo()

        choice = click.prompt("  Select option", default="", show_default=False).strip()

        if not choice:
            return []

        try:
            idx = int(choice)
            if 1 <= idx <= len(presets[tool]):
                return presets[tool][idx - 1][0]
            elif idx == len(presets[tool]) + 1:
                # Custom args
                click.echo()
                click.echo("  " + click.style("Placeholders available:", fg="yellow"))
                click.echo("    {target} - Target URL/IP/host")
                click.echo("    {port} - Target port")
                click.echo("    {domain} - Domain name")
                click.echo()
                click.echo(
                    "  "
                    + click.style("Example:", fg="yellow")
                    + " -u {target} -o /tmp/output.txt"
                )
                click.echo()
                args_str = click.prompt("  Enter arguments", type=str)
                return args_str.split()
        except ValueError:
            pass
    else:
        # No presets for this tool - show help and get custom args
        click.echo(
            "  " + click.style("No presets available for this tool.", fg="yellow")
        )
        click.echo()
        click.echo("  " + click.style("Available placeholders:", fg="cyan"))
        click.echo("    {target}  - Target URL/IP/host")
        click.echo("    {port}    - Target port")
        click.echo("    {domain}  - Domain name")
        click.echo()
        click.echo("  " + click.style("Examples:", fg="cyan"))
        click.echo("    -u {target} --threads 10")
        click.echo("    --target {target}:{port}")
        click.echo("    -d {domain} -o output.txt")
        click.echo()

        args_str = click.prompt(
            "  Enter arguments (or ENTER to skip)", default="", show_default=False
        )
        if args_str:
            return args_str.split()

    return []


def _configure_rule_settings() -> Optional[Dict[str, Any]]:
    """Step 5: Configure rule settings."""
    DesignSystem.clear_screen()
    width = 60

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" STEP 5: RULE SETTINGS ".center(width - 2), bold=True, fg="cyan")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    try:
        priority = click.prompt(
            "  Priority (1-10, higher = runs first)",
            type=click.IntRange(1, 10),
            default=5,
        )

        click.echo()
        click.echo("  Category:")
        click.echo("    [1] CTF - Aggressive scanning for practice environments")
        click.echo("    [2] Enterprise - Conservative scanning for production")
        click.echo("    [3] General - Balanced approach for most scenarios")
        click.echo()

        cat_choice = click.prompt(
            "  Select option", type=click.IntRange(1, 3), default=3, show_default=False
        )
        categories = {1: "CTF", 2: "ENTERPRISE", 3: "GENERAL"}
        category = categories[cat_choice]

        click.echo()
        enabled = click.confirm("  Enable immediately?", default=True)

        click.echo()
        description = click.prompt(
            "  Description (optional)", default="", show_default=False
        )

        return {
            "priority": priority,
            "category": category,
            "enabled": enabled,
            "description": description,
        }

    except (KeyboardInterrupt, click.Abort):
        return None


def _confirm_rule(rule: Dict[str, Any]) -> bool:
    """Show rule summary and confirm creation."""
    DesignSystem.clear_screen()
    width = 60

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" RULE CREATED! ".center(width - 2), bold=True, fg="green")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    # Format rule display
    click.echo(
        "  "
        + click.style("WHEN", fg="yellow", bold=True)
        + f" {rule['trigger_tool']} finds {rule['condition']}"
    )
    click.echo(
        "  "
        + click.style("THEN", fg="yellow", bold=True)
        + f" run {rule['target_tool']}"
    )

    if rule["args"]:
        args_str = " ".join(rule["args"])
        click.echo("  " + click.style("WITH", fg="yellow", bold=True) + f" {args_str}")

    click.echo()
    click.echo(f"  Priority: {rule['priority']}/10")
    click.echo(f"  Category: {rule['category']}")
    click.echo(f"  Status: {'ENABLED' if rule['enabled'] else 'DISABLED'}")

    if rule["description"]:
        click.echo(f"  Description: {rule['description']}")

    click.echo()
    click.echo("  [ENTER] Save rule  [+] Create another  [q] Cancel")
    click.echo()

    choice = (
        click.prompt("  Select option", default="", show_default=False).strip().lower()
    )

    return choice != "q"


def _advanced_mode_builder() -> Optional[Dict[str, Any]]:
    """Advanced mode with full control (to be implemented)."""
    click.echo(click.style("\n  Advanced mode coming soon!", fg="yellow"))
    click.pause()
    return None


def _save_custom_rule(rule: Dict[str, Any]) -> bool:
    """
    Save custom rule to file.

    Args:
        rule: Rule dictionary

    Returns:
        bool: True if saved successfully
    """
    try:
        from souleyez.core.tool_chaining import ToolChaining

        tc = ToolChaining()
        tc.add_custom_rule(rule)

        click.echo()
        click.echo(click.style("  ✓ Rule saved successfully!", fg="green"))
        click.pause()
        return True

    except Exception as e:
        click.echo()
        click.echo(click.style(f"  ✗ Failed to save rule: {e}", fg="red"))
        click.pause()
        return False
