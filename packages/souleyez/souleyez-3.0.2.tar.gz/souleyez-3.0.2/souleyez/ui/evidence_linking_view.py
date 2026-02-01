"""Evidence linking interface for deliverables."""

import click

from souleyez.storage.deliverable_evidence import EvidenceManager
from souleyez.storage.deliverables import DeliverableManager
from souleyez.ui.design_system import DesignSystem


def show_evidence_linking_view(deliverable_id: int):
    """
    Show evidence linking interface for a deliverable.

    Options:
    - View linked evidence
    - Add evidence (manual selection)
    - AI suggest evidence
    - Remove evidence links
    """
    em = EvidenceManager()
    dm = DeliverableManager()

    deliverable = dm.get_deliverable(deliverable_id)
    if not deliverable:
        click.echo(click.style("  Error: Deliverable not found", fg="red"))
        click.pause()
        return

    while True:
        DesignSystem.clear_screen()

        width = DesignSystem.get_terminal_width()

        # Header
        click.echo("\n┌" + "─" * (width - 2) + "┐")
        click.echo(
            "│"
            + click.style(
                " 🔗 EVIDENCE LINKING ".center(width - 2), bold=True, fg="cyan"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        # Deliverable info
        click.echo(
            f"  Deliverable: {click.style(deliverable['title'], bold=True, fg='cyan')}"
        )
        if deliverable.get("description"):
            click.echo(f"  Description: {deliverable['description'][:80]}...")
        click.echo()

        # Get linked evidence
        evidence = em.get_evidence(deliverable_id)
        evidence_count = em.get_evidence_count(deliverable_id)

        # Display linked evidence summary
        click.echo(
            click.style(
                f"  📋 LINKED EVIDENCE ({evidence_count} items)", bold=True, fg="cyan"
            )
        )
        click.echo("  " + "─" * (width - 4))
        click.echo()

        if evidence_count == 0:
            click.echo(click.style("  No evidence linked yet", fg="yellow"))
            click.echo()
        else:
            # Show findings
            if evidence["findings"]:
                click.echo(
                    click.style(
                        f"  🔍 Findings ({len(evidence['findings'])})", bold=True
                    )
                )
                for f in evidence["findings"][:3]:
                    severity_color = {
                        "critical": "red",
                        "high": "yellow",
                        "medium": "white",
                        "low": "bright_black",
                    }.get(f.get("severity", "medium"), "white")
                    click.echo(
                        f"     • [{click.style(f.get('severity', 'N/A').upper(), fg=severity_color)}] {f.get('title', 'Unknown')[:60]}"
                    )
                if len(evidence["findings"]) > 3:
                    click.echo(
                        click.style(
                            f"     ... and {len(evidence['findings']) - 3} more",
                            fg="bright_black",
                        )
                    )
                click.echo()

            # Show credentials
            if evidence["credentials"]:
                click.echo(
                    click.style(
                        f"  🔑 Credentials ({len(evidence['credentials'])})", bold=True
                    )
                )
                for c in evidence["credentials"][:3]:
                    click.echo(
                        f"     • {c.get('username', 'N/A')}@{c.get('host', 'N/A')}"
                    )
                if len(evidence["credentials"]) > 3:
                    click.echo(
                        click.style(
                            f"     ... and {len(evidence['credentials']) - 3} more",
                            fg="bright_black",
                        )
                    )
                click.echo()

            # Show screenshots
            if evidence["screenshots"]:
                click.echo(
                    click.style(
                        f"  📸 Screenshots ({len(evidence['screenshots'])})", bold=True
                    )
                )
                for s in evidence["screenshots"][:3]:
                    click.echo(
                        f"     • {s.get('description', s.get('filename', 'Unknown'))[:60]}"
                    )
                if len(evidence["screenshots"]) > 3:
                    click.echo(
                        click.style(
                            f"     ... and {len(evidence['screenshots']) - 3} more",
                            fg="bright_black",
                        )
                    )
                click.echo()

            # Show jobs
            if evidence["jobs"]:
                click.echo(
                    click.style(f"  ⚡ Jobs ({len(evidence['jobs'])})", bold=True)
                )
                for j in evidence["jobs"][:3]:
                    click.echo(
                        f"     • #{j.get('id')} - {j.get('tool', 'N/A')} @ {j.get('target', 'N/A')}"
                    )
                if len(evidence["jobs"]) > 3:
                    click.echo(
                        click.style(
                            f"     ... and {len(evidence['jobs']) - 3} more",
                            fg="bright_black",
                        )
                    )
                click.echo()

        # Menu
        click.echo(click.style("  ⚙️  ACTIONS", bold=True, fg="cyan"))
        click.echo("  " + "─" * (width - 4))
        click.echo()
        click.echo("  [A] Add Evidence (manual selection)")
        click.echo("  [S] Smart Suggest (AI-powered)")
        click.echo("  [V] View All Evidence (detailed)")
        click.echo("  [R] Remove Evidence")
        click.echo()
        click.echo("  [q] ← Back")
        click.echo()

        choice = (
            click.prompt("Select option", type=str, default="q", show_default=False)
            .strip()
            .lower()
        )

        if choice == "q":
            break
        elif choice == "a":
            _add_evidence_manual(deliverable_id, deliverable["engagement_id"])
        elif choice == "s":
            _show_smart_suggestions(deliverable_id, deliverable["engagement_id"])
        elif choice == "v":
            _view_evidence_detailed(deliverable_id)
        elif choice == "r":
            _remove_evidence(deliverable_id)


def _add_evidence_manual(deliverable_id: int, engagement_id: int):
    """Manually select and link evidence."""
    from souleyez.storage.credentials import CredentialsManager
    from souleyez.storage.findings import FindingsManager

    em = EvidenceManager()
    fm = FindingsManager()
    cm = CredentialsManager()

    DesignSystem.clear_screen()
    click.echo()
    click.echo(click.style("  📎 ADD EVIDENCE", bold=True, fg="cyan"))
    click.echo()
    click.echo("  Select evidence type:")
    click.echo()
    click.echo("  [1] Finding")
    click.echo("  [2] Credential")
    click.echo("  [3] Screenshot")
    click.echo("  [4] Job")
    click.echo("  [q] Cancel")
    click.echo()

    etype_choice = click.prompt("Evidence type", type=str, default="q").strip()

    if etype_choice == "q":
        return

    evidence_type_map = {
        "1": "finding",
        "2": "credential",
        "3": "screenshot",
        "4": "job",
    }

    evidence_type = evidence_type_map.get(etype_choice)
    if not evidence_type:
        click.echo(click.style("  Invalid choice", fg="yellow"))
        click.pause()
        return

    # Fetch available evidence
    if evidence_type == "finding":
        findings = fm.list_findings(engagement_id)
        if not findings:
            click.echo(click.style("  No findings available", fg="yellow"))
            click.pause()
            return

        click.echo()
        click.echo(click.style("  Available Findings:", bold=True))
        for idx, f in enumerate(findings[:20], 1):
            severity_color = {
                "critical": "red",
                "high": "yellow",
                "medium": "white",
                "low": "bright_black",
            }.get(f.get("severity", "medium"), "white")
            click.echo(
                f"  [{idx}] [{click.style(f.get('severity', 'N/A').upper(), fg=severity_color)}] {f.get('title', 'Unknown')[:70]}"
            )

        click.echo()
        choice = click.prompt("Select finding # (0 to cancel)", type=int, default=0)
        if choice == 0 or choice > len(findings):
            return

        finding = findings[choice - 1]
        notes = click.prompt("Optional notes", type=str, default="")

        em.link_evidence(deliverable_id, "finding", finding["id"], notes=notes or None)
        click.echo(click.style("  ✅ Finding linked successfully", fg="green"))
        click.pause()

    elif evidence_type == "credential":
        credentials = cm.list_credentials(engagement_id)
        if not credentials:
            click.echo(click.style("  No credentials available", fg="yellow"))
            click.pause()
            return

        click.echo()
        click.echo(click.style("  Available Credentials:", bold=True))
        for idx, c in enumerate(credentials[:20], 1):
            click.echo(
                f"  [{idx}] {c.get('username', 'N/A')}@{c.get('host', 'N/A')} ({c.get('credential_type', 'N/A')})"
            )

        click.echo()
        choice = click.prompt("Select credential # (0 to cancel)", type=int, default=0)
        if choice == 0 or choice > len(credentials):
            return

        credential = credentials[choice - 1]
        notes = click.prompt("Optional notes", type=str, default="")

        em.link_evidence(
            deliverable_id, "credential", credential["id"], notes=notes or None
        )
        click.echo(click.style("  ✅ Credential linked successfully", fg="green"))
        click.pause()

    else:
        click.echo(click.style("  Feature coming soon", fg="yellow"))
        click.pause()


def _show_smart_suggestions(deliverable_id: int, engagement_id: int):
    """Show AI-powered evidence suggestions."""
    em = EvidenceManager()

    DesignSystem.clear_screen()
    click.echo()
    click.echo(click.style("  🤖 SMART EVIDENCE SUGGESTIONS", bold=True, fg="cyan"))
    click.echo()
    click.echo("  Analyzing deliverable and finding matches...")
    click.echo()

    suggestions = em.suggest_evidence(deliverable_id, engagement_id)

    if not any(suggestions.values()):
        click.echo(click.style("  No suggestions found", fg="yellow"))
        click.echo()
        click.echo("  Try adding evidence manually or run more scans first.")
        click.pause()
        return

    # Show findings suggestions
    if suggestions["findings"]:
        click.echo(
            click.style(
                f"  🔍 SUGGESTED FINDINGS ({len(suggestions['findings'])} matches)",
                bold=True,
            )
        )
        click.echo()
        for idx, f in enumerate(suggestions["findings"][:10], 1):
            confidence = f.get("_confidence", 0)
            keyword = f.get("_match_keyword", "N/A")
            severity_color = {
                "critical": "red",
                "high": "yellow",
                "medium": "white",
                "low": "bright_black",
            }.get(f.get("severity", "medium"), "white")

            confidence_color = (
                "green"
                if confidence >= 70
                else ("yellow" if confidence >= 50 else "bright_black")
            )

            click.echo(
                f"  [{idx}] [{click.style(f'{confidence}%', fg=confidence_color)}] "
                f"[{click.style(f.get('severity', 'N/A').upper(), fg=severity_color)}] "
                f"{f.get('title', 'Unknown')[:60]}"
            )
            click.echo(click.style(f"      Match: '{keyword}'", fg="bright_black"))
        click.echo()

    # Show credentials suggestions
    if suggestions["credentials"]:
        click.echo(
            click.style(
                f"  🔑 SUGGESTED CREDENTIALS ({len(suggestions['credentials'])} matches)",
                bold=True,
            )
        )
        click.echo()
        for idx, c in enumerate(suggestions["credentials"][:5], 1):
            click.echo(f"  [{idx}] {c.get('username', 'N/A')}@{c.get('host', 'N/A')}")
        click.echo()

    # Offer to link
    click.echo()
    if click.confirm("  Link suggested findings to this deliverable?", default=True):
        count = 0
        for f in suggestions["findings"][:5]:  # Link top 5
            em.link_evidence(
                deliverable_id,
                "finding",
                f["id"],
                notes=f"Auto-linked (confidence: {f.get('_confidence', 0)}%)",
            )
            count += 1

        click.echo(click.style(f"  ✅ Linked {count} findings", fg="green"))

    click.pause()


def _view_evidence_detailed(deliverable_id: int):
    """Show detailed view of all linked evidence."""
    em = EvidenceManager()
    evidence = em.get_evidence(deliverable_id)

    DesignSystem.clear_screen()
    click.echo()
    click.echo(click.style("  📋 EVIDENCE DETAILS", bold=True, fg="cyan"))
    click.echo()

    # Detailed findings
    if evidence["findings"]:
        click.echo(
            click.style(f"  🔍 FINDINGS ({len(evidence['findings'])})", bold=True)
        )
        click.echo("  " + "─" * 80)
        for f in evidence["findings"]:
            severity_color = {
                "critical": "red",
                "high": "yellow",
                "medium": "white",
                "low": "bright_black",
            }.get(f.get("severity", "medium"), "white")

            click.echo(
                f"  • [{click.style(f.get('severity', 'N/A').upper(), fg=severity_color)}] {f.get('title', 'Unknown')}"
            )
            click.echo(f"    Host: {f.get('host', 'N/A')}")
            if f.get("_link_notes"):
                click.echo(f"    Notes: {f['_link_notes']}")
            click.echo(f"    Linked: {f.get('_linked_at', 'N/A')}")
            click.echo()
        click.echo()

    # Detailed credentials
    if evidence["credentials"]:
        click.echo(
            click.style(f"  🔑 CREDENTIALS ({len(evidence['credentials'])})", bold=True)
        )
        click.echo("  " + "─" * 80)
        for c in evidence["credentials"]:
            click.echo(f"  • {c.get('username', 'N/A')}@{c.get('host', 'N/A')}")
            click.echo(f"    Type: {c.get('credential_type', 'N/A')}")
            if c.get("_link_notes"):
                click.echo(f"    Notes: {c['_link_notes']}")
            click.echo()
        click.echo()

    click.pause()


def _remove_evidence(deliverable_id: int):
    """Remove evidence links."""
    em = EvidenceManager()
    evidence = em.get_evidence(deliverable_id)

    if not any(evidence.values()):
        click.echo(click.style("  No evidence to remove", fg="yellow"))
        click.pause()
        return

    DesignSystem.clear_screen()
    click.echo()
    click.echo(click.style("  🗑️  REMOVE EVIDENCE", bold=True, fg="red"))
    click.echo()

    # Build removal menu
    items = []

    for f in evidence["findings"]:
        items.append(
            ("finding", f["id"], f"[Finding] {f.get('title', 'Unknown')[:60]}")
        )

    for c in evidence["credentials"]:
        items.append(
            (
                "credential",
                c["id"],
                f"[Credential] {c.get('username', 'N/A')}@{c.get('host', 'N/A')}",
            )
        )

    for s in evidence["screenshots"]:
        items.append(
            (
                "screenshot",
                s["id"],
                f"[Screenshot] {s.get('description', s.get('filename', 'Unknown'))[:60]}",
            )
        )

    for j in evidence["jobs"]:
        items.append(("job", j["id"], f"[Job] #{j.get('id')} - {j.get('tool', 'N/A')}"))

    click.echo("  Select evidence to remove:")
    click.echo()
    for idx, item in enumerate(items, 1):
        click.echo(f"  [{idx}] {item[2]}")
    click.echo()
    click.echo("  [q] Cancel")
    click.echo()

    choice = click.prompt("Select option", type=int, default=0, show_default=False)
    if choice == 0 or choice > len(items):
        return

    evidence_type, evidence_id, _ = items[choice - 1]

    if click.confirm("  Are you sure?", default=False):
        em.unlink_evidence(deliverable_id, evidence_type, evidence_id)
        click.echo(click.style("  ✅ Evidence unlinked", fg="green"))

    click.pause()
