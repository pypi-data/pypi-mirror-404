# CLI Commands Reference

## Overview

This document provides a complete reference for all souleyez CLI commands, including syntax, options, and examples.

## Command Structure

```bash
souleyez [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGS]
```

### Global Options

| Option | Description |
|--------|-------------|
| `--version` | Show version and exit |
| `--help` | Show help message |

---

## Interactive Commands

### interactive

Launch the interactive tool selection menu.

**Usage:**
```bash
souleyez interactive
```

**Description:**  
Provides a TUI (Text User Interface) for browsing and executing security tools. Recommended for beginners.

**Navigation:**
- Arrow keys: Move up/down
- Enter: Select
- `q`: Quit/Back
- `h`: View hosts
- `s`: View services
- `f`: View findings
- `j`: View jobs
- `c`: View credentials

**Example:**
```bash
souleyez interactive
```

---

### dashboard

Launch live dashboard with real-time monitoring.

**Usage:**
```bash
souleyez dashboard [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--follow, -f` | INTEGER | None | Follow live output of specific job ID |
| `--refresh, -r` | INTEGER | 5 | Refresh interval in seconds |

**Examples:**
```bash
# Default dashboard (5 second refresh)
souleyez dashboard

# Custom refresh rate
souleyez dashboard -r 10

# Follow specific job
souleyez dashboard -f 42
```

**Dashboard Hotkeys:**
- `[h]` - Help menu
- `[q]` - Quit
- `[t]` - Toggle sections
- `[m]` - Main menu
- `[a]` - Toggle auto-chaining

---

## Engagement Management

Engagements organize your penetration testing workspaces.

### engagement create

Create a new engagement.

**Usage:**
```bash
souleyez engagement create NAME [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `NAME` | Yes | Engagement name (unique) |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--description, -d` | TEXT | Engagement description |

**Examples:**
```bash
# Basic engagement
souleyez engagement create "ACME Corp"

# With description
souleyez engagement create "Client XYZ" -d "External network assessment"
```

---

### engagement list

List all engagements with statistics.

**Usage:**
```bash
souleyez engagement list
```

**Output:**
- Asterisk (*) marks current engagement
- Shows hosts, services, findings count
- Displays descriptions

**Example:**
```bash
souleyez engagement list
```

**Output:**
```
================================================================================
ENGAGEMENTS
================================================================================
* ACME Corp          | Hosts:  12 | Services:  45 | Findings:   8
  └─ Internal network security assessment
  Client XYZ         | Hosts:   5 | Services:  18 | Findings:   3
  └─ External network assessment
================================================================================
Current: ACME Corp
```

---

### engagement use

Switch to a different engagement.

**Usage:**
```bash
souleyez engagement use NAME
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `NAME` | Yes | Engagement name to activate |

**Examples:**
```bash
souleyez engagement use "ACME Corp"
souleyez engagement use "Client XYZ"
```

---

### engagement current

Show current engagement details and statistics.

**Usage:**
```bash
souleyez engagement current
```

**Example:**
```bash
souleyez engagement current
```

**Output:**
```
============================================================
Current Engagement: ACME Corp
============================================================
Description: Internal network assessment
Created: 2025-10-29 10:00:00

Statistics:
  Hosts:     12
  Services:  45
  Findings:  8
============================================================
```

---

### engagement delete

Delete an engagement and all associated data.

**Usage:**
```bash
souleyez engagement delete NAME [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `NAME` | Yes | Engagement name to delete |

**Options:**

| Option | Description |
|--------|-------------|
| `--force, -f` | Skip confirmation prompt |

**Examples:**
```bash
# With confirmation
souleyez engagement delete "Old Project"

# Force delete (no confirmation)
souleyez engagement delete "Old Project" -f
```

**Warning:** This permanently deletes:
- All hosts
- All services
- All findings
- All credentials
- All job history

---

## Job Management

Background job execution and monitoring.

### jobs enqueue

Enqueue a background job for execution.

**Usage:**
```bash
souleyez jobs enqueue TOOL TARGET [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `TOOL` | Yes | Tool name (nmap, nikto, gobuster, etc.) |
| `TARGET` | Yes | Target IP, hostname, or URL |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--args, -a` | TEXT | Tool-specific arguments (space-separated) |
| `--label, -l` | TEXT | Descriptive job label |

**Examples:**
```bash
# Basic nmap scan
souleyez jobs enqueue nmap 192.168.1.0/24

# With arguments
souleyez jobs enqueue nmap 192.168.1.100 -a "-sV -p-"

# With label
souleyez jobs enqueue nmap 192.168.1.100 -a "-sS" -l "SYN Scan DC01"

# Web scan
souleyez jobs enqueue nikto http://example.com -l "Web Vuln Scan"

# Directory enumeration
souleyez jobs enqueue gobuster http://example.com -a "dir -w data/wordlists/web_dirs_common.txt"
```

---

### jobs list

List background jobs with status.

**Usage:**
```bash
souleyez jobs list [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--limit, -n` | INTEGER | 20 | Number of jobs to show |
| `--status, -s` | TEXT | None | Filter by status |

**Status Values:**
- `queued` - Waiting to run
- `running` - Currently executing
- `done` - Completed successfully
- `failed` - Completed with errors
- `killed` - Manually terminated

**Examples:**
```bash
# Last 20 jobs (default)
souleyez jobs list

# Last 50 jobs
souleyez jobs list -n 50

# Only running jobs
souleyez jobs list -s running

# Only failed jobs
souleyez jobs list -s failed
```

---

### jobs get

Get detailed information about a job.

**Usage:**
```bash
souleyez jobs get JOB_ID
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `JOB_ID` | Yes | Job ID number |

**Example:**
```bash
souleyez jobs get 42
```

---

### jobs show

Show job details and log output (combined view).

**Usage:**
```bash
souleyez jobs show JOB_ID
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `JOB_ID` | Yes | Job ID number |

**Example:**
```bash
souleyez jobs show 42
```

**Output:**
- Job metadata (tool, target, args, status)
- Last 100 lines of log output

---

### jobs tail

Follow job log output in real-time.

**Usage:**
```bash
souleyez jobs tail JOB_ID [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `JOB_ID` | Yes | Job ID number |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--lines, -n` | INTEGER | 50 | Number of lines to show |
| `--follow, -f` | FLAG | False | Follow output (like tail -f) |

**Examples:**
```bash
# Show last 50 lines
souleyez jobs tail 42

# Show last 100 lines
souleyez jobs tail 42 -n 100

# Follow output (Ctrl+C to stop)
souleyez jobs tail 42 -f
```

---

### jobs kill

Terminate a running job.

**Usage:**
```bash
souleyez jobs kill JOB_ID
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `JOB_ID` | Yes | Job ID number |

**Example:**
```bash
souleyez jobs kill 42
```

---

## Worker Management

Background worker controls job queue processing.

### worker start

Start the background worker.

**Usage:**
```bash
souleyez worker start
```

**Example:**
```bash
souleyez worker start
```

**Note:** Worker must be running for jobs to execute.

---

### worker status

Check worker status.

**Usage:**
```bash
souleyez worker status
```

**Example:**
```bash
souleyez worker status
```

**Output:**
- Worker PID if running
- "Worker not running" if stopped

---

## Data Management

### hosts list

List discovered hosts.

**Usage:**
```bash
souleyez hosts list [OPTIONS]
```

**Examples:**
```bash
souleyez hosts list
```

---

### hosts show

Show detailed host information.

**Usage:**
```bash
souleyez hosts show IP_ADDRESS
```

**Example:**
```bash
souleyez hosts show 192.168.1.100
```

---

### services list

List discovered services.

**Usage:**
```bash
souleyez services list [OPTIONS]
```

**Examples:**
```bash
# All services
souleyez services list

# Filter by port
souleyez services list --port 80

# Filter by host
souleyez services list --host 192.168.1.100
```

---

### findings list

List security findings.

**Usage:**
```bash
souleyez findings list [OPTIONS]
```

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--severity, -s` | TEXT | Filter by severity (critical, high, medium, low, info) |

**Examples:**
```bash
# All findings
souleyez findings list

# Critical only
souleyez findings list -s critical

# High severity
souleyez findings list -s high
```

---

### findings show

Show detailed finding information.

**Usage:**
```bash
souleyez findings show FINDING_ID
```

---

### findings summary

Show findings summary by severity.

**Usage:**
```bash
souleyez findings summary
```

---

### creds list

List discovered credentials.

**Usage:**
```bash
souleyez creds list
```

**Example:**
```bash
souleyez creds list
```

**Note:** If encryption is enabled, you'll be prompted for master password.

---

### creds stats

Show credential statistics.

**Usage:**
```bash
souleyez creds stats
```

---

### osint list

List OSINT data (emails, domains, etc.).

**Usage:**
```bash
souleyez osint list
```

---

### osint summary

Show OSINT summary statistics.

**Usage:**
```bash
souleyez osint summary
```

---

### paths list

List discovered web paths/directories.

**Usage:**
```bash
souleyez paths list
```

---

### paths summary

Show web paths summary.

**Usage:**
```bash
souleyez paths summary
```

---

## Database Management

### db migrate

Run database migrations.

**Usage:**
```bash
souleyez db migrate
```

---

### db status

Show database migration status.

**Usage:**
```bash
souleyez db status
```

---

## Reporting

### report generate

Generate penetration test report.

**Usage:**
```bash
souleyez report generate TITLE [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `TITLE` | Yes | Report title |

**Examples:**
```bash
souleyez report generate "ACME Corp Final Report"
```

**Output:** Report saved to `reports/` directory

---

### report list

List generated reports.

**Usage:**
```bash
souleyez report list
```

---

## Data Import

### import-data msf

Import data from Metasploit Framework.

**Usage:**
```bash
souleyez import-data msf WORKSPACE
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `WORKSPACE` | Yes | MSF workspace name |

**Example:**
```bash
souleyez import-data msf client_pentest
```

---

## Plugin Management

### plugins

List available plugins.

**Usage:**
```bash
souleyez plugins
```

**Example:**
```bash
souleyez plugins
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SOULEYEZ_DEBUG` | Enable debug logging (set to 1) |
| `SOULEYEZ_DB` | Override database path |

---

## Common Patterns

### Quick Network Scan
```bash
souleyez engagement create "Quick Scan"
souleyez engagement use "Quick Scan"
souleyez jobs enqueue nmap 192.168.1.0/24 -a "-sn" -l "Discovery"
souleyez dashboard
```

### Web Application Testing
```bash
souleyez jobs enqueue nikto http://example.com -l "Nikto Scan"
souleyez jobs enqueue gobuster http://example.com -a "dir -w data/wordlists/web_dirs_common.txt" -l "Dir Enum"
souleyez findings list
```

### View All Data for Engagement
```bash
souleyez hosts list
souleyez services list
souleyez findings list
souleyez creds list
souleyez report generate "Final Report"
```

---

## Getting Help

For any command, append `--help`:

```bash
souleyez --help
souleyez engagement --help
souleyez jobs --help
souleyez jobs enqueue --help
```

---

## See Also

- [Getting Started Guide](../user-guide/getting-started.md)
- [Engagement API Reference](engagement-api.md)
- [Parser Formats](parser-formats.md)
- [Integration Guide](integration-guide.md)
