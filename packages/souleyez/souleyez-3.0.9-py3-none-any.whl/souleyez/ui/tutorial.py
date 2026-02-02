#!/usr/bin/env python3
"""
souleyez.ui.tutorial - Interactive guided tutorial for first-time users

This tutorial guides new users through:
1. Understanding engagements
2. Creating their first engagement
3. Enabling auto-chaining
4. Running reconnaissance scans
5. Exploring the Command Center (dashboard) interactively
"""

import time
from pathlib import Path

import click

from souleyez.ui.tutorial_state import TutorialStep, get_tutorial_state


def clear_screen():
    """Clear the terminal screen."""
    from souleyez.ui.design_system import DesignSystem

    DesignSystem.clear_screen()


def wait_for_enter(prompt="Press Enter to continue..."):
    """Wait for user to press Enter."""
    click.pause(prompt)


def show_header(title, subtitle=None):
    """Display a section header."""
    click.echo()
    click.echo(click.style("=" * 60, fg="cyan"))
    click.echo(click.style(f"  {title}", fg="cyan", bold=True))
    if subtitle:
        click.echo(click.style(f"  {subtitle}", fg="white"))
    click.echo(click.style("=" * 60, fg="cyan"))
    click.echo()


def type_text(text, delay=0.02):
    """Print text with a typewriter effect."""
    for char in text:
        click.echo(char, nl=False)
        time.sleep(delay)
    click.echo()


def run_tutorial():
    """Main tutorial flow."""
    clear_screen()

    # Welcome
    show_header("Welcome to SoulEyez!", "Your AI-Powered Penetration Testing Platform")

    click.echo("This tutorial will walk you through:")
    click.echo()
    click.echo("  1. Understanding engagements")
    click.echo("  2. Creating your first engagement")
    click.echo("  3. Enabling auto-chaining")
    click.echo("  4. Running reconnaissance scans")
    click.echo(
        "  5. "
        + click.style("Hands-on exploration", fg="yellow")
        + " of the Command Center"
    )
    click.echo()

    wait_for_enter()

    # Step 1: What is an Engagement?
    clear_screen()
    show_header("Step 1: Understanding Engagements")

    click.echo(
        "An "
        + click.style("engagement", fg="cyan", bold=True)
        + " is a container for all your pentest data."
    )
    click.echo()
    click.echo("Think of it like a project folder that keeps everything organized:")
    click.echo()
    click.echo(
        "  • " + click.style("Hosts", fg="green") + " - Target systems you discover"
    )
    click.echo(
        "  • "
        + click.style("Services", fg="green")
        + " - Open ports and running software"
    )
    click.echo(
        "  • " + click.style("Findings", fg="green") + " - Vulnerabilities you find"
    )
    click.echo(
        "  • "
        + click.style("Credentials", fg="green")
        + " - Usernames, passwords, keys"
    )
    click.echo(
        "  • " + click.style("Evidence", fg="green") + " - Screenshots, logs, artifacts"
    )
    click.echo()
    click.echo(
        "Each engagement is "
        + click.style("isolated", fg="yellow")
        + " - data from one"
    )
    click.echo("pentest never mixes with another.")
    click.echo()

    wait_for_enter()

    # Step 2: Create an Engagement
    clear_screen()
    show_header("Step 2: Create Your First Engagement")

    click.echo("Let's create a test engagement to practice with.")
    click.echo()
    click.echo(
        "We'll use a " + click.style("safe, legal target", fg="green", bold=True) + ":"
    )
    click.echo()
    click.echo("  " + click.style("vulnweb.com", fg="cyan"))
    click.echo("  (Acunetix's intentionally vulnerable test domain)")
    click.echo()

    if not click.confirm("Create a practice engagement?", default=True):
        click.echo()
        click.echo("No problem! You can run 'souleyez tutorial' anytime.")
        return

    click.echo()

    # Create the engagement
    try:
        from souleyez.storage.engagements import EngagementManager

        em = EngagementManager()

        # Check if tutorial engagement already exists
        existing = em.get("Tutorial Engagement")
        if existing:
            engagement_id = existing["id"]
            click.echo(click.style("✓ Using existing Tutorial Engagement", fg="green"))
        else:
            engagement_id = em.create(
                name="Tutorial Engagement",
                description="Created by SoulEyez tutorial. Target: vulnweb.com",
            )
            click.echo(
                click.style("✓ Created engagement: Tutorial Engagement", fg="green")
            )

        # Set as current engagement
        em.set_current("Tutorial Engagement")
        click.echo(f"  ID: {engagement_id}")
        click.echo()

    except Exception as e:
        click.echo(click.style(f"✗ Error creating engagement: {e}", fg="red"))
        click.echo("Please check 'souleyez doctor' for issues.")
        wait_for_enter()
        return

    wait_for_enter()

    # Step 3: Enable Auto-Chaining
    clear_screen()
    show_header("Step 3: Enable Auto-Chaining")

    click.echo(
        "Before we scan, let's enable "
        + click.style("auto-chaining", fg="yellow", bold=True)
        + "!"
    )
    click.echo()
    click.echo("Auto-chaining is SoulEyez's killer feature:")
    click.echo()
    click.echo(
        "  • When recon finds a host → " + click.style("auto-queue nmap", fg="cyan")
    )
    click.echo(
        "  • When nmap finds HTTP → "
        + click.style("auto-queue gobuster, nikto", fg="cyan")
    )
    click.echo(
        "  • When nmap finds SSH → " + click.style("auto-queue hydra", fg="cyan")
    )
    click.echo()
    click.echo("It thinks like a pentester and queues the logical next steps!")
    click.echo()

    if click.confirm("Enable auto-chaining for this tutorial?", default=True):
        try:
            from souleyez.core.tool_chaining import ToolChaining

            chaining = ToolChaining()
            chaining.enable_chaining()
            click.echo()
            click.echo(click.style("  ✓ Auto-chaining ENABLED!", fg="green", bold=True))
            click.echo(
                "  Mode: "
                + click.style("AUTO", fg="green")
                + " (chains execute immediately)"
            )
            click.echo()
        except Exception as e:
            click.echo(click.style(f"  Could not enable: {e}", fg="yellow"))
            click.echo()
    else:
        click.echo()
        click.echo("  Skipped. You can enable it later in Settings.")
        click.echo()

    wait_for_enter()

    # Step 4: Run Reconnaissance
    clear_screen()
    show_header("Step 4: Running Your First Recon")

    click.echo(
        "Now let's run "
        + click.style("passive reconnaissance", fg="cyan", bold=True)
        + "!"
    )
    click.echo()
    click.echo(
        "We'll use "
        + click.style("theHarvester", fg="green", bold=True)
        + " to search URLScan.io"
    )
    click.echo("for emails, subdomains, and IPs related to our target.")
    click.echo()
    click.echo(
        "With "
        + click.style("auto-chaining ON", fg="yellow", bold=True)
        + ", when theHarvester finds hosts:"
    )
    click.echo(
        "  → "
        + click.style("whois", fg="cyan")
        + " and "
        + click.style("dnsrecon", fg="cyan")
        + " will auto-queue"
    )
    click.echo(
        "  → Found web servers trigger " + click.style("nmap", fg="cyan") + " scans"
    )
    click.echo("  → And so on... SoulEyez chains tools intelligently!")
    click.echo()

    target_domain = "vulnweb.com"

    queue_scan = click.confirm(
        f"Queue theHarvester against {target_domain}?", default=True
    )
    if queue_scan:
        click.echo()
        click.echo(
            click.style(
                "  ✓ Scan will start when you enter the Command Center!", fg="green"
            )
        )
        click.echo()
    else:
        click.echo()
        click.echo("  Skipped. You can run scans from the main menu.")
        click.echo()

    wait_for_enter()

    # Step 5: Launch into Command Center
    clear_screen()
    show_header("Step 5: Entering the Command Center")

    click.echo(
        "Now for the " + click.style("hands-on", fg="yellow", bold=True) + " part!"
    )
    click.echo()
    click.echo(
        "We're about to launch you into the "
        + click.style("Command Center", fg="cyan", bold=True)
        + " (dashboard)."
    )
    click.echo()
    click.echo(
        "The tutorial will continue there with "
        + click.style("interactive hints", fg="green")
        + ":"
    )
    click.echo()
    click.echo("  • You'll see your queued scans running")
    click.echo("  • Hints will guide you to explore different views")
    click.echo("  • Press the highlighted keys to navigate")
    click.echo()
    click.echo(click.style("Quick reference for the Command Center:", bold=True))
    click.echo(
        "  " + click.style("[j]", fg="yellow") + " Jobs queue    - See running scans"
    )
    click.echo(
        "  "
        + click.style("[h]", fg="yellow")
        + " Hosts view    - See discovered targets"
    )
    click.echo(
        "  " + click.style("[f]", fg="yellow") + " Findings      - See vulnerabilities"
    )
    click.echo(
        "  " + click.style("[q]", fg="yellow") + " Quit          - Exit dashboard"
    )
    click.echo()

    if click.confirm("Ready to enter the Command Center?", default=True):
        # Set tutorial state for dashboard hints
        tutorial_state = get_tutorial_state()
        tutorial_state.set_step(TutorialStep.DASHBOARD_INTRO)

        # Queue the scan NOW (right before entering dashboard)
        if queue_scan:
            try:
                from souleyez.engine.background import enqueue_job

                click.echo()
                click.echo("Starting scan...")
                job_id = enqueue_job(
                    tool="theharvester",
                    target=target_domain,
                    args=["-b", "urlscan", "-l", "500"],
                    label="tutorial-recon",
                    engagement_id=engagement_id,
                )
                click.echo(
                    click.style(f"  ✓ theHarvester queued (Job #{job_id})", fg="green")
                )
            except Exception as e:
                click.echo(
                    click.style(f"  Note: Could not queue scan: {e}", fg="yellow")
                )

        click.echo()
        click.echo(click.style("Launching Command Center...", fg="cyan"))
        time.sleep(1)

        # Launch the dashboard with tutorial mode active
        try:
            from souleyez.ui.dashboard import run_dashboard

            run_dashboard()
        except Exception as e:
            click.echo(click.style(f"Could not launch dashboard: {e}", fg="red"))
            click.echo("You can launch it manually with: souleyez dashboard")

        # After dashboard exits, show completion
        _show_tutorial_complete()
    else:
        click.echo()
        click.echo("No problem! You can explore the Command Center anytime with:")
        click.echo(click.style("  souleyez dashboard", fg="cyan"))
        click.echo()
        _show_tutorial_complete()


def _show_tutorial_complete():
    """Show tutorial completion screen."""
    # Mark tutorial complete
    tutorial_state = get_tutorial_state()
    tutorial_state.complete()

    clear_screen()
    show_header("Tutorial Complete!")

    click.echo(
        click.style(
            "You're ready to start pentesting with SoulEyez!", fg="green", bold=True
        )
    )
    click.echo()
    click.echo("What you learned:")
    click.echo("  ✓ Engagements organize your pentest data")
    click.echo("  ✓ Auto-chaining queues follow-up scans automatically")
    click.echo("  ✓ Passive recon (theHarvester, whois, dnsrecon) is a great start")
    click.echo("  ✓ The Command Center shows live progress and recommendations")
    click.echo()
    click.echo(click.style("Quick reference:", bold=True))
    click.echo()
    click.echo(
        "  "
        + click.style("souleyez dashboard", fg="cyan")
        + "    - Real-time Command Center"
    )
    click.echo(
        "  "
        + click.style("souleyez interactive", fg="cyan")
        + "  - Menu-driven interface"
    )
    click.echo(
        "  "
        + click.style("souleyez setup", fg="cyan")
        + "        - Install pentest tools"
    )
    click.echo(
        "  " + click.style("souleyez doctor", fg="cyan") + "       - Diagnose issues"
    )
    click.echo()
    click.echo(click.style("Practice targets (safe & legal):", bold=True))
    click.echo("  • vulnweb.com subdomains (Acunetix)")
    click.echo("  • demo.owasp-juice.shop (OWASP)")
    click.echo()
    click.echo(
        click.style("⚠️  NEVER scan systems without permission!", fg="red", bold=True)
    )
    click.echo()

    # Always disable auto-chaining (it's a PRO feature, tutorial enabled for demo)
    try:
        from souleyez.core.tool_chaining import ToolChaining

        chaining = ToolChaining()
        chaining.disable_chaining()
    except Exception:
        pass

    # Offer to clean up tutorial data
    click.echo()
    if click.confirm("Clean up tutorial engagement and jobs?", default=True):
        _cleanup_tutorial_data()
        click.echo(click.style("  ✓ Tutorial data cleaned up!", fg="green"))
    else:
        click.echo(
            "Tutorial engagement kept. Check results with: "
            + click.style("souleyez interactive", fg="cyan")
        )

    click.echo()
    click.echo("Need help?")
    click.echo(
        "  • In-app: Press " + click.style("[?]", fg="yellow") + " for contextual help"
    )
    click.echo(
        "  • Full docs: "
        + click.style("souleyez interactive", fg="cyan")
        + " → Settings → "
        + click.style("[h]", fg="yellow")
        + " Help Center"
    )
    click.echo()
    click.echo(click.style("Happy hacking! 🎯", fg="cyan", bold=True))
    click.echo()

    wait_for_enter("Press Enter to exit tutorial...")


def _cleanup_tutorial_data():
    """Clean up tutorial engagement, jobs, and related data."""
    try:
        from souleyez.core.tool_chaining import ToolChaining
        from souleyez.engine.background import delete_job, kill_job, list_jobs
        from souleyez.storage.engagements import EngagementManager

        # Disable auto-chaining (it's a PRO feature, tutorial enabled it for demo)
        try:
            chaining = ToolChaining()
            chaining.disable_chaining()
        except Exception:
            pass

        em = EngagementManager()

        # Find tutorial engagement
        tutorial_eng = em.get("Tutorial Engagement")
        engagement_id = tutorial_eng["id"] if tutorial_eng else None

        # Delete all tutorial jobs (by label OR by engagement_id)
        all_jobs = list_jobs(limit=500)
        for job in all_jobs:
            is_tutorial_job = job.get("label") == "tutorial-recon" or (
                engagement_id and job.get("engagement_id") == engagement_id
            )
            if is_tutorial_job:
                try:
                    # Kill if running, then delete
                    if job.get("status") in ("running", "queued"):
                        kill_job(job["id"])
                    delete_job(job["id"])
                except Exception:
                    pass

        # Reset current engagement BEFORE deleting tutorial engagement
        # (otherwise get_current() will fail trying to load deleted engagement)
        if tutorial_eng:
            current = em.get_current()
            if current and current.get("id") == tutorial_eng["id"]:
                em.set_current("default")

            # Now safe to delete the tutorial engagement
            em.delete("Tutorial Engagement")

    except Exception as e:
        click.echo(click.style(f"  Note: Could not fully clean up: {e}", fg="yellow"))


if __name__ == "__main__":
    run_tutorial()
