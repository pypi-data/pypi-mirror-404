# Role-Based Access Control (RBAC) Guide

**Version:** 1.2.0
**Last Updated:** December 2025

SoulEyez includes a comprehensive role-based access control system for enterprise multi-user deployments. This guide covers user management, roles, permissions, engagement ownership, and audit logging.

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Roles & Permissions](#roles--permissions)
4. [License Tiers](#license-tiers)
5. [User Management](#user-management)
6. [Authentication](#authentication)
7. [Engagement Ownership](#engagement-ownership)
8. [Audit Logging](#audit-logging)
9. [Single-User Mode](#single-user-mode)
10. [Security Best Practices](#security-best-practices)

---

## Overview

SoulEyez RBAC provides:

- **Multi-user authentication** with secure password hashing
- **Four role levels** (Admin, Lead, Analyst, Viewer)
- **Two license tiers** (Free, Pro)
- **Engagement-level access control** (Owner, Editor, Viewer)
- **Comprehensive audit logging** for compliance
- **Backward-compatible single-user mode**

---

## Getting Started

### First Run

On first launch, SoulEyez creates a default admin account:

```
$ souleyez interactive

🔐 FIRST RUN SETUP
======================================================================

No users found. Creating default admin account...

┌─────────────────────────────────────────┐
│  Default admin account created!         │
│                                         │
│  Username: admin                        │
│  Password: xK9#mP2$vL5nQ8wR             │
│                                         │
│  ⚠️  Save this password!                │
│  It will not be shown again.           │
└─────────────────────────────────────────┘
```

**Important:** Save the generated password immediately. It cannot be recovered.

### Logging In

```bash
# Interactive login
$ souleyez login
Username: admin
Password: ********

✅ Welcome, admin!
   Role: ADMIN | Tier: 💎 PRO
   Session expires: 2025-12-16 06:00
```

### Checking Current User

```bash
$ souleyez whoami

┌─────────────────────────────────────────┐
│  👤 Current User                        │
├─────────────────────────────────────────┤
│  Username      admin                    │
│  Role          ADMIN                    │
│  Tier          💎 PRO                   │
│  Email         admin@company.com        │
│  Last Login    2025-12-15 22:00         │
│  Status        Active                   │
└─────────────────────────────────────────┘
```

### Logging Out

```bash
$ souleyez logout
✅ Logged out. Goodbye, admin!
```

---

## Roles & Permissions

### Role Hierarchy

```
ADMIN → LEAD → ANALYST → VIEWER
  ↓       ↓        ↓         ↓
 All   Manage   Operate   Read-only
```

### Role Descriptions

| Role | Description | Typical Use Case |
|------|-------------|------------------|
| **Admin** | Full system access, user management | System administrators |
| **Lead** | Create/manage engagements, full scanning | Team leads, senior pentesters |
| **Analyst** | Run scans, add findings, generate reports | Pentesters, security analysts |
| **Viewer** | Read-only access to assigned engagements | Clients, auditors, trainees |

### Permission Matrix

| Action | Admin | Lead | Analyst | Viewer |
|--------|:-----:|:----:|:-------:|:------:|
| **User Management** |
| Create users | ✓ | | | |
| Update users | ✓ | | | |
| Delete users | ✓ | | | |
| List users | ✓ | | | |
| **Engagement Management** |
| Create engagement | ✓ | ✓ | | |
| Delete engagement | ✓ | ✓* | | |
| Switch engagement | ✓ | ✓ | ✓ | ✓ |
| Manage team | ✓ | ✓* | | |
| **Scanning & Tools** |
| Run scans | ✓ | ✓ | ✓ | |
| Kill scans | ✓ | ✓ | | |
| View job queue | ✓ | ✓ | ✓ | ✓ |
| **Data Management** |
| View findings | ✓ | ✓ | ✓ | ✓ |
| Add findings | ✓ | ✓ | ✓ | |
| Delete findings | ✓ | ✓ | | |
| View credentials | ✓ | ✓ | ✓ | ✓ |
| Add credentials | ✓ | ✓ | ✓ | |
| Delete credentials | ✓ | ✓ | | |
| **Reporting** |
| Generate reports | ✓ | ✓ | ✓ | |
| Export reports | ✓ | ✓ | ✓ | |
| **AI Features** |
| AI recommendations | ✓ | ✓ | ✓ | |
| AI execute | ✓ | ✓ | ✓ | |
| **System** |
| View audit logs | ✓ | ✓ | | |
| Export audit logs | ✓ | | | |
| Database management | ✓ | | | |
| System configuration | ✓ | | | |

*\* Lead can only delete/manage engagements they own*

---

## License Tiers

SoulEyez has two license tiers that work alongside roles:

### Free Tier

- All reconnaissance tools (theHarvester, WHOIS, DNSRecon)
- All scanning tools (Nmap, Gobuster, Nuclei, etc.)
- All data management features
- Basic reporting

### Pro Tier (💎)

Everything in Free, plus:

- **AI Execute** - Autonomous AI-driven pentesting
- **Automation** - Chain rules and automated workflows
- **MSF Integration** - Advanced Metasploit integration
- **Reports & Export** - Professional client deliverables

### Tier + Role Interaction

Both tier AND role must permit an action:

```
Example: AI Execute requires:
  - Role: Analyst or above (Analyst, Lead, Admin)
  - Tier: Pro

A Lead with Free tier CANNOT use AI Execute.
An Analyst with Pro tier CAN use AI Execute.
```

### Checking Your Tier

```bash
$ souleyez whoami
# Shows your current tier

# Or in the interactive menu status line:
👤 analyst (ANALYST) 💎  |  📊 Client Pentest  |  ...
```

### Upgrading to Pro

```bash
# In interactive menu, select a Pro feature:
[x] 🤖 AI Execute 💎

# If you're on Free tier, you'll see:
┌─────────────────────────────────────────┐
│  💎 PRO FEATURE                         │
│                                         │
│  AI Execute requires a Pro license.     │
│                                         │
│  [a] Activate license key               │
│  [p] Purchase at cybersoulsecurity.com  │
│  [q] Return to menu                     │
└─────────────────────────────────────────┘
```

---

## User Management

User management is **Admin-only**.

### Creating Users

```bash
$ souleyez user create analyst1 --role analyst --email analyst1@company.com

Creating user: analyst1
Password requirements: 8+ chars, upper, lower, digit, special

Password: ********
Confirm password: ********

✅ User 'analyst1' created successfully!
   Role: ANALYST
   Tier: FREE
```

### Listing Users

```bash
$ souleyez user list

┌─────────────────────────────────────────────────────────────────┐
│  👥 Users                                                       │
├──────────┬────────┬──────┬─────────────────────┬────────┬──────┤
│ Username │ Role   │ Tier │ Email               │ Status │ Last │
├──────────┼────────┼──────┼─────────────────────┼────────┼──────┤
│ admin    │ ADMIN  │ 💎   │ admin@company.com   │ Active │ Today│
│ lead1    │ LEAD   │ 💎   │ lead@company.com    │ Active │ Today│
│ analyst1 │ ANALYST│ FREE │ analyst1@company.com│ Active │ Never│
│ viewer1  │ VIEWER │ FREE │ client@external.com │ Active │ Dec 1│
└──────────┴────────┴──────┴─────────────────────┴────────┴──────┘

Total: 4 user(s)
```

### Updating Users

```bash
# Change role
$ souleyez user update analyst1 --role lead
✅ User 'analyst1' updated successfully!

# Change tier
$ souleyez user update analyst1 --tier PRO
✅ User 'analyst1' updated successfully!

# Deactivate account
$ souleyez user update analyst1 --deactivate
✅ User 'analyst1' updated successfully!

# Reactivate account
$ souleyez user update analyst1 --activate
✅ User 'analyst1' updated successfully!
```

### Changing Passwords

```bash
# Change your own password
$ souleyez user passwd
Current password: ********
New password: ********
Confirm new password: ********
✅ Password changed successfully!

# Admin: Reset another user's password
$ souleyez user passwd analyst1
New password: ********
Confirm new password: ********
✅ Password changed successfully!
```

### Deleting Users

```bash
$ souleyez user delete analyst1
Delete user 'analyst1'? This cannot be undone [y/N]: y
✅ User 'analyst1' deleted
```

---

## Authentication

### Password Requirements

- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)
- At least one special character (!@#$%^&*(),.?":{}|<>)

### Session Management

- Sessions expire after 8 hours by default
- Session token stored in `~/.souleyez/session.json`
- Secured with file permissions (600)

### Account Lockout

After 5 failed login attempts:
- Account locks for 15 minutes
- Admin can unlock via user update

```bash
# Check if locked
$ souleyez user list --all
# Shows "Locked" status

# Admin unlock
$ souleyez user update analyst1 --activate
```

### Security Features

| Feature | Implementation |
|---------|----------------|
| Password hashing | PBKDF2-HMAC-SHA256, 480,000 iterations |
| Session tokens | 32-byte cryptographically secure random |
| Token storage | Hashed in database (never stored plain) |
| Timing attacks | Constant-time password comparison |

---

## Engagement Ownership

Engagements have ownership and team-based access control.

### Permission Levels

| Level | Can View | Can Edit | Can Delete | Can Manage Team |
|-------|:--------:|:--------:|:----------:|:---------------:|
| **Owner** | ✓ | ✓ | ✓ | ✓ |
| **Editor** | ✓ | ✓ | | |
| **Viewer** | ✓ | | | |

*Note: Admins bypass all engagement access checks*

### Viewing Team

```bash
$ souleyez engagement team list "Client Pentest"

┌─────────────────────────────────────────────────────────┐
│  👥 Team: Client Pentest                                │
├──────────┬─────────────────────┬────────┬──────────────┤
│ Username │ Email               │ Role   │ Added        │
├──────────┼─────────────────────┼────────┼──────────────┤
│ lead1    │ lead@company.com    │ OWNER  │ 2025-12-01   │
│ analyst1 │ analyst1@company.com│ EDITOR │ 2025-12-05   │
│ viewer1  │ client@external.com │ VIEWER │ 2025-12-10   │
└──────────┴─────────────────────┴────────┴──────────────┘
```

### Adding Team Members

```bash
# Add as editor (can run scans, add findings)
$ souleyez engagement team add "Client Pentest" analyst2 --role editor
✅ Added analyst2 as editor to 'Client Pentest'

# Add as viewer (read-only, great for clients)
$ souleyez engagement team add "Client Pentest" client1 --role viewer
✅ Added client1 as viewer to 'Client Pentest'
```

### Removing Team Members

```bash
$ souleyez engagement team remove "Client Pentest" analyst2
✅ Removed analyst2 from 'Client Pentest'
```

### Transferring Ownership

```bash
$ souleyez engagement team transfer "Client Pentest" analyst1
Transfer ownership of 'Client Pentest' to analyst1? [y/N]: y
✅ Ownership transferred to analyst1
   You have been added as an editor.
```

### Engagement Visibility

Users only see engagements they have access to:

```bash
# As analyst1 (has access to 2 engagements)
$ souleyez engagement list

📁 Your Engagements:

  [1] 👑 My Project           (owner)
  [2] ✏️ Client Pentest        (editor)

# As viewer1 (has access to 1 engagement)
$ souleyez engagement list

📁 Your Engagements:

  [1] 👁️ Client Pentest        (viewer)
```

---

## Audit Logging

All sensitive actions are logged for compliance and security monitoring.

### What Gets Logged

| Category | Events |
|----------|--------|
| **User** | login, logout, created, updated, deleted, password_changed |
| **Engagement** | created, deleted, team.added, team.removed, transferred |
| **Scan** | started, completed, failed, killed |
| **Finding** | created, updated, deleted |
| **Credential** | created, updated, deleted |
| **Report** | generated, exported |
| **AI** | executed, recommendation |
| **Security** | auth.failed, permission.denied |

### Viewing Audit Logs

```bash
# List recent events
$ souleyez audit list

┌────────────────────────────────────────────────────────────────────────┐
│  📋 Audit Log (Last 50 entries)                                        │
├─────────────────────┬──────────┬─────────────────────┬─────────┬───────┤
│ Time                │ User     │ Action              │ Resource│ ✓     │
├─────────────────────┼──────────┼─────────────────────┼─────────┼───────┤
│ 2025-12-15 22:30:15 │ analyst1 │ scan.started        │ job:142 │ ✓     │
│ 2025-12-15 22:28:03 │ admin    │ user.created        │ user:5  │ ✓     │
│ 2025-12-15 22:25:41 │ lead1    │ engagement.created  │ eng:12  │ ✓     │
│ 2025-12-15 22:20:00 │ -        │ auth.failed         │ -       │ ✗     │
└─────────────────────┴──────────┴─────────────────────┴─────────┴───────┘

# Filter by user
$ souleyez audit list --user analyst1

# Filter by action
$ souleyez audit list --action scan
```

### Searching Logs

```bash
# Search with multiple filters
$ souleyez audit search --user admin --start 2025-12-01 --end 2025-12-15

# Find failed actions
$ souleyez audit search --failed

# Find specific resource types
$ souleyez audit search --resource engagement
```

### Audit Statistics

```bash
$ souleyez audit stats

┌─────────────────────────────────────────┐
│  📊 Audit Statistics                    │
├─────────────────────────────────────────┤
│  Period:        Last 30 days            │
│  Total Events:  1,247                   │
│  Failed Events: 23                      │
│  Unique Users:  8                       │
└─────────────────────────────────────────┘

Events by Category:
  scan         ████████████████████  487
  finding      ██████████████        312
  user         ██████                156
  engagement   █████                 128
  credential   ████                  98
  report       ██                    42
  auth         █                     24
```

### Exporting Logs

```bash
# Export to JSON (Admin only)
$ souleyez audit export --start 2025-12-01 --format json -o audit.json
✅ Exported 1,247 entries to audit.json

# Export to CSV for spreadsheet analysis
$ souleyez audit export --start 2025-12-01 --format csv -o audit.csv
✅ Exported 1,247 entries to audit.csv
```

---

## Single-User Mode

For individual users or simple setups, RBAC operates in single-user mode:

### How It Works

- If only **one user** exists in the system
- Auto-login happens at startup (no password prompt)
- All features work normally
- Session lasts 30 days

### Switching to Multi-User

Simply create a second user:

```bash
$ souleyez user create analyst1 --role analyst
```

Now:
- Login prompt appears on startup
- Sessions expire after 8 hours
- Full RBAC enforcement active

### Forcing Login Prompt

Even in single-user mode, you can require login:

```bash
$ souleyez interactive --require-login
```

---

## Security Best Practices

### For Administrators

1. **Change the default admin password immediately**
   ```bash
   $ souleyez user passwd
   ```

2. **Use strong passwords** (12+ characters recommended)

3. **Create individual accounts** - Don't share credentials

4. **Use least privilege** - Assign minimum required role

5. **Review audit logs regularly**
   ```bash
   $ souleyez audit stats
   $ souleyez audit list --action auth.failed
   ```

6. **Remove inactive users**
   ```bash
   $ souleyez user update olduser --deactivate
   ```

### For Team Leads

1. **Limit engagement access** - Only add team members who need access

2. **Use Viewer role for clients** - Read-only is safer

3. **Transfer ownership before leaving** - Don't orphan engagements

4. **Monitor team activity**
   ```bash
   $ souleyez audit list --user teamember1
   ```

### For All Users

1. **Log out when done**
   ```bash
   $ souleyez logout
   ```

2. **Don't share your password**

3. **Report suspicious activity** to your admin

4. **Use a password manager** for your SoulEyez credentials

---

## Troubleshooting

### "Authentication required"

You need to log in:
```bash
$ souleyez login
```

### "Permission denied"

Your role doesn't allow this action. Contact an admin for elevated access.

### "Pro license required"

The feature requires a Pro tier license. Upgrade at cybersoulsecurity.com/souleyez or contact your admin.

### "Account is temporarily locked"

Too many failed login attempts. Wait 15 minutes or ask an admin to unlock:
```bash
$ souleyez user update username --activate
```

### "You don't have access to this engagement"

You're not on the engagement's team. Ask the owner to add you:
```bash
$ souleyez engagement team add "Engagement Name" yourusername --role viewer
```

### Forgot Password

Ask an admin to reset it:
```bash
# Admin runs:
$ souleyez user passwd username
```

---

## Quick Reference

### Common Commands

```bash
# Authentication
souleyez login                          # Log in
souleyez logout                         # Log out
souleyez whoami                         # Show current user

# User Management (Admin)
souleyez user create <name>             # Create user
souleyez user list                      # List users
souleyez user update <name> --role X    # Change role
souleyez user update <name> --tier X    # Change tier
souleyez user delete <name>             # Delete user
souleyez user passwd [name]             # Change password

# Team Management (Owner/Admin)
souleyez engagement team list <eng>     # List team
souleyez engagement team add <eng> <user> --role X
souleyez engagement team remove <eng> <user>
souleyez engagement team transfer <eng> <user>

# Audit (Lead/Admin)
souleyez audit list                     # Recent events
souleyez audit search --user X          # Search by user
souleyez audit stats                    # Statistics
souleyez audit export --start X         # Export (Admin)
```

### Role Quick Reference

| Need to... | Required Role |
|------------|---------------|
| View findings | Viewer+ |
| Run scans | Analyst+ |
| Create engagements | Lead+ |
| Manage users | Admin |
| Use AI Execute | Analyst+ with Pro tier |

---

## Related Documentation

- [Licensing Architecture](../LICENSING_ARCHITECTURE.md) - Pro tier details
- [Security Guide](../SECURITY.md) - Overall security practices
- [Getting Started](./getting-started.md) - First-time setup

---

*For support, contact cysoul.secit@gmail.com or visit github.com/cyber-soul-security/SoulEyez*
