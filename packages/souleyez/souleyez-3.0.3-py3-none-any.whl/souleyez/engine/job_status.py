#!/usr/bin/env python3
"""
souleyez.engine.job_status - Job status constants and utilities

Defines the status lifecycle for jobs in the system.
"""

# Job status constants
STATUS_QUEUED = "queued"  # Job waiting to execute
STATUS_RUNNING = "running"  # Job actively executing
STATUS_DONE = "done"  # Completed successfully WITH results
STATUS_NO_RESULTS = "no_results"  # Completed successfully but found NOTHING
STATUS_WARNING = "warning"  # Partial success or non-critical issues
STATUS_ERROR = "error"  # TRUE failures (crashes, timeouts, invalid args)
STATUS_KILLED = "killed"  # User terminated

# Valid status values
VALID_STATUSES = {
    STATUS_QUEUED,
    STATUS_RUNNING,
    STATUS_DONE,
    STATUS_NO_RESULTS,
    STATUS_WARNING,
    STATUS_ERROR,
    STATUS_KILLED,
}

# Statuses that indicate job completion (terminal states)
TERMINAL_STATUSES = {
    STATUS_DONE,
    STATUS_NO_RESULTS,
    STATUS_WARNING,
    STATUS_ERROR,
    STATUS_KILLED,
}

# Statuses that should trigger auto-chaining
CHAINABLE_STATUSES = {
    STATUS_DONE,  # Always chain - results found
    STATUS_NO_RESULTS,  # May chain if intelligence-driven
    STATUS_WARNING,  # May chain with special handling
}


def is_terminal(status: str) -> bool:
    """Check if status is terminal (job completed)."""
    return status in TERMINAL_STATUSES


def is_chainable(status: str) -> bool:
    """Check if status allows auto-chaining."""
    return status in CHAINABLE_STATUSES


def get_status_display_info(status: str) -> dict:
    """
    Get display information for a status.

    Returns:
        dict with 'color', 'icon', and 'label' keys
    """
    status_info = {
        STATUS_QUEUED: {"color": "cyan", "icon": "◷", "label": "queued"},
        STATUS_RUNNING: {"color": "yellow", "icon": "▶", "label": "running"},
        STATUS_DONE: {"color": "green", "icon": "✓", "label": "done"},
        STATUS_NO_RESULTS: {"color": "white", "icon": "⊘", "label": "no results"},
        STATUS_WARNING: {"color": "yellow", "icon": "⚠", "label": "warning"},
        STATUS_ERROR: {"color": "red", "icon": "✗", "label": "error"},
        STATUS_KILLED: {"color": "magenta", "icon": "●", "label": "killed"},
    }

    return status_info.get(status, {"color": "white", "icon": "?", "label": status})
