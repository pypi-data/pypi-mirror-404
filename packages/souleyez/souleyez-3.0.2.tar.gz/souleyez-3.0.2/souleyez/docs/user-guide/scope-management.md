# Engagement Scope Management Guide

**Version:** 2.27.0
**Last Updated:** January 2026

SoulEyez includes a comprehensive scope validation system to ensure scanning activities remain within authorized boundaries. This guide covers scope definitions, enforcement modes, validation behavior, and audit logging.

---

## Table of Contents

1. [Overview](#overview)
2. [Why Scope Management?](#why-scope-management)
3. [Getting Started](#getting-started)
4. [Scope Entry Types](#scope-entry-types)
5. [Enforcement Modes](#enforcement-modes)
6. [Managing Scope](#managing-scope)
7. [Interactive UI](#interactive-ui)
8. [CLI Commands](#cli-commands)
9. [Host Scope Status](#host-scope-status)
10. [Audit Trail](#audit-trail)
11. [Tool Chaining Behavior](#tool-chaining-behavior)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

---

## Overview

SoulEyez Scope Management provides:

- **Structured scope definitions** (CIDR ranges, domains, URLs, hostnames)
- **Three enforcement modes** (Off, Warn, Block)
- **Automatic target validation** before job execution
- **Exclusion rules** for explicitly denied targets
- **Host scope status tracking** for visual indicators
- **Complete audit trail** for compliance
- **Non-breaking defaults** for existing engagements

---

## Why Scope Management?

During penetration testing engagements, it's critical to stay within authorized boundaries. Scanning unauthorized targets can lead to:

- **Legal liability** for unauthorized access
- **Contract violations** with clients
- **Accidental impact** on production systems
- **Compliance failures** in regulated industries

SoulEyez Scope Management prevents these issues by:

1. **Validating every target** before scanning
2. **Blocking or warning** on out-of-scope targets
3. **Automatically handling** tool chaining boundaries
4. **Creating audit trails** for compliance documentation

---

## Getting Started

### Default Behavior

By default, **no scope validation occurs**. This ensures backward compatibility:

- Existing engagements work unchanged
- New engagements without defined scope are fully permissive
- Scope validation only activates when you explicitly add scope entries

### Quick Setup

```bash
# 1. Add scope entries
$ souleyez scope add "Client Pentest" --cidr 192.168.1.0/24
$ souleyez scope add "Client Pentest" --domain "*.example.com"

# 2. Set enforcement mode
$ souleyez scope enforcement "Client Pentest" warn

# 3. Test a target
$ souleyez scope validate "Client Pentest" 192.168.1.100
```

---

## Scope Entry Types

### CIDR Ranges

Define network ranges using CIDR notation:

```bash
# Single subnet
$ souleyez scope add "Engagement" --cidr 192.168.1.0/24

# Large network
$ souleyez scope add "Engagement" --cidr 10.0.0.0/8

# Single IP (as /32)
$ souleyez scope add "Engagement" --cidr 192.168.1.100/32
```

**Matching behavior:**
- IP `192.168.1.50` matches `192.168.1.0/24`
- IP `192.168.2.50` does NOT match `192.168.1.0/24`

### Domains

Define domain patterns with optional wildcards:

```bash
# Wildcard subdomain
$ souleyez scope add "Engagement" --domain "*.example.com"

# Exact domain
$ souleyez scope add "Engagement" --domain "example.com"
```

**Matching behavior:**
- `*.example.com` matches `app.example.com`, `deep.sub.example.com`, `example.com`
- `example.com` matches only `example.com` exactly
- Matching is case-insensitive

### URLs

Define specific URL prefixes:

```bash
# Web application
$ souleyez scope add "Engagement" --url "https://app.example.com"

# API endpoint
$ souleyez scope add "Engagement" --url "https://api.example.com/v2"
```

**Matching behavior:**
- Host is extracted for validation
- Port numbers are handled correctly
- URLs like `https://app.example.com/path/to/resource` match the scope

### Hostnames

Define exact hostnames or IP addresses:

```bash
# Exact hostname
$ souleyez scope add "Engagement" --hostname "webserver.local"

# Specific IP
$ souleyez scope add "Engagement" --hostname "192.168.1.100"
```

---

## Enforcement Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| **off** | No validation (default) | Development, testing, legacy engagements |
| **warn** | Allow but log warning | Production with monitoring, gradual rollout |
| **block** | Reject out-of-scope targets | Production, strict compliance requirements |

### Setting Enforcement Mode

```bash
# Turn off validation (default)
$ souleyez scope enforcement "Engagement" off

# Enable warnings only
$ souleyez scope enforcement "Engagement" warn

# Enable strict blocking
$ souleyez scope enforcement "Engagement" block
```

### How Each Mode Works

**Off Mode:**
- All targets allowed
- No warnings added to jobs
- No scope validation occurs

**Warn Mode:**
- All targets allowed
- Warning added to job metadata
- Logged to audit trail
- Visible in job details

**Block Mode:**
- In-scope targets allowed
- Out-of-scope targets rejected with error
- Job creation prevented
- Logged to audit trail

---

## Managing Scope

### Adding Scope Entries

```bash
# Add with description
$ souleyez scope add "Engagement" --cidr 192.168.1.0/24 --desc "Corporate LAN"

# Add exclusion (deny rule)
$ souleyez scope add "Engagement" --cidr 192.168.1.0/24 --exclude --desc "Production server"

# Multiple entries
$ souleyez scope add "Engagement" --cidr 10.0.0.0/8
$ souleyez scope add "Engagement" --domain "*.target.com"
$ souleyez scope add "Engagement" --url "https://webapp.target.com"
```

### Listing Scope

```bash
$ souleyez scope list "Engagement"

Engagement Scope: Client Pentest
Enforcement Mode: block

ID  Type      Value                  Excluded  Description
──  ────      ─────                  ────────  ───────────
1   cidr      192.168.1.0/24         No        Corporate LAN
2   domain    *.example.com          No        Target domain
3   hostname  192.168.1.1            Yes       Gateway - excluded
```

### Removing Scope Entries

```bash
# Remove by ID
$ souleyez scope remove "Engagement" 3
Removed scope entry 3
```

### Testing Validation

Before running scans, test if targets are in scope:

```bash
$ souleyez scope validate "Engagement" 192.168.1.100

Target: 192.168.1.100
Result: IN SCOPE
Matched: cidr 192.168.1.0/24 (Corporate LAN)

$ souleyez scope validate "Engagement" 10.0.0.50

Target: 10.0.0.50
Result: OUT OF SCOPE
Reason: Target '10.0.0.50' does not match any scope entry
```

---

## Interactive UI

Access scope management from the engagement menu:

```
📊 Engagement Management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[i] Info        [h] Hosts        [f] Findings
[c] Credentials [j] Jobs         [r] Reports
[s] Scope       [a] Attack Surface
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[b] Back to menu
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Select option:
```

### Scope Management Menu

```
🎯 Scope Management: Client Pentest
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Enforcement Mode: block

Current Scope Entries:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID  Type      Value                  Excluded  Description
──  ────      ─────                  ────────  ───────────
1   cidr      192.168.1.0/24                   Corporate LAN
2   domain    *.example.com                    Target domain
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[a] Add scope entry     [r] Remove entry
[e] Change enforcement  [t] Test target
[h] Revalidate hosts    [l] View log
[b] Back

Select option:
```

### Host Scope Indicators

In the hosts view, scope status is shown with indicators:

```
📡 Discovered Hosts (12 total)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    IP              Hostname           OS              Status
──  ──              ────────           ──              ──────
[S] 192.168.1.10    webserver.local    Ubuntu 22.04    up
[S] 192.168.1.11    dbserver.local     Ubuntu 22.04    up
[!] 10.0.0.50       external.other     Unknown         up
[?] 172.16.0.1      router.internal    -               up
```

| Indicator | Meaning |
|-----------|---------|
| `[S]` | In scope - target matches scope entries |
| `[!]` | Out of scope - target outside defined scope |
| `[?]` | Unknown - no scope defined or not yet validated |

---

## CLI Commands

### Command Reference

```bash
# Add scope entries
souleyez scope add <engagement> --cidr <range>
souleyez scope add <engagement> --domain <pattern>
souleyez scope add <engagement> --url <url>
souleyez scope add <engagement> --hostname <host>
souleyez scope add <engagement> --exclude --cidr <range>  # Exclusion

# Options for add:
#   --desc TEXT     Optional description
#   --exclude       Mark as exclusion (deny rule)

# List scope
souleyez scope list <engagement>

# Remove scope entry
souleyez scope remove <engagement> <scope_id>

# Set enforcement mode
souleyez scope enforcement <engagement> [off|warn|block]

# Validate a target
souleyez scope validate <engagement> <target>

# Revalidate all hosts
souleyez scope revalidate <engagement>

# View validation log
souleyez scope log <engagement> [--limit N] [--action ACTION]
```

### Examples

```bash
# Complete scope setup for a pentest
$ souleyez scope add "Client Pentest" --cidr 10.10.0.0/16 --desc "Client internal network"
$ souleyez scope add "Client Pentest" --domain "*.client.com" --desc "Client web properties"
$ souleyez scope add "Client Pentest" --cidr 10.10.1.0/24 --exclude --desc "Production - do not scan"
$ souleyez scope enforcement "Client Pentest" block

# View what's configured
$ souleyez scope list "Client Pentest"

# Test before scanning
$ souleyez scope validate "Client Pentest" 10.10.2.50
$ souleyez scope validate "Client Pentest" 10.10.1.50  # Should fail

# Check audit log
$ souleyez scope log "Client Pentest" --limit 20
```

---

## Host Scope Status

When hosts are discovered or imported, they're automatically checked against the scope.

### Status Values

| Status | Meaning |
|--------|---------|
| `in_scope` | Host matches a scope entry |
| `out_of_scope` | Host doesn't match any scope entry |
| `unknown` | No scope defined for engagement |

### Revalidating Hosts

After modifying scope entries, revalidate all hosts:

```bash
$ souleyez scope revalidate "Client Pentest"

Revalidating hosts for: Client Pentest
Updated: 15 hosts
  In scope: 12
  Out of scope: 3
```

Or in the interactive UI:

```
[h] Revalidate hosts

Revalidating 15 hosts against current scope...

Results:
  Updated: 15
  In scope: 12
  Out of scope: 3
```

---

## Audit Trail

Every scope validation decision is logged for compliance.

### Viewing the Log

```bash
$ souleyez scope log "Client Pentest"

Validation Log: Client Pentest (Last 50 entries)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Time                 Target           Result       Action   Job
────                 ──────           ──────       ──────   ───
2026-01-09 10:30:15  192.168.1.100    in_scope     allowed  142
2026-01-09 10:28:03  10.0.0.50        out_of_scope blocked  -
2026-01-09 10:25:41  app.example.com  in_scope     allowed  141
```

### Filtering the Log

```bash
# Show only blocked entries
$ souleyez scope log "Client Pentest" --action blocked

# Limit results
$ souleyez scope log "Client Pentest" --limit 100
```

### Log Entry Details

Each log entry includes:

| Field | Description |
|-------|-------------|
| `engagement_id` | Which engagement |
| `job_id` | Associated job (if any) |
| `target` | Target that was validated |
| `validation_result` | `in_scope`, `out_of_scope`, `no_scope_defined` |
| `action_taken` | `allowed`, `blocked`, `warned` |
| `matched_scope_id` | Which scope entry matched (if any) |
| `user_id` | User who initiated the action |
| `created_at` | Timestamp |

---

## Tool Chaining Behavior

When auto-chaining discovers new targets, scope validation is applied automatically.

### How It Works

1. Parent job discovers new targets (e.g., Nmap finds hosts)
2. Chain rules attempt to create child jobs
3. **Each target is validated against scope**
4. Out-of-scope targets are silently skipped
5. In-scope targets proceed normally

### Example Output

```
🔗 Auto-chaining from nmap...
  ✓ Enqueued: gobuster → 192.168.1.10
  ✓ Enqueued: gobuster → 192.168.1.11
  ⚠️ Skipped (out of scope): 10.0.0.50
  ✓ Enqueued: nikto → 192.168.1.10
```

### Key Behaviors

- **Silent skip**: Out-of-scope targets don't cause errors
- **Chain continues**: Other targets in the chain still process
- **Logged**: Skipped targets are logged in the audit trail
- **Parent unaffected**: Parent job completes normally

---

## Best Practices

### Before Starting an Engagement

1. **Define scope before scanning**
   ```bash
   $ souleyez scope add "Engagement" --cidr 10.0.0.0/8
   $ souleyez scope enforcement "Engagement" warn  # Start with warn
   ```

2. **Document scope sources**
   ```bash
   $ souleyez scope add "Engagement" --cidr 10.0.0.0/8 --desc "Per SOW Section 2.1"
   ```

3. **Add exclusions explicitly**
   ```bash
   $ souleyez scope add "Engagement" --cidr 10.0.1.0/24 --exclude --desc "Production - client request"
   ```

### During the Engagement

1. **Test before large scans**
   ```bash
   $ souleyez scope validate "Engagement" 10.0.5.1
   ```

2. **Review warnings regularly**
   ```bash
   $ souleyez scope log "Engagement" --action warned
   ```

3. **Upgrade to block mode when confident**
   ```bash
   $ souleyez scope enforcement "Engagement" block
   ```

### For Compliance

1. **Export audit logs** for client reports
   ```bash
   $ souleyez scope log "Engagement" --limit 1000
   ```

2. **Include scope in deliverables**
   - Document what was in scope
   - Document what was excluded
   - Reference enforcement mode used

3. **Use block mode** for regulated industries
   - Healthcare (HIPAA)
   - Finance (PCI-DSS)
   - Government (FedRAMP)

### Enforcement Mode Guidelines

| Scenario | Recommended Mode |
|----------|------------------|
| Learning/testing the feature | `off` |
| First engagement with scope | `warn` |
| Established workflow | `block` |
| Compliance-sensitive | `block` |
| Bug bounty (broad scope) | `warn` |
| Internal red team | `block` |

---

## Troubleshooting

### "Target is out of scope"

The target doesn't match any scope entry and enforcement is set to `block`.

**Solutions:**
1. Add the target to scope:
   ```bash
   $ souleyez scope add "Engagement" --cidr 10.0.0.0/24
   ```

2. Check existing scope:
   ```bash
   $ souleyez scope list "Engagement"
   ```

3. Temporarily switch to warn mode:
   ```bash
   $ souleyez scope enforcement "Engagement" warn
   ```

### Hosts showing `[?]` unknown status

No scope is defined for the engagement.

**Solution:**
Add scope entries to enable status tracking:
```bash
$ souleyez scope add "Engagement" --cidr 192.168.0.0/16
$ souleyez scope revalidate "Engagement"
```

### Tool chaining skipping valid targets

Targets may appear valid but aren't matching scope patterns.

**Debug steps:**
1. Test the target directly:
   ```bash
   $ souleyez scope validate "Engagement" <target>
   ```

2. Check for typos in scope entries:
   ```bash
   $ souleyez scope list "Engagement"
   ```

3. Verify domain patterns:
   - `*.example.com` - includes subdomains
   - `example.com` - exact match only

### Scope validation slowing down jobs

Scope validation adds minimal overhead (< 1ms per target). If experiencing slowness:

1. Check database performance
2. Reduce scope entry count if possible
3. Use broader CIDR ranges instead of many /32s

### Warnings not appearing in job metadata

Ensure enforcement mode is set to `warn`:
```bash
$ souleyez scope enforcement "Engagement" warn
```

If set to `off`, no validation occurs.

---

## Quick Reference

### Common Commands

```bash
# Setup
souleyez scope add <eng> --cidr <range>         # Add network
souleyez scope add <eng> --domain "<pattern>"   # Add domain
souleyez scope add <eng> --exclude --cidr <r>   # Add exclusion
souleyez scope enforcement <eng> [off|warn|block]

# Manage
souleyez scope list <eng>                       # List entries
souleyez scope remove <eng> <id>                # Remove entry
souleyez scope validate <eng> <target>          # Test target

# Hosts
souleyez scope revalidate <eng>                 # Update all hosts

# Audit
souleyez scope log <eng>                        # View log
souleyez scope log <eng> --action blocked       # Filter blocked
```

### Scope Types Quick Reference

| Type | Example | Matches |
|------|---------|---------|
| `cidr` | `192.168.1.0/24` | Any IP in range |
| `domain` | `*.example.com` | Subdomains + base |
| `domain` | `example.com` | Exact match only |
| `url` | `https://app.example.com` | Host extraction |
| `hostname` | `server.local` | Exact match |

### Enforcement Quick Reference

| Mode | Out-of-scope targets |
|------|---------------------|
| `off` | Allowed, no logging |
| `warn` | Allowed + warning logged |
| `block` | Rejected with error |

---

## Related Documentation

- [Auto-Chaining Guide](./auto-chaining.md) - How tool chaining works
- [Getting Started](./getting-started.md) - Initial setup
- [RBAC Guide](./rbac.md) - User permissions
- [Security Best Practices](../security/best-practices.md) - Security guidelines

---

*For support, contact cysoul.secit@gmail.com or visit github.com/cyber-soul-security/SoulEyez*
