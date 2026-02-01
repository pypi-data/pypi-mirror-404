#!/usr/bin/env python3
"""
souleyez.engine.background — plugin-aware job queue + worker (file-backed)

Design notes:
 - Small, robust JSON-backed job store (data/jobs/jobs.json)
 - Logs to data/jobs/<job_id>.log
 - Plugin-first execution: attempt to call plugin.run(target, args, label, log_path)
 - Fallback to subprocess.run([tool, ...]) if plugin not available
 - Worker supports foreground (--fg) and background start
 - Long-running tool kill timeout: 300s (5 minutes)
 - Minimal, clean logging to worker.log and per-job logs
 - Auto-parse results into database when jobs complete
"""

from __future__ import annotations

import fcntl
import inspect
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from souleyez.log_config import get_logger

from .job_status import (
    STATUS_DONE,
    STATUS_ERROR,
    STATUS_KILLED,
    STATUS_NO_RESULTS,
    STATUS_QUEUED,
    STATUS_RUNNING,
    STATUS_WARNING,
    is_chainable,
)
from .log_sanitizer import LogSanitizer

logger = get_logger(__name__)

# Use user home directory for data storage (not package directory)
DATA_DIR = os.path.join(os.path.expanduser("~"), ".souleyez", "data")
JOBS_DIR = os.path.join(DATA_DIR, "jobs")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
JOBS_FILE = os.path.join(JOBS_DIR, "jobs.json")
WORKER_LOG = os.path.join(LOGS_DIR, "worker.log")
HEARTBEAT_FILE = os.path.join(JOBS_DIR, ".worker_heartbeat")
JOBS_LOCK_FILE = os.path.join(JOBS_DIR, ".jobs.lock")  # Cross-process file lock
JOB_TIMEOUT_SECONDS = 3600  # 1 hour (changed from 300s/5min)
HEARTBEAT_INTERVAL = 10  # seconds between heartbeat writes
HEARTBEAT_STALE_THRESHOLD = 30  # seconds before heartbeat considered stale
JOB_HUNG_THRESHOLD = 300  # 5 minutes with no output = possibly hung
JOBS_BACKUP_COUNT = 3  # Number of rotating backups to keep
MAX_RETRIES = 2  # Maximum auto-retries for transient errors

# Patterns indicating transient errors that should trigger auto-retry
# These are network/timing issues that often succeed on retry
TRANSIENT_ERROR_PATTERNS = [
    "NetBIOSTimeout",
    "connection timed out",
    "Connection timed out",
    "NETBIOS connection with the remote host timed out",
    "Connection reset by peer",
    "temporarily unavailable",
    "Resource temporarily unavailable",
    "SMBTimeout",
    "timed out while waiting",
    # Impacket-specific timeout patterns
    "] timed out",  # Matches: [Errno Connection error (IP:port)] timed out
    "RemoteOperations failed",  # Impacket remote operation failures
    "Errno Connection error",  # Generic Impacket connection errors
]

_lock = threading.RLock()  # Reentrant lock allows nested acquisition by same thread


def _is_transient_error(log_content: str) -> bool:
    """Check if log content indicates a transient error that should be retried."""
    if not log_content:
        return False
    for pattern in TRANSIENT_ERROR_PATTERNS:
        if pattern.lower() in log_content.lower():
            return True
    return False


def _is_netexec_flaky_empty(log_content: str, job: dict) -> bool:
    """
    Check if netexec/crackmapexec produced no output (flaky ARM behavior).

    On ARM, netexec is ~20% flaky - it exits 0 but sometimes produces
    zero output. This detects ONLY that case.

    DOES NOT retry when:
    - Access denied (has "[-]" error output)
    - Connected but no shares (legitimate result)
    - Any netexec output exists
    """
    tool = job.get("tool", "").lower()
    args = job.get("args", [])

    if tool not in ("crackmapexec", "nxc", "netexec"):
        return False

    args_str = " ".join(args).lower() if args else ""
    if "--shares" not in args_str and "smb" not in args_str:
        return False

    lower = log_content.lower()

    # If we got ANY netexec output, it's a real response - don't retry
    # This includes error output like "[-]" which indicates access denied
    has_any_output = any(
        x in lower for x in ["smb", "[*]", "[+]", "[-]", "445", "signing"]
    )

    # Only retry if truly zero output (ARM flakiness)
    return not has_any_output


class _CrossProcessLock:
    """
    Cross-process file lock using fcntl.flock().

    This ensures that only one process (UI or worker) can read/write
    jobs.json at a time, preventing race conditions where one process
    overwrites another's changes.
    """

    def __init__(self, lock_file: str, timeout: float = 10.0):
        self.lock_file = lock_file
        self.timeout = timeout
        self._fd = None

    def __enter__(self):
        import errno
        import fcntl

        # Ensure lock file directory exists
        os.makedirs(os.path.dirname(self.lock_file), exist_ok=True)

        # Open lock file (create if doesn't exist)
        self._fd = open(self.lock_file, "w")

        # Try to acquire lock with timeout
        start_time = time.time()
        while True:
            try:
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self  # Lock acquired
            except (IOError, OSError) as e:
                if e.errno not in (errno.EWOULDBLOCK, errno.EAGAIN):
                    raise
                # Lock held by another process, wait and retry
                if time.time() - start_time > self.timeout:
                    raise TimeoutError(
                        f"Could not acquire lock on {self.lock_file} within {self.timeout}s"
                    )
                time.sleep(0.05)  # 50ms backoff

    def __exit__(self, exc_type, exc_val, exc_tb):
        import fcntl

        if self._fd:
            try:
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                self._fd.close()
            except Exception:
                pass
            self._fd = None
        return False  # Don't suppress exceptions


def _jobs_lock():
    """Get a cross-process lock for jobs.json access."""
    return _CrossProcessLock(JOBS_LOCK_FILE)


def _ensure_dirs():
    os.makedirs(JOBS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)


def _get_backup_files() -> List[str]:
    """Get list of backup files sorted by modification time (newest first)."""
    backups = []
    for i in range(1, JOBS_BACKUP_COUNT + 1):
        backup_path = f"{JOBS_FILE}.bak.{i}"
        if os.path.exists(backup_path):
            backups.append((os.path.getmtime(backup_path), backup_path))
    # Sort by mtime descending (newest first)
    backups.sort(reverse=True)
    return [path for _, path in backups]


def _rotate_backups():
    """Rotate backup files, keeping only JOBS_BACKUP_COUNT backups."""
    # Shift existing backups: .bak.2 -> .bak.3, .bak.1 -> .bak.2
    for i in range(JOBS_BACKUP_COUNT, 1, -1):
        src = f"{JOBS_FILE}.bak.{i - 1}"
        dst = f"{JOBS_FILE}.bak.{i}"
        if os.path.exists(src):
            try:
                shutil.move(src, dst)
            except Exception:
                pass

    # Create new .bak.1 from current jobs.json
    if os.path.exists(JOBS_FILE):
        try:
            shutil.copy2(JOBS_FILE, f"{JOBS_FILE}.bak.1")
        except Exception:
            pass


def _recover_from_backup() -> List[Dict[str, Any]]:
    """
    Attempt to recover jobs from backup files.

    Returns:
        List of jobs from the first valid backup, or empty list if no valid backup found
    """
    backups = _get_backup_files()
    for backup_path in backups:
        try:
            with open(backup_path, "r", encoding="utf-8") as fh:
                jobs = json.load(fh)
            if isinstance(jobs, list):
                _append_worker_log(
                    f"recovered {len(jobs)} jobs from backup: {backup_path}"
                )
                logger.info(
                    "Jobs recovered from backup",
                    extra={"backup_path": backup_path, "job_count": len(jobs)},
                )
                return jobs
        except Exception as e:
            _append_worker_log(f"backup {backup_path} also corrupt: {e}")
            continue
    return []


def _read_jobs() -> List[Dict[str, Any]]:
    """
    Read jobs from jobs.json with cross-process file locking.

    The file lock ensures we don't read while another process is writing,
    preventing partially-written files from being read.
    """
    _ensure_dirs()
    if not os.path.exists(JOBS_FILE):
        return []
    try:
        with _jobs_lock():
            with open(JOBS_FILE, "r", encoding="utf-8") as fh:
                return json.load(fh)
    except TimeoutError:
        # Lock acquisition timed out - log and try without lock
        _append_worker_log("jobs.json lock timeout on read, reading anyway")
        try:
            with open(JOBS_FILE, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return []
    except Exception as e:
        # Log corruption event
        _append_worker_log(f"jobs.json corrupt: {e}")
        logger.error(
            "Jobs file corrupted", extra={"error": str(e), "jobs_file": JOBS_FILE}
        )

        # Try to recover from backup
        recovered_jobs = _recover_from_backup()

        # Move corrupt file aside
        try:
            corrupt = JOBS_FILE + ".corrupt." + str(int(time.time()))
            shutil.move(JOBS_FILE, corrupt)
            _append_worker_log(f"corrupt jobs file moved to {corrupt}")
        except Exception:
            pass

        # If we recovered jobs, write them back
        if recovered_jobs:
            try:
                _write_jobs_unlocked(recovered_jobs)
                _append_worker_log(f"restored {len(recovered_jobs)} jobs from backup")
            except Exception as write_err:
                _append_worker_log(f"failed to restore jobs: {write_err}")

        return recovered_jobs


def _read_jobs_unlocked() -> List[Dict[str, Any]]:
    """Read jobs without acquiring file lock (for internal use when lock already held)."""
    if not os.path.exists(JOBS_FILE):
        return []
    try:
        with open(JOBS_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return []


def _write_jobs_unlocked(jobs: List[Dict[str, Any]]):
    """Write jobs without acquiring file lock (for internal use when lock already held)."""
    _ensure_dirs()

    # Rotate backups before writing (keeps last 3 good copies)
    _rotate_backups()

    tmp = tempfile.NamedTemporaryFile("w", delete=False, dir=JOBS_DIR, encoding="utf-8")
    try:
        json.dump(jobs, tmp, indent=2, ensure_ascii=False)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()
        os.replace(tmp.name, JOBS_FILE)
    finally:
        if os.path.exists(tmp.name):
            try:
                os.unlink(tmp.name)
            except Exception:
                pass


def _write_jobs(jobs: List[Dict[str, Any]]):
    """
    Write jobs to jobs.json with cross-process file locking.

    The file lock ensures we don't write while another process is reading
    or writing, preventing race conditions.
    """
    _ensure_dirs()

    try:
        with _jobs_lock():
            _write_jobs_unlocked(jobs)
    except TimeoutError:
        # Lock acquisition timed out - log and write anyway (better than losing data)
        _append_worker_log("jobs.json lock timeout on write, writing anyway")
        _write_jobs_unlocked(jobs)


def _append_worker_log(msg: str):
    _ensure_dirs()
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    line = f"{ts} {msg}\n"
    with open(WORKER_LOG, "a", encoding="utf-8", errors="replace") as fh:
        fh.write(line)


def _update_heartbeat():
    """Write current timestamp to heartbeat file for health monitoring."""
    _ensure_dirs()
    try:
        with open(HEARTBEAT_FILE, "w") as fh:
            fh.write(str(time.time()))
    except Exception:
        pass  # Non-critical, don't crash worker


def get_heartbeat_age() -> Optional[float]:
    """
    Get age of worker heartbeat in seconds.

    Returns:
        Age in seconds, or None if heartbeat file doesn't exist
    """
    try:
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE, "r") as fh:
                last_beat = float(fh.read().strip())
            return time.time() - last_beat
        return None
    except Exception:
        return None


def is_heartbeat_stale() -> bool:
    """Check if worker heartbeat is stale (older than threshold)."""
    age = get_heartbeat_age()
    if age is None:
        return True  # No heartbeat = stale
    return age > HEARTBEAT_STALE_THRESHOLD


def _get_process_start_time(pid: int) -> Optional[float]:
    """
    Get process start time from /proc filesystem (Linux only).

    Returns:
        Process start time as Unix timestamp, or None if not available
    """
    try:
        stat_path = f"/proc/{pid}/stat"
        if not os.path.exists(stat_path):
            return None

        with open(stat_path, "r") as f:
            stat = f.read()

        # Parse stat file - field 22 is starttime (in clock ticks since boot)
        # Format: pid (comm) state ppid pgrp session tty_nr ... starttime ...
        # Need to handle comm field which may contain spaces/parentheses
        parts = stat.rsplit(")", 1)
        if len(parts) < 2:
            return None

        fields = parts[1].split()
        if len(fields) < 20:
            return None

        starttime_ticks = int(
            fields[19]
        )  # 0-indexed, field 22 is at index 19 after comm

        # Convert to timestamp using system boot time and clock ticks per second
        with open("/proc/stat", "r") as f:
            for line in f:
                if line.startswith("btime"):
                    boot_time = int(line.split()[1])
                    break
            else:
                return None

        # Get clock ticks per second (usually 100)
        ticks_per_sec = os.sysconf(os.sysconf_names["SC_CLK_TCK"])

        return boot_time + (starttime_ticks / ticks_per_sec)
    except Exception:
        return None


def _next_job_id(jobs: List[Dict[str, Any]]) -> int:
    """
    Get next available job ID with file locking.

    Uses a persistent counter with fcntl locking to ensure IDs are never
    reused, even across multiple processes. This prevents duplicate job IDs
    when multiple jobs are enqueued concurrently.
    """
    counter_file = os.path.join(JOBS_DIR, ".job_counter")
    lock_file = os.path.join(JOBS_DIR, ".job_counter.lock")

    try:
        _ensure_dirs()

        # Use a separate lock file to allow atomic read-modify-write
        with open(lock_file, "w") as lock_fh:
            # Acquire exclusive lock (blocks until available)
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)

            try:
                # Read current counter
                if os.path.exists(counter_file):
                    with open(counter_file, "r") as f:
                        next_id = int(f.read().strip())
                else:
                    # Initialize from existing jobs
                    maxid = 0
                    for j in jobs:
                        try:
                            if isinstance(j.get("id"), int) and j["id"] > maxid:
                                maxid = j["id"]
                        except Exception:
                            continue
                    next_id = maxid + 1

                # Write incremented counter atomically
                tmp_file = counter_file + ".tmp"
                with open(tmp_file, "w") as f:
                    f.write(str(next_id + 1))
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_file, counter_file)

                return next_id

            finally:
                # Release lock
                fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)

    except Exception:
        # Fallback to old behavior if file operations fail
        maxid = 0
        for j in jobs:
            try:
                if isinstance(j.get("id"), int) and j["id"] > maxid:
                    maxid = j["id"]
            except Exception:
                continue
        return maxid + 1


def enqueue_job(
    tool: str,
    target: str,
    args: List[str],
    label: str = "",
    engagement_id: int = None,
    metadata: Dict[str, Any] = None,
    parent_id: int = None,
    reason: str = None,
    rule_id: int = None,
    skip_scope_check: bool = False,
) -> int:
    # Prepare data outside lock to minimize lock hold time
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Get current engagement if not specified
    if engagement_id is None:
        try:
            from souleyez.storage.engagements import EngagementManager

            em = EngagementManager()
            current = em.get_current()
            engagement_id = current["id"] if current else None
        except BaseException:
            engagement_id = None

    # Merge parent_id, reason, and rule_id into metadata
    job_metadata = metadata or {}
    if parent_id is not None:
        job_metadata["parent_id"] = parent_id
    if reason:
        job_metadata["reason"] = reason
    if rule_id is not None:
        job_metadata["rule_id"] = rule_id

    # Atomic read-modify-write with both thread lock and cross-process file lock
    with _lock:  # Thread safety within this process
        try:
            with _jobs_lock():  # Cross-process safety
                _ensure_dirs()
                jobs = _read_jobs_unlocked()
                jid = _next_job_id(jobs)

                # Scope validation - check if target is within engagement scope
                # Done inside lock because it uses jid for logging
                if not skip_scope_check and engagement_id:
                    try:
                        from souleyez.security.scope_validator import (
                            ScopeValidator,
                            ScopeViolationError,
                        )

                        validator = ScopeValidator(engagement_id)
                        result = validator.validate_target(target)
                        enforcement = validator.get_enforcement_mode()

                        if not result.is_in_scope and validator.has_scope_defined():
                            if enforcement == "block":
                                validator.log_validation(
                                    target, result, "blocked", job_id=jid
                                )
                                raise ScopeViolationError(
                                    f"Target '{target}' is out of scope. {result.reason}"
                                )
                            elif enforcement == "warn":
                                validator.log_validation(
                                    target, result, "warned", job_id=jid
                                )
                                if "warnings" not in job_metadata:
                                    job_metadata["warnings"] = []
                                job_metadata["warnings"].append(
                                    f"SCOPE WARNING: {target} may be out of scope. {result.reason}"
                                )
                                logger.warning(
                                    "Out-of-scope target allowed (warn mode)",
                                    extra={
                                        "target": target,
                                        "engagement_id": engagement_id,
                                        "reason": result.reason,
                                    },
                                )
                        else:
                            validator.log_validation(
                                target, result, "allowed", job_id=jid
                            )
                    except ScopeViolationError:
                        raise  # Re-raise scope violations
                    except Exception as e:
                        # Don't block jobs if scope validation fails unexpectedly
                        logger.warning(
                            "Scope validation error (allowing job)",
                            extra={"target": target, "error": str(e)},
                        )

                job = {
                    "id": jid,
                    "tool": tool,
                    "target": target,
                    "args": args or [],
                    "label": label or "",
                    "status": STATUS_QUEUED,
                    "created_at": now,
                    "started_at": None,
                    "finished_at": None,
                    "result_scan_id": None,
                    "error": None,
                    "log": os.path.join(JOBS_DIR, f"{jid}.log"),
                    "pid": None,
                    "engagement_id": engagement_id,
                    "chainable": False,
                    "chained": False,
                    "chained_job_ids": [],
                    "chain_error": None,
                    "metadata": job_metadata,
                    "parent_id": parent_id,  # Top-level field for easier querying
                    "rule_id": rule_id,  # Rule that triggered this job (if auto-chained)
                }
                jobs.append(job)
                _write_jobs_unlocked(jobs)
        except TimeoutError:
            # Lock acquisition timed out - fall back to non-locked operation
            _append_worker_log("jobs.json lock timeout in enqueue_job, using fallback")
            jobs = _read_jobs()
            jid = _next_job_id(jobs)

            # Scope validation fallback
            if not skip_scope_check and engagement_id:
                try:
                    from souleyez.security.scope_validator import (
                        ScopeValidator,
                        ScopeViolationError,
                    )

                    validator = ScopeValidator(engagement_id)
                    result = validator.validate_target(target)
                    enforcement = validator.get_enforcement_mode()

                    if not result.is_in_scope and validator.has_scope_defined():
                        if enforcement == "block":
                            validator.log_validation(
                                target, result, "blocked", job_id=jid
                            )
                            raise ScopeViolationError(
                                f"Target '{target}' is out of scope. {result.reason}"
                            )
                        elif enforcement == "warn":
                            validator.log_validation(
                                target, result, "warned", job_id=jid
                            )
                            if "warnings" not in job_metadata:
                                job_metadata["warnings"] = []
                            job_metadata["warnings"].append(
                                f"SCOPE WARNING: {target} may be out of scope. {result.reason}"
                            )
                    else:
                        validator.log_validation(target, result, "allowed", job_id=jid)
                except ScopeViolationError:
                    raise
                except Exception:
                    pass

            job = {
                "id": jid,
                "tool": tool,
                "target": target,
                "args": args or [],
                "label": label or "",
                "status": STATUS_QUEUED,
                "created_at": now,
                "started_at": None,
                "finished_at": None,
                "result_scan_id": None,
                "error": None,
                "log": os.path.join(JOBS_DIR, f"{jid}.log"),
                "pid": None,
                "engagement_id": engagement_id,
                "chainable": False,
                "chained": False,
                "chained_job_ids": [],
                "chain_error": None,
                "metadata": job_metadata,
                "parent_id": parent_id,
                "rule_id": rule_id,
            }
            jobs.append(job)
            _write_jobs(jobs)

    logger.info(
        "Job enqueued",
        extra={
            "event_type": "job_enqueued",
            "job_id": jid,
            "tool": tool,
            "target": target,
            "engagement_id": engagement_id,
            "label": label,
        },
    )
    _append_worker_log(f"enqueued job {jid}: {tool} {target}")
    return jid


def list_jobs(limit: int = 100) -> List[Dict[str, Any]]:
    jobs = _read_jobs()
    # Sort by job ID descending (newest first) so limit cuts old jobs, not new ones
    return sorted(jobs, key=lambda x: x.get("id", 0), reverse=True)[:limit]


def get_active_jobs() -> List[Dict[str, Any]]:
    """Get all running/pending/queued jobs without limit.

    Returns jobs sorted with running jobs first, then by ID descending.
    """
    jobs = _read_jobs()
    active = [j for j in jobs if j.get("status") in ("pending", "running", "queued")]

    # Sort: running jobs first, then by ID descending (newest first)
    def sort_key(j):
        status = j.get("status", "")
        status_priority = 0 if status == "running" else 1
        job_id = j.get("id", 0)
        return (status_priority, -job_id)

    return sorted(active, key=sort_key)


def get_all_jobs() -> List[Dict[str, Any]]:
    """Get ALL jobs without any limit.

    Returns jobs sorted by ID descending (newest first).
    """
    jobs = _read_jobs()
    return sorted(jobs, key=lambda x: x.get("id", 0), reverse=True)


def get_job(jid: int) -> Optional[Dict[str, Any]]:
    jobs = _read_jobs()
    for j in jobs:
        if j.get("id") == jid:
            return j
    return None


def kill_job(jid: int) -> bool:
    """
    Kill a job by removing it from queue or sending SIGTERM to its process.

    Args:
        jid: Job ID to kill

    Returns:
        True if job was killed/removed, False if not found
    """
    job = get_job(jid)
    if not job:
        return False

    status = job.get("status")
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Handle queued jobs - just mark as killed
    if status == STATUS_QUEUED:
        _update_job(jid, status=STATUS_KILLED, finished_at=now)
        _append_worker_log(f"job {jid}: removed from queue")
        return True

    # Handle terminal statuses (done, no_results, warning, error) - mark as killed
    if status in [STATUS_DONE, STATUS_NO_RESULTS, STATUS_WARNING, STATUS_ERROR]:
        _update_job(jid, status=STATUS_KILLED, finished_at=now)
        _append_worker_log(f"job {jid}: marked as killed")
        return True

    # Handle running jobs - send signal
    if status == STATUS_RUNNING:
        pid = job.get("pid")
        if not pid:
            _update_job(jid, status=STATUS_KILLED, finished_at=now)
            return True

        try:
            import signal

            # Get process group ID
            try:
                pgid = os.getpgid(pid)
            except ProcessLookupError:
                # Process already dead
                _update_job(jid, status=STATUS_KILLED, finished_at=now, pid=None)
                _append_worker_log(f"job {jid}: process already dead, marked as killed")
                return True

            # Kill entire process group (parent + all children)
            try:
                os.killpg(pgid, signal.SIGTERM)
                _append_worker_log(f"job {jid}: sent SIGTERM to process group {pgid}")
            except ProcessLookupError:
                # Process group already dead
                _update_job(jid, status=STATUS_KILLED, finished_at=now, pid=None)
                _append_worker_log(
                    f"job {jid}: process group already dead, marked as killed"
                )
                return True
            except PermissionError:
                _append_worker_log(
                    f"job {jid}: permission denied to kill process group {pgid}"
                )
                return False

            # Wait briefly for graceful termination
            time.sleep(1)

            # Check if still alive, force kill with SIGKILL
            try:
                os.getpgid(pgid)  # Throws if group doesn't exist
                os.killpg(pgid, signal.SIGKILL)
                _append_worker_log(f"job {jid}: sent SIGKILL to process group {pgid}")
            except ProcessLookupError:
                pass  # Already dead, good

            # Update job status
            _update_job(jid, status=STATUS_KILLED, finished_at=now, pid=None)
            _append_worker_log(f"job {jid}: killed successfully")
            return True
        except ProcessLookupError:
            # Process already dead
            _update_job(jid, status=STATUS_KILLED, finished_at=now, pid=None)
            _append_worker_log(f"job {jid}: process already dead, marked as killed")
            return True
        except PermissionError:
            _append_worker_log(f"job {jid}: permission denied to kill PID {pid}")
            return False
        except Exception as e:
            _append_worker_log(f"job {jid}: error killing process: {e}")
            return False

    # Job is in some other state (done, killed, etc.)
    _append_worker_log(f"job {jid}: cannot kill - status is '{status}'")
    return False


def delete_job(jid: int) -> bool:
    """
    Delete a job from the queue (completed jobs only).

    Uses atomic read-modify-write with cross-process file locking.

    Args:
        jid: Job ID to delete

    Returns:
        True if job was deleted, False if not found or still running
    """
    with _lock:  # Thread safety within this process
        try:
            with _jobs_lock():  # Cross-process safety
                jobs = _read_jobs_unlocked()
                job = None
                for j in jobs:
                    if j.get("id") == jid:
                        job = j
                        break

                if not job:
                    return False

                # Don't delete running or pending jobs
                if job.get("status") in ("running", "pending"):
                    return False

                jobs = [j for j in jobs if j.get("id") != jid]
                _write_jobs_unlocked(jobs)
                return True
        except TimeoutError:
            # Fall back to non-locked operation
            _append_worker_log(
                f"jobs.json lock timeout in delete_job for {jid}, using fallback"
            )
            jobs = _read_jobs()
            job = None
            for j in jobs:
                if j.get("id") == jid:
                    job = j
                    break

            if not job:
                return False

            if job.get("status") in ("running", "pending"):
                return False

            jobs = [j for j in jobs if j.get("id") != jid]
            _write_jobs(jobs)
            return True


def purge_jobs(status_filter: List[str] = None, engagement_id: int = None) -> int:
    """
    Purge multiple jobs at once based on filters.

    Uses atomic read-modify-write with cross-process file locking.

    Args:
        status_filter: List of statuses to purge (e.g., ['done', 'error', 'killed'])
                      If None, purges all non-running jobs
        engagement_id: Only purge jobs from this engagement (if provided)

    Returns:
        Number of jobs purged
    """
    if status_filter is None:
        status_filter = ["done", "error", "killed"]

    def _filter_jobs(jobs):
        """Filter out jobs to keep based on criteria."""
        kept_jobs = []
        for j in jobs:
            # Keep running/pending jobs always
            if j.get("status") in ("running", "pending"):
                kept_jobs.append(j)
                continue

            # Keep if status doesn't match filter
            if j.get("status") not in status_filter:
                kept_jobs.append(j)
                continue

            # Keep if engagement_id specified and doesn't match
            if engagement_id is not None and j.get("engagement_id") != engagement_id:
                kept_jobs.append(j)
                continue

            # Otherwise, purge this job (don't add to kept_jobs)
        return kept_jobs

    with _lock:  # Thread safety within this process
        try:
            with _jobs_lock():  # Cross-process safety
                jobs = _read_jobs_unlocked()
                original_count = len(jobs)
                kept_jobs = _filter_jobs(jobs)
                _write_jobs_unlocked(kept_jobs)
                return original_count - len(kept_jobs)
        except TimeoutError:
            # Fall back to non-locked operation
            _append_worker_log("jobs.json lock timeout in purge_jobs, using fallback")
            jobs = _read_jobs()
            original_count = len(jobs)
            kept_jobs = _filter_jobs(jobs)
            _write_jobs(kept_jobs)
            return original_count - len(kept_jobs)


def purge_all_jobs() -> int:
    """
    Purge ALL completed jobs (done, error, killed).
    WARNING: This cannot be undone!

    Returns:
        Number of jobs purged
    """
    return purge_jobs(status_filter=["done", "error", "killed"])


def _update_job(jid: int, respect_killed: bool = True, **fields):
    """
    Update job fields atomically with cross-process locking.

    Uses both threading lock (for same-process safety) and file lock
    (for cross-process safety) to ensure atomic read-modify-write.

    Args:
        jid: Job ID to update
        respect_killed: If True (default), don't overwrite status if job is killed.
                       This prevents race condition where job is killed while completing.
        **fields: Fields to update
    """
    with _lock:  # Thread safety within this process
        try:
            with _jobs_lock():  # Cross-process safety
                # Read directly without going through _read_jobs (we already have lock)
                _ensure_dirs()
                jobs = []
                if os.path.exists(JOBS_FILE):
                    try:
                        with open(JOBS_FILE, "r", encoding="utf-8") as fh:
                            jobs = json.load(fh)
                    except Exception:
                        jobs = []

                changed = False
                for j in jobs:
                    if j.get("id") == jid:
                        # Race condition protection: don't change status of killed jobs
                        if (
                            respect_killed
                            and j.get("status") == STATUS_KILLED
                            and "status" in fields
                        ):
                            # Job was killed - don't overwrite status, but allow other updates
                            fields_copy = dict(fields)
                            del fields_copy["status"]
                            if fields_copy:
                                j.update(fields_copy)
                                changed = True
                            logger.debug(
                                "Skipped status update for killed job",
                                extra={
                                    "job_id": jid,
                                    "attempted_status": fields.get("status"),
                                },
                            )
                        else:
                            j.update(fields)
                            changed = True
                        break

                if changed:
                    # Write directly without going through _write_jobs (we already have lock)
                    _write_jobs_unlocked(jobs)
        except TimeoutError:
            # Fall back to non-locked operation (better than failing)
            _append_worker_log(
                f"jobs.json lock timeout updating job {jid}, using fallback"
            )
            jobs = _read_jobs()
            changed = False
            for j in jobs:
                if j.get("id") == jid:
                    j.update(fields)
                    changed = True
                    break
            if changed:
                _write_jobs(jobs)


def _process_pending_chains():
    """
    Process ONE chainable job and trigger auto-chaining.

    Called by worker loop every 5 seconds. Only processes one job
    at a time to avoid database conflicts and race conditions.

    Job lifecycle:
    - chainable=False, chained=False → Not ready for chaining
    - chainable=True, chained=False  → Ready to process (we handle this)
    - chainable=True, chained=True   → Already processed (skip)

    Returns:
        int: Number of jobs processed (0 or 1)
    """
    try:
        jobs = _read_jobs()

        # Cleanup: Mark jobs stuck in "chaining in progress" for too long (> 5 min) as failed
        CHAIN_TIMEOUT_SECONDS = 300  # 5 minutes
        now = datetime.now(timezone.utc)
        for j in jobs:
            chaining_started = j.get("chaining_started_at")
            if chaining_started and not j.get("chained", False):
                try:
                    started_at = datetime.fromisoformat(
                        chaining_started.replace("Z", "+00:00")
                    )
                    if (now - started_at).total_seconds() > CHAIN_TIMEOUT_SECONDS:
                        jid = j.get("id")
                        _append_worker_log(
                            f"job {jid}: chaining timed out after {CHAIN_TIMEOUT_SECONDS}s, marking as failed"
                        )
                        _update_job(
                            jid,
                            chained=True,
                            chain_error="Chaining timed out",
                            chaining_started_at=None,
                        )
                except Exception:
                    pass  # Ignore parse errors

        # Find jobs ready for chaining
        # Include jobs with chainable statuses: done, no_results, warning
        # Skip jobs that are currently being chained (chaining_started_at is set)
        chainable_jobs = [
            j
            for j in jobs
            if j.get("chainable", False) == True
            and j.get("chained", False) == False
            and is_chainable(j.get("status", ""))
            and not j.get("chaining_started_at")  # Skip if already being processed
        ]

        if not chainable_jobs:
            return 0  # Nothing to process

        # Sort by created_at (process oldest first - FIFO)
        chainable_jobs.sort(key=lambda x: x.get("created_at", ""))
        job_to_chain = chainable_jobs[0]

        jid = job_to_chain["id"]
        tool = job_to_chain.get("tool", "unknown")

        _append_worker_log(f"processing chains for job {jid} ({tool})")
        logger.info(
            "Processing chainable job",
            extra={"job_id": jid, "tool": tool, "queue_depth": len(chainable_jobs)},
        )

        # Mark job as chaining in progress BEFORE starting (prevents retry loop if auto_chain hangs)
        chaining_start = datetime.now(timezone.utc).isoformat()
        _update_job(jid, chaining_started_at=chaining_start)

        try:
            from souleyez.core.tool_chaining import ToolChaining

            chaining = ToolChaining()

            if not chaining.is_enabled():
                # Chaining was disabled after job marked as chainable
                _update_job(jid, chained=True, chaining_started_at=None)
                _append_worker_log(f"job {jid}: chaining now disabled, skipping")
                return 1

            # Get parse results from job
            parse_result = job_to_chain.get("parse_result", {})

            if not parse_result:
                # No parse results - this shouldn't happen if job was properly marked chainable
                # Log warning and store reason for debugging
                logger.warning(
                    "Job marked chainable but has no parse_result",
                    extra={
                        "job_id": jid,
                        "tool": tool,
                        "status": job_to_chain.get("status"),
                    },
                )
                _append_worker_log(
                    f"job {jid}: WARNING - marked chainable but parse_result is empty/missing"
                )
                _update_job(
                    jid,
                    chained=True,
                    chain_skip_reason="parse_result missing",
                    chaining_started_at=None,
                )
                return 1

            if "error" in parse_result:
                # Parse had an error - log and skip
                logger.warning(
                    "Job has parse error, skipping chaining",
                    extra={
                        "job_id": jid,
                        "tool": tool,
                        "parse_error": parse_result.get("error"),
                    },
                )
                _append_worker_log(
                    f"job {jid}: parse error '{parse_result.get('error')}', skipping chain"
                )
                _update_job(
                    jid,
                    chained=True,
                    chain_skip_reason=f"parse_error: {parse_result.get('error')}",
                    chaining_started_at=None,
                )
                return 1

            # Process auto-chaining
            chained_job_ids = chaining.auto_chain(job_to_chain, parse_result)

            # Update job with chaining results (clear chaining_started_at)
            _update_job(
                jid,
                chained=True,
                chained_job_ids=chained_job_ids or [],
                chaining_started_at=None,
            )

            if chained_job_ids:
                logger.info(
                    "Auto-chaining completed",
                    extra={
                        "job_id": jid,
                        "chained_jobs": chained_job_ids,
                        "count": len(chained_job_ids),
                    },
                )
                _append_worker_log(
                    f"job {jid}: created {len(chained_job_ids)} chained job(s): {chained_job_ids}"
                )
            else:
                _append_worker_log(f"job {jid}: no follow-up jobs triggered")

            return 1  # Processed one job

        except Exception as chain_err:
            # Chaining failed - mark as chained with error to prevent retry loops
            error_msg = str(chain_err)
            logger.error(
                "Auto-chaining failed",
                extra={
                    "job_id": jid,
                    "error": error_msg,
                    "traceback": traceback.format_exc(),
                },
            )
            _append_worker_log(f"job {jid} chain error: {error_msg}")
            _update_job(
                jid, chained=True, chain_error=error_msg, chaining_started_at=None
            )
            return 1  # Still count as processed (with error)

    except Exception as e:
        # Unexpected error in chain processor itself
        logger.error(
            "Chain processor error",
            extra={"error": str(e), "traceback": traceback.format_exc()},
        )
        _append_worker_log(f"chain processor error: {e}")
        return 0


def _try_run_plugin(
    tool: str, target: str, args: List[str], label: str, log_path: str, jid: int = None
) -> tuple:
    try:
        from .loader import discover_plugins

        plugins = discover_plugins()
        plugin = None

        plugin = plugins.get(tool.lower())

        if not plugin:
            for key, p in plugins.items():
                try:
                    plugin_tool = getattr(p, "tool", "").lower()
                    plugin_name = getattr(p, "name", "").lower()
                    if tool.lower() in (plugin_tool, plugin_name):
                        plugin = p
                        break
                except Exception:
                    continue

        if not plugin:
            return (False, 0)

        # NEW: Check for build_command() first (preferred method)
        build_command_method = getattr(plugin, "build_command", None)
        if callable(build_command_method):
            try:
                with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
                    fh.write(f"=== Plugin: {getattr(plugin, 'name', tool)} ===\n")
                    fh.write(f"Target: {target}\n")
                    fh.write(f"Args: {args}\n")
                    fh.write(f"Label: {label}\n")
                    fh.write(
                        f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
                    )

                # Build command specification
                cmd_spec = build_command_method(
                    target, args or [], label or "", log_path
                )

                if cmd_spec is None:
                    # build_command returned None - check if this is a deliberate abort
                    # (e.g., gobuster detected host redirect and aborted to avoid wasted scan)
                    if os.path.exists(log_path):
                        with open(
                            log_path, "r", encoding="utf-8", errors="replace"
                        ) as fh:
                            log_content = fh.read()
                            if "HOST_REDIRECT_TARGET:" in log_content:
                                # Plugin aborted due to host redirect - don't fall through to run()
                                # Return success (0) so parser can set WARNING status and trigger retry
                                _append_worker_log(
                                    f"job {jid}: gobuster aborted due to host redirect"
                                )
                                return (True, 0)

                    # Otherwise check if plugin has run() method
                    # This allows plugins to signal "use run() instead" by returning None
                    run_method = getattr(plugin, "run", None)
                    if callable(run_method):
                        # Plugin wants to handle execution itself via run() method
                        sig = inspect.signature(run_method)
                        params = list(sig.parameters.keys())

                        try:
                            if "log_path" in params:
                                rc = run_method(
                                    target, args or [], label or "", log_path
                                )
                            elif "label" in params:
                                rc = run_method(target, args or [], label or "")
                            elif "args" in params:
                                rc = run_method(target, args or [])
                            else:
                                rc = run_method(target)
                            return (True, rc if isinstance(rc, int) else 0)
                        except Exception as e:
                            with open(
                                log_path, "a", encoding="utf-8", errors="replace"
                            ) as fh:
                                fh.write(f"\n=== PLUGIN RUN ERROR ===\n")
                                fh.write(f"{type(e).__name__}: {e}\n")
                                fh.write(f"\n{traceback.format_exc()}\n")
                            return (True, 1)
                    else:
                        # No run() method either - actual validation failure
                        with open(
                            log_path, "a", encoding="utf-8", errors="replace"
                        ) as fh:
                            fh.write(
                                "ERROR: Plugin validation failed (build_command returned None)\n"
                            )
                        return (True, 1)

                # Execute using new subprocess handler with PID tracking
                rc = _run_subprocess_with_spec(
                    cmd_spec, log_path, jid=jid, plugin=plugin
                )

                # Completion message already written by _run_subprocess_with_spec
                return (True, rc)

            except Exception as e:
                with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                    fh.write("\n=== PLUGIN ERROR ===\n")
                    fh.write(f"{type(e).__name__}: {e}\n")
                    fh.write(f"\n{traceback.format_exc()}\n")
                return (True, 1)

        # FALLBACK: Use old run() method for backward compatibility
        run_method = getattr(plugin, "run", None)
        if not callable(run_method):
            return (False, 0)

        sig = inspect.signature(run_method)
        params = list(sig.parameters.keys())

        with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
            fh.write(f"=== Plugin: {getattr(plugin, 'name', tool)} ===\n")
            fh.write(f"Target: {target}\n")
            fh.write(f"Args: {args}\n")
            fh.write(f"Label: {label}\n")
            fh.write(
                f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
            )

        try:
            if "log_path" in params or len(params) >= 4:
                rc = run_method(target, args or [], label or "", log_path)
            else:
                result = run_method(target, args or [], label or "")

                if isinstance(result, tuple) and len(result) >= 2:
                    rc, old_logpath = result[0], result[1]
                    if (
                        old_logpath
                        and os.path.exists(old_logpath)
                        and old_logpath != log_path
                    ):
                        try:
                            with open(
                                old_logpath, "r", encoding="utf-8", errors="replace"
                            ) as src:
                                with open(
                                    log_path, "a", encoding="utf-8", errors="replace"
                                ) as dst:
                                    dst.write("\n=== Plugin Output ===\n")
                                    dst.write(src.read())
                        except Exception as e:
                            with open(
                                log_path, "a", encoding="utf-8", errors="replace"
                            ) as fh:
                                fh.write(f"\nWarning: Could not copy old log: {e}\n")
                elif isinstance(result, int):
                    rc = result
                else:
                    rc = 0

            if not isinstance(rc, int):
                rc = 0 if rc is None else 1

            # Completion message already written by plugin run() method
            return (True, rc)

        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write("\n=== PLUGIN ERROR ===\n")
                fh.write(f"{type(e).__name__}: {e}\n")
            return (True, 1)

    except Exception as e:
        _append_worker_log(f"plugin loading error: {e}")
        return (False, 0)


def _run_rpc_exploit(
    cmd_spec: Dict[str, Any], log_path: str, jid: int = None, plugin=None
) -> int:
    """
    Execute MSF exploit via RPC mode (Pro feature).

    This function:
    1. Uses msfrpcd to execute the exploit
    2. Polls for session creation
    3. Stores session in database on success
    4. Updates job with session info

    Args:
        cmd_spec: RPC command specification with:
            - exploit_path: str - MSF exploit module path
            - target: str - Target IP/hostname
            - options: Dict - Exploit options
            - payload: str - Payload to use (optional)
        log_path: Path to write logs
        jid: Job ID for tracking
        plugin: Plugin instance

    Returns:
        Exit code (0 = success with session, non-zero = failure)
    """
    exploit_path = cmd_spec.get("exploit_path")
    target = cmd_spec.get("target")
    options = cmd_spec.get("options", {})
    payload = cmd_spec.get("payload")

    _append_worker_log(f"job {jid}: RPC mode exploit - {exploit_path}")

    # Get or create plugin instance
    if plugin is None:
        try:
            from souleyez.plugins.msf_exploit import MsfExploitPlugin

            plugin = MsfExploitPlugin()
        except Exception as e:
            with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"ERROR: Could not load msf_exploit plugin: {e}\n")
            return 1

    # Execute via RPC
    result = plugin.run_rpc_exploit(
        exploit_path=exploit_path,
        target=target,
        options=options,
        log_path=log_path,
        payload=payload,
    )

    if result.get("success"):
        session_id = result.get("session_id")
        session_info = result.get("session_info", {})

        # Store session in database
        try:
            _store_msf_session(jid, target, exploit_path, session_id, session_info)
        except Exception as e:
            _append_worker_log(f"job {jid}: failed to store session: {e}")

        # Update job with session info
        session_type = session_info.get("type", "shell")
        _update_job(
            jid,
            exploitation_detected=True,
            session_info=f"Session {session_id} ({session_type})",
        )

        return 0
    elif result.get("no_session"):
        # Exploit ran but no session opened - this is "no results", not an error
        # Return 1 but let parser set status to no_results
        reason = result.get("reason", "No session opened")
        _append_worker_log(f"job {jid}: exploit completed - {reason}")
        return 1
    else:
        # True error (connection failed, RPC error, etc.)
        error = result.get("error", "Unknown error")
        _append_worker_log(f"job {jid}: RPC exploit failed - {error}")
        return 1


def _store_msf_session(
    jid: int,
    target: str,
    exploit_path: str,
    session_id: str,
    session_info: Dict[str, Any],
):
    """Store MSF session in database."""
    try:
        from souleyez.storage.database import get_db
        from souleyez.storage.hosts import HostManager
        from souleyez.storage.msf_sessions import add_msf_session

        # Get job info for engagement_id
        job = get_job(jid)
        if not job:
            return

        engagement_id = job.get("engagement_id")
        if not engagement_id:
            return

        # Get or create host
        db = get_db()
        conn = db.get_connection()

        hm = HostManager()
        host = hm.get_host_by_ip(engagement_id, target)
        host_id = host["id"] if host else None

        if host_id:
            add_msf_session(
                conn,
                engagement_id=engagement_id,
                host_id=host_id,
                msf_session_id=int(session_id),
                session_type=session_info.get("type"),
                via_exploit=exploit_path,
                via_payload=session_info.get("via_payload"),
                platform=session_info.get("platform"),
                arch=session_info.get("arch"),
                username=session_info.get("username"),
                port=session_info.get("target_port"),
                tunnel_peer=session_info.get("tunnel_peer"),
                notes=f"Created by job #{jid}",
            )
            conn.commit()

        conn.close()
        _append_worker_log(f"job {jid}: stored session {session_id} in database")

    except Exception as e:
        _append_worker_log(f"job {jid}: session storage error: {e}")


# Cache stdbuf availability check
_stdbuf_available = None


def _is_stdbuf_available() -> bool:
    """Check if stdbuf is available for line-buffered output."""
    global _stdbuf_available
    if _stdbuf_available is None:
        _stdbuf_available = shutil.which("stdbuf") is not None
    return _stdbuf_available


def _is_python_tool(cmd: List[str]) -> bool:
    """
    Check if a command is a Python-based tool.

    stdbuf doesn't work well with Python scripts because Python manages its own
    buffering internally. On some systems (especially ARM), stdbuf can prevent
    Python tools from producing any output at all.

    Args:
        cmd: Command array to check

    Returns:
        True if the command is a Python tool that should skip stdbuf
    """
    if not cmd:
        return False

    executable = cmd[0]

    # Direct Python invocation
    if executable in ("python", "python3") or executable.startswith("python"):
        return True

    # .py extension
    if executable.endswith(".py"):
        return True

    # Known Python tools that don't work with stdbuf
    # These are tools installed via pip/pipx that are Python scripts
    python_tools = {
        "netexec",
        "nxc",
        "crackmapexec",
        "cme",
        "smbmap",
        "impacket-GetNPUsers",
        "impacket-GetUserSPNs",
        "impacket-secretsdump",
        "impacket-psexec",
        "impacket-smbclient",
        "impacket-wmiexec",
        "impacket-dcomexec",
        "impacket-atexec",
        "GetNPUsers.py",
        "GetUserSPNs.py",
        "secretsdump.py",
        "psexec.py",
        "smbclient.py",
        "certipy",
        "bloodhound-python",
        "ldapdomaindump",
    }

    # Check base name (handle full paths)
    base_name = os.path.basename(executable)
    if base_name in python_tools:
        return True

    # Check shebang for Python interpreter
    exe_path = shutil.which(executable)
    if exe_path:
        try:
            with open(exe_path, "rb") as f:
                first_bytes = f.read(100)
                if first_bytes.startswith(b"#!") and b"python" in first_bytes:
                    return True
        except (IOError, OSError):
            pass

    return False


def _wrap_cmd_for_line_buffering(cmd: List[str]) -> List[str]:
    """
    Wrap a command with stdbuf for line-buffered output when available.

    This ensures output is written line-by-line instead of in 4-8KB blocks,
    improving real-time log monitoring and ensuring output is captured
    before process termination.

    Note: Python tools are excluded because stdbuf interferes with Python's
    internal buffering and can cause zero output on some systems (Ubuntu ARM).

    Args:
        cmd: Command to wrap

    Returns:
        Command wrapped with stdbuf if available, original command otherwise
    """
    if not cmd:
        return cmd

    # Skip stdbuf for Python tools - causes output capture failures on ARM
    if _is_python_tool(cmd):
        return cmd

    if _is_stdbuf_available():
        # stdbuf -oL = line-buffered stdout, -eL = line-buffered stderr
        return ["stdbuf", "-oL", "-eL"] + cmd

    return cmd


def _get_subprocess_env() -> Dict[str, str]:
    """
    Get environment for subprocess with buffering disabled.

    Sets PYTHONUNBUFFERED=1 for Python subprocesses and TERM=dumb
    to prevent interactive terminal issues.
    """
    env = os.environ.copy()
    env["TERM"] = "dumb"  # Prevent stty errors from interactive tools
    env["PYTHONUNBUFFERED"] = "1"  # Disable Python output buffering
    return env


def _run_subprocess_with_spec(
    cmd_spec: Dict[str, Any], log_path: str, jid: int = None, plugin=None
) -> int:
    """
    Execute a command specification with proper PID tracking.

    This function handles command execution for plugins using build_command().
    It provides PID tracking, timeout handling, and kill signal support.

    Supports two modes:
    - Console mode: Standard subprocess execution (cmd array)
    - RPC mode: MSF RPC API execution (mode='rpc') - Pro feature

    Args:
        cmd_spec: Command specification dict with:
            - For console mode:
                - cmd: List[str] - Command array (required)
                - timeout: int - Timeout in seconds (optional, default: JOB_TIMEOUT_SECONDS)
                - env: Dict[str, str] - Environment variables (optional)
                - cwd: str - Working directory (optional)
                - needs_shell: bool - Use shell=True (optional, default: False)
            - For RPC mode:
                - mode: 'rpc'
                - exploit_path: str - MSF exploit module path
                - target: str - Target IP/hostname
                - options: Dict - Exploit options
                - payload: str - Payload to use (optional)
        log_path: Path to write logs
        jid: Job ID for PID tracking (optional)
        plugin: Plugin instance (optional, for RPC mode)

    Returns:
        Exit code (0 = success, non-zero = failure)
    """
    # Check for RPC mode (Pro feature)
    if cmd_spec.get("mode") == "rpc":
        return _run_rpc_exploit(cmd_spec, log_path, jid, plugin)

    cmd = cmd_spec.get("cmd")
    if not cmd:
        with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
            fh.write("ERROR: No command provided in spec\n")
        return 1

    timeout = cmd_spec.get("timeout", JOB_TIMEOUT_SECONDS)
    spec_env = cmd_spec.get("env")
    cwd = cmd_spec.get("cwd")
    needs_shell = cmd_spec.get("needs_shell", False)

    _append_worker_log(f"_run_subprocess_with_spec: timeout={timeout}s for job {jid}")

    # Wrap command with stdbuf for line-buffered output (unless shell mode)
    original_cmd = cmd
    if not needs_shell:
        cmd = _wrap_cmd_for_line_buffering(cmd)

    # Prepare environment with PYTHONUNBUFFERED=1 and TERM=dumb
    proc_env = _get_subprocess_env()
    if spec_env:
        proc_env.update(spec_env)

    with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
        fh.write("=== Command Execution (build_command) ===\n")
        fh.write(f"Command: {' '.join(original_cmd)}\n")
        fh.write(f"Timeout: {timeout} seconds\n")
        if spec_env:
            fh.write(f"Environment: {spec_env}\n")
        if cwd:
            fh.write(f"Working Dir: {cwd}\n")
        fh.write(
            f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
        )
        fh.flush()

        try:
            # Create new process group so all children can be killed together
            # Redirect stdin to /dev/null to prevent password prompts from hanging
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,  # Prevent interactive prompts
                stdout=fh,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid,  # Creates new session
                env=proc_env,
                cwd=cwd,
                shell=needs_shell,  # nosec B602 - intentional for security tool command execution
            )

            # Store PID and process start time for stale detection
            if jid is not None:
                proc_start_time = _get_process_start_time(proc.pid)
                _update_job(jid, pid=proc.pid, process_start_time=proc_start_time)
                _append_worker_log(f"job {jid}: running with PID {proc.pid}")

            # Wait for process with timeout
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Kill entire process group on timeout
                try:
                    pgid = os.getpgid(proc.pid)
                    os.killpg(pgid, signal.SIGKILL)
                except:
                    proc.kill()  # Fallback to single process
                proc.wait()

                # For MSF exploits, check if a session was opened before timeout
                # A timeout with an open session is success, not failure
                session_opened = False
                if hasattr(plugin, "tool") and plugin.tool in (
                    "msf_exploit",
                    "msf_auxiliary",
                ):
                    try:
                        fh.flush()
                        with open(
                            log_path, "r", encoding="utf-8", errors="replace"
                        ) as rf:
                            content = rf.read()
                        import re

                        session_opened = bool(
                            re.search(r"session \d+ opened", content, re.IGNORECASE)
                        )
                    except Exception:
                        pass

                if session_opened:
                    fh.write(
                        f"\n[*] Session opened successfully (timeout expected - session is active)\n"
                    )
                    fh.write(
                        f"=== Completed: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} ===\n"
                    )
                    return 0
                else:
                    fh.write(f"\nERROR: Command timed out after {timeout} seconds\n")
                    fh.flush()
                    return 124

            # Check if job was killed externally during execution
            if jid is not None:
                job = get_job(jid)
                if job and job.get("status") == "killed":
                    fh.write(f"\nINFO: Job was killed externally\n")
                    # Process may already be dead, but ensure cleanup
                    try:
                        if proc.poll() is None:  # Still running
                            pgid = os.getpgid(proc.pid)
                            os.killpg(pgid, signal.SIGTERM)
                            time.sleep(1)
                            # Force kill if still alive
                            try:
                                os.getpgid(pgid)
                                os.killpg(pgid, signal.SIGKILL)
                            except:
                                pass
                            proc.wait(timeout=5)
                    except:
                        pass
                    fh.flush()
                    return 143  # 128 + 15 (SIGTERM)

            fh.write(
                f"\n=== Completed: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} ===\n"
            )
            fh.write(f"Exit Code: {proc.returncode}\n")
            fh.flush()
            os.fsync(fh.fileno())  # Ensure data is on disk before parsing
            return proc.returncode

        except FileNotFoundError:
            fh.write(f"\nERROR: Tool not found: {cmd[0]}\n")
            fh.flush()
            return 127
        except Exception as e:
            fh.write(f"\nERROR: {type(e).__name__}: {e}\n")
            fh.flush()
            return 1


def _run_subprocess(
    tool: str,
    target: str,
    args: List[str],
    log_path: str,
    jid: int = None,
    timeout: int = None,
) -> int:
    # Use None as default and resolve at runtime to avoid Python's early binding issue
    if timeout is None:
        timeout = JOB_TIMEOUT_SECONDS

    # Log the timeout being used for debugging
    _append_worker_log(f"_run_subprocess: timeout={timeout}s for job {jid}")

    cmd = [tool] + (args or [])
    cmd = [c.replace("<target>", target) for c in cmd]

    # Wrap command with stdbuf for line-buffered output
    cmd = _wrap_cmd_for_line_buffering(cmd)

    with open(log_path, "a", encoding="utf-8", errors="replace") as fh:
        # Log original command (without stdbuf wrapper for clarity)
        original_cmd = cmd[3:] if cmd[:3] == ["stdbuf", "-oL", "-eL"] else cmd
        fh.write("=== Subprocess Execution ===\n")
        fh.write(f"Command: {' '.join(original_cmd)}\n")
        fh.write(f"Timeout: {timeout} seconds\n")
        fh.write(
            f"Started: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
        )
        fh.flush()

        try:
            # Create new process group so all children can be killed together
            # Redirect stdin to /dev/null to prevent password prompts from hanging
            # Use env with PYTHONUNBUFFERED=1 and TERM=dumb
            env = _get_subprocess_env()

            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,  # Prevent interactive prompts
                stdout=fh,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid,  # Creates new session
                env=env,
            )

            # Store PID and process start time for stale detection
            if jid is not None:
                proc_start_time = _get_process_start_time(proc.pid)
                _update_job(jid, pid=proc.pid, process_start_time=proc_start_time)
                _append_worker_log(f"job {jid}: running with PID {proc.pid}")

            # Wait for process with timeout
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Kill entire process group on timeout
                try:
                    pgid = os.getpgid(proc.pid)
                    os.killpg(pgid, signal.SIGKILL)
                except:
                    proc.kill()  # Fallback to single process
                proc.wait()
                fh.write(f"\nERROR: Command timed out after {timeout} seconds\n")
                fh.flush()
                return 124

            # Check if job was killed externally during execution
            if jid is not None:
                job = get_job(jid)
                if job and job.get("status") == "killed":
                    fh.write(f"\nINFO: Job was killed externally\n")
                    # Process may already be dead, but ensure cleanup
                    try:
                        if proc.poll() is None:  # Still running
                            pgid = os.getpgid(proc.pid)
                            os.killpg(pgid, signal.SIGTERM)
                            time.sleep(1)
                            # Force kill if still alive
                            try:
                                os.getpgid(pgid)
                                os.killpg(pgid, signal.SIGKILL)
                            except:
                                pass
                            proc.wait(timeout=5)
                    except:
                        pass
                    fh.flush()
                    return 143  # 128 + 15 (SIGTERM)

            fh.write(
                f"\n=== Completed: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} ===\n"
            )
            fh.write(f"Exit Code: {proc.returncode}\n")
            fh.flush()
            os.fsync(fh.fileno())  # Ensure data is on disk before parsing
            return proc.returncode

        except FileNotFoundError:
            fh.write(f"\nERROR: Tool not found: {cmd[0]}\n")
            fh.flush()
            return 127
        except Exception as e:
            fh.write(f"\nERROR: {type(e).__name__}: {e}\n")
            fh.flush()
            return 1


def _is_true_error_exit_code(rc: int, tool: str) -> bool:
    """
    Determine if an exit code indicates a true error (crash, timeout, not found).

    Some tools use non-zero exit codes for legitimate conditions (e.g., gobuster
    returns 1 for wildcard detection). Let the parser determine status for those.

    Args:
        rc: Exit code from tool
        tool: Tool name

    Returns:
        True if this is a true error that should set status=error immediately
    """
    # Exit codes that always indicate true errors
    if rc == 124:  # timeout command timeout
        return True
    if rc == 127:  # command not found
        return True
    if rc in [126, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137]:
        # Permission denied, fatal signals, killed by signal
        return True

    # Tools that use non-zero exit codes for non-error conditions
    # Parser will determine the actual status based on output
    # msf_exploit returns 1 when no session opened (exploit ran but target not vulnerable)
    # nikto returns non-zero when it finds vulnerabilities (not an error!)
    # dnsrecon returns 1 when crt.sh lookup fails (known bug) but still collects valid DNS data
    # evil_winrm returns non-zero even on successful auth - let handler parse output
    # bloodhound exits non-zero on connection errors but still collects AD data
    # hashcat returns 1 when exhausted (no passwords cracked) - not an error, just no results
    # bash scripts and web_login_test return 1 when credentials fail - not an error, just invalid creds
    tools_with_nonzero_success = [
        "gobuster",
        "hydra",
        "medusa",
        "msf_exploit",
        "nikto",
        "dnsrecon",
        "evil_winrm",
        "bloodhound",
        "hashcat",
        "bash",
        "web_login_test",
    ]

    if tool.lower() in tools_with_nonzero_success:
        # Let parser determine status
        return False

    # For most tools, rc != 0 means error
    return rc != 0


def run_job(jid: int) -> None:
    """
    Run a job by its ID.

    Uses atomic status transition with cross-process file locking to prevent
    race conditions with kill/delete and other processes (UI).
    If job is not in QUEUED status when we try to start it, we abort.
    """
    # Atomically check status and transition to RUNNING
    # Both thread lock and file lock ensure no other process/thread can
    # read/write jobs.json while we're modifying it
    with _lock:  # Thread safety within this process
        try:
            with _jobs_lock():  # Cross-process safety
                jobs = _read_jobs_unlocked()
                job = None
                for j in jobs:
                    if j.get("id") == jid:
                        job = j
                        break

                if not job:
                    logger.error("Job not found", extra={"job_id": jid})
                    _append_worker_log(f"run_job: job {jid} not found")
                    return

                current_status = job.get("status")
                if current_status != STATUS_QUEUED:
                    # Job was killed, deleted, or already running - abort
                    logger.info(
                        "Job not in queued status, skipping",
                        extra={"job_id": jid, "current_status": current_status},
                    )
                    _append_worker_log(
                        f"run_job: job {jid} not queued (status={current_status}), skipping"
                    )
                    return

                # Atomically set to RUNNING while still holding both locks
                now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                job["status"] = STATUS_RUNNING
                job["started_at"] = now
                _write_jobs_unlocked(jobs)
        except TimeoutError:
            # Fall back to non-locked operation
            _append_worker_log(
                f"jobs.json lock timeout in run_job for {jid}, using fallback"
            )
            jobs = _read_jobs()
            job = None
            for j in jobs:
                if j.get("id") == jid:
                    job = j
                    break

            if not job:
                logger.error("Job not found", extra={"job_id": jid})
                _append_worker_log(f"run_job: job {jid} not found")
                return

            current_status = job.get("status")
            if current_status != STATUS_QUEUED:
                _append_worker_log(
                    f"run_job: job {jid} not queued (status={current_status}), skipping"
                )
                return

            now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            job["status"] = STATUS_RUNNING
            job["started_at"] = now
            _write_jobs(jobs)

    log_path = job.get("log") or os.path.join(JOBS_DIR, f"{jid}.log")
    _ensure_dirs()

    log_dir = os.path.dirname(log_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    _append_worker_log(f"job {jid} started: {job.get('tool')} {job.get('target')}")

    logger.info(
        "Job started",
        extra={
            "event_type": "job_started",
            "job_id": jid,
            "tool": job.get("tool"),
            "target": job.get("target"),
            "engagement_id": job.get("engagement_id"),
        },
    )

    try:
        tool = job.get("tool", "")
        target = job.get("target", "")
        args = job.get("args", [])
        label = job.get("label", "")

        # Resolve wordlist paths to actual filesystem locations
        try:
            from ..wordlists import resolve_args_wordlists

            args = resolve_args_wordlists(args)
        except ImportError:
            pass  # Wordlists module not available, use args as-is

        start_time = time.perf_counter()
        plugin_executed, rc = _try_run_plugin(
            tool, target, args, label, log_path, jid=jid
        )

        if not plugin_executed:
            _append_worker_log(
                f"job {jid}: no plugin found for '{tool}', using subprocess"
            )
            logger.info(
                "Using subprocess fallback", extra={"job_id": jid, "tool": tool}
            )
            rc = _run_subprocess(tool, target, args, log_path, jid=jid)

        # Check if job was killed externally while we were running
        job = get_job(jid)
        job_killed = job and job.get("status") == "killed"

        if job_killed:
            _append_worker_log(
                f"job {jid}: detected external kill signal, skipping post-processing"
            )
            logger.info("Job was killed externally", extra={"job_id": jid})

        # ALWAYS update status, finished_at, and pid - even if job was killed
        # This ensures the job record is properly finalized
        duration_ms = (time.perf_counter() - start_time) * 1000
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Determine initial status based on exit code and tool behavior
        # Parser will set final status (done/no_results/warning) after parsing
        if job_killed:
            status = STATUS_KILLED
        elif _is_true_error_exit_code(rc, tool):
            status = STATUS_ERROR
        else:
            # Not a true error - let parser determine final status
            # Use a temporary status that parser will update
            status = STATUS_DONE  # Temporary - parser will refine this

        _update_job(jid, status=status, finished_at=now, pid=None)

        logger.info(
            "Job completed",
            extra={
                "event_type": "job_completed",
                "job_id": jid,
                "status": status,
                "exit_code": rc,
                "duration_ms": round(duration_ms, 2),
            },
        )

        # Only do post-processing if job was not killed externally
        if job_killed:
            _append_worker_log(f"job {jid} finished: status={status} rc={rc}")
            return

        # Check for transient errors and auto-retry
        job = get_job(jid)
        retry_count = job.get("metadata", {}).get("retry_count", 0)
        if retry_count < MAX_RETRIES:
            # Read log to check for transient errors or flaky netexec
            log_path = job.get("log", "")
            if log_path and os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                        log_content = f.read()

                    # Check for transient errors OR flaky netexec (connected but no shares)
                    is_transient = _is_transient_error(log_content)
                    is_netexec_flaky = _is_netexec_flaky_empty(log_content, job)
                    retry_reason = None

                    if is_transient:
                        retry_reason = "transient error"
                    elif is_netexec_flaky:
                        retry_reason = "netexec connected but no shares"

                    if retry_reason:
                        logger.info(
                            f"Auto-retrying job: {retry_reason}",
                            extra={"job_id": jid, "retry_count": retry_count + 1},
                        )
                        _append_worker_log(
                            f"job {jid}: {retry_reason}, auto-retry {retry_count + 1}/{MAX_RETRIES}"
                        )

                        # Build new job metadata with incremented retry count
                        new_metadata = job.get("metadata", {}).copy()
                        new_metadata["retry_count"] = retry_count + 1
                        new_metadata["retried_from"] = jid

                        # Enqueue retry job
                        retry_jid = enqueue_job(
                            tool=job.get("tool"),
                            target=job.get("target"),
                            args=job.get("args", []),
                            label=job.get("label", ""),
                            engagement_id=job.get("engagement_id"),
                            metadata=new_metadata,
                            parent_id=job.get("metadata", {}).get("parent_id"),
                            reason=f"Auto-retry {retry_count + 1}/{MAX_RETRIES} ({retry_reason})",
                            rule_id=job.get("metadata", {}).get("rule_id"),
                            skip_scope_check=True,  # Already validated on first run
                        )
                        _append_worker_log(
                            f"job {jid}: retry enqueued as job #{retry_jid}"
                        )

                        # Mark original job as retried (not error)
                        _update_job(
                            jid,
                            status=STATUS_WARNING,
                            chained=True,  # Prevent chaining from failed job
                            parse_result={"note": f"Retried as job #{retry_jid}"},
                        )
                        return
                except Exception as e:
                    logger.warning(f"Failed to check for transient errors: {e}")

        # Try to parse results into database
        try:
            from .result_handler import handle_job_result

            # Re-fetch job to get updated data
            job = get_job(jid)

            # Ensure log file is fully flushed to disk before parsing
            # Some tools (especially Python-based like impacket) may have buffered output
            log_path = job.get("log", "")
            if log_path and os.path.exists(log_path):
                # Wait for completion marker with retries
                # Log files end with "Exit Code:" or "=== Completed"
                max_retries = 5
                retry_delay = 0.2  # 200ms between retries
                log_complete = False

                for attempt in range(max_retries):
                    try:
                        with open(
                            log_path, "r", encoding="utf-8", errors="replace"
                        ) as f:
                            content = f.read()
                            # Check for completion markers
                            if "Exit Code:" in content or "=== Completed" in content:
                                log_complete = True
                                break
                    except Exception:
                        pass

                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)

                if not log_complete:
                    # Last resort: force filesystem sync and proceed anyway
                    try:
                        with open(log_path, "a") as f:
                            os.fsync(f.fileno())
                    except Exception:
                        pass

            parse_result = handle_job_result(job)

            # Handle parse failure cases
            if parse_result is None:
                # Parser returned None - likely missing log file, no parser for tool, or missing engagement
                logger.warning(
                    "Job parse returned None - no parser for this tool",
                    extra={
                        "job_id": jid,
                        "tool": job.get("tool"),
                        "log_exists": (
                            os.path.exists(job.get("log", ""))
                            if job.get("log")
                            else False
                        ),
                    },
                )
                _append_worker_log(
                    f"job {jid} parse returned None (tool={job.get('tool')}) - check if parser exists"
                )
                # Only update status to WARNING if it wasn't already an ERROR
                # (e.g., exit code 127 = command not found should stay as ERROR)
                current_status = job.get("status")
                if current_status != STATUS_ERROR:
                    _update_job(
                        jid,
                        status=STATUS_WARNING,
                        parse_result={
                            "error": "Parser returned None - no results extracted"
                        },
                    )
                # Mark as chained to prevent infinite retry
                _update_job(jid, chained=True)
                return

            if "error" in parse_result:
                logger.error(
                    "Job parse error - results may be incomplete",
                    extra={"job_id": jid, "error": parse_result["error"]},
                )
                _append_worker_log(f"job {jid} parse error: {parse_result['error']}")
                # Update job status to warning with the error
                _update_job(jid, status=STATUS_WARNING, parse_result=parse_result)
                # Mark as chained to prevent infinite retry
                _update_job(jid, chained=True)
                return

            # Parse succeeded
            logger.info(
                "Job parsed successfully",
                extra={"job_id": jid, "parse_result": parse_result},
            )
            _append_worker_log(f"job {jid} parsed: {parse_result}")

            # Determine chainable status BEFORE updating to avoid race condition
            # We must set parse_result and chainable in a single atomic update
            try:
                from souleyez.core.tool_chaining import ToolChaining

                chaining = ToolChaining()

                # Get current job to check status
                job = get_job(jid)
                job_status = job.get("status", STATUS_ERROR)

                # Determine final status from parser if provided
                final_status = parse_result.get("status", job_status)

                # Check if job should be chainable
                should_chain = (
                    chaining.is_enabled()
                    and parse_result
                    and "error" not in parse_result
                    and is_chainable(final_status)
                )

                # Build update dict - ATOMIC update of parse_result + chainable
                update_fields = {"parse_result": parse_result}

                if "status" in parse_result:
                    update_fields["status"] = final_status
                    logger.info(
                        "Job status updated from parser",
                        extra={"job_id": jid, "status": final_status},
                    )
                    _append_worker_log(f"job {jid} status updated to: {final_status}")

                if should_chain:
                    update_fields["chainable"] = True
                else:
                    # Not chainable - mark as chained to skip
                    update_fields["chained"] = True

                # Single atomic update to prevent race condition
                _update_job(jid, **update_fields)

                # Log chaining decision
                if should_chain:
                    if final_status == STATUS_WARNING:
                        logger.info(
                            "Job with warning status marked for chaining",
                            extra={
                                "job_id": jid,
                                "tool": job.get("tool"),
                                "wildcard_detected": parse_result.get(
                                    "wildcard_detected", False
                                ),
                            },
                        )
                        _append_worker_log(
                            f"job {jid} (status=warning) marked as chainable"
                        )
                    else:
                        logger.info(
                            "Job marked as chainable",
                            extra={
                                "job_id": jid,
                                "tool": job.get("tool"),
                                "status": final_status,
                            },
                        )
                        _append_worker_log(
                            f"job {jid} marked as chainable (status={final_status})"
                        )
                else:
                    reason = f"chaining_disabled={not chaining.is_enabled()}, has_error={'error' in parse_result}, status={final_status}"
                    _append_worker_log(f"job {jid} not chainable ({reason})")

            except Exception as chain_err:
                logger.error(
                    "Failed to mark job as chainable",
                    extra={"job_id": jid, "error": str(chain_err)},
                )
                _append_worker_log(f"job {jid} chainable marking error: {chain_err}")
                # Mark as chained to prevent retry loops
                _update_job(jid, chained=True, chain_error=str(chain_err))

        except Exception as e:
            logger.error(
                "Job parse exception",
                extra={
                    "job_id": jid,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                },
            )
            _append_worker_log(f"job {jid} parse exception: {e}")

        # Sanitize log file to remove credentials
        try:
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    original_log = f.read()

                # Check if encryption is enabled - only sanitize if encryption is on
                from souleyez.storage.crypto import CryptoManager

                crypto_mgr = CryptoManager()

                if (
                    crypto_mgr.is_encryption_enabled()
                    and LogSanitizer.contains_credentials(original_log)
                ):
                    sanitized_log = LogSanitizer.sanitize(original_log)

                    # Write sanitized log back
                    with open(log_path, "w", encoding="utf-8") as f:
                        f.write(sanitized_log)

                    summary = LogSanitizer.get_redaction_summary(
                        original_log, sanitized_log
                    )
                    if summary:
                        _append_worker_log(f"job {jid}: {summary}")
                        logger.info(
                            "Log sanitized", extra={"job_id": jid, "summary": summary}
                        )
        except Exception as sanitize_err:
            logger.warning(
                "Log sanitization failed",
                extra={"job_id": jid, "error": str(sanitize_err)},
            )
            # Don't fail the job if sanitization fails

        _append_worker_log(f"job {jid} finished: status={status} rc={rc}")

    except Exception as e:
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _update_job(jid, status="error", error=str(e), finished_at=now)
        logger.error(
            "Job crashed",
            extra={
                "event_type": "job_failed",
                "job_id": jid,
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
        )
        _append_worker_log(f"job {jid} crashed: {e}")

        # Sanitize log even on error
        try:
            if os.path.exists(log_path):
                from souleyez.storage.crypto import CryptoManager

                crypto_mgr = CryptoManager()

                if crypto_mgr.is_encryption_enabled():
                    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                        original_log = f.read()

                    if LogSanitizer.contains_credentials(original_log):
                        sanitized_log = LogSanitizer.sanitize(original_log)
                        with open(log_path, "w", encoding="utf-8") as f:
                            f.write(sanitized_log)
        except Exception:
            pass  # Silently fail sanitization on error


def _is_pid_alive(pid: int) -> bool:
    """Check if a process with the given PID is still running."""
    if pid is None:
        return False
    try:
        os.kill(pid, 0)  # Signal 0 doesn't kill, just checks existence
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we can't signal it (owned by another user)
        return True
    except Exception:
        return False


def _check_log_for_completion(log_path: str, tool: str) -> tuple:
    """
    Check a job's log file for completion markers.

    Returns:
        (completed: bool, exit_code: int or None)
    """
    if not log_path or not os.path.exists(log_path):
        return (False, None)

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            # Read last 5KB of log (completion markers are at the end)
            f.seek(0, 2)  # End of file
            file_size = f.tell()
            read_size = min(5000, file_size)
            f.seek(max(0, file_size - read_size))
            log_tail = f.read()

        # Tool-specific completion markers
        completion_markers = {
            "nmap": ["Nmap done:", "Nmap scan report for"],
            "gobuster": ["Finished", "Progress:"],
            "nikto": ["host(s) tested", "End Time:"],
            "nuclei": ["Scan completed", "matches found", "No results found"],
            "sqlmap": ["fetched data logged", "shutting down"],
            "hydra": ["valid password", "host:", "targets finished"],
            "ffuf": ["Progress:", "Duration:"],
            "default": ["=== Completed:", "Exit Code:"],
        }

        markers = completion_markers.get(tool.lower(), completion_markers["default"])

        for marker in markers:
            if marker in log_tail:
                # Try to extract exit code
                exit_code = None
                if "Exit Code:" in log_tail:
                    try:
                        idx = log_tail.index("Exit Code:")
                        code_str = log_tail[idx + 10 : idx + 15].strip().split()[0]
                        exit_code = int(code_str)
                    except (ValueError, IndexError):
                        exit_code = 0
                return (True, exit_code if exit_code is not None else 0)

        return (False, None)

    except Exception as e:
        _append_worker_log(f"Error checking log for completion: {e}")
        return (False, None)


def _detect_and_recover_stale_jobs() -> int:
    """
    Detect and recover jobs stuck in 'running' state with dead PIDs.

    This handles cases where the worker crashed/restarted while a job was
    executing. If the job's process is dead but log shows completion,
    finalize the job properly. If crashed mid-execution, mark as error.

    Returns:
        Number of stale jobs recovered
    """
    recovered = 0

    try:
        jobs = _read_jobs()
        running_jobs = [j for j in jobs if j.get("status") == STATUS_RUNNING]

        for job in running_jobs:
            jid = job.get("id")
            pid = job.get("pid")
            tool = job.get("tool", "unknown")
            log_path = job.get("log")
            stored_start_time = job.get("process_start_time")

            # Check if PID is alive
            if _is_pid_alive(pid):
                # PID is alive - but check for PID reuse
                if stored_start_time is not None:
                    current_start_time = _get_process_start_time(pid)
                    if current_start_time is not None:
                        # Allow 2 second tolerance for timing differences
                        if abs(current_start_time - stored_start_time) > 2:
                            # PID reused by different process
                            _append_worker_log(
                                f"job {jid}: PID {pid} reused (stored start: {stored_start_time:.0f}, "
                                f"current: {current_start_time:.0f})"
                            )
                            logger.warning(
                                "PID reuse detected",
                                extra={
                                    "job_id": jid,
                                    "tool": tool,
                                    "pid": pid,
                                    "stored_start_time": stored_start_time,
                                    "current_start_time": current_start_time,
                                },
                            )
                            # Fall through to stale job handling
                        else:
                            # Same process, still running
                            continue
                    else:
                        # Can't get current start time, assume still valid
                        continue
                else:
                    # No stored start time (old job), assume still valid
                    continue
            else:
                # PID is dead - definitely stale
                _append_worker_log(f"job {jid}: detected stale (PID {pid} is dead)")
                logger.warning(
                    "Stale job detected",
                    extra={"job_id": jid, "tool": tool, "pid": pid},
                )

            # Check if log shows completion
            completed, exit_code = _check_log_for_completion(log_path, tool)
            now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            if completed:
                # Job finished but status wasn't updated - finalize it
                _append_worker_log(f"job {jid}: log shows completion, finalizing")

                # Determine status based on exit code
                if exit_code == 0 or exit_code is None:
                    status = STATUS_DONE
                elif _is_true_error_exit_code(exit_code, tool):
                    status = STATUS_ERROR
                else:
                    status = STATUS_DONE

                _update_job(jid, status=status, finished_at=now, pid=None)

                # Try to parse results
                try:
                    from souleyez.core.tool_chaining import ToolChaining

                    from .result_handler import handle_job_result

                    job = get_job(jid)
                    parse_result = handle_job_result(job)

                    if parse_result:
                        if "error" in parse_result:
                            _append_worker_log(
                                f"job {jid} stale recovery parse error: {parse_result['error']}"
                            )
                        else:
                            # Determine final status and chainable in one check
                            final_status = parse_result.get("status", status)
                            chaining = ToolChaining()
                            should_chain = chaining.is_enabled() and is_chainable(
                                final_status
                            )

                            # Build atomic update - parse_result + status + chainable together
                            update_fields = {"parse_result": parse_result}
                            if "status" in parse_result:
                                update_fields["status"] = final_status
                            if should_chain:
                                update_fields["chainable"] = True

                            # Single atomic update to prevent race condition
                            _update_job(jid, **update_fields)

                            _append_worker_log(
                                f"job {jid} stale recovery parsed: {parse_result.get('findings_added', 0)} findings"
                            )

                            logger.info(
                                "Stale job recovered with results",
                                extra={
                                    "job_id": jid,
                                    "tool": tool,
                                    "status": final_status,
                                    "parse_result": parse_result,
                                    "chainable": should_chain,
                                },
                            )

                            if should_chain:
                                _append_worker_log(
                                    f"job {jid} stale recovery marked as chainable"
                                )

                except Exception as parse_err:
                    _append_worker_log(
                        f"job {jid} stale recovery parse exception: {parse_err}"
                    )

                recovered += 1

            else:
                # Process died mid-execution - mark as error
                _append_worker_log(
                    f"job {jid}: process died unexpectedly, marking as error"
                )
                _update_job(
                    jid,
                    status=STATUS_ERROR,
                    finished_at=now,
                    pid=None,
                    error="Process terminated unexpectedly (worker restart or crash)",
                )

                logger.warning(
                    "Stale job marked as error",
                    extra={
                        "job_id": jid,
                        "tool": tool,
                        "reason": "process_died_unexpectedly",
                    },
                )

                recovered += 1

        return recovered

    except Exception as e:
        logger.error(
            "Stale job detection error",
            extra={"error": str(e), "traceback": traceback.format_exc()},
        )
        _append_worker_log(f"stale job detection error: {e}")
        return 0


def _check_msf_exploitation_success():
    """
    Check running MSF jobs for exploitation success indicators.

    When a session is opened, updates the job with exploitation_detected=True
    and records the successful exploitation attempt.

    Returns:
        int: Number of jobs where exploitation was detected
    """
    import re

    try:
        jobs = _read_jobs()
        running_msf = [
            j
            for j in jobs
            if j.get("status") == STATUS_RUNNING
            and j.get("tool") in ("msfconsole", "msf")
            and not j.get("exploitation_detected")  # Not already detected
        ]

        if not running_msf:
            return 0

        detected_count = 0

        # Success patterns from MSF output
        success_patterns = [
            r"\[\*\]\s+Command shell session \d+ opened",
            r"\[\*\]\s+Meterpreter session \d+ opened",
            r"\[\+\]\s+\d+\.\d+\.\d+\.\d+:\d+\s+-\s+Session \d+ created",
            r"\[\+\].*session.*opened",
            r"\[\+\].*session.*created",
        ]

        for job in running_msf:
            jid = job.get("id")
            log_path = os.path.join(JOBS_DIR, f"{jid}.log")

            if not os.path.exists(log_path):
                continue

            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

                # Check for success patterns
                session_opened = False
                session_info = None

                for pattern in success_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        session_opened = True
                        # Extract session number if available
                        session_match = re.search(
                            r"session (\d+)", match.group(), re.IGNORECASE
                        )
                        if session_match:
                            session_info = f"Session {session_match.group(1)}"
                        break

                if session_opened:
                    # Update job with exploitation success
                    _update_job(
                        jid, exploitation_detected=True, session_info=session_info
                    )
                    _append_worker_log(
                        f"job {jid}: exploitation success detected - {session_info or 'session opened'}"
                    )

                    # Record exploit attempt as success
                    engagement_id = job.get("engagement_id")
                    target = job.get("target")
                    label = job.get("label", "")
                    args = job.get("args", [])

                    if engagement_id and target:
                        try:
                            from souleyez.storage.exploit_attempts import record_attempt
                            from souleyez.storage.hosts import HostManager

                            hm = HostManager()
                            host = hm.get_host_by_ip(engagement_id, target)

                            if host:
                                # Extract port from args (look for "set RPORT X" or "RPORT X")
                                port = None
                                args_str = " ".join(args) if args else ""
                                port_match = re.search(
                                    r"RPORT\s+(\d+)", args_str, re.IGNORECASE
                                )
                                if port_match:
                                    port = int(port_match.group(1))

                                # Find service_id for this port
                                service_id = None
                                if port:
                                    services = hm.get_host_services(host["id"])
                                    for svc in services:
                                        if svc.get("port") == port:
                                            service_id = svc.get("id")
                                            break

                                # Extract exploit identifier from label or args
                                exploit_id = (
                                    label.replace("MSF: ", "msf:")
                                    if label.startswith("MSF:")
                                    else f"msf:{label}"
                                )

                                record_attempt(
                                    engagement_id=engagement_id,
                                    host_id=host["id"],
                                    exploit_identifier=exploit_id,
                                    exploit_title=label,
                                    status="success",
                                    service_id=service_id,
                                    notes=(
                                        f"Session opened - {session_info}"
                                        if session_info
                                        else "Session opened"
                                    ),
                                )
                                _append_worker_log(
                                    f"job {jid}: recorded exploitation success for {target}:{port or 'unknown'}"
                                )
                        except Exception as e:
                            _append_worker_log(
                                f"job {jid}: failed to record exploit attempt: {e}"
                            )

                    detected_count += 1

            except Exception as e:
                _append_worker_log(f"job {jid}: error checking log: {e}")
                continue

        return detected_count

    except Exception as e:
        _append_worker_log(f"MSF success detection error: {e}")
        return 0


def _update_job_progress():
    """
    Update progress tracking for running jobs.

    Checks log file modification times and flags jobs with no recent output
    as possibly hung (no output for JOB_HUNG_THRESHOLD seconds).
    """
    try:
        jobs = _read_jobs()
        running_jobs = [j for j in jobs if j.get("status") == STATUS_RUNNING]

        for job in running_jobs:
            jid = job.get("id")
            log_path = job.get("log")

            if not log_path or not os.path.exists(log_path):
                continue

            try:
                # Get log file modification time
                mtime = os.path.getmtime(log_path)
                current_time = time.time()
                time_since_output = current_time - mtime

                # Update last_output_at in job record
                updates = {"last_output_at": mtime}

                # Flag as possibly hung if no output for threshold
                was_hung = job.get("possibly_hung", False)
                is_hung = time_since_output > JOB_HUNG_THRESHOLD

                if is_hung != was_hung:
                    updates["possibly_hung"] = is_hung
                    if is_hung:
                        _append_worker_log(
                            f"job {jid}: no output for {int(time_since_output)}s, flagged as possibly hung"
                        )
                        logger.warning(
                            "Job possibly hung",
                            extra={
                                "job_id": jid,
                                "tool": job.get("tool"),
                                "time_since_output": int(time_since_output),
                            },
                        )

                _update_job(jid, **updates)

            except Exception as e:
                # Non-critical, just skip this job
                pass

    except Exception as e:
        logger.error("Job progress tracking error", extra={"error": str(e)})


def worker_loop(poll_interval: float = 2.0):
    """
    Main worker loop that processes jobs and handles auto-chaining.

    Loop behavior:
    1. Update heartbeat for health monitoring
    2. Detect and recover stale jobs (dead PIDs)
    3. Update progress tracking for running jobs
    4. Check for running jobs
    5. If none running, start next queued job
    6. Process one chainable job (if any)
    7. Sleep poll_interval seconds, repeat

    Args:
        poll_interval: Seconds to sleep between iterations (default: 2.0)
    """
    _ensure_dirs()
    _update_heartbeat()  # Initial heartbeat
    _append_worker_log("souleyez background worker: starting loop")

    # Track last stale job check time (check every 15 seconds, not every iteration)
    last_stale_check = 0
    stale_check_interval = 15  # seconds (reduced from 30s for faster detection)

    # Track last heartbeat time
    last_heartbeat = time.time()

    # Run stale job detection on startup
    try:
        recovered = _detect_and_recover_stale_jobs()
        if recovered > 0:
            _append_worker_log(f"startup: recovered {recovered} stale job(s)")
    except Exception as e:
        _append_worker_log(f"startup stale job detection error: {e}")

    try:
        while True:
            current_time = time.time()

            # Update heartbeat every HEARTBEAT_INTERVAL seconds
            if current_time - last_heartbeat >= HEARTBEAT_INTERVAL:
                _update_heartbeat()
                last_heartbeat = current_time

            # Periodic stale job detection (every 15 seconds)
            if current_time - last_stale_check >= stale_check_interval:
                try:
                    recovered = _detect_and_recover_stale_jobs()
                    if recovered > 0:
                        _append_worker_log(f"recovered {recovered} stale job(s)")
                except Exception as e:
                    _append_worker_log(f"stale job detection error: {e}")
                last_stale_check = current_time

            # Update progress tracking for running jobs
            try:
                _update_job_progress()
            except Exception as e:
                _append_worker_log(f"progress tracking error: {e}")

            # Check running MSF jobs for exploitation success (every iteration)
            try:
                detected = _check_msf_exploitation_success()
                # Only log if something was detected (avoid log spam)
            except Exception as e:
                _append_worker_log(f"MSF success detection error: {e}")

            jobs = _read_jobs()
            queued = [j for j in jobs if j.get("status") == STATUS_QUEUED]
            running = [j for j in jobs if j.get("status") == STATUS_RUNNING]

            # Start next queued job if worker is idle
            if not running and queued:
                queued_sorted = sorted(queued, key=lambda x: x.get("created_at", ""))
                job = queued_sorted[0]
                jid = job.get("id")

                try:
                    run_job(jid)
                except Exception as e:
                    _append_worker_log(f"run_job exception for {jid}: {e}")

            # Process pending chains (one per loop iteration)
            # This runs AFTER job processing, when DB is more likely to be idle
            try:
                processed = _process_pending_chains()
                if processed > 0:
                    _append_worker_log(f"processed {processed} chainable job(s)")
            except Exception as e:
                logger.error(
                    "Chain processing error in worker loop", extra={"error": str(e)}
                )
                _append_worker_log(f"chain processing error: {e}")

            # Sleep before next iteration
            time.sleep(poll_interval)

    except KeyboardInterrupt:
        _append_worker_log("worker: KeyboardInterrupt, shutting down")
    except Exception as e:
        _append_worker_log(f"worker loop stopped with exception: {e}")


def start_worker(detach: bool = True, fg: bool = False):
    if fg:
        worker_loop()
        return

    if detach:
        _ensure_dirs()  # Ensure log directory exists

        # Detect if running as compiled binary or Python script
        exe = sys.executable or ""
        if exe.endswith("main.bin") or "/souleyez/" in exe:
            # Running as Nuitka-compiled binary - use souleyez command
            souleyez_bin = shutil.which("souleyez") or "/usr/bin/souleyez"
            cmd = [souleyez_bin, "worker", "start", "--fg"]
        else:
            # Running as Python script
            python = exe or "python3"
            cmd = [
                python,
                "-u",
                "-c",
                "import sys; from souleyez.engine.background import worker_loop; worker_loop()",
            ]

        subprocess.Popen(
            cmd, stdout=open(WORKER_LOG, "a"), stderr=subprocess.STDOUT, close_fds=True
        )
        _append_worker_log("Started background worker (detached)")
