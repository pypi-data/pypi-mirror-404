#!/usr/bin/env python3
"""
souleyez.ui.setup_wizard - First-run setup wizard for new users
"""

import getpass
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

import click

from souleyez.ui.design_system import DesignSystem

# Wizard state file
WIZARD_STATE_FILE = Path.home() / ".souleyez" / ".wizard_completed"


def is_wizard_completed() -> bool:
    """Check if wizard has been completed."""
    return WIZARD_STATE_FILE.exists()


def mark_wizard_completed():
    """Mark wizard as completed."""
    WIZARD_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    WIZARD_STATE_FILE.touch()


def _check_disk_space(min_mb: int = 500) -> bool:
    """Check if there's enough disk space for installs."""
    try:
        usage = shutil.disk_usage("/")
        free_mb = usage.free // (1024 * 1024)
        return free_mb >= min_mb
    except Exception:
        return True  # Assume OK if we can't check


def _configure_sudoers(tool_name: str, tool_path: str) -> bool:
    """
    Add NOPASSWD sudoers entry for privileged tool.

    Args:
        tool_name: Name of the tool (used for sudoers filename)
        tool_path: Absolute path to tool binary

    Returns:
        True if configured successfully, False otherwise
    """
    # Skip if running as root
    if os.geteuid() == 0:
        return True

    username = getpass.getuser()
    sudoers_file = f"/etc/sudoers.d/{tool_name}"
    sudoers_line = f"{username} ALL=(ALL) NOPASSWD: {tool_path}"
    tmp_file = f"/tmp/sudoers_{tool_name}_{os.getpid()}"

    try:
        # Write to temp file first
        with open(tmp_file, "w") as f:
            f.write(sudoers_line + "\n")

        # Validate syntax with visudo before applying
        result = subprocess.run(
            ["sudo", "visudo", "-c", "-f", tmp_file], capture_output=True, timeout=30
        )

        if result.returncode != 0:
            click.echo(
                f"    {click.style('!', fg='yellow')} Invalid sudoers syntax for {tool_name}, skipping"
            )
            os.unlink(tmp_file)
            return False

        # Safe to move to sudoers.d
        subprocess.run(["sudo", "mv", tmp_file, sudoers_file], check=True, timeout=30)
        subprocess.run(["sudo", "chmod", "0440", sudoers_file], check=True, timeout=30)

        return True

    except subprocess.TimeoutExpired:
        click.echo(
            f"    {click.style('!', fg='yellow')} Timeout configuring sudoers for {tool_name}"
        )
        return False
    except Exception as e:
        click.echo(
            f"    {click.style('!', fg='yellow')} Error configuring sudoers for {tool_name}: {e}"
        )
        # Clean up temp file if it exists
        if os.path.exists(tmp_file):
            try:
                os.unlink(tmp_file)
            except Exception:
                pass
        return False


def _install_desktop_shortcut():
    """
    Install desktop shortcut for SoulEyez in Applications menu.

    This runs silently during setup - any errors are ignored to not
    disrupt the setup flow.
    """
    try:
        applications_dir = Path.home() / ".local" / "share" / "applications"
        icons_dir = Path.home() / ".local" / "share" / "icons"
        desktop_file = applications_dir / "souleyez.desktop"
        icon_dest = icons_dir / "souleyez.png"

        # Skip if already installed
        if desktop_file.exists():
            return

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
                icon_source = (
                    Path(__file__).parent.parent / "assets" / "souleyez-icon.png"
                )
                with open(icon_source, "rb") as src:
                    icon_data = src.read()

            with open(icon_dest, "wb") as dst:
                dst.write(icon_data)
        except Exception:
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

        # Update desktop database (optional)
        try:
            subprocess.run(
                ["update-desktop-database", str(applications_dir)],
                capture_output=True,
                check=False,
                timeout=5,
            )
        except Exception:
            pass

        click.echo(
            f"  {click.style('✓', fg='green')} Desktop shortcut: Added to Applications menu"
        )

    except Exception:
        # Silently ignore errors - desktop shortcut is nice-to-have
        pass


def _run_tool_installs(
    missing_tools: List[Dict], wrong_version_tools: List[Dict], distro: str
) -> bool:
    """
    Prompt user and run install/upgrade commands.

    Args:
        missing_tools: List of missing tool dicts with 'name', 'install', 'tool_info'
        wrong_version_tools: List of wrong version tool dicts
        distro: Detected distribution

    Returns:
        True if any installs were run
    """
    from souleyez.utils.tool_checker import EXTERNAL_TOOLS, get_upgrade_command

    all_installs = []

    # Add wrong version tools (upgrades)
    for tool in wrong_version_tools:
        # Try to get upgrade command, fall back to install command
        tool_info = tool.get("tool_info", {})
        upgrade_cmd = get_upgrade_command(tool_info, distro) if tool_info else None
        install_cmd = upgrade_cmd or tool.get("install", "")

        all_installs.append(
            {
                "name": tool["name"],
                "cmd": install_cmd,
                "action": "upgrade",
                "tool_info": tool_info,
            }
        )

    # Add missing tools (installs)
    for tool in missing_tools:
        all_installs.append(
            {
                "name": tool["name"],
                "cmd": tool["install"],
                "action": "install",
                "tool_info": tool.get("tool_info", {}),
            }
        )

    if not all_installs:
        return False

    # Check disk space
    if not _check_disk_space(500):
        click.echo()
        click.echo(
            f"  {click.style('!', fg='yellow')} Low disk space (<500MB free). Installs may fail."
        )
        if not click.confirm("  Continue anyway?", default=False):
            return False

    # Show what will be installed/upgraded
    click.echo()
    click.echo(f"  {len(all_installs)} tool(s) to install/upgrade:")
    for item in all_installs:
        action_color = "cyan" if item["action"] == "upgrade" else "green"
        click.echo(
            f"    - {item['name']} ({click.style(item['action'], fg=action_color)})"
        )

    click.echo()
    if not click.confirm("  Install/upgrade now?", default=False):
        click.echo("  Skipped. You can run 'souleyez setup' later to install tools.")
        return False

    # Request sudo upfront
    click.echo()
    click.echo("  Requesting sudo access...")
    result = subprocess.run(["sudo", "-v"], check=False)
    if result.returncode != 0:
        click.echo(
            f"  {click.style('x', fg='red')} Could not obtain sudo. Aborting installs."
        )
        return False

    # Update apt cache first (for apt-based installs)
    has_apt_installs = any("apt" in item["cmd"] for item in all_installs)
    if has_apt_installs:
        click.echo()
        click.echo("  Updating package lists...")
        result = subprocess.run(["sudo", "apt", "update"], capture_output=True)
        if result.returncode != 0:
            click.echo(
                f"  {click.style('!', fg='yellow')} apt update had issues, continuing anyway..."
            )

    # Track results for summary
    results = []

    # Run each install command
    for item in all_installs:
        click.echo()
        click.echo(
            f"  {click.style(item['action'].capitalize() + 'ing', fg='cyan')} {item['name']}..."
        )

        try:
            # Run install command
            proc = subprocess.run(
                item["cmd"],
                shell=True,  # nosec B602 - commands from trusted EXTERNAL_TOOLS
                timeout=600,  # 10 minute timeout per tool
            )

            if proc.returncode == 0:
                click.echo(
                    f"  {click.style('✓', fg='green')} {item['name']} {item['action']} complete"
                )
                results.append(
                    {
                        "name": item["name"],
                        "success": True,
                        "tool_info": item["tool_info"],
                    }
                )
            else:
                click.echo(
                    f"  {click.style('✗', fg='red')} {item['name']} failed (exit {proc.returncode})"
                )
                results.append(
                    {
                        "name": item["name"],
                        "success": False,
                        "tool_info": item["tool_info"],
                    }
                )

        except subprocess.TimeoutExpired:
            click.echo(f"  {click.style('✗', fg='red')} {item['name']} timed out")
            results.append(
                {"name": item["name"], "success": False, "tool_info": item["tool_info"]}
            )
        except Exception as e:
            click.echo(f"  {click.style('✗', fg='red')} {item['name']} error: {e}")
            results.append(
                {"name": item["name"], "success": False, "tool_info": item["tool_info"]}
            )

    # Configure sudoers for privileged tools that installed successfully
    click.echo()
    click.echo("  Configuring permissions for privileged tools...")

    sudoers_configured = False
    for res in results:
        if not res["success"]:
            continue

        tool_info = res["tool_info"]
        if not tool_info.get("needs_sudo"):
            continue

        sudoers_configured = True
        # Find the actual binary path
        command = tool_info.get("command", res["name"])
        tool_path = shutil.which(command)

        # Check alt_commands if primary not found
        if not tool_path and tool_info.get("alt_commands"):
            for alt in tool_info["alt_commands"]:
                tool_path = shutil.which(alt)
                if tool_path:
                    break

        if tool_path:
            if _configure_sudoers(res["name"], tool_path):
                click.echo(
                    f"    {click.style('✓', fg='green')} {res['name']} configured for passwordless sudo"
                )
            else:
                click.echo(
                    f"    {click.style('!', fg='yellow')} {res['name']} sudoers config failed"
                )
        else:
            click.echo(
                f"    {click.style('!', fg='yellow')} {res['name']} binary not found, skipping sudoers"
            )

    if not sudoers_configured:
        click.echo("    No privileged tools needed configuration.")

    # Re-verify installed tools
    click.echo()
    click.echo("  Verifying installations...")

    success_count = 0
    fail_count = 0

    for res in results:
        tool_info = res["tool_info"]
        command = tool_info.get("command", res["name"])
        alt_commands = tool_info.get("alt_commands")

        # Check if tool is now available
        found = shutil.which(command) is not None
        if not found and alt_commands:
            for alt in alt_commands:
                if shutil.which(alt):
                    found = True
                    break

        if found:
            click.echo(f"    {click.style('✓', fg='green')} {res['name']} verified")
            success_count += 1
        else:
            click.echo(
                f"    {click.style('✗', fg='red')} {res['name']} not found after install"
            )
            fail_count += 1

    # Summary
    click.echo()
    if fail_count == 0:
        click.echo(
            f"  {click.style('✓', fg='green')} All {success_count} tool(s) installed successfully!"
        )
    else:
        click.echo(
            f"  {click.style('!', fg='yellow')} {success_count} succeeded, {fail_count} failed"
        )
        click.echo("  Failed tools may need manual installation.")

    return True


def _show_wizard_banner():
    """Display the SoulEyez ASCII banner for wizard steps."""
    click.echo()
    click.echo(
        click.style(
            "   ███████╗ ██████╗ ██╗   ██╗██╗     ███████╗██╗   ██╗███████╗███████╗",
            fg="bright_cyan",
            bold=True,
        )
        + click.style("        ▄██▄", fg="bright_blue", bold=True)
    )
    click.echo(
        click.style(
            "   ██╔════╝██╔═══██╗██║   ██║██║     ██╔════╝╚██╗ ██╔╝██╔════╝╚══███╔╝",
            fg="bright_cyan",
            bold=True,
        )
        + click.style("      ▄█▀  ▀█▄", fg="bright_blue", bold=True)
    )
    click.echo(
        click.style(
            "   ███████╗██║   ██║██║   ██║██║     █████╗   ╚████╔╝ █████╗    ███╔╝ ",
            fg="bright_cyan",
            bold=True,
        )
        + click.style("     █   ◉   █", fg="bright_blue", bold=True)
    )
    click.echo(
        click.style(
            "   ╚════██║██║   ██║██║   ██║██║     ██╔══╝    ╚██╔╝  ██╔══╝   ███╔╝  ",
            fg="bright_cyan",
            bold=True,
        )
        + click.style("     █  ═══  █", fg="bright_blue", bold=True)
    )
    click.echo(
        click.style(
            "   ███████║╚██████╔╝╚██████╔╝███████╗███████╗   ██║   ███████╗███████╗",
            fg="bright_cyan",
            bold=True,
        )
        + click.style("      ▀█▄  ▄█▀", fg="bright_blue", bold=True)
    )
    click.echo(
        click.style(
            "   ╚══════╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝   ╚═╝   ╚══════╝╚══════╝",
            fg="bright_cyan",
            bold=True,
        )
        + click.style("        ▀██▀", fg="bright_blue", bold=True)
    )
    click.echo()
    click.echo(click.style("  Created by CyberSoul SecurITy", fg="bright_blue"))
    click.echo()


def run_setup_wizard() -> bool:
    """
    Run the setup wizard for new users.

    Returns:
        bool: True if wizard completed, False if skipped/cancelled
    """
    try:
        # Check if user has Pro tier
        from souleyez.auth import Tier, get_current_user

        user = get_current_user()
        is_pro = user and user.tier == Tier.PRO

        # Step 1: Welcome
        if not _wizard_welcome(is_pro):
            mark_wizard_completed()  # Mark as completed even if skipped
            return False

        # Step 2: Encryption Setup
        encryption_enabled = _wizard_encryption_setup()

        # Step 3: Create First Engagement
        engagement_info = _wizard_create_engagement()
        if not engagement_info:
            return False

        # Step 4: Tool Check
        tool_status = _wizard_tool_check()

        # Step 5: AI Setup (Optional - Ollama)
        ai_enabled = _wizard_ai_setup()

        # Step 6: Automation Preferences (Pro only)
        if is_pro:
            automation_prefs = _wizard_automation_prefs()
        else:
            automation_prefs = {"enabled": False, "mode": None}

        # Step 7: Deliverable Templates (Pro only)
        if is_pro:
            templates = _wizard_deliverables(engagement_info.get("type"))
        else:
            templates = []

        # Step 8: Summary (adjust step numbers for FREE)
        _wizard_summary(
            encryption_enabled,
            engagement_info,
            tool_status,
            ai_enabled,
            automation_prefs,
            templates,
            is_pro,
        )

        mark_wizard_completed()
        return True

    except (KeyboardInterrupt, click.Abort):
        click.echo(click.style("\n\n  Setup wizard cancelled.", fg="yellow"))
        mark_wizard_completed()  # Don't show wizard again
        click.pause()
        return False


def _wizard_welcome(is_pro: bool = False) -> bool:
    """Show welcome screen with ASCII banner."""
    DesignSystem.clear_screen()
    width = DesignSystem.get_terminal_width()

    # Header
    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            " WELCOME TO SOULEYEZ - SETUP WIZARD ".center(width - 2),
            bold=True,
            fg="cyan",
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    # ASCII Art Banner - SOULEYEZ with all-seeing eye on the right
    click.echo(
        click.style(
            "   ███████╗ ██████╗ ██╗   ██╗██╗     ███████╗██╗   ██╗███████╗███████╗",
            fg="bright_cyan",
            bold=True,
        )
        + click.style("        ▄██▄", fg="bright_blue", bold=True)
    )
    click.echo(
        click.style(
            "   ██╔════╝██╔═══██╗██║   ██║██║     ██╔════╝╚██╗ ██╔╝██╔════╝╚══███╔╝",
            fg="bright_cyan",
            bold=True,
        )
        + click.style("      ▄█▀  ▀█▄", fg="bright_blue", bold=True)
    )
    click.echo(
        click.style(
            "   ███████╗██║   ██║██║   ██║██║     █████╗   ╚████╔╝ █████╗    ███╔╝ ",
            fg="bright_cyan",
            bold=True,
        )
        + click.style("     █   ◉   █", fg="bright_blue", bold=True)
    )
    click.echo(
        click.style(
            "   ╚════██║██║   ██║██║   ██║██║     ██╔══╝    ╚██╔╝  ██╔══╝   ███╔╝  ",
            fg="bright_cyan",
            bold=True,
        )
        + click.style("     █  ═══  █", fg="bright_blue", bold=True)
    )
    click.echo(
        click.style(
            "   ███████║╚██████╔╝╚██████╔╝███████╗███████╗   ██║   ███████╗███████╗",
            fg="bright_cyan",
            bold=True,
        )
        + click.style("      ▀█▄  ▄█▀", fg="bright_blue", bold=True)
    )
    click.echo(
        click.style(
            "   ╚══════╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝   ╚═╝   ╚══════╝╚══════╝",
            fg="bright_cyan",
            bold=True,
        )
        + click.style("        ▀██▀", fg="bright_blue", bold=True)
    )
    click.echo()

    # Tagline and description
    click.echo(click.style("  Created by CyberSoul SecurITy", fg="bright_blue"))
    click.echo()
    click.echo(
        "  SoulEyez brings your hacking tools together so you can spend less time switching windows"
    )
    click.echo(
        "  and more time breaking things (ethically, of course). Launch scans with Nmap, Metasploit,"
    )
    click.echo(
        "  Gobuster, theHarvester, and many more. Manage engagements, review findings, generate reports,"
    )
    click.echo("  and let AI recommend your next moves — all in one place.")
    click.echo()
    click.echo(click.style("  SETUP WIZARD", bold=True, fg="cyan"))
    click.echo("  ─────────────")
    click.echo()
    click.echo("  This wizard will help you get started:")
    click.echo(
        "  " + click.style("✓", fg="green") + " Set up encryption for credentials"
    )
    click.echo("  " + click.style("✓", fg="green") + " Create your first engagement")
    click.echo("  " + click.style("✓", fg="green") + " Check installed tools")
    click.echo("  " + click.style("✓", fg="green") + " Set up AI features (optional)")

    # Only show Pro steps if user has Pro tier
    if is_pro:
        click.echo(
            "  " + click.style("✓", fg="green") + " Configure automation preferences"
        )
        click.echo("  " + click.style("✓", fg="green") + " Select report templates")

    click.echo()
    click.pause("  Press ENTER to continue...")

    return True


def _wizard_encryption_setup() -> bool:
    """Set up encryption for credentials."""
    from souleyez.storage.crypto import CryptoManager

    DesignSystem.clear_screen()
    _show_wizard_banner()
    width = 60

    click.echo("┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            " STEP 2: ENCRYPTION SETUP ".center(width - 2), bold=True, fg="cyan"
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    crypto = CryptoManager()

    if crypto.is_encryption_enabled():
        click.echo("  " + click.style("✓ Encryption already configured", fg="green"))
        click.echo()
        click.pause("  Press any key to continue...")
        return True

    click.echo("  SoulEyez encrypts all credentials (passwords, API keys, tokens)")
    click.echo(
        "  with a master password. This is "
        + click.style("required", fg="green", bold=True)
        + " for security."
    )
    click.echo()
    click.echo(
        "  " + click.style("[y]", fg="green") + " Enable encryption (recommended)"
    )
    click.echo("  " + click.style("[n]", fg="bright_black") + " Skip encryption")
    click.echo()

    choice = click.prompt("  Enable encryption? [y/n]", default="y").strip().lower()

    if choice in ("n", "s", "no", "skip"):
        click.echo()
        time.sleep(0.5)
        click.echo("  " + click.style("SIKE! 😏", fg="magenta", bold=True))
        time.sleep(0.8)
        click.echo()
        click.echo(
            "  " + click.style("Security is not optional.", fg="cyan", bold=True)
        )
        click.echo("  " + "We're a security company. Encryption is mandatory.")
        click.echo()
        time.sleep(1)
        click.echo(
            "  " + click.style("Let's set up your vault password...", fg="green")
        )
        click.pause("  Press any key to continue...")

    click.echo()
    click.echo("  " + click.style("Password Requirements:", bold=True))
    click.echo("    • At least 12 characters")
    click.echo("    • Mix of uppercase and lowercase")
    click.echo("    • At least one number")
    click.echo("    • At least one special character (!@#$%^&*)")
    click.echo()
    click.echo(
        "  "
        + click.style(
            "⚠️  If you lose this password, encrypted credentials cannot be recovered!",
            fg="yellow",
            bold=True,
        )
    )
    click.echo()

    import re

    password_set = False
    while not password_set:
        password = getpass.getpass("  Enter master password: ")

        # Validate password strength
        if len(password) < 12:
            click.echo(
                click.style("  ✗ Password must be at least 12 characters.", fg="red")
            )
            continue

        if not re.search(r"[a-z]", password):
            click.echo(
                click.style(
                    "  ✗ Password must contain at least one lowercase letter.", fg="red"
                )
            )
            continue

        if not re.search(r"[A-Z]", password):
            click.echo(
                click.style(
                    "  ✗ Password must contain at least one uppercase letter.", fg="red"
                )
            )
            continue

        if not re.search(r"\d", password):
            click.echo(
                click.style("  ✗ Password must contain at least one number.", fg="red")
            )
            continue

        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
            click.echo(
                click.style(
                    "  ✗ Password must contain at least one special character.",
                    fg="red",
                )
            )
            continue

        password_confirm = getpass.getpass("  Confirm master password: ")
        if password != password_confirm:
            click.echo(click.style("  ✗ Passwords don't match!", fg="red"))
            continue

        password_set = True

    click.echo()
    click.echo("  Enabling encryption...")

    try:
        if crypto.enable_encryption(password):
            click.echo("  " + click.style("✓ Encryption enabled!", fg="green"))
        else:
            click.echo("  " + click.style("✗ Failed to enable encryption!", fg="red"))
            click.pause("  Press any key to continue...")
            return False
    except Exception as e:
        click.echo("  " + click.style(f"✗ Error: {e}", fg="red"))
        click.pause("  Press any key to continue...")
        return False

    click.pause("  Press any key to continue...")
    return True


def _wizard_create_engagement() -> dict:
    """Create first engagement."""
    from souleyez.storage.engagements import EngagementManager

    DesignSystem.clear_screen()
    _show_wizard_banner()
    width = 60

    click.echo("┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            " STEP 3: CREATE YOUR ENGAGEMENT ".center(width - 2), bold=True, fg="cyan"
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()
    click.echo("  An engagement organizes all your work for a specific target.")
    click.echo(
        "  Give it a descriptive name like 'Acme Corp Pentest' or 'HackTheBox Lab'."
    )
    click.echo()

    name = click.prompt("  Engagement Name").strip()

    # Require a name
    while not name:
        click.echo(click.style("  ✗ Name is required!", fg="red"))
        name = click.prompt("  Engagement Name").strip()

    click.echo()
    click.echo("  " + click.style("Engagement Type:", bold=True))
    click.echo("    [1] Penetration Test  - Full-scope security assessment")
    click.echo("    [2] Bug Bounty        - Vulnerability hunting with defined scope")
    click.echo(
        "    [3] CTF / Lab         - Practice environment, aggressive scanning OK"
    )
    click.echo("    [4] Red Team          - Adversary simulation, stealth preferred")
    click.echo("    [5] Custom            - Define your own")
    click.echo()
    click.echo(
        "  "
        + click.style("NOTE:", fg="yellow")
        + " Type affects default automation and scan aggressiveness"
    )
    click.echo()

    type_choice = click.prompt(
        "  Select option", type=click.IntRange(1, 5), default=1, show_default=False
    )

    engagement_types = {
        1: "penetration_test",
        2: "bug_bounty",
        3: "ctf",
        4: "red_team",
        5: "custom",
    }

    engagement_type = engagement_types[type_choice]

    # Create engagement and set it as active
    em = EngagementManager()

    # Handle duplicate engagement names
    try:
        engagement_id = em.create_engagement(
            name, f"Created via Setup Wizard - Type: {engagement_type}"
        )
        click.echo()
        click.echo(
            "  "
            + click.style(
                f"✓ Engagement '{name}' created and set as active!", fg="green"
            )
        )
    except ValueError as e:
        if "already exists" in str(e):
            click.echo()
            click.echo(
                "  " + click.style(f"Engagement '{name}' already exists.", fg="yellow")
            )
            click.echo("  " + click.style("✓ Using existing engagement.", fg="green"))
            # Get existing engagement ID
            existing = em.get_engagement(name)
            engagement_id = existing["id"] if existing else None
        else:
            raise

    em.set_current(name)  # Set as active so user drops into this engagement
    click.pause("  Press any key to continue...")

    return {"id": engagement_id, "name": name, "type": engagement_type}


def _wizard_tool_check() -> dict:
    """Check installed tools using the centralized tool_checker module."""
    from souleyez.utils.tool_checker import (
        EXTERNAL_TOOLS,
        check_tool_version,
        detect_distro,
        get_install_command,
        get_tool_version,
        get_upgrade_command,
    )

    DesignSystem.clear_screen()
    _show_wizard_banner()
    width = 60
    distro = detect_distro()

    click.echo("┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            " STEP 4: TOOL AVAILABILITY ".center(width - 2), bold=True, fg="cyan"
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()
    click.echo("  Checking installed tools...")
    click.echo()

    # Core tools to check in the wizard (subset of full tool list)
    # Maps display name -> tool_checker key (category, tool_name)
    wizard_tools = {
        "nmap": ("reconnaissance", "nmap"),
        "gobuster": ("web_scanning", "gobuster"),
        "sqlmap": ("exploitation", "sqlmap"),
        "nuclei": ("web_scanning", "nuclei"),
        "hydra": ("credential_attacks", "hydra"),
        "theHarvester": ("reconnaissance", "theharvester"),
        "wpscan": ("web_scanning", "wpscan"),
        "netexec": ("windows_ad", "netexec"),
        "enum4linux": ("windows_ad", "enum4linux"),
        "dnsrecon": ("reconnaissance", "dnsrecon"),
        "whois": ("reconnaissance", "whois"),
    }

    found = 0
    total = len(wizard_tools)
    tool_status = {}
    wrong_version_tools = []
    missing_tools = []

    for display_name, (category, tool_key) in wizard_tools.items():
        tool_info = EXTERNAL_TOOLS[category][tool_key]
        command = tool_info["command"]

        # Use version-aware check
        version_status = check_tool_version(tool_info)

        if version_status["installed"]:
            # Use the actual command that was found (may be primary or alt)
            actual_cmd = version_status.get("actual_command") or command
            path = shutil.which(actual_cmd)

            # Try to get version for display (even if no min_version requirement)
            version_str = version_status["version"]
            if not version_str:
                # Try to get version using the actual found command
                version_str = get_tool_version(actual_cmd)

            # Check if version is OK
            if version_status["needs_upgrade"]:
                # Tool installed but wrong version
                ver_display = version_str or "unknown"
                min_ver = version_status["min_version"]
                click.echo(
                    f"  {click.style('!', fg='yellow')} {display_name:<15} v{ver_display} "
                    + click.style(f"(needs v{min_ver}+)", fg="yellow")
                )
                tool_status[display_name] = {
                    "found": True,
                    "path": path,
                    "version": ver_display,
                    "needs_upgrade": True,
                }
                wrong_version_tools.append(
                    {
                        "name": display_name,
                        "installed": ver_display,
                        "required": min_ver,
                        "install": get_upgrade_command(tool_info, distro)
                        or get_install_command(tool_info, distro),
                        "note": version_status.get("version_note"),
                        "tool_info": tool_info,
                    }
                )
                found += 1  # Still counts as found, just needs upgrade
            else:
                # Tool installed with correct version
                ver_display = f"v{version_str}" if version_str else ""
                click.echo(
                    f"  {click.style('✓', fg='green')} {display_name:<15} Found {ver_display}"
                )
                tool_status[display_name] = {
                    "found": True,
                    "path": path,
                    "version": version_str,
                }
                found += 1
        else:
            click.echo(f"  {click.style('✗', fg='red')} {display_name:<15} NOT FOUND")
            tool_status[display_name] = {"found": False, "path": None}
            missing_tools.append(
                {
                    "name": display_name,
                    "install": get_install_command(tool_info, distro),
                    "tool_info": tool_info,
                }
            )

    click.echo()
    click.echo(f"  Found {found}/{total} recommended tools")

    # Show version warnings
    if wrong_version_tools:
        click.echo()
        click.echo("  " + click.style("VERSION ISSUES:", fg="yellow", bold=True))
        for tool in wrong_version_tools:
            click.echo(
                f"    - {tool['name']}: installed v{tool['installed']}, needs v{tool['required']}+"
            )
            if tool.get("note"):
                click.echo(f"      {click.style(tool['note'], fg='bright_black')}")

    # Offer to install/upgrade tools
    if missing_tools or wrong_version_tools:
        click.echo()
        # Run the install flow (will prompt user)
        if _run_tool_installs(missing_tools, wrong_version_tools, distro):
            # Re-check tools after install
            click.echo()
            click.echo("  Re-checking tool availability...")
            click.echo()

            found = 0
            wrong_version_tools = []
            for display_name, (category, tool_key) in wizard_tools.items():
                tool_info = EXTERNAL_TOOLS[category][tool_key]
                version_status = check_tool_version(tool_info)

                if version_status["installed"] and not version_status["needs_upgrade"]:
                    tool_status[display_name] = {
                        "found": True,
                        "path": shutil.which(tool_info["command"]),
                    }
                    found += 1
                elif version_status["installed"] and version_status["needs_upgrade"]:
                    tool_status[display_name] = {"found": True, "needs_upgrade": True}
                    wrong_version_tools.append({"name": display_name})
                    found += 1
                else:
                    tool_status[display_name] = {"found": False, "path": None}

            click.echo(f"  Now have {found}/{total} tools available")

    click.echo()
    click.pause("  Press any key to continue...")

    return {
        "found": found,
        "total": total,
        "tools": tool_status,
        "wrong_version": wrong_version_tools,
    }


def _wizard_ai_setup() -> bool:
    """Set up AI features with Ollama."""
    import subprocess
    import time

    DesignSystem.clear_screen()
    _show_wizard_banner()
    width = 60

    click.echo("┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            " STEP 5: AI FEATURES (OPTIONAL) ".center(width - 2), bold=True, fg="cyan"
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()
    click.echo("  SoulEyez can use AI to suggest scanning strategies and")
    click.echo(
        "  prioritize targets. This requires "
        + click.style("Ollama", bold=True)
        + " (local AI runtime)."
    )
    click.echo()

    # Check if Ollama is installed
    ollama_path = shutil.which("ollama")

    if ollama_path:
        click.echo("  " + click.style("✓", fg="green") + " Ollama is installed")

        # Check if it's running
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                click.echo("  " + click.style("✓", fg="green") + " Ollama is running")

                # Check for models
                import json

                try:
                    data = json.loads(result.stdout)
                    models = data.get("models", [])
                    if models:
                        click.echo(
                            f"  "
                            + click.style("✓", fg="green")
                            + f" {len(models)} model(s) available"
                        )
                        click.echo()
                        click.echo(
                            "  "
                            + click.style(
                                "AI features are ready!", fg="green", bold=True
                            )
                        )
                        click.echo()
                        click.pause("  Press any key to continue...")
                        return True
                    else:
                        click.echo(
                            "  "
                            + click.style("!", fg="yellow")
                            + " No models installed"
                        )
                except:
                    pass

                # Offer to pull a model
                click.echo()
                click.echo("  Would you like to download a model now?")
                click.echo(
                    "  Recommended: "
                    + click.style("llama3.1:8b", fg="cyan")
                    + " (~4.7GB)"
                )
                click.echo()

                try:
                    response = input("  Download model? (y/n): ").strip().lower()
                    if response == "y":
                        return _pull_ollama_model()
                except (KeyboardInterrupt, EOFError):
                    click.echo("\n  Skipped.")

                click.pause("  Press any key to continue...")
                return False
            else:
                # Ollama installed but not running
                click.echo(
                    "  " + click.style("!", fg="yellow") + " Ollama is not running"
                )
                return _start_ollama_and_setup()

        except subprocess.TimeoutExpired:
            click.echo(
                "  " + click.style("!", fg="yellow") + " Ollama is not responding"
            )
            return _start_ollama_and_setup()
        except FileNotFoundError:
            # curl not found, try another method
            pass

    else:
        # Ollama not installed - offer to install
        click.echo("  " + click.style("!", fg="yellow") + " Ollama is not installed")
        click.echo()
        click.echo("  Would you like to install Ollama now?")
        click.echo("  This will download and install the Ollama runtime (~100MB).")
        click.echo()

        try:
            response = input("  Install Ollama? (y/n): ").strip().lower()
            if response == "y":
                return _install_ollama()
        except (KeyboardInterrupt, EOFError):
            click.echo("\n  Skipped.")

    click.echo()
    click.echo(
        "  "
        + click.style("Skipping AI setup.", fg="bright_black")
        + " You can enable it later in Settings."
    )
    click.pause("  Press any key to continue...")
    return False


def _install_ollama() -> bool:
    """Install Ollama using the official install script."""
    import subprocess

    click.echo()
    click.echo("  Installing Ollama...")
    click.echo(
        "  "
        + click.style(
            "(This may take a minute - downloading ~100MB)", fg="bright_black"
        )
    )
    click.echo()

    try:
        # Run the official Ollama install script with timeout
        # Add curl timeouts to fail faster on network issues
        result = subprocess.run(
            [
                "bash",
                "-c",
                "curl --connect-timeout 30 --max-time 300 -fsSL https://ollama.ai/install.sh | sh",
            ],
            check=False,
            timeout=360,  # 6 minute total timeout
        )

        if result.returncode == 0:
            click.echo()
            click.echo(
                "  " + click.style("✓ Ollama installed successfully!", fg="green")
            )

            # Start Ollama and set up model
            return _start_ollama_and_setup()
        else:
            click.echo()
            click.echo("  " + click.style("✗ Installation failed", fg="red"))
            click.echo(
                "  "
                + click.style(
                    "This is usually a network issue (slow connection or timeout).",
                    fg="yellow",
                )
            )
            click.echo()
            click.echo("  To install manually:")
            click.echo("    curl -fsSL https://ollama.ai/install.sh | sh")
            click.echo()
            click.echo("  Or visit: https://ollama.ai")
            click.pause("  Press any key to continue...")
            return False

    except subprocess.TimeoutExpired:
        click.echo()
        click.echo("  " + click.style("✗ Installation timed out", fg="red"))
        click.echo(
            "  "
            + click.style(
                "The download took too long. Check your internet connection.",
                fg="yellow",
            )
        )
        click.echo()
        click.echo("  To install manually:")
        click.echo("    curl -fsSL https://ollama.ai/install.sh | sh")
        click.pause("  Press any key to continue...")
        return False

    except Exception as e:
        click.echo()
        click.echo(click.style(f"  ✗ Error: {e}", fg="red"))
        click.echo("  You can install manually from https://ollama.ai")
        click.pause("  Press any key to continue...")
        return False


def _start_ollama_and_setup() -> bool:
    """Start Ollama service and optionally pull a model."""
    import subprocess
    import time

    click.echo()
    click.echo("  Starting Ollama service...")

    try:
        # Start ollama serve in background
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        # Wait for it to start
        click.echo("  Waiting for Ollama to start...")
        time.sleep(3)

        # Verify it's running
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            capture_output=True,
            timeout=5,
        )

        if result.returncode == 0:
            click.echo("  " + click.style("✓ Ollama started!", fg="green"))

            # Offer to pull model
            click.echo()
            click.echo("  Would you like to download a model now?")
            click.echo(
                "  Recommended: " + click.style("llama3.1:8b", fg="cyan") + " (~4.7GB)"
            )
            click.echo()

            try:
                response = input("  Download model? (y/n): ").strip().lower()
                if response == "y":
                    return _pull_ollama_model()
            except (KeyboardInterrupt, EOFError):
                click.echo("\n  Skipped.")

            click.pause("  Press any key to continue...")
            return True
        else:
            click.echo("  " + click.style("✗ Failed to start Ollama", fg="red"))
            click.pause("  Press any key to continue...")
            return False

    except Exception as e:
        click.echo(click.style(f"  ✗ Error: {e}", fg="red"))
        click.pause("  Press any key to continue...")
        return False


def _pull_ollama_model() -> bool:
    """Pull the recommended Ollama model."""
    import subprocess

    model = "llama3.1:8b"

    click.echo()
    click.echo(f"  Downloading {model}...")
    click.echo(
        "  "
        + click.style(
            "(This may take several minutes depending on your connection)",
            fg="bright_black",
        )
    )
    click.echo()

    try:
        # Run ollama pull and let it output directly to terminal for proper progress bar
        result = subprocess.run(["ollama", "pull", model], check=False)

        if result.returncode == 0:
            click.echo()
            click.echo("  " + click.style(f"✓ Model {model} ready!", fg="green"))
            click.echo()
            click.echo(
                "  "
                + click.style("AI features are now enabled!", fg="green", bold=True)
            )
            click.pause("  Press any key to continue...")
            return True
        else:
            click.echo()
            click.echo("  " + click.style("✗ Failed to download model", fg="red"))
            click.echo("  You can try later with: ollama pull " + model)
            click.pause("  Press any key to continue...")
            return False

    except Exception as e:
        click.echo(click.style(f"  ✗ Error: {e}", fg="red"))
        click.pause("  Press any key to continue...")
        return False


def _wizard_automation_prefs() -> dict:
    """Configure automation preferences."""
    DesignSystem.clear_screen()
    _show_wizard_banner()
    width = 60

    click.echo("┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            " STEP 6: AUTOMATION PREFERENCES ".center(width - 2), bold=True, fg="cyan"
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()
    click.echo("  SoulEyez can automatically chain tools based on discoveries.")
    click.echo("  Example: Finding port 80 → auto-run gobuster + nuclei")
    click.echo()
    click.echo("  " + click.style("Chain Mode:", bold=True))
    click.echo("    [1] AUTO     - Execute chains immediately (recommended for labs)")
    click.echo("    [2] APPROVAL - Queue chains for your approval first")
    click.echo("    [3] DISABLED - No automatic chaining")
    click.echo()

    mode_choice = click.prompt("  Select option", type=click.IntRange(1, 3), default=1)

    if mode_choice == 3:
        click.echo()
        click.echo(f"  {click.style('✓', fg='green')} Auto-chaining disabled")
        click.pause("  Press any key to continue...")
        return {"enabled": False, "mode": None}

    mode = "auto" if mode_choice == 1 else "approval"

    click.echo()
    click.echo(
        f"  {click.style('✓', fg='green')} Auto-chaining enabled in {mode.upper()} mode"
    )
    click.pause("  Press any key to continue...")

    return {"enabled": True, "mode": mode}


def _wizard_deliverables(engagement_type: str) -> list:
    """Select deliverable templates."""
    DesignSystem.clear_screen()
    _show_wizard_banner()
    width = 60

    click.echo("┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            " STEP 7: REPORT TEMPLATES ".center(width - 2), bold=True, fg="cyan"
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()
    click.echo("  Pre-select report templates that will be available for export.")
    click.echo("  You can change these later in Reports & Export menu.")
    click.echo()
    click.echo(
        "  "
        + click.style("NOTE:", fg="yellow")
        + " Templates help generate professional reports from your findings"
    )
    click.echo()

    # Default templates based on engagement type
    type_templates = {
        "penetration_test": [
            "Executive Summary",
            "Technical Findings Report",
            "Vulnerability Details",
        ],
        "bug_bounty": ["Vulnerability Details", "Proof of Concept"],
        "ctf": ["Technical Findings Report", "Attack Narrative"],
        "red_team": ["Attack Narrative", "Remediation Roadmap"],
        "custom": ["Technical Findings Report"],
    }

    recommended = type_templates.get(engagement_type, ["Technical Findings Report"])

    click.echo(f"  Recommended for {engagement_type.replace('_', ' ').title()}:")
    for template in recommended:
        click.echo(f"    {click.style('✓', fg='green')} {template}")

    click.echo()
    click.echo(f"  {click.style('✓', fg='green')} Templates configured!")
    click.pause("  Press any key to continue...")

    return recommended


def _wizard_summary(
    encryption_enabled,
    engagement_info,
    tool_status,
    ai_enabled,
    automation_prefs,
    templates,
    is_pro=False,
):
    """Show wizard summary."""
    DesignSystem.clear_screen()
    _show_wizard_banner()
    width = 60

    # Adjust step number based on tier
    step_num = "8" if is_pro else "6"
    click.echo("┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(
            f" STEP {step_num}: SETUP COMPLETE! ".center(width - 2),
            bold=True,
            fg="green",
        )
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    # Summary
    enc_status = (
        click.style("Enabled", fg="green")
        if encryption_enabled
        else click.style("Disabled", fg="yellow")
    )
    click.echo(f"  {click.style('✓', fg='green')} Encryption: {enc_status}")

    eng_name = engagement_info["name"]
    eng_type = engagement_info["type"].replace("_", " ").title()
    click.echo(
        f"  {click.style('✓', fg='green')} Engagement: \"{eng_name}\" ({eng_type})"
    )

    tools_found = tool_status["found"]
    tools_total = tool_status["total"]
    click.echo(
        f"  {click.style('✓', fg='green')} Tools: {tools_found}/{tools_total} available"
    )

    # AI status
    if ai_enabled:
        click.echo(f"  {click.style('✓', fg='green')} AI Features: Enabled (Ollama)")
    else:
        click.echo(
            f"  {click.style('○', fg='bright_black')} AI Features: Not configured"
        )

    # Show tier status
    if is_pro:
        click.echo(f"  {click.style('💎', fg='magenta')} License: PRO")
        if automation_prefs["enabled"]:
            auto_mode = automation_prefs["mode"].upper()
            click.echo(
                f"  {click.style('✓', fg='green')} Auto-Chain: ON ({auto_mode} mode)"
            )
        else:
            click.echo(f"  {click.style('✓', fg='green')} Auto-Chain: OFF")

        if templates:
            click.echo(
                f"  {click.style('✓', fg='green')} Templates: {len(templates)} selected"
            )
    else:
        click.echo(f"  {click.style('○', fg='bright_black')} License: FREE")
        click.echo()
        click.echo(click.style("  Upgrade to Pro for:", fg="yellow"))
        click.echo("    • AI Execute - Autonomous exploitation")
        click.echo("    • Automation - Smart tool chaining")
        click.echo("    • MSF Integration - Advanced attack chains")
        click.echo("    • Reports - Professional deliverables")
        click.echo(f"    {click.style('→ cybersoulsecurity.com/upgrade', fg='cyan')}")

    click.echo()
    click.echo("  " + click.style("You're ready to start!", bold=True, fg="cyan"))
    click.echo()

    # Install desktop shortcut automatically
    _install_desktop_shortcut()

    # Prompt for interactive tutorial
    click.echo("  ┌" + "─" * 56 + "┐")
    click.echo(
        "  │"
        + click.style(
            " Would you like to run the interactive tutorial?", fg="cyan"
        ).center(65)
        + "│"
    )
    click.echo(
        "  │" + " Recommended for new users - takes about 5 minutes".center(56) + "│"
    )
    click.echo("  └" + "─" * 56 + "┘")
    click.echo()
    click.echo(
        "  " + click.style("[Y]", fg="green", bold=True) + " Yes, show me around"
    )
    click.echo("  " + click.style("[n]", fg="bright_black") + " No, go to main menu")
    click.echo()

    choice = (
        click.prompt("  Run tutorial?", default="y", show_default=False).strip().lower()
    )

    if choice in ("y", "yes", ""):
        from souleyez.ui.tutorial import run_tutorial

        run_tutorial()
    else:
        click.echo()
        click.echo(
            "  "
            + click.style("No problem!", fg="cyan")
            + " You can run the tutorial anytime from:"
        )
        click.echo(
            "  " + click.style("Settings & Security → [t] Tutorial", fg="yellow")
        )
        click.echo()
        click.pause("  Press any key to continue to main menu...")
