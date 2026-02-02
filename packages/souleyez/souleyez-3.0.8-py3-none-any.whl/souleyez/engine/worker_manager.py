#!/usr/bin/env python3
"""
Worker health check and management utilities
"""

import time
from typing import Any, Dict, Optional, Tuple

import psutil


def is_worker_running() -> Tuple[bool, Optional[int]]:
    """
    Check if background worker is running.

    Returns: (is_running, pid)
    """
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline", [])
            if not cmdline:
                continue
            cmdline_str = " ".join(str(arg) for arg in cmdline)
            # Check for Python-based worker (dev mode)
            if (
                "souleyez.engine.background" in cmdline_str
                and "worker_loop" in cmdline_str
            ):
                return True, proc.info["pid"]
            # Check for binary-based worker (compiled mode)
            if (
                "souleyez" in cmdline_str
                and "worker" in cmdline_str
                and "start" in cmdline_str
            ):
                return True, proc.info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False, None


def is_worker_healthy() -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Check if background worker is running AND healthy (responding).

    Uses heartbeat file to verify worker is actively processing.
    A worker process may exist but be frozen/hung - heartbeat detects this.

    Returns: (is_healthy, pid, issue)
        - is_healthy: True if worker is running and heartbeat is fresh
        - pid: Worker PID if found, None otherwise
        - issue: Description of issue if not healthy, None otherwise
    """
    from souleyez.engine.background import HEARTBEAT_STALE_THRESHOLD, get_heartbeat_age

    is_running, pid = is_worker_running()

    if not is_running:
        return False, None, "Worker process not found"

    # Check heartbeat
    heartbeat_age = get_heartbeat_age()

    if heartbeat_age is None:
        # No heartbeat file - worker may have just started
        return True, pid, "No heartbeat yet (may be starting)"

    if heartbeat_age > HEARTBEAT_STALE_THRESHOLD:
        return (
            False,
            pid,
            f"Heartbeat stale ({int(heartbeat_age)}s old, threshold: {HEARTBEAT_STALE_THRESHOLD}s)",
        )

    return True, pid, None


def start_worker_if_needed() -> bool:
    """
    Start worker if not running
    Returns: True if worker was started, False if already running
    """
    is_running, pid = is_worker_running()

    if is_running:
        return False

    # Start the worker
    from souleyez.engine.background import start_worker

    start_worker(detach=True)
    time.sleep(1)  # Give it a moment to start

    # Verify it started
    is_running, new_pid = is_worker_running()
    if is_running:
        return True
    else:
        raise RuntimeError("Failed to start background worker")


def stop_worker(pid: int) -> bool:
    """
    Stop the worker process
    """
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=5)
        return True
    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
        try:
            proc.kill()
            return True
        except BaseException:
            return False


def restart_worker() -> bool:
    """
    Restart the background worker
    Returns: True if successful
    """
    is_running, pid = is_worker_running()

    if is_running and pid:
        stop_worker(pid)
        time.sleep(1)

    return start_worker_if_needed()


def get_worker_status() -> dict:
    """
    Get comprehensive worker status
    """
    is_running, pid = is_worker_running()

    status = {
        "running": is_running,
        "pid": pid,
        "uptime": None,
        "cpu_percent": None,
        "memory_mb": None,
    }

    if is_running and pid:
        try:
            proc = psutil.Process(pid)
            status["uptime"] = int(time.time() - proc.create_time())
            status["cpu_percent"] = proc.cpu_percent(interval=0.1)
            status["memory_mb"] = proc.memory_info().rss / 1024 / 1024
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return status


def get_worker_health() -> Dict[str, Any]:
    """
    Get detailed worker health status including heartbeat info.

    Returns dict with:
        - running: Whether worker process exists
        - healthy: Whether worker is running AND responsive
        - pid: Worker PID if running
        - uptime: Seconds since worker started
        - heartbeat_age: Seconds since last heartbeat
        - heartbeat_stale: Whether heartbeat is stale
        - issue: Description of any health issue
        - cpu_percent: CPU usage percentage
        - memory_mb: Memory usage in MB
    """
    from souleyez.engine.background import HEARTBEAT_STALE_THRESHOLD, get_heartbeat_age

    is_running, pid = is_worker_running()
    heartbeat_age = get_heartbeat_age()

    health = {
        "running": is_running,
        "healthy": False,
        "pid": pid,
        "uptime": None,
        "heartbeat_age": heartbeat_age,
        "heartbeat_stale": heartbeat_age is None
        or heartbeat_age > HEARTBEAT_STALE_THRESHOLD,
        "issue": None,
        "cpu_percent": None,
        "memory_mb": None,
    }

    if not is_running:
        health["issue"] = "Worker process not found"
        return health

    # Get process info
    try:
        proc = psutil.Process(pid)
        health["uptime"] = int(time.time() - proc.create_time())
        health["cpu_percent"] = proc.cpu_percent(interval=0.1)
        health["memory_mb"] = round(proc.memory_info().rss / 1024 / 1024, 1)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        health["issue"] = "Cannot access worker process"
        return health

    # Check heartbeat
    if heartbeat_age is None:
        health["issue"] = "No heartbeat yet (worker may be starting)"
        health["healthy"] = True  # Give benefit of doubt for new workers
    elif heartbeat_age > HEARTBEAT_STALE_THRESHOLD:
        health["issue"] = f"Worker unresponsive (heartbeat {int(heartbeat_age)}s old)"
        health["healthy"] = False
    else:
        health["healthy"] = True

    return health
