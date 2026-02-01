# Worker Management Guide

**Purpose:** Understanding and managing SoulEyez's background job system

**Last Updated:** 2025-11-18

---

## Overview

SoulEyez uses a background worker system to run scans and tools without blocking your terminal. This guide explains how to manage workers, troubleshoot issues, and monitor job execution.

---

## Table of Contents

1. [Worker Architecture](#worker-architecture)
2. [Starting & Stopping Workers](#starting--stopping-workers)
3. [Monitoring Jobs](#monitoring-jobs)
4. [Job States](#job-states)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

---

## Worker Architecture

### How It Works

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│              │       │              │       │              │
│  User/CLI    │  ───► │  Job Queue   │  ───► │    Worker    │
│              │       │  (Database)  │       │   (Process)  │
└──────────────┘       └──────────────┘       └──────────────┘
                              │                       │
                              │                       │
                              ▼                       ▼
                       ┌──────────────┐       ┌──────────────┐
                       │              │       │              │
                       │  Job Status  │       │   Tool       │
                       │   Updates    │       │  Execution   │
                       │              │       │              │
                       └──────────────┘       └──────────────┘
```

**Components:**
- **Job Queue** - SQLite database table storing all jobs
- **Worker Process** - Background Python process that executes jobs
- **Job States** - pending → running → done/error/killed
- **Results** - Parsed output stored in database

---

## Starting & Stopping Workers

### Start Worker

**Foreground (Interactive):**
```bash
souleyez worker start --fg
```
- Runs in current terminal
- Shows real-time output
- Ctrl+C stops the worker
- **Use for:** Debugging, watching execution

**Background (Daemon):**
```bash
souleyez worker start
```
- Runs in background
- Continues after closing terminal
- **Use for:** Production scans, long-running jobs

---

### Check Worker Status

```bash
souleyez worker status
```

**Output:**
```
Worker Status: RUNNING
PID: 12345
Uptime: 2h 34m
Jobs processed: 47
Current job: nmap 10.0.0.82 (ID: 23)
```

**States:**
- `RUNNING` - Worker is active and processing jobs
- `STOPPED` - No worker is running
- `STALE` - Worker PID exists but not responding (needs cleanup)

---

### Stop Worker

```bash
souleyez worker stop
```

**What happens:**
1. Sends SIGTERM to worker process
2. Current job finishes (graceful shutdown)
3. Pending jobs remain in queue
4. Worker can be restarted later

**Force stop (if needed):**
```bash
kill -9 <PID>  # Use PID from 'souleyez worker status'
```

---

## Monitoring Jobs

### List All Jobs

```bash
# From CLI
souleyez jobs list

# From interactive menu
souleyez interactive → [j] Jobs
```

**Example Output:**
```
 ID     Status     Tool        Target         Label         Created
────────────────────────────────────────────────────────────────
 5      ✓ done     nmap        10.0.0.82      FULL          2025-11-05T05:43
 4      ⟳ running  gobuster    10.0.0.28      WEB           2025-11-05T05:50
 3      ○ pending  nikto       10.0.0.28      VULN          2025-11-05T05:51
────────────────────────────────────────────────────────────────
```

---

### View Job Details

```bash
# From CLI
souleyez jobs get <job_id>

# From interactive menu
souleyez interactive → [j] Jobs → Enter job ID
```

**Shows:**
- Full command executed
- Start/end timestamps
- Exit code
- Output logs
- Parsed results summary

---

### Follow Job Output (Live)

```bash
souleyez jobs tail <job_id>
```

**Real-time log streaming:**
```
[2025-11-05 05:43:12] Starting nmap scan...
[2025-11-05 05:43:15] Discovered host: 10.0.0.82 (up)
[2025-11-05 05:43:18] Port 22/tcp open (ssh)
[2025-11-05 05:43:20] Port 80/tcp open (http)
[2025-11-05 05:43:25] Scan complete (13s elapsed)
```

---

### Dashboard Monitoring

```bash
souleyez dashboard
```

**Shows:**
- Active jobs section (running/pending)
- Job progress indicators
- Auto-refresh every 15s
- Press `[j]` to jump to jobs view

---

## Job States

### State Lifecycle

```
   ┌─────────┐
   │ pending │  ← Job created, waiting for worker
   └────┬────┘
        │
        ▼
   ┌─────────┐
   │ running │  ← Worker executing the job
   └────┬────┘
        │
        ├──────┐──────┐
        ▼      ▼      ▼
   ┌────┴─┐ ┌──┴──┐ ┌─┴──┐
   │ done │ │error│ │kill│  ← Final states
   └──────┘ └─────┘ └────┘
```

---

### State Descriptions

| State | Icon | Description | Actions |
|-------|------|-------------|---------|
| **pending** | ○ | Job queued, waiting for worker | Wait or kill |
| **running** | ⟳ | Worker is executing the job | Monitor or kill |
| **done** | ✓ | Job completed successfully | View results |
| **error** | ✗ | Job failed (exit code != 0) | Check logs, retry |
| **killed** | ⊗ | Job was manually terminated | Check why |

---

## Troubleshooting

### Problem: Worker Not Processing Jobs

**Symptoms:**
- Jobs stuck in `pending` state
- `souleyez worker status` shows `STOPPED`

**Solution:**
```bash
# Start the worker
souleyez worker start

# Or start in foreground to see errors
souleyez worker start --fg
```

---

### Problem: Worker Crashed

**Symptoms:**
- `worker status` shows `STALE`
- Worker was running but now unresponsive

**Solution:**
```bash
# 1. Check if process still exists
ps aux | grep "souleyez worker"

# 2. Force kill if needed
kill -9 <PID>

# 3. Clean up stale state
rm -f ~/.souleyez/worker.pid

# 4. Restart worker
souleyez worker start
```

---

### Problem: Jobs Failing with Errors

**Symptoms:**
- Jobs show `error` state
- Tools not producing expected output

**Troubleshooting Steps:**

1. **Check job logs:**
   ```bash
   souleyez jobs get <job_id>
   ```

2. **Common causes:**
   - Missing tool dependency (install via `apt-get`)
   - Invalid target format
   - Permission issues (need sudo?)
   - Network connectivity

3. **Test tool manually:**
   ```bash
   # Run the exact command from job details
   nmap -sV 10.0.0.82
   ```

4. **Check dependencies:**
   ```bash
   souleyez doctor  # If this command exists
   # Or manually check:
   which nmap gobuster nikto hydra
   ```

---

### Problem: Jobs Stuck in Running State

**Symptoms:**
- Job shows `running` for abnormally long time
- No progress visible

**Solution:**

1. **Check if job is actually running:**
   ```bash
   # Look for tool process
   ps aux | grep nmap  # or gobuster, nikto, etc.
   ```

2. **Kill stuck job:**
   ```bash
   souleyez jobs kill <job_id>
   ```

3. **If that doesn't work, force kill:**
   ```bash
   # Find the PID
   ps aux | grep <tool_name>

   # Kill it
   kill -9 <PID>

   # Mark job as killed in database
   souleyez jobs kill <job_id>
   ```

---

### Problem: Too Many Jobs in Queue

**Symptoms:**
- Hundreds of pending jobs
- Worker overwhelmed

**Solution:**

1. **Purge completed jobs:**
   ```bash
   souleyez jobs purge
   ```

2. **Kill all pending jobs:**
   ```bash
   # From interactive menu
   souleyez interactive → [j] Jobs → [p] Purge
   ```

3. **Clear specific jobs:**
   ```bash
   souleyez jobs kill <job_id>
   souleyez jobs kill <job_id>
   ...
   ```

---

## Best Practices

### ✅ Do's

**1. Start worker at beginning of engagement:**
```bash
souleyez engagement create "my-test"
souleyez worker start  # ← Start this first!
```

**2. Monitor long-running scans:**
```bash
# Use dashboard for overview
souleyez dashboard

# Or tail specific job
souleyez jobs tail <job_id>
```

**3. Use labels for organization:**
```bash
souleyez jobs enqueue nmap 10.0.0.82 --label "INITIAL_RECON"
souleyez jobs enqueue gobuster 10.0.0.82 --label "WEB_ENUM"
```

**4. Purge old jobs regularly:**
```bash
# At end of engagement
souleyez jobs purge
```

**5. Stop worker when done:**
```bash
# Clean shutdown
souleyez worker stop
```

---

### ❌ Don'ts

**1. Don't run multiple workers simultaneously**
- Only ONE worker per system
- Multiple workers will conflict

**2. Don't kill worker during critical jobs**
- Let current job finish
- Use `souleyez worker stop` (graceful)
- Not `kill -9` (forceful)

**3. Don't ignore error states**
- Check logs: `souleyez jobs get <job_id>`
- Fix underlying issue
- Retry if needed

**4. Don't queue duplicate jobs**
- Check existing jobs first: `souleyez jobs list`
- Worker will run them sequentially
- Wastes time scanning same target twice

**5. Don't forget to start worker after reboot**
- Worker is NOT a system service
- Must be manually started
- Consider adding to startup scripts if needed

---

## Advanced Topics

### Running Worker as System Service

**Create systemd service** (optional, for production):

```bash
# /etc/systemd/system/souleyez-worker.service
[Unit]
Description=SoulEyez Background Worker
After=network.target

[Service]
Type=simple
User=pentester
WorkingDirectory=/home/pentester
ExecStart=/usr/local/bin/souleyez worker start --fg
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable souleyez-worker
sudo systemctl start souleyez-worker
```

---

### Job Priority (Future Feature)

Currently, jobs are processed in FIFO order (first in, first out). Future versions may support:
- Priority levels (high/medium/low)
- Job dependencies (Job B waits for Job A)
- Parallel execution (multiple workers)

---

## Quick Reference

### Essential Commands

```bash
# Worker control
souleyez worker start           # Start worker (background)
souleyez worker start --fg      # Start worker (foreground)
souleyez worker status          # Check worker status
souleyez worker stop            # Stop worker gracefully

# Job management
souleyez jobs list              # List all jobs
souleyez jobs get <id>          # View job details
souleyez jobs tail <id>         # Follow job output
souleyez jobs kill <id>         # Kill specific job
souleyez jobs purge             # Delete done/error/killed jobs

# Monitoring
souleyez dashboard              # Real-time dashboard
souleyez interactive            # Interactive menu ([j] for jobs)
```

---

### Keyboard Shortcuts (Interactive Menu)

```
[j] - Jump to jobs view
[#] - Enter job ID to view details
[p] - Purge completed jobs
[a] - View all engagements
[0] - Back to main menu
[q] - Quit
```

---

## Getting Help

**Documentation:**
- Troubleshooting Guide: `docs/user-guide/troubleshooting.md`
- Getting Started: `docs/user-guide/getting-started.md`
- Auto-Chaining: `docs/AUTO_CHAINING.md`

**Common Issues:**
- Tool not found → Install dependencies
- Permission denied → Run with sudo or check file permissions
- Jobs stuck → Kill and restart worker

**Still stuck?**
- Check logs in `~/.souleyez/logs/`
- Report issue on GitHub: https://github.com/cyber-soul-security/SoulEyez/issues

---

**Last Updated:** 2025-11-18
**Version:** 1.0
