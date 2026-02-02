"""Smart recommendations dashboard."""

from typing import Dict

import click

from souleyez.storage.engagements import EngagementManager
from souleyez.storage.recommendation_engine import RecommendationEngine
from souleyez.ui.design_system import DesignSystem


def show_recommendations_dashboard(engagement_id: int):
    """
    Display AI-powered recommendations dashboard.

    Shows:
    - Next recommended actions
    - Blocker resolution suggestions
    - Quick wins
    - Coverage gaps
    - At-risk deliverables
    - Priority boost suggestions
    """
    re = RecommendationEngine()
    em = EngagementManager()

    engagement = em.get_by_id(engagement_id)
    if not engagement:
        click.echo(click.style("  Error: Engagement not found", fg="red"))
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
                " 🤖 SMART RECOMMENDATIONS ".center(width - 2), bold=True, fg="cyan"
            )
            + "│"
        )
        click.echo("└" + "─" * (width - 2) + "┘")
        click.echo()

        click.echo(
            f"  Engagement: {click.style(engagement['name'], bold=True, fg='cyan')}"
        )
        click.echo()
        click.echo(
            click.style(
                "  Analyzing deliverables, evidence, and progress...", fg="bright_black"
            )
        )
        click.echo()

        # Get recommendations
        recommendations = re.get_recommendations(engagement_id)

        # Next Actions
        next_actions = recommendations["next_actions"]
        if next_actions:
            click.echo(
                click.style("  🎯 RECOMMENDED NEXT ACTIONS", bold=True, fg="green")
            )
            click.echo("  " + "─" * (width - 4))
            click.echo()

            for idx, rec in enumerate(next_actions[:5], 1):
                d = rec["deliverable"]
                confidence = rec["confidence"]

                confidence_color = (
                    "green"
                    if confidence >= 70
                    else ("yellow" if confidence >= 50 else "white")
                )
                priority_color = {
                    "critical": "red",
                    "high": "yellow",
                    "medium": "white",
                    "low": "bright_black",
                }.get(d.get("priority", "medium"), "white")

                click.echo(
                    f"  {idx}. [{click.style(f'{confidence}%', fg=confidence_color)}] "
                    f"[{click.style(d.get('priority', 'medium').upper(), fg=priority_color)}] "
                    f"{d['title'][:60]}"
                )

                if rec["reasons"]:
                    reasons_str = ", ".join(rec["reasons"][:3])
                    click.echo(
                        click.style(f"     Why: {reasons_str}", fg="bright_black")
                    )

            click.echo()

        # Quick Wins
        quick_wins = recommendations["quick_wins"]
        if quick_wins:
            click.echo(click.style("  ⚡ QUICK WINS", bold=True, fg="cyan"))
            click.echo("  " + "─" * (width - 4))
            click.echo()

            for idx, qw in enumerate(quick_wins[:3], 1):
                d = qw["deliverable"]
                est_min = qw["estimated_minutes"]

                click.echo(f"  {idx}. {d['title'][:60]}")
                click.echo(
                    click.style(
                        f"     ~{est_min} minutes | {', '.join(qw['reasons'][:2])}",
                        fg="bright_black",
                    )
                )

            click.echo()

        # Coverage Gaps
        coverage_gaps = recommendations["coverage_gaps"]
        if coverage_gaps:
            click.echo(click.style("  📊 COVERAGE GAPS", bold=True, fg="yellow"))
            click.echo("  " + "─" * (width - 4))
            click.echo()

            for gap in coverage_gaps[:3]:
                severity_color = "red" if gap["severity"] == "critical" else "yellow"
                phase_name = gap["phase"].replace("_", " ").title()

                click.echo(
                    f"  • {click.style(phase_name, fg=severity_color)}: "
                    f"{gap['completion_rate']:.0f}% complete "
                    f"({gap['remaining']} remaining)"
                )
                click.echo(
                    click.style(f"    → {gap['recommendation']}", fg="bright_black")
                )

            click.echo()

        # At Risk
        at_risk = recommendations["at_risk"]
        if at_risk:
            click.echo(click.style("  ⚠️  AT RISK", bold=True, fg="red"))
            click.echo("  " + "─" * (width - 4))
            click.echo()

            for item in at_risk[:3]:
                d = item["deliverable"]
                severity_color = {
                    "critical": "red",
                    "high": "yellow",
                    "medium": "white",
                }.get(item["severity"], "white")

                click.echo(
                    f"  • [{click.style(item['severity'].upper(), fg=severity_color)}] "
                    f"{d['title'][:60]}"
                )

                if item["risk_factors"]:
                    factors_str = ", ".join(item["risk_factors"])
                    click.echo(
                        click.style(f"    Risk: {factors_str}", fg="bright_black")
                    )

            click.echo()

        # Blockers
        blockers = recommendations["blockers"]
        if blockers:
            click.echo(click.style("  🚧 BLOCKER RESOLUTION", bold=True, fg="yellow"))
            click.echo("  " + "─" * (width - 4))
            click.echo()

            for blocker in blockers[:3]:
                d = blocker["deliverable"]

                click.echo(f"  • {d['title'][:60]}")
                click.echo(
                    click.style(f"    Blocker: {blocker['blocker']}", fg="yellow")
                )

                if blocker["suggestions"]:
                    click.echo(click.style(f"    Suggestions:", fg="bright_black"))
                    for sugg in blocker["suggestions"][:2]:
                        click.echo(click.style(f"      - {sugg}", fg="bright_black"))

            click.echo()

        # Priority Boost
        priority_boost = recommendations["priority_boost"]
        if priority_boost:
            click.echo(
                click.style("  🔼 PRIORITY BOOST SUGGESTIONS", bold=True, fg="cyan")
            )
            click.echo("  " + "─" * (width - 4))
            click.echo()

            for item in priority_boost[:3]:
                d = item["deliverable"]

                click.echo(f"  • {d['title'][:60]}")
                click.echo(
                    f"    {item['current_priority'].title()} → "
                    f"{click.style(item['suggested_priority'].title(), bold=True, fg='yellow')}"
                )

                if item["reasons"]:
                    reasons_str = ", ".join(item["reasons"])
                    click.echo(
                        click.style(f"    Why: {reasons_str}", fg="bright_black")
                    )

            click.echo()

        # Summary message if no recommendations
        if not any(
            [next_actions, quick_wins, coverage_gaps, at_risk, blockers, priority_boost]
        ):
            click.echo(click.style("  ✅ No recommendations at this time", fg="green"))
            click.echo()
            click.echo("  All deliverables are on track!")
            click.echo()

        # Menu
        click.echo(click.style("  ⚙️  ACTIONS", bold=True, fg="cyan"))
        click.echo("  " + "─" * (width - 4))
        click.echo()
        click.echo("  [R] Refresh Recommendations")
        click.echo("  [D] View Detailed Analysis")
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
        elif choice == "r":
            continue
        elif choice == "d":
            _show_detailed_analysis(engagement_id, recommendations)


def _show_detailed_analysis(engagement_id: int, recommendations: Dict):
    """Show detailed breakdown of all recommendations."""
    DesignSystem.clear_screen()

    width = DesignSystem.get_terminal_width()

    click.echo("\n┌" + "─" * (width - 2) + "┐")
    click.echo(
        "│"
        + click.style(" 📊 DETAILED ANALYSIS ".center(width - 2), bold=True, fg="cyan")
        + "│"
    )
    click.echo("└" + "─" * (width - 2) + "┘")
    click.echo()

    # All Next Actions
    next_actions = recommendations["next_actions"]
    if next_actions:
        click.echo(click.style("  🎯 ALL RECOMMENDED ACTIONS", bold=True, fg="green"))
        click.echo("  " + "─" * (width - 4))
        click.echo()

        for idx, rec in enumerate(next_actions, 1):
            d = rec["deliverable"]

            click.echo(f"  {idx}. {d['title']}")
            click.echo(f"     Score: {rec['score']} | Confidence: {rec['confidence']}%")
            click.echo(
                f"     Priority: {d.get('priority', 'medium').title()} | "
                f"Status: {d['status'].replace('_', ' ').title()}"
            )

            if rec["reasons"]:
                click.echo(f"     Reasons: {', '.join(rec['reasons'])}")

            click.echo()

    # All Quick Wins
    quick_wins = recommendations["quick_wins"]
    if quick_wins:
        click.echo(click.style("  ⚡ ALL QUICK WINS", bold=True, fg="cyan"))
        click.echo("  " + "─" * (width - 4))
        click.echo()

        for idx, qw in enumerate(quick_wins, 1):
            d = qw["deliverable"]

            click.echo(f"  {idx}. {d['title']}")
            click.echo(f"     Estimated: ~{qw['estimated_minutes']} minutes")
            click.echo(f"     Reasons: {', '.join(qw['reasons'])}")
            click.echo()

    # All Coverage Gaps
    coverage_gaps = recommendations["coverage_gaps"]
    if coverage_gaps:
        click.echo(click.style("  📊 ALL COVERAGE GAPS", bold=True, fg="yellow"))
        click.echo("  " + "─" * (width - 4))
        click.echo()

        for gap in coverage_gaps:
            phase_name = gap["phase"].replace("_", " ").title()

            click.echo(f"  • {phase_name}")
            click.echo(
                f"    Completion: {gap['completion_rate']:.1f}% "
                f"({gap['completed']}/{gap['total']})"
            )
            click.echo(f"    Recommendation: {gap['recommendation']}")
            click.echo()

    click.pause()
