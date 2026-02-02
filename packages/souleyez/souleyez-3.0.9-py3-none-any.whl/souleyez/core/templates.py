#!/usr/bin/env python3
"""
souleyez.core.templates - Workflow presets for different pentest types

Presets provide recommended tools, scan phases, and tips to help users
get started quickly with common engagement types.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ScanPhase:
    """A phase in the recommended scan sequence."""

    name: str
    description: str
    tools: List[str]
    auto_chain: bool = True  # Whether to enable tool chaining for this phase


@dataclass
class EngagementTemplate:
    """Workflow preset for a specific type of penetration test."""

    id: str
    name: str
    description: str
    icon: str

    # Recommended tools for this engagement type
    recommended_tools: List[str] = field(default_factory=list)

    # Suggested scan phases in order
    scan_phases: List[ScanPhase] = field(default_factory=list)

    # Default wordlists (category -> wordlist name)
    wordlists: Dict[str, str] = field(default_factory=dict)

    # Common findings to look for
    common_findings: List[str] = field(default_factory=list)

    # Tips for this engagement type
    tips: List[str] = field(default_factory=list)

    # Scope examples
    scope_examples: List[str] = field(default_factory=list)

    # Initial scan configuration for auto-queue
    initial_scan_tool: str = ""
    initial_scan_args: str = ""
    initial_scan_description: str = ""


# Define available templates
TEMPLATES: Dict[str, EngagementTemplate] = {
    "webapp": EngagementTemplate(
        id="webapp",
        name="Web Application",
        description="Test web applications for OWASP Top 10 and common web vulnerabilities",
        icon="[W]",
        recommended_tools=[
            "nmap",
            "nikto",
            "gobuster",
            "feroxbuster",
            "sqlmap",
            "whatweb",
            "wpscan",
            "nuclei",
            "ffuf",
            "httpx",
        ],
        scan_phases=[
            ScanPhase(
                name="Reconnaissance",
                description="Discover services, technologies, and entry points",
                tools=["nmap", "whatweb", "httpx"],
            ),
            ScanPhase(
                name="Content Discovery",
                description="Find hidden directories, files, and endpoints",
                tools=["gobuster", "feroxbuster", "ffuf"],
            ),
            ScanPhase(
                name="Vulnerability Scanning",
                description="Identify known vulnerabilities and misconfigurations",
                tools=["nikto", "nuclei", "wpscan"],
            ),
            ScanPhase(
                name="Exploitation Testing",
                description="Test for injectable parameters and weaknesses",
                tools=["sqlmap"],
            ),
        ],
        wordlists={
            "directories": "directory-list-2.3-medium.txt",
            "files": "raft-large-files.txt",
            "subdomains": "subdomains-top1million-5000.txt",
        },
        common_findings=[
            "SQL Injection",
            "Cross-Site Scripting (XSS)",
            "CSRF",
            "Insecure Direct Object Reference",
            "Security Misconfiguration",
            "Sensitive Data Exposure",
            "Broken Authentication",
            "Directory Listing Enabled",
            "Information Disclosure",
        ],
        tips=[
            "Start with nmap to identify web ports (80, 443, 8080, 8443)",
            "Use whatweb to fingerprint technologies before deeper scanning",
            "Check robots.txt and sitemap.xml for hidden paths",
            "Test both authenticated and unauthenticated access",
            "Look for API endpoints (/api/, /v1/, /graphql)",
        ],
        scope_examples=["https://example.com", "app.example.com", "192.168.1.100:8080"],
        initial_scan_tool="nmap",
        initial_scan_args="-sV -sC -p 80,443,8080,8443",
        initial_scan_description="Service scan on common web ports",
    ),
    "network": EngagementTemplate(
        id="network",
        name="Network Infrastructure",
        description="Test network devices, services, and infrastructure security",
        icon="[N]",
        recommended_tools=[
            "nmap",
            "masscan",
            "enum4linux-ng",
            "smbclient",
            "snmpwalk",
            "nbtscan",
            "onesixtyone",
            "hydra",
            "crackmapexec",
            "rpcclient",
        ],
        scan_phases=[
            ScanPhase(
                name="Host Discovery",
                description="Identify live hosts on the network",
                tools=["nmap", "masscan", "nbtscan"],
            ),
            ScanPhase(
                name="Port Scanning",
                description="Enumerate open ports and services",
                tools=["nmap", "masscan"],
            ),
            ScanPhase(
                name="Service Enumeration",
                description="Gather detailed information about services",
                tools=["nmap", "enum4linux-ng", "snmpwalk", "onesixtyone"],
            ),
            ScanPhase(
                name="Vulnerability Assessment",
                description="Identify vulnerabilities in network services",
                tools=["nmap"],  # NSE scripts
            ),
            ScanPhase(
                name="Credential Testing",
                description="Test for weak or default credentials",
                tools=["hydra", "crackmapexec"],
            ),
        ],
        wordlists={
            "passwords": "passwords_brute.txt",
            "usernames": "usernames_common.txt",
            "snmp": "snmp-strings.txt",
        },
        common_findings=[
            "Default Credentials",
            "Weak Passwords",
            "SMB Signing Disabled",
            "Anonymous FTP Access",
            "SNMP Community Strings",
            "Unpatched Services",
            "Telnet Enabled",
            "Clear-text Protocols",
            "Unnecessary Services",
            "Network Segmentation Issues",
        ],
        tips=[
            "Use masscan for fast initial discovery, nmap for detailed scans",
            "Check for SMB null sessions and anonymous access",
            "Look for SNMP with default community strings (public/private)",
            "Test SSH, FTP, and Telnet for weak/default credentials",
            "Document the network topology as you discover it",
        ],
        scope_examples=["192.168.1.0/24", "10.0.0.0/8", "172.16.0.1-172.16.0.254"],
        initial_scan_tool="nmap",
        initial_scan_args="-sn",
        initial_scan_description="Host discovery ping sweep",
    ),
    "activedirectory": EngagementTemplate(
        id="activedirectory",
        name="Active Directory",
        description="Test Windows Active Directory environments for privilege escalation paths",
        icon="[AD]",
        recommended_tools=[
            "nmap",
            "enum4linux-ng",
            "crackmapexec",
            "smbclient",
            "rpcclient",
            "impacket",
            "bloodhound",
            "ldapsearch",
            "kerbrute",
            "responder",
        ],
        scan_phases=[
            ScanPhase(
                name="Domain Enumeration",
                description="Identify domain controllers and domain info",
                tools=["nmap", "crackmapexec"],
            ),
            ScanPhase(
                name="User Enumeration",
                description="Enumerate domain users, groups, and computers",
                tools=["enum4linux-ng", "crackmapexec", "rpcclient"],
            ),
            ScanPhase(
                name="Kerberos Attacks",
                description="Test for Kerberoasting and AS-REP roasting",
                tools=["impacket", "kerbrute"],
            ),
            ScanPhase(
                name="SMB/LDAP Enumeration",
                description="Enumerate shares, GPOs, and LDAP objects",
                tools=["smbclient", "crackmapexec", "ldapsearch"],
            ),
            ScanPhase(
                name="Attack Path Analysis",
                description="Identify paths to domain admin",
                tools=["bloodhound"],
            ),
        ],
        wordlists={
            "passwords": "passwords_brute.txt",
            "usernames": "usernames_common.txt",
            "ad-users": "ad_users.txt",
        },
        common_findings=[
            "Kerberoastable Accounts",
            "AS-REP Roastable Accounts",
            "Weak Domain Passwords",
            "LLMNR/NBT-NS Poisoning",
            "Unconstrained Delegation",
            "Password in Description",
            "Service Account Misconfiguration",
            "GPP Passwords",
            "SMB Signing Disabled",
            "Path to Domain Admin",
        ],
        tips=[
            "Start by identifying all Domain Controllers",
            "Check for null sessions and anonymous LDAP binds",
            "Look for service accounts with SPNs (Kerberoasting)",
            "Use BloodHound to visualize attack paths",
            "Check GPO for stored credentials (GPP)",
            "Test password spray attacks carefully (lockout policies!)",
        ],
        scope_examples=[
            "CORP.EXAMPLE.COM",
            "10.10.10.0/24 (DC subnet)",
            "dc01.corp.local",
        ],
        initial_scan_tool="nmap",
        initial_scan_args="-sV -p 53,88,135,139,389,445,464,636,3268,3269",
        initial_scan_description="AD/DC service discovery",
    ),
    "custom": EngagementTemplate(
        id="custom",
        name="Custom / Blank",
        description="Start with a blank engagement and configure everything manually",
        icon="[?]",
        recommended_tools=[],
        scan_phases=[],
        wordlists={},
        common_findings=[],
        tips=[
            "Define your scope clearly before starting",
            "Enable only the tools you need",
            "Use 'souleyez run <tool>' to queue scans",
            "Check 'souleyez dashboard' to monitor progress",
        ],
        scope_examples=["any target or range"],
    ),
    "ctf": EngagementTemplate(
        id="ctf",
        name="CTF / HackTheBox",
        description="Optimized for CTF challenges and platforms like HackTheBox/TryHackMe",
        icon="[CTF]",
        recommended_tools=[
            "nmap",
            "gobuster",
            "nikto",
            "ffuf",
            "enum4linux-ng",
            "linpeas",
            "winpeas",
            "pspy",
            "hydra",
            "john",
            "hashcat",
        ],
        scan_phases=[
            ScanPhase(
                name="Full Port Scan",
                description="Scan all 65535 ports - CTF boxes often have unusual ports",
                tools=["nmap"],
            ),
            ScanPhase(
                name="Service Enumeration",
                description="Deep dive into each discovered service",
                tools=["nmap", "enum4linux-ng"],
            ),
            ScanPhase(
                name="Web Enumeration",
                description="If web ports found, enumerate thoroughly",
                tools=["gobuster", "ffuf", "nikto"],
            ),
            ScanPhase(
                name="Exploitation",
                description="Exploit vulnerabilities for initial access",
                tools=[],  # Manual + searchsploit
            ),
            ScanPhase(
                name="Privilege Escalation",
                description="Escalate to root/admin",
                tools=["linpeas", "winpeas"],
            ),
        ],
        wordlists={
            "directories": "web_dirs_large.txt",
            "passwords": "passwords_brute.txt",
            "extensions": "web_extensions.txt",
        },
        common_findings=[
            "Hidden Web Directory",
            "Default Credentials",
            "Outdated Software Version",
            "SUID Binary",
            "Writable Script in Cron",
            "SSH Key Exposure",
            "Database Credentials in Config",
            "Kernel Exploit",
        ],
        tips=[
            "Always do a full port scan (-p-) - CTF boxes hide services",
            "Check source code comments for hints",
            "Look for version numbers to searchsploit",
            "After initial access, stabilize your shell first",
            "Run linPEAS/winPEAS immediately after access",
            "Check sudo -l, SUID binaries, and cron jobs",
        ],
        scope_examples=["10.10.10.X (HTB)", "10.10.X.X (THM)", "ctf.example.com"],
        initial_scan_tool="nmap",
        initial_scan_args="-sV -sC -p-",
        initial_scan_description="Full port scan (all 65535 ports)",
    ),
}


def get_template(template_id: str) -> Optional[EngagementTemplate]:
    """Get a template by ID."""
    return TEMPLATES.get(template_id)


def list_templates() -> List[EngagementTemplate]:
    """List all available templates."""
    return list(TEMPLATES.values())


def get_template_choices() -> List[tuple]:
    """Get templates as (id, display_name) tuples for menus."""
    return [(t.id, f"{t.icon} {t.name}") for t in TEMPLATES.values()]


def apply_template_settings(engagement_id: int, template_id: str) -> Dict[str, Any]:
    """
    Apply template settings to an engagement.

    Returns dict with what was applied for confirmation display.
    """
    template = get_template(template_id)
    if not template or template_id == "custom":
        return {"applied": False, "reason": "No template or custom selected"}

    # Store template metadata with engagement (for future reference)
    from souleyez.storage.engagements import EngagementManager

    em = EngagementManager()

    # Update engagement type
    em.update(engagement_id, {"engagement_type": template_id})

    return {
        "applied": True,
        "template": template.name,
        "recommended_tools": template.recommended_tools,
        "scan_phases": [p.name for p in template.scan_phases],
        "tips": template.tips[:3],  # First 3 tips
    }


def display_template_info(template: EngagementTemplate) -> None:
    """Display detailed template information."""
    import click

    click.echo()
    click.echo(click.style(f"  {template.icon} {template.name}", fg="cyan", bold=True))
    click.echo(click.style(f"  {template.description}", fg="white"))
    click.echo()

    if template.recommended_tools:
        click.echo(click.style("  Recommended Tools:", fg="yellow"))
        # Display in rows of 5
        tools = template.recommended_tools
        for i in range(0, len(tools), 5):
            row = tools[i : i + 5]
            click.echo("    " + ", ".join(row))
        click.echo()

    if template.scan_phases:
        click.echo(click.style("  Scan Phases:", fg="yellow"))
        for i, phase in enumerate(template.scan_phases, 1):
            click.echo(f"    {i}. {phase.name} - {phase.description}")
        click.echo()

    if template.tips:
        click.echo(click.style("  Quick Tips:", fg="yellow"))
        for tip in template.tips[:3]:
            click.echo(f"    - {tip}")
        click.echo()

    if template.scope_examples:
        click.echo(click.style("  Scope Examples:", fg="yellow"))
        for ex in template.scope_examples:
            click.echo(f"    - {ex}")


def get_recommended_tools(engagement_type: str) -> set:
    """Get set of recommended tool names for an engagement type."""
    template = get_template(engagement_type)
    if not template:
        return set()
    return set(t.lower() for t in template.recommended_tools)


def queue_initial_scan(
    template_id: str, target: str, engagement_id: int
) -> Optional[int]:
    """
    Queue the initial scan for a template.

    Returns job ID if queued, None if template has no initial scan or on error.
    """
    template = get_template(template_id)
    if not template or not template.initial_scan_tool:
        return None

    try:
        from souleyez.engine.background import enqueue_job

        job_id = enqueue_job(
            tool=template.initial_scan_tool,
            target=target,
            args=template.initial_scan_args,
            label=f"Initial: {template.initial_scan_description}",
            engagement_id=engagement_id,
            metadata={"auto_queued": True, "template": template_id},
        )
        return job_id
    except Exception:
        return None


def display_scan_phases_guide(template_id: str, clear_screen: bool = True) -> None:
    """Display the scan phases guide for a template."""
    import shutil

    import click

    from souleyez.ui.design_system import DesignSystem

    template = get_template(template_id)

    # Get terminal width
    width = shutil.get_terminal_size().columns

    if clear_screen:
        DesignSystem.clear_screen()

    # Header box
    click.echo()
    click.echo("┌" + "─" * (width - 2) + "┐")
    title = f"SCAN PHASES GUIDE: {template.name if template else 'Unknown'}"
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

    if not template:
        click.echo(click.style("  No template found.", fg="red"))
        return

    if not template.scan_phases:
        click.echo(
            click.style(
                "  No scan phases defined for this engagement type.", fg="yellow"
            )
        )
        click.echo("  This is a custom engagement - define your own workflow!")
        return

    click.echo(click.style("  📋 RECOMMENDED WORKFLOW", bold=True))
    click.echo("  " + "─" * (width - 4))
    click.echo()

    for i, phase in enumerate(template.scan_phases, 1):
        click.echo(click.style(f"    Phase {i}: {phase.name}", fg="yellow", bold=True))
        click.echo(f"    {phase.description}")
        if phase.tools:
            tools_str = ", ".join(phase.tools)
            click.echo(click.style("    Tools: ", fg="green") + tools_str)
        click.echo()

    if template.tips:
        click.echo("  " + "─" * (width - 4))
        click.echo()
        click.echo(click.style("  💡 TIPS", bold=True))
        click.echo()
        for tip in template.tips:
            click.echo(f"    • {tip}")
        click.echo()

    click.echo("  " + "─" * (width - 4))
    click.echo()
    click.echo(click.style("    [q] ← Back", fg="bright_black"))
    click.echo()
    click.echo("  " + "─" * (width - 4))
