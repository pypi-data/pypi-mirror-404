# Auto-Chaining Guide

## Overview

SoulEyez's **Auto-Chaining System** automatically triggers follow-up tools and scans based on discovered services, findings, and credentials. This intelligent workflow automation saves time and ensures comprehensive testing without manual intervention.

## Table of Contents

1. [How Auto-Chaining Works](#how-auto-chaining-works)
2. [Chain Rules](#chain-rules)
   - [Understanding Priority](#understanding-priority)
3. [Enabling/Disabling Auto-Chaining](#enablingdisabling-auto-chaining)
4. [Safety Controls](#safety-controls)
5. [Active Orchestration (Approval Mode)](#active-orchestration-approval-mode)
6. [Common Auto-Chain Workflows](#common-auto-chain-workflows)
7. [Monitoring Auto-Chained Jobs](#monitoring-auto-chained-jobs)
8. [Customizing Chain Rules](#customizing-chain-rules)
9. [Troubleshooting](#troubleshooting)

---

## How Auto-Chaining Works

Auto-chaining uses **trigger conditions** and **chain rules** to automatically launch appropriate tools when specific criteria are met.

### The Process

1. **Trigger Event** - A tool completes and discovers services/findings
2. **Rule Matching** - Auto-chain engine checks which rules match the results
3. **Job Creation** - Matching rules generate new background jobs
4. **Execution** - Jobs run automatically with appropriate arguments
5. **Recursive Chaining** - Results can trigger additional chains

### Example Flow

```
Port Scan (nmap)
  → Discovers HTTP on port 80
    → Auto-chains to http_fingerprint (WAF/CDN detection)
      → http_fingerprint completes
        → Auto-chains to nikto + gobuster + nuclei
          → nikto finds admin panel
            → Auto-chains to hydra (brute force)
```

---

## Chain Rules

Chain rules define **when** and **what** to run automatically.

### Rule Structure

Each rule contains:
- **Trigger Tool** - Which tool activates this rule (e.g., `nmap`)
- **Trigger Condition** - What to look for (e.g., `service:http`, `port:445`)
- **Target Tool** - Tool to run next (e.g., `nikto`, `gobuster`)
- **Priority** - Execution order (1-10, higher runs first)
- **Args Template** - Arguments to pass to target tool
- **Target Format** - How the target should be formatted (`ip`, `url`, or `host:port`)

### Understanding Priority

Priority determines the **execution order** when multiple rules match the same trigger event. It does **not** prevent other rules from firing.

#### How Priority Works

When a job completes and triggers multiple chain rules:

1. All matching rules are collected
2. Rules are sorted by priority (highest first)
3. Jobs are queued in that order
4. **All matching rules fire** - priority only controls sequencing

#### Example: nmap finds SMB + SSH + HTTP on a host

| Rule | Condition | Target | Priority | Queue Order |
|------|-----------|--------|----------|-------------|
| SMB Enum | service:smb | crackmapexec | 10 | 1st |
| HTTP Scan | service:http | nuclei | 9 | 2nd |
| SMB Shares | service:smb | enum4linux | 8 | 3rd |
| SSH Creds | service:ssh | msf_auxiliary | 5 | 4th |
| SSH Brute | service:ssh | hydra | 4 | 5th |

All 5 jobs run, but crackmapexec starts first (priority 10) and hydra starts last (priority 4).

#### Priority Guidelines

| Priority | Use Case | Examples |
|----------|----------|----------|
| 10 | Critical/must-run-first | SMB enumeration, domain discovery |
| 8-9 | High-value reconnaissance | Web scanning, service fingerprinting |
| 6-7 | Standard enumeration | Directory brute-force, version detection |
| 4-5 | Credential attacks | Brute-force, password spraying |
| 1-3 | Low priority/slow scans | Full dumps, exhaustive testing |

#### Key Points

- **Priority is about order, not exclusion** - all matching rules execute
- **Higher priority = runs sooner** - critical checks before slow scans
- **Same priority = arbitrary order** - no guaranteed sequence within same level
- **Recon before exploitation** - gather info before attempting attacks

### Built-in Chain Rules

#### Web Service Chains

| Trigger | Condition | Target Tool | Purpose |
|---------|-----------|-------------|---------|
| nmap | `service:http` | http_fingerprint | WAF/CDN/platform detection (runs first) |
| http_fingerprint | `has:services` | nikto | Web vulnerability scanning |
| http_fingerprint | `has:services` | gobuster | Directory/file enumeration |
| http_fingerprint | `has:services` | nuclei | CVE and misconfiguration scanning |
| nmap | `service:https` | sslscan | SSL/TLS configuration testing |

#### Windows/SMB Chains

| Trigger | Condition | Target Tool | Purpose |
|---------|-----------|-------------|---------|
| nmap | `port:445` | crackmapexec | SMB enumeration & exploitation |
| nmap | `port:445` | GetNPUsers | AS-REP Roasting (Kerberos) |
| nmap | `port:135` | MSF endpoint_mapper | RPC endpoint discovery |
| nmap | `port:5985` | crackmapexec | WinRM authentication testing |
| nmap | `port:389` | crackmapexec | LDAP enumeration |

#### Database Chains

| Trigger | Condition | Target Tool | Purpose |
|---------|-----------|-------------|---------|
| nmap | `service:mysql` | sqlmap | SQL injection testing |
| nmap | `port:3306` | hydra | MySQL brute force |
| nmap | `port:5432` | hydra | PostgreSQL brute force |

#### Credential-Based Chains

| Trigger | Condition | Target Tool | Purpose |
|---------|-----------|-------------|---------|
| any | `has:credentials` | crackmapexec | Credential validation across hosts |
| sqlmap | `finding:database_access` | sqlmap | Database enumeration |

---

## Enabling/Disabling Auto-Chaining

### Toggle from Dashboard

Press **`[a]`** in the Command Center dashboard to toggle auto-chaining on/off.

```
Auto-Chaining: ON ✓   [a] Toggle
```

### Check Status

```bash
souleyez dashboard
# Look for "Auto-Chaining: ON" in the header
```

### Via Feature Flags (Code)

```python
from souleyez.feature_flags.features import FeatureFlags, Feature

# Check status
is_enabled = FeatureFlags.is_enabled(Feature.AUTO_CHAINING)

# Disable temporarily
FeatureFlags.set_status(Feature.AUTO_CHAINING, FeatureStatus.DISABLED)
```

---

## Safety Controls

Auto-chaining includes several safety mechanisms to prevent runaway job creation and DoS conditions.

### Rate Limiting

- **Max Jobs per Rule**: Prevents creating 50+ jobs from a single trigger
- **Cooldown Period**: Rules can't re-trigger for the same target within X minutes
- **SQLMap Database Limit**: Enumerates max 5 databases (not all 50+ system DBs)

### Progressive Timeouts

Different phases have different timeout limits:

```python
SQLMAP_TIMEOUTS = {
    'injection_detection': 300,    # 5 minutes
    'database_enumeration': 600,   # 10 minutes
    'table_enumeration': 900,      # 15 minutes
    'full_dump': 1800              # 30 minutes
}
```

### User Controls

- **Manual Approval**: Review suggested chains before execution (optional)
- **Emergency Stop**: Kill all auto-chained jobs with `souleyez jobs kill --all`
- **Disable Auto-Chain**: Press `[a]` in dashboard to stop new chains

### Scope Protection

Auto-chains respect your engagement scope:
- Only targets hosts in current engagement
- Honors exclude lists
- Checks port/service availability before chaining

---

## Active Orchestration (Approval Mode)

Active Orchestration lets you **review and approve** suggested chains before they execute. Instead of auto-running follow-up scans, chains queue for your decision - giving you full control over what runs.

### Why Use Approval Mode?

| Scenario | Recommendation |
|----------|----------------|
| CTF/Lab environment | Auto Mode - speed matters |
| Client engagement | Approval Mode - control & audit trail |
| Noisy tools (hydra, sqlmap) | Approval Mode - review before brute-force |
| Initial reconnaissance | Auto Mode - gather data quickly |
| Post-exploitation | Approval Mode - careful lateral movement |

### Accessing Pending Chains

From the **Main Menu**:
1. Press **`[j]`** to open **Job Queue**
2. Press **`[p]`** to open **Pending Chains - Active Orchestration**

```
┌─────────────────────────────────────────────────────────────────┐
│            PENDING CHAINS - ACTIVE ORCHESTRATION                │
└─────────────────────────────────────────────────────────────────┘

  Mode: APPROVAL MODE
  Chains queue for your review before execution

📊 CHAIN STATISTICS
───────────────────────────────────────────────────────────────────
  ⏳ Pending:   12 chains awaiting your decision
  ✓ Approved:  3 ready to execute
  ✗ Rejected:  5
  ✔ Executed:  28
```

### Menu Options

| Option | Description |
|--------|-------------|
| `[1]` Review & Approve | View pending chains, approve/reject individually or batch |
| `[2]` Approve All | Approve all pending chains at once |
| `[3]` Reject All | Reject all pending chains |
| `[4]` Execute Approved | Run all approved chains now |
| `[5]` Toggle Approval Mode | Switch between Auto Mode and Approval Mode |
| `[6]` View Chain History | See previously executed and rejected chains |

### Enabling Approval Mode

**Option 1: From Pending Chains Menu**
1. Press `[j]` from Main Menu (Job Queue)
2. Press `[p]` (Pending Chains)
3. Select `[5] Toggle Approval Mode`
4. Confirm the change

**Option 2: From Code**
```python
from souleyez.core.tool_chaining import ToolChaining

chaining = ToolChaining()
chaining.set_approval_mode(True)   # Enable approval mode
chaining.set_approval_mode(False)  # Disable (auto mode)

# Check current mode
if chaining.is_approval_mode():
    print("Chains will queue for approval")
```

### Reviewing Pending Chains

When you select `[1] Review & Approve`, you see a paginated list:

```
📋 PENDING CHAINS  Page 1/2
───────────────────────────────────────────────────────────────────
   # │ Tool              │ Target          │ Priority │ Triggered By
───────────────────────────────────────────────────────────────────
   1 │ nuclei            │ 10.0.0.50:80    │        9 │ HTTP service detected
   2 │ gobuster          │ 10.0.0.50:80    │        7 │ HTTP service detected
   3 │ crackmapexec      │ 10.0.0.51       │       10 │ SMB port 445 open
   4 │ hydra             │ 10.0.0.50:22    │        6 │ SSH service detected
───────────────────────────────────────────────────────────────────

  [#] Select chain  [a] Approve all  [r] Reject all  [n] Next  [0] Back
```

**Actions:**
- Enter a number to view chain details and approve/reject
- `[a]` - Approve all visible chains
- `[r]` - Reject all visible chains
- `[s]` - Multi-select mode for batch operations

### Chain Details View

Selecting a chain shows full context:

```
═══════════════════════════════════════════════════════════════════
  CHAIN #3: crackmapexec → 10.0.0.51
═══════════════════════════════════════════════════════════════════

  Status:      ⏳ PENDING
  Priority:    10/10 (Critical)

  Triggered By:
    Job #42 (nmap) found: SMB port 445 open

  Command Preview:
    crackmapexec smb 10.0.0.51 --shares

  Rule Description:
    SMB detected - enumerate shares and check for null sessions

───────────────────────────────────────────────────────────────────
  [a] Approve  [r] Reject  [0] Back
```

### Workflow: Approval Mode in Practice

```
1. Run initial nmap scan
   │
2. nmap completes, triggers chain rules
   │
   ├─ AUTO MODE: Jobs created immediately
   │
   └─ APPROVAL MODE: Chains queued for review
                        │
                        ▼
3. Review pending chains ([j] → [p])
   │
   ├─ Approve safe chains (nuclei, gobuster)
   ├─ Reject noisy chains (hydra brute-force)
   └─ Review suspicious chains individually
   │
4. Execute approved chains
   │
5. Repeat as new chains are suggested
```

### Batch Operations

**Approve/Reject by Category:**
When reviewing chains, use multi-select `[s]` to:
- Select all web scanning chains → Approve
- Select all brute-force chains → Reject
- Select specific targets → Approve/Reject

**Approve All with Confirmation:**
```
⚠️  This will approve 12 pending chains including:
   - 3 brute-force rules (hydra)
   - 2 exploitation rules (msf)

Are you sure? [y/N]:
```

### Chain Storage

Pending chains are stored in `data/chains/pending.json`:

```json
{
  "id": 42,
  "parent_job_id": 15,
  "rule_description": "HTTP detected - web vulnerability scan",
  "tool": "nuclei",
  "target": "10.0.0.50",
  "args": ["-t", "http", "-severity", "critical,high"],
  "priority": 9,
  "status": "pending",
  "created_at": "2025-01-15T10:30:00Z",
  "engagement_id": 1
}
```

### Best Practices for Approval Mode

1. **Start in Auto Mode** for initial recon (port scans, service detection)
2. **Switch to Approval Mode** before:
   - Running brute-force attacks
   - Executing exploits
   - Accessing sensitive systems
3. **Review high-priority chains first** (sorted by priority)
4. **Reject duplicate chains** - same tool/target combinations
5. **Use batch approve** for known-safe operations (nuclei, gobuster)
6. **Keep history** - rejected chains provide audit trail

---

## Common Auto-Chain Workflows

### Web Application Testing

```
1. nmap discovers HTTP/HTTPS
   └─→ http_fingerprint (WAF/CDN/platform detection)

2. http_fingerprint completes
   ├─→ nikto (vulnerability scan)
   ├─→ gobuster (directory brute force)
   ├─→ nuclei (CVE scanning)
   └─→ sslscan (if HTTPS)

3. gobuster finds /admin, /api
   └─→ hydra (login brute force)

4. Form detected with SQL parameter
   └─→ sqlmap (SQL injection testing)
```

### Windows Domain Enumeration

```
1. nmap discovers SMB (445), LDAP (389), WinRM (5985)
   ├─→ crackmapexec SMB enumeration
   ├─→ crackmapexec LDAP queries
   ├─→ GetNPUsers (AS-REP roasting)
   └─→ RPC endpoint mapper

2. Valid credentials found
   └─→ crackmapexec --shares (enumerate shares across all hosts)

3. Domain admin credentials found
   └─→ secretsdump (dump domain secrets)
```

### Database Exploitation

```
1. nmap finds MySQL (3306)
   ├─→ hydra (brute force)
   └─→ sqlmap (injection testing)

2. sqlmap finds SQL injection
   ├─→ Enumerate databases (limit: 5)
   ├─→ Enumerate tables per database
   └─→ Dump sensitive tables (users, credentials)

3. Database credentials found
   └─→ Test credentials on other databases
```

---

## Monitoring Auto-Chained Jobs

### View Active Jobs

```bash
souleyez jobs list
```

Look for jobs with labels like:
- `Auto: nmap` - Triggered by nmap results
- `Auto: crackmapexec` - Credential-based auto-chain
- `Chain: HTTP→nikto` - Service-based chain

### Dashboard View

Jobs panel shows:
```
BACKGROUND JOBS (12 total)
├─ Running: 3
│  ├─ nikto → 10.0.0.50:80 (Auto: nmap)
│  ├─ gobuster → 10.0.0.50:80 (Auto: nmap)
│  └─ crackmapexec → 10.0.0.51 (Auto: credentials)
├─ Pending: 8
└─ Completed: 1
```

### Job Details

```bash
souleyez jobs show <job_id>
```

Shows:
- Trigger reason (e.g., "Auto-triggered by nmap: HTTP service detected")
- Parent job ID (if chained from another job)
- Chain depth (how many levels deep in the chain)

### Quick Access from Job Queue

From the **Job Queue** screen, you can:
- Press **`[?]`** to view this help guide
- Press **`[r]`** to configure chain rules (enable/disable specific triggers)

**💡 TIP:** Type `?` anytime in the Job Queue for instant help!

---

## Customizing Chain Rules

### Adding Custom Rules

Chain rules are defined in `souleyez/core/tool_chaining.py`.

**Example: Add Metasploit chain for RDP**

```python
ChainRule(
    trigger_tool='nmap',
    trigger_condition='port:3389',
    target_tool='msfconsole',
    priority=8,
    args_template=[
        '-x', 'use auxiliary/scanner/rdp/rdp_scanner; '
        'set RHOSTS {target}; run; exit'
    ],
    description='RDP scanner for exposed Remote Desktop'
)
```

### Condition Types

- `service:http` - Match service name
- `port:445` - Match port number
- `service:mysql+http` - Multiple services required
- `finding:any` - Any finding exists
- `finding:sqli` - Specific finding keyword
- `has:credentials` - Credentials discovered

### Placeholder Replacement

Available placeholders in `args_template`:
- `{target}` - IP address or hostname
- `{target_url}` - Full URL with scheme and port (e.g., `http://192.168.1.1:8080`)
- `{port}` - Port number from trigger
- `{service}` - Service name
- `{nuclei_tags}` - Auto-detected technology tags for Nuclei (see below)
- `{domain}` - Domain name (for AD tools)
- `{dc_ip}` - Domain controller IP
- `{subnet}` - /24 subnet of target (e.g., 10.0.0.0/24)

### Target Format

The `target_format` field controls how the target is passed to chained tools:

| Format | Example | Use Case |
|--------|---------|----------|
| `ip` (default) | `192.168.1.1` | Most tools (crackmapexec, nmap, etc.) |
| `url` | `http://192.168.1.1:8080` | Web tools (gobuster, nuclei, nikto) |
| `host:port` | `192.168.1.1:445` | Tools needing explicit port |

**Example:** When http_fingerprint triggers gobuster, the rule has `target_format=url` so gobuster receives the full URL (e.g., `http://192.168.1.1:8080`) instead of just the IP.

### Smart Scanning Features

#### Tech-Based Template Selection (Nuclei)

When Nuclei is chained from nmap, SoulEyez automatically detects the target's technology stack and runs only relevant templates:

| Detected Tech | Nuclei Tags Used |
|---------------|------------------|
| Apache | `apache,cve` |
| nginx | `nginx,cve` |
| WordPress | `wordpress,wp-plugin,cve` |
| Drupal | `drupal,drupalgeddon,cve` |
| PHP | `php,cve` |
| Tomcat | `tomcat,apache,cve` |
| IIS | `iis,microsoft,cve` |

**Before:** Nuclei ran 5000+ templates on every target (~5 min)
**After:** Nuclei runs 100-400 relevant templates (~1-2 min)

If no technology is detected, Nuclei falls back to severity-based scanning (`-severity critical,high`).

#### Pre-Flight Checks (Gobuster)

Before running directory enumeration, Gobuster now performs a pre-flight check:

1. Probes target with a random UUID path (e.g., `/a1b2c3d4-...`)
2. If server returns 403/401/200 for non-existent paths, captures the response length
3. Automatically adds `--exclude-length <size>` to filter false positives

This prevents gobuster from failing on servers with anti-bruteforce protection that return the same response for all paths.

---

## Troubleshooting

### Auto-Chains Not Triggering

**Check:**
1. Auto-chaining is enabled (`[a]` in dashboard)
2. Tool results are being parsed correctly
3. Services are detected in database:
   ```bash
   souleyez services list
   ```
4. Review chain rules match your environment

**Debug:**
```bash
# Enable debug logging
export SOULEYEZ_LOGGING_LEVEL=DEBUG
souleyez dashboard
# Check logs for "Auto-chain rule matched" messages
```

### Too Many Jobs Created

**Solutions:**
1. **Disable auto-chaining temporarily**: Press `[a]` in dashboard
2. **Kill pending jobs**:
   ```bash
   souleyez jobs kill --status pending
   ```
3. **Adjust rate limits**: Edit `MAX_DATABASES_TO_ENUMERATE` in `tool_chaining.py`

### Auto-Chained Jobs Failing

**Common causes:**
- **Tool not installed**: Install missing tool or disable rule
- **Invalid arguments**: Check args_template in chain rule
- **Network issues**: Verify target is reachable
- **Permissions**: Some tools require root/sudo

**Fix:**
```bash
# View failed job logs
souleyez jobs show <failed_job_id>

# Re-run manually with --verbose
souleyez jobs retry <job_id> --verbose
```

### Credential Chains Not Working

**Verify:**
1. Credentials are stored in database:
   ```bash
   souleyez creds list
   ```
2. Credentials have proper metadata (username, password, service)
3. Check parser is extracting credentials correctly

---

## Best Practices

### Start Small

1. **First scan**: Disable auto-chaining
2. **Review results**: Understand what services exist
3. **Enable selectively**: Turn on auto-chaining for specific rules
4. **Monitor jobs**: Watch for unexpected behavior

### Use Scope Files

Define your testing scope to prevent chains from hitting out-of-scope hosts:

```bash
souleyez engagement create "Internal Pentest" \
  --scope 10.0.0.0/24 \
  --exclude 10.0.0.1,10.0.0.254
```

### Review Before Mass Execution

For sensitive environments:
1. Run initial scans with auto-chain OFF
2. Review suggested chains in dashboard
3. Manually trigger important chains first
4. Enable auto-chain for remainder

### Monitor Resource Usage

Auto-chaining can launch many parallel jobs:
- Monitor CPU/memory usage
- Adjust thread limits: `souleyez config set settings.threads 5`
- Use job priorities to control execution order

---

## Related Documentation

- [Worker Management Guide](user-guide/worker-management.md) - Managing background jobs
- [Configuration Guide](CONFIG.md) - Adjusting auto-chain settings
- [Tool Usage Reference](user-guide/tools-reference.md) - Available tools and arguments
- [Pentesting Workflows](user-guide/workflows.md) - End-to-end testing scenarios

---

**Last Updated:** 2026-01-18 | **Version:** 2.2.0
