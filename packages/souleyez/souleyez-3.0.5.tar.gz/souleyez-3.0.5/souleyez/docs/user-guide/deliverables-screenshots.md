# Deliverables & Screenshots - User Guide

**Last Updated:** 2025-11-18

---

## What Are Deliverables?

Deliverables are **testing requirements and acceptance criteria** for your penetration test. They help track whether you've met the engagement objectives.

**Think of it as:**
- Client says: "Find at least 5 usernames"
- Deliverable tracks: "Found 12 usernames ✓"

---

## What Are Screenshots?

Screenshots are **visual evidence** captured during testing. They complement tool outputs and provide proof for findings.

**Examples:**
- Web application vulnerability proof
- Successful exploitation (got shell!)
- Sensitive data discovered
- Configuration issues

---

## Why Use Deliverables & Screenshots?

### Problems They Solve

❌ **Before:**
- Manual tracking of test objectives in spreadsheet
- Easy to forget requirements
- Hard to prove you met criteria
- Screenshots scattered across folders
- No organization of visual evidence

✅ **With Deliverables & Screenshots:**
- Automatic progress tracking
- Clear pass/fail status
- Centralized screenshot management
- Integrated with Evidence Vault
- Client-facing proof of completion

---

## Part 1: Deliverable Tracking

### Deliverable Categories

Deliverables are organized by PTES methodology phase:

**1. Reconnaissance**
- Email addresses discovered
- Subdomains identified
- Infrastructure mapping

**2. Enumeration**
- Users enumerated
- Services identified
- Shares discovered
- Directories found

**3. Exploitation**
- Vulnerabilities exploited
- Sessions obtained
- Credentials validated

**4. Post-Exploitation**
- Privilege escalation achieved
- Lateral movement successful
- Data exfiltrated

**5. Techniques**
- Attack techniques demonstrated
- Specific methodologies followed

---

### Deliverable Types

#### Count-Based Deliverable

**Purpose:** Track quantity (e.g., "Find 5+ users")

**Example:**
```
Title: Enumerate at least 5 user accounts
Target: 5 users
Current: 12 users ✓
Status: COMPLETED
Auto-validation: SELECT COUNT(*) FROM credentials WHERE type='username'
```

---

#### Boolean Deliverable

**Purpose:** Track yes/no objectives (e.g., "Gain shell access")

**Example:**
```
Title: Obtain shell access to target system
Target: True
Status: COMPLETED ✓
Evidence: Metasploit session opened on 10.0.0.82
```

---

#### Manual Deliverable

**Purpose:** Subjective requirements (e.g., "Document methodology")

**Example:**
```
Title: Provide comprehensive report with remediation steps
Status: PENDING
Notes: Waiting for final review
```

---

### Accessing Deliverables

#### Interactive Menu

```bash
# Start interactive dashboard
souleyez interactive

# Navigate to:
Intelligence → Deliverables Dashboard
```

#### Command Line

```bash
# List all deliverables
souleyez deliverables list

# Add new deliverable
souleyez deliverables add \
  --title "Enumerate 10+ users" \
  --category enumeration \
  --type count \
  --target 10 \
  --auto-validate

# Mark as complete
souleyez deliverables complete <id>

# View progress
souleyez deliverables stats
```

---

### Reading the Deliverables Dashboard

```
┌─ Deliverables Dashboard ───────────────────────────┐
│ Engagement: acme-corp-pentest                      │
│ Overall Progress: 7/10 deliverables completed (70%)│
└────────────────────────────────────────────────────┘

RECONNAISSANCE (3/3 completed) ✓
─────────────────────────────────────────────────────
✓ [CRITICAL] Identify client email addresses
  Target: 10+ emails  |  Actual: 15 emails
  Auto-validated: 2025-11-05 14:32

✓ [HIGH] Map infrastructure (DNS, subdomains)
  Target: Complete mapping  |  Status: Done
  Evidence: 5 subdomains, 8 A records discovered

✓ [MEDIUM] OSINT reconnaissance
  Target: Complete  |  Status: Done
  Evidence: theHarvester, dnsrecon completed

ENUMERATION (3/4 completed)
─────────────────────────────────────────────────────
✓ [CRITICAL] Enumerate user accounts
  Target: 5+ users  |  Actual: 12 users
  Auto-validated: 2025-11-05 15:10

✓ [HIGH] Identify all open ports and services
  Target: Complete scan of /24  |  Status: Done
  Evidence: 8 hosts, 24 services documented

✓ [MEDIUM] Enumerate SMB shares
  Target: All Windows hosts  |  Actual: 3 hosts scanned
  Evidence: enum4linux, smbmap completed

⚠ [MEDIUM] Web directory enumeration
  Target: Test all web servers  |  Status: IN PROGRESS
  Progress: 2/3 web servers scanned

EXPLOITATION (1/3 completed)
─────────────────────────────────────────────────────
✓ [CRITICAL] Demonstrate SQL injection
  Target: Find and exploit SQLi  |  Status: COMPLETED
  Evidence: SQLMap confirmed on login.php

⚠ [HIGH] Obtain shell access
  Target: At least one system  |  Status: PENDING
  Note: FTP backdoor attempted, awaiting results

⚠ [MEDIUM] Validate discovered credentials
  Target: Test all username/password pairs  |  Status: PENDING
  Progress: 4/12 credentials tested

POST-EXPLOITATION (0/0 completed)
─────────────────────────────────────────────────────
(No deliverables defined for this phase)
```

---

### Auto-Validation

**What it does:** Automatically checks database to update deliverable status

**Example:**
```
Deliverable: Enumerate 10+ user accounts
Auto-validation query: SELECT COUNT(*) FROM credentials WHERE type='username'

When query result >= 10:
  Status automatically updates to COMPLETED ✓
```

**Benefits:**
- No manual updates needed
- Real-time progress tracking
- Accurate counts

**Supported for:**
- Count-based deliverables
- Some boolean deliverables

---

### Priority Levels

#### CRITICAL (Red)
**Must-have requirements** - Engagement fails if not met

**Examples:**
- Demonstrate critical vulnerability
- Obtain system access
- Exploit specific service

---

#### HIGH (Orange)
**Important objectives** - Should be achieved

**Examples:**
- Enumerate users
- Map attack surface
- Test authentication

---

#### MEDIUM (Yellow)
**Nice-to-have goals** - Enhance engagement value

**Examples:**
- Additional reconnaissance
- Extra service testing
- Comprehensive documentation

---

#### LOW (Blue)
**Optional objectives** - Time permitting

**Examples:**
- Test low-priority services
- Additional OSINT
- Extra validation

---

## Part 2: Screenshot Management

### Why Screenshots Matter

**Value:**
- Visual proof of findings
- Client can see what you saw
- Demonstrates impact
- Required for some compliance standards

**What to Screenshot:**
- Successful exploits (shell access)
- Vulnerability proof (SQLi, XSS demos)
- Sensitive data discovered
- Configuration issues
- Error messages revealing info
- Access to restricted areas

---

### Adding Screenshots

#### Interactive Menu

```bash
# Start interactive dashboard
souleyez interactive

# Navigate to:
Data & Management → Screenshots → Add Screenshot
```

#### Command Line

```bash
# Add screenshot
souleyez screenshots add \
  --file /path/to/screenshot.png \
  --title "SQL Injection Proof" \
  --phase exploitation \
  --host 10.0.0.82 \
  --tool sqlmap \
  --description "SQLMap successfully dumped users table"

# Add with automatic metadata
souleyez screenshots add \
  --file ~/Desktop/shell_access.png \
  --title "Shell Access via vsftpd Backdoor" \
  --phase exploitation \
  --host 10.0.0.82
```

---

### Screenshot Organization

**Organized by Phase:**
```
Screenshots/
├── reconnaissance/
│   ├── emails_discovered.png
│   └── dns_enumeration.png
├── enumeration/
│   ├── nmap_scan_results.png
│   ├── gobuster_directories.png
│   └── smb_shares.png
├── exploitation/
│   ├── sqli_proof.png
│   ├── shell_access.png
│   └── credential_validation.png
└── post-exploitation/
    ├── privilege_escalation.png
    └── lateral_movement.png
```

---

### Viewing Screenshots

```
┌─ Screenshots ──────────────────────────────────────┐
│ Engagement: acme-corp-pentest                      │
│ Total Screenshots: 23                              │
└────────────────────────────────────────────────────┘

RECONNAISSANCE (4 screenshots)
─────────────────────────────────────────────────────
[2025-11-05 14:32] emails_discovered.png
  Title: Email Addresses from theHarvester
  Host: example.com
  Tool: theHarvester

[2025-11-05 14:35] dns_records.png
  Title: DNS Enumeration Results
  Host: example.com
  Tool: dnsrecon

ENUMERATION (12 screenshots)
─────────────────────────────────────────────────────
[2025-11-05 14:45] nmap_results.png
  Title: Nmap Service Scan - Web Server
  Host: 10.0.0.82
  Tool: Nmap
  Description: 5 open ports identified

[2025-11-05 15:00] gobuster_output.png
  Title: Directory Enumeration
  Host: 10.0.0.82
  Tool: Gobuster
  Description: 23 directories discovered, including /admin/

EXPLOITATION (6 screenshots)
─────────────────────────────────────────────────────
[2025-11-05 15:15] sqli_confirmed.png
  Title: SQL Injection Confirmation
  Host: 10.0.0.82
  Tool: SQLMap
  Description: Blind boolean-based SQL injection confirmed

[2025-11-05 15:20] database_dump.png
  Title: Users Table Dumped
  Host: 10.0.0.82
  Tool: SQLMap
  Description: 156 user records extracted

[2025-11-05 15:30] shell_access.png
  Title: Shell Access via FTP Backdoor
  Host: 10.0.0.82
  Tool: Metasploit
  Description: Command shell opened, user 'root'

POST-EXPLOITATION (1 screenshot)
─────────────────────────────────────────────────────
[2025-11-05 15:45] etc_shadow.png
  Title: /etc/shadow File Access
  Host: 10.0.0.82
  Description: Password hashes obtained for cracking
```

---

### Screenshot Best Practices

#### ✅ Do

1. **Timestamp Everything**
   - Include timestamp in screenshot
   - Proves when action occurred
   - Important for incident response

2. **Show Context**
   - Include URL bar (web screenshots)
   - Show command prompt (terminal)
   - Capture enough to understand what's happening

3. **Annotate If Needed**
   - Highlight important parts
   - Add arrows/circles
   - Include brief explanation

4. **Screenshot Incrementally**
   - Capture as you go
   - Don't wait until end
   - Easy to forget otherwise

#### ❌ Don't

1. **Don't Screenshot Sensitive Client Data**
   - Redact PII (personal info)
   - Blur passwords (unless necessary for proof)
   - Sanitize before including in report

2. **Don't Over-Screenshot**
   - Quality > Quantity
   - 5 good screenshots > 50 mediocre ones
   - Focus on key findings

3. **Don't Forget to Organize**
   - Name files clearly
   - Use consistent naming
   - Associate with phase/finding

---

### Integration with Evidence Vault

**Screenshots are automatically included in evidence exports:**

```
evidence-bundle.zip
├── screenshots/
│   ├── reconnaissance/
│   │   ├── emails_discovered.png
│   │   └── dns_enumeration.png
│   ├── enumeration/
│   │   └── nmap_scan.png
│   └── exploitation/
│       ├── sqli_proof.png
│       └── shell_access.png
├── logs/
└── findings.txt
```

---

## Working Together: Deliverables + Screenshots

### Example Workflow

**Deliverable:**
```
Title: Demonstrate SQL injection vulnerability
Category: Exploitation
Target: Find and exploit at least one SQLi
Status: IN PROGRESS
```

**Steps:**
1. **Run SQLMap** → Tool output captured
2. **SQLi confirmed** → Update deliverable status
3. **Screenshot proof** → Add visual evidence
4. **Link together:**
   - Deliverable: Points to finding
   - Finding: References screenshot
   - Screenshot: Proves exploitation
   - All included in Evidence Vault

**Result:**
```
Deliverable: ✓ COMPLETED
Evidence:
  - Finding #12: SQL Injection in login.php
  - Screenshot: sqli_proof.png
  - Tool Output: sqlmap_login_php.txt
```

---

## Common Questions

### Q: Can deliverables be added after engagement starts?

**A:** Yes! Add deliverables anytime:
```bash
souleyez deliverables add --title "New objective" --category exploitation
```

### Q: What if I don't meet a deliverable?

**A:** Document why:
1. Update deliverable with notes
2. Explain blockers (e.g., "Service patched")
3. Include in report as "Attempted but not achievable"

### Q: Can I export just screenshots?

**A:** Yes, screenshots are included in evidence export, or:
```bash
# Copy all screenshots
cp -r ~/.souleyez/screenshots/[engagement-id]/ /path/to/export/
```

### Q: What format should screenshots be?

**A:** Recommended:
- PNG (lossless, good for text)
- JPG (smaller file size)
- Avoid: GIF (low quality), BMP (huge files)

---

## Troubleshooting

### Deliverable Not Auto-Updating

**Possible causes:**
1. **Query incorrect** - Check SQL syntax
2. **Data not in database** - Verify findings/creds exist
3. **Auto-validate disabled** - Enable in deliverable settings

**Solution:**
```bash
# Manually update
souleyez deliverables update <id> --status completed

# Or verify data exists
souleyez creds list
souleyez findings list
```

### Screenshot Not Showing

**Possible causes:**
1. **File path wrong** - Use absolute path
2. **File permissions** - Check read access
3. **Unsupported format** - Use PNG/JPG

**Solution:**
```bash
# Check file exists
ls -la /path/to/screenshot.png

# Verify permissions
chmod 644 /path/to/screenshot.png

# Re-add screenshot
souleyez screenshots add --file ...
```

---

## Next Steps

**Learn More:**
- [Evidence Vault Guide](evidence-vault.md) - Comprehensive evidence management
- [Report Generator Guide](report-generation.md) - Including screenshots in reports
- [Workflows Guide](workflows.md) - Complete testing workflows

**Related Commands:**
```bash
souleyez deliverables list              # View all deliverables
souleyez deliverables stats             # Progress summary
souleyez screenshots add --file ...     # Add screenshot
souleyez evidence export                # Export with screenshots
```

---

**Need Help?** Check `docs/user-guide/troubleshooting.md` or open an issue on GitHub.
