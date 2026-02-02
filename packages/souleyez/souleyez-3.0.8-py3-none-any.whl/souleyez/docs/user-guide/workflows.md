# Pentesting Workflows Guide

**Purpose:** End-to-end penetration testing workflows using SoulEyez

**Last Updated:** 2025-11-18

---

## Overview

This guide demonstrates complete penetration testing workflows from initial reconnaissance to exploitation. Each workflow shows how to combine multiple tools effectively to achieve your testing objectives.

---

## Table of Contents

1. [Network Penetration Test Workflow](#network-penetration-test-workflow)
2. [Web Application Security Assessment](#web-application-security-assessment)
3. [Credential Harvesting Workflow](#credential-harvesting-workflow)
4. [Internal Network Enumeration](#internal-network-enumeration)
5. [WordPress Specific Testing](#wordpress-specific-testing)
6. [Automated Workflow (AI-Driven)](#automated-workflow-ai-driven)

---

## Network Penetration Test Workflow

### Objective
Complete network penetration test from discovery to exploitation

### Workflow Steps

#### **Phase 1: Setup** (2 mins)

```bash
# 1. Create engagement
souleyez engagement create "acme-corp-pentest"

# 2. Start background worker
souleyez worker start

# 3. Verify setup
souleyez engagement current
souleyez worker status
```

---

#### **Phase 2: Network Discovery** (5-15 mins)

```bash
# 1. Quick host discovery (live hosts only)
souleyez jobs enqueue nmap 10.0.0.0/24 --label "HOST_DISCOVERY" --args="-sn"

# 2. Monitor discovery
souleyez dashboard  # Press 'j' to see jobs

# 3. View discovered hosts
# From dashboard or:
souleyez hosts list

# Expected output: 5-20 live hosts discovered
```

---

#### **Phase 3: Service Enumeration** (10-30 mins)

```bash
# For each discovered host, run detailed scan
# (Or use auto-chaining - Nmap will trigger follow-ups automatically)

# 1. Service version scan on discovered hosts
souleyez jobs enqueue nmap 10.0.0.82 --label "SERVICES_82" --args="-sV -sC -T4"
souleyez jobs enqueue nmap 10.0.0.83 --label "SERVICES_83" --args="-sV -sC -T4"

# 2. Monitor progress
souleyez jobs tail <job_id>

# 3. Review services
souleyez services list

# Expected output:
# - HTTP/HTTPS servers → Web testing
# - SSH → Credential attacks
# - SMB → Share enumeration
# - MySQL/PostgreSQL → Database attacks
```

---

#### **Phase 4: Automated Follow-Up** (Automatic)

**With auto-chaining ENABLED:**

```
Nmap discovers HTTP on port 80
  ↓
  Nikto scan automatically triggered
  ↓
  Gobuster directory scan automatically triggered
  ↓
  Results parsed and stored
```

**Check auto-chaining status:**
```bash
# View from dashboard (shows "⚡ Auto-chaining: ENABLED")
souleyez dashboard

# Or check findings
souleyez findings list
```

---

#### **Phase 5: Web Application Testing** (15-60 mins)

```bash
# If HTTP/HTTPS services found:

# 1. Already done by auto-chaining:
#    - Nikto scan
#    - Gobuster directory scan

# 2. Manual web testing for interesting paths:
# Check discovered paths first
souleyez paths list

# 3. Test for SQL injection on interesting endpoints
souleyez jobs enqueue sqlmap "http://10.0.0.82/login.php?id=1" --label "SQLI_TEST"

# 4. If WordPress detected:
souleyez jobs enqueue wpscan http://10.0.0.82 --label "WP_SCAN"
```

---

#### **Phase 6: Credential Attacks** (30-120 mins)

```bash
# 1. Check for enumerated usernames
souleyez creds list --status "untested"

# 2. SSH brute-force (if SSH service found)
souleyez jobs enqueue hydra ssh://10.0.0.82 --label "SSH_BRUTE" \
  --args="-L data/wordlists/usernames/usernames-common.txt -P data/wordlists/passwords/passwords-common.txt"

# 3. MySQL brute-force (if MySQL found)
souleyez jobs enqueue hydra mysql://10.0.0.82 --label "MYSQL_BRUTE" \
  --args="-l root -P data/wordlists/passwords/passwords-common.txt"

# 4. Monitor credential discoveries
souleyez creds list --status "valid"
```

---

#### **Phase 7: Exploitation** (Variable)

```bash
# 1. Review all findings
souleyez findings list --severity critical
souleyez findings list --severity high

# 2. Validate credentials
souleyez creds list --status valid

# 3. Manual exploitation based on findings:
# Example: Valid SSH credentials found
ssh admin@10.0.0.82  # Use discovered password

# Example: SQL injection confirmed
# Use sqlmap --dump carefully (authorization required!)

# 4. Document exploitation path
# Use screenshots, notes, and export findings
```

---

#### **Phase 8: Reporting** (30-60 mins)

```bash
# 1. Generate report
souleyez report generate --format html

# 2. Review statistics
souleyez stats

# 3. Export data
souleyez export findings findings.csv
souleyez export creds credentials.csv

# 4. Clean up
souleyez worker stop
```

---

### Timeline Summary

```
Phase 1: Setup                  →  2 mins
Phase 2: Network Discovery      →  5-15 mins
Phase 3: Service Enumeration    →  10-30 mins
Phase 4: Auto Follow-Up         →  Automatic (20-40 mins)
Phase 5: Web Testing           →  15-60 mins
Phase 6: Credential Attacks     →  30-120 mins
Phase 7: Exploitation          →  Variable
Phase 8: Reporting             →  30-60 mins

Total (automated):  1.5 - 5 hours
Total (manual):     Longer, more thorough
```

---

## Web Application Security Assessment

### Objective
Comprehensive web application vulnerability assessment

### Scenario
Target: `http://webapp.example.com`

### Workflow Steps

#### **Phase 1: Information Gathering** (5-10 mins)

```bash
# 1. Create engagement
souleyez engagement create "webapp-assessment"
souleyez worker start

# 2. OSINT reconnaissance
souleyez jobs enqueue theharvester example.com --label "OSINT"

# 3. DNS enumeration
souleyez jobs enqueue dnsrecon example.com --label "DNS_ENUM"

# 4. Check for subdomains
souleyez jobs enqueue gobuster example.com --label "SUBDOMAIN_ENUM" \
  --args="dns -d example.com -w data/wordlists/web/subdomains.txt"

# Expected output: Subdomains, IPs, emails
```

---

#### **Phase 2: Web Server Fingerprinting** (5-10 mins)

```bash
# 1. Nikto scan
souleyez jobs enqueue nikto http://webapp.example.com --label "NIKTO_MAIN"

# 2. Check for common files/directories
souleyez jobs enqueue gobuster http://webapp.example.com --label "DIR_ENUM" \
  --args="-x php,html,txt,bak,old"

# Expected output:
# - Server version
# - Interesting paths
# - Backup files
# - Config files
```

---

#### **Phase 3: Vulnerability Scanning** (10-30 mins)

```bash
# 1. Check discovered paths
souleyez paths list --status 200

# 2. SQL injection testing on parameters
# For each interesting endpoint:
souleyez jobs enqueue sqlmap "http://webapp.example.com/product.php?id=1" --label "SQLI_PRODUCT"
souleyez jobs enqueue sqlmap "http://webapp.example.com/user.php?id=1" --label "SQLI_USER"

# 3. If WordPress detected:
souleyez jobs enqueue wpscan http://webapp.example.com --label "WP_VULN" \
  --args="--enumerate vp,vt,u"

# 4. Monitor findings
souleyez dashboard  # Check findings section
```

---

#### **Phase 4: Authentication Testing** (15-30 mins)

```bash
# 1. Identify login endpoints from Gobuster results
souleyez paths list | grep login

# 2. Test common credentials
souleyez jobs enqueue hydra http://webapp.example.com/login.php --label "WEB_LOGIN" \
  --args="http-post-form '/login.php:user=^USER^&pass=^PASS^:F=incorrect'"

# 3. SQL injection on login forms
souleyez jobs enqueue sqlmap "http://webapp.example.com/login.php" --label "SQLI_LOGIN" \
  --args="--data='user=admin&pass=test' --level=5 --risk=3"
```

---

#### **Phase 5: Deep Exploitation** (30-60 mins)

```bash
# 1. Review critical findings
souleyez findings list --severity critical

# 2. If SQL injection confirmed:
# Check what was discovered
souleyez findings list --tool sqlmap

# 3. Progressive exploitation (manual approval required)
# Already done automatically:
#   - SQLMap detected vulnerability
#   - Enumerated databases (auto-chaining)
#   - Enumerated tables (auto-chaining)
#   - STOPPED (manual review required before dump)

# 4. Manual exploitation (with authorization):
# Get exact command from job details
souleyez jobs get <sqlmap_job_id>

# Then run manually if authorized:
sqlmap --url="http://..." -D database_name -T users --dump
```

---

#### **Phase 6: Reporting**

```bash
# 1. Export findings
souleyez report generate

# 2. Review web-specific data
souleyez paths list --status 200   # Accessible paths
souleyez paths list --status 403   # Forbidden (interesting!)
souleyez paths list --status 500   # Server errors (potential bugs)

# 3. Generate vulnerability summary
souleyez findings list --severity high
souleyez findings list --severity critical
```

---

### Key Findings to Look For

✅ **High Priority:**
- SQL injection vulnerabilities
- Authentication bypasses
- Remote code execution (RCE)
- File upload vulnerabilities
- Directory traversal

⚠️ **Medium Priority:**
- Cross-site scripting (XSS)
- Information disclosure
- Weak session management
- Outdated software versions

ℹ️ **Low Priority:**
- Missing security headers
- HTTP methods enabled
- Directory listing
- Verbose error messages

---

## Credential Harvesting Workflow

### Objective
Collect and validate credentials across multiple services

### Workflow Steps

#### **Phase 1: Username Enumeration** (10-20 mins)

```bash
# 1. Setup
souleyez engagement create "cred-harvest"
souleyez worker start

# 2. OSINT for email addresses
souleyez jobs enqueue theharvester target.com --label "EMAIL_HARVEST"

# 3. SSH user enumeration (if SSH service found)
souleyez jobs enqueue msf_auxiliary auxiliary/scanner/ssh/ssh_enumusers \
  --label "SSH_ENUM" --args="RHOSTS=10.0.0.82"

# 4. SMB user enumeration
souleyez jobs enqueue enum4linux 10.0.0.82 --label "SMB_ENUM" --args="-U"

# 5. Review discovered usernames
souleyez creds list --status untested
```

---

#### **Phase 2: Password Attacks** (30-120 mins)

```bash
# 1. SSH brute-force with discovered users
souleyez jobs enqueue hydra ssh://10.0.0.82 --label "SSH_BRUTE" \
  --args="-L data/wordlists/usernames/discovered.txt -P data/wordlists/passwords/passwords-medium.txt"

# 2. FTP brute-force
souleyez jobs enqueue hydra ftp://10.0.0.82 --label "FTP_BRUTE" \
  --args="-L data/wordlists/usernames/usernames-common.txt -P data/wordlists/passwords/passwords-common.txt"

# 3. MySQL brute-force
souleyez jobs enqueue hydra mysql://10.0.0.82 --label "MYSQL_BRUTE" \
  --args="-l root -P data/wordlists/passwords/passwords-medium.txt"

# 4. Monitor valid credentials
souleyez dashboard  # Check "Valid Credentials" section
```

---

#### **Phase 3: Hash Cracking** (Variable)

```bash
# If hashes were obtained (via SQL injection, file read, etc.)

# 1. Prepare hash file
echo "5f4dcc3b5aa765d61d8327deb882cf99" > hashes.txt

# 2. Crack MD5 hashes
souleyez jobs enqueue hashcat hashes.txt --label "MD5_CRACK" \
  --args="-m 0 -a 0 data/wordlists/passwords/passwords-large.txt"

# 3. Check cracked passwords
souleyez creds list --status valid

# Auto-update: Hashcat parser automatically adds cracked passwords to database
```

---

#### **Phase 4: Credential Validation** (10-30 mins)

```bash
# 1. Review all valid credentials
souleyez creds list --status valid

# 2. Test credential reuse across services
# SSH credentials work on FTP?
# MySQL password same as SSH?

# 3. Manual validation
ssh username@10.0.0.82  # Test SSH access
mysql -h 10.0.0.82 -u root -p  # Test MySQL access

# 4. Document access levels
# Note which credentials provide:
# - User-level access
# - Admin/root access
# - Database access
```

---

#### **Phase 5: Reporting**

```bash
# Export credentials (encrypted)
souleyez export creds credentials.csv

# Summary statistics
souleyez creds stats

# Expected output:
# - Total credentials: 50
# - Valid credentials: 5
# - Username-only: 30
# - Full pairs: 15
```

---

## Internal Network Enumeration

### Objective
Enumerate an internal corporate network after initial access

### Scenario
You have obtained initial access via compromised credentials or VPN access

### Workflow Steps

#### **Phase 1: Host Discovery** (5-10 mins)

```bash
# 1. Setup
souleyez engagement create "internal-network"
souleyez worker start

# 2. Quick ping sweep of entire subnet
souleyez jobs enqueue nmap 192.168.1.0/24 --label "PING_SWEEP" --args="-sn -T5"

# 3. Review live hosts
souleyez hosts list

# Expected: 20-100+ hosts in corporate network
```

---

#### **Phase 2: Service Discovery** (15-45 mins)

```bash
# 1. Service scan on all live hosts (may take time)
souleyez jobs enqueue nmap 192.168.1.0/24 --label "SERVICE_SCAN" --args="-sV -T4 -p-"

# OR scan specific high-value targets:
souleyez jobs enqueue nmap 192.168.1.10 --label "DC_SCAN" --args="-sV -sC -p-"  # Domain Controller
souleyez jobs enqueue nmap 192.168.1.20 --label "FILE_SERVER" --args="-sV -sC -p-"  # File Server

# 2. Monitor for interesting services:
# - Port 445 (SMB) → Windows file shares
# - Port 389/636 (LDAP) → Active Directory
# - Port 3389 (RDP) → Remote Desktop
# - Port 1433 (MSSQL) → SQL Server
# - Port 5432 (PostgreSQL) → Database
```

---

#### **Phase 3: SMB Enumeration** (10-30 mins)

```bash
# 1. Enumerate all SMB hosts
# (Already discovered from Nmap on port 445)

# 2. Anonymous share enumeration
souleyez jobs enqueue smbmap 192.168.1.10 --label "SMB_ANON_DC"
souleyez jobs enqueue enum4linux 192.168.1.10 --label "ENUM_DC"

# 3. Authenticated enumeration (if creds available)
souleyez jobs enqueue smbmap 192.168.1.10 --label "SMB_AUTH_DC" \
  --args="-u 'domain\user' -p 'password'"

# 4. Review accessible shares
souleyez interactive → View Data → SMB Shares
```

---

#### **Phase 4: Active Directory Enumeration** (15-45 mins)

```bash
# If Domain Controller identified:

# 1. LDAP enumeration
souleyez jobs enqueue msf_auxiliary auxiliary/gather/ldap_query \
  --label "LDAP_ENUM" --args="RHOSTS=192.168.1.10"

# 2. Kerberos user enumeration
souleyez jobs enqueue msf_auxiliary auxiliary/gather/kerberos_enumusers \
  --label "KERB_USERS" --args="RHOSTS=192.168.1.10"

# 3. Review discovered AD users
souleyez creds list --service ldap
```

---

#### **Phase 5: Credential Attacks on Internal Services** (30-120 mins)

```bash
# 1. RDP brute-force (careful - may cause lockouts!)
souleyez jobs enqueue hydra rdp://192.168.1.10 --label "RDP_BRUTE" \
  --args="-L data/wordlists/usernames/usernames-common.txt -P data/wordlists/passwords/passwords-common.txt -t 4"

# 2. SMB password spraying (low and slow)
souleyez jobs enqueue hydra smb://192.168.1.10 --label "SMB_SPRAY" \
  --args="-L users.txt -p 'Password123!' -t 1"

# 3. MSSQL brute-force
souleyez jobs enqueue hydra mssql://192.168.1.30 --label "MSSQL_BRUTE" \
  --args="-l sa -P data/wordlists/passwords/passwords-medium.txt"
```

---

#### **Phase 6: Lateral Movement Preparation**

```bash
# 1. Review all valid credentials
souleyez creds list --status valid

# 2. Test credential reuse
# Try same credentials across multiple hosts:
# - Domain credentials on workstations
# - Local admin on file servers
# - Service accounts on databases

# 3. Map credential→host relationships
# Document which credentials work where

# 4. Identify high-value targets:
# - Domain Admin accounts
# - Database admin credentials
# - File server access
```

---

## WordPress Specific Testing

### Objective
Comprehensive WordPress security assessment

### Scenario
Target: `http://blog.example.com` (WordPress site)

### Workflow Steps

#### **Phase 1: WordPress Detection** (2-5 mins)

```bash
# 1. Setup
souleyez engagement create "wordpress-test"
souleyez worker start

# 2. Initial Nikto scan (auto-detects WordPress)
souleyez jobs enqueue nikto http://blog.example.com --label "NIKTO_WP"

# OR direct WPScan:
souleyez jobs enqueue wpscan http://blog.example.com --label "WP_INITIAL"

# Expected output: WordPress version, theme, plugins
```

---

#### **Phase 2: Enumeration** (10-20 mins)

```bash
# 1. Enumerate all plugins
souleyez jobs enqueue wpscan http://blog.example.com --label "WP_PLUGINS" \
  --args="--enumerate ap"  # All plugins

# 2. Enumerate users
souleyez jobs enqueue wpscan http://blog.example.com --label "WP_USERS" \
  --args="--enumerate u"

# 3. Check for vulnerable plugins
souleyez jobs enqueue wpscan http://blog.example.com --label "WP_VULN" \
  --args="--enumerate vp"  # Vulnerable plugins only

# 4. Review findings
souleyez findings list --tool wpscan
```

---

#### **Phase 3: Brute-Force Attack** (30-60 mins)

```bash
# 1. Get enumerated usernames
souleyez creds list | grep wordpress

# 2. WordPress login brute-force
souleyez jobs enqueue wpscan http://blog.example.com --label "WP_BRUTE" \
  --args="--enumerate u --passwords data/wordlists/passwords/passwords-medium.txt"

# 3. Monitor for valid logins
souleyez creds list --status valid --service wordpress
```

---

#### **Phase 4: Exploitation** (Variable)

```bash
# If vulnerable plugin found:

# 1. Review CVE details
souleyez findings list --tool wpscan --severity critical

# 2. Search for exploit
searchsploit "wordpress plugin_name"

# 3. Manual exploitation
# Use Metasploit or manual exploit based on findings

# 4. Document access
# If admin access obtained:
# - Upload malicious plugin?
# - Edit theme files?
# - Access database?
```

---

## Automated Workflow (AI-Driven)

### Objective
Let SoulEyez's AI suggest and execute penetration testing steps automatically

### Workflow Steps

#### **Phase 1: Initial Setup** (2 mins)

```bash
# 1. Create engagement
souleyez engagement create "ai-pentest"

# 2. Start worker
souleyez worker start

# 3. Enable auto-chaining (if not already enabled)
# Check dashboard - should show "⚡ Auto-chaining: ENABLED"
souleyez dashboard
```

---

#### **Phase 2: Initial Scan** (5 mins)

```bash
# 1. Run initial reconnaissance
souleyez jobs enqueue nmap 10.0.0.82 --label "INITIAL"

# 2. Let auto-chaining take over
# No further commands needed!

# Auto-chaining will:
# - Detect HTTP service → Launch Nikto
# - Detect HTTP service → Launch Gobuster
# - Detect SSH service → (wait for credentials)
# - Parse all results → Store findings
```

---

#### **Phase 3: AI Recommendations** (Ongoing)

```bash
# 1. Check AI recommendations
souleyez ai recommend

# Expected output:
# ┌─────────────────────────────────────────────────┐
# │ 🤖 AI RECOMMENDATION                            │
# ├─────────────────────────────────────────────────┤
# │ Action:  Brute-force SSH authentication         │
# │ Target:  10.0.0.82:22                          │
# │ Risk:    MEDIUM                                 │
# │ Reason:  SSH service detected, no valid creds   │
# │                                                 │
# │ Command: hydra ssh://10.0.0.82 ...             │
# │                                                 │
# │ [a] Approve  [d] Deny  [q] Quit                │
# └─────────────────────────────────────────────────┘

# 2. Execute with approval prompts
souleyez ai execute --manual

# 3. Or execute single action
souleyez ai execute --once

# 4. Or full automation (CAREFUL!)
souleyez ai execute --auto-low  # Executes LOW-risk actions automatically
```

---

#### **Phase 4: Monitor Progress** (Ongoing)

```bash
# 1. Real-time dashboard
souleyez dashboard

# Shows:
# - Active jobs (AI-triggered)
# - Recent findings
# - Credentials discovered
# - Next recommended actions

# 2. Check execution history
souleyez ai history

# 3. Review findings
souleyez findings list
```

---

#### **Phase 5: Manual Intervention** (As Needed)

```bash
# AI will recommend but NOT auto-execute:
# - HIGH-risk actions (database dumps)
# - CRITICAL-risk actions (exploitation)
# - Actions requiring specific parameters

# You must manually approve:
souleyez ai recommend  # See recommendation
souleyez ai execute --manual  # Approve one-by-one

# Or execute specific action manually:
souleyez jobs enqueue <tool> <target> --label "MANUAL_ACTION"
```

---

## Best Practices

### ✅ Do's

1. **Always get proper authorization before testing**
2. **Start with reconnaissance, then move to active testing**
3. **Use auto-chaining for efficiency (review output regularly)**
4. **Label your jobs for better organization**
5. **Monitor long-running scans with dashboard**
6. **Export findings and credentials regularly**
7. **Document your methodology and findings**
8. **Test discovered credentials across multiple services**

---

### ❌ Don'ts

1. **Don't test production systems without authorization**
2. **Don't use aggressive scan settings without permission**
3. **Don't ignore safety controls (AUTO-DUMP disabled for a reason!)**
4. **Don't brute-force authentication without lockout awareness**
5. **Don't trust automated findings without manual verification**
6. **Don't skip the reconnaissance phase**
7. **Don't forget to stop the worker when done**

---

## Troubleshooting Common Issues

### Jobs Not Running

```bash
# Check worker status
souleyez worker status

# If stopped, start it
souleyez worker start --fg  # Foreground for debugging
```

---

### No Results from Tools

```bash
# Check job output
souleyez jobs get <job_id>

# Common causes:
# - Tool not installed (apt-get install <tool>)
# - Invalid target format
# - Permission denied (need sudo?)
# - Network connectivity issues
```

---

### Auto-Chaining Not Working

```bash
# Verify auto-chaining enabled
souleyez dashboard  # Check for "⚡ Auto-chaining: ENABLED"

# View chaining guide
cat docs/AUTO_CHAINING.md

# Check if parsers are working
souleyez jobs reparse <job_id>  # Reparse output
```

---

## Next Steps

### Want to Learn More?

- **Tools Reference:** `docs/user-guide/tools-reference.md`
- **Worker Management:** `docs/user-guide/worker-management.md`
- **Auto-Chaining Details:** `docs/AUTO_CHAINING.md`
- **Troubleshooting:** `docs/user-guide/troubleshooting.md`

### Practice Environments

- **HackTheBox:** https://www.hackthebox.com/
- **TryHackMe:** https://tryhackme.com/
- **VulnHub:** https://www.vulnhub.com/
- **OWASP WebGoat:** Local vulnerable web apps

---

**Last Updated:** 2025-11-18
**Version:** 1.0
