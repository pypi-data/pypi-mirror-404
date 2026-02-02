# Attack Surface Dashboard - User Guide

**Last Updated:** 2025-11-18

---

## What is the Attack Surface Dashboard?

The Attack Surface Dashboard shows you **what you've attacked vs. what's still pending** in your penetration test. It's like a progress tracker for your exploitation efforts.

**Simple Answer:** It helps you answer "Did I try to exploit this service yet?"

---

## Why Use the Attack Surface Dashboard?

### Problems It Solves

❌ **Before:**
- Manual tracking of what's been tested
- Easy to miss untested services
- Hard to prioritize targets
- No visibility into exploitation progress
- Pen-and-paper checklists

✅ **With Attack Surface Dashboard:**
- Automatic tracking of all services
- Clear status: Not Tried | Attempted | Exploited ✓
- Priority scoring (high-value targets first)
- Progress metrics at a glance
- One-click exploitation launch

---

## Understanding Attack Surface

### What is "Attack Surface"?

**Attack surface** = All the ways an attacker can interact with a system

Think of it like doors and windows on a house:
- More doors/windows = larger attack surface = more opportunities
- Unlocked doors = higher-value targets
- Already-broken windows = confirmed vulnerabilities

### What Contributes to Attack Surface?

```
Attack Surface Score =
  (Open Ports × 2) +
  (Services × 3) +
  (Findings × 5) +
  (Critical Findings × 15)
```

**Example:**
```
Host: 10.0.0.82

5 open ports          → 5 × 2 = 10 points
5 services running    → 5 × 3 = 15 points
12 findings           → 12 × 5 = 60 points
2 critical findings   → 2 × 15 = 30 points
─────────────────────────────────
Total Attack Surface  → 115 points (HIGH)
```

Higher score = More attractive target = Should test first!

---

## Accessing the Dashboard

### Option 1: Interactive Menu

```bash
# Start interactive dashboard
souleyez interactive

# Navigate to:
Intelligence → Attack Surface Analysis
```

### Option 2: Direct Command (Coming Soon)

```bash
souleyez attack-surface analyze
```

---

## Reading the Dashboard

### Overview Section

```
┌─ Attack Surface Analysis ──────────────────────────┐
│ Engagement: acme-corp-pentest                      │
│                                                    │
│ Total Hosts Scanned: 8                            │
│ Total Services: 24                                │
│ Services Exploited: 4 / 24 (17%)                  │
│ Critical Findings: 3                              │
└────────────────────────────────────────────────────┘
```

**What This Tells You:**
- You've scanned 8 hosts
- Found 24 different services
- Successfully exploited 4 of them (83% still untested!)
- Have 3 critical vulnerabilities to investigate

---

### Top Targets

**Hosts ranked by attack surface score (highest first):**

```
TOP 5 TARGETS
─────────────────────────────────────────────────────
1. 10.0.0.82 (web-server.acme.local)
   Score: 115  |  5 ports  |  12 findings  |  2 critical
   Status: 4/5 services exploited

2. 10.0.0.5 (db-server.acme.local)
   Score: 85   |  3 ports  |  8 findings  |  1 critical
   Status: 0/3 services exploited ⚠️

3. 10.0.0.10 (mail.acme.local)
   Score: 62   |  4 ports  |  5 findings  |  0 critical
   Status: 2/4 services exploited
```

**How to Use:**
- Focus on hosts with highest scores first
- ⚠️ = No exploitation attempts (low-hanging fruit!)
- ✓ = Services already exploited (still check for more!)

---

### Service Breakdown

**Detailed status for each service:**

```
HOST: 10.0.0.82 (Attack Surface: 115)
────────────────────────────────────────────────────────

Port 21 - FTP (vsftpd 2.3.4)
  Status: ✅ EXPLOITED
  Evidence: Session opened, backdoor confirmed
  Jobs: msf_exploit_vsftpd_234 (SUCCESS)

Port 22 - SSH (OpenSSH 7.2)
  Status: 🔄 ATTEMPTED
  Evidence: Brute-force attempted, no valid creds
  Jobs: hydra_ssh_brute (FAILED)
  Recommendation: Try wordlist-medium.txt

Port 80 - HTTP (Apache 2.4.7)
  Status: 🔄 ATTEMPTED
  Evidence: SQLMap tested, no injection found
  Jobs: sqlmap_test (COMPLETED), nikto_scan (COMPLETED)

Port 3306 - MySQL (5.7.12)
  Status: ⚠️ NOT TRIED
  Recommendation: Try mysql_login, check for default creds
  [Press 'e' to auto-exploit]

Port 8080 - HTTP (Tomcat 7.0)
  Status: ⚠️ NOT TRIED
  Recommendation: Check for manager console, test default creds
  [Press 'e' to auto-exploit]
```

---

## Exploitation Status

### ✅ EXPLOITED (Green)

**Meaning:** You successfully exploited this service

**Evidence Required:**
- Metasploit session opened, OR
- Valid credentials confirmed, OR
- Vulnerability confirmed exploitable

**Example:**
- FTP backdoor triggered → Shell access
- SSH credentials validated → Login successful
- SQL injection confirmed → Database dumped

---

### 🔄 ATTEMPTED (Yellow)

**Meaning:** You tried to exploit but haven't succeeded yet

**What Counts as "Attempted":**
- Brute-force job completed (no valid creds)
- SQLMap scan finished (no injection)
- Exploit module ran (failed/no session)

**Example:**
- Hydra brute-force → No matches in wordlist
- SQLMap test → No vulnerability detected
- Metasploit exploit → Exploit failed

**What to Do:**
- Try different wordlists
- Try different attack vectors
- Research CVEs for that service version

---

### ⚠️ NOT TRIED (Red)

**Meaning:** Service discovered but no exploitation attempts logged

**This is Your TODO List!**

**High Priority:** These are unexploited services that could be vulnerable

**Quick Action:**
- Press 'e' on the service to auto-exploit
- Dashboard will queue appropriate attack jobs
- Monitor progress

---

## Smart Recommendations

The dashboard suggests next steps based on your progress:

### Example Recommendations

```
RECOMMENDED ACTIONS (Priority Order)
─────────────────────────────────────────────────────

1. [CRITICAL] Exploit MySQL on 10.0.0.82:3306
   Reason: Database service, not attempted, high-value target
   Action: Test default credentials, brute-force root account
   Command: hydra mysql://10.0.0.82 -l root -P passwords.txt

2. [HIGH] Re-attempt SSH on 10.0.0.82:22
   Reason: Previous brute-force failed, try larger wordlist
   Action: Use wordlist-medium.txt (10,000 passwords)
   Command: hydra ssh://10.0.0.82 -L users.txt -P medium.txt

3. [MEDIUM] Test Tomcat manager on 10.0.0.82:8080
   Reason: Tomcat often has weak/default credentials
   Action: Test tomcat:tomcat, admin:admin
   Command: hydra http://10.0.0.82:8080/manager -L ... -P ...
```

**How Recommendations Work:**
1. **Analyzes all services** across all hosts
2. **Identifies gaps** (not tried, or failed attempts)
3. **Ranks by priority** (critical findings → high score → not tried)
4. **Suggests specific actions** with commands

---

## One-Click Auto-Exploit

### What It Does

Press 'e' on a NOT TRIED service to automatically:
1. **Select appropriate tools** for that service type
2. **Enqueue exploitation jobs** with smart defaults
3. **Track progress** automatically
4. **Update status** when jobs complete

### Example: Auto-Exploit MySQL

```
You press 'e' on: Port 3306 - MySQL (⚠️ NOT TRIED)

Dashboard automatically enqueues:
  1. Hydra mysql_login (default creds)
  2. Hydra mysql_login (common passwords)
  3. MSF mysql_hashdump (if creds found)

Status updates to: 🔄 ATTEMPTED

If credentials found:
  Status updates to: ✅ EXPLOITED
```

### Supported Auto-Exploits

| Service | Auto-Exploit Actions |
|---------|---------------------|
| **SSH** | Hydra brute-force (users + passwords) |
| **FTP** | Hydra brute-force, test anonymous login |
| **MySQL** | Hydra mysql_login, test root/admin |
| **PostgreSQL** | Hydra postgres, test postgres user |
| **SMB** | enum4linux, smbmap, test null session |
| **HTTP** | Nikto scan, Gobuster directories, SQLMap (if params) |
| **HTTPS** | Same as HTTP |
| **RDP** | Hydra RDP (careful with lockouts!) |

---

## Viewing Reports

### Export Attack Surface Report

**What's Included:**
- Complete attack surface analysis
- All services with exploitation status
- Recommendations ranked by priority
- Evidence for exploited services
- Gap analysis (what's not tried)

**How to Export:**
1. Open Attack Surface Dashboard
2. Press 'r' for Report
3. Select format (Markdown, HTML, CSV)
4. File saved to: `~/.souleyez/reports/attack-surface-[engagement]-[date].md`

---

## Best Practices

### ✅ Do

1. **Review After Major Scans**
   - After Nmap host discovery → Check attack surface
   - After service enumeration → See what's unexploited
   - After exploitation phase → Verify progress

2. **Focus on NOT TRIED Services**
   - These are low-hanging fruit
   - Use one-click auto-exploit
   - Quick wins

3. **Don't Ignore ATTEMPTED Services**
   - Failed doesn't mean impossible
   - Try different wordlists
   - Research specific CVEs

4. **Track Progress Daily**
   - Set goals: "Exploit 5 services today"
   - Use dashboard for accountability
   - Document what worked

### ❌ Don't

1. **Don't Blindly Auto-Exploit Everything**
   - Some services trigger alerts/lockouts
   - RDP brute-force → account lockouts!
   - Manual approval for sensitive targets

2. **Don't Rely Only on Automation**
   - Dashboard shows status, but manual testing is key
   - Custom exploitation may be needed
   - Research service versions

3. **Don't Forget to Document**
   - Dashboard tracks attempts, but not methodology
   - Keep notes on techniques used
   - Document why attacks failed

---

## Attack Surface + Other Features

### Works Great With:

**Exploit Suggestions**
- Attack Surface: Shows what to attack
- Exploit Suggestions: Shows how to attack it

**Correlation Engine**
- Attack Surface: Service-level status
- Correlation: Cross-phase tracking (user enum → brute force → session)

**Evidence Vault**
- Attack Surface: Shows exploitation progress
- Evidence Vault: Stores proof of exploitation

---

## Common Questions

### Q: Why is a low-severity finding giving a high attack surface score?

**A:** Attack surface measures *opportunity*, not *severity*. A host with 20 services (low severity) has more attack surface than a host with 1 service (critical).

Target high-severity findings *within* high attack surface hosts for maximum impact.

### Q: Service shows EXPLOITED but I don't have root access?

**A:** EXPLOITED means you successfully exploited the service (e.g., got valid credentials, confirmed SQLi). It doesn't mean full system compromise.

Check Evidence Vault for what was actually achieved.

### Q: Auto-exploit didn't work, what now?

**A:** Auto-exploit uses common techniques. For custom exploitation:
1. Research the specific service version
2. Check for public exploits (searchsploit)
3. Manual testing
4. Consult exploit suggestions for CVEs

### Q: Can I reset exploitation status?

**A:** Not directly. Status is calculated from jobs/findings. To "reset":
1. Re-run the exploitation attempt
2. Update findings if needed
3. Dashboard will recalculate automatically

---

## Troubleshooting

### Score Seems Wrong

**Possible causes:**
1. **Stale data** - Dashboard caches temporarily
2. **Findings not parsed** - Check if jobs completed
3. **Services not detected** - Verify Nmap scanned correctly

**Solution:**
- Refresh dashboard (exit and re-enter)
- Check job status: `souleyez jobs list`
- Re-run service scan if needed

### Auto-Exploit Not Enqueueing Jobs

**Possible causes:**
1. **Worker not running** - Jobs won't start
2. **No appropriate tool** - Service type not supported for auto-exploit
3. **Already attempted** - Auto-exploit only works on NOT TRIED

**Solution:**
```bash
# Check worker
souleyez worker status

# Start if stopped
souleyez worker start

# For unsupported services, manual exploitation required
```

---

## Next Steps

**Learn More:**
- [Exploit Suggestions Guide](exploit-suggestions.md) - Find CVEs and exploits for services
- [Correlation Engine Guide](correlation.md) - Track attack phases
- [Workflows Guide](workflows.md) - Complete pentesting workflows

**Related Commands:**
```bash
souleyez interactive                # Access Attack Surface Dashboard
souleyez services list              # See all discovered services
souleyez findings list --severity critical  # Check critical findings
```

---

**Need Help?** Check `docs/user-guide/troubleshooting.md` or open an issue on GitHub.
