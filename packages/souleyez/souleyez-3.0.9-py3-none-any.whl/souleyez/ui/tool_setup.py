#!/usr/bin/env python3
"""
souleyez.ui.tool_setup - Tool installation wizard for Ubuntu/Debian systems

Helps users install pentesting tools that aren't available via apt on Ubuntu.
Handles PATH configuration for go and pipx installed tools.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import click

from souleyez.ui.design_system import DesignSystem
from souleyez.utils.tool_checker import (
    EXTERNAL_TOOLS,
    check_tool,
    detect_distro,
    get_category_name,
    get_missing_tools,
    get_tool_stats,
    get_tools_by_category,
)


def _reset_terminal():
    """Reset terminal to sane state after interrupt."""
    try:
        # Reset terminal using stty
        subprocess.run(["stty", "sane"], check=False, timeout=5)
        # Also try the reset command for good measure
        subprocess.run(
            ["reset", "-I"],
            check=False,
            timeout=5,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


# Prerequisites needed for various install methods
PREREQUISITES = {
    "build-deps": {
        "check": None,  # Always install to ensure all deps present
        "install": "sudo apt-get -o DPkg::Lock::Timeout=120 install -y build-essential python3-dev libxml2-dev libxslt1-dev libuv1-dev libffi-dev libssl-dev rustc cargo",
        "description": "Build dependencies for Python packages with native extensions",
        "always_install": True,  # Flag to always run this
    },
    "pipx": {
        "check": "pipx",
        "install": "sudo apt-get -o DPkg::Lock::Timeout=120 install -y pipx && pipx ensurepath",
        "description": "Python application installer (for theHarvester, NetExec, etc.)",
        "path_additions": ["~/.local/bin"],
    },
    "golang": {
        "check": "go",
        "install": "sudo apt-get -o DPkg::Lock::Timeout=120 install -y golang-go",
        "description": "Go programming language (for nuclei, ffuf)",
        "path_additions": ["~/go/bin"],
    },
    "ruby": {
        "check": "gem",
        "install": "sudo apt-get -o DPkg::Lock::Timeout=120 install -y ruby-full ruby-dev build-essential",
        "description": "Ruby programming language (for wpscan)",
    },
    "snap": {
        "check": "snap",
        "install": "sudo apt-get -o DPkg::Lock::Timeout=120 install -y snapd",
        "description": "Snap package manager (for enum4linux)",
    },
    "git": {
        "check": "git",
        "install": "sudo apt-get -o DPkg::Lock::Timeout=120 install -y git",
        "description": "Git version control (for exploitdb, Responder)",
    },
}


def _ensure_path_configured():
    """Ensure go and pipx paths are in current session PATH."""
    home = os.path.expanduser("~")
    paths_to_add = [
        os.path.join(home, "go", "bin"),
        os.path.join(home, ".local", "bin"),
        "/snap/bin",
    ]

    current_path = os.environ.get("PATH", "")
    new_paths = []

    for p in paths_to_add:
        if os.path.exists(p) and p not in current_path:
            new_paths.append(p)

    if new_paths:
        os.environ["PATH"] = ":".join(new_paths) + ":" + current_path


def _add_paths_to_shell_rc():
    """Add tool paths to shell rc files (bash and zsh) if not already present."""
    paths_to_add = [
        ('export PATH="$HOME/go/bin:$PATH"', "go/bin"),
        ('export PATH="$HOME/.local/bin:$PATH"', ".local/bin"),
    ]

    # Update both .bashrc and .zshrc (Kali Linux uses zsh by default)
    rc_files = [
        Path.home() / ".bashrc",
        Path.home() / ".zshrc",
    ]

    for rc_file in rc_files:
        if not rc_file.exists():
            continue

        try:
            content = rc_file.read_text()
            additions = []

            for line, marker in paths_to_add:
                if marker not in content:
                    additions.append(line)

            if additions:
                with open(rc_file, "a") as f:
                    f.write("\n# Added by souleyez setup\n")
                    for line in additions:
                        f.write(line + "\n")
        except Exception:
            pass  # Don't fail on PATH configuration issues


def _run_command(
    cmd: str, console, description: str = "", capture: bool = False
) -> tuple:
    """Run a command with proper error handling."""
    import sys

    try:
        # Never capture sudo commands - password prompt needs to be visible
        if cmd.strip().startswith("sudo"):
            capture = False
            # Flush output and print newline so sudo prompt appears on new line
            sys.stdout.flush()
            sys.stderr.flush()
            print()  # Newline for sudo password prompt

        if capture:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(
                cmd,
                shell=True,
                stdin=sys.stdin,  # Ensure stdin is connected for password input
                timeout=600,
            )
            return result.returncode == 0, "", ""
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


# Tools that need privileged access
# Binary tools: simple executables that need sudo
PRIVILEGED_BINARY_TOOLS = ["nmap"]

# Script-based tools: need sudo to run interpreter + script
# Format: {'name': {'interpreter': path, 'script_paths': [possible locations], 'description': str}}
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


def _check_sudoers_configured_binary(tool_name: str) -> bool:
    """Check if passwordless sudo is configured for a binary tool."""
    tool_path = shutil.which(tool_name)
    if not tool_path:
        return True  # Not installed, nothing to configure

    # Try running sudo -n (non-interactive) to see if NOPASSWD is set
    try:
        subprocess.run(["sudo", "-k"], capture_output=True, timeout=5)
        result = subprocess.run(
            ["sudo", "-n", tool_path, "--version"], capture_output=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def _check_sudoers_configured_script(interpreter: str, script_path: str) -> bool:
    """Check if passwordless sudo is configured for a script-based tool."""
    if not Path(script_path).exists():
        return True  # Script not found, nothing to configure

    # Try running sudo -n with interpreter + script
    try:
        subprocess.run(["sudo", "-k"], capture_output=True, timeout=5)
        result = subprocess.run(
            ["sudo", "-n", interpreter, script_path, "--help"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def _configure_sudoers(console):
    """Configure passwordless sudo for privileged tools."""
    import getpass

    binary_tools_to_configure = []
    script_tools_to_configure = []

    # Check binary tools
    for tool_name in PRIVILEGED_BINARY_TOOLS:
        tool_path = shutil.which(tool_name)
        if tool_path and not _check_sudoers_configured_binary(tool_name):
            binary_tools_to_configure.append((tool_name, tool_path))

    # Check script-based tools
    for tool_name, tool_info in PRIVILEGED_SCRIPT_TOOLS.items():
        script_path = _find_script_path(tool_info["script_paths"])
        if script_path:
            interpreter = tool_info["interpreter"]
            if not _check_sudoers_configured_script(interpreter, script_path):
                script_tools_to_configure.append(
                    (tool_name, interpreter, script_path, tool_info["description"])
                )

    if not binary_tools_to_configure and not script_tools_to_configure:
        return  # All configured or not installed

    console.print()
    console.print("  " + "═" * 60)
    console.print("[bold cyan]  PRIVILEGED SCAN SETUP[/bold cyan]")
    console.print()
    console.print(
        "  Some scans require root privileges (SYN scans, credential capture)."
    )
    console.print("  SoulEyez can configure passwordless sudo so these scans")
    console.print("  work automatically without running as root.")
    console.print()
    console.print("  Tools to configure:")
    for tool_name, tool_path in binary_tools_to_configure:
        console.print(f"    • {tool_name} ({tool_path})")
    for tool_name, interpreter, script_path, description in script_tools_to_configure:
        console.print(f"    • {tool_name} ({description})")
    console.print()

    if not click.confirm(
        "  Configure passwordless sudo for these tools?", default=True
    ):
        console.print()
        console.print(
            "  [yellow]Skipped.[/yellow] Privileged scans will require running as root."
        )
        console.print("  Run 'souleyez setup --fix-permissions' later to configure.")
        return

    console.print()

    username = getpass.getuser()

    # Configure binary tools
    for tool_name, tool_path in binary_tools_to_configure:
        sudoers_file = f"/etc/sudoers.d/{tool_name}"
        sudoers_line = f"{username} ALL=(ALL) NOPASSWD: {tool_path}"

        try:
            cmd = f"printf '%s\\n' '{sudoers_line}' | sudo tee {sudoers_file} > /dev/null && sudo chmod 0440 {sudoers_file}"
            proc = subprocess.run(cmd, shell=True, timeout=60)  # nosec B602

            if proc.returncode == 0:
                console.print(
                    f"    [green]✓[/green] {tool_name} - configured for privileged scans"
                )
            else:
                console.print(f"    [red]✗[/red] {tool_name} - failed to configure")
        except subprocess.TimeoutExpired:
            console.print(f"    [red]✗[/red] {tool_name} - sudo timed out")
        except Exception as e:
            console.print(f"    [red]✗[/red] {tool_name} - {e}")

    # Configure script-based tools
    for tool_name, interpreter, script_path, description in script_tools_to_configure:
        sudoers_file = f"/etc/sudoers.d/souleyez-{tool_name}"
        # Allow interpreter to run the specific script with any arguments
        sudoers_line = f"{username} ALL=(ALL) NOPASSWD: {interpreter} {script_path} *"

        try:
            cmd = f"printf '%s\\n' '{sudoers_line}' | sudo tee {sudoers_file} > /dev/null && sudo chmod 0440 {sudoers_file}"
            proc = subprocess.run(cmd, shell=True, timeout=60)  # nosec B602

            if proc.returncode == 0:
                console.print(
                    f"    [green]✓[/green] {tool_name} - configured for privileged scans"
                )
            else:
                console.print(f"    [red]✗[/red] {tool_name} - failed to configure")
        except subprocess.TimeoutExpired:
            console.print(f"    [red]✗[/red] {tool_name} - sudo timed out")
        except Exception as e:
            console.print(f"    [red]✗[/red] {tool_name} - {e}")

    console.print()


def _ensure_msfdb_initialized(console):
    """Ensure Metasploit database is initialized if MSF is installed."""
    from pathlib import Path

    # Check if msfdb exists (either apt install or official installer)
    msfdb_path = shutil.which("msfdb")
    if not msfdb_path:
        # Try the official installer path
        msfdb_path = "/opt/metasploit-framework/bin/msfdb"
        if not Path(msfdb_path).exists():
            return  # Metasploit not installed

    # Check if database is already initialized by looking for database.yml
    user_db_yml = Path.home() / ".msf4" / "database.yml"
    if user_db_yml.exists():
        return  # Already initialized

    console.print()
    console.print("  " + "═" * 60)
    console.print("[bold cyan]  METASPLOIT DATABASE SETUP[/bold cyan]")
    console.print()
    console.print("  Metasploit is installed but the database isn't initialized.")
    console.print("  The database enables faster searches and session tracking.")
    console.print()

    if not click.confirm("  Initialize MSF database now?", default=True):
        console.print()
        console.print(
            "  [yellow]Skipped.[/yellow] Run 'sudo msfdb init' manually when needed."
        )
        return

    console.print()
    console.print("  [dim]Initializing MSF database (this may take a minute)...[/dim]")

    try:
        # Distro-aware msfdb init:
        # - Kali/Parrot (apt install): requires sudo
        # - Ubuntu/Debian (omnibus installer): must run as normal user, NOT root
        distro = detect_distro()
        if distro in ("kali", "parrot"):
            msfdb_cmd = ["sudo", msfdb_path, "init"]
        else:
            msfdb_cmd = [msfdb_path, "init"]

        result = subprocess.run(
            msfdb_cmd,
            capture_output=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            console.print("  [green]✓ MSF database initialized[/green]")

            # Copy database.yml to /root/.msf4/ so sudo msfconsole can connect
            user_db_yml = Path.home() / ".msf4" / "database.yml"
            if user_db_yml.exists():
                console.print("  [dim]Configuring sudo access to MSF database...[/dim]")
                try:
                    subprocess.run(
                        ["sudo", "mkdir", "-p", "/root/.msf4"], capture_output=True
                    )
                    copy_result = subprocess.run(
                        ["sudo", "cp", str(user_db_yml), "/root/.msf4/database.yml"],
                        capture_output=True,
                    )
                    if copy_result.returncode == 0:
                        console.print("  [green]✓ Sudo MSF access configured[/green]")
                    else:
                        console.print(
                            "  [yellow]⚠ Run: sudo cp ~/.msf4/database.yml /root/.msf4/[/yellow]"
                        )
                except Exception:
                    console.print(
                        "  [yellow]⚠ Run: sudo cp ~/.msf4/database.yml /root/.msf4/[/yellow]"
                    )
        else:
            stderr = result.stderr.decode() if result.stderr else ""
            if "already" in stderr.lower():
                console.print("  [green]✓ MSF database already initialized[/green]")
            else:
                console.print(f"  [yellow]⚠ msfdb init failed (run manually)[/yellow]")
    except subprocess.TimeoutExpired:
        console.print("  [yellow]⚠ msfdb init timed out (run manually)[/yellow]")
    except Exception as e:
        console.print(
            f"  [yellow]⚠ Could not init MSF database: {str(e)[:40]}[/yellow]"
        )

    console.print()


def run_tool_setup(check_only: bool = False, install_all: bool = False):
    """Run the tool setup wizard."""
    try:
        _run_tool_setup_impl(check_only, install_all)
    except KeyboardInterrupt:
        # Reset terminal to sane state after Ctrl+C
        _reset_terminal()
        print("\n\n  Setup cancelled.")
        raise


def _run_tool_setup_impl(check_only: bool = False, install_all: bool = False):
    """Internal implementation of tool setup wizard."""
    console = DesignSystem.get_console()
    distro = detect_distro()

    # Ensure paths are configured for this session
    _ensure_path_configured()

    # Header
    DesignSystem.clear_screen()
    console.print()
    console.print(
        "[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]"
    )
    console.print(
        "[bold cyan]║              SOULEYEZ TOOL SETUP WIZARD                      ║[/bold cyan]"
    )
    console.print(
        "[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]"
    )
    console.print()

    # Distro detection
    distro_names = {
        "kali": "Kali Linux",
        "parrot": "Parrot OS",
        "ubuntu": "Ubuntu",
        "debian": "Debian",
        "unknown": "Unknown Linux",
    }
    console.print(f"  Detected OS: [bold]{distro_names.get(distro, distro)}[/bold]")
    console.print()

    # Show distro-specific messaging
    if distro in ("kali", "parrot"):
        console.print("  [green]✓ You're on a pentesting distro![/green]")
        console.print(
            "    Most tools are available via apt. Some may use pipx or direct download."
        )
        console.print()
    elif distro in ("ubuntu", "debian"):
        console.print(
            "  [yellow]Note:[/yellow] Some pentesting tools aren't in Ubuntu/Debian repos."
        )
        console.print(
            "  This wizard will install them using pipx, go, snap, or from source."
        )
        console.print()

    _show_tool_status(console)

    if check_only:
        return

    missing = get_missing_tools(distro)
    if not missing:
        console.print()
        console.print("  [green]✓ All tools are installed![/green]")
        # Still need to run post-install tasks (sudoers, MSF db, etc.)
        _run_post_install_tasks(console, distro)
        return

    console.print()
    console.print(f"  [yellow]⚠ {len(missing)} tools need installation[/yellow]")
    console.print()

    if not install_all:
        if not click.confirm("  Proceed with installation?", default=True):
            console.print("  Setup cancelled.")
            return

    # Check and install prerequisites first
    _check_prerequisites(console, missing, distro)

    # Group tools by install method for smarter ordering
    apt_tools = [t for t in missing if t["install_method"] == "apt"]
    pipx_tools = [t for t in missing if "pipx" in t["install"]]
    go_tools = [t for t in missing if "go install" in t["install"]]
    gem_tools = [t for t in missing if "gem install" in t["install"]]
    snap_tools = [t for t in missing if "snap install" in t["install"]]
    git_tools = [t for t in missing if "git clone" in t["install"]]
    other_tools = [
        t
        for t in missing
        if t
        not in apt_tools + pipx_tools + go_tools + gem_tools + snap_tools + git_tools
    ]

    total_to_install = len(missing)
    installed_count = 0
    failed_tools = []

    # Install apt tools first (batch)
    if apt_tools:
        console.print()
        console.print("[bold cyan]  Installing apt packages...[/bold cyan]")
        success = _install_apt_tools(console, apt_tools)
        if success:
            installed_count += len(apt_tools)
        else:
            failed_tools.extend([t["name"] for t in apt_tools])

    # Install pipx tools
    if pipx_tools:
        console.print()
        console.print("[bold cyan]  Installing pipx packages...[/bold cyan]")
        for tool in pipx_tools:
            if _install_pipx_tool(console, tool):
                installed_count += 1
            else:
                failed_tools.append(tool["name"])

    # Install go tools
    if go_tools:
        console.print()
        console.print("[bold cyan]  Installing Go tools...[/bold cyan]")
        for tool in go_tools:
            if _install_go_tool(console, tool):
                installed_count += 1
            else:
                failed_tools.append(tool["name"])

    # Install gem tools
    if gem_tools:
        console.print()
        console.print("[bold cyan]  Installing Ruby gems...[/bold cyan]")
        for tool in gem_tools:
            if _install_gem_tool(console, tool):
                installed_count += 1
            else:
                failed_tools.append(tool["name"])

    # Install snap tools
    if snap_tools:
        console.print()
        console.print("[bold cyan]  Installing snap packages...[/bold cyan]")
        for tool in snap_tools:
            if _install_snap_tool(console, tool):
                installed_count += 1
            else:
                failed_tools.append(tool["name"])

    # Install git-based tools
    if git_tools:
        console.print()
        console.print("[bold cyan]  Installing from git...[/bold cyan]")
        for tool in git_tools:
            if _install_git_tool(console, tool):
                installed_count += 1
            else:
                failed_tools.append(tool["name"])

    # Install other tools (like metasploit)
    if other_tools:
        console.print()
        console.print("[bold cyan]  Installing additional tools...[/bold cyan]")
        for tool in other_tools:
            if _install_other_tool(console, tool):
                installed_count += 1
            else:
                failed_tools.append(tool["name"])

    # Configure PATH in shell rc files (bash and zsh)
    _add_paths_to_shell_rc()

    # Final status
    console.print()
    console.print("  " + "═" * 60)
    console.print("[bold cyan]  SETUP COMPLETE[/bold cyan]")
    console.print()

    if failed_tools:
        console.print(
            f"  [yellow]⚠ {len(failed_tools)} tools failed to install:[/yellow]"
        )
        for name in failed_tools:
            console.print(f"    • {name}")
        console.print()

    # Refresh PATH and show final status
    _ensure_path_configured()
    _show_tool_status(console)

    # Run post-install tasks
    _run_post_install_tasks(console, distro)


def _run_post_install_tasks(console, distro: str):
    """Run tasks that should happen after tool installation or when all tools are present."""
    # Ensure PATH is configured in shell rc files
    _add_paths_to_shell_rc()

    # Configure passwordless sudo for privileged scans
    _configure_sudoers(console)

    # Initialize MSF database if needed
    _ensure_msfdb_initialized(console)

    # Remind about PATH for pipx/go tools
    console.print()
    console.print("  [yellow]Important:[/yellow] To use newly installed tools, either:")
    console.print("    1. Restart your terminal, OR")
    if distro in ("kali", "parrot"):
        console.print("    2. Run: [cyan]source ~/.zshrc[/cyan]  (Kali uses zsh)")
    else:
        console.print("    2. Run: [cyan]source ~/.bashrc[/cyan]")
    console.print()


def _show_tool_status(console):
    """Display current tool installation status."""
    tools_by_cat = get_tools_by_category()
    installed, total = get_tool_stats()

    status_color = (
        "green" if installed == total else "yellow" if installed > 0 else "red"
    )
    console.print(
        f"  [bold]Tool Status:[/bold] [{status_color}]{installed}/{total} installed[/{status_color}]"
    )
    console.print()

    for category, tools in tools_by_cat.items():
        cat_name = get_category_name(category)
        console.print(f"  [bold]{cat_name}[/bold]")

        for tool in tools:
            if tool["installed"]:
                status = "[green]✓[/green]"
            else:
                status = "[red]✗[/red]"

            console.print(
                f"    {status} {tool['name']:<18} - {tool['description'][:40]}"
            )

        console.print()


def _check_prerequisites(console, missing_tools: List[Dict], distro: str):
    """Check and install prerequisites needed for tool installation."""
    needed_prereqs = set()

    for tool in missing_tools:
        install_cmd = tool["install"]
        if "pipx" in install_cmd:
            needed_prereqs.add("pipx")
            # pipx tools with native extensions need build dependencies
            needed_prereqs.add("build-deps")
        if "go install" in install_cmd:
            needed_prereqs.add("golang")
        if "gem install" in install_cmd:
            needed_prereqs.add("ruby")
        if "snap install" in install_cmd:
            needed_prereqs.add("snap")
        if "git clone" in install_cmd:
            needed_prereqs.add("git")

    missing_prereqs = []
    for prereq in needed_prereqs:
        info = PREREQUISITES[prereq]
        # Check if always_install flag is set, or if tool check fails
        if info.get("always_install") or (
            info.get("check") and not check_tool(info["check"])
        ):
            missing_prereqs.append((prereq, info))

    if not missing_prereqs:
        return

    # Sort to ensure build-deps comes first (needed before pipx installs)
    prereq_order = {
        "build-deps": 0,
        "pipx": 1,
        "golang": 2,
        "ruby": 3,
        "snap": 4,
        "git": 5,
    }
    missing_prereqs.sort(key=lambda x: prereq_order.get(x[0], 99))

    console.print()
    console.print("[bold cyan]  Installing prerequisites...[/bold cyan]")

    for prereq, info in missing_prereqs:
        console.print(f"    Installing {prereq}...", end=" ")
        success, _, stderr = _run_command(info["install"], console, capture=True)
        if success:
            console.print("[green]✓[/green]")

            # Run pipx ensurepath if we just installed pipx
            if prereq == "pipx":
                subprocess.run("pipx ensurepath", shell=True, capture_output=True)
        else:
            console.print(f"[red]✗[/red] {stderr[:50]}")

    # Update PATH after installing prerequisites
    _ensure_path_configured()


def _install_apt_tools(console, tools: List[Dict]) -> bool:
    """Install tools available via apt."""
    packages = []
    for tool in tools:
        cmd = tool["install"]
        if "apt install" in cmd:
            # Extract package name
            parts = cmd.split()
            for i, part in enumerate(parts):
                if part == "install" and i + 1 < len(parts):
                    pkg = parts[i + 1]
                    if not pkg.startswith("-"):
                        packages.append(pkg)
                    break

    if not packages:
        return True

    console.print(f"    Packages: {', '.join(packages)}")
    cmd = f"sudo apt-get -o DPkg::Lock::Timeout=120 install -y {' '.join(packages)}"
    success, _, _ = _run_command(cmd, console)

    if success:
        console.print("    [green]✓ apt packages installed[/green]")
    else:
        console.print("    [yellow]⚠ Some packages may have failed[/yellow]")

    return success


def _install_pipx_tool(console, tool: Dict) -> bool:
    """Install a tool using pipx."""
    name = tool["name"]
    cmd = tool["install"]

    console.print(f"    {name}...", end=" ")

    # For netexec and other complex builds, show message about output capture
    if "NetExec" in cmd or "netexec" in cmd.lower():
        console.print()
        console.print(
            "      [dim]Building (output captured, this may take a while)...[/dim]"
        )

    # pipx install commands - use subprocess directly to ensure full capture
    # Some tools (like netexec with Rust deps) can corrupt terminal with progress bars
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )
        success = result.returncode == 0
        stderr = result.stderr

        if success:
            console.print(
                "    [green]✓[/green]"
                if "NetExec" not in cmd
                else "      [green]✓[/green]"
            )
            return True
        else:
            # Check if already installed
            if "already exists" in stderr or "already installed" in stderr.lower():
                console.print(
                    "    [green]✓ (already installed)[/green]"
                    if "NetExec" not in cmd
                    else "      [green]✓ (already installed)[/green]"
                )
                return True
            console.print(
                "    [red]✗[/red]" if "NetExec" not in cmd else "      [red]✗[/red]"
            )
            if stderr:
                # Truncate and clean stderr for display
                clean_stderr = stderr.replace("\n", " ")[:80]
                console.print(f"      [dim]{clean_stderr}[/dim]")
            return False
    except subprocess.TimeoutExpired:
        console.print(
            "    [red]✗ timeout[/red]"
            if "NetExec" not in cmd
            else "      [red]✗ timeout[/red]"
        )
        return False
    except Exception as e:
        console.print(
            f"    [red]✗[/red] {str(e)[:50]}"
            if "NetExec" not in cmd
            else f"      [red]✗[/red] {str(e)[:50]}"
        )
        return False


def _install_go_tool(console, tool: Dict) -> bool:
    """Install a tool using go install."""
    name = tool["name"]
    cmd = tool["install"]

    console.print(f"    {name}...", end=" ")

    # Ensure GOPATH is set
    gopath = os.path.expanduser("~/go")
    env = os.environ.copy()
    env["GOPATH"] = gopath
    env["PATH"] = f"{gopath}/bin:" + env.get("PATH", "")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            env=env,
            timeout=300,  # 5 minute timeout for go installs
        )
        if result.returncode == 0:
            console.print("[green]✓[/green]")
            return True
        else:
            console.print("[red]✗[/red]")
            if result.stderr:
                console.print(f"      [dim]{result.stderr[:80]}[/dim]")
            return False
    except Exception as e:
        console.print(f"[red]✗[/red] {str(e)[:50]}")
        return False


def _install_gem_tool(console, tool: Dict) -> bool:
    """Install a tool using gem."""
    name = tool["name"]
    cmd = tool["install"]

    console.print(f"    {name}...", end=" ")

    success, _, stderr = _run_command(cmd, console, capture=True)

    if success:
        console.print("[green]✓[/green]")
        return True
    else:
        console.print(f"[red]✗[/red]")
        if stderr:
            console.print(f"      [dim]{stderr[:80]}[/dim]")
        return False


def _install_snap_tool(console, tool: Dict) -> bool:
    """Install a tool using snap."""
    name = tool["name"]
    cmd = tool["install"]

    console.print(f"    {name}...", end=" ")

    success, _, stderr = _run_command(cmd, console, capture=True)

    if success:
        console.print("[green]✓[/green]")
        return True
    else:
        console.print(f"[red]✗[/red]")
        if stderr:
            console.print(f"      [dim]{stderr[:80]}[/dim]")
        return False


def _install_git_tool(console, tool: Dict) -> bool:
    """Install a tool from git (requires sudo for /opt)."""
    import re

    name = tool["name"]
    cmd = tool["install"]

    console.print(f"    {name}...")

    # Parse the command to handle existing directories properly
    # Commands are typically: prereq && git clone <url> <dir> && pip install ... && ln -sf ...
    commands = [c.strip() for c in cmd.split("&&")]

    clone_cmd = None
    pre_clone_cmds = []
    post_clone_cmds = []
    target_dir = None

    for i, c in enumerate(commands):
        if "git clone" in c:
            clone_cmd = c
            pre_clone_cmds = commands[:i]  # Commands before git clone (e.g., cpan)
            post_clone_cmds = commands[i + 1 :]
            # Extract target directory from clone command
            # Pattern: git clone <url> <directory>
            match = re.search(r"git clone\s+\S+\s+(\S+)", c)
            if match:
                target_dir = match.group(1)
            break

    # If we found a git clone command and target directory
    if clone_cmd and target_dir:
        # Run pre-clone commands first (e.g., installing dependencies like cpan)
        for pre_cmd in pre_clone_cmds:
            pre_cmd = pre_cmd.strip()
            if not pre_cmd:
                continue
            console.print(f"      [dim]Running: {pre_cmd[:50]}...[/dim]")
            success, _, stderr = _run_command(pre_cmd, console, capture=True)
            if not success:
                console.print(f"[red]✗[/red]")
                if stderr:
                    console.print(f"      [dim]{stderr[:80]}[/dim]")
                return False
        dir_exists = Path(target_dir).exists()

        if dir_exists:
            console.print(
                f"      [dim]Directory {target_dir} exists, updating...[/dim]"
            )
            # Try to update with git pull
            pull_cmd = f"sudo git -C {target_dir} pull"
            success, _, stderr = _run_command(pull_cmd, console, capture=True)

            if not success and "not a git repository" in stderr.lower():
                # Directory exists but isn't a git repo - remove and re-clone
                console.print(f"      [dim]Not a git repo, re-cloning...[/dim]")
                rm_cmd = f"sudo rm -rf {target_dir}"
                _run_command(rm_cmd, console, capture=True)
                success, _, stderr = _run_command(clone_cmd, console, capture=True)
                if not success:
                    console.print(f"[red]✗[/red]")
                    if stderr:
                        console.print(f"      [dim]{stderr[:80]}[/dim]")
                    return False
            elif not success:
                # Pull failed for other reasons, try to continue anyway
                console.print(
                    f"      [yellow]⚠ git pull failed, continuing with existing files[/yellow]"
                )
        else:
            # Directory doesn't exist, run the clone
            success, _, stderr = _run_command(clone_cmd, console, capture=True)
            if not success:
                console.print(f"[red]✗[/red]")
                if stderr:
                    console.print(f"      [dim]{stderr[:80]}[/dim]")
                return False

        # Run post-clone commands (pip install, symlink, etc.)
        for post_cmd in post_clone_cmds:
            post_cmd = post_cmd.strip()
            if not post_cmd:
                continue
            success, _, stderr = _run_command(post_cmd, console, capture=True)
            if not success:
                console.print(f"[red]✗[/red]")
                if stderr:
                    console.print(f"      [dim]{stderr[:80]}[/dim]")
                return False

        console.print(f"    [green]✓[/green]")
        return True

    # Fallback: run the full command as-is (no git clone detected)
    success, _, stderr = _run_command(cmd, console, capture=True)

    if success:
        console.print("[green]✓[/green]")
        return True
    else:
        console.print(f"[red]✗[/red]")
        if stderr:
            console.print(f"      [dim]{stderr[:80]}[/dim]")
        return False


def _install_other_tool(console, tool: Dict) -> bool:
    """Install tools with custom installation methods (like metasploit)."""
    name = tool["name"]
    cmd = tool["install"]

    console.print(f"    {name}...", end=" ")

    # Special handling for metasploit installer (takes a while)
    if "msfinstall" in cmd:
        console.print()
        console.print(
            "      [yellow]Installing Metasploit (this may take several minutes)...[/yellow]"
        )
        console.print(
            "      [dim]Installing postgresql and downloading Metasploit installer...[/dim]"
        )
        console.print(
            "      [dim]Output is captured to prevent terminal corruption...[/dim]"
        )

        # Run the full install command with captured output to prevent terminal corruption
        # Metasploit installer outputs progress bars and escape sequences that can corrupt Rich console
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,  # Capture to prevent terminal corruption
                text=True,
                timeout=1800,  # 30 minute timeout for metasploit
            )
            if result.returncode == 0:
                console.print("      [green]✓ Metasploit installed[/green]")

                # Initialize MSF database (must run as normal user, not root)
                console.print("      [dim]Initializing MSF database...[/dim]")
                try:
                    # Use full path since /opt/metasploit-framework/bin isn't in PATH yet
                    msfdb_path = "/opt/metasploit-framework/bin/msfdb"
                    init_result = subprocess.run(
                        [msfdb_path, "init"],
                        capture_output=True,
                        timeout=300,  # 5 minute timeout
                    )
                    if init_result.returncode == 0:
                        console.print("      [green]✓ MSF database initialized[/green]")

                        # Copy database.yml to /root/.msf4/ so sudo msfconsole can connect
                        # msfdb init creates config in ~/.msf4/, but sudo looks in /root/.msf4/
                        import os
                        from pathlib import Path

                        user_msf4 = Path.home() / ".msf4"
                        user_db_yml = user_msf4 / "database.yml"
                        if user_db_yml.exists():
                            console.print(
                                "      [dim]Configuring sudo access to MSF database...[/dim]"
                            )
                            try:
                                # Create /root/.msf4/ directory and copy database.yml
                                copy_result = subprocess.run(
                                    ["sudo", "mkdir", "-p", "/root/.msf4"],
                                    capture_output=True,
                                )
                                copy_result = subprocess.run(
                                    [
                                        "sudo",
                                        "cp",
                                        str(user_db_yml),
                                        "/root/.msf4/database.yml",
                                    ],
                                    capture_output=True,
                                )
                                if copy_result.returncode == 0:
                                    console.print(
                                        "      [green]✓ Sudo MSF access configured[/green]"
                                    )
                                else:
                                    console.print(
                                        "      [yellow]⚠ Could not configure sudo access (run manually: sudo cp ~/.msf4/database.yml /root/.msf4/)[/yellow]"
                                    )
                            except Exception as e:
                                console.print(
                                    f"      [yellow]⚠ Could not configure sudo access: {str(e)[:30]}[/yellow]"
                                )
                    else:
                        console.print(
                            "      [yellow]⚠ MSF database init returned non-zero (may already be initialized)[/yellow]"
                        )
                except Exception as e:
                    console.print(
                        f"      [yellow]⚠ Could not init MSF database: {str(e)[:40]}[/yellow]"
                    )

                return True
            else:
                console.print("      [red]✗ Metasploit installation failed[/red]")
                return False
        except subprocess.TimeoutExpired:
            console.print("      [red]✗ Installation timed out[/red]")
            return False
        except Exception as e:
            console.print(f"      [red]✗ Error: {str(e)[:50]}[/red]")
            return False

    success, _, stderr = _run_command(cmd, console, capture=True)

    if success:
        console.print("[green]✓[/green]")
        return True
    else:
        console.print(f"[red]✗[/red]")
        if stderr:
            console.print(f"      [dim]{stderr[:80]}[/dim]")
        return False
