# Getting Started Guide

## Introduction

Welcome to SoulEyez! This guide will help you run your first penetration test engagement in under 10 minutes.

## Prerequisites

✅ SoulEyez installed (see [Installation Guide](installation.md))
✅ At least one security tool installed (e.g., nmap)
✅ A target network or system you have permission to test

> **⚠️ LEGAL WARNING**: Only test systems you own or have explicit written authorization to test. Unauthorized scanning is illegal.

## Quick Start (5 Minutes)

### Step 1: Launch SoulEyez

Start the interactive interface:

```bash
# If using virtual environment
source venv/bin/activate
souleyez interactive

# If using pipx
souleyez interactive
```

### Step 2: First-Run Setup Wizard (First Time Only)

**On your first launch, you'll be guided through the setup wizard:**

```
   ███████╗ ██████╗ ██╗   ██╗██╗     ███████╗██╗   ██╗███████╗███████╗
   ██╔════╝██╔═══██╗██║   ██║██║     ██╔════╝╚██╗ ██╔╝██╔════╝╚══███╔╝
   ███████╗██║   ██║██║   ██║██║     █████╗   ╚████╔╝ █████╗    ███╔╝
   ╚════██║██║   ██║██║   ██║██║     ██╔══╝    ╚██╔╝  ██╔══╝   ███╔╝
   ███████║╚██████╔╝╚██████╔╝███████╗███████╗   ██║   ███████╗███████╗
   ╚══════╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝   ╚═╝   ╚══════╝╚══════╝

  Created by CyberSoul SecurITy
```

#### Setup Wizard Steps

| Step | Name | Description |
|------|------|-------------|
| 1 | **Welcome** | Introduction and overview of what to expect |
| 2 | **Encryption Setup** | Create vault master password (mandatory) |
| 3 | **Create Engagement** | Set up your first engagement with name and type |
| 4 | **Tool Availability** | Check which security tools are installed |
| 5 | **AI Features** | Configure Ollama for AI features (optional) |
| 6 | **Summary** | Review settings and option to run tutorial |

#### Step 2: Encryption Setup

SoulEyez encrypts all credentials with a master password. This is **mandatory** for security.

**Password Requirements:**
- At least 12 characters
- Mix of uppercase and lowercase
- At least one number
- At least one special character (!@#$%^&*)

> ⚠️ **If you lose this password, encrypted credentials cannot be recovered!**

#### Step 3: Create Your Engagement

Enter your engagement name (e.g., "ACME Corp Pentest" or "HackTheBox Lab").

Select your engagement type:
- **Penetration Test** - Full-scope security assessment
- **Bug Bounty** - Vulnerability hunting with defined scope
- **CTF/Lab** - Practice environment, aggressive scanning OK
- **Red Team** - Adversary simulation, stealth preferred
- **Custom** - Define your own parameters

> **Note:** Type affects default automation and scan aggressiveness

#### Step 4: Tool Availability

The wizard scans your system for installed security tools:
- Shows which tools are available (✓) and missing (✗)
- Shows version warnings for outdated tools (!)
- Option to install/upgrade missing tools

#### Step 5: AI Features (Optional)

Configure Ollama for AI-powered features:
- Checks if Ollama is installed and running
- Option to install Ollama if not present
- Option to download recommended model (llama3.1:8b)

#### Step 6: Summary & Tutorial

Review all your settings:
- Encryption status
- Engagement details
- Available tools count
- AI features status

**Tutorial Offer:** The wizard offers to run an interactive tutorial (recommended for new users).

> 💡 **Tip**: You can run the tutorial anytime from **Settings → [t] Tutorial**

### Step 3: Enter the Main Menu

After completing the wizard, you'll see the main menu:

```
⚡ MISSION CONTROL
════════════════════════════════════════════════════════════════════════════════
   Your central hub for intelligent pentesting

  [c ] 🧿 Command Center       - Live monitoring, attack surface, next actions
  [i ] 🕵️ Intelligence Hub     🔒 PRO - Host analysis, exploitation coverage, gaps
  [x ] 🤖 AI Execute           🔒 PRO - AI-driven autonomous execution
  [a ] 🔗 Automation           🔒 PRO - Chain rules & settings
  [m ] 🔧 Metasploit           🔒 PRO - Advanced exploitation & attack chains
  [r ] 📊 Reports & Export     🔒 PRO - Professional deliverables

🔍 PHASE 1: RECONNAISSANCE
────────────────────────────────────────────────────────────
   Gather information before active scanning (OSINT)

  [ 7]   theHarvester            - Email, domain, subdomain discovery
  [ 8]   WHOIS                   - Domain registration and ownership lookup
  [ 9]   DNSRecon                - DNS enumeration and subdomain discovery

🔬 PHASE 2: SCANNING & ENUMERATION
────────────────────────────────────────────────────────────
   Identify hosts, ports, services, shares, and web paths

  [10]   Nmap                    - Network scanner with presets
  [11]   CrackMapExec            - Windows/AD enumeration (SMB, WinRM, LDAP)
  ...

⚠️ PHASE 3: VULNERABILITY ANALYSIS
💥 PHASE 4: EXPLOITATION
🎯 PHASE 5: POST-EXPLOITATION

⚙️ OPERATIONS
────────────────────────────────────────────────────────────
   Monitor progress and manage engagement

  [j ] Job Queue                 - Manage active jobs and worker
  [e ] Engagements               - Switch or create engagements
  [h ] Help Center               - Documentation and guides
  [g ] Scan Phases Guide         - View recommended workflow
  [* ] Settings                  - Encryption and preferences

  [L ] Logout                    - End session
```

**🔒 PRO = Premium features** (AI, automation, Metasploit, reports)

### Step 4: Verify Your Engagement

If you completed the setup wizard, your first engagement is already created and active. You'll see it displayed at the top of the menu.

**To create additional engagements later:**

```
1. Press [e] for Engagement Management
2. Press [c] to Create New Engagement
3. Enter name: "ACME Corp Assessment"
4. (Optional) Enter description: "Internal network security assessment"
5. Press Enter to confirm
```

**Result**: Engagement created and automatically set as active.

### Step 5: Run Your First Scan

Navigate back to the main menu and launch a scan:

```
1. From the main menu, type [10] for Nmap (under Phase 2: Scanning & Enumeration)
2. Select a preset (e.g., [1] Quick Scan - Ping Sweep)
3. Enter target: 192.168.1.0/24
4. Confirm to start
```

**Job queued**: The scan runs in the background. The worker processes it automatically.

> 💡 **Tip**: Make sure the worker is running: `souleyez worker status`. Start it with: `souleyez worker start`

### Step 6: Monitor Progress

View running jobs from the Command Center:

```
1. Return to Main Menu (press [0] or 'q')
2. Press [c] for Command Center
3. See real-time job status and results
```

**Or check the job queue:**

```
1. From main menu, press [j] for Job Queue
2. See all jobs with status and progress
```

**Status indicators**:
- ⟳ Running
- ✓ Completed (done)
- ✗ Failed (error)
- ○ Pending (queued)

### Step 7: View Results

Check what was discovered from the Command Center:

```
1. Return to Main Menu (press [0] or 'q')
2. Press [c] for Command Center
3. Review the intelligence dashboard showing:
   - Attack Surface (hosts, ports, services)
   - Findings by severity
   - Credentials discovered
   - Job Queue Status
   - Evidence collection status
```

**From the Command Center, you can drill into details:**
- Attack Surface Dashboard - detailed host/service analysis
- Findings - vulnerabilities discovered with severity ratings
- Credentials - usernames/passwords with validation status
- Host details - OS info, ports, and service versions

**Congratulations!** You've completed your first scan with SoulEyez and learned the basics of the Command Center!

---

### Alternative: CLI Quick Start

For automation or scripting, use command-line interface:

```bash
# Create engagement
souleyez engagement create "ACME Corp Assessment" -d "Internal network security assessment"

# Set active
souleyez engagement use "ACME Corp Assessment"

# Run scan
souleyez jobs enqueue nmap 192.168.1.0/24 -a "-sn" -l "Network Discovery"

# View results
souleyez hosts list
souleyez services list
souleyez findings list
```

## Understanding Engagements

### What is an Engagement?

An engagement is a workspace that contains:
- **Hosts**: Discovered IP addresses and hostnames
- **Services**: Running services and ports
- **Findings**: Identified vulnerabilities
- **Credentials**: Discovered usernames/passwords
- **Jobs**: Command history and tool output

### Managing Engagements

```bash
# List all engagements
souleyez engagement list

# Switch between engagements
souleyez engagement use "Different Project"

# View current engagement
souleyez engagement list
```

**Why use engagements?**
- Separate client data
- Organize long-term projects
- Generate per-client reports
- Maintain audit trails

## Using the Interactive Menu

The interactive menu is the easiest way to use SoulEyez:

```bash
souleyez interactive
```

### Main Menu Options

From the main menu, you can access:

**Mission Control (Top Section)**
- `[c]` **Command Center** - Live monitoring dashboard with attack surface, findings
- `[i]` **Intelligence Hub** 🔒 PRO - Host analysis, exploitation coverage, gaps
- `[x]` **AI Execute** 🔒 PRO - AI-driven autonomous execution
- `[a]` **Automation** 🔒 PRO - Chain rules and auto-scan settings
- `[m]` **Metasploit** 🔒 PRO - Advanced exploitation and attack chains
- `[r]` **Reports & Export** 🔒 PRO - Professional deliverables and reports

**Phase-Organized Tools (Numbered)**
- **Phase 1: Reconnaissance** - theHarvester, WHOIS, DNSRecon
- **Phase 2: Scanning & Enumeration** - Nmap, CrackMapExec, SMBMap, Gobuster, ffuf
- **Phase 3: Vulnerability Analysis** - Nuclei, Nikto, WPScan, SearchSploit
- **Phase 4: Exploitation** - SQLMap, Hydra, Metasploit Auxiliary
- **Phase 5: Post-Exploitation** - Credential harvesting, lateral movement, data collection

**Operations (Bottom Section)**
- `[j]` **Job Queue** - Monitor and control background jobs
- `[e]` **Engagements** - Create, switch, and manage engagements
- `[h]` **Help Center** - Documentation and guides
- `[g]` **Scan Phases Guide** - View recommended workflow
- `[*]` **Settings** - Encryption and preferences
- `[L]` **Logout** - End session
- `[q]` **Quit** - Exit the application

### Running Tools

1. From main menu, type a tool number (e.g., `10` for Nmap under Phase 2)
2. Choose a preset or configure custom options
3. Enter target
4. Job is queued and runs in background

## Understanding the Command Center

The Command Center is your intelligence hub - it provides a real-time overview of your engagement:

**Access it from the interactive menu:**
```
Press [c] from the main menu
```

### Intelligence at a Glance

The Command Center shows comprehensive engagement intelligence:

1. **Attack Surface** - Total hosts, ports, services discovered with quick stats
2. **Exploit Suggestions** - Automated vulnerability recommendations based on service versions
3. **Credentials** - Total credentials, validity status, hash vs plaintext breakdown
4. **Job Queue Status** - Queued, running, completed, failed job counts
5. **Findings** - Severity breakdown (CRITICAL/HIGH/MEDIUM/LOW)
6. **Evidence Collection** - Screenshots, logs, artifacts by phase
7. **Deliverables** - Engagement deliverable progress tracking

**Navigation from Command Center:**
- Use menu options to drill into specific areas
- Attack Surface Dashboard for detailed host/service analysis
- Credentials Management for discovered passwords
- Findings for vulnerability details
- Evidence Vault for collected artifacts

### Read-Only Dashboard (Optional)

For monitoring only (no interactive controls):

```bash
souleyez dashboard
```

This auto-refreshing dashboard is useful for:
- Monitoring jobs on a second screen
- Read-only status viewing
- Quick checks without entering interactive mode

**Note:** Most users should use the interactive Command Center (`souleyez interactive` → `[c]`) for full functionality.

## CLI Command Basics

### Job Management

```bash
# Enqueue a job
souleyez jobs enqueue <tool> <target> -a "<args>" -l "Label"

# List jobs
souleyez jobs list

# View job details
souleyez jobs get <job_id>

# View job output
souleyez jobs get <job_id> --output
```

### Host Management

```bash
# List hosts
souleyez hosts list

# Add host manually
souleyez hosts add 192.168.1.100 -n "webserver.local"

# Get host details
souleyez hosts get 192.168.1.100
```

### Service Management

```bash
# List all services
souleyez services list

# Filter by port
souleyez services list --port 80

# Filter by host
souleyez services list --host 192.168.1.100
```

### Findings Management

```bash
# List findings
souleyez findings list

# Filter by severity
souleyez findings list --severity critical

# Add finding manually
souleyez findings add "SQL Injection" \
    --severity critical \
    --host 192.168.1.100 \
    --description "Login form vulnerable to SQLi"
```

### Credentials Management

```bash
# List credentials
souleyez creds list

# Add credential
souleyez creds add admin P@ssw0rd \
    --host 192.168.1.100 \
    --service ssh
```

> **Note**: Enable encryption for sensitive credentials (see [Security Guide](../security/credential-encryption.md))

## Common Workflows

### Workflow 1: Network Discovery

```bash
# 1. Quick host discovery
souleyez jobs enqueue nmap 192.168.1.0/24 -a "-sn" -l "Ping Scan"

# 2. Port scan live hosts
souleyez jobs enqueue nmap 192.168.1.100 -a "-p-" -l "Full Port Scan"

# 3. Service detection
souleyez jobs enqueue nmap 192.168.1.100 -a "-sV -sC -p 80,443,22" -l "Service Scan"
```

### Workflow 2: Web Application Testing

```bash
# 1. Basic vulnerability scan
souleyez jobs enqueue nikto http://192.168.1.100 -l "Nikto Scan"

# 2. Directory enumeration
souleyez jobs enqueue gobuster http://192.168.1.100 -a "dir -w data/wordlists/web_dirs_common.txt" -l "Dir Brute"

# 3. SQL injection testing
souleyez jobs enqueue sqlmap http://192.168.1.100/login.php?id=1 -l "SQLMap"
```

### Workflow 3: SMB Enumeration

```bash
# 1. Enumerate SMB
souleyez jobs enqueue enum4linux 192.168.1.100 -l "SMB Enum"

# 2. List shares
souleyez jobs enqueue smbmap 192.168.1.100 -l "SMB Shares"

# 3. Check null sessions
souleyez jobs enqueue smbclient "//192.168.1.100/share" -l "SMB Access"
```

## Auto-Chaining Feature

SoulEyez can automatically trigger follow-up scans based on discoveries.

**How it works:**
- When Nmap discovers an HTTP service → Automatically launches Nikto and Gobuster
- When theHarvester finds URLs with parameters → Automatically launches SQLMap
- When MySQL is detected → Automatically suggests exploitation options

**Configure auto-chaining:**
From the main menu, press `[a]` for Automation (🔒 PRO premium feature) to manage chain rules and approval settings.

**Examples of auto-chaining:**
1. **Web Services**: HTTP/HTTPS → Nikto, Gobuster, WhatWeb
2. **Database Services**: MySQL, PostgreSQL, MSSQL → Exploitation modules
3. **SMB Services**: Port 445 → Enum4Linux, SMBMap
4. **SSH Services**: Port 22 → SSH enumeration tools

The system intelligently avoids duplicate jobs and only chains when new information is discovered. For more details, see [AUTO_CHAINING.md](../AUTO_CHAINING.md).

### Chain Rule Builder

Create custom automation rules from the Automation menu:

**Simple Mode** - Quick rule creation:
1. Press `[a]` for Automation → `[n]` New Rule
2. Select trigger type (Service Discovery, Finding, Credential, etc.)
3. Choose condition (e.g., "HTTP service found")
4. Select action tool (e.g., Nikto, Gobuster)
5. Rule is saved and active

**Advanced Mode** - Complex multi-condition rules:
1. Press `[a]` for Automation → `[n]` New Rule → `[a]` Advanced
2. Build compound conditions with AND/OR logic
3. Add multiple actions per trigger
4. Set priorities and rate limits
5. Configure per-rule approval overrides

**Example custom rules:**
- "When port 3389 (RDP) found → run rdp-sec-check"
- "When admin credential found AND SSH open → run ssh-audit"
- "When WordPress detected → run WPScan with API key"

## Generating Reports

After testing, generate professional reports:

**From Interactive Menu:**
Press `[r]` for Reports & Export (🔒 PRO premium feature) to access professional deliverables.

**From CLI:**
```bash
# Generate HTML report
souleyez report generate "ACME Corp Final Report"

# Output location
ls reports/
```

Report includes:
- Executive summary
- Discovered hosts and services
- Findings by severity
- Discovered credentials
- Recommendations

## Best Practices

### 1. Always Create Engagements
Don't run scans without an active engagement. Data organization is critical.

### 2. Use Descriptive Labels
Label jobs clearly:
```bash
# Good
souleyez jobs enqueue nmap 10.0.0.1 -l "DC01 Full Port Scan"

# Bad
souleyez jobs enqueue nmap 10.0.0.1 -l "scan"
```

### 3. Monitor Dashboard Regularly
Stay aware of what's running and what's been found.

### 4. Document Findings Immediately
Add context while details are fresh:
```bash
souleyez findings add "Weak Password" \
    --severity medium \
    --host 10.0.0.1 \
    --description "Admin account uses password 'admin123'. Confirmed via SSH login."
```

### 5. Encryption is Always Enabled
Encryption is mandatory and configured during the setup wizard. Your credentials are protected with your vault master password.

To change your vault password:
```bash
souleyez db change-password
```

### 6. Regular Backups
```bash
# Backup database
cp ~/.souleyez/souleyez.db ~/.souleyez/backups/souleyez.db.backup-$(date +%Y%m%d)
```

## Tips & Tricks

### Keyboard Shortcuts
Learn the hotkeys for faster navigation (press `h` in any UI).

### Command History
Use shell history to repeat commands:
```bash
history | grep souleyez
!<number>  # Re-run command
```

### Tab Completion
If installed with completion support:
```bash
souleyez <TAB><TAB>  # Show commands
```

### Quick Status Check
```bash
# One-liner to see current status
souleyez engagement list && souleyez jobs list --status running
```

## Troubleshooting

### "No active engagement"
```bash
souleyez engagement list
souleyez engagement use "<name>"
```

### Job stuck or not starting
Check worker is running (jobs are processed by background worker):
```bash
souleyez worker status
souleyez worker start  # If not running
```

### Can't see job output
```bash
# View job logs
souleyez jobs get <job_id> --output

# Or check raw log file in user data directory
cat ~/.souleyez/artifacts/<job_id>.log
```

For more issues, see [Troubleshooting Guide](troubleshooting.md).

## What's Next?

Now that you're familiar with the basics:

1. **Explore More Tools**: Try different scanners and enumeration tools
   - Web Application Testing (Nikto, Gobuster, SQLMap)
   - SMB Enumeration (Enum4Linux, SMBMap)
   - Post-Exploitation (secretsdump, CrackMapExec)

2. **PRO Features** (🔒):
   - **Metasploit** `[m]` - Advanced exploitation and attack chains
   - **Automation** `[a]` - Configure auto-chaining rules and approval modes
   - **AI Execute** `[x]` - AI-driven autonomous execution
   - **Intelligence Hub** `[i]` - Host analysis, exploitation coverage, gaps
   - **Reports & Export** `[r]` - Professional deliverables

3. **Learn Advanced Features**:
   - [MSF Integration Guide](../MSF_INTEGRATION.md)
   - [Auto-Chaining](../AUTO_CHAINING.md)
   - [Worker Management](worker-management.md)

4. **Security Best Practices**:
   - [Credential Encryption](../security/credential-encryption.md)

5. **Reference Documentation**:
   - [Tools Reference](tools-reference.md)
   - [Configuration Guide](../CONFIG.md)

## Getting Help

- **Built-in help**: `souleyez --help`, `souleyez <command> --help`
- **Documentation**: Browse `docs/` directory
- **Issues**: https://github.com/cyber-soul-security/SoulEyez/issues
- **Interactive help**: Press `h` in any menu

Happy hacking! 🎯
