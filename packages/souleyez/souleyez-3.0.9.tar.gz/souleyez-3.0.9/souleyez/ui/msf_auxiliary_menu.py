#!/usr/bin/env python3
"""
souleyez.ui.msf_auxiliary_menu - Enhanced MSF Auxiliary preset selector

Features:
- Service-aware filtering (only show relevant modules for target's services)
- Status indicators (ran, running, not run)
- Smart recommendations based on findings
- Batch execution mode
- Quick actions (auto-enum, search)
"""

from typing import Any, Dict, List, Optional, Set, Tuple

import click

from souleyez.ui.design_system import DesignSystem


def get_terminal_width() -> int:
    """Get terminal width, defaulting to 120 if not available."""
    import shutil

    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 120


def get_target_services(
    target_ip: str, engagement_id: int
) -> Tuple[List[Dict], Set[str], Set[int]]:
    """
    Get services running on target host.

    Returns:
        Tuple of (services_list, service_names_set, ports_set)
    """
    from souleyez.storage.hosts import HostManager

    hm = HostManager()
    host = hm.get_host_by_ip(engagement_id, target_ip)

    if not host:
        return [], set(), set()

    services = hm.get_host_services(host["id"])

    service_names = set()
    ports = set()

    for svc in services:
        svc_name = (svc.get("service_name") or "").lower()
        port = svc.get("port")

        if svc_name:
            service_names.add(svc_name)
        if port:
            ports.add(port)

    return services, service_names, ports


def get_msf_job_status(target_ip: str, engagement_id: int) -> Dict[str, Dict]:
    """
    Get status of MSF auxiliary jobs run against this target.

    Returns:
        Dict mapping module_path to {status, job_id, completed_at}
    """
    from souleyez.engine.background import get_all_jobs

    all_jobs = get_all_jobs()

    # Filter to MSF jobs for this target and engagement
    msf_jobs = [
        j
        for j in all_jobs
        if j.get("tool") == "msf_auxiliary"
        and j.get("engagement_id") == engagement_id
        and target_ip in (j.get("target") or "")
    ]

    status_map = {}

    for job in msf_jobs:
        args = job.get("args", [])
        if args:
            module_path = args[0]
            current_status = status_map.get(module_path, {})
            job_status = job.get("status", "unknown")

            # Keep most recent / highest priority status
            if job_status == "running":
                status_map[module_path] = {
                    "status": "running",
                    "job_id": job.get("id"),
                    "started_at": job.get("queued_at"),
                }
            elif job_status == "done" and current_status.get("status") != "running":
                status_map[module_path] = {
                    "status": "done",
                    "job_id": job.get("id"),
                    "completed_at": job.get("completed_at"),
                }
            elif job_status in ("pending", "queued") and current_status.get(
                "status"
            ) not in ("running", "done"):
                status_map[module_path] = {"status": "pending", "job_id": job.get("id")}

    return status_map


def get_recommendations(
    target_ip: str, engagement_id: int, services: List[Dict]
) -> List[Dict]:
    """
    Generate smart recommendations based on discovered services and findings.

    Returns:
        List of recommended presets with priority and reason
    """
    from souleyez.storage.findings import FindingsManager

    recommendations = []
    fm = FindingsManager()

    # Get service names and ports
    service_names = set()
    ports = set()
    for svc in services:
        svc_name = (svc.get("service_name") or "").lower()
        if svc_name:
            service_names.add(svc_name)
        port = svc.get("port")
        if port:
            ports.add(port)

    # Check for SMBv1 or SMB - recommend MS17-010 check
    if "smb" in service_names or "microsoft-ds" in service_names or 445 in ports:
        recommendations.append(
            {
                "module": "auxiliary/scanner/smb/smb_ms17_010",
                "name": "MS17-010 Check",
                "reason": "SMB detected - check for EternalBlue",
                "priority": "high",
            }
        )

    # Check for anonymous FTP
    if "ftp" in service_names or 21 in ports:
        recommendations.append(
            {
                "module": "auxiliary/scanner/ftp/anonymous",
                "name": "FTP Anonymous Check",
                "reason": "FTP detected - check anonymous access",
                "priority": "high",
            }
        )

    # Check for VNC without auth
    if "vnc" in service_names or 5900 in ports or 5901 in ports:
        recommendations.append(
            {
                "module": "auxiliary/scanner/vnc/vnc_none_auth",
                "name": "VNC None Auth",
                "reason": "VNC detected - check for no-auth",
                "priority": "high",
            }
        )

    # Check for RDP NLA
    if "rdp" in service_names or "ms-wbt-server" in service_names or 3389 in ports:
        recommendations.append(
            {
                "module": "auxiliary/scanner/rdp/rdp_scanner",
                "name": "RDP Scanner",
                "reason": "RDP detected - check NLA settings",
                "priority": "medium",
            }
        )

    # HTTP services - recommend directory scan
    if any(s in service_names for s in ["http", "https"]) or any(
        p in ports for p in [80, 443, 8080]
    ):
        recommendations.append(
            {
                "module": "auxiliary/scanner/http/dir_scanner",
                "name": "HTTP Dir Scanner",
                "reason": "Web server detected - discover directories",
                "priority": "medium",
            }
        )

    return recommendations


def filter_presets_by_services(
    preset_categories: Dict[str, List[Dict]], service_names: Set[str], ports: Set[int]
) -> Tuple[Dict[str, List[Dict]], int]:
    """
    Filter presets to only show those relevant to target's services.

    Returns:
        Tuple of (filtered_categories, hidden_count)
    """
    if not service_names and not ports:
        # No service info - show all
        return preset_categories, 0

    filtered = {}
    hidden_count = 0

    for category, presets in preset_categories.items():
        relevant_presets = []
        for preset in presets:
            preset_services = set(s.lower() for s in preset.get("services", []))
            preset_ports = set(preset.get("ports", []))

            # Check if any of target's services/ports match
            service_match = bool(preset_services & service_names)
            port_match = bool(preset_ports & ports)

            if service_match or port_match:
                relevant_presets.append(preset)
            else:
                hidden_count += 1

        if relevant_presets:
            filtered[category] = relevant_presets

    return filtered, hidden_count


def render_msf_auxiliary_menu(
    target: str,
    preset_categories: Dict[str, List[Dict]],
    engagement_id: int,
    show_all: bool = False,
) -> Optional[Dict]:
    """
    Render enhanced MSF Auxiliary preset menu.

    Args:
        target: Target IP/hostname
        preset_categories: Dict of category -> list of presets
        engagement_id: Current engagement ID
        show_all: If True, show all presets regardless of services

    Returns:
        Selected preset dict or None if cancelled
    """
    from rich.console import Console
    from rich.table import Table

    console = Console()
    width = get_terminal_width()

    # Get target services
    services, service_names, ports = get_target_services(target, engagement_id)

    # Get job status for this target
    job_status_map = get_msf_job_status(target, engagement_id)

    # Get recommendations
    recommendations = get_recommendations(target, engagement_id, services)

    # Filter presets if we have service info and not showing all
    if show_all or not (service_names or ports):
        filtered_categories = preset_categories
        hidden_count = 0
    else:
        filtered_categories, hidden_count = filter_presets_by_services(
            preset_categories, service_names, ports
        )

    while True:
        DesignSystem.clear_screen()

        # Header
        click.echo()
        click.echo(click.style("=" * width, fg="cyan"))
        click.echo(
            click.style(
                "  MSF Auxiliary (Metasploit)".center(width), fg="cyan", bold=True
            )
        )
        click.echo(click.style("=" * width, fg="cyan"))
        click.echo()

        # Target info with detected services
        click.echo(click.style(f"  Target: {target}", fg="green", bold=True))
        if services:
            svc_summary = ", ".join(sorted(service_names)[:8])
            if len(service_names) > 8:
                svc_summary += f" (+{len(service_names) - 8} more)"
            click.echo(click.style(f"  Services: {svc_summary}", fg="cyan"))
            click.echo(
                click.style(
                    f"  Ports: {', '.join(str(p) for p in sorted(ports)[:12])}",
                    fg="cyan",
                )
            )
        else:
            click.echo(
                click.style("  Services: No service data (run nmap first)", fg="yellow")
            )
        click.echo()

        # Quick actions
        click.echo(click.style("  QUICK ACTIONS", bold=True, fg="yellow"))
        click.echo("    [e] Run ALL enumeration modules for detected services")
        click.echo("    [v] Run ALL vulnerability scans for detected services")
        click.echo("    [/] Search modules by keyword")
        if hidden_count > 0:
            click.echo(f"    [*] Show ALL modules ({hidden_count} hidden)")
        click.echo()

        # Recommendations (if any)
        if recommendations and not show_all:
            click.echo(click.style("  RECOMMENDED", bold=True, fg="red"))
            for i, rec in enumerate(recommendations[:3], 1):
                priority_color = "red" if rec["priority"] == "high" else "yellow"
                status = job_status_map.get(rec["module"], {})
                status_icon = _get_status_icon(status.get("status"))
                click.echo(f"    [r{i}] {status_icon} {rec['name']} - {rec['reason']}")
            click.echo()

        # Filtered presets by category
        preset_num = 1
        preset_map = {}  # num -> preset

        for category_name, category_presets in filtered_categories.items():
            display_name = category_name.replace("_", " ").title()
            click.echo(click.style(f"  {display_name}:", bold=True, fg="cyan"))

            for preset in category_presets:
                # Get job status for this module
                module_path = preset["args"][0] if preset.get("args") else ""
                status = job_status_map.get(module_path, {})
                status_icon = _get_status_icon(status.get("status"))
                status_info = _get_status_info(status)

                # Format name with status
                name = preset["name"]
                desc = preset["desc"]

                if status_info:
                    click.echo(
                        f"    {preset_num:2d}. {status_icon} {name:<24} - {desc} {status_info}"
                    )
                else:
                    click.echo(
                        f"    {preset_num:2d}. {status_icon} {name:<24} - {desc}"
                    )

                preset_map[preset_num] = preset
                preset_num += 1

            click.echo()

        # Custom and back options
        click.echo(f"    {preset_num}. Custom module args")
        click.echo("     q. Back")
        click.echo()

        # Hidden modules notice
        if hidden_count > 0 and not show_all:
            click.echo(
                click.style(
                    f"    ({hidden_count} modules hidden - no matching services)",
                    fg="yellow",
                    dim=True,
                )
            )
            click.echo()

        try:
            choice = (
                click.prompt(
                    click.style("  Select option", fg="green", bold=True),
                    type=str,
                    default="1",
                    show_default=False,
                )
                .strip()
                .lower()
            )

            # Handle special commands
            if choice == "q":
                return None

            elif choice == "e":
                # Batch enumeration
                return _batch_select(
                    filtered_categories.get("enumeration", []), "enumeration"
                )

            elif choice == "v":
                # Batch vulnerability scan
                return _batch_select(
                    filtered_categories.get("vulnerability_scanning", []),
                    "vulnerability",
                )

            elif choice == "/":
                # Search
                search_term = (
                    click.prompt("  Search", type=str, default="").strip().lower()
                )
                if search_term:
                    return _search_presets(preset_categories, search_term)
                continue

            elif choice == "*":
                # Show all - recursive call with show_all=True
                return render_msf_auxiliary_menu(
                    target, preset_categories, engagement_id, show_all=True
                )

            elif choice.startswith("r") and len(choice) == 2:
                # Recommendation selection
                try:
                    rec_num = int(choice[1])
                    if 1 <= rec_num <= len(recommendations):
                        rec = recommendations[rec_num - 1]
                        # Find matching preset
                        for presets in preset_categories.values():
                            for preset in presets:
                                if preset.get("args", [""])[0] == rec["module"]:
                                    return preset
                except ValueError:
                    pass

            else:
                # Numeric selection
                try:
                    num = int(choice)
                    if num in preset_map:
                        return preset_map[num]
                    elif num == preset_num:
                        # Custom args
                        return {"custom": True}
                except ValueError:
                    click.echo(click.style("  Invalid selection", fg="red"))
                    click.pause()

        except (KeyboardInterrupt, click.Abort):
            return None


def _get_status_icon(status: Optional[str]) -> str:
    """Get status icon for a module."""
    if status == "done":
        return click.style("", fg="green")
    elif status == "running":
        return click.style("", fg="yellow")
    elif status == "pending":
        return click.style("", fg="blue")
    else:
        return click.style("", fg="white", dim=True)


def _get_status_info(status: Dict) -> str:
    """Get status info string."""
    if not status:
        return ""

    s = status.get("status")
    if s == "done":
        return click.style(f"(Job #{status.get('job_id')})", fg="green", dim=True)
    elif s == "running":
        return click.style(f"(Running #{status.get('job_id')})", fg="yellow")
    elif s == "pending":
        return click.style(f"(Queued #{status.get('job_id')})", fg="blue", dim=True)
    return ""


def _batch_select(presets: List[Dict], batch_type: str) -> Optional[Dict]:
    """Handle batch selection of multiple presets."""
    if not presets:
        click.echo(
            click.style(
                f"  No {batch_type} modules available for this target", fg="yellow"
            )
        )
        click.pause()
        return None

    return {"batch": True, "batch_type": batch_type, "presets": presets}


def _search_presets(preset_categories: Dict, search_term: str) -> Optional[Dict]:
    """Search presets by keyword."""
    matches = []

    for category, presets in preset_categories.items():
        for preset in presets:
            name = preset.get("name", "").lower()
            desc = preset.get("desc", "").lower()
            module = preset.get("args", [""])[0].lower()

            if search_term in name or search_term in desc or search_term in module:
                matches.append(preset)

    if not matches:
        click.echo(click.style(f"  No modules matching '{search_term}'", fg="yellow"))
        click.pause()
        return None

    if len(matches) == 1:
        return matches[0]

    # Show matches
    click.echo()
    click.echo(click.style(f"  Found {len(matches)} matching modules:", fg="cyan"))
    for i, preset in enumerate(matches, 1):
        click.echo(f"    {i}. {preset['name']} - {preset['desc']}")
    click.echo()

    try:
        choice = click.prompt(
            "  Select option", type=int, default=1, show_default=False
        )
        if 1 <= choice <= len(matches):
            return matches[choice - 1]
    except (ValueError, KeyboardInterrupt, click.Abort):
        pass

    return None
