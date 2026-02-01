# Evidence Vault - User Guide

**Last Updated:** 2025-11-18

---

## What is the Evidence Vault?

The Evidence Vault is your **centralized evidence collection system** for penetration testing engagements. Instead of hunting through multiple files, folders, and tool outputs, all your evidence is organized in one place.

Think of it as a **digital filing cabinet** that automatically organizes all artifacts by penetration testing phase.

---

## Why Use the Evidence Vault?

### Problems It Solves

❌ **Before Evidence Vault:**
- Evidence scattered across Metasploit, text files, screenshots folder
- Hard to find what evidence you collected
- Manual bundling for reports takes forever
- Easy to miss important artifacts
- No standard organization

✅ **With Evidence Vault:**
- Single source of truth for all evidence
- Automatic organization by methodology phase
- One-click export of complete evidence bundle
- Quick filtering by tool, host, or date
- Professional evidence management

---

## How Evidence is Organized

The Evidence Vault uses the **PTES (Penetration Testing Execution Standard)** methodology phases:

### 1. **Reconnaissance** 🔍
Tools: theHarvester, dnsrecon, whois
- OSINT intelligence
- Email addresses discovered
- Domain information
- Infrastructure mapping

### 2. **Enumeration** 📊
Tools: Nmap, Nikto, Gobuster, enum4linux
- Port scans
- Service detection
- Directory listings
- SMB shares
- User enumeration

### 3. **Exploitation** 💥
Tools: SQLMap, Metasploit, Hydra, Hashcat
- Vulnerability exploitation attempts
- Brute-force attacks
- SQL injection tests
- Password cracking results

### 4. **Post-Exploitation** 🎯
Tools: Metasploit sessions, credential dumps
- System access evidence
- Privilege escalation
- Lateral movement
- Data exfiltration

---

## Accessing the Evidence Vault

### Option 1: Interactive Menu

```bash
# Start interactive dashboard
souleyez interactive

# Navigate to:
Reports & Export → Evidence Vault
```

### Option 2: Direct Command (Coming Soon)

```bash
# View all evidence
souleyez evidence list

# Export evidence bundle
souleyez evidence export --format zip
```

---

## Using the Evidence Vault

### Viewing Evidence

**What You'll See:**

```
┌─ Evidence Vault ────────────────────────────────────────┐
│ Engagement: acme-corp-pentest                          │
│ Total Items: 47 artifacts                              │
└────────────────────────────────────────────────────────┘

RECONNAISSANCE (12 items)
  [2025-11-05 14:32] theHarvester → example.com
    → 15 emails, 3 IPs, 5 subdomains discovered

  [2025-11-05 14:35] dnsrecon → example.com
    → DNS enumeration: 8 A records, 2 MX records

ENUMERATION (28 items)
  [2025-11-05 14:40] Nmap → 10.0.0.82
    → 5 open ports: 21,22,80,3306,8080

  [2025-11-05 14:45] Gobuster → http://10.0.0.82
    → 23 directories found (200 status)

EXPLOITATION (6 items)
  [2025-11-05 15:10] SQLMap → http://10.0.0.82/login.php
    → SQL injection CONFIRMED (MySQL 5.7)
    → 3 databases enumerated

  [2025-11-05 15:20] Hydra → ssh://10.0.0.82
    → Valid credentials: admin:password123

POST-EXPLOITATION (1 item)
  [2025-11-05 15:45] Metasploit → 10.0.0.82
    → Shell session opened
```

### Filtering Evidence

Use filters to find specific evidence:

**By Tool:**
- Filter to see only Nmap scans
- Filter to see only SQLMap tests
- Filter to see only credential discoveries

**By Host:**
- See all evidence for specific IP address
- Track evidence across multiple hosts

**By Date:**
- Evidence from today
- Evidence from last week
- Custom date range

---

## Exporting Evidence

### Complete Evidence Bundle (ZIP Export)

**What's Included:**

```
evidence-bundle-acme-corp-20251105.zip
├── README.txt                 # Engagement summary
├── reconnaissance/
│   ├── theharvester_output.txt
│   ├── dnsrecon_output.txt
│   └── whois_output.txt
├── enumeration/
│   ├── nmap_scans/
│   │   ├── 10.0.0.82_scan.xml
│   │   ├── 10.0.0.83_scan.xml
│   │   └── ...
│   ├── gobuster_directories.txt
│   └── nikto_scan.txt
├── exploitation/
│   ├── sqlmap_results.txt
│   ├── hydra_credentials.txt
│   └── metasploit_sessions.txt
├── post-exploitation/
│   └── loot/
├── credentials.txt            # All discovered credentials
└── findings.txt               # All vulnerability findings
```

### How to Export

1. **Open Evidence Vault** (Reports & Export menu)
2. **Review evidence** to ensure everything is captured
3. **Press 'e' for Export**
4. **Select ZIP format**
5. **File saved** to: `~/.souleyez/exports/evidence-bundle-[engagement]-[date].zip`

---

## Evidence Auto-Collection

Evidence is **automatically collected** when you run tools:

### What Gets Collected

✅ **Command Execution**
- Full command that was run
- Arguments and parameters
- Timestamp of execution

✅ **Tool Output**
- Complete stdout/stderr
- Parsed results (when available)
- Error messages (if any)

✅ **Discovered Data**
- Findings extracted
- Credentials found
- Services identified
- Vulnerabilities detected

✅ **Metadata**
- Tool name and version
- Target (host/URL)
- Duration
- Success/failure status

### Example: Automatic Evidence Flow

```
1. You run: souleyez jobs enqueue nmap 10.0.0.82

2. Nmap executes and completes

3. Evidence Vault automatically stores:
   - Command: nmap -sV -sC 10.0.0.82
   - Output: Full scan results (XML + text)
   - Findings: 5 open ports detected
   - Phase: ENUMERATION
   - Timestamp: 2025-11-05 14:40:23

4. Available immediately in Evidence Vault
```

---

## Best Practices

### ✅ Do

1. **Review Evidence Regularly**
   - Check Evidence Vault after major scan phases
   - Verify important results are captured

2. **Export Evidence Frequently**
   - Export after each major phase
   - Keep backups of evidence bundles

3. **Use Descriptive Labels**
   - Label jobs clearly: `--label "NMAP_WEB_SERVER"`
   - Makes evidence easier to find later

4. **Combine with Screenshots**
   - Evidence Vault captures tool output
   - Add screenshots for visual evidence (GUI apps, web pages)

### ❌ Don't

1. **Don't Rely Only on Evidence Vault**
   - Take additional notes
   - Capture screenshots for critical findings
   - Document your methodology

2. **Don't Delete Engagement Too Soon**
   - Export evidence first
   - Keep engagement until report is delivered

3. **Don't Mix Personal/Test Data**
   - Use separate engagements for testing
   - Keep client data isolated

---

## Evidence Vault + Other Features

### Works Great With:

**Attack Surface Dashboard**
- Evidence Vault: Stores what you found
- Attack Surface: Shows what you haven't exploited yet

**Report Generator**
- Evidence Vault: Provides all artifacts
- Report Generator: Organizes into professional report

**Correlation Engine**
- Evidence Vault: Raw evidence storage
- Correlation: Links evidence across phases

---

## Common Questions

### Q: Does Evidence Vault store everything forever?

**A:** Evidence is stored until you delete the engagement. Export evidence bundles to keep long-term archives.

### Q: What if I run a scan outside of SoulEyez?

**A:** Manual evidence can be added:
1. Save tool output to text file
2. Add as finding: `souleyez findings add --tool nmap --file scan.txt`
3. Evidence will be included in vault

### Q: Can I customize evidence organization?

**A:** The 4-phase structure follows PTES standard and isn't customizable. However, you can:
- Use filters to view by tool/host/date
- Export and reorganize in your own format
- Use labels for additional organization

### Q: How much storage does evidence use?

**A:** Typical engagement uses 10-100 MB for evidence. Large scans (full subnet Nmap) may use more. Monitor with:
```bash
du -sh ~/.souleyez/
```

---

## Troubleshooting

### Evidence Not Showing Up

**Possible causes:**
1. **Job hasn't completed** - Check job status
2. **Parser failed** - Check job output for errors
3. **No results** - Tool may have found nothing (not an error)

**Solution:**
```bash
# Check if job completed
souleyez jobs get <job_id>

# Manually reparse if needed
souleyez jobs reparse <job_id>
```

### Export Failed

**Possible causes:**
1. **Disk space full** - Check available space
2. **Permission denied** - Check ~/.souleyez/ permissions
3. **No evidence** - Engagement has no completed jobs

**Solution:**
```bash
# Check disk space
df -h

# Check permissions
ls -la ~/.souleyez/

# Verify evidence exists
# Open Evidence Vault and check item count
```

---

## Next Steps

**Learn More:**
- [Report Generator Guide](report-generation.md) - Turn evidence into professional reports
- [Attack Surface Dashboard](attack-surface.md) - Track what's been exploited
- [Workflows Guide](workflows.md) - Complete pentesting workflows

**Related Commands:**
```bash
souleyez interactive          # Access Evidence Vault via menu
souleyez jobs list           # See what evidence is being collected
souleyez findings list       # View findings included in vault
```

---

**Need Help?** Check `docs/user-guide/troubleshooting.md` or open an issue on GitHub.
