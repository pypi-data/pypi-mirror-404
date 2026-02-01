#!/usr/bin/env python3
"""
souleyez.ui.tutorial_state - Tutorial state manager for interactive guided tutorial

This module tracks tutorial progress across different UI screens,
allowing contextual hints to be displayed in dashboard, job queue, etc.
"""

import json
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, Optional


class TutorialStep(Enum):
    """Tutorial steps in order."""

    INACTIVE = auto()  # Tutorial not running
    WELCOME = auto()  # Welcome screen
    ENGAGEMENT_EXPLAIN = auto()  # Explaining engagements
    ENGAGEMENT_CREATE = auto()  # Creating first engagement
    AUTOCHAIN_ENABLE = auto()  # Enabling auto-chaining
    SCANS_QUEUE = auto()  # Queuing recon scans
    DASHBOARD_INTRO = auto()  # Entered dashboard for first time
    VIEW_JOBS = auto()  # Hint: press [j] for jobs
    IN_JOB_QUEUE = auto()  # User is in job queue
    VIEW_OSINT = auto()  # Hint: press [o] for OSINT
    IN_OSINT_VIEW = auto()  # User is viewing OSINT
    VIEW_HOSTS = auto()  # Hint: press [h] for hosts
    IN_HOSTS_VIEW = auto()  # User is viewing hosts
    VIEW_JOB_DETAILS = auto()  # Hint: press [j] again for job details
    IN_JOB_DETAILS = auto()  # User viewing job details (interactive mode)
    COMPLETE = auto()  # Tutorial complete


# Hints for each step when user is in the dashboard
DASHBOARD_HINTS: Dict[TutorialStep, Dict[str, str]] = {
    TutorialStep.DASHBOARD_INTRO: {
        "title": "Welcome to the Command Center!",
        "hint": "This is your mission control - active jobs, stats, and recommendations.",
        "action": "Press Enter to continue the tutorial...",
    },
    TutorialStep.VIEW_JOBS: {
        "title": "Check Your Queued Scans",
        "hint": "Your recon scans are now running! Let's check them out.",
        "action": "Press [j] to open the Job Queue",
    },
    TutorialStep.VIEW_OSINT: {
        "title": "View OSINT Discoveries",
        "hint": "Passive recon found domains, emails, IPs and more. Let's explore!",
        "action": "Press [o] to open the OSINT view",
    },
    TutorialStep.VIEW_HOSTS: {
        "title": "View Discovered Hosts",
        "hint": "As scans complete, hosts will appear here.",
        "action": "Press [h] to open the Hosts view",
    },
    TutorialStep.VIEW_JOB_DETAILS: {
        "title": "View Job Details",
        "hint": "Now let's learn to inspect individual scan results!",
        "action": "Press [j] to go back to the Job Queue",
    },
}

# Hints for job queue view
JOB_QUEUE_HINTS: Dict[TutorialStep, Dict[str, str]] = {
    TutorialStep.IN_JOB_QUEUE: {
        "title": "This is the Job Queue",
        "hint": "Here you can see all queued, running, and completed scans.\n"
        "  • White = queued  • Yellow = running  • Green = completed  • Red = failed\n"
        "  With auto-chaining ON, new jobs will auto-queue based on findings!",
        "action": "Press [q] to go back, then try [o] for OSINT",
    },
    TutorialStep.IN_JOB_DETAILS: {
        "title": "View Job Details",
        "hint": "Type a job number to see its full output and results.\n"
        "  Or press [i] for interactive mode with more options.",
        "action": "Press [q] when done to complete the tutorial!",
    },
}

# Hints for OSINT view
OSINT_HINTS: Dict[TutorialStep, Dict[str, str]] = {
    TutorialStep.IN_OSINT_VIEW: {
        "title": "This is the OSINT View",
        "hint": "Passive recon discovered domains, emails, IPs and more.\n"
        "  This data came from theHarvester, whois, and dnsrecon.\n"
        "  No packets were sent to the target - all public sources!",
        "action": "Press [q] to go back, then try [h] for Hosts",
    },
}

# Hints for hosts view
HOSTS_HINTS: Dict[TutorialStep, Dict[str, str]] = {
    TutorialStep.IN_HOSTS_VIEW: {
        "title": "This is the Hosts View",
        "hint": "As your scans discover targets, they appear here.\n"
        "  Each host shows its IP, hostname, and discovered services.",
        "action": "Press [q] to go back, then [j] for Job Details",
    },
}


class TutorialState:
    """
    Singleton class to manage tutorial state across UI screens.

    Usage:
        from souleyez.ui.tutorial_state import get_tutorial_state, TutorialStep

        state = get_tutorial_state()
        if state.is_active():
            hint = state.get_hint_for_dashboard()
            if hint:
                show_hint(hint)
    """

    _instance: Optional["TutorialState"] = None
    STATE_FILE = Path.home() / ".souleyez" / ".tutorial_state.json"

    def __new__(cls) -> "TutorialState":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.current_step = TutorialStep.INACTIVE
        self.engagement_id: Optional[int] = None
        self._load_state()

    def _load_state(self):
        """Load tutorial state from file."""
        if self.STATE_FILE.exists():
            try:
                with open(self.STATE_FILE) as f:
                    data = json.load(f)
                    step_name = data.get("step", "INACTIVE")
                    self.current_step = TutorialStep[step_name]
                    self.engagement_id = data.get("engagement_id")
            except (json.JSONDecodeError, KeyError, FileNotFoundError):
                self.current_step = TutorialStep.INACTIVE

    def _save_state(self):
        """Save tutorial state to file."""
        self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.STATE_FILE, "w") as f:
            json.dump(
                {"step": self.current_step.name, "engagement_id": self.engagement_id}, f
            )

    def start(self, engagement_id: Optional[int] = None):
        """Start the tutorial."""
        self.current_step = TutorialStep.WELCOME
        self.engagement_id = engagement_id
        self._save_state()

    def set_step(self, step: TutorialStep):
        """Set the current tutorial step."""
        self.current_step = step
        self._save_state()

    def advance(self):
        """Advance to the next tutorial step."""
        steps = list(TutorialStep)
        current_idx = steps.index(self.current_step)
        if current_idx < len(steps) - 1:
            self.current_step = steps[current_idx + 1]
            self._save_state()

    def complete(self):
        """Mark tutorial as complete."""
        self.current_step = TutorialStep.COMPLETE
        self._save_state()

    def reset(self):
        """Reset tutorial state."""
        self.current_step = TutorialStep.INACTIVE
        self.engagement_id = None
        if self.STATE_FILE.exists():
            self.STATE_FILE.unlink()

    def is_active(self) -> bool:
        """Check if tutorial is currently active."""
        return self.current_step not in (TutorialStep.INACTIVE, TutorialStep.COMPLETE)

    def is_step(self, step: TutorialStep) -> bool:
        """Check if we're at a specific step."""
        return self.current_step == step

    def get_hint_for_dashboard(self) -> Optional[Dict[str, str]]:
        """Get hint to display in dashboard, if any."""
        return DASHBOARD_HINTS.get(self.current_step)

    def get_hint_for_job_queue(self) -> Optional[Dict[str, str]]:
        """Get hint to display in job queue, if any."""
        return JOB_QUEUE_HINTS.get(self.current_step)

    def get_hint_for_osint(self) -> Optional[Dict[str, str]]:
        """Get hint to display in OSINT view, if any."""
        return OSINT_HINTS.get(self.current_step)

    def get_hint_for_hosts(self) -> Optional[Dict[str, str]]:
        """Get hint to display in hosts view, if any."""
        return HOSTS_HINTS.get(self.current_step)


# Convenience function
def get_tutorial_state() -> TutorialState:
    """Get the tutorial state singleton."""
    return TutorialState()
