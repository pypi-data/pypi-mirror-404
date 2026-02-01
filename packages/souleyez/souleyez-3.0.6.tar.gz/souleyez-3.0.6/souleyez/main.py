#!/usr/bin/env python3
"""
souleyez.main - CLI entry point
"""

import datetime
import getpass
import os
import shutil
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from souleyez.security import require_password, unlock_credentials_if_needed
from souleyez.storage.crypto import get_crypto_manager
from souleyez.ui.design_system import DesignSystem

try:
    from souleyez.engine.background import (
        enqueue_job,
        get_job,
        list_jobs,
        start_worker,
        worker_loop,
    )
    from souleyez.storage.engagements import EngagementManager
    from souleyez.ui.dashboard import run_dashboard
    from souleyez.ui.interactive import run_interactive_menu
except ImportError as e:
    click.echo(f"Import error: {e}", err=True)
    sys.exit(1)


def _check_prerequisites():
    """Check for required system tools and warn if missing."""
    missing = []

    if not shutil.which("curl"):
        missing.append("curl")
    if not shutil.which("pip3"):
        missing.append("python3-pip")

    if missing:
        click.secho("⚠️  Missing prerequisites:", fg="yellow", bold=True)
        click.echo()
        for pkg in missing:
            click.echo(f"   • {pkg}")
        click.echo()
        click.echo("Install with:")
        click.secho(f"   sudo apt install {' '.join(missing)}", fg="cyan")
        click.echo()


def _check_first_run_setup():
    """Check if this is first run and prompt to install tools if needed."""
    marker_file = Path.home() / ".souleyez" / ".setup_prompted"

    # Skip if already prompted
    if marker_file.exists():
        return

    # Skip if running the setup command itself
    if len(sys.argv) > 1 and sys.argv[1] in ("setup", "--version", "--help"):
        return

    try:
        from souleyez.utils.tool_checker import get_tool_stats

        installed, total = get_tool_stats()

        # If less than 3 tools installed, prompt user
        if installed < 3:
            click.echo()
            click.secho("=" * 60, fg="cyan")
            click.secho("  FIRST RUN DETECTED", fg="cyan", bold=True)
            click.secho("=" * 60, fg="cyan")
            click.echo()
            click.echo(
                f"  SoulEyez wraps 40+ pentesting tools, but only {installed}/{total}"
            )
            click.echo("  tools are currently installed on your system.")
            click.echo()
            click.echo("  Run the setup wizard to install tools like nmap, sqlmap,")
            click.echo("  gobuster, metasploit, and more.")
            click.echo()

            if click.confirm("  Run setup wizard now?", default=True):
                click.echo()
                # Create marker before running setup
                marker_file.parent.mkdir(parents=True, exist_ok=True)
                marker_file.touch()

                # Import and run setup
                from souleyez.ui.tool_setup import run_tool_setup

                run_tool_setup(check_only=False, install_all=False)
                sys.exit(0)
            else:
                click.echo()
                click.echo("  Skipped. Run 'souleyez setup' anytime to install tools.")
                click.echo()

        # Create marker file so we don't prompt again
        marker_file.parent.mkdir(parents=True, exist_ok=True)
        marker_file.touch()

    except Exception:
        # Don't block CLI if check fails
        pass


def _check_privileged_tools():
    """Check if privileged tools need sudoers configuration."""
    import subprocess

    # Skip if running setup or help commands
    if len(sys.argv) > 1 and sys.argv[1] in ("setup", "--version", "--help"):
        return

    marker_file = Path.home() / ".souleyez" / ".sudoers_declined"

    # Skip if user previously declined
    if marker_file.exists():
        return

    # Check if nmap is installed and needs configuration
    nmap_path = shutil.which("nmap")
    if not nmap_path:
        return

    # Check if passwordless sudo already works
    # First clear any cached sudo credentials so we test the actual config
    try:
        subprocess.run(["sudo", "-k"], capture_output=True, timeout=5)
        result = subprocess.run(
            ["sudo", "-n", nmap_path, "--version"], capture_output=True, timeout=5
        )
        if result.returncode == 0:
            return  # Already configured
    except Exception:
        pass  # Need to configure

    # Prompt user
    click.echo()
    click.secho("=" * 60, fg="yellow")
    click.secho("  PRIVILEGED SCAN SETUP NEEDED", fg="yellow", bold=True)
    click.secho("=" * 60, fg="yellow")
    click.echo()
    click.echo("  Some nmap scans (SYN, UDP, OS detection) require root.")
    click.echo("  SoulEyez can configure passwordless sudo so these work")
    click.echo("  automatically.")
    click.echo()

    if click.confirm("  Configure now?", default=True):
        click.echo()
        username = getpass.getuser()
        sudoers_file = "/etc/sudoers.d/nmap"
        sudoers_line = f"{username} ALL=(ALL) NOPASSWD: {nmap_path}"

        try:
            import subprocess

            # Use printf to ensure newline at end (required by sudoers parser)
            # echo should add newline but some environments strip it
            cmd = f"printf '%s\\n' '{sudoers_line}' | sudo tee {sudoers_file} > /dev/null && sudo chmod 0440 {sudoers_file}"
            proc = subprocess.run(cmd, shell=True, timeout=60)  # nosec B602

            if proc.returncode == 0:
                click.secho("  ✓ Configured! Privileged scans now work.", fg="green")
            else:
                click.secho(
                    "  ✗ Failed to configure. Run 'souleyez setup --fix-permissions'",
                    fg="red",
                )
        except Exception as e:
            click.secho(f"  ✗ Error: {e}", fg="red")
        click.echo()
    else:
        # Remember they declined
        marker_file.parent.mkdir(parents=True, exist_ok=True)
        marker_file.touch()
        click.echo()
        click.echo("  Skipped. Run 'souleyez setup --fix-permissions' anytime.")
        click.echo()


@click.group()
@click.version_option(version="3.0.6")
def cli():
    """SoulEyez - AI-Powered Pentesting Platform by CyberSoul Security"""
    from souleyez.log_config import init_logging

    init_logging()

    # Initialize auth system for CLI commands
    try:
        from souleyez.auth import init_auth
        from souleyez.storage.database import get_db

        init_auth(get_db().db_path)
    except Exception:
        pass  # Auth not required for all commands (e.g., --help, --version)

    # Check for system prerequisites
    _check_prerequisites()

    # Check for first run and prompt setup if needed
    _check_first_run_setup()

    # Check if privileged tools need configuration
    _check_privileged_tools()

    # Ensure user has local copy of wordlists
    try:
        from souleyez.wordlists import ensure_user_wordlists

        ensure_user_wordlists()
    except ImportError:
        pass


@cli.command()
def interactive():
    """Launch interactive tool selection menu."""
    run_interactive_menu()


@cli.command()
@click.option(
    "--check", "-c", is_flag=True, help="Only check tool status, don't install"
)
@click.option(
    "--install-all", "-a", is_flag=True, help="Install all missing tools automatically"
)
@click.option(
    "--fix-permissions",
    is_flag=True,
    help="Configure tools for privileged operations (nmap, responder)",
)
def setup(check, install_all, fix_permissions):
    """Install and configure pentesting tools for your system.

    This command detects your Linux distribution and helps install
    the pentesting tools that SoulEyez integrates with.

    On Ubuntu, tools not available via apt are installed using:
    - pipx (for Python tools like theHarvester, NetExec)
    - snap (for enum4linux)
    - Official installers (for Metasploit)
    - Go install (for nuclei, ffuf)

    Examples:
        souleyez setup              # Interactive setup wizard
        souleyez setup --check      # Just show tool status
        souleyez setup -a           # Install all missing tools
        souleyez setup --fix-permissions  # Enable privileged scans
    """
    if fix_permissions:
        _fix_tool_permissions()
        return
    from souleyez.ui.tool_setup import run_tool_setup

    run_tool_setup(check_only=check, install_all=install_all)


# Privileged tools configuration - binary tools
PRIVILEGED_BINARY_TOOLS = ["nmap"]

# Privileged tools configuration - script-based tools
PRIVILEGED_SCRIPT_TOOLS = {
    "responder": {
        "interpreter": "/usr/bin/python3",
        "script_paths": [
            "/usr/share/responder/Responder.py",
            "/opt/Responder/Responder.py",
            str(Path.home() / "tools/Responder/Responder.py"),
        ],
        "description": "LLMNR/NBT-NS credential capture",
    }
}


def _find_script_path(script_paths: list) -> str:
    """Find the first existing script path from a list of candidates."""
    for path in script_paths:
        if Path(path).exists():
            return path
    return None


def _fix_tool_permissions():
    """Configure passwordless sudo for privileged tools."""
    import subprocess

    click.echo()
    click.echo(click.style("  PRIVILEGED TOOL SETUP", bold=True, fg="cyan"))
    click.echo("  " + "─" * 50)
    click.echo()
    click.echo("  Configuring passwordless sudo for security tools.")
    click.echo("  (Required for SYN scans, UDP scans, credential capture)")
    click.echo()

    username = getpass.getuser()
    binary_tools_to_fix = []
    binary_tools_already_fixed = []
    binary_tools_not_installed = []
    script_tools_to_fix = []
    script_tools_already_fixed = []
    script_tools_not_installed = []

    # Check binary tools
    for tool_name in PRIVILEGED_BINARY_TOOLS:
        tool_path = shutil.which(tool_name)
        if not tool_path:
            binary_tools_not_installed.append(tool_name)
            continue

        # Check if passwordless sudo already works
        try:
            subprocess.run(["sudo", "-k"], capture_output=True, timeout=5)
            result = subprocess.run(
                ["sudo", "-n", tool_path, "--version"], capture_output=True, timeout=5
            )
            if result.returncode == 0:
                binary_tools_already_fixed.append(tool_name)
            else:
                binary_tools_to_fix.append((tool_name, tool_path))
        except Exception:
            binary_tools_to_fix.append((tool_name, tool_path))

    # Check script-based tools
    for tool_name, tool_info in PRIVILEGED_SCRIPT_TOOLS.items():
        script_path = _find_script_path(tool_info["script_paths"])
        if not script_path:
            script_tools_not_installed.append(tool_name)
            continue

        interpreter = tool_info["interpreter"]
        try:
            subprocess.run(["sudo", "-k"], capture_output=True, timeout=5)
            result = subprocess.run(
                ["sudo", "-n", interpreter, script_path, "--help"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                script_tools_already_fixed.append(tool_name)
            else:
                script_tools_to_fix.append(
                    (tool_name, interpreter, script_path, tool_info["description"])
                )
        except Exception:
            script_tools_to_fix.append(
                (tool_name, interpreter, script_path, tool_info["description"])
            )

    # Show status
    click.echo("  " + click.style("STATUS:", bold=True))
    click.echo()

    for name in binary_tools_already_fixed:
        click.echo(f"    {click.style('✓', fg='green')} {name} - already configured")

    for name in script_tools_already_fixed:
        click.echo(f"    {click.style('✓', fg='green')} {name} - already configured")

    for name in binary_tools_not_installed:
        click.echo(
            f"    {click.style('○', fg='yellow')} {name} - not installed (skipping)"
        )

    for name in script_tools_not_installed:
        click.echo(
            f"    {click.style('○', fg='yellow')} {name} - not installed (skipping)"
        )

    for name, _ in binary_tools_to_fix:
        click.echo(f"    {click.style('✗', fg='red')} {name} - needs configuration")

    for name, _, _, _ in script_tools_to_fix:
        click.echo(f"    {click.style('✗', fg='red')} {name} - needs configuration")

    click.echo()

    if not binary_tools_to_fix and not script_tools_to_fix:
        click.echo(
            click.style("  All installed tools are already configured!", fg="green")
        )
        return

    click.echo("  This requires sudo to configure /etc/sudoers.d/")
    click.echo()

    if not click.confirm("  Proceed?", default=True):
        click.echo("  Cancelled.")
        return

    click.echo()

    # Configure binary tools
    for tool_name, tool_path in binary_tools_to_fix:
        sudoers_file = f"/etc/sudoers.d/{tool_name}"
        sudoers_line = f"{username} ALL=(ALL) NOPASSWD: {tool_path}"

        click.echo(f"  Configuring {tool_name}...")

        try:
            cmd = f"printf '%s\\n' '{sudoers_line}' | sudo tee {sudoers_file} > /dev/null && sudo chmod 0440 {sudoers_file}"
            proc = subprocess.run(cmd, shell=True, timeout=60)  # nosec B602

            if proc.returncode == 0:
                click.echo(f"    {click.style('✓', fg='green')} {tool_name} configured")
            else:
                click.echo(f"    {click.style('✗', fg='red')} Failed to configure")
        except subprocess.TimeoutExpired:
            click.echo(f"    {click.style('✗', fg='red')} sudo timed out")
        except Exception as e:
            click.echo(f"    {click.style('✗', fg='red')} Error: {e}")

    # Configure script-based tools
    for tool_name, interpreter, script_path, description in script_tools_to_fix:
        sudoers_file = f"/etc/sudoers.d/souleyez-{tool_name}"
        sudoers_line = f"{username} ALL=(ALL) NOPASSWD: {interpreter} {script_path} *"

        click.echo(f"  Configuring {tool_name}...")

        try:
            cmd = f"printf '%s\\n' '{sudoers_line}' | sudo tee {sudoers_file} > /dev/null && sudo chmod 0440 {sudoers_file}"
            proc = subprocess.run(cmd, shell=True, timeout=60)  # nosec B602

            if proc.returncode == 0:
                click.echo(f"    {click.style('✓', fg='green')} {tool_name} configured")
            else:
                click.echo(f"    {click.style('✗', fg='red')} Failed to configure")
        except subprocess.TimeoutExpired:
            click.echo(f"    {click.style('✗', fg='red')} sudo timed out")
        except Exception as e:
            click.echo(f"    {click.style('✗', fg='red')} Error: {e}")

    click.echo()
    click.echo(
        click.style("  Done! Privileged scans now work automatically.", fg="green")
    )


@cli.command()
@click.option(
    "--follow", "-f", type=int, default=None, help="Follow live output of job ID"
)
@click.option(
    "--refresh",
    "-r",
    type=int,
    default=15,
    help="Refresh interval in seconds (default: 15)",
)
@require_password
def dashboard(follow, refresh):
    """Launch live dashboard with real-time job status and findings."""
    run_dashboard(follow_job_id=follow, refresh_interval=refresh)


@cli.group()
def engagement():
    """Engagement management - organize your penetration testing engagements."""
    pass


@engagement.command("create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Engagement description")
def engagement_create(name, description):
    """Create a new engagement."""
    em = EngagementManager()
    try:
        eng_id = em.create(name, description)
        click.echo(f"✓ Created engagement '{name}' (id={eng_id})")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@engagement.command("list")
def engagement_list():
    """List all engagements."""
    em = EngagementManager()
    engagements = em.list()
    current = em.get_current()

    if not engagements:
        click.echo(
            "No engagements found. Create one with: souleyez engagement create <name>"
        )
        return

    click.echo("\n" + "=" * 80)
    click.echo("ENGAGEMENTS")
    click.echo("=" * 80)

    for eng in engagements:
        marker = "* " if current and eng["id"] == current["id"] else "  "
        stats = em.stats(eng["id"])
        click.echo(
            f"{marker}{eng['name']:<20} | Hosts: {stats['hosts']:>3} | Services: {stats['services']:>3} | Findings: {stats['findings']:>3}"
        )
        if eng.get("description"):
            click.echo(f"  └─ {eng['description']}")

    click.echo("=" * 80)
    if current:
        click.echo(f"Current: {current['name']}")
    click.echo()


@engagement.command("use")
@click.argument("name")
def engagement_use(name):
    """Switch to an engagement."""
    em = EngagementManager()
    if em.set_current(name):
        click.echo(f"✓ Switched to workspace '{name}'")
    else:
        click.echo(f"✗ Workspace '{name}' not found", err=True)
        click.echo("Available engagements:")
        for eng in em.list():
            click.echo(f"  - {eng['name']}")


@engagement.command("current")
def engagement_current():
    """Show current engagement."""
    em = EngagementManager()
    current = em.get_current()

    if not current:
        click.echo("No engagement selected")
        return

    stats = em.stats(current["id"])

    click.echo("\n" + "=" * 60)
    click.echo(f"Current Engagement: {current['name']}")
    click.echo("=" * 60)
    click.echo(f"Description: {current.get('description', 'N/A')}")
    click.echo(f"Created: {current.get('created_at', 'N/A')}")
    click.echo()
    click.echo("Statistics:")
    click.echo(f"  Hosts:     {stats['hosts']}")
    click.echo(f"  Services:  {stats['services']}")
    click.echo(f"  Findings:  {stats['findings']}")
    click.echo("=" * 60 + "\n")


@engagement.command("delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def engagement_delete(name, force):
    """Delete an engagement and all its data."""
    em = EngagementManager()
    eng = em.get(name)

    if not eng:
        click.echo(f"✗ Workspace '{name}' not found", err=True)
        return

    if not force:
        stats = em.stats(eng["id"])
        click.echo(f"\nWarning: This will delete engagement '{name}' and:")
        click.echo(f"  - {stats['hosts']} hosts")
        click.echo(f"  - {stats['services']} services")
        click.echo(f"  - {stats['findings']} findings")

        if not click.confirm("\nAre you sure?"):
            click.echo("Cancelled")
            return

    if em.delete(name):
        click.echo(f"✓ Deleted workspace '{name}'")
    else:
        click.echo(f"✗ Error deleting workspace", err=True)


@engagement.command("delete-all")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.option(
    "--keep-current", is_flag=True, help="Keep the currently active engagement"
)
def engagement_delete_all(force, keep_current):
    """Delete all engagements (except optionally the current one)."""
    em = EngagementManager()
    all_engagements = em.list()

    if not all_engagements:
        click.echo("No engagements to delete")
        return

    # Get current engagement if we're keeping it
    current = em.get_current() if keep_current else None

    # Filter engagements to delete
    to_delete = []
    for eng in all_engagements:
        if keep_current and current and eng["id"] == current["id"]:
            continue
        to_delete.append(eng)

    if not to_delete:
        click.echo("No engagements to delete")
        return

    # Show what will be deleted
    click.echo(f"\n⚠️  Warning: This will delete {len(to_delete)} engagement(s):")
    for eng in to_delete[:10]:  # Show first 10
        click.echo(f"  - {eng['name']}")

    if len(to_delete) > 10:
        click.echo(f"  ... and {len(to_delete) - 10} more")

    if keep_current and current:
        click.echo(f"\n✓ Will keep current engagement: {current['name']}")

    # Confirmation
    if not force:
        click.echo()
        if not click.confirm(f"Delete {len(to_delete)} engagement(s)?", default=False):
            click.echo("Cancelled")
            return

    # Delete engagements
    deleted = 0
    failed = 0

    click.echo()
    with click.progressbar(to_delete, label="Deleting engagements") as bar:
        for eng in bar:
            if em.delete(eng["name"]):
                deleted += 1
            else:
                failed += 1

    click.echo()
    click.echo(f"✓ Deleted {deleted} engagement(s)")
    if failed > 0:
        click.echo(f"✗ Failed to delete {failed} engagement(s)", err=True)


# Register engagement team subcommand
from souleyez.commands.engagement import team

engagement.add_command(team)

# Register audit commands
from souleyez.commands.audit import audit

cli.add_command(audit)


# ============================================================================
# SCOPE MANAGEMENT
# ============================================================================


@cli.group()
def scope():
    """Engagement scope management - define and enforce target boundaries."""
    pass


@scope.command("add")
@click.argument("engagement_name")
@click.option("--cidr", help="Add CIDR range (e.g., 192.168.1.0/24)")
@click.option("--domain", help="Add domain pattern (e.g., *.example.com)")
@click.option("--url", help="Add URL (e.g., https://app.example.com)")
@click.option("--hostname", help="Add specific hostname or IP")
@click.option("--exclude", is_flag=True, help="Add as exclusion (deny rule)")
@click.option(
    "--description", "-d", default="", help="Description for this scope entry"
)
def scope_add(engagement_name, cidr, domain, url, hostname, exclude, description):
    """Add a scope entry to an engagement."""
    from souleyez.security.scope_validator import ScopeManager

    em = EngagementManager()
    eng = em.get(engagement_name)
    if not eng:
        click.echo(f"Error: Engagement '{engagement_name}' not found", err=True)
        return

    manager = ScopeManager()

    # Determine scope type and value
    if cidr:
        scope_type, value = "cidr", cidr
    elif domain:
        scope_type, value = "domain", domain
    elif url:
        scope_type, value = "url", url
    elif hostname:
        scope_type, value = "hostname", hostname
    else:
        click.echo(
            "Error: Must specify one of --cidr, --domain, --url, or --hostname",
            err=True,
        )
        return

    try:
        scope_id = manager.add_scope(
            engagement_id=eng["id"],
            scope_type=scope_type,
            value=value,
            is_excluded=exclude,
            description=description,
        )
        action = "exclusion" if exclude else "scope entry"
        click.echo(f"Added {action}: {scope_type}={value} (id={scope_id})")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)


@scope.command("list")
@click.argument("engagement_name")
def scope_list(engagement_name):
    """List scope entries for an engagement."""
    from souleyez.security.scope_validator import ScopeManager, ScopeValidator

    em = EngagementManager()
    eng = em.get(engagement_name)
    if not eng:
        click.echo(f"Error: Engagement '{engagement_name}' not found", err=True)
        return

    manager = ScopeManager()
    validator = ScopeValidator(eng["id"])
    entries = manager.list_scope(eng["id"])
    enforcement = validator.get_enforcement_mode()

    click.echo(f"\nScope for '{engagement_name}' (enforcement: {enforcement})")
    click.echo("=" * 70)

    if not entries:
        click.echo("No scope entries defined (all targets allowed)")
        return

    click.echo(f"{'ID':<5} {'Type':<10} {'Value':<35} {'Excluded':<10}")
    click.echo("-" * 70)

    for entry in entries:
        excluded = "EXCLUDE" if entry.get("is_excluded") else ""
        click.echo(
            f"{entry['id']:<5} {entry['scope_type']:<10} {entry['value']:<35} {excluded:<10}"
        )
        if entry.get("description"):
            click.echo(f"      {entry['description']}")

    click.echo()


@scope.command("remove")
@click.argument("engagement_name")
@click.argument("scope_id", type=int)
def scope_remove(engagement_name, scope_id):
    """Remove a scope entry by ID."""
    from souleyez.security.scope_validator import ScopeManager

    em = EngagementManager()
    eng = em.get(engagement_name)
    if not eng:
        click.echo(f"Error: Engagement '{engagement_name}' not found", err=True)
        return

    manager = ScopeManager()
    if manager.remove_scope(scope_id):
        click.echo(f"Removed scope entry {scope_id}")
    else:
        click.echo(f"Error: Failed to remove scope entry {scope_id}", err=True)


@scope.command("enforcement")
@click.argument("engagement_name")
@click.argument("mode", type=click.Choice(["off", "warn", "block"]))
def scope_enforcement(engagement_name, mode):
    """Set enforcement mode for an engagement.

    Modes:
      off   - No scope validation (default)
      warn  - Allow out-of-scope targets but log warning
      block - Reject jobs targeting out-of-scope hosts
    """
    from souleyez.security.scope_validator import ScopeManager

    em = EngagementManager()
    eng = em.get(engagement_name)
    if not eng:
        click.echo(f"Error: Engagement '{engagement_name}' not found", err=True)
        return

    manager = ScopeManager()
    if manager.set_enforcement(eng["id"], mode):
        click.echo(f"Enforcement mode set to '{mode}' for '{engagement_name}'")
    else:
        click.echo("Error: Failed to set enforcement mode", err=True)


@scope.command("validate")
@click.argument("engagement_name")
@click.argument("target")
def scope_validate(engagement_name, target):
    """Test if a target is in scope."""
    from souleyez.security.scope_validator import ScopeValidator

    em = EngagementManager()
    eng = em.get(engagement_name)
    if not eng:
        click.echo(f"Error: Engagement '{engagement_name}' not found", err=True)
        return

    validator = ScopeValidator(eng["id"])
    result = validator.validate_target(target)

    if result.is_in_scope:
        click.echo(f"IN SCOPE: {target}")
        if result.matched_entry:
            click.echo(f"  Matched: {result.matched_entry.get('value')}")
    else:
        click.echo(f"OUT OF SCOPE: {target}")
        click.echo(f"  Reason: {result.reason}")

    click.echo(f"  Enforcement: {validator.get_enforcement_mode()}")


@scope.command("revalidate")
@click.argument("engagement_name")
def scope_revalidate(engagement_name):
    """Revalidate scope status for all hosts in an engagement."""
    from souleyez.storage.hosts import HostManager

    em = EngagementManager()
    eng = em.get(engagement_name)
    if not eng:
        click.echo(f"Error: Engagement '{engagement_name}' not found", err=True)
        return

    hm = HostManager()
    result = hm.revalidate_scope_status(eng["id"])

    click.echo(f"Revalidated hosts for '{engagement_name}':")
    click.echo(f"  Updated: {result['updated']}")
    click.echo(f"  In scope: {result['in_scope']}")
    click.echo(f"  Out of scope: {result['out_of_scope']}")


@scope.command("log")
@click.argument("engagement_name")
@click.option("--limit", "-n", default=50, help="Number of entries to show")
def scope_log(engagement_name, limit):
    """Show scope validation audit log."""
    from souleyez.security.scope_validator import ScopeManager

    em = EngagementManager()
    eng = em.get(engagement_name)
    if not eng:
        click.echo(f"Error: Engagement '{engagement_name}' not found", err=True)
        return

    manager = ScopeManager()
    log_entries = manager.get_validation_log(eng["id"], limit)

    click.echo(f"\nScope validation log for '{engagement_name}' (last {limit})")
    click.echo("=" * 80)

    if not log_entries:
        click.echo("No validation log entries")
        return

    click.echo(f"{'Time':<20} {'Target':<25} {'Result':<12} {'Action':<10}")
    click.echo("-" * 80)

    for entry in log_entries:
        timestamp = entry.get("created_at", "")[:19]  # Trim to datetime
        target = entry.get("target", "")[:24]
        result = entry.get("validation_result", "")
        action = entry.get("action_taken", "")
        click.echo(f"{timestamp:<20} {target:<25} {result:<12} {action:<10}")


@cli.group()
def jobs():
    """Background job management."""
    pass


@jobs.command("enqueue")
@click.argument("tool")
@click.argument("target")
@click.option("--args", "-a", default="", help="Tool arguments (space-separated)")
@click.option("--label", "-l", default="", help="Job label")
def jobs_enqueue(tool, target, args, label):
    """Enqueue a background job."""
    args_list = args.split() if args else []

    try:
        job_id = enqueue_job(tool, target, args_list, label)
        click.echo(f"✓ Enqueued job {job_id}: {tool} {target}")
        click.echo(f"  Monitor: souleyez jobs get {job_id}")
        click.echo(f"  Tail log: souleyez jobs tail {job_id}")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@jobs.command("list")
@click.option("--limit", "-n", default=20, help="Number of jobs to show")
@click.option("--status", "-s", default=None, help="Filter by status")
def jobs_list(limit, status):
    """List background jobs."""
    jobs_data = list_jobs(limit=limit)

    if status:
        jobs_data = [j for j in jobs_data if j.get("status") == status]

    if not jobs_data:
        click.echo("No jobs found")
        return

    click.echo("\n" + "=" * 100)
    click.echo(
        f"{'ID':<5} {'Tool':<12} {'Target':<25} {'Status':<10} {'Label':<20} {'Created':<20}"
    )
    click.echo("=" * 100)

    for job in jobs_data:
        status_val = job.get("status", "N/A")

        # Color code status
        if status_val == "done":
            status_str = click.style(f"{status_val:<10}", fg="green")
        elif status_val == "running":
            status_str = click.style(f"{status_val:<10}", fg="yellow")
        elif status_val in ("error", "failed"):
            status_str = click.style(f"{status_val:<10}", fg="red")
        elif status_val == "killed":
            status_str = click.style(f"{status_val:<10}", fg="magenta")
        else:
            status_str = f"{status_val:<10}"

        click.echo(
            f"{job['id']:<5} "
            f"{job.get('tool', 'N/A'):<12} "
            f"{job.get('target', 'N/A')[:24]:<25} "
            f"{status_str} "
            f"{job.get('label', '')[:19]:<20} "
            f"{job.get('created_at', 'N/A'):<20}"
        )

    click.echo("=" * 100 + "\n")


@jobs.command("get")
@click.argument("job_id", type=int)
def jobs_get(job_id):
    """Get job details."""
    job = get_job(job_id)

    if not job:
        click.echo(f"✗ Job {job_id} not found", err=True)
        return

    click.echo("\n" + "=" * 60)
    click.echo(f"Job {job_id}")
    click.echo("=" * 60)
    click.echo(f"Tool:       {job.get('tool', 'N/A')}")
    click.echo(f"Target:     {job.get('target', 'N/A')}")
    click.echo(f"Args:       {' '.join(job.get('args', []))}")
    click.echo(f"Label:      {job.get('label', 'N/A')}")
    click.echo(f"Status:     {job.get('status', 'N/A')}")
    click.echo(f"Created:    {job.get('created_at', 'N/A')}")
    click.echo(f"Started:    {job.get('started_at', 'N/A')}")
    click.echo(f"Finished:   {job.get('finished_at', 'N/A')}")
    click.echo(f"Log:        {job.get('log', 'N/A')}")

    if job.get("error"):
        click.echo(f"Error:      {job['error']}")

    click.echo("=" * 60 + "\n")


@jobs.command("show")
@click.argument("job_id", type=int)
def jobs_show(job_id):
    """Show job details and log output (alias for get + tail)."""
    import os

    job = get_job(job_id)

    if not job:
        click.echo(f"✗ Job {job_id} not found", err=True)
        return

    # Show job details
    click.echo("\n" + "=" * 70)
    click.echo(f"JOB #{job_id}")
    click.echo("=" * 70)
    click.echo(f"Tool:       {job.get('tool', 'N/A')}")
    click.echo(f"Target:     {job.get('target', 'N/A')}")
    click.echo(f"Args:       {' '.join(job.get('args', []))}")
    if job.get("label"):
        click.echo(f"Label:      {job['label']}")
    click.echo(f"Status:     {job.get('status', 'N/A')}")
    click.echo(f"Created:    {job.get('created_at', 'N/A')}")
    if job.get("started_at"):
        click.echo(f"Started:    {job['started_at']}")
    if job.get("finished_at"):
        click.echo(f"Finished:   {job['finished_at']}")

    if job.get("error"):
        click.echo(f"Error:      {job['error']}")

    click.echo()

    # Show log output
    log_path = job.get("log")
    if log_path and os.path.exists(log_path):
        click.echo(click.style("LOG OUTPUT:", bold=True, fg="cyan"))
        click.echo("-" * 70)

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Show last 100 lines
            lines = content.split("\n")
            if len(lines) > 100:
                click.echo(f"... (showing last 100 of {len(lines)} lines)\n")
                lines = lines[-100:]

            for line in lines:
                click.echo(line)

        except Exception as e:
            click.echo(click.style(f"Error reading log: {e}", fg="red"))
    else:
        click.echo(click.style("No log file available", fg="yellow"))

    click.echo("\n" + "=" * 70 + "\n")


@jobs.command("tail")
@click.argument("job_id", type=int)
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
def jobs_tail(job_id, follow):
    """Tail job log file."""
    import subprocess

    job = get_job(job_id)

    if not job:
        click.echo(f"✗ Job {job_id} not found", err=True)
        return

    log_path = job.get("log")

    if not log_path or not os.path.exists(log_path):
        click.echo(f"✗ Log file not found: {log_path}", err=True)
        return

    try:
        if follow:
            subprocess.run(["tail", "-f", log_path])
        else:
            subprocess.run(["tail", "-30", log_path])
    except KeyboardInterrupt:
        pass
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@jobs.command("kill")
@click.argument("job_id", type=int)
@click.option("--force", "-f", is_flag=True, help="Force kill (SIGKILL)")
def jobs_kill(job_id, force):
    """Kill a running job."""
    from souleyez.engine.background import kill_job

    job = get_job(job_id)

    if not job:
        click.echo(f"✗ Job {job_id} not found", err=True)
        return

    status = job.get("status")

    # Allow killing queued, running, and error jobs
    if status not in ["queued", "running", "error"]:
        click.echo(f"✗ Job {job_id} cannot be killed (status: {status})", err=True)
        return

    if kill_job(job_id):
        if status == "queued":
            click.secho(f"✓ Job {job_id} removed from queue", fg="green")
        elif status == "error":
            click.secho(f"✓ Job {job_id} marked as killed", fg="green")
        else:
            click.secho(f"✓ Job {job_id} killed successfully", fg="green")
    else:
        click.echo(f"✗ Failed to kill job {job_id}", err=True)


@jobs.command("sanitize")
@click.argument("job_id", type=int, required=False)
@click.option("--all", is_flag=True, help="Sanitize all job logs")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be redacted without modifying logs"
)
def jobs_sanitize(job_id, all, dry_run):
    """Sanitize job logs by redacting credentials."""
    from souleyez.engine.log_sanitizer import LogSanitizer
    from souleyez.storage.crypto import CryptoManager

    crypto_mgr = CryptoManager()
    if not crypto_mgr.is_enabled():
        click.secho("⚠️  Warning: Encryption is not enabled.", fg="yellow")
        click.echo(
            "   Sanitization is primarily useful when encryption is enabled to prevent"
        )
        click.echo("   plaintext credentials in logs while encrypted in database.")
        if not click.confirm("Continue anyway?"):
            return

    if all:
        jobs_to_sanitize = list_jobs(limit=10000)
        if not jobs_to_sanitize:
            click.echo("No jobs found")
            return

        click.echo(f"Found {len(jobs_to_sanitize)} job(s)")

        if not dry_run and not click.confirm(
            f"Sanitize logs for all {len(jobs_to_sanitize)} jobs?"
        ):
            return
    elif job_id:
        job = get_job(job_id)
        if not job:
            click.echo(f"✗ Job {job_id} not found", err=True)
            return
        jobs_to_sanitize = [job]
    else:
        click.echo("Error: Specify --all or provide a job ID", err=True)
        click.echo("Usage: souleyez jobs sanitize <job_id>")
        click.echo("       souleyez jobs sanitize --all")
        return

    sanitized_count = 0
    redacted_count = 0

    for job in jobs_to_sanitize:
        jid = job["id"]
        log_path = job.get("log")

        if not log_path or not os.path.exists(log_path):
            continue

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                original = f.read()

            if not LogSanitizer.contains_credentials(original):
                continue

            sanitized = LogSanitizer.sanitize(original)

            if original == sanitized:
                continue

            summary = LogSanitizer.get_redaction_summary(original, sanitized)

            if dry_run:
                click.echo(f"Job {jid}: {summary}")
                redacted_count += 1
            else:
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(sanitized)
                click.secho(f"✓ Job {jid}: {summary}", fg="green")
                sanitized_count += 1

        except Exception as e:
            click.echo(f"✗ Job {jid}: Failed - {e}", err=True)

    if dry_run:
        click.echo(f"\n{redacted_count} job log(s) contain credentials (dry-run)")
    else:
        click.secho(f"\n✓ Sanitized {sanitized_count} job log(s)", fg="green")


@jobs.command("reparse")
@click.argument("job_id", type=int, required=False)
@click.option("--all", is_flag=True, help="Reparse all completed jobs")
@click.option("--tool", "-t", default=None, help="Filter by tool type")
@click.option("--chain", is_flag=True, help="Re-evaluate chain rules after reparsing")
def jobs_reparse(job_id, all, tool, chain):
    """Reparse completed job results to update database and status.

    Useful for applying new parsing logic to old jobs. This will:
    - Re-run the parser on existing log files
    - Update findings/credentials in database
    - Update job status (e.g., no_results -> done if data found)
    - Optionally re-trigger chain rules with --chain
    """
    from souleyez.engine.result_handler import reparse_job

    if all:
        jobs_to_reparse = list_jobs(limit=10000)
        if not jobs_to_reparse:
            click.echo("No jobs found")
            return

        # Filter by status and optionally by tool
        # Include no_results since that's what we're trying to fix
        jobs_to_reparse = [
            j
            for j in jobs_to_reparse
            if j.get("status") in ("done", "error", "no_results")
        ]
        if tool:
            jobs_to_reparse = [j for j in jobs_to_reparse if j.get("tool") == tool]

        if not jobs_to_reparse:
            filter_msg = f" for tool '{tool}'" if tool else ""
            click.echo(f"No completed jobs found{filter_msg}")
            return

        click.echo(f"Found {len(jobs_to_reparse)} job(s)")

        if not click.confirm(f"Reparse {len(jobs_to_reparse)} job(s)?"):
            return
    elif job_id:
        job = get_job(job_id)
        if not job:
            click.echo(f"✗ Job {job_id} not found", err=True)
            return

        if job.get("status") not in ("done", "error", "no_results"):
            click.echo(
                f"✗ Job {job_id} is not completed (status: {job.get('status')})",
                err=True,
            )
            return

        jobs_to_reparse = [job]
    else:
        click.echo("Error: Specify --all or provide a job ID", err=True)
        click.echo("Usage: souleyez jobs reparse <job_id>")
        click.echo("       souleyez jobs reparse --all")
        click.echo("       souleyez jobs reparse --all --tool enum4linux")
        return

    parsed_count = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0

    for job in jobs_to_reparse:
        jid = job["id"]
        tool_name = job.get("tool", "unknown")
        old_status = job.get("status")

        try:
            result = reparse_job(jid)

            if not result.get("success"):
                msg = result.get("message", "Unknown error")
                if "No parser" in msg:
                    click.echo(f"  Job {jid} ({tool_name}): No parser available")
                    skipped_count += 1
                else:
                    click.secho(f"✗ Job {jid} ({tool_name}): {msg}", fg="red")
                    error_count += 1
            else:
                # Show what was parsed
                parse_result = result.get("parse_result", {})
                new_status = result.get("new_status")
                summary = []

                if parse_result.get("hosts_added", 0) > 0:
                    summary.append(f"{parse_result['hosts_added']} hosts")
                if parse_result.get("osint_added", 0) > 0:
                    summary.append(f"{parse_result['osint_added']} OSINT records")
                if parse_result.get("findings_added", 0) > 0:
                    summary.append(f"{parse_result['findings_added']} findings")
                if parse_result.get("credentials_added", 0) > 0:
                    summary.append(f"{parse_result['credentials_added']} credentials")
                if parse_result.get("users_found", 0) > 0:
                    summary.append(f"{parse_result['users_found']} users")
                if parse_result.get("shares_found", 0) > 0:
                    summary.append(f"{parse_result['shares_found']} shares")

                summary_str = ", ".join(summary) if summary else "parsed"

                # Highlight status changes
                if old_status != new_status:
                    click.secho(
                        f"✓ Job {jid} ({tool_name}): {summary_str} [{old_status} → {new_status}]",
                        fg="green",
                    )
                    updated_count += 1
                else:
                    click.secho(f"✓ Job {jid} ({tool_name}): {summary_str}", fg="green")
                parsed_count += 1

                # Re-evaluate chain rules if requested
                if chain and parse_result:
                    try:
                        from souleyez.core.tool_chaining import ToolChaining

                        crm = ToolChaining()
                        chain_job_ids = crm.auto_chain(
                            job=job, parse_results=parse_result
                        )
                        if chain_job_ids:
                            click.secho(
                                f"  → Chained {len(chain_job_ids)} job(s): {chain_job_ids}",
                                fg="cyan",
                            )
                    except Exception as chain_err:
                        click.secho(f"  → Chain error: {chain_err}", fg="yellow")

        except Exception as e:
            click.secho(f"✗ Job {jid} ({tool_name}): Failed - {e}", fg="red")
            error_count += 1

    click.echo(f"\n{'=' * 60}")
    click.secho(f"✓ Reparsed: {parsed_count}", fg="green")
    if updated_count > 0:
        click.secho(f"  Status updated: {updated_count}", fg="cyan")
    if skipped_count > 0:
        click.echo(f"  Skipped: {skipped_count}")
    if error_count > 0:
        click.secho(f"✗ Errors: {error_count}", fg="red")
    click.echo("=" * 60)


@cli.group()
def worker():
    """Background worker management."""
    pass


@worker.command("start")
@click.option("--fg", is_flag=True, help="Run in foreground")
def worker_start(fg):
    """Start the background worker."""
    if fg:
        click.echo("Starting worker in foreground (Ctrl+C to stop)...")
        try:
            worker_loop()
        except KeyboardInterrupt:
            click.echo("\nWorker stopped")
    else:
        start_worker(detach=True)
        click.echo("✓ Background worker started")
        click.echo("  Logs: tail -f data/logs/worker.log")


@worker.command("status")
def worker_status():
    """Check worker status."""
    import subprocess

    try:
        # Use pgrep to find worker_loop processes (more reliable than ps + grep)
        result = subprocess.run(
            ["pgrep", "-f", "worker_loop"], capture_output=True, text=True
        )

        if result.returncode == 0 and result.stdout.strip():
            # Found worker processes
            pids = result.stdout.strip().split("\n")
            click.secho(
                f"✓ Worker is running ({len(pids)} process{'es' if len(pids) > 1 else ''}):",
                fg="green",
            )
            for pid in pids:
                click.echo(f"  PID {pid}: background worker")
        else:
            click.echo("✗ Worker is not running")
            click.echo("  Start with: souleyez worker start")
    except FileNotFoundError:
        # pgrep not available, fall back to ps
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            worker_procs = []
            for line in result.stdout.split("\n"):
                if "worker_loop" in line and "grep" not in line:
                    worker_procs.append(line)

            if worker_procs:
                click.secho("✓ Worker is running:", fg="green")
                for proc in worker_procs:
                    parts = proc.split()
                    if len(parts) >= 2:
                        click.echo(f"  PID {parts[1]}: background worker")
            else:
                click.echo("✗ Worker is not running")
                click.echo("  Start with: souleyez worker start")
        except Exception as e:
            click.echo(f"✗ Error checking status: {e}", err=True)
    except Exception as e:
        click.echo(f"✗ Error checking status: {e}", err=True)


@cli.command("plugins")
def list_plugins():
    """List available plugins."""
    try:
        from souleyez.engine.loader import discover_plugins

        plugins = discover_plugins()

        if not plugins:
            click.echo("No plugins found")
            return

        click.echo("\n" + "=" * 80)
        click.echo("AVAILABLE PLUGINS")
        click.echo("=" * 80)

        for key, plugin in sorted(plugins.items()):
            name = getattr(plugin, "name", "Unknown")
            category = getattr(plugin, "category", "misc")
            click.echo(f"{key:<15} | {name:<30} | {category}")

        click.echo("=" * 80)
        click.echo(f"Total: {len(plugins)} plugins\n")
    except Exception as e:
        click.echo(f"✗ Error loading plugins: {e}", err=True)


# ==================== DATABASE COMMANDS ====================


@cli.group()
def db():
    """Database management commands."""
    pass


@db.command("migrate")
def db_migrate():
    """Apply pending database migrations."""
    from souleyez.storage.database import get_db
    from souleyez.storage.migrations.migration_manager import MigrationManager

    click.echo()
    click.echo(click.style("🔄 DATABASE MIGRATION", bold=True, fg="cyan"))
    click.echo("=" * 80)

    # Get database path
    db_instance = get_db()
    db_path = db_instance.db_path

    # Run migrations
    manager = MigrationManager(db_path)
    applied = manager.migrate()

    click.echo()


@db.command("status")
def db_status():
    """Show database migration status."""
    from souleyez.storage.database import get_db
    from souleyez.storage.migrations.migration_manager import MigrationManager

    # Get database path
    db_instance = get_db()
    db_path = db_instance.db_path

    # Show status
    manager = MigrationManager(db_path)
    manager.status()


@db.command("encrypt")
def db_encrypt():
    """Encrypt all plaintext credentials in the database."""
    import getpass

    from souleyez.storage.credentials import CredentialsManager
    from souleyez.storage.crypto import get_crypto_manager

    crypto = get_crypto_manager()

    # Check if encryption is enabled
    if not crypto.is_encryption_enabled():
        click.echo(click.style("✗ Encryption is not enabled", fg="red"))
        click.echo("Run 'souleyez interactive' to set up encryption first")
        return

    # Unlock crypto if needed
    if not crypto.is_unlocked():
        click.echo(click.style("🔐 Master password required", fg="cyan"))
        password = getpass.getpass("Enter master password: ")
        try:
            crypto.unlock(password)
            click.echo(click.style("✓ Unlocked", fg="green"))
        except Exception as e:
            click.echo(click.style(f"✗ Failed to unlock: {e}", fg="red"))
            return

    # Encrypt all credentials
    cm = CredentialsManager()
    result = cm.encrypt_all_unencrypted()

    if "error" in result:
        click.echo(click.style(f"✗ {result['error']}", fg="red"))
        return

    click.echo()
    click.echo(click.style("✓ Encryption complete", fg="green", bold=True))
    click.echo(f"  • Encrypted: {result.get('encrypted', 0)} credentials")
    click.echo(f"  • Already encrypted: {result.get('skipped', 0)} credentials")
    click.echo(f"  • Total: {result.get('total', 0)} credentials")
    click.echo()


def _run_doctor(fix=False, verbose=False):
    """Run diagnostics (callable from CLI or interactive UI)."""
    import shutil
    import sqlite3

    click.echo()
    click.echo(click.style("🩺 SoulEyez Doctor", fg="cyan", bold=True))
    click.echo(click.style("=" * 50, fg="cyan"))
    click.echo()

    issues = []
    warnings = []

    def check_pass(msg):
        click.echo(click.style(f"  ✓ {msg}", fg="green"))

    def check_fail(msg, fix_cmd=None):
        click.echo(click.style(f"  ✗ {msg}", fg="red"))
        issues.append((msg, fix_cmd))

    def check_warn(msg, suggestion=None):
        click.echo(click.style(f"  ⚠ {msg}", fg="yellow"))
        warnings.append((msg, suggestion))

    # Section 1: Python Environment
    click.echo(click.style("Python Environment", bold=True))
    import sys

    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    if sys.version_info >= (3, 8):
        check_pass(f"Python {python_version}")
    else:
        check_fail(
            f"Python {python_version} (need 3.8+)", "Install Python 3.8 or newer"
        )

    # Check required packages
    required_packages = ["click", "rich", "wcwidth"]
    for pkg in required_packages:
        try:
            __import__(pkg)
            if verbose:
                check_pass(f"Package: {pkg}")
        except ImportError:
            check_fail(f"Missing package: {pkg}", f"pip install {pkg}")

    click.echo()

    # Section 2: Data Directory
    click.echo(click.style("Data Directory", bold=True))
    data_dir = Path.home() / ".souleyez"
    if data_dir.exists():
        check_pass(f"Data directory: {data_dir}")
    else:
        check_warn(
            f"Data directory missing: {data_dir}", "Will be created on first run"
        )

    # Check database
    db_path = data_dir / "souleyez.db"
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM engagements")
            count = cursor.fetchone()[0]
            conn.close()
            check_pass(f"Database OK ({count} engagements)")
        except Exception as e:
            check_fail(
                f"Database error: {str(e)[:40]}", "Run: souleyez setup --repair-db"
            )
    else:
        check_warn("No database yet", "Will be created on first run")

    click.echo()

    # Section 3: Essential Tools
    click.echo(click.style("Essential Tools", bold=True))
    essential_tools = {
        "nmap": "sudo apt install nmap",
        "git": "sudo apt install git",
        "curl": "sudo apt install curl",
    }

    for tool, install_cmd in essential_tools.items():
        if shutil.which(tool):
            check_pass(tool)
        else:
            check_fail(f"Missing: {tool}", install_cmd)

    click.echo()

    # Section 4: Pentesting Tools
    click.echo(click.style("Pentesting Tools", bold=True))
    # Use the same tool checker as the setup wizard for consistency
    from souleyez.utils.tool_checker import get_tool_stats

    installed, total = get_tool_stats()

    if installed == total:
        check_pass(f"All {total} tools installed")
    elif installed > 0:
        check_warn(f"{installed}/{total} tools installed", "Run: souleyez setup")
    else:
        check_fail("No pentesting tools installed", "souleyez setup")

    click.echo()

    # Section 5: Configuration
    click.echo(click.style("Configuration", bold=True))
    config_file = data_dir / "config.json"
    if config_file.exists():
        try:
            import json

            with open(config_file) as f:
                config = json.load(f)
            check_pass("Config file valid")

            # Check AI providers
            ai_config = config.get("ai", {})
            provider = ai_config.get("provider", "")
            has_ollama = provider == "ollama" or ai_config.get("ollama_model")
            has_claude = ai_config.get("claude_api_key") or ai_config.get(
                "anthropic_api_key"
            )
            has_openai = ai_config.get("openai_api_key")
            if has_ollama or has_claude or has_openai:
                provider_name = provider or (
                    "ollama" if has_ollama else "claude" if has_claude else "openai"
                )
                check_pass(f"AI provider: {provider_name}")
        except Exception as e:
            check_fail(f"Config error: {str(e)[:30]}", "Check ~/.souleyez/config.json")
    else:
        check_warn("No config file", "Run souleyez interactive to create")

    click.echo()

    # Section 6: System Configuration
    click.echo(click.style("System Configuration", bold=True))

    # Check sudoers files for proper format (trailing newline)
    sudoers_dir = Path("/etc/sudoers.d")
    sudoers_tools = ["nmap", "souleyez-responder"]  # Tools we configure in sudoers
    for tool in sudoers_tools:
        sudoers_file = sudoers_dir / tool
        if sudoers_file.exists():
            try:
                # Check file size vs expected content
                content = sudoers_file.read_bytes()
                if content and not content.endswith(b"\n"):
                    check_fail(
                        f"Sudoers {tool}: missing newline",
                        f"echo '' | sudo tee -a /etc/sudoers.d/{tool}",
                    )
                elif verbose:
                    check_pass(f"Sudoers {tool}: OK")
            except PermissionError:
                if verbose:
                    click.echo(
                        click.style(
                            f"  - Sudoers {tool}: need sudo to verify",
                            fg="bright_black",
                        )
                    )

    # Check PATH for common tool directories
    path_dirs = os.environ.get("PATH", "").split(":")
    pipx_bin = str(Path.home() / ".local" / "bin")
    go_bin = str(Path.home() / "go" / "bin")

    # Detect shell config file (zsh for Kali, bash for others)
    shell = os.environ.get("SHELL", "/bin/bash")
    shell_rc = "~/.zshrc" if "zsh" in shell else "~/.bashrc"

    if pipx_bin in path_dirs:
        if verbose:
            check_pass("PATH includes ~/.local/bin (pipx)")
    else:
        if Path(pipx_bin).exists() and any(Path(pipx_bin).iterdir()):
            check_warn(
                "~/.local/bin not in PATH",
                f'Add to {shell_rc}: export PATH="$HOME/.local/bin:$PATH"',
            )

    if go_bin in path_dirs:
        if verbose:
            check_pass("PATH includes ~/go/bin")
    else:
        if Path(go_bin).exists() and any(Path(go_bin).iterdir()):
            check_warn(
                "~/go/bin not in PATH",
                f'Add to {shell_rc}: export PATH="$HOME/go/bin:$PATH"',
            )

    # Check database is writable
    if db_path.exists():
        try:
            if os.access(db_path, os.W_OK):
                if verbose:
                    check_pass("Database writable")
            else:
                check_fail("Database not writable", f"chmod 600 {db_path}")
        except Exception:
            pass

    # Check background worker
    try:
        import subprocess

        result = subprocess.run(
            ["pgrep", "-f", "souleyez worker"], capture_output=True, timeout=5
        )
        if result.returncode == 0:
            check_pass("Background worker running")
        else:
            check_warn(
                "Background worker not running",
                "souleyez dashboard (starts automatically)",
            )
    except Exception:
        pass

    # Check for orphaned pending chains
    try:
        from souleyez.core.pending_chains import _read_chains, purge_orphaned_chains

        chains = _read_chains()
        if chains:
            # Check which are orphaned
            db_path = os.path.join(data_dir, "souleyez.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT id FROM engagements")
            valid_ids = {row[0] for row in cursor.fetchall()}
            conn.close()

            orphaned = [
                c
                for c in chains
                if c.get("engagement_id") not in valid_ids
                and c.get("engagement_id") is not None
            ]
            if orphaned:
                check_warn(
                    f"Orphaned pending chains: {len(orphaned)}",
                    "Run with --fix to clean up",
                )
                if fix:
                    purged = purge_orphaned_chains()
                    if purged > 0:
                        check_pass(f"Cleaned up {purged} orphaned chains")
            elif verbose:
                check_pass(f"Pending chains OK ({len(chains)} active)")
        elif verbose:
            check_pass("No pending chains")
    except Exception:
        pass

    # Check dashboard cache status
    if verbose:
        try:
            from souleyez.ui.dashboard import _HEADER_CACHE_TTL, _header_cache

            cache_entries = len(_header_cache)
            if cache_entries > 0:
                check_pass(
                    f"Dashboard cache: {cache_entries} entries (TTL: {_HEADER_CACHE_TTL}s)"
                )
            else:
                check_pass("Dashboard cache: empty (will populate on first load)")
        except Exception:
            pass

        try:
            from souleyez.intelligence.exploit_suggestions import (
                _CACHE_TIMEOUT,
                _SUGGESTION_CACHE,
            )

            cache_entries = len(_SUGGESTION_CACHE)
            if cache_entries > 0:
                check_pass(
                    f"Exploit suggestions cache: {cache_entries} entries (TTL: {_CACHE_TIMEOUT}s)"
                )
            else:
                check_pass(
                    "Exploit suggestions cache: empty (will populate on first load)"
                )
        except Exception:
            pass

    click.echo()

    # Section 7: MSF Database (if msfconsole available)
    if shutil.which("msfconsole"):
        click.echo(click.style("Metasploit", bold=True))

        # Use comprehensive msfdb status check
        from souleyez.utils.tool_checker import check_msfdb_status

        db_status = check_msfdb_status()

        if db_status["initialized"] and db_status["running"]:
            check_pass("MSF database initialized and running")
        elif db_status["initialized"] and not db_status["running"]:
            check_warn(
                "MSF database initialized but PostgreSQL not running",
                "sudo systemctl start postgresql",
            )
        elif not db_status["initialized"]:
            # Fall back to file check in case msfdb status failed
            msf_db = Path.home() / ".msf4" / "database.yml"
            system_msf_db = Path("/usr/share/metasploit-framework/config/database.yml")
            if msf_db.exists() or system_msf_db.exists():
                check_warn(
                    "MSF database config exists but status unclear",
                    db_status.get("message", "Run: sudo msfdb status"),
                )
            else:
                check_fail("MSF database not initialized", "msfdb init")

        if verbose:
            click.echo(
                click.style(
                    f"    Status: {db_status.get('message', 'Unknown')}",
                    fg="bright_black",
                )
            )

        # Check if root has access (for sudo msfconsole)
        # Skip if we can't access /root (not an error, just needs sudo to check)
        root_msf_db = Path("/root/.msf4/database.yml")
        try:
            if root_msf_db.exists():
                check_pass("Sudo MSF access configured")
            else:
                check_warn(
                    "Sudo MSF may not connect to DB",
                    "sudo cp ~/.msf4/database.yml /root/.msf4/",
                )
        except PermissionError:
            # Can't check without sudo - not a problem, just skip
            if verbose:
                click.echo(
                    click.style(
                        "  - Sudo MSF config: need sudo to verify", fg="bright_black"
                    )
                )

        click.echo()

    # Summary
    click.echo(click.style("=" * 50, fg="cyan"))
    if not issues and not warnings:
        click.echo(
            click.style(
                "✓ All checks passed! SoulEyez is healthy.", fg="green", bold=True
            )
        )
    else:
        if issues:
            click.echo(
                click.style(f"\n{len(issues)} issue(s) found:", fg="red", bold=True)
            )
            for issue, fix_cmd in issues:
                click.echo(f"  • {issue}")
                if fix_cmd:
                    click.echo(click.style(f"    Fix: {fix_cmd}", fg="cyan"))

        if warnings:
            click.echo(
                click.style(f"\n{len(warnings)} warning(s):", fg="yellow", bold=True)
            )
            for warning, suggestion in warnings:
                click.echo(f"  • {warning}")
                if suggestion:
                    click.echo(click.style(f"    Suggestion: {suggestion}", fg="cyan"))

    # Auto-fix if requested
    if fix and issues:
        click.echo()
        click.echo(click.style("Attempting auto-fix...", fg="cyan", bold=True))
        # TODO: Implement auto-fix for common issues
        click.echo(
            "Auto-fix not yet implemented. Please run the suggested commands manually."
        )

    click.echo()

    return len(issues), len(warnings)


@cli.command()
@click.option("--fix", is_flag=True, help="Attempt to automatically fix issues")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed diagnostic info")
def doctor(fix, verbose):
    """Diagnose and fix common SoulEyez issues.

    Checks for:
    - Missing dependencies and tools
    - Database connectivity
    - Configuration problems
    - Permission issues
    - Environment setup
    """
    _run_doctor(fix=fix, verbose=verbose)


@cli.command()
def tutorial():
    """Interactive guided tutorial for first-time users.

    Walks you through:
    - Creating your first engagement
    - Running a basic scan
    - Viewing results
    - Understanding the dashboard
    """
    from souleyez.ui.tutorial import run_tutorial

    run_tutorial()


@cli.command("install-desktop")
@click.option("--remove", is_flag=True, help="Remove the desktop shortcut")
def install_desktop(remove):
    """Install SoulEyez desktop shortcut in Applications menu.

    Creates a .desktop file so SoulEyez appears in your
    Applications > Security menu with its icon.
    """
    import shutil
    from importlib import resources

    applications_dir = Path.home() / ".local" / "share" / "applications"
    icons_dir = Path.home() / ".local" / "share" / "icons"
    desktop_file = applications_dir / "souleyez.desktop"
    icon_dest = icons_dir / "souleyez.png"

    if remove:
        # Remove desktop shortcut
        removed = False
        if desktop_file.exists():
            desktop_file.unlink()
            click.echo(click.style("  Removed desktop shortcut", fg="green"))
            removed = True
        if icon_dest.exists():
            icon_dest.unlink()
            click.echo(click.style("  Removed icon", fg="green"))
            removed = True
        if removed:
            click.echo(
                click.style("\nSoulEyez removed from Applications menu.", fg="cyan")
            )
        else:
            click.echo(click.style("No desktop shortcut found.", fg="yellow"))
        return

    click.echo(
        click.style("\nInstalling SoulEyez desktop shortcut...\n", fg="cyan", bold=True)
    )

    # Create directories
    applications_dir.mkdir(parents=True, exist_ok=True)
    icons_dir.mkdir(parents=True, exist_ok=True)

    # Find and copy icon
    try:
        # Try importlib.resources first (Python 3.9+)
        try:
            from importlib.resources import files

            icon_source = files("souleyez.assets").joinpath("souleyez-icon.png")
            with open(icon_source, "rb") as src:
                icon_data = src.read()
        except (ImportError, TypeError, FileNotFoundError):
            # Fallback: find icon relative to this file
            icon_source = Path(__file__).parent / "assets" / "souleyez-icon.png"
            with open(icon_source, "rb") as src:
                icon_data = src.read()

        with open(icon_dest, "wb") as dst:
            dst.write(icon_data)
        click.echo(click.style("  Installed icon", fg="green"))
    except Exception as e:
        click.echo(click.style(f"  Warning: Could not copy icon: {e}", fg="yellow"))
        icon_dest = "utilities-terminal"  # Fallback to system icon

    # Create .desktop file
    desktop_content = f"""[Desktop Entry]
Name=SoulEyez
Comment=AI-Powered Penetration Testing Platform
Exec=souleyez interactive
Icon={icon_dest}
Terminal=true
Type=Application
Categories=Security;System;Network;
Keywords=pentest;security;hacking;nmap;metasploit;
"""

    desktop_file.write_text(desktop_content)
    click.echo(click.style("  Created desktop entry", fg="green"))

    # Update desktop database (optional, may not be available)
    try:
        import subprocess

        subprocess.run(
            ["update-desktop-database", str(applications_dir)],
            capture_output=True,
            check=False,
        )
    except Exception:
        pass  # Not critical if this fails

    click.echo()
    click.echo(
        click.style("SoulEyez added to Applications menu!", fg="green", bold=True)
    )
    click.echo()
    click.echo("You can find it under:")
    click.echo(click.style("  Applications > Security > SoulEyez", fg="cyan"))
    click.echo()
    click.echo("To remove: souleyez install-desktop --remove")


def main():
    """Main entry point."""
    cli()


@cli.command()
@click.option("--purge-data", is_flag=True, help="Remove all user data (~/.souleyez)")
@click.confirmation_option(prompt="Are you sure you want to uninstall SoulEyez?")
def uninstall(purge_data):
    """Uninstall SoulEyez and optionally remove all user data."""
    import shutil
    import signal
    import subprocess

    click.echo(click.style("\n🗑️  Uninstalling SoulEyez...", fg="yellow", bold=True))
    click.echo()

    # Stop background worker (both dev mode and CLI mode)
    click.echo("1. Stopping background worker...")
    try:
        subprocess.run(
            ["pkill", "-f", "souleyez.engine.background"],
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["pkill", "-f", "souleyez worker"], capture_output=True, check=False
        )
        click.echo(click.style("   ✓ Worker stopped", fg="green"))
    except Exception as e:
        click.echo(click.style(f"   ⚠ Could not stop worker: {e}", fg="yellow"))

    # Remove user data if requested
    if purge_data:
        click.echo("\n2. Removing user data...")
        data_dir = Path.home() / ".souleyez"
        if data_dir.exists():
            click.echo(
                click.style(f"   ⚠ WARNING: This will delete:", fg="yellow", bold=True)
            )
            click.echo(f"   • Database: {data_dir / 'souleyez.db'}")
            click.echo(f"   • Crypto keys: {data_dir / 'crypto.json'}")
            click.echo(f"   • Logs: {data_dir / 'souleyez.log'}")
            click.echo(f"   • All engagement data")
            click.echo()

            if click.confirm(
                click.style("   Delete ALL user data?", fg="red", bold=True)
            ):
                try:
                    shutil.rmtree(data_dir)
                    click.echo(click.style(f"   ✓ Removed {data_dir}", fg="green"))
                except Exception as e:
                    click.echo(click.style(f"   ✗ Error: {e}", fg="red"))
            else:
                click.echo(click.style("   → User data preserved", fg="cyan"))
        else:
            click.echo(click.style("   ℹ No user data found", fg="cyan"))
    else:
        click.echo(click.style("\n2. User data preserved in ~/.souleyez", fg="cyan"))
        click.echo("   • Your engagements and database are safe")
        click.echo("   • Reinstalling will restore access to your data")
        click.echo("   • To remove data: souleyez uninstall --purge-data")

    # Remove application with pipx
    click.echo("\n3. Removing application...")
    click.echo("   Run: pipx uninstall souleyez")
    click.echo()

    try:
        result = subprocess.run(
            ["pipx", "uninstall", "souleyez"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            click.echo(
                click.style("   ✓ SoulEyez uninstalled successfully", fg="green")
            )
        else:
            click.echo(
                click.style(
                    f"   ⚠ pipx uninstall returned: {result.stderr}", fg="yellow"
                )
            )
            click.echo("   You may need to run manually: pipx uninstall souleyez")
    except FileNotFoundError:
        click.echo(click.style("   ℹ pipx not found - uninstall manually", fg="cyan"))
        click.echo("   Run: pip uninstall souleyez")
    except Exception as e:
        click.echo(click.style(f"   ✗ Error: {e}", fg="red"))

    click.echo()
    if purge_data:
        click.echo(click.style("✓ SoulEyez completely removed", fg="green", bold=True))
    else:
        click.echo(
            click.style("✓ SoulEyez removed (data preserved)", fg="green", bold=True)
        )
    click.echo()


# Import and register auth commands (must be before if __name__ block)
from souleyez.commands.auth import login, logout, whoami

cli.add_command(login)
cli.add_command(logout)
cli.add_command(whoami)

# Import and register user management commands
from souleyez.commands.user import user

cli.add_command(user)

# Import and register license management commands
from souleyez.commands.license import license

cli.add_command(license)


if __name__ == "__main__":
    main()


# ==================== HOST COMMANDS ====================


@cli.group()
def hosts():
    """Host management commands."""
    pass


@hosts.command("list")
@click.option(
    "--engagement", "-w", default=None, help="Engagement name (default: current)"
)
@click.option("--all", "-a", is_flag=True, help="Show all hosts (including down hosts)")
@click.option("--status", "-s", default=None, help="Filter by status (up/down/unknown)")
def hosts_list(engagement, all, status):
    """List hosts in engagement (default: only live/up hosts)."""
    from souleyez.storage.hosts import HostManager

    em = EngagementManager()

    if engagement:
        eng = em.get(engagement)
        if not eng:
            click.echo(f"✗ Workspace '{engagement}' not found", err=True)
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo(
                "✗ No engagement selected. Use: souleyez engagement use <name>",
                err=True,
            )
            return

    hm = HostManager()
    all_hosts = hm.list_hosts(eng["id"])

    # Filter hosts
    if status:
        hosts = [h for h in all_hosts if h.get("status", "unknown") == status]
    elif not all:
        # Default: only show 'up' hosts
        hosts = [h for h in all_hosts if h.get("status", "unknown") == "up"]
    else:
        hosts = all_hosts

    if not hosts:
        filter_msg = (
            f" with status='{status}'" if status else " (live only)" if not all else ""
        )
        click.echo(f"No hosts found in workspace '{eng['name']}'{filter_msg}")
        return

    # Show filter info in header
    filter_info = ""
    if status:
        filter_info = f" (status={status})"
    elif not all:
        filter_info = " (live hosts only)"

    click.echo("\n" + "=" * 100)
    click.echo(f"HOSTS - Engagement: {eng['name']}{filter_info}")
    click.echo("=" * 100)
    click.echo(f"{'IP Address':<18} {'Hostname':<30} {'Status':<10} {'OS':<30}")
    click.echo("=" * 100)

    for host in hosts:
        click.echo(
            f"{host['ip_address']:<18} "
            f"{(host.get('hostname') or 'N/A')[:29]:<30} "
            f"{host.get('status', 'unknown'):<10} "
            f"{(host.get('os_name') or 'N/A')[:29]:<30}"
        )

    click.echo("=" * 100)
    click.echo(f"Total: {len(hosts)} hosts\n")


@hosts.command("add")
@click.argument("ip_address")
@click.option("--hostname", "-n", default=None, help="Hostname")
@click.option("--os", default=None, help="Operating system")
@click.option(
    "--status",
    "-s",
    default="up",
    type=click.Choice(["up", "down", "unknown"]),
    help="Host status",
)
@click.option(
    "--engagement", "-e", default=None, help="Engagement name (default: current)"
)
def hosts_add(ip_address, hostname, os, status, engagement):
    """Manually add a host to engagement."""
    from souleyez.storage.hosts import HostManager

    em = EngagementManager()

    if engagement:
        eng = em.get(engagement)
        if not eng:
            click.echo(f"✗ Engagement '{engagement}' not found", err=True)
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo(
                "✗ No engagement selected. Use: souleyez engagement use <name>",
                err=True,
            )
            return

    hm = HostManager()

    try:
        host_data = {"ip": ip_address, "hostname": hostname, "os": os, "status": status}
        host_id = hm.add_or_update_host(eng["id"], host_data)
        click.echo(
            f"✓ Added host {ip_address} to engagement '{eng['name']}' (id={host_id})"
        )
        if hostname:
            click.echo(f"  Hostname: {hostname}")
        if os:
            click.echo(f"  OS: {os}")
        click.echo(f"  Status: {status}")
    except Exception as e:
        click.echo(f"✗ Error adding host: {e}", err=True)


@hosts.command("show")
@click.argument("ip_address")
@click.option(
    "--engagement", "-w", default=None, help="Engagement name (default: current)"
)
def hosts_show(ip_address, engagement):
    """Show detailed host information."""
    from souleyez.storage.hosts import HostManager

    em = EngagementManager()

    if engagement:
        eng = em.get(engagement)
        if not eng:
            click.echo(f"✗ Workspace '{engagement}' not found", err=True)
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo("✗ No engagement selected", err=True)
            return

    hm = HostManager()
    host = hm.get_host_by_ip(eng["id"], ip_address)

    if not host:
        click.echo(
            f"✗ Host {ip_address} not found in workspace '{eng['name']}'", err=True
        )
        return

    services = hm.get_host_services(host["id"])

    click.echo("\n" + "=" * 80)
    click.echo(f"HOST: {host['ip_address']}")
    click.echo("=" * 80)
    click.echo(f"Hostname:     {host.get('hostname') or 'N/A'}")
    click.echo(f"Status:       {host.get('status', 'unknown')}")
    click.echo(f"OS:           {host.get('os_name') or 'N/A'}")
    click.echo(f"MAC:          {host.get('mac_address') or 'N/A'}")
    click.echo(f"First seen:   {host.get('created_at', 'N/A')}")
    click.echo(f"Last updated: {host.get('updated_at', 'N/A')}")

    click.echo("\n" + "-" * 80)
    click.echo(f"SERVICES ({len(services)})")
    click.echo("-" * 80)

    if services:
        click.echo(
            f"{'Port':<10} {'Protocol':<10} {'State':<10} {'Service':<20} {'Version':<30}"
        )
        click.echo("-" * 80)
        for svc in services:
            click.echo(
                f"{svc['port']:<10} "
                f"{svc['protocol']:<10} "
                f"{svc['state']:<10} "
                f"{(svc.get('service_name') or 'unknown')[:19]:<20} "
                f"{(svc.get('service_version') or 'N/A')[:29]:<30}"
            )
    else:
        click.echo("No services found")

    click.echo("=" * 80 + "\n")


@hosts.command("update")
@click.argument("ip_address")
@click.option(
    "--status",
    type=click.Choice(["active", "compromised", "offline", "up", "down"]),
    help="Host status",
)
@click.option(
    "--access-level",
    type=click.Choice(["none", "user", "admin", "root"]),
    help="Access level gained",
)
@click.option("--notes", help="Additional notes about the host")
@click.option(
    "--engagement", "-w", default=None, help="Engagement name (default: current)"
)
def hosts_update(ip_address, status, access_level, notes, engagement):
    """Update host status, access level, and notes."""
    from souleyez.storage.hosts import HostManager

    if not status and not access_level and notes is None:
        click.echo(
            "✗ Must provide at least one of --status, --access-level, or --notes",
            err=True,
        )
        return

    em = EngagementManager()

    if engagement:
        eng = em.get(engagement)
        if not eng:
            click.echo(f"✗ Workspace '{engagement}' not found", err=True)
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo("✗ No engagement selected", err=True)
            return

    hm = HostManager()
    host = hm.get_host_by_ip(eng["id"], ip_address)

    if not host:
        click.echo(
            f"✗ Host {ip_address} not found in workspace '{eng['name']}'", err=True
        )
        return

    success = hm.update_host_status(
        host["id"], status=status, access_level=access_level, notes=notes
    )

    if success:
        click.echo(click.style(f"✓ Host {ip_address} updated", fg="green"))
        if status:
            click.echo(f"  Status: {status}")
        if access_level:
            click.echo(f"  Access level: {access_level}")
        if notes:
            click.echo(f"  Notes: {notes}")
    else:
        click.echo(click.style(f"✗ Failed to update host {ip_address}", fg="red"))


# ==================== SERVICE COMMANDS ====================


@cli.group()
def services():
    """Service management commands."""
    pass


@services.command("add")
@click.argument("ip_address")
@click.argument("port", type=int)
@click.argument("protocol", type=click.Choice(["tcp", "udp"]))
@click.option("--service", "-s", default=None, help="Service name (e.g., ssh, http)")
@click.option("--version", "-v", default=None, help="Service version")
@click.option(
    "--state",
    default="open",
    type=click.Choice(["open", "closed", "filtered"]),
    help="Service state",
)
@click.option(
    "--engagement", "-e", default=None, help="Engagement name (default: current)"
)
def services_add(ip_address, port, protocol, service, version, state, engagement):
    """Manually add a service to a host."""
    from souleyez.storage.hosts import HostManager

    em = EngagementManager()

    if engagement:
        eng = em.get(engagement)
        if not eng:
            click.echo(f"✗ Engagement '{engagement}' not found", err=True)
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo(
                "✗ No engagement selected. Use: souleyez engagement use <name>",
                err=True,
            )
            return

    hm = HostManager()

    # Get or create host
    host = hm.get_host_by_ip(eng["id"], ip_address)
    if not host:
        # Create host first
        click.echo(f"Host {ip_address} not found, creating it...")
        host_data = {"ip": ip_address, "status": "up"}
        host_id = hm.add_or_update_host(eng["id"], host_data)
    else:
        host_id = host["id"]

    # Add service
    try:
        service_data = {
            "port": port,
            "protocol": protocol,
            "state": state,
            "service": service,
            "version": version,
        }
        service_id = hm.add_service(host_id, service_data)
        click.echo(
            f"✓ Added service {ip_address}:{port}/{protocol} to engagement '{eng['name']}' (id={service_id})"
        )
        if service:
            click.echo(f"  Service: {service}")
        if version:
            click.echo(f"  Version: {version}")
        click.echo(f"  State: {state}")
    except Exception as e:
        click.echo(f"✗ Error adding service: {e}", err=True)


@services.command("list")
@click.option(
    "--engagement", "-w", default=None, help="Engagement name (default: current)"
)
@click.option("--port", "-p", type=int, default=None, help="Filter by port")
def services_list(engagement, port):
    """List all services across all hosts."""
    from souleyez.storage.hosts import HostManager

    em = EngagementManager()

    if engagement:
        eng = em.get(engagement)
        if not eng:
            click.echo(f"✗ Workspace '{engagement}' not found", err=True)
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo("✗ No engagement selected", err=True)
            return

    hm = HostManager()

    # Get all hosts and their services
    hosts = hm.list_hosts(eng["id"])

    all_services = []
    for host in hosts:
        services = hm.get_host_services(host["id"])
        for svc in services:
            if port is None or svc["port"] == port:
                all_services.append(
                    {
                        "host_ip": host["ip_address"],
                        "host_name": host.get("hostname"),
                        **svc,
                    }
                )

    if not all_services:
        click.echo(f"No services found in workspace '{eng['name']}'")
        return

    click.echo("\n" + "=" * 120)
    click.echo(f"SERVICES - Engagement: {eng['name']}")
    if port:
        click.echo(f"Filtered by port: {port}")
    click.echo("=" * 120)
    click.echo(
        f"{'Host':<18} {'Port':<8} {'Proto':<8} {'State':<10} {'Service':<20} {'Version':<40}"
    )
    click.echo("=" * 120)

    for svc in sorted(all_services, key=lambda x: (x["host_ip"], x["port"])):
        click.echo(
            f"{svc['host_ip']:<18} "
            f"{svc['port']:<8} "
            f"{svc['protocol']:<8} "
            f"{svc['state']:<10} "
            f"{(svc.get('service_name') or 'unknown')[:19]:<20} "
            f"{(svc.get('service_version') or 'N/A')[:39]:<40}"
        )

    click.echo("=" * 120)
    click.echo(f"Total: {len(all_services)} services\n")


# ==================== FINDINGS COMMANDS ====================


@cli.group()
@require_password
def findings():
    """Findings/vulnerabilities management commands."""
    pass


@findings.command("list")
@click.option(
    "--engagement", "-w", default=None, help="Engagement name (default: current)"
)
@click.option(
    "--severity",
    "-s",
    default=None,
    help="Filter by severity (critical, high, medium, low, info)",
)
@click.option("--tool", "-t", default=None, help="Filter by tool")
@click.option("--host", "-h", default=None, help="Filter by host IP")
def findings_list(engagement, severity, tool, host):
    """List all findings in engagement."""
    from souleyez.storage.findings import FindingsManager

    em = EngagementManager()

    if engagement:
        eng = em.get(engagement)
        if not eng:
            click.echo(f"✗ Workspace '{engagement}' not found", err=True)
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo("✗ No engagement selected", err=True)
            return

    fm = FindingsManager()

    # Get host_id if filtering by host
    host_id = None
    if host:
        from souleyez.storage.hosts import HostManager

        hm = HostManager()
        host_obj = hm.get_host_by_ip(eng["id"], host)
        if not host_obj:
            click.echo(f"✗ Host {host} not found", err=True)
            return
        host_id = host_obj["id"]

    findings = fm.list_findings(
        eng["id"], host_id=host_id, severity=severity, tool=tool
    )

    if not findings:
        click.echo(f"No findings found in workspace '{eng['name']}'")
        return

    # Get severity color mapping
    severity_colors = {
        "critical": "red",
        "high": "red",
        "medium": "yellow",
        "low": "blue",
        "info": "white",
    }

    click.echo("\n" + "=" * 140)
    click.echo(f"FINDINGS - Engagement: {eng['name']}")
    if severity:
        click.echo(f"Filtered by severity: {severity}")
    if tool:
        click.echo(f"Filtered by tool: {tool}")
    click.echo("=" * 140)
    click.echo(
        f"{'ID':<6} {'Severity':<10} {'Host':<18} {'Port':<6} {'Tool':<10} {'Title':<80}"
    )
    click.echo("=" * 140)

    for finding in findings:
        sev_color = severity_colors.get(finding.get("severity", "info"), "white")
        click.echo(
            f"{finding['id']:<6} "
            f"{click.style(finding.get('severity', 'info').upper()[:9], fg=sev_color):<19} "
            f"{(finding.get('ip_address') or 'N/A')[:17]:<18} "
            f"{str(finding.get('port') or 'N/A')[:5]:<6} "
            f"{(finding.get('tool') or 'N/A')[:9]:<10} "
            f"{finding.get('title', '')[:79]:<80}"
        )

    click.echo("=" * 140)
    click.echo(f"Total: {len(findings)} findings\n")


@findings.command("show")
@click.argument("finding_id", type=int)
def findings_show(finding_id):
    """Show detailed finding information."""
    from souleyez.storage.findings import FindingsManager

    fm = FindingsManager()
    finding = fm.get_finding(finding_id)

    if not finding:
        click.echo(f"✗ Finding {finding_id} not found", err=True)
        return

    click.echo("\n" + "=" * 80)
    click.echo(f"FINDING #{finding['id']}")
    click.echo("=" * 80)
    click.echo(f"Severity:     {finding.get('severity', 'unknown').upper()}")
    click.echo(f"Type:         {finding.get('finding_type', 'N/A')}")
    click.echo(f"Tool:         {finding.get('tool', 'N/A')}")
    click.echo(f"Title:        {finding.get('title', 'N/A')}")
    click.echo(f"\nDescription:")
    click.echo(f"  {finding.get('description', 'N/A')}")

    if finding.get("path"):
        click.echo(f"\nPath:         {finding['path']}")

    if finding.get("port"):
        click.echo(f"Port:         {finding['port']}")

    if finding.get("refs"):
        click.echo(f"\nReference:    {finding['refs']}")

    click.echo(f"\nDiscovered:   {finding.get('created_at', 'N/A')}")
    click.echo("=" * 80 + "\n")


@findings.command("summary")
@click.option(
    "--engagement", "-w", default=None, help="Engagement name (default: current)"
)
def findings_summary(engagement):
    """Show findings summary by severity."""
    from souleyez.storage.findings import FindingsManager

    em = EngagementManager()

    if engagement:
        eng = em.get(engagement)
        if not eng:
            click.echo(f"✗ Workspace '{engagement}' not found", err=True)
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo("✗ No engagement selected", err=True)
            return

    fm = FindingsManager()
    summary = fm.get_findings_summary(eng["id"])

    total = sum(summary.values())

    click.echo("\n" + "=" * 60)
    click.echo(f"FINDINGS SUMMARY - Engagement: {eng['name']}")
    click.echo("=" * 60)
    click.echo(f"{'Severity':<15} {'Count':<10} {'Percentage':<15}")
    click.echo("=" * 60)

    for severity in ["critical", "high", "medium", "low", "info"]:
        count = summary.get(severity, 0)
        pct = (count / total * 100) if total > 0 else 0

        color = {
            "critical": "red",
            "high": "red",
            "medium": "yellow",
            "low": "blue",
            "info": "white",
        }.get(severity, "white")

        click.echo(
            f"{click.style(severity.upper(), fg=color):<24} "
            f"{count:<10} "
            f"{pct:.1f}%"
        )

    click.echo("=" * 60)
    click.echo(f"{'TOTAL':<15} {total}")
    click.echo("=" * 60 + "\n")


# ==================== OSINT COMMANDS ====================


@cli.group()
@require_password
def osint():
    """OSINT data management commands."""
    pass


@osint.command("list")
@click.option(
    "--engagement", "-w", default=None, help="Engagement name (default: current)"
)
@click.option(
    "--type", "-t", default=None, help="Filter by data type (email, host, ip, url, asn)"
)
@click.option("--source", "-s", default=None, help="Filter by source tool")
def osint_list(engagement, type, source):
    """List all OSINT data in engagement."""
    from souleyez.storage.osint import OsintManager

    em = EngagementManager()

    if engagement:
        eng = em.get(engagement)
        if not eng:
            click.echo(f"✗ Workspace '{engagement}' not found", err=True)
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo("✗ No engagement selected", err=True)
            return

    om = OsintManager()
    osint_data = om.list_osint_data(eng["id"], data_type=type, source=source)

    if not osint_data:
        click.echo(f"No OSINT data found in workspace '{eng['name']}'")
        return

    click.echo("\n" + "=" * 120)
    click.echo(f"OSINT DATA - Engagement: {eng['name']}")
    if type:
        click.echo(f"Filtered by type: {type}")
    if source:
        click.echo(f"Filtered by source: {source}")
    click.echo("=" * 120)
    click.echo(
        f"{'ID':<6} {'Type':<12} {'Source':<15} {'Value':<70} {'Discovered':<20}"
    )
    click.echo("=" * 120)

    for item in osint_data:
        click.echo(
            f"{item['id']:<6} "
            f"{(item.get('data_type') or 'N/A')[:11]:<12} "
            f"{(item.get('source') or 'N/A')[:14]:<15} "
            f"{item.get('value', '')[:69]:<70} "
            f"{item.get('created_at', 'N/A')[:19]:<20}"
        )

    click.echo("=" * 120)
    click.echo(f"Total: {len(osint_data)} entries\n")


@osint.command("summary")
@click.option(
    "--engagement", "-w", default=None, help="Engagement name (default: current)"
)
def osint_summary(engagement):
    """Show OSINT data summary by type."""
    from souleyez.storage.osint import OsintManager

    em = EngagementManager()

    if engagement:
        eng = em.get(engagement)
        if not eng:
            click.echo(f"✗ Workspace '{engagement}' not found", err=True)
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo("✗ No engagement selected", err=True)
            return

    om = OsintManager()
    summary = om.get_osint_summary(eng["id"])

    total = sum(summary.values())

    if total == 0:
        click.echo(f"No OSINT data found in workspace '{eng['name']}'")
        return

    click.echo("\n" + "=" * 60)
    click.echo(f"OSINT SUMMARY - Engagement: {eng['name']}")
    click.echo("=" * 60)
    click.echo(f"{'Type':<15} {'Count':<10} {'Percentage':<15}")
    click.echo("=" * 60)

    for data_type in sorted(summary.keys()):
        count = summary[data_type]
        pct = (count / total * 100) if total > 0 else 0

        click.echo(f"{data_type:<15} " f"{count:<10} " f"{pct:.1f}%")

    click.echo("=" * 60)
    click.echo(f"{'TOTAL':<15} {total}")
    click.echo("=" * 60 + "\n")


# ==================== WEB PATHS COMMANDS ====================


@cli.group()
def paths():
    """Web paths/directories management commands."""
    pass


@paths.command("list")
@click.option(
    "--engagement", "-w", default=None, help="Engagement name (default: current)"
)
@click.option(
    "--status", "-s", type=int, default=None, help="Filter by HTTP status code"
)
@click.option("--host", "-h", default=None, help="Filter by host IP or hostname")
def paths_list(engagement, status, host):
    """List discovered web paths."""
    from souleyez.storage.hosts import HostManager
    from souleyez.storage.web_paths import WebPathsManager

    em = EngagementManager()

    if engagement:
        eng = em.get(engagement)
        if not eng:
            click.echo(f"✗ Workspace '{engagement}' not found", err=True)
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo("✗ No engagement selected", err=True)
            return

    wpm = WebPathsManager()

    # Get host_id if filtering by host
    host_id = None
    if host:
        hm = HostManager()
        hosts = hm.list_hosts(eng["id"])
        for h in hosts:
            if h.get("hostname") == host or h.get("ip_address") == host:
                host_id = h["id"]
                break
        if not host_id:
            click.echo(f"✗ Host {host} not found", err=True)
            return

    # List paths
    if host_id:
        paths = wpm.list_web_paths(host_id=host_id, status_code=status)
    else:
        paths = wpm.list_web_paths(engagement_id=eng["id"], status_code=status)

    if not paths:
        click.echo(f"No web paths found in workspace '{eng['name']}'")
        return

    click.echo("\n" + "=" * 140)
    click.echo(f"WEB PATHS - Engagement: {eng['name']}")
    if status:
        click.echo(f"Filtered by status: {status}")
    if host:
        click.echo(f"Filtered by host: {host}")
    click.echo("=" * 140)
    click.echo(f"{'ID':<6} {'Status':<8} {'Size':<10} {'Host':<25} {'URL':<80}")
    click.echo("=" * 140)

    for path in paths:
        status_code = path.get("status_code", "N/A")
        # Color code status
        if status_code == 200:
            status_str = click.style(str(status_code), fg="green")
        elif 300 <= status_code < 400:
            status_str = click.style(str(status_code), fg="yellow")
        elif 400 <= status_code < 500:
            status_str = click.style(str(status_code), fg="red")
        else:
            status_str = str(status_code)

        host_info = path.get("hostname") or path.get("ip_address") or "N/A"

        click.echo(
            f"{path['id']:<6} "
            f"{status_str:<17} "  # Extra space for ANSI codes
            f"{str(path.get('content_length') or 'N/A')[:9]:<10} "
            f"{host_info[:24]:<25} "
            f"{path.get('url', '')[:79]:<80}"
        )

    click.echo("=" * 140)
    click.echo(f"Total: {len(paths)} paths\n")


@paths.command("summary")
@click.option(
    "--engagement", "-w", default=None, help="Engagement name (default: current)"
)
def paths_summary(engagement):
    """Show web paths summary by status code."""
    from souleyez.storage.web_paths import WebPathsManager

    em = EngagementManager()

    if engagement:
        eng = em.get(engagement)
        if not eng:
            click.echo(f"✗ Workspace '{engagement}' not found", err=True)
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo("✗ No engagement selected", err=True)
            return

    wpm = WebPathsManager()
    summary = wpm.get_paths_summary(eng["id"])

    total = sum(summary.values())

    if total == 0:
        click.echo(f"No web paths found in workspace '{eng['name']}'")
        return

    click.echo("\n" + "=" * 60)
    click.echo(f"WEB PATHS SUMMARY - Engagement: {eng['name']}")
    click.echo("=" * 60)
    click.echo(f"{'Status Code':<15} {'Count':<10} {'Percentage':<15}")
    click.echo("=" * 60)

    for status_code in sorted(
        summary.keys(), key=lambda x: int(x) if x.isdigit() else 999
    ):
        count = summary[status_code]
        pct = (count / total * 100) if total > 0 else 0

        # Color code
        status_int = int(status_code) if status_code.isdigit() else 0
        if status_int == 200:
            status_display = click.style(status_code, fg="green")
        elif 300 <= status_int < 400:
            status_display = click.style(status_code, fg="yellow")
        elif 400 <= status_int < 500:
            status_display = click.style(status_code, fg="red")
        else:
            status_display = status_code

        click.echo(
            f"{status_display:<24} "  # Extra space for ANSI
            f"{count:<10} "
            f"{pct:.1f}%"
        )

    click.echo("=" * 60)
    click.echo(f"{'TOTAL':<15} {total}")
    click.echo("=" * 60 + "\n")


# ==================== CREDENTIALS COMMANDS ====================


@cli.group()
def creds():
    """Credentials management - similar to MSF's creds command."""
    pass


@creds.command("add")
@click.argument("username")
@click.argument("password")
@click.option(
    "--service", "-s", default=None, help="Service type (ssh, smb, mysql, etc.)"
)
@click.option("--host", "-h", default=None, help="Host IP address")
@click.option("--port", "-p", type=int, default=None, help="Port number")
@click.option(
    "--status",
    default="untested",
    type=click.Choice(["valid", "invalid", "untested"]),
    help="Credential status",
)
@click.option(
    "--engagement", "-e", default=None, help="Engagement name (default: current)"
)
def creds_add(username, password, service, host, port, status, engagement):
    """Manually add credentials to engagement."""
    from souleyez.storage.credentials import CredentialsManager
    from souleyez.storage.hosts import HostManager

    em = EngagementManager()

    if engagement:
        eng = em.get(engagement)
        if not eng:
            click.echo(f"✗ Engagement '{engagement}' not found", err=True)
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo(
                "✗ No engagement selected. Use: souleyez engagement use <name>",
                err=True,
            )
            return

    # Get host_id if host specified
    host_id = None
    if host:
        hm = HostManager()
        host_obj = hm.get_host_by_ip(eng["id"], host)
        if not host_obj:
            # Create host if it doesn't exist
            click.echo(f"Host {host} not found, creating it...")
            host_data = {"ip": host, "status": "up"}
            host_id = hm.add_or_update_host(eng["id"], host_data)
        else:
            host_id = host_obj["id"]

    cm = CredentialsManager()

    try:
        cred_id = cm.add_credential(
            engagement_id=eng["id"],
            host_id=host_id,
            username=username,
            password=password,
            service=service,
            port=port,
            status=status,
            tool="manual",
        )
        click.echo(f"✓ Added credential to engagement '{eng['name']}' (id={cred_id})")
        click.echo(f"  Username: {username}")
        click.echo(f"  Password: {'*' * len(password)}")  # Hide password
        if service:
            click.echo(f"  Service: {service}")
        if host:
            click.echo(f"  Host: {host}")
        if port:
            click.echo(f"  Port: {port}")
        click.echo(f"  Status: {status}")
    except Exception as e:
        click.echo(f"✗ Error adding credential: {e}", err=True)


@creds.command("list")
@click.option(
    "--engagement", "-w", default=None, help="Engagement name (default: current)"
)
@click.option(
    "--service", "-s", default=None, help="Filter by service (ssh, smb, mysql, etc.)"
)
@click.option("--status", "-t", default=None, help="Filter by status (valid, untested)")
@click.option("--host", "-h", default=None, help="Filter by host IP")
def creds_list(engagement, service, status, host):
    """List all discovered credentials (similar to MSF's creds command)."""
    from souleyez.storage.credentials import CredentialsManager
    from souleyez.storage.hosts import HostManager

    # Unlock credentials if needed
    if not unlock_credentials_if_needed():
        return

    em = EngagementManager()

    if engagement:
        eng = em.get(engagement)
        if not eng:
            click.echo(f"✗ Workspace '{engagement}' not found", err=True)
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo("✗ No engagement selected", err=True)
            return

    cm = CredentialsManager()

    # Get host_id if filtering by host
    host_id = None
    if host:
        hm = HostManager()
        host_obj = hm.get_host_by_ip(eng["id"], host)
        if not host_obj:
            click.echo(f"✗ Host {host} not found", err=True)
            return
        host_id = host_obj["id"]

    creds = cm.list_credentials(
        eng["id"], host_id=host_id, service=service, status=status
    )

    if not creds:
        filter_msg = ""
        if service:
            filter_msg += f" (service={service})"
        if status:
            filter_msg += f" (status={status})"
        click.echo(f"No credentials found in workspace '{eng['name']}'{filter_msg}")
        return

    # Get stats
    stats = cm.get_stats(eng["id"])

    click.echo("\n" + "=" * 100)
    click.echo(f"CREDENTIALS - Engagement: {eng['name']}")
    if service or status or host:
        filters = []
        if service:
            filters.append(f"service={service}")
        if status:
            filters.append(f"status={status}")
        if host:
            filters.append(f"host={host}")
        click.echo(f"Filters: {', '.join(filters)}")
    click.echo("=" * 100)

    # Summary line
    click.echo(
        f"Total: {stats['total']}  |  "
        + click.style(f"Valid: {stats['valid']}", fg="green", bold=True)
        + f"  |  Usernames: {stats['users_only']}  |  Pairs: {stats['pairs']}"
    )
    click.echo()

    # Separate valid and untested
    valid_creds = [c for c in creds if c.get("status") == "valid"]
    untested_creds = [c for c in creds if c.get("status") != "valid"]

    # Show valid credentials
    if valid_creds:
        click.echo(
            click.style("VALID CREDENTIALS (Confirmed Working)", bold=True, fg="green")
        )
        click.echo()

        # Create Rich Table
        console = Console()
        table = DesignSystem.create_table()
        table.add_column("✓", style="green bold", width=3)
        table.add_column("Username", style="green bold", width=20)
        table.add_column("Password", style="green bold", width=20)
        table.add_column("Service", width=10)
        table.add_column("Host", width=18)
        table.add_column("Port", width=6)
        table.add_column("Tool", width=15)

        for cred in valid_creds:
            username = cred.get("username", "")[:19]
            password = cred.get("password", "")[:19]
            service_name = cred.get("service", "N/A")[:9]
            ip = cred.get("ip_address", "N/A")[:17]
            port = str(cred.get("port", "N/A"))[:5]
            tool_name = cred.get("tool", "N/A")[:14]

            table.add_row("✓", username, password, service_name, ip, port, tool_name)

        console.print(table)
        click.echo()

    # Show discovered usernames
    if untested_creds:
        click.echo(
            click.style(
                f"DISCOVERED USERNAMES ({len(untested_creds)} untested)",
                bold=True,
                fg="cyan",
            )
        )
        click.echo(DesignSystem.separator())

        # Group by service
        by_service = {}
        for cred in untested_creds:
            svc = cred.get("service", "unknown")
            if svc not in by_service:
                by_service[svc] = []
            by_service[svc].append(cred.get("username", ""))

        for svc, usernames in sorted(by_service.items()):
            user_list = ", ".join(sorted(usernames))
            click.echo(f"{svc.upper():<8} ({len(usernames):2}): {user_list}")

        click.echo(DesignSystem.separator())

    click.echo(f"\nTotal displayed: {len(creds)} credentials\n")


@creds.command("stats")
@click.option(
    "--engagement", "-w", default=None, help="Engagement name (default: current)"
)
def creds_stats(engagement):
    """Show credentials statistics."""
    from souleyez.storage.credentials import CredentialsManager

    em = EngagementManager()

    if engagement:
        eng = em.get(engagement)
        if not eng:
            click.echo(f"✗ Workspace '{engagement}' not found", err=True)
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo("✗ No engagement selected", err=True)
            return

    cm = CredentialsManager()
    stats = cm.get_stats(eng["id"])

    click.echo("\n" + "=" * 60)
    click.echo(f"CREDENTIALS STATISTICS - Engagement: {eng['name']}")
    click.echo("=" * 60)
    click.echo(f"Total Credentials:       {stats['total']}")
    click.echo(
        f"Valid (confirmed):       {click.style(str(stats['valid']), fg='green')}"
    )
    click.echo(f"Username-only:           {stats['users_only']}")
    click.echo(f"Password-only:           {stats['passwords_only']}")
    click.echo(f"Username:Password pairs: {stats['pairs']}")
    click.echo("=" * 60 + "\n")


@creds.command("update")
@click.argument("credential_id", type=int)
@click.option(
    "--status",
    type=click.Choice(["untested", "valid", "invalid"]),
    help="Credential status",
)
@click.option("--notes", help="Additional notes")
def creds_update(credential_id, status, notes):
    """Update credential status and notes."""
    from souleyez.storage.credentials import CredentialsManager

    if not status and notes is None:
        click.echo("✗ Must provide --status or --notes", err=True)
        return

    cm = CredentialsManager()

    try:
        success = cm.update_credential_status(credential_id, status=status, notes=notes)
        if success:
            click.echo(click.style(f"✓ Credential {credential_id} updated", fg="green"))
        else:
            click.echo(click.style(f"✗ Credential {credential_id} not found", fg="red"))
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))


@creds.command("cleanup")
@require_password
@click.option("--engagement", "-e", type=int, help="Engagement ID (default: all)")
@click.option(
    "--confirm",
    is_flag=True,
    default=False,
    help="Actually delete the garbage credentials",
)
@click.option(
    "--all",
    "-a",
    "show_all",
    is_flag=True,
    default=False,
    help="Show all garbage credentials (default: first 20)",
)
def creds_cleanup(engagement, confirm, show_all):
    """Remove garbage credentials (scanner artifacts, injection payloads).

    By default runs in dry-run mode to show what would be deleted.
    Use --confirm to actually delete the garbage entries.

    Examples:
        souleyez creds cleanup              # Preview what would be deleted
        souleyez creds cleanup --all        # Show all garbage credentials
        souleyez creds cleanup --confirm    # Actually delete garbage
        souleyez creds cleanup -e 5         # Preview for engagement 5 only
    """
    import re

    from souleyez.storage.credentials import CredentialsManager
    from souleyez.storage.engagements import EngagementManager

    def is_garbage_username(username: str) -> bool:
        """Check if username is scanner garbage."""
        if not username or len(username) > 100:
            return True

        username_lower = username.lower()

        # Scanner tool signatures
        scanner_patterns = [
            "netsparker",
            "burpsuite",
            "burp",
            "acunetix",
            "nikto",
            "sqlmap",
            "havij",
            "w3af",
            "owasp",
            "zap",
            "wvs",
        ]
        for pattern in scanner_patterns:
            if pattern in username_lower:
                return True

        # Template injection patterns
        injection_patterns = [
            "{{",
            "}}",
            "${",
            "}$",
            "<%",
            "%>",
            "{%",
            "%}",
            "sleep(",
            "benchmark(",
            "waitfor delay",
            "pg_sleep",
        ]
        for pattern in injection_patterns:
            if pattern in username_lower:
                return True

        # Path traversal patterns
        path_patterns = [
            "/etc/",
            "\\etc\\",
            "/passwd",
            "/shadow",
            "/windows/",
            "c:\\",
            ".asp",
            ".aspx",
            ".axd",
            ".php",
            ".jsp",
            ".pl",
            "../",
            "..\\",
            "file://",
            "php://",
            "data://",
            "::1/",
            "[::1]",
            "/elmah",
            "/trace",
            "127.0.0.1/",
        ]
        for pattern in path_patterns:
            if pattern in username_lower:
                return True

        # Command injection patterns
        cmd_patterns = [
            "& ping ",
            "| ping ",
            "; ping ",
            "ping -",
            "& whoami",
            "| whoami",
            "; whoami",
            "`whoami`",
            "$(whoami)",
            "cmd.exe",
            "/bin/sh",
            "& dir",
            "| dir",
            "; dir",
            "& ls",
            "| ls",
            "; ls",
            "nc -",
            "ncat ",
            "netcat ",
        ]
        for pattern in cmd_patterns:
            if pattern in username_lower:
                return True

        # SQL injection patterns
        sql_patterns = [
            "' or ",
            "' and ",
            "1=1",
            "1'='1",
            "' union ",
            "select ",
            "insert ",
            "update ",
            "delete ",
            "drop ",
            "concat(",
            "char(",
            "chr(",
            "0x00",
            "@@version",
        ]
        for pattern in sql_patterns:
            if pattern in username_lower:
                return True

        # URL encoding patterns
        if "%27" in username or "%22" in username or "%3c" in username_lower:
            return True

        # Hex patterns
        if re.search(r"0x[0-9a-f]{4,}", username_lower):
            return True

        # Starts/ends with injection chars
        injection_chars = ['"', "'", ";", "|", "&", "`", "(", ")", "<", ">"]
        if username[0] in injection_chars or username[-1] in injection_chars:
            return True

        # Too many special characters
        special_count = sum(1 for c in username if c in "{}[]()$%^&*|\\/<>\"`'")
        if special_count > 3:
            return True

        # Mostly digits and long
        if len(username) > 20:
            alnum_only = re.sub(r"[^a-zA-Z0-9]", "", username)
            if len(alnum_only) > 0:
                digit_ratio = sum(1 for c in alnum_only if c.isdigit()) / len(
                    alnum_only
                )
                if digit_ratio > 0.7:
                    return True

        return False

    cm = CredentialsManager()
    em = EngagementManager()

    # Get credentials (must decrypt to check actual usernames)
    if engagement:
        creds_list = cm.list_credentials_for_engagement(engagement, decrypt=True)
        eng_name = f"engagement {engagement}"
    else:
        # Get all engagements (unfiltered for cleanup operation)
        all_creds = []
        for eng in em.list(user_filtered=False):
            eng_creds = cm.list_credentials_for_engagement(eng["id"], decrypt=True)
            all_creds.extend(eng_creds)
        creds_list = all_creds
        eng_name = "all engagements"

    # Find garbage
    garbage = []
    for cred in creds_list:
        username = cred.get("username", "")
        if is_garbage_username(username):
            garbage.append(cred)

    if not garbage:
        click.echo(
            click.style(f"✓ No garbage credentials found in {eng_name}", fg="green")
        )
        return

    # Display what we found
    click.echo(
        click.style(
            f"\nFound {len(garbage)} garbage credential(s) in {eng_name}:\n",
            fg="yellow",
            bold=True,
        )
    )

    # Table header
    click.echo(f"  {'ID':<6} {'Service':<18} {'Username':<50}")
    click.echo("-" * 80)

    display_list = garbage if show_all else garbage[:20]
    for cred in display_list:
        username = (cred.get("username") or "<empty>")[:48]
        cred_id = str(cred.get("id", "?"))
        service = (cred.get("service") or "unknown")[:16]
        click.echo(f"  {cred_id:<6} {service:<18} {username}")

    if not show_all and len(garbage) > 20:
        click.echo(f"\n  ... and {len(garbage) - 20} more (use --all to see all)")

    click.echo("-" * 80)

    if confirm:
        # Actually delete
        click.echo(
            click.style(f"\nDeleting {len(garbage)} garbage credential(s)...", fg="red")
        )
        deleted = 0
        for cred in garbage:
            try:
                cm.delete_credential(cred["id"])
                deleted += 1
            except Exception as e:
                click.echo(f"  Failed to delete {cred['id']}: {e}")

        click.echo(
            click.style(f"✓ Deleted {deleted} garbage credential(s)", fg="green")
        )
    else:
        click.echo(
            click.style(
                f"\n[DRY RUN] Would delete {len(garbage)} credential(s)", fg="yellow"
            )
        )
        click.echo("Run with --confirm to actually delete them.")


@cli.group()
@require_password
def report():
    """Generate penetration test reports in various formats."""
    pass


@report.command("generate")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "html", "json"], case_sensitive=False),
    default="html",
    help="Report format",
)
@click.option(
    "--type",
    "-t",
    type=click.Choice(
        ["executive", "technical", "summary", "detection"], case_sensitive=False
    ),
    default="technical",
    help="Report type (executive, technical, summary, detection)",
)
@click.option(
    "--output",
    "-o",
    type=str,
    help="Output file path (default: reports/<engagement>_<timestamp>.<ext>)",
)
@click.option(
    "--engagement", "-e", type=int, help="Engagement ID (default: current engagement)"
)
@click.option(
    "--ai",
    is_flag=True,
    default=False,
    help="Enable AI-enhanced report (PRO tier, requires Claude API or Ollama)",
)
def report_generate(format, type, output, engagement, ai):
    """Generate a penetration test report.

    Report Types:
    - executive: High-level report for C-level/management (top findings, compliance, no technical details)
    - technical: Full technical report for security engineers (all findings, evidence, methodology)
    - summary: Brief report for quick status updates (top 3 findings, key metrics only)
    - detection: SIEM detection coverage report with MITRE ATT&CK heatmap (requires Wazuh integration)

    AI Enhancement (--ai flag):
    - Generates AI-powered executive summary
    - Adds business impact context to findings
    - Creates prioritized remediation plan
    - Requires Claude API key or local Ollama
    """
    import datetime

    from souleyez.reporting.generator import ReportGenerator
    from souleyez.storage.engagements import EngagementManager

    # Get engagement
    em = EngagementManager()

    if engagement:
        eng = em.get_by_id(engagement)
        if not eng:
            click.echo(click.style(f"✗ Engagement {engagement} not found", fg="red"))
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo(
                click.style(
                    "✗ No current engagement. Use 'souleyez engagement list' to see available engagements.",
                    fg="red",
                )
            )
            return

    engagement_id = eng["id"]
    engagement_name = eng["name"]

    # Detection reports require Wazuh integration
    if type == "detection":
        from souleyez.integrations.wazuh.config import WazuhConfig

        wazuh_config = WazuhConfig.get_config(engagement_id)
        if not wazuh_config or not wazuh_config.get("enabled"):
            click.echo(
                click.style("✗ Detection reports require Wazuh integration.", fg="red")
            )
            click.echo("  Configure Wazuh first: souleyez wazuh configure")
            return

        # Check for detection results
        from souleyez.storage.database import get_db

        db = get_db()
        results = db.execute(
            "SELECT COUNT(*) FROM detection_results WHERE engagement_id = ?",
            (engagement_id,),
        ).fetchone()[0]
        if results == 0:
            click.echo(
                click.style("✗ No detection validation results found.", fg="red")
            )
            click.echo("  Run attacks and validate detections first.")
            click.echo("  Use: souleyez detection validate")
            return

    # Show report type being generated
    type_label = {
        "executive": "EXECUTIVE (C-Level)",
        "technical": "TECHNICAL (Full Details)",
        "summary": "SUMMARY (Quick Status)",
        "detection": "DETECTION COVERAGE (SIEM Analysis)",
    }
    ai_label = " + AI Enhanced" if ai else ""
    click.echo(
        f"Generating {click.style(type_label[type] + ai_label, fg='yellow', bold=True)} {format.upper()} report"
    )
    click.echo(f"Engagement: {click.style(engagement_name, fg='cyan', bold=True)}")

    # Check AI availability if requested
    ai_provider = None
    if ai:
        from souleyez.ai import AIReportService
        from souleyez.ai.llm_factory import LLMFactory

        ai_provider = LLMFactory.get_available_provider()
        if ai_provider and ai_provider.is_available():
            provider_info = ai_provider.get_status()
            provider_name = provider_info.get("provider", "Unknown")
            click.echo(
                f"AI Provider: {click.style(provider_name, fg='magenta', bold=True)}"
            )

            # Show privacy warning for cloud providers
            if provider_name.lower() == "claude":
                click.echo(
                    click.style(
                        "⚠ PRIVACY: Engagement data will be sent to Anthropic's servers.",
                        fg="yellow",
                    )
                )
        else:
            click.echo(
                click.style(
                    "⚠ AI not available. Falling back to standard report.", fg="yellow"
                )
            )
            click.echo("  Configure Claude API key or ensure Ollama is running.")
            ai = False
            ai_provider = None

    # Generate output filename if not specified
    if not output:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = engagement_name.replace(" ", "_").replace("/", "_")
        ext = format if format != "markdown" else "md"
        # Include report type and AI in filename
        ai_suffix = "_ai" if ai else ""
        output = f"reports/{safe_name}_{type}{ai_suffix}_{timestamp}.{ext}"

    try:
        # Create report generator
        rg = ReportGenerator()

        # Set explicit AI provider to avoid factory fallback issues
        if ai_provider:
            from souleyez.ai import AIReportService

            rg._ai_service = AIReportService(provider=ai_provider)

        # Generate report with specified type and AI enhancement
        report_path = rg.generate_report(
            engagement_id=engagement_id,
            format=format,
            output_path=output,
            report_type=type,
            ai_enhanced=ai,
        )

        click.echo(click.style(f"✓ Report generated successfully!", fg="green"))
        click.echo(f"  Type: {type_label[type]}{' + AI' if ai else ''}")
        click.echo(f"  Format: {format.upper()}")
        click.echo(f"  File: {report_path}")

        # Show summary (different for detection reports)
        if type == "detection":
            from souleyez.reporting.detection_report import DetectionReportGatherer

            gatherer = DetectionReportGatherer(engagement_id)
            stats = gatherer.get_summary_stats()
            click.echo(f"\nDetection Summary:")
            click.echo(f"  Coverage: {stats['coverage_percent']}%")
            click.echo(f"  Attacks Tested: {stats['total_attacks']}")
            click.echo(f"  Detected: {stats['detected']}")
            click.echo(f"  Not Detected: {stats['not_detected']}")
            click.echo(f"  Risk Level: {stats['risk_level']}")
        else:
            data = rg.collect_data()
            click.echo(f"\nReport Summary:")
            click.echo(f"  Hosts: {len(data['hosts'])}")
            click.echo(f"  Findings: {len(data['findings'])}")
            click.echo(f"  Credentials: {len(data['credentials'])}")

    except Exception as e:
        click.echo(click.style(f"✗ Error generating report: {e}", fg="red"))
        import traceback

        traceback.print_exc()


@report.command("list")
def report_list():
    """List generated reports."""
    import os

    reports_dir = Path("reports")

    if not reports_dir.exists():
        click.echo("No reports directory found.")
        return

    reports = sorted(
        reports_dir.glob("*.*"), key=lambda p: p.stat().st_mtime, reverse=True
    )

    if not reports:
        click.echo("No reports found.")
        return

    click.echo("\n" + "=" * 70)
    click.echo("GENERATED REPORTS")
    click.echo("=" * 70)

    for rpt in reports:
        size = rpt.stat().st_size
        mtime = datetime.datetime.fromtimestamp(rpt.stat().st_mtime)
        click.echo(f"{rpt.name}")
        click.echo(
            f"  Size: {size:,} bytes | Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    click.echo("=" * 70 + "\n")


# ============================================================================
# AI Commands
# ============================================================================


@cli.group()
def ai():
    """AI-powered attack path recommendations (Pro feature)."""


@ai.command("status")
def ai_status():
    """Check Ollama connection and AI feature status."""
    from souleyez.ai.ollama_service import OllamaService

    click.echo("\n" + "=" * 70)
    click.echo("AI SERVICE STATUS")
    click.echo("=" * 70)

    # Create service and get status
    service = OllamaService()
    status = service.get_status()

    # Display connection status
    if status["connected"]:
        click.echo(click.style("✓ Ollama Connection: ", fg="green") + "Connected")
        click.echo(f"  Endpoint: {status['endpoint']}")
    else:
        click.echo(click.style("✗ Ollama Connection: ", fg="red") + "Not connected")
        click.echo(f"  Endpoint: {status['endpoint']}")
        if status.get("error"):
            click.echo(f"  Error: {status['error']}")
        click.echo(
            "\n"
            + click.style("💡 TIP:", fg="yellow")
            + " Install Ollama from https://ollama.ai"
        )
        click.echo("  Then run: ollama serve")
        click.echo("=" * 70 + "\n")
        return

    # Display available models
    click.echo(f"\nAvailable Models: {len(status['models'])}")
    if status["models"]:
        for model in status["models"]:
            if status["configured_model"] in model:
                click.echo(f"  • {model} " + click.style("(configured)", fg="cyan"))
            elif status["default_model"] in model:
                click.echo(f"  • {model} " + click.style("(default)", fg="yellow"))
            else:
                click.echo(f"  • {model}")
    else:
        click.echo("  No models found")

    # Display configured model status
    click.echo(f"\nConfigured Model: {status['configured_model']}")
    if status["model_available"]:
        click.echo(click.style("✓ Status: ", fg="green") + "Ready")
    else:
        click.echo(click.style("✗ Status: ", fg="red") + "Not available")
        click.echo(
            f"\n" + click.style("💡 TIP:", fg="yellow") + f" Pull the model with:"
        )
        click.echo(f"  ollama pull {status['configured_model']}")
        click.echo(f"  Or change the model in Settings & Security → AI Settings")

    click.echo("=" * 70 + "\n")


@ai.command("init")
def ai_init():
    """Initialize AI features by checking connection and pulling required models."""
    from souleyez.ai.ollama_service import OllamaService

    click.echo("\n" + "=" * 70)
    click.echo("AI FEATURE INITIALIZATION")
    click.echo("=" * 70 + "\n")

    # Create service
    service = OllamaService()

    # Check connection
    click.echo("🔄 Checking Ollama connection...")
    if not service.check_connection():
        click.echo(click.style("✗ Failed:", fg="red") + " Cannot connect to Ollama")
        click.echo(
            "\n" + click.style("💡 TIP:", fg="yellow") + " Install and start Ollama:"
        )
        click.echo("  1. Download from https://ollama.ai")
        click.echo("  2. Run: ollama serve")
        click.echo("=" * 70 + "\n")
        sys.exit(1)

    click.echo(click.style("✓ Connected", fg="green") + " to Ollama\n")

    # Check if model exists
    configured_model = service.model
    click.echo(f"🔍 Checking for model: {configured_model}...")

    if service.check_model():
        click.echo(click.style("✓ Model already available", fg="green"))
        click.echo("\n" + click.style("✓ AI features ready!", fg="green", bold=True))
        click.echo("=" * 70 + "\n")
        return

    # Model doesn't exist, pull it
    click.echo(click.style("⬇️  Model not found, pulling now...", fg="yellow"))
    click.echo(f"   This may take a few minutes depending on your connection.\n")

    try:
        if service.pull_model():
            click.echo(click.style("\n✓ Model pulled successfully!", fg="green"))
            click.echo(click.style("✓ AI features ready!", fg="green", bold=True))
        else:
            click.echo(click.style("\n✗ Failed to pull model", fg="red"))
            click.echo("  Please try manually: ollama pull " + configured_model)
            sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"\n✗ Error pulling model: {e}", fg="red"))
        click.echo("  Please try manually: ollama pull " + configured_model)
        sys.exit(1)

    click.echo("=" * 70 + "\n")


@ai.command("recommend")
@click.option(
    "--engagement",
    "-e",
    type=int,
    default=None,
    help="Engagement ID to analyze (default: current)",
)
@click.option(
    "--steps",
    "-s",
    type=int,
    default=1,
    help="Number of attack steps to generate (default: 1)",
)
def ai_recommend(engagement, steps):
    """Generate AI-powered attack path recommendation."""
    from souleyez.ai.recommender import AttackRecommender
    from souleyez.storage.engagements import EngagementManager

    # Get engagement (either specified or current)
    eng_mgr = EngagementManager()

    if engagement:
        # Use specified engagement ID
        engagement_data = eng_mgr.get_by_id(engagement)
        if not engagement_data:
            click.echo(
                click.style(f"✗ Error:", fg="red")
                + f" Engagement ID {engagement} not found"
            )
            sys.exit(1)
    else:
        # Use current engagement
        engagement_data = eng_mgr.get_current()
        if not engagement_data:
            click.echo(
                click.style("✗ Error:", fg="red") + " No current engagement selected"
            )
            click.echo("  Use: souleyez engagement use <name>")
            sys.exit(1)
        engagement = engagement_data["id"]

    click.echo("\n" + "=" * 70)
    if steps > 1:
        click.echo(f"AI ATTACK CHAIN ({steps} steps)")
    else:
        click.echo(f"AI ATTACK PATH RECOMMENDATION")
    click.echo(f"Engagement: {engagement_data['name']}")
    click.echo("=" * 70 + "\n")

    # Generate recommendation
    click.echo("🤔 Analyzing engagement data...")
    recommender = AttackRecommender()

    if steps > 1:
        result = recommender.generate_chain(engagement, num_steps=steps)
    else:
        result = recommender.suggest_next_step(engagement)

    # Check for errors
    if result.get("error"):
        click.echo(click.style("✗ Failed:", fg="red") + f" {result['error']}")
        if "ai init" in result["error"]:
            click.echo(
                "\n" + click.style("💡 TIP:", fg="yellow") + " Run: souleyez ai init"
            )
        click.echo("=" * 70 + "\n")
        sys.exit(1)

    # Display recommendation
    if steps > 1:
        # Display multi-step chain
        click.echo(click.style("✓ Attack chain generated!", fg="green") + "\n")

        for step in result["steps"]:
            click.echo(
                click.style(f"STEP {step['step_number']}:", fg="yellow", bold=True)
                + f" {step['action']}"
            )
            click.echo(f"  {click.style('TARGET:', fg='cyan')} {step['target']}")
            click.echo(f"  {click.style('RATIONALE:', fg='white')} {step['rationale']}")
            click.echo(f"  {click.style('EXPECTED:', fg='green')} {step['expected']}")

            risk_color = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red"}.get(
                step["risk"], "white"
            )
            click.echo(
                f"  {click.style('RISK:', fg='cyan')} {click.style(step['risk'], fg=risk_color)}"
            )
            click.echo(
                f"  {click.style('DEPENDENCIES:', fg='cyan')} {step['dependencies']}"
            )
            click.echo()
    else:
        # Display single-step recommendation
        click.echo(click.style("✓ Recommendation generated!", fg="green") + "\n")

        click.echo(click.style("NEXT ACTION:", fg="cyan", bold=True))
        click.echo(f"  {result['action']}\n")

        click.echo(click.style("TARGET:", fg="cyan", bold=True))
        click.echo(f"  {result['target']}\n")

        click.echo(click.style("RATIONALE:", fg="cyan", bold=True))
        click.echo(f"  {result['rationale']}\n")

        click.echo(click.style("EXPECTED OUTCOME:", fg="cyan", bold=True))
        click.echo(f"  {result['expected_outcome']}\n")

        # Color-code risk level
        risk = result["risk_level"]
        risk_colors = {"low": "green", "medium": "yellow", "high": "red"}
        risk_color = risk_colors.get(risk, "white")

        click.echo(click.style("RISK LEVEL:", fg="cyan", bold=True))
        click.echo("  " + click.style(risk.upper(), fg=risk_color, bold=True))

    click.echo("\n" + "=" * 70 + "\n")


@ai.command("paths")
@click.option("--engagement", "-e", type=int, help="Engagement ID (default: current)")
@click.option(
    "--number",
    "-n",
    type=int,
    default=3,
    help="Number of paths to generate (default: 3)",
)
def ai_paths(engagement, number):
    """Generate and rank multiple attack paths."""
    from souleyez.ai.recommender import AttackRecommender
    from souleyez.storage.engagements import EngagementManager

    em = EngagementManager()

    # Get engagement
    if engagement:
        eng = em.get_by_id(engagement)
        if not eng:
            click.echo(click.style(f"✗ Engagement {engagement} not found", fg="red"))
            return
    else:
        eng = em.get_current()
        if not eng:
            click.echo(
                click.style(
                    "✗ No active engagement. Use: souleyez engagement use <name>",
                    fg="red",
                )
            )
            return

    click.echo(
        click.style(
            f"\n🤖 Generating {number} alternative attack paths...",
            fg="cyan",
            bold=True,
        )
    )
    click.echo(
        click.style(
            "⏳ This may take 1-3 minutes depending on AI model speed...\n", fg="yellow"
        )
    )

    # Generate paths
    recommender = AttackRecommender()
    result = recommender.suggest_multiple_paths(eng["id"], num_paths=number)

    # Handle errors
    if result.get("error"):
        click.echo(click.style(f"✗ Error: {result['error']}", fg="red"))
        return

    paths = result.get("paths", [])
    if not paths:
        click.echo(click.style("No attack paths generated", fg="yellow"))
        return

    # Display ranked paths
    click.echo("=" * 80)
    click.echo(
        click.style(f"RANKED ATTACK PATHS (Top {len(paths)})", bold=True, fg="cyan")
    )
    click.echo("=" * 80)

    for scored_path in paths:
        rank = scored_path["rank"]
        path = scored_path["path"]
        scores = scored_path["scores"]
        total = scored_path["total_score"]

        # Rank header with score
        if rank == 1:
            rank_color = "green"
            rank_icon = "🥇"
        elif rank == 2:
            rank_color = "yellow"
            rank_icon = "🥈"
        elif rank == 3:
            rank_color = "cyan"
            rank_icon = "🥉"
        else:
            rank_color = "white"
            rank_icon = f"#{rank}"

        click.echo(
            f"\n{rank_icon} "
            + click.style(f"PATH {rank}", bold=True, fg=rank_color)
            + click.style(f" (Score: {total}/100)", fg=rank_color)
        )
        click.echo("-" * 80)

        # Path details
        click.echo(f"ACTION: {path['action']}")
        click.echo(f"TARGET: {path['target']}")
        risk_color = (
            "green"
            if path["risk_level"] == "LOW"
            else ("yellow" if path["risk_level"] == "MEDIUM" else "red")
        )
        click.echo(f"RISK: {click.style(path['risk_level'], fg=risk_color)}")
        click.echo(f"\nRATIONALE: {path['rationale']}")
        click.echo(f"EXPECTED: {path['expected']}")

        # Score breakdown
        click.echo(f"\n📊 Score Breakdown:")
        click.echo(f"   Success Probability: {scores['success']}/100 (40% weight)")
        click.echo(f"   Impact:             {scores['impact']}/100 (30% weight)")
        click.echo(f"   Stealth:            {scores['stealth']}/100 (20% weight)")
        click.echo(f"   Complexity:         -{scores['complexity']} (penalty)")

    click.echo("\n" + "=" * 80)
    click.echo(
        click.style(f"\n💡 Tip: Execute top path with: souleyez ai execute", fg="cyan")
    )


@ai.command("execute")
@click.option(
    "--engagement",
    "-e",
    type=int,
    default=None,
    help="Engagement ID (default: current)",
)
@click.option("--once", is_flag=True, help="Run only one iteration then stop")
@click.option("--dry-run", is_flag=True, help="Show commands but don't execute")
@click.option("--auto-low", is_flag=True, help="Auto-approve LOW risk commands")
@click.option(
    "--auto-medium", is_flag=True, help="Auto-approve LOW and MEDIUM risk commands"
)
@click.option(
    "--max-iterations", "-n", type=int, default=None, help="Maximum iterations to run"
)
def ai_execute(engagement, once, dry_run, auto_low, auto_medium, max_iterations):
    """Execute AI-driven attack recommendations interactively."""
    from souleyez.ai.executor import InteractiveExecutor
    from souleyez.ai.safety import ApprovalMode
    from souleyez.storage.engagements import EngagementManager

    # Get engagement
    eng_mgr = EngagementManager()

    if engagement:
        engagement_data = eng_mgr.get_by_id(engagement)
        if not engagement_data:
            click.echo(
                click.style(f"✗ Error:", fg="red")
                + f" Engagement ID {engagement} not found"
            )
            sys.exit(1)
    else:
        engagement_data = eng_mgr.get_current()
        if not engagement_data:
            click.echo(
                click.style("✗ Error:", fg="red") + " No current engagement selected"
            )
            click.echo("  Use: souleyez engagement use <name>")
            sys.exit(1)
        engagement = engagement_data["id"]

    # Determine approval mode
    if dry_run:
        approval_mode = ApprovalMode.DRY_RUN
    elif auto_medium:
        approval_mode = ApprovalMode.AUTO_MEDIUM
    elif auto_low:
        approval_mode = ApprovalMode.AUTO_LOW
    else:
        approval_mode = ApprovalMode.MANUAL

    # Create executor and run
    try:
        executor = InteractiveExecutor(approval_mode=approval_mode)
        executor.execute_loop(
            engagement_id=engagement, max_iterations=max_iterations, once=once
        )
    except KeyboardInterrupt:
        click.echo(click.style("\n\n🛑 Execution stopped by user", fg="yellow"))
        sys.exit(0)
    except Exception as e:
        click.echo(click.style(f"\n✗ Fatal error: {e}", fg="red"))
        sys.exit(1)


# ============================================================================
# Import Commands
# ============================================================================


@cli.group()
def import_data():
    """Import data from external sources."""
    pass


@import_data.command("msf")
@click.argument("xml_file", type=click.Path(exists=True))
@click.option("-v", "--verbose", is_flag=True, help="Show detailed import progress")
def import_msf(xml_file, verbose):
    """
    Import data from Metasploit Framework XML export.

    Export from MSF console:
        db_export -f xml /path/to/export.xml

    Example:
        souleyez import-data msf /path/to/msf_export.xml
    """
    from souleyez.importers.msf_importer import MSFImporter

    em = EngagementManager()
    current_ws = em.get_current()

    if not current_ws:
        click.echo(
            click.style(
                "✗ No engagement selected! Use 'souleyez engagement use <name>'",
                fg="red",
            )
        )
        return

    engagement_id = current_ws["id"]
    engagement_name = current_ws["name"]

    click.echo(
        click.style(
            f"\n🔄 Importing Metasploit data into engagement: {engagement_name}",
            fg="cyan",
            bold=True,
        )
    )
    click.echo()

    importer = MSFImporter(engagement_id)

    try:
        stats = importer.import_xml(xml_file, verbose=verbose)

        click.echo()
        click.echo(
            click.style("✓ Import completed successfully!", fg="green", bold=True)
        )
        click.echo()
        click.echo("Import Summary:")
        click.echo(f"  • Hosts:           {stats['hosts']}")
        click.echo(f"  • Services:        {stats['services']}")
        click.echo(f"  • Credentials:     {stats['credentials']}")
        click.echo(f"  • Vulnerabilities: {stats['vulnerabilities']}")

        if stats["skipped"] > 0:
            click.echo(f"  • Skipped:         {stats['skipped']}")

        click.echo()
        click.echo(
            click.style("💡 TIP:", fg="yellow", bold=True) + " View imported data with:"
        )
        click.echo("  • souleyez dashboard")
        click.echo("  • souleyez interactive")
        click.echo("  • souleyez report generate")
        click.echo()

    except Exception as e:
        click.echo(click.style(f"\n✗ Import failed: {e}", fg="red"))
        if verbose:
            import traceback

            traceback.print_exc()
        return


@cli.group()
def config():
    """View and modify configuration settings."""
    pass


@config.command("get")
@click.argument("key")
def config_get(key):
    """
    Get a configuration value.

    KEY is a dotted path like 'ai.ollama_url' or 'security.session_timeout_minutes'

    Examples:
        souleyez config get ai.provider
        souleyez config get ai.ollama_url
        souleyez config get security.session_timeout_minutes
    """
    from souleyez.config import get as cfg_get

    value = cfg_get(key)
    if value is None:
        click.echo(f"{key} = (not set)")
    else:
        click.echo(f"{key} = {value}")


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """
    Set a configuration value.

    KEY is a dotted path like 'ai.ollama_url' or 'settings.threads'
    VALUE is the new value to set

    Examples:
        souleyez config set ai.ollama_url http://10.0.0.28:11434
        souleyez config set ai.ollama_model llama3.1:8b
        souleyez config set settings.threads 20
    """
    from souleyez.config import _set_nested, read_config, write_config

    # Read current config
    cfg = read_config()

    # Convert value types for common settings
    if key in (
        "settings.threads",
        "security.session_timeout_minutes",
        "security.max_login_attempts",
        "security.lockout_duration_minutes",
        "security.min_password_length",
        "crypto.iterations",
        "database.backup_interval_hours",
        "ai.max_tokens",
        "logging.max_bytes",
        "logging.backup_count",
    ):
        try:
            value = int(value)
        except ValueError:
            click.echo(click.style(f"Error: {key} requires an integer value", fg="red"))
            return

    if key in ("ai.temperature",):
        try:
            value = float(value)
        except ValueError:
            click.echo(click.style(f"Error: {key} requires a numeric value", fg="red"))
            return

    if key in ("database.backup_enabled",):
        value = value.lower() in ("true", "1", "yes")

    # Set the value
    _set_nested(cfg, key, value)

    # Write config
    write_config(cfg)

    click.echo(click.style(f"✓ Set {key} = {value}", fg="green"))


@config.command("list")
def config_list():
    """
    List all configuration values.
    """
    import json

    from souleyez.config import read_config

    cfg = read_config()
    click.echo(json.dumps(cfg, indent=2))


# Import and register screenshot commands
from souleyez.commands.screenshots import screenshots

cli.add_command(screenshots)

# Import and register deliverable commands
from souleyez.commands.deliverables import deliverables

cli.add_command(deliverables)
