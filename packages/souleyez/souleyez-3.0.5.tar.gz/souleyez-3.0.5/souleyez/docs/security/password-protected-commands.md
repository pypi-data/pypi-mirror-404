# Password-Protected Commands

## Overview

SoulEyez uses master password protection for commands that access sensitive data. This document lists which commands require authentication and why.

## Authentication System

The password protection system uses the same master password as credential encryption (configured via `migrate_credentials.py`). When encryption is enabled, users will be prompted for their master password when accessing sensitive commands.

**Key Features:**
- Session-based unlock (enter password once per session)
- 3 attempt limit for security
- Automatic timeout after inactivity
- Protects against unauthorized access to sensitive engagement data

## Protected Commands

The following commands require master password authentication:

### 1. `souleyez creds`
**What it protects:** Discovered credentials (usernames, passwords, API keys)

**Why:** Contains the most sensitive data from pentests - valid credentials that could be used to access client systems.

**Example:**
```bash
$ souleyez creds list
🔒 Credentials are encrypted.
Enter master password: ******
✅ Unlocked successfully!
```

### 2. `souleyez findings`
**What it protects:** Vulnerability findings and exploitation evidence

**Why:** Contains detailed vulnerability information, exploitation steps, and evidence that could be misused if accessed by unauthorized parties.

**Subcommands protected:**
- `findings list` - View all findings
- `findings add` - Add new findings
- `findings update` - Modify findings
- `findings delete` - Remove findings
- `findings show` - View detailed finding information

### 3. `souleyez report`
**What it protects:** Generated penetration test reports

**Why:** Reports aggregate all sensitive data (findings, credentials, screenshots) into comprehensive documents for clients.

**Subcommands protected:**
- `report generate` - Generate reports in various formats
- `report list` - View generated reports
- `report preview` - Preview report contents

### 4. `souleyez osint`
**What it protects:** OSINT data (emails, subdomains, metadata)

**Why:** OSINT data can reveal sensitive information about targets, employees, and infrastructure that could be used for social engineering or further attacks.

**Subcommands protected:**
- `osint list` - View OSINT data
- `osint add` - Add OSINT findings
- `osint search` - Search OSINT database

### 5. `souleyez dashboard`
**What it protects:** Live view of all engagement data

**Why:** Dashboard displays real-time status including credentials, findings, and job results in a single view.

### 6. `souleyez screenshots`
**What it protects:** Screenshot evidence from engagements

**Why:** Screenshots may contain:
- Credentials visible on screen
- Exploitation evidence
- Client system information
- Sensitive application data

**Subcommands protected:**
- `screenshots add` - Upload screenshots
- `screenshots list` - View all screenshots
- `screenshots show` - Display screenshot details

### 7. `souleyez deliverables`
**What it protects:** Engagement deliverables and acceptance criteria

**Why:** Deliverables contain:
- Scope of engagement
- Findings summaries
- Evidence links
- Client-specific requirements

**Subcommands protected:**
- `deliverables init` - Initialize deliverables
- `deliverables list` - View deliverables
- `deliverables status` - Check completion status

## Unprotected Commands

The following commands do NOT require authentication as they work with non-sensitive operational data:

### Safe Commands (No Password Required)

- **`souleyez engagement`** - Engagement metadata (names, dates, scopes)
- **`souleyez hosts`** - IP addresses and hostnames (not sensitive alone)
- **`souleyez services`** - Port and service information
- **`souleyez jobs`** - Background job status
- **`souleyez worker`** - Worker management
- **`souleyez plugins`** - Available tool plugins
- **`souleyez db`** - Database utilities
- **`souleyez interactive`** - Tool selection menu

**Rationale:** These commands manage operational aspects of engagements without exposing credentials, vulnerabilities, or client-specific findings.

## Enabling Encryption

Password protection only activates when encryption is enabled. To enable:

```bash
# Run the migration script
python migrate_credentials.py

# Follow prompts to:
# 1. Set master password
# 2. Encrypt existing credentials
# 3. Enable encryption

# Verify encryption status
souleyez creds list  # Should prompt for password
```

## Security Best Practices

1. **Use a Strong Master Password**
   - Minimum 12 characters
   - Mix of letters, numbers, symbols
   - Store in password manager (KeePassXC, 1Password, etc.)

2. **Lock When Away**
   - Session auto-locks after inactivity timeout
   - Manually lock by exiting terminal

3. **Protect Database File**
   - Encryption protects `~/.souleyez/souleyez.db` at rest
   - File permissions set to `0600` (user-only access)

4. **Backup Encrypted Data**
   - Encrypted credentials remain encrypted in backups
   - Remember master password - no recovery mechanism!

## Implementation Details

Password protection is implemented via the `@require_password` decorator defined in `souleyez/security.py`:

```python
from souleyez.security import require_password

@cli.group()
@require_password
def findings():
    """Findings/vulnerabilities management commands."""
    pass
```

The decorator:
1. Checks if encryption is enabled
2. Prompts for password if not unlocked
3. Validates password via PBKDF2 + Fernet
4. Stores unlock state in memory for session
5. Blocks access if authentication fails

## Related Documentation

- [Master Password Encryption Approach](../architecture/decisions/002-master-password-approach.md)
- [Credential Encryption Guide](./credential-encryption.md)
- [Security Best Practices](./best-practices.md)

---

**Last Updated:** 2025-01-21
**Author:** Security Team
