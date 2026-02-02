#!/usr/bin/env python3
"""
souleyez.core.pending_chains - Pending chain approval queue

Manages chains that require user approval before execution.
This enables "active orchestration" where users review and approve
suggested follow-up scans instead of auto-executing them.
"""

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = os.path.join(os.path.expanduser("~"), ".souleyez", "data")
CHAINS_DIR = os.path.join(DATA_DIR, "chains")
PENDING_FILE = os.path.join(CHAINS_DIR, "pending.json")

_lock = threading.RLock()


# Chain status constants
CHAIN_PENDING = "pending"  # Awaiting user decision
CHAIN_APPROVED = "approved"  # User approved, ready to execute
CHAIN_REJECTED = "rejected"  # User rejected, will not execute
CHAIN_EXECUTED = "executed"  # Approved and job created


def _ensure_dirs():
    """Ensure chain data directory exists."""
    os.makedirs(CHAINS_DIR, exist_ok=True)


def _read_chains() -> List[Dict[str, Any]]:
    """Read pending chains from storage."""
    _ensure_dirs()
    if not os.path.exists(PENDING_FILE):
        return []
    try:
        with open(PENDING_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return []


def _write_chains(chains: List[Dict[str, Any]]):
    """Write chains to storage atomically."""
    _ensure_dirs()
    tmp = tempfile.NamedTemporaryFile(
        "w", delete=False, dir=CHAINS_DIR, encoding="utf-8"
    )
    try:
        json.dump(chains, tmp, indent=2, ensure_ascii=False)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()
        os.replace(tmp.name, PENDING_FILE)
    finally:
        if os.path.exists(tmp.name):
            try:
                os.remove(tmp.name)
            except Exception:
                pass


def _next_chain_id(chains: List[Dict[str, Any]]) -> int:
    """Get next available chain ID."""
    counter_file = os.path.join(CHAINS_DIR, ".chain_counter")

    try:
        if os.path.exists(counter_file):
            with open(counter_file, "r") as f:
                next_id = int(f.read().strip())
        else:
            maxid = 0
            for c in chains:
                if isinstance(c.get("id"), int) and c["id"] > maxid:
                    maxid = c["id"]
            next_id = maxid + 1

        with open(counter_file, "w") as f:
            f.write(str(next_id + 1))

        return next_id
    except Exception:
        maxid = 0
        for c in chains:
            if isinstance(c.get("id"), int) and c["id"] > maxid:
                maxid = c["id"]
        return maxid + 1


def add_pending_chain(
    parent_job_id: int,
    rule_description: str,
    tool: str,
    target: str,
    args: List[str],
    priority: int,
    engagement_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Add a chain to the pending approval queue.

    Args:
        parent_job_id: Job that triggered this chain
        rule_description: Description from the ChainRule
        tool: Target tool to run
        target: Target (IP, URL, etc.)
        args: Arguments for the tool
        priority: Chain priority (1-10)
        engagement_id: Associated engagement
        metadata: Additional context

    Returns:
        Chain ID
    """
    with _lock:
        chains = _read_chains()
        chain_id = _next_chain_id(chains)
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        chain = {
            "id": chain_id,
            "parent_job_id": parent_job_id,
            "rule_description": rule_description,
            "tool": tool,
            "target": target,
            "args": args or [],
            "priority": priority,
            "status": CHAIN_PENDING,
            "created_at": now,
            "decided_at": None,
            "executed_at": None,
            "job_id": None,  # Set when executed
            "engagement_id": engagement_id,
            "metadata": metadata or {},
        }

        chains.append(chain)
        _write_chains(chains)

    return chain_id


def list_pending_chains(
    status: Optional[str] = None,
    engagement_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    List chains, optionally filtered by status and engagement.

    Args:
        status: Filter by status (pending, approved, rejected, executed)
        engagement_id: Filter by engagement
        limit: Max chains to return
        offset: Number of chains to skip (for pagination)

    Returns:
        List of chain dicts, sorted by priority (high to low) then created_at
    """
    chains = _read_chains()

    # Apply filters
    if status:
        chains = [c for c in chains if c.get("status") == status]
    if engagement_id is not None:
        chains = [c for c in chains if c.get("engagement_id") == engagement_id]

    # Sort by priority (desc) then created_at (asc)
    chains.sort(key=lambda c: (-c.get("priority", 5), c.get("created_at", "")))

    return chains[offset : offset + limit]


def get_pending_chain(chain_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific chain by ID."""
    chains = _read_chains()
    for c in chains:
        if c.get("id") == chain_id:
            return c
    return None


def approve_chain(chain_id: int) -> bool:
    """
    Approve a pending chain for execution.

    Returns:
        True if approved, False if not found or already decided
    """
    with _lock:
        chains = _read_chains()
        for c in chains:
            if c.get("id") == chain_id:
                if c.get("status") != CHAIN_PENDING:
                    return False  # Already decided
                c["status"] = CHAIN_APPROVED
                c["decided_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                _write_chains(chains)
                return True
    return False


def reject_chain(chain_id: int) -> bool:
    """
    Reject a pending chain.

    Returns:
        True if rejected, False if not found or already decided
    """
    with _lock:
        chains = _read_chains()
        for c in chains:
            if c.get("id") == chain_id:
                if c.get("status") != CHAIN_PENDING:
                    return False
                c["status"] = CHAIN_REJECTED
                c["decided_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                _write_chains(chains)
                return True
    return False


def approve_all_pending(engagement_id: Optional[int] = None) -> int:
    """
    Approve all pending chains.

    Args:
        engagement_id: Only approve for this engagement (optional)

    Returns:
        Number of chains approved
    """
    with _lock:
        chains = _read_chains()
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        approved = 0

        for c in chains:
            if c.get("status") == CHAIN_PENDING:
                if engagement_id is None or c.get("engagement_id") == engagement_id:
                    c["status"] = CHAIN_APPROVED
                    c["decided_at"] = now
                    approved += 1

        if approved > 0:
            _write_chains(chains)

        return approved


def reject_all_pending(engagement_id: Optional[int] = None) -> int:
    """
    Reject all pending chains.

    Args:
        engagement_id: Only reject for this engagement (optional)

    Returns:
        Number of chains rejected
    """
    with _lock:
        chains = _read_chains()
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rejected = 0

        for c in chains:
            if c.get("status") == CHAIN_PENDING:
                if engagement_id is None or c.get("engagement_id") == engagement_id:
                    c["status"] = CHAIN_REJECTED
                    c["decided_at"] = now
                    rejected += 1

        if rejected > 0:
            _write_chains(chains)

        return rejected


def mark_chain_executed(chain_id: int, job_id: int) -> bool:
    """
    Mark an approved chain as executed with the created job ID.

    Args:
        chain_id: Chain that was executed
        job_id: Job ID that was created

    Returns:
        True if updated, False if not found
    """
    with _lock:
        chains = _read_chains()
        for c in chains:
            if c.get("id") == chain_id:
                c["status"] = CHAIN_EXECUTED
                c["executed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                c["job_id"] = job_id
                _write_chains(chains)
                return True
    return False


def get_approved_chains(
    engagement_id: Optional[int] = None, limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get approved chains ready for execution.

    Args:
        engagement_id: Filter by engagement (None = all)
        limit: Max chains to return

    Returns:
        List of approved chains, sorted by priority
    """
    return list_pending_chains(
        status=CHAIN_APPROVED, engagement_id=engagement_id, limit=limit
    )


def purge_old_chains(days: int = 7) -> int:
    """
    Remove chains older than specified days (executed or rejected only).

    Args:
        days: Remove chains older than this

    Returns:
        Number of chains purged
    """
    import datetime

    with _lock:
        chains = _read_chains()
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

        original_count = len(chains)
        chains = [
            c
            for c in chains
            if c.get("status") == CHAIN_PENDING  # Keep pending
            or c.get("status") == CHAIN_APPROVED  # Keep approved (not yet executed)
            or c.get("created_at", "") > cutoff_str  # Keep recent
        ]

        purged = original_count - len(chains)
        if purged > 0:
            _write_chains(chains)

        return purged


def get_pending_count(engagement_id: Optional[int] = None) -> int:
    """Get count of pending chains awaiting approval."""
    chains = _read_chains()
    pending = [c for c in chains if c.get("status") == CHAIN_PENDING]
    if engagement_id is not None:
        pending = [c for c in pending if c.get("engagement_id") == engagement_id]
    return len(pending)


def get_chain_stats(engagement_id: Optional[int] = None) -> Dict[str, int]:
    """
    Get chain statistics.

    Returns:
        Dict with counts: pending, approved, rejected, executed
    """
    chains = _read_chains()

    if engagement_id is not None:
        chains = [c for c in chains if c.get("engagement_id") == engagement_id]

    stats = {
        "pending": 0,
        "approved": 0,
        "rejected": 0,
        "executed": 0,
        "total": len(chains),
    }

    for c in chains:
        status = c.get("status", "")
        if status in stats:
            stats[status] += 1

    return stats


def purge_orphaned_chains() -> int:
    """
    Remove chains that reference non-existent engagements.

    This can happen when engagements are deleted but their pending
    chains weren't cleaned up. Orphaned chains waste resources and
    will never be processed.

    Returns:
        Number of orphaned chains removed
    """
    import sqlite3

    with _lock:
        chains = _read_chains()
        if not chains:
            return 0

        # Get all valid engagement IDs from database
        try:
            db_path = os.path.join(os.path.expanduser("~"), ".souleyez", "souleyez.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT id FROM engagements")
            valid_ids = {row[0] for row in cursor.fetchall()}
            conn.close()
        except Exception:
            return 0  # Can't verify, don't purge

        original_count = len(chains)

        # Keep only chains with valid engagement IDs (or None)
        chains = [
            c
            for c in chains
            if c.get("engagement_id") is None or c.get("engagement_id") in valid_ids
        ]

        purged = original_count - len(chains)
        if purged > 0:
            _write_chains(chains)

        return purged
