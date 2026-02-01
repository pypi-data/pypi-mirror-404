#!/usr/bin/env python3
"""
souleyez.ui.splunk_gap_analysis_view - Splunk Gap Analysis View

Displays comparison between Splunk (passive, synced from Wazuh) and
scan (active) vulnerability detection to identify gaps in coverage.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import click
from rich import box
from rich.console import Console
from rich.table import Table

from souleyez.storage.database import get_db
from souleyez.ui.design_system import DesignSystem

console = Console()

# Severity colors
SEVERITY_COLORS = {
    "Critical": "red",
    "High": "yellow",
    "Medium": "white",
    "Low": "bright_black",
    "critical": "red",
    "high": "yellow",
    "medium": "white",
    "low": "bright_black",
}

SEVERITY_ICONS = {
    "Critical": "[red bold]C[/red bold]",
    "High": "[yellow bold]H[/yellow bold]",
    "Medium": "[white]M[/white]",
    "Low": "[bright_black]L[/bright_black]",
}


@dataclass
class SplunkVulnGap:
    """Represents a vulnerability gap between detection sources."""

    cve_id: str
    severity: str
    host_ip: str
    source: str  # 'splunk', 'scan', 'both'
    splunk_details: Optional[Dict[str, Any]] = None
    scan_details: Optional[Dict[str, Any]] = None
    recommendation: str = ""
    confidence: str = "high"


@dataclass
class SplunkGapResult:
    """Result of Splunk gap analysis."""

    splunk_total: int = 0
    scan_total: int = 0
    splunk_only: List[SplunkVulnGap] = field(default_factory=list)
    scan_only: List[SplunkVulnGap] = field(default_factory=list)
    confirmed: List[SplunkVulnGap] = field(default_factory=list)
    coverage_pct: float = 0.0


def show_splunk_gap_analysis_view(
    engagement_id: int, engagement_name: str = ""
) -> None:
    """
    Display Splunk gap analysis view.

    Args:
        engagement_id: Current engagement ID
        engagement_name: Engagement name for display
    """
    from souleyez.integrations.wazuh.config import WazuhConfig

    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        # Header
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " SPLUNK GAP ANALYSIS ".center(width - 2), bold=True, fg="cyan"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()
        click.echo(
            click.style(
                "  Compare Splunk (passive/synced) vs Scan (active) findings",
                fg="bright_black",
            )
        )
        click.echo()

        # Check if Splunk is configured
        config = WazuhConfig.get_config(engagement_id)

        if (
            not config
            or config.get("siem_type") != "splunk"
            or not config.get("enabled")
        ):
            click.echo(
                click.style(
                    "  Splunk is not configured for this engagement.", fg="yellow"
                )
            )
            click.echo()
            click.echo("  Configure Splunk in Settings -> SIEM Integration")
            click.echo()
            click.echo("─" * width)
            click.echo()
            click.echo("  [q] Back")
            click.echo()
            try:
                if click.getchar().lower() == "q":
                    return
            except (KeyboardInterrupt, EOFError):
                return
            continue

        # Get Splunk client and run analysis
        try:
            from souleyez.integrations.siem.splunk import SplunkSIEMClient

            client = SplunkSIEMClient.from_config(
                {
                    "api_url": config.get("api_url", ""),
                    "username": config.get("username", ""),
                    "password": config.get("password", ""),
                    "verify_ssl": config.get("verify_ssl", False),
                    "default_index": config.get("default_index", "main"),
                }
            )

            # Run gap analysis
            result = _analyze_gaps(engagement_id, client)
            stats = _get_coverage_stats(result)

        except Exception as e:
            click.echo(click.style(f"  Error connecting to Splunk: {e}", fg="red"))
            click.echo()
            click.echo("  Make sure the wazuh_vulns index exists and has data.")
            click.echo("  Run: python3 scripts/wazuh_vuln_to_splunk.py --all")
            click.echo()
            click.pause("  Press any key to return...")
            return

        # Summary dashboard
        _render_summary_dashboard(result, stats, width)

        # Menu
        click.echo("─" * width)
        click.echo()
        click.echo("  [1] Splunk Only (scan missed)")
        click.echo("  [2] Scan Only (Splunk missed)")
        click.echo("  [3] Confirmed (both)")
        click.echo("  [a] Actionable Gaps")
        click.echo("  [r] Refresh")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = input("  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "1":
                _show_splunk_only(result, width)
            elif choice == "2":
                _show_scan_only(result, width)
            elif choice == "3":
                _show_confirmed(result, width)
            elif choice == "a":
                _show_actionable_gaps(result, width)
            elif choice == "r":
                continue  # Refresh
        except (KeyboardInterrupt, EOFError):
            return


def _analyze_gaps(engagement_id: int, client) -> SplunkGapResult:
    """Run gap analysis comparing Splunk vs scan findings.

    Matching strategy:
    1. CVE-based matching (primary) - same CVE found by both sources
    2. Host correlation is informational, not required for matching
    """
    result = SplunkGapResult()

    # Get Splunk vulnerabilities
    splunk_vulns = _get_splunk_cves(client)
    result.splunk_total = len(splunk_vulns)

    # Get scan findings with CVE IDs
    scan_findings = _get_scan_cves(engagement_id)
    result.scan_total = len(scan_findings)

    # Build CVE lookup sets (CVE-based matching, not host-dependent)
    # Group by CVE ID to find matches
    splunk_by_cve: Dict[str, List[Dict]] = {}
    for v in splunk_vulns:
        cve = v.get("cve_id")
        if cve:
            splunk_by_cve.setdefault(cve, []).append(v)

    scan_by_cve: Dict[str, List[Dict]] = {}
    for f in scan_findings:
        cve = f.get("cve_id")
        if cve:
            scan_by_cve.setdefault(cve, []).append(f)

    # Get all unique CVEs
    all_splunk_cves = set(splunk_by_cve.keys())
    all_scan_cves = set(scan_by_cve.keys())

    # Find confirmed (CVE exists in both sources)
    confirmed_cves = all_splunk_cves & all_scan_cves
    for cve_id in confirmed_cves:
        splunk_entries = splunk_by_cve[cve_id]
        scan_entries = scan_by_cve[cve_id]
        # Use first entry from each for details
        splunk_v = splunk_entries[0]
        scan_f = scan_entries[0]

        result.confirmed.append(
            SplunkVulnGap(
                cve_id=cve_id,
                severity=splunk_v.get("severity", "Medium"),
                host_ip=f"{splunk_v.get('host_ip', '-')} / {scan_f.get('host_ip', '-')}",
                source="both",
                splunk_details=splunk_v,
                scan_details=scan_f,
                recommendation=f"Confirmed by both sources ({len(splunk_entries)} Splunk, {len(scan_entries)} scan)",
                confidence="high",
            )
        )

    # Find Splunk-only CVEs (scan didn't find this CVE anywhere)
    splunk_only_cves = all_splunk_cves - all_scan_cves
    for cve_id in splunk_only_cves:
        splunk_entries = splunk_by_cve[cve_id]
        splunk_v = splunk_entries[0]

        result.splunk_only.append(
            SplunkVulnGap(
                cve_id=cve_id,
                severity=splunk_v.get("severity", "Medium"),
                host_ip=splunk_v.get("host_ip", "-"),
                source="splunk",
                splunk_details=splunk_v,
                recommendation="Package-level vulnerability - network scans typically can't detect",
                confidence="medium",
            )
        )

    # Find Scan-only CVEs (Splunk/Wazuh didn't detect this CVE)
    scan_only_cves = all_scan_cves - all_splunk_cves
    for cve_id in scan_only_cves:
        scan_entries = scan_by_cve[cve_id]
        scan_f = scan_entries[0]

        result.scan_only.append(
            SplunkVulnGap(
                cve_id=cve_id,
                severity=scan_f.get("severity", "Medium"),
                host_ip=scan_f.get("host_ip", "-"),
                source="scan",
                scan_details=scan_f,
                recommendation="Network-exposed CVE - Wazuh agent may not be installed on this host",
                confidence="medium",
            )
        )

    # Calculate coverage based on unique CVEs
    total_unique_cves = len(all_splunk_cves | all_scan_cves)
    if total_unique_cves > 0:
        result.coverage_pct = (len(confirmed_cves) / total_unique_cves) * 100

    return result


def _get_splunk_cves(client) -> List[Dict[str, Any]]:
    """Get vulnerability CVEs from Splunk."""
    try:
        vulns = client.get_vulnerabilities(limit=2000)

        # Transform to standard format with host_ip mapping
        result = []
        for v in vulns:
            # Map agent_name to host_ip if available
            host_ip = v.get("agent_ip") or v.get("agent_name", "-")
            # Normalize CVE ID to uppercase for matching
            cve_id = v.get("cve_id", "")
            if cve_id:
                cve_id = cve_id.upper()
            result.append(
                {
                    "cve_id": cve_id,
                    "severity": v.get("severity", "Medium"),
                    "host_ip": host_ip,
                    "package_name": v.get("package_name"),
                    "package_version": v.get("package_version"),
                    "cvss_score": v.get("cvss_score"),
                    "agent_name": v.get("agent_name"),
                    "os_name": v.get("os_name"),
                }
            )
        return result
    except Exception as e:
        click.echo(
            click.style(f"  Warning: Error fetching Splunk vulns: {e}", fg="yellow")
        )
        return []


def _get_scan_cves(engagement_id: int) -> List[Dict[str, Any]]:
    """Get CVE findings from active scans."""
    import re

    db = get_db()
    cve_pattern = re.compile(r"CVE-\d{4}-\d+", re.IGNORECASE)
    result = []

    # Get hosts for this engagement
    hosts = db.execute(
        "SELECT id, ip_address FROM hosts WHERE engagement_id = ?", (engagement_id,)
    )

    host_map = {h["id"]: h["ip_address"] for h in hosts}

    if not host_map:
        return []

    # 1. Get nuclei_findings with CVE IDs (they have cve_id column)
    nuclei_findings = db.execute(
        "SELECT * FROM nuclei_findings WHERE engagement_id = ? AND cve_id IS NOT NULL",
        (engagement_id,),
    )

    for f in nuclei_findings:
        cve_id = f.get("cve_id")
        if cve_id:
            # Extract host IP from matched_at if available
            matched_at = f.get("matched_at", "")
            host_ip = None
            # Try to extract IP from matched_at URL
            ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", matched_at)
            if ip_match:
                host_ip = ip_match.group(1)

            result.append(
                {
                    "cve_id": cve_id.upper(),
                    "host_ip": host_ip or "-",
                    "severity": (f.get("severity") or "Medium").title(),
                    "title": f.get("name"),
                    "tool": "nuclei",
                    "port": None,
                    "service": None,
                }
            )

    # 2. Get regular findings and extract CVEs from title/refs
    host_ids = list(host_map.keys())
    placeholders = ",".join("?" * len(host_ids))
    findings = db.execute(
        f"""
        SELECT f.*, h.ip_address
        FROM findings f
        JOIN hosts h ON f.host_id = h.id
        WHERE f.host_id IN ({placeholders})
        AND (f.title LIKE '%CVE-%' OR f.refs LIKE '%CVE-%')
    """,
        tuple(host_ids),
    )

    for f in findings:
        # Try to extract CVE from title
        title = f.get("title", "") or ""
        refs = f.get("refs", "") or ""
        combined = title + " " + refs

        matches = cve_pattern.findall(combined)
        for cve_id in matches:
            result.append(
                {
                    "cve_id": cve_id.upper(),
                    "host_ip": f.get("ip_address"),
                    "severity": (f.get("severity") or "Medium").title(),
                    "title": f.get("title"),
                    "tool": f.get("tool"),
                    "port": f.get("port"),
                    "service": None,
                }
            )

    return result


def _get_coverage_stats(result: SplunkGapResult) -> Dict[str, Any]:
    """Calculate coverage statistics."""
    stats = {
        "coverage_pct": result.coverage_pct,
        "by_severity": {"splunk_only": {}, "scan_only": {}, "confirmed": {}},
    }

    # Count by severity
    for gap in result.splunk_only:
        sev = gap.severity
        stats["by_severity"]["splunk_only"][sev] = (
            stats["by_severity"]["splunk_only"].get(sev, 0) + 1
        )

    for gap in result.scan_only:
        sev = gap.severity
        stats["by_severity"]["scan_only"][sev] = (
            stats["by_severity"]["scan_only"].get(sev, 0) + 1
        )

    for gap in result.confirmed:
        sev = gap.severity
        stats["by_severity"]["confirmed"][sev] = (
            stats["by_severity"]["confirmed"].get(sev, 0) + 1
        )

    return stats


def _render_summary_dashboard(result: SplunkGapResult, stats: Dict, width: int) -> None:
    """Render the summary dashboard."""
    splunk_total = result.splunk_total
    scan_total = result.scan_total
    confirmed = len(result.confirmed)
    splunk_only = len(result.splunk_only)
    scan_only = len(result.scan_only)
    coverage = stats.get("coverage_pct", 0)

    # Coverage color
    if coverage >= 80:
        coverage_color = "green"
    elif coverage >= 50:
        coverage_color = "yellow"
    else:
        coverage_color = "red"

    # Detection Sources
    click.echo(click.style("  DETECTION SOURCES", bold=True))
    click.echo(
        f"    Splunk (passive):  {click.style(str(splunk_total), fg='cyan', bold=True)} CVEs"
    )
    click.echo(
        f"    Scans (active):    {click.style(str(scan_total), fg='cyan', bold=True)} CVEs"
    )
    click.echo()

    # Analysis Results
    click.echo(click.style("  ANALYSIS RESULTS", bold=True))
    click.echo(
        f"    ✓ Confirmed (both):     {click.style(str(confirmed), fg='green', bold=True)}"
    )
    click.echo(
        f"    ⚠ Splunk Only:          {click.style(str(splunk_only), fg='yellow', bold=True)}  <- Scans missed these"
    )
    click.echo(
        f"    ◐ Scan Only:            {click.style(str(scan_only), fg='blue', bold=True)}  <- Splunk missed these"
    )
    click.echo()

    # Coverage
    click.echo(
        f"  Coverage: "
        + click.style(f"{coverage:.1f}%", fg=coverage_color, bold=True)
        + " of Splunk vulns confirmed by scans"
    )
    click.echo()

    # Add explanation note for low coverage
    if coverage < 20:
        click.echo(
            click.style("  NOTE: ", fg="cyan", bold=True)
            + click.style(
                "Low overlap is expected. Splunk/Wazuh detects ", fg="bright_black"
            )
            + click.style("package-level", fg="cyan")
            + click.style(" vulns", fg="bright_black")
        )
        click.echo(
            click.style(
                "        (installed software), while scans find ", fg="bright_black"
            )
            + click.style("network-exposed", fg="cyan")
            + click.style(" vulns (services).", fg="bright_black")
        )
        click.echo()

    # Severity breakdown
    sev_breakdown = stats.get("by_severity", {})
    if (
        sev_breakdown.get("splunk_only")
        or sev_breakdown.get("scan_only")
        or sev_breakdown.get("confirmed")
    ):
        _render_severity_breakdown(sev_breakdown, width)


def _render_severity_breakdown(breakdown: Dict, width: int) -> None:
    """Render severity breakdown."""
    table = Table(
        show_header=True,
        header_style="bold",
        box=box.SIMPLE,
        padding=(0, 2),
        expand=False,
    )

    table.add_column("Severity", width=14)
    table.add_column("Splunk Only", width=12, justify="right")
    table.add_column("Scan Only", width=12, justify="right")
    table.add_column("Confirmed", width=12, justify="right")

    for sev in ["Critical", "High", "Medium", "Low"]:
        color = SEVERITY_COLORS.get(sev, "white")
        splunk_only = breakdown.get("splunk_only", {}).get(sev, 0)
        scan_only = breakdown.get("scan_only", {}).get(sev, 0)
        confirmed = breakdown.get("confirmed", {}).get(sev, 0)

        table.add_row(
            f"[{color}]{sev}[/{color}]",
            str(splunk_only) if splunk_only else "-",
            str(scan_only) if scan_only else "-",
            str(confirmed) if confirmed else "-",
        )

    console.print("  ", table)
    click.echo()


def _show_splunk_only(result: SplunkGapResult, width: int) -> None:
    """Show vulnerabilities found only by Splunk with pagination."""
    page = 0
    page_size = 20
    view_all = False
    gaps = result.splunk_only

    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " SPLUNK ONLY - SCANS MISSED ".center(width - 2), bold=True, fg="yellow"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        click.echo(f"  {len(gaps)} CVEs detected by Splunk but NOT by active scans.")
        click.echo(
            click.style(
                "  These may be local/package vulnerabilities not exposed to network scanning.",
                fg="bright_black",
            )
        )
        click.echo()

        if not gaps:
            click.echo(
                click.style(
                    "  V No gaps - all Splunk vulns confirmed by scans!", fg="green"
                )
            )
            click.echo()
            click.pause("  Press any key to return...")
            return

        # Pagination
        total_pages = max(1, (len(gaps) + page_size - 1) // page_size)
        page = min(page, total_pages - 1)

        if view_all:
            page_gaps = gaps
        else:
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(gaps))
            page_gaps = gaps[start_idx:end_idx]

        _render_gaps_table(
            page_gaps,
            show_package=True,
            page=page,
            page_size=page_size,
            view_all=view_all,
        )

        # Pagination info
        if view_all:
            click.echo(f"\n  Showing all {len(gaps)} results")
        else:
            click.echo(f"\n  Page {page + 1}/{total_pages}")

        click.echo()
        click.echo("  💡 TIP: Press 'i' for interactive mode")
        if total_pages > 1 and not view_all:
            click.echo("  n/p: Next/Previous page")

        # Menu
        click.echo()
        click.echo("─" * width)
        click.echo()
        click.echo("  [#] View details")
        click.echo("  [i] Interactive mode")
        click.echo("  [t] Toggle pagination")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = input("  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "i":
                _interactive_gaps_mode(gaps, "SPLUNK ONLY GAPS", show_package=True)
            elif choice == "t":
                view_all = not view_all
                if not view_all:
                    page = 0
            elif choice == "n" and not view_all and page < total_pages - 1:
                page += 1
            elif choice == "p" and not view_all and page > 0:
                page -= 1
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(page_gaps):
                    _show_gap_detail(page_gaps[idx])
        except (KeyboardInterrupt, EOFError):
            return


def _show_scan_only(result: SplunkGapResult, width: int) -> None:
    """Show vulnerabilities found only by scans with pagination."""
    page = 0
    page_size = 20
    view_all = False
    gaps = result.scan_only

    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " SCAN ONLY - SPLUNK MISSED ".center(width - 2), bold=True, fg="blue"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        click.echo(f"  {len(gaps)} CVEs detected by active scans but NOT by Splunk.")
        click.echo(
            click.style(
                "  This may indicate: missing Wazuh agent, detection rule gap, or network-only vuln.",
                fg="bright_black",
            )
        )
        click.echo()

        if not gaps:
            click.echo(
                click.style(
                    "  V No gaps - Splunk detected all scan findings!", fg="green"
                )
            )
            click.echo()
            click.pause("  Press any key to return...")
            return

        # Pagination
        total_pages = max(1, (len(gaps) + page_size - 1) // page_size)
        page = min(page, total_pages - 1)

        if view_all:
            page_gaps = gaps
        else:
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(gaps))
            page_gaps = gaps[start_idx:end_idx]

        _render_gaps_table(
            page_gaps, show_tool=True, page=page, page_size=page_size, view_all=view_all
        )

        # Pagination info
        if view_all:
            click.echo(f"\n  Showing all {len(gaps)} results")
        else:
            click.echo(f"\n  Page {page + 1}/{total_pages}")

        click.echo()
        click.echo("  💡 TIP: Press 'i' for interactive mode")
        if total_pages > 1 and not view_all:
            click.echo("  n/p: Next/Previous page")

        # Menu
        click.echo()
        click.echo("─" * width)
        click.echo()
        click.echo("  [#] View details")
        click.echo("  [i] Interactive mode")
        click.echo("  [t] Toggle pagination")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = input("  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "i":
                _interactive_gaps_mode(gaps, "SCAN ONLY GAPS", show_tool=True)
            elif choice == "t":
                view_all = not view_all
                if not view_all:
                    page = 0
            elif choice == "n" and not view_all and page < total_pages - 1:
                page += 1
            elif choice == "p" and not view_all and page > 0:
                page -= 1
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(page_gaps):
                    _show_gap_detail(page_gaps[idx])
        except (KeyboardInterrupt, EOFError):
            return


def _show_confirmed(result: SplunkGapResult, width: int) -> None:
    """Show vulnerabilities confirmed by both sources with pagination."""
    page = 0
    page_size = 20
    view_all = False
    gaps = result.confirmed

    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " CONFIRMED - BOTH SOURCES ".center(width - 2), bold=True, fg="green"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        click.echo(f"  {len(gaps)} CVEs detected by BOTH Splunk and active scans.")
        click.echo(
            click.style(
                "  High confidence - prioritize these for exploitation.",
                fg="bright_black",
            )
        )
        click.echo()

        if not gaps:
            click.echo(
                click.style(
                    "  No confirmed matches between Splunk and scans.", fg="yellow"
                )
            )
            click.echo()
            click.pause("  Press any key to return...")
            return

        # Pagination
        total_pages = max(1, (len(gaps) + page_size - 1) // page_size)
        page = min(page, total_pages - 1)

        if view_all:
            page_gaps = gaps
        else:
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(gaps))
            page_gaps = gaps[start_idx:end_idx]

        _render_gaps_table(
            page_gaps, show_both=True, page=page, page_size=page_size, view_all=view_all
        )

        # Pagination info
        if view_all:
            click.echo(f"\n  Showing all {len(gaps)} results")
        else:
            click.echo(f"\n  Page {page + 1}/{total_pages}")

        click.echo()
        click.echo("  💡 TIP: Press 'i' for interactive mode")
        if total_pages > 1 and not view_all:
            click.echo("  n/p: Next/Previous page")

        # Menu
        click.echo()
        click.echo("─" * width)
        click.echo()
        click.echo("  [#] View details")
        click.echo("  [i] Interactive mode")
        click.echo("  [t] Toggle pagination")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = input("  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "i":
                _interactive_gaps_mode(gaps, "CONFIRMED GAPS", show_both=True)
            elif choice == "t":
                view_all = not view_all
                if not view_all:
                    page = 0
            elif choice == "n" and not view_all and page < total_pages - 1:
                page += 1
            elif choice == "p" and not view_all and page > 0:
                page -= 1
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(page_gaps):
                    _show_gap_detail(page_gaps[idx])
        except (KeyboardInterrupt, EOFError):
            return


def _show_actionable_gaps(result: SplunkGapResult, width: int) -> None:
    """Show actionable gaps with recommendations."""
    page = 0
    page_size = 20
    view_all = False

    # Get high-priority gaps (Critical/High severity from Splunk that scans missed)
    gaps = []
    for g in result.splunk_only:
        if g.severity in ("Critical", "High"):
            gaps.append(
                {
                    "cve_id": g.cve_id,
                    "severity": g.severity,
                    "host_ip": g.host_ip,
                    "package": (
                        g.splunk_details.get("package_name", "-")
                        if g.splunk_details
                        else "-"
                    ),
                    "package_version": (
                        g.splunk_details.get("package_version", "-")
                        if g.splunk_details
                        else "-"
                    ),
                    "recommendation": g.recommendation,
                    "priority": "high" if g.severity == "Critical" else "medium",
                }
            )

    # Sort by severity
    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    gaps.sort(key=lambda x: severity_order.get(x["severity"], 4))

    while True:
        DesignSystem.clear_screen()
        width = DesignSystem.get_terminal_width()

        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(" ACTIONABLE GAPS ".center(width - 2), bold=True, fg="yellow")
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        click.echo(
            f"  {len(gaps)} prioritized vulnerabilities from Splunk that need targeted scanning."
        )
        click.echo()

        if not gaps:
            click.echo(
                click.style("  V No actionable gaps - great scan coverage!", fg="green")
            )
            click.echo()
            click.pause("  Press any key to return...")
            return

        # Pagination
        total_pages = max(1, (len(gaps) + page_size - 1) // page_size)
        page = min(page, total_pages - 1)

        if view_all:
            page_gaps = gaps
        else:
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(gaps))
            page_gaps = gaps[start_idx:end_idx]

        # Render table
        table = DesignSystem.create_table()

        table.add_column("○", width=3, justify="center")
        table.add_column("#", width=3, style="dim")
        table.add_column("PRIORITY", width=8)
        table.add_column("CVE", width=18)
        table.add_column("SEVERITY", width=10)
        table.add_column("HOST", width=15)
        table.add_column("PACKAGE", width=20)
        table.add_column("RECOMMENDATION", width=35)

        for idx, gap in enumerate(page_gaps):
            if view_all:
                display_idx = idx + 1
            else:
                display_idx = (page * page_size) + idx + 1

            priority = gap.get("priority", "medium")
            priority_display = (
                "[red]HIGH[/red]" if priority == "high" else "[yellow]MEDIUM[/yellow]"
            )

            severity = gap.get("severity", "Medium")
            sev_color = SEVERITY_COLORS.get(severity, "white")

            table.add_row(
                "○",
                str(display_idx),
                priority_display,
                gap.get("cve_id", "-"),
                f"[{sev_color}]{severity}[/{sev_color}]",
                gap.get("host_ip", "-"),
                gap.get("package", "-")[:19],
                gap.get("recommendation", "-")[:34],
            )

        console.print(table)

        # Pagination info
        if view_all:
            click.echo(f"\n  Showing all {len(gaps)} results")
        else:
            click.echo(f"\n  Page {page + 1}/{total_pages}")

        click.echo()
        click.echo("  💡 TIP: Press 'i' for interactive mode")
        if total_pages > 1 and not view_all:
            click.echo("  n/p: Next/Previous page")

        # Menu
        click.echo()
        click.echo("─" * width)
        click.echo()
        click.echo("  [#] View details")
        click.echo("  [i] Interactive mode")
        click.echo("  [t] Toggle pagination")
        click.echo("  [q] Back")
        click.echo()

        try:
            choice = input("  Select option: ").strip().lower()

            if choice == "q":
                return
            elif choice == "i":
                _interactive_actionable_gaps_mode(gaps)
            elif choice == "t":
                view_all = not view_all
                if not view_all:
                    page = 0
            elif choice == "n" and not view_all and page < total_pages - 1:
                page += 1
            elif choice == "p" and not view_all and page > 0:
                page -= 1
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(page_gaps):
                    _show_actionable_gap_detail(page_gaps[idx])
        except (KeyboardInterrupt, EOFError):
            return


def _render_gaps_table(
    gaps: List,
    show_package: bool = False,
    show_tool: bool = False,
    show_both: bool = False,
    page: int = 0,
    page_size: int = 20,
    view_all: bool = False,
) -> None:
    """Render gaps table with pagination support."""
    table = DesignSystem.create_table()

    table.add_column("○", width=3, justify="center")
    table.add_column("#", width=3, style="dim")
    table.add_column("CVE", width=18)
    table.add_column("SEVERITY", width=10)
    table.add_column("HOST", width=15)

    if show_package:
        table.add_column("PACKAGE", width=25)
        table.add_column("RECOMMENDATION", width=35)
    elif show_tool:
        table.add_column("TOOL", width=15)
        table.add_column("RECOMMENDATION", width=40)
    elif show_both:
        table.add_column("PACKAGE", width=20)
        table.add_column("SCAN TOOL", width=15)
        table.add_column("CONFIDENCE", width=10)

    for idx, gap in enumerate(gaps):
        if view_all:
            display_idx = idx + 1
        else:
            display_idx = (page * page_size) + idx + 1

        severity = gap.severity
        sev_color = SEVERITY_COLORS.get(severity, "white")

        row = [
            "○",
            str(display_idx),
            gap.cve_id,
            f"[{sev_color}]{severity}[/{sev_color}]",
            gap.host_ip or "-",
        ]

        if show_package:
            package = (
                gap.splunk_details.get("package_name", "-")
                if gap.splunk_details
                else "-"
            )
            row.append(package[:24])
            row.append(gap.recommendation[:34])
        elif show_tool:
            tool = gap.scan_details.get("tool", "-") if gap.scan_details else "-"
            row.append(tool)
            row.append(gap.recommendation[:39])
        elif show_both:
            package = (
                gap.splunk_details.get("package_name", "-")
                if gap.splunk_details
                else "-"
            )
            tool = gap.scan_details.get("tool", "-") if gap.scan_details else "-"
            row.append(package[:19])
            row.append(tool)
            row.append(f"[green]{gap.confidence}[/green]")

        table.add_row(*row)

    console.print(table)


def _show_gap_detail(gap: SplunkVulnGap) -> None:
    """Show detailed info for a gap item."""
    DesignSystem.clear_screen()
    width = DesignSystem.get_terminal_width()

    cve = gap.cve_id or "Unknown"
    severity = gap.severity or "Medium"
    sev_color = SEVERITY_COLORS.get(severity, "white")

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│" + click.style(f" {cve} ".center(width - 2), bold=True, fg="cyan") + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    click.echo(f"  Severity: " + click.style(severity, fg=sev_color, bold=True))
    click.echo(f"  Host: {gap.host_ip or '-'}")
    click.echo(f"  Source: {gap.source or '-'}")
    click.echo(f"  Confidence: {gap.confidence or '-'}")
    click.echo()

    if gap.splunk_details:
        click.echo(click.style("  Splunk Details:", bold=True))
        click.echo(f"    Package: {gap.splunk_details.get('package_name', '-')}")
        click.echo(f"    Version: {gap.splunk_details.get('package_version', '-')}")
        click.echo(f"    CVSS: {gap.splunk_details.get('cvss_score', '-')}")
        click.echo(f"    Agent: {gap.splunk_details.get('agent_name', '-')}")
        click.echo(f"    OS: {gap.splunk_details.get('os_name', '-')}")
        click.echo()

    if gap.scan_details:
        click.echo(click.style("  Scan Details:", bold=True))
        click.echo(f"    Tool: {gap.scan_details.get('tool', '-')}")
        click.echo(f"    Port: {gap.scan_details.get('port', '-')}")
        click.echo(f"    Service: {gap.scan_details.get('service', '-')}")
        click.echo()

    if gap.recommendation:
        click.echo(click.style("  Recommendation:", bold=True))
        click.echo(f"    {gap.recommendation}")
        click.echo()

    click.pause("  Press any key to return...")


def _show_actionable_gap_detail(gap: Dict) -> None:
    """Show detailed info for an actionable gap."""
    DesignSystem.clear_screen()
    width = DesignSystem.get_terminal_width()

    cve = gap.get("cve_id", "Unknown")
    severity = gap.get("severity", "Medium")
    sev_color = SEVERITY_COLORS.get(severity, "white")

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│" + click.style(f" {cve} ".center(width - 2), bold=True, fg="cyan") + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    priority = gap.get("priority", "medium")
    priority_color = "red" if priority == "high" else "yellow"

    click.echo(f"  Severity: " + click.style(severity, fg=sev_color, bold=True))
    click.echo(
        f"  Priority: " + click.style(priority.upper(), fg=priority_color, bold=True)
    )
    click.echo(f"  Host: {gap.get('host_ip', '-')}")
    click.echo()

    click.echo(click.style("  Package:", bold=True))
    click.echo(f"    Name: {gap.get('package', '-')}")
    click.echo(f"    Version: {gap.get('package_version', '-')}")
    click.echo()

    if gap.get("recommendation"):
        click.echo(click.style("  Recommendation:", bold=True))
        click.echo(f"    {gap.get('recommendation')}")
        click.echo()

    click.pause("  Press any key to return...")


def _interactive_gaps_mode(
    gaps: List,
    title: str,
    show_package: bool = False,
    show_tool: bool = False,
    show_both: bool = False,
) -> None:
    """Interactive selection mode for gaps."""
    from souleyez.ui.interactive_selector import interactive_select

    if not gaps:
        click.echo(click.style("  No gaps to select.", fg="yellow"))
        click.pause()
        return

    # Prepare items for interactive selector
    gap_items = []
    for gap in gaps:
        item = {
            "id": id(gap),
            "cve_id": gap.cve_id or "-",
            "severity": gap.severity or "Medium",
            "host": gap.host_ip or "-",
            "raw": gap,
        }
        if show_package:
            item["package"] = (
                gap.splunk_details.get("package_name", "-")[:20]
                if gap.splunk_details
                else "-"
            )
        elif show_tool:
            item["tool"] = (
                gap.scan_details.get("tool", "-") if gap.scan_details else "-"
            )
        elif show_both:
            item["package"] = (
                gap.splunk_details.get("package_name", "-")[:15]
                if gap.splunk_details
                else "-"
            )
            item["tool"] = (
                gap.scan_details.get("tool", "-") if gap.scan_details else "-"
            )
        gap_items.append(item)

    columns = [
        {"name": "CVE", "key": "cve_id", "width": 18},
        {"name": "Severity", "key": "severity", "width": 10},
        {"name": "Host", "key": "host", "width": 15},
    ]

    if show_package:
        columns.append({"name": "Package", "key": "package", "width": 20})
    elif show_tool:
        columns.append({"name": "Tool", "key": "tool", "width": 15})
    elif show_both:
        columns.append({"name": "Package", "key": "package", "width": 15})
        columns.append({"name": "Tool", "key": "tool", "width": 15})

    def format_cell(item: Dict, key: str) -> str:
        if key == "severity":
            sev = item.get("severity", "Medium")
            color = SEVERITY_COLORS.get(sev, "white")
            return f"[{color}]{sev}[/{color}]"
        return str(item.get(key, "-"))

    selected_ids: set = set()
    interactive_select(
        items=gap_items,
        columns=columns,
        selected_ids=selected_ids,
        get_id=lambda g: g["id"],
        title=title,
        format_cell=format_cell,
    )

    # Show details of first selected
    if selected_ids:
        for item in gap_items:
            if item["id"] in selected_ids:
                _show_gap_detail(item["raw"])
                break


def _interactive_actionable_gaps_mode(gaps: List[Dict]) -> None:
    """Interactive selection mode for actionable gaps."""
    from souleyez.ui.interactive_selector import interactive_select

    if not gaps:
        click.echo(click.style("  No gaps to select.", fg="yellow"))
        click.pause()
        return

    # Prepare items for interactive selector
    gap_items = []
    for gap in gaps:
        gap_items.append(
            {
                "id": id(gap),
                "cve_id": gap.get("cve_id", "-"),
                "severity": gap.get("severity", "Medium"),
                "priority": gap.get("priority", "medium").upper(),
                "host": gap.get("host_ip", "-"),
                "package": gap.get("package", "-")[:20],
                "raw": gap,
            }
        )

    columns = [
        {"name": "Priority", "key": "priority", "width": 8},
        {"name": "CVE", "key": "cve_id", "width": 18},
        {"name": "Severity", "key": "severity", "width": 10},
        {"name": "Host", "key": "host", "width": 15},
        {"name": "Package", "key": "package", "width": 20},
    ]

    def format_cell(item: Dict, key: str) -> str:
        if key == "severity":
            sev = item.get("severity", "Medium")
            color = SEVERITY_COLORS.get(sev, "white")
            return f"[{color}]{sev}[/{color}]"
        elif key == "priority":
            pri = item.get("priority", "MEDIUM")
            color = "red" if pri == "HIGH" else "yellow"
            return f"[{color}]{pri}[/{color}]"
        return str(item.get(key, "-"))

    selected_ids: set = set()
    interactive_select(
        items=gap_items,
        columns=columns,
        selected_ids=selected_ids,
        get_id=lambda g: g["id"],
        title="ACTIONABLE GAPS",
        format_cell=format_cell,
    )

    # Show details of first selected
    if selected_ids:
        for item in gap_items:
            if item["id"] in selected_ids:
                _show_actionable_gap_detail(item["raw"])
                break
