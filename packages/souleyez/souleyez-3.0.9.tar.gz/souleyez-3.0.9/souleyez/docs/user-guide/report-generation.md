# Report Generator - User Guide

**Last Updated:** 2025-12-23

---

## What is the Report Generator?

The Report Generator creates **professional penetration test reports** from your engagement data in seconds. No more manual copy-pasting from tools or spending hours formatting documents.

**One command → Client-ready report**

---

## Why Use the Report Generator?

### Problems It Solves

❌ **Before:**
- Manual report writing takes 2-4 hours
- Copy-pasting from multiple tools
- Inconsistent formatting
- Missing evidence
- Hard to include all findings

✅ **With Report Generator:**
- One-click report generation (<10 seconds)
- Automatic data aggregation from all sources
- Professional formatting (HTML/PDF/Markdown)
- All findings, evidence, and recommendations included
- Consistent, repeatable format

---

## Report Formats

### 1. Markdown (.md)

**Best For:** Version control, plain text editing, conversion to other formats

**Pros:**
- Human-readable
- Git-friendly
- Easy to edit
- Convert to anything

**Cons:**
- No styling
- Basic formatting

**Use Case:** Internal reviews, quick sharing with team

---

### 2. HTML (.html)

**Best For:** Web viewing, styled presentations, email attachments

**Pros:**
- Professional CSS styling
- Clickable table of contents
- Color-coded severity
- No extra software needed (opens in browser)

**Cons:**
- Single file (large for long reports)
- Requires browser to view

**Use Case:** Client deliverables, presentations, web publishing

---

### 3. PDF (.pdf)

**Best For:** Final client deliverables, archiving, printing

**Pros:**
- Professional appearance
- Universal compatibility
- Cannot be easily modified
- Suitable for official reports

**Cons:**
- Requires wkhtmltopdf installed
- Harder to edit later

**Use Case:** Final report submission, executive summaries, compliance documentation

**Requirement:**
```bash
# Install wkhtmltopdf for PDF generation
sudo apt-get install wkhtmltopdf
```

---

## AI-Enhanced Reports (PRO Feature)

SoulEyez supports **AI-powered report enhancement** using either Claude API or local Ollama. This feature generates professional, business-focused content automatically.

### What AI Adds to Your Report

| Section | AI Enhancement |
|---------|----------------|
| **Executive Summary** | Business-focused narrative with risk assessment and action timeline |
| **Finding Analysis** | Business impact, attack scenarios, and compliance context for each finding |
| **Remediation Plan** | Prioritized 4-phase remediation roadmap with effort estimates |
| **Risk Rating** | Overall organizational risk assessment with justification |

### Enabling AI Enhancement

#### Option 1: Interactive Menu

```
Reports & Export → Generate Report → [Select Type] → [Select Format]
→ AI Enhancement: [y] Yes
```

#### Option 2: Command Line

```bash
# Generate AI-enhanced HTML report
souleyez report generate --format html --ai

# Generate AI-enhanced executive report
souleyez report generate --format pdf --type executive --ai
```

### Choosing an AI Provider

| Feature | Ollama (Local) | Claude (Cloud) |
|---------|----------------|----------------|
| **Cost** | Free | ~$0.02-0.04/report |
| **Speed** | 30-60 seconds | 10-20 seconds |
| **Quality** | Good | Excellent |
| **Privacy** | Data stays local | Data sent to Anthropic |
| **Setup** | Install Ollama | Get API key + credits |
| **Internet** | Not required | Required |

**Recommendation:**
- **Ollama** for: Privacy-sensitive engagements, offline use, budget constraints
- **Claude** for: Client-facing reports, best quality executive summaries

### Configuring AI Providers

#### Claude API (Recommended for Quality)

Claude produces excellent business writing for executive summaries and remediation plans.

**Step 1: Get an API Key**
1. Go to https://console.anthropic.com
2. Sign up or log in with your email
3. Navigate to **API Keys** in the left sidebar
4. Click **Create Key** and give it a name (e.g., "SoulEyez")
5. Copy the key (starts with `sk-ant-api03-...`)

**Step 2: Add Credits**
1. Go to **Billing** in the console
2. Add at least $5 in credits
3. Cost per report: ~$0.02-0.04 (so $5 = ~125+ reports)

**Step 3: Configure SoulEyez**
```bash
# Set your API key (stored encrypted)
souleyez config set ai.claude_api_key sk-ant-api03-xxxxx

# Set Claude as default provider (optional - can also select in UI)
souleyez config set ai.provider claude

# Optional: Change model (default: claude-sonnet-4-20250514)
souleyez config set ai.claude_model claude-sonnet-4-20250514
```

**Step 4: Verify Setup**
```bash
# Check your configuration
souleyez config get ai.provider
souleyez config get ai.claude_api_key
```

**Requirements:**
- Anthropic API key with credits
- PRO tier license
- Internet connection

**Privacy Notice:**
When using Claude, the following engagement data is sent to Anthropic's servers:
- Finding titles, descriptions, and severity
- Host IPs and hostnames
- Service names and ports
- Credential metadata (usernames, not passwords)

This data is used only for AI processing and is not stored by Anthropic after the request completes. Review Anthropic's privacy policy at https://anthropic.com/privacy.

For sensitive engagements where data must remain local, use Ollama instead.

#### Ollama (Free, Local)

```bash
# Set Ollama as provider
souleyez config set ai.provider ollama

# Optional: Change model (default: llama3.1:8b)
souleyez config set ai.ollama_model llama3.1:8b

# Ensure Ollama is running
ollama serve
```

**Requirements:**
- Ollama installed: https://ollama.ai
- Model downloaded: `ollama pull llama3.1:8b`
- PRO tier license (feature is PRO-gated)

### AI Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `ai.provider` | `ollama` | `claude` or `ollama` |
| `ai.claude_api_key` | `None` | Your Anthropic API key (encrypted) |
| `ai.claude_model` | `claude-sonnet-4-20250514` | Claude model to use |
| `ai.ollama_model` | `llama3.1:8b` | Ollama model to use |
| `ai.max_tokens` | `4096` | Max tokens per generation |
| `ai.temperature` | `0.3` | Generation temperature (lower = more focused) |

### Token Usage & Cost

**Claude API (estimated per report):**
- Executive summary: ~500-800 tokens
- Remediation plan: ~800-1200 tokens
- Finding enhancements (top 10): ~2000-3000 tokens
- **Total per report:** ~3500-5000 tokens (~$0.02-0.04 with Claude Sonnet)

**Ollama:** Free (runs locally)

### Example AI-Generated Content

**AI Executive Summary:**
```
The security assessment of ACME Corporation revealed significant
vulnerabilities that pose immediate risk to business operations.
Three critical findings, including SQL injection in the customer
portal, could enable complete database compromise and regulatory
non-compliance under GDPR and PCI-DSS frameworks.

Immediate action is required to address authentication bypass
vulnerabilities that provide unauthenticated access to internal
systems. The estimated financial impact of exploitation ranges
from $150,000-$500,000 in incident response costs, with additional
regulatory penalties possible.

Recommended Timeline:
- Immediate (24-48h): Patch critical SQL injection, rotate credentials
- Short-term (1-2 weeks): Address high-priority access control issues
- Medium-term (30 days): Implement systematic hardening measures
```

**AI Remediation Plan (excerpt):**
```
## IMMEDIATE (24-48 hours)

1. **SQL Injection in Login Form** (4-6 hours)
   - Deploy parameterized queries in login.php
   - Required: Developer with PHP/MySQL experience
   - Success criteria: SQLMap scan returns no vulnerabilities

2. **Default MySQL Credentials** (30 minutes)
   - Change root password, create application-specific user
   - Required: Database administrator access
   - Dependencies: Update application connection strings

## SHORT-TERM (1-2 weeks)
...
```

### Troubleshooting AI Reports

**AI not available:**
```
⚠ AI not available. Falling back to standard report.
```

**Solutions:**
1. **For Claude:** Check API key is set correctly
   ```bash
   souleyez config get ai.claude_api_key
   ```
2. **For Ollama:** Ensure Ollama is running
   ```bash
   ollama serve  # Start Ollama
   ollama list   # Verify model is downloaded
   ```

**Generation timeout:**
- Large engagements may take 30-60 seconds for AI enhancement
- Progress indicator shows during generation

---

## Report Structure

Every report includes **9 standardized sections**:

### 1. Executive Summary
**Target Audience:** Management, non-technical stakeholders

**What's Included:**
- Overall risk assessment (Low/Medium/High/Critical)
- Key findings summary (top 3-5 issues)
- High-level statistics
- Immediate action recommendations

**Example:**
```
EXECUTIVE SUMMARY

Risk Level: HIGH

Three critical vulnerabilities were identified that could result in
complete system compromise:

1. SQL Injection (http://app.acme.com/login.php) - CRITICAL
2. Default Credentials (MySQL root account) - HIGH
3. Outdated SSH Version (CVE-2023-XXXX) - HIGH

Immediate Actions Required:
- Patch SQL injection vulnerability (Priority 1)
- Change default MySQL credentials (Priority 1)
- Update SSH to latest version (Priority 2)
```

---

### 2. Engagement Overview
**Target Audience:** All readers

**What's Included:**
- Scope of testing
- Timeline (start/end dates)
- Tools used
- Methodology (PTES-based)
- Limitations and constraints

**Example:**
```
ENGAGEMENT OVERVIEW

Client: ACME Corporation
Engagement: acme-corp-pentest
Duration: Nov 1-5, 2025 (5 days)

Scope:
- External network: 10.0.0.0/24
- Web applications: *.acme.com
- No social engineering
- No DoS testing

Tools Used: Nmap, Nikto, SQLMap, Gobuster, Hydra, Metasploit
```

---

### 3. Attack Surface Analysis
**Target Audience:** Technical team, security engineers

**What's Included:**
- Top 5 hosts by attack surface score
- Service breakdown
- Exploitation progress
- High-value targets identified

**Example:**
```
ATTACK SURFACE ANALYSIS

Top Targets:
1. 10.0.0.82 (web-server) - Score: 115 - 4/5 services exploited
2. 10.0.0.5 (db-server) - Score: 85 - 0/3 services exploited
3. 10.0.0.10 (mail-server) - Score: 62 - 2/4 services exploited

Total Services Scanned: 24
Services Exploited: 6 (25%)
```

---

### 4. Findings Summary
**Target Audience:** All readers

**What's Included:**
- Findings count by severity
- Findings by category (Web, Network, Credentials)
- Quick statistics

**Example:**
```
FINDINGS SUMMARY

By Severity:
- Critical: 3 findings
- High: 8 findings
- Medium: 15 findings
- Low: 22 findings

By Category:
- Web Application: 18 findings
- Network Security: 12 findings
- Credentials: 10 findings
- Configuration: 8 findings
```

---

### 5. Detailed Findings
**Target Audience:** Technical team, developers

**What's Included:**
For each finding:
- Title and severity
- Description
- Affected system/URL
- Evidence (commands run, output)
- Impact
- Remediation steps
- References (CVE, CWE)

**Example:**
```
FINDING #1: SQL Injection in Login Form

Severity: CRITICAL
Affected: http://app.acme.com/login.php?id=1
Tool: SQLMap

Description:
The login.php endpoint is vulnerable to SQL injection via the 'id'
parameter. An attacker can bypass authentication and extract database
contents.

Evidence:
Command: sqlmap --url="http://..." --dbs
Result: 3 databases enumerated (mysql, information_schema, app_db)

Impact:
- Complete database compromise
- Unauthorized data access
- Potential admin account creation
- Data exfiltration

Remediation:
1. Use parameterized queries (prepared statements)
2. Implement input validation
3. Apply least privilege database permissions
4. Add WAF rules to detect SQL injection attempts

References:
- OWASP A03:2021 - Injection
- CWE-89: SQL Injection
```

---

### 6. Evidence Collection
**Target Audience:** Technical team, auditors

**What's Included:**
- Evidence summary by phase
- Number of artifacts collected
- Key discoveries per phase
- Link to full evidence bundle

**Example:**
```
EVIDENCE COLLECTION

Reconnaissance (12 items):
- Email addresses: 15 discovered
- Subdomains: 5 identified
- IP addresses: 3 mapped

Enumeration (28 items):
- Hosts scanned: 8
- Services identified: 24
- Directories discovered: 147

Exploitation (6 items):
- Valid credentials: 4 pairs
- SQL injection: 1 confirmed
- Sessions opened: 2

Complete evidence bundle: evidence-acme-corp-20251105.zip
```

---

### 7. Recommendations
**Target Audience:** IT team, management

**What's Included:**
- Prioritized action items
- Quick wins (easy fixes)
- Long-term improvements
- Security best practices

**Example:**
```
RECOMMENDATIONS

Immediate Actions (Within 1 week):
1. Patch SQL injection in login.php (CRITICAL)
2. Change default MySQL root password (CRITICAL)
3. Disable FTP service (not needed)

Short-term (Within 1 month):
4. Update SSH to latest version
5. Implement strong password policy
6. Enable MFA for admin accounts

Long-term (Within 3 months):
7. Deploy WAF for web applications
8. Implement network segmentation
9. Conduct security awareness training
10. Establish regular vulnerability scanning
```

---

### 8. Methodology
**Target Audience:** Auditors, compliance teams

**What's Included:**
- PTES phases followed
- Testing approach
- Tools and techniques
- Ethical considerations

**Example:**
```
METHODOLOGY

This penetration test followed the Penetration Testing Execution
Standard (PTES) methodology:

Phase 1: Pre-Engagement
- Scope definition and rules of engagement
- Authorization obtained

Phase 2: Intelligence Gathering
- OSINT reconnaissance
- DNS enumeration
- Subdomain discovery

Phase 3: Threat Modeling
- Attack surface identification
- Target prioritization

Phase 4: Vulnerability Analysis
- Port scanning
- Service enumeration
- Vulnerability scanning

Phase 5: Exploitation
- Manual exploitation attempts
- Credential attacks
- Web application testing

Phase 6: Post-Exploitation
- Privilege escalation testing
- Lateral movement analysis

Phase 7: Reporting
- Findings documentation
- Evidence collection
- Report generation
```

---

### 9. Appendix
**Target Audience:** Technical team (reference)

**What's Included:**
- Complete host list
- All services discovered
- All credentials found (sanitized)
- Tool versions used
- Scan command references

**Example:**
```
APPENDIX A: Host Inventory

10.0.0.82 (web-server.acme.local)
- OS: Linux 3.13
- Services: FTP (21), SSH (22), HTTP (80), MySQL (3306)
- Status: 4/4 services tested

10.0.0.5 (db-server.acme.local)
- OS: Linux 4.4
- Services: SSH (22), MySQL (3306), PostgreSQL (5432)
- Status: 0/3 services tested

...

APPENDIX B: Tool Versions

- Nmap: 7.94
- SQLMap: 1.7.2
- Metasploit: 6.3.10
- Hydra: 9.4
```

---

## Generating Reports

### Method 1: Interactive Menu

```bash
# Start interactive dashboard
souleyez interactive

# Navigate to:
Reports & Export → Generate Report

# Select format:
- [m] Markdown
- [h] HTML
- [p] PDF
```

---

### Method 2: Command Line

```bash
# Generate HTML report (recommended)
souleyez report generate --format html

# Generate PDF report
souleyez report generate --format pdf

# Generate AI-enhanced report (PRO feature)
souleyez report generate --format html --ai

# Generate executive report with AI
souleyez report generate --format pdf --type executive --ai

# Custom output path
souleyez report generate --format html --output /path/to/report.html
```

---

### Generation Speed

**Typical Performance:**
- Markdown: 2-3 seconds
- HTML: 5-8 seconds
- PDF: 8-12 seconds (includes HTML → PDF conversion)

**For engagements with:**
- < 50 findings: < 10 seconds
- 50-200 findings: 10-30 seconds
- > 200 findings: 30-60 seconds

---

## Report Output Location

### Default Paths

**Interactive Menu:**
```
~/.souleyez/reports/[engagement-name]-[date]-[format].ext
```

**Command Line:**
```
./souleyez-report-[engagement]-[timestamp].[format]
```

**Example:**
```
~/.souleyez/reports/acme-corp-pentest-20251105-143022.html
~/.souleyez/reports/acme-corp-pentest-20251105-143022.pdf
~/.souleyez/reports/acme-corp-pentest-20251105-143022.md
```

---

## Customizing Reports

### Template Customization (Future Feature)

Currently, reports use the built-in professional template. Future versions will support:
- Custom company logos
- Custom color schemes
- Custom section ordering
- Client-specific templates

**Workaround for now:**
1. Generate Markdown report
2. Edit Markdown file manually
3. Convert to HTML/PDF using external tools

---

## Best Practices

### ✅ Do

1. **Review Before Generating**
   - Verify all scans completed
   - Check findings are accurate
   - Ensure credentials are sanitized

2. **Generate Multiple Formats**
   - PDF for client deliverable
   - HTML for internal review
   - Markdown for version control

3. **Include Evidence Bundle**
   - Export Evidence Vault as ZIP
   - Attach to report as supplementary material
   - Provides proof for all findings

4. **Sanitize Sensitive Data**
   - Don't include cleartext passwords in final report
   - Redact sensitive URLs if needed
   - Check screenshots for sensitive info

### ❌ Don't

1. **Don't Send Unreviewed Reports**
   - Always manual review first
   - Verify findings are accurate
   - Check for false positives

2. **Don't Include Everything**
   - Low-priority findings can clutter report
   - Focus on actionable items
   - Use appendix for comprehensive data

3. **Don't Forget Context**
   - Add custom notes where needed
   - Explain business impact
   - Provide realistic remediation timelines

---

## Report Quality Checklist

Before delivering to client:

- [ ] All critical/high findings included
- [ ] Evidence provided for each finding
- [ ] Remediation steps are clear and actionable
- [ ] No false positives
- [ ] Sensitive data sanitized
- [ ] Executive summary is non-technical
- [ ] Scope and limitations documented
- [ ] Professional formatting (no errors)
- [ ] Contact information included
- [ ] Evidence bundle attached

---

## Common Questions

### Q: Can I edit the generated report?

**A:** Yes!
- **Markdown:** Edit directly in any text editor
- **HTML:** Edit HTML source (requires HTML knowledge)
- **PDF:** Hard to edit; regenerate from Markdown instead

**Best Practice:** Generate Markdown → Edit → Convert to HTML/PDF

---

### Q: What if I have 500+ findings?

**A:** Large reports work fine but may be overwhelming.

**Solutions:**
1. **Filter by severity:** Only include Critical/High in main report
2. **Create summary report:** Top 10-20 findings
3. **Separate appendix:** Full findings in supplementary document
4. **Multiple reports:** By category (Web, Network, etc.)

---

### Q: Can I schedule automatic report generation?

**A:** Not yet, but you can script it:

```bash
#!/bin/bash
# daily-report.sh

souleyez engagement use "ongoing-assessment"
souleyez report generate --format html --output /reports/daily-$(date +%Y%m%d).html
```

---

### Q: How do I include screenshots?

**A:** Screenshots are managed separately:

```bash
# Add screenshot to engagement
souleyez screenshots add --file screenshot.png --description "SQLi proof" --phase exploitation

# Screenshots will be referenced in report
# Future: Inline screenshots in HTML/PDF reports
```

---

## Troubleshooting

### PDF Generation Fails

**Error:** `wkhtmltopdf not found`

**Solution:**
```bash
sudo apt-get install wkhtmltopdf

# Test installation
wkhtmltopdf --version
```

---

### Report is Missing Findings

**Possible causes:**
1. **Jobs not completed** - Check job status
2. **Parser failed** - Findings not extracted
3. **Filter applied** - Check if severity filter active

**Solution:**
```bash
# Verify findings exist
souleyez findings list

# Check job completion
souleyez jobs list --status completed

# Reparse if needed
souleyez jobs reparse <job_id>
```

---

### Report Generation Hangs

**Possible causes:**
1. **Too many findings** (>1000) - Be patient!
2. **Disk space full** - Check available space
3. **Database locked** - Close other SoulEyez processes

**Solution:**
```bash
# Check disk space
df -h

# Check for locks
ps aux | grep souleyez

# Kill hung processes if needed
killall -9 souleyez
```

---

## Next Steps

**Learn More:**
- [Evidence Vault Guide](evidence-vault.md) - Collect comprehensive evidence
- [Attack Surface Dashboard](attack-surface.md) - Track testing progress
- [Findings Management](../database/SCHEMA.md) - Understanding findings data

**Related Commands:**
```bash
souleyez report generate --format html     # Generate report
souleyez findings list --severity critical # Review findings
souleyez evidence export --format zip      # Export evidence
```

---

**Need Help?** Check `docs/user-guide/troubleshooting.md` or open an issue on GitHub.
