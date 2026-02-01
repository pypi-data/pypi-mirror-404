# Tool Usage Reference

**Purpose:** Quick reference for all integrated security tools in SoulEyez

**Last Updated:** 2025-11-18

---

## Overview

SoulEyez integrates **20+ security tools** for comprehensive penetration testing. This guide provides quick reference information for each tool, including purpose, common commands, and use cases.

---

## Table of Contents

1. [Reconnaissance Tools](#reconnaissance-tools)
2. [Web Application Tools](#web-application-tools)
3. [Network Tools](#network-tools)
4. [Credential Tools](#credential-tools)
5. [Exploitation Tools](#exploitation-tools)
6. [Quick Command Reference](#quick-command-reference)

---

## Reconnaissance Tools

### 1. Nmap - Network Discovery & Port Scanning

**Purpose:** Discover hosts, open ports, and services on a network

**Common Use Cases:**
- Initial network reconnaissance
- Service version detection
- OS fingerprinting
- Vulnerability scanning (with NSE scripts)

**SoulEyez Commands:**
```bash
# Quick scan (top 1000 ports)
souleyez jobs enqueue nmap 10.0.0.82

# Full scan (all ports)
souleyez jobs enqueue nmap 10.0.0.82 --args="-p-"

# Service version detection
souleyez jobs enqueue nmap 10.0.0.82 --args="-sV"

# Aggressive scan (OS, version, scripts, traceroute)
souleyez jobs enqueue nmap 10.0.0.82 --args="-A"

# Stealth scan (SYN scan, no ping)
souleyez jobs enqueue nmap 10.0.0.82 --args="-sS -Pn"
```

**Common Arguments:**
- `-sV` - Service version detection
- `-sC` - Default NSE scripts
- `-p-` - Scan all 65535 ports
- `-T4` - Faster timing (0-5, default is 3)
- `-Pn` - Skip host discovery (treat as online)
- `-A` - Aggressive scan (OS, version, scripts)

**Output:** Hosts, services, ports added to engagement

---

### 2. theHarvester - OSINT Data Collection

**Purpose:** Gather emails, subdomains, IPs from public sources

**Common Use Cases:**
- Email address discovery for phishing campaigns
- Subdomain enumeration
- IP address collection
- Employee name harvesting

**SoulEyez Commands:**
```bash
# Search all sources
souleyez jobs enqueue theharvester example.com

# Specific source
souleyez jobs enqueue theharvester example.com --args="-b google"

# Deep search with DNS resolution
souleyez jobs enqueue theharvester example.com --args="-b all -c"
```

**Common Sources (`-b` flag):**
- `all` - All sources
- `google` - Google search
- `bing` - Bing search
- `linkedin` - LinkedIn
- `hunter` - Hunter.io API
- `shodan` - Shodan (requires API key)

**Output:** OSINT data (emails, IPs, subdomains) added to database

**Auto-Chaining:** Automatically triggers:
- WHOIS lookups on discovered domains
- DNS reconnaissance on subdomains
- SQLMap scans on discovered endpoints

---

### 3. DNSRecon - DNS Enumeration

**Purpose:** DNS reconnaissance and enumeration

**Common Use Cases:**
- Zone transfer attempts
- Subdomain brute-forcing
- DNS record enumeration
- Reverse DNS lookups

**SoulEyez Commands:**
```bash
# Standard enumeration
souleyez jobs enqueue dnsrecon example.com

# Zone transfer attempt
souleyez jobs enqueue dnsrecon example.com --args="-t axfr"

# Subdomain brute force
souleyez jobs enqueue dnsrecon example.com --args="-t brt -D /path/to/wordlist.txt"
```

**Common Arguments:**
- `-t std` - Standard DNS enumeration (default)
- `-t axfr` - Zone transfer
- `-t brt` - Brute force subdomains
- `-D <wordlist>` - Wordlist for brute forcing

**Output:** DNS records, subdomains added to database

---

### 4. WHOIS - Domain Registration Lookup

**Purpose:** Retrieve domain registration information

**Common Use Cases:**
- Identify domain owner
- Find registration dates
- Discover name servers
- Locate abuse contacts

**SoulEyez Commands:**
```bash
# Lookup domain
souleyez jobs enqueue whois example.com

# IP address lookup
souleyez jobs enqueue whois 8.8.8.8
```

**Output:** Domain registration info stored as OSINT data

---

## Web Application Tools

### 5. Nikto - Web Server Scanner

**Purpose:** Scan web servers for vulnerabilities and misconfigurations

**Common Use Cases:**
- Identify outdated software versions
- Discover dangerous files/CGIs
- Check for misconfigurations
- Find common vulnerabilities

**SoulEyez Commands:**
```bash
# Scan web server
souleyez jobs enqueue nikto http://10.0.0.82

# Scan specific port
souleyez jobs enqueue nikto http://10.0.0.82:8080

# SSL scan
souleyez jobs enqueue nikto https://example.com
```

**Common Arguments:**
- `-h <host>` - Target host (auto-added)
- `-p <port>` - Port to scan
- `-ssl` - Force SSL mode
- `-Tuning <1-9>` - Scan tuning (1=interesting files, 2=misconfigs, etc.)

**Output:** Web vulnerabilities added as findings

**Auto-Chaining:** Automatically triggered after Nmap discovers HTTP/HTTPS services

---

### 6. Gobuster - Directory/File Brute-Forcing

**Purpose:** Discover hidden directories, files, and virtual hosts

**Common Use Cases:**
- Find hidden admin panels
- Discover backup files
- Enumerate API endpoints
- Virtual host discovery

**SoulEyez Commands:**
```bash
# Directory brute-force
souleyez jobs enqueue gobuster http://10.0.0.82

# With custom wordlist
souleyez jobs enqueue gobuster http://10.0.0.82 --args="-w /path/to/wordlist.txt"

# File brute-force (specific extensions)
souleyez jobs enqueue gobuster http://10.0.0.82 --args="-x php,html,txt"

# DNS subdomain enumeration
souleyez jobs enqueue gobuster example.com --args="dns -d example.com"
```

**Common Arguments:**
- `dir` - Directory brute-forcing mode (default)
- `dns` - DNS subdomain mode
- `vhost` - Virtual host mode
- `-w <wordlist>` - Wordlist path
- `-x <extensions>` - File extensions to search
- `-t <threads>` - Number of threads (default: 10)
- `-s <status codes>` - Status codes to match (default: 200,204,301,302,307,401,403)

**Output:** Web paths added to database with status codes

**Auto-Chaining:** Automatically triggered after Nmap discovers HTTP/HTTPS services

---

### 7. SQLMap - SQL Injection Testing

**Purpose:** Automated SQL injection detection and exploitation

**Common Use Cases:**
- Detect SQL injection vulnerabilities
- Extract database contents
- Enumerate database structure
- File system access

**SoulEyez Commands:**
```bash
# Test URL for SQL injection
souleyez jobs enqueue sqlmap "http://example.com/page.php?id=1"

# Test with POST data
souleyez jobs enqueue sqlmap "http://example.com/login.php" --args="--data='user=admin&pass=test'"

# Extract databases
souleyez jobs enqueue sqlmap "http://example.com/page.php?id=1" --args="--dbs"

# Extract tables
souleyez jobs enqueue sqlmap "http://example.com/page.php?id=1" --args="-D database_name --tables"
```

**Common Arguments:**
- `--dbs` - Enumerate databases
- `-D <database>` - Target database
- `--tables` - Enumerate tables
- `-T <table>` - Target table
- `--columns` - Enumerate columns
- `--dump` - Dump table data
- `--batch` - Never ask for user input (non-interactive)
- `--level=<1-5>` - Test depth (default: 1)
- `--risk=<1-3>` - Risk level (default: 1)

**Output:** SQL injection findings with severity levels

**Auto-Chaining:** Progressive exploitation (detection → --dbs → --tables) with safety controls

**⚠️ Safety:** Auto-dump is DISABLED by default. Manual review required before data extraction.

---

### 8. WPScan - WordPress Security Scanner

**Purpose:** Identify WordPress vulnerabilities and misconfigurations

**Common Use Cases:**
- Detect vulnerable WordPress plugins
- Enumerate users
- Check theme vulnerabilities
- Find weak passwords

**SoulEyez Commands:**
```bash
# Basic WordPress scan
souleyez jobs enqueue wpscan http://example.com

# Enumerate users
souleyez jobs enqueue wpscan http://example.com --args="--enumerate u"

# Enumerate vulnerable plugins
souleyez jobs enqueue wpscan http://example.com --args="--enumerate vp"

# Aggressive scan (all plugins)
souleyez jobs enqueue wpscan http://example.com --args="--enumerate ap"
```

**Common Arguments:**
- `--enumerate u` - Enumerate users
- `--enumerate vp` - Enumerate vulnerable plugins
- `--enumerate ap` - Enumerate all plugins
- `--enumerate vt` - Enumerate vulnerable themes
- `--api-token <token>` - WPScan API token (for CVE data)

**Output:** WordPress vulnerabilities added as findings

---

## Network Tools

### 9. Enum4linux - SMB/Windows Enumeration

**Purpose:** Enumerate information from Windows and Samba systems

**Common Use Cases:**
- User enumeration
- Share enumeration
- Group membership discovery
- Password policy retrieval

**SoulEyez Commands:**
```bash
# Full enumeration
souleyez jobs enqueue enum4linux 10.0.0.82

# User enumeration only
souleyez jobs enqueue enum4linux 10.0.0.82 --args="-U"

# Share enumeration only
souleyez jobs enqueue enum4linux 10.0.0.82 --args="-S"
```

**Common Arguments:**
- `-U` - Users enumeration
- `-S` - Shares enumeration
- `-G` - Groups enumeration
- `-P` - Password policy enumeration
- `-a` - All basic enumeration

**Output:** SMB findings, shares, users added to database

---

### 10. SMBMap - SMB Share Enumeration

**Purpose:** Enumerate SMB shares and permissions

**Common Use Cases:**
- Find accessible shares
- Check share permissions
- List share contents
- Upload/download files

**SoulEyez Commands:**
```bash
# Anonymous enumeration
souleyez jobs enqueue smbmap 10.0.0.82

# Authenticated enumeration
souleyez jobs enqueue smbmap 10.0.0.82 --args="-u username -p password"

# List share contents
souleyez jobs enqueue smbmap 10.0.0.82 --args="-u username -p password -R"
```

**Common Arguments:**
- `-u <username>` - Username
- `-p <password>` - Password
- `-d <domain>` - Domain
- `-H <host>` - Target host
- `-R` - Recursively list directories

**Output:** SMB shares with permissions added to database

---

## Credential Tools

### 11. Hydra - Network Login Brute-Forcing

**Purpose:** Brute-force authentication for network protocols

**Common Use Cases:**
- SSH password cracking
- FTP login testing
- MySQL authentication brute-force
- HTTP form authentication

**SoulEyez Commands:**
```bash
# SSH brute-force (single user)
souleyez jobs enqueue hydra ssh://10.0.0.82 --args="-l admin -P /path/to/passwords.txt"

# SSH brute-force (multiple users)
souleyez jobs enqueue hydra ssh://10.0.0.82 --args="-L /path/to/users.txt -P /path/to/passwords.txt"

# MySQL brute-force
souleyez jobs enqueue hydra mysql://10.0.0.82 --args="-l root -P /path/to/passwords.txt"

# FTP brute-force
souleyez jobs enqueue hydra ftp://10.0.0.82 --args="-L users.txt -P passwords.txt"
```

**Supported Protocols:**
- `ssh` - SSH (port 22)
- `ftp` - FTP (port 21)
- `mysql` - MySQL (port 3306)
- `postgres` - PostgreSQL (port 5432)
- `smb` - SMB (port 445)
- `rdp` - RDP (port 3389)
- `http-post-form` - HTTP form authentication

**Common Arguments:**
- `-l <user>` - Single username
- `-L <file>` - Username list
- `-p <pass>` - Single password
- `-P <file>` - Password list
- `-t <threads>` - Number of parallel connections (default: 16)
- `-V` - Verbose mode
- `-f` - Exit on first valid password found

**Output:** Valid credentials added to credentials database

**⚠️ Performance:** SoulEyez uses optimized wordlists (25x faster than default lists)

---

### 12. Hashcat - Password Hash Cracking

**Purpose:** Crack password hashes using GPU acceleration

**Common Use Cases:**
- Crack captured password hashes
- Offline password recovery
- Hash type identification
- Dictionary and brute-force attacks

**SoulEyez Commands:**
```bash
# Crack MD5 hashes
souleyez jobs enqueue hashcat hashes.txt --args="-m 0 -a 0 /path/to/wordlist.txt"

# Crack NTLM hashes
souleyez jobs enqueue hashcat hashes.txt --args="-m 1000 -a 0 /path/to/wordlist.txt"

# Crack WPA handshakes
souleyez jobs enqueue hashcat capture.hccapx --args="-m 2500 -a 0 /path/to/wordlist.txt"

# Show cracked passwords
hashcat --show hashes.txt
```

**Common Hash Types (`-m` flag):**
- `0` - MD5
- `100` - SHA1
- `1000` - NTLM
- `1400` - SHA256
- `1800` - SHA512
- `2500` - WPA/WPA2
- `3200` - bcrypt
- `5600` - NetNTLMv2

**Common Attack Modes (`-a` flag):**
- `0` - Dictionary attack
- `1` - Combinator attack
- `3` - Brute-force attack
- `6` - Hybrid wordlist + mask
- `7` - Hybrid mask + wordlist

**Output:** Cracked passwords automatically update credentials database

**⚠️ Performance:** 100K - 10M hashes/second (GPU-dependent)

---

### 13. John the Ripper - Password Cracking

**Purpose:** Versatile password cracker for various hash formats

**Common Use Cases:**
- Crack Unix/Linux password hashes
- Crack Windows SAM hashes
- ZIP/RAR password recovery
- SSH key password recovery

**SoulEyez Commands:**
```bash
# Crack password file
souleyez jobs enqueue john hashes.txt

# Crack with custom wordlist
souleyez jobs enqueue john hashes.txt --args="--wordlist=/path/to/wordlist.txt"

# Crack with rules
souleyez jobs enqueue john hashes.txt --args="--wordlist=/path/to/wordlist.txt --rules"

# Show cracked passwords
john --show hashes.txt
```

**Common Arguments:**
- `--wordlist=<file>` - Wordlist path
- `--rules` - Apply John's mangling rules
- `--format=<type>` - Hash format (md5, sha256, nt, etc.)
- `--incremental` - Brute-force mode

**Output:** Cracked passwords added to credentials database

---

## Exploitation Tools

### 14. Metasploit Auxiliary Modules

**Purpose:** Run Metasploit auxiliary scanners and modules

**Common Use Cases:**
- Service-specific vulnerability scanning
- Protocol fuzzing
- Banner grabbing
- Exploit verification

**SoulEyez Commands:**
```bash
# Run SSH version scanner
souleyez jobs enqueue msf_auxiliary auxiliary/scanner/ssh/ssh_version --args="RHOSTS=10.0.0.82"

# Run SMB version scanner
souleyez jobs enqueue msf_auxiliary auxiliary/scanner/smb/smb_version --args="RHOSTS=10.0.0.82"

# Run FTP anonymous login check
souleyez jobs enqueue msf_auxiliary auxiliary/scanner/ftp/anonymous --args="RHOSTS=10.0.0.82"
```

**Common Modules:**
- `auxiliary/scanner/ssh/ssh_version` - SSH version detection
- `auxiliary/scanner/smb/smb_version` - SMB version detection
- `auxiliary/scanner/http/http_version` - HTTP version detection
- `auxiliary/scanner/ftp/anonymous` - FTP anonymous login check

**Output:** Auxiliary scan results added as findings

---

## Quick Command Reference

### Enqueue Jobs

```bash
# Basic syntax
souleyez jobs enqueue <tool> <target> [--args="<tool-specific-args>"]

# With label (for organization)
souleyez jobs enqueue <tool> <target> --label "DESCRIPTION"

# Examples
souleyez jobs enqueue nmap 10.0.0.82 --label "INITIAL_SCAN"
souleyez jobs enqueue gobuster http://10.0.0.82 --label "WEB_ENUM"
souleyez jobs enqueue hydra ssh://10.0.0.82 --label "SSH_BRUTE"
```

---

### Job Management

```bash
# List all jobs
souleyez jobs list

# View specific job
souleyez jobs get <job_id>

# Follow job output (live)
souleyez jobs tail <job_id>

# Kill running job
souleyez jobs kill <job_id>

# Purge completed jobs
souleyez jobs purge

# Reparse job output (if parser was updated)
souleyez jobs reparse <job_id>
```

---

### Tool Availability

```bash
# Check which tools are installed
souleyez plugins list

# Test tool manually
<tool_name> --version

# Install missing tools (Kali Linux)
sudo apt-get install <tool_name>
```

---

## Tool Categories Summary

| Category | Tools | Primary Use |
|----------|-------|-------------|
| **Reconnaissance** | Nmap, theHarvester, DNSRecon, WHOIS | Network/OSINT discovery |
| **Web Scanning** | Nikto, Gobuster, SQLMap, WPScan | Web application testing |
| **Network Enum** | Enum4linux, SMBMap | Windows/SMB enumeration |
| **Credentials** | Hydra, Hashcat, John | Password attacks |
| **Exploitation** | Metasploit Auxiliary | Exploit verification |

---

## Wordlist Locations

**SoulEyez Optimized Wordlists:**
```
data/wordlists/
├── passwords/
│   ├── passwords-common.txt    (1,500 passwords)
│   ├── passwords-medium.txt    (10,000 passwords)
│   └── passwords-large.txt     (100,000 passwords)
├── usernames/
│   ├── usernames-common.txt    (100 usernames)
│   └── usernames-medium.txt    (1,000 usernames)
└── web/
    ├── web-common.txt          (65 paths)
    └── web-medium.txt          (220 paths)
```

**Note:** SoulEyez is self-contained with bundled wordlists in `data/wordlists/`. No external wordlists required.

---

## Best Practices

### ✅ Do's

1. **Start with reconnaissance:**
   - Nmap → theHarvester → DNSRecon
   - Build target knowledge first

2. **Use appropriate wordlists:**
   - Start small (common lists)
   - Expand if needed (medium/large)
   - Custom lists for targeted attacks

3. **Label your jobs:**
   - Makes tracking easier
   - Helps with reporting later

4. **Monitor long-running scans:**
   - Use `souleyez dashboard`
   - Or `souleyez jobs tail <id>`

5. **Let auto-chaining work:**
   - Tools trigger follow-ups automatically
   - Review recommendations before approving

---

### ❌ Don'ts

1. **Don't run aggressive scans on production systems**
   - Get proper authorization
   - Use --timing options carefully

2. **Don't use full wordlists on every scan**
   - Wastes time
   - May trigger IDS/IPS
   - Start small, expand if needed

3. **Don't ignore tool output**
   - Review findings
   - Verify discoveries manually
   - False positives exist

4. **Don't brute-force without authorization**
   - Account lockouts
   - Legal implications
   - IDS/IPS detection

5. **Don't run multiple instances of same scan**
   - Check existing jobs first
   - Wastes resources
   - May conflict

---

## Getting Help

**Tool-Specific Help:**
```bash
# From command line
nmap --help
gobuster --help
hydra --help

# From SoulEyez
souleyez plugins list          # See available tools
souleyez jobs get <id>         # View exact command used
```

**Documentation:**
- Worker Management: `docs/user-guide/worker-management.md`
- Workflows Guide: `docs/user-guide/workflows.md`
- Troubleshooting: `docs/user-guide/troubleshooting.md`

**Official Tool Documentation:**
- Nmap: https://nmap.org/book/man.html
- Metasploit: https://docs.metasploit.com/
- Hydra: https://github.com/vanhauser-thc/thc-hydra
- Hashcat: https://hashcat.net/wiki/

---

**Last Updated:** 2025-11-18
**Version:** 1.0
