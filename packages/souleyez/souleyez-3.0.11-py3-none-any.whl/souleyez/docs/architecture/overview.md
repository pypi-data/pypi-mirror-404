# souleyez Architecture

> Comprehensive technical architecture documentation for the souleyez penetration testing automation framework

**Version:** 2.0.29
**Last Updated:** December 2025
**Authors:** y0d8 & S0ul H@ck3r$

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Core Components](#core-components)
4. [Data Models & Relationships](#data-models--relationships)
5. [Credential Encryption Architecture](#credential-encryption-architecture)
6. [Parser Architecture](#parser-architecture)
7. [Job Execution Engine](#job-execution-engine)
8. [Tool Chaining System](#tool-chaining-system)
9. [Technology Stack](#technology-stack)
10. [Directory Structure](#directory-structure)
11. [Security Considerations](#security-considerations)

---

## System Overview

### Purpose

souleyez is a penetration testing automation framework designed to:
- Automate reconnaissance and vulnerability discovery workflows
- Manage multiple security engagements with isolated data
- Track discovered credentials, services, and vulnerabilities
- Enable intelligent tool chaining based on discoveries
- Provide real-time monitoring through an interactive dashboard

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                          │
├────────────────┬────────────────────────┬───────────────────────┤
│  CLI Commands  │  Interactive Dashboard │  Interactive Menu     │
│  (Click)       │  (Curses + Live UI)    │  (Curses)             │
└────────┬───────┴───────────┬────────────┴────────────┬──────────┘
         │                   │                         │
         └───────────────────┴─────────────────────────┘
                             │
         ┌───────────────────▼─────────────────────┐
         │         CORE BUSINESS LOGIC             │
         ├─────────────────────────────────────────┤
         │  • Engagement Manager                   │
         │  • Findings Manager                     │
         │  • Credentials Manager (+ Encryption)   │
         │  • Hosts & Services Manager             │
         │  • Tool Chaining Engine                 │
         │  • CVE Matcher                          │
         │  • Credential Tester                    │
         └───────────┬─────────────────────────────┘
                     │
         ┌───────────▼─────────────────────────────┐
         │      JOB EXECUTION ENGINE               │
         ├─────────────────────────────────────────┤
         │  • Background Worker Manager            │
         │  • Job Queue (File-backed)              │
         │  • Plugin System                        │
         │  • Result Handler                       │
         └───────────┬─────────────────────────────┘
                     │
         ┌───────────▼─────────────────────────────┐
         │        PLUGIN LAYER                     │
         ├─────────────────────────────────────────┤
         │  Network Tools:  nmap, masscan          │
         │  Web Tools:      nikto, gobuster, wpscan│
         │  Exploitation:   msf_auxiliary, sqlmap  │
         │  OSINT:          theharvester, whois    │
         │  Credentials:    hydra, enum4linux      │
         │  SMB:            smbmap                  │
         └───────────┬─────────────────────────────┘
                     │
         ┌───────────▼─────────────────────────────┐
         │        PARSER LAYER                     │
         ├─────────────────────────────────────────┤
         │  • Nmap Parser (text output)            │
         │  • Metasploit Parser (auxiliary output) │
         │  • Nikto Parser (JSON)                  │
         │  • Gobuster Parser (directory bruteforce)│
         │  • SMBMap Parser (shares/files)         │
         │  • And 8+ more specialized parsers      │
         └───────────┬─────────────────────────────┘
                     │
         ┌───────────▼─────────────────────────────┐
         │      STORAGE LAYER                      │
         ├─────────────────────────────────────────┤
         │  • SQLite Database (souleyez.db)      │
         │  • Encryption Manager (crypto.json)     │
         │  • File Storage (logs, reports)         │
         │  • Migration System                     │
         └─────────────────────────────────────────┘
```

### Design Philosophy

1. **Plugin-First Architecture**: All security tools are wrapped in plugins with standardized interfaces
2. **Engagement-Centric**: All data is scoped to engagements (workspaces) for isolation
3. **Parse-Store-Correlate**: Tool output → Parser → Database → Correlation → Findings
4. **Security-by-Default**: Mandatory credential encryption with industry-standard cryptography
5. **File-Backed Job Queue**: Persistent, crash-resilient job tracking without external dependencies
6. **Real-Time Monitoring**: Live dashboard with automatic refresh and status updates

---

## Architecture Principles

### 1. Separation of Concerns

- **UI Layer**: Handles user interaction (CLI, dashboard, interactive menu)
- **Business Logic**: Manages engagements, findings, credentials, correlation
- **Execution Layer**: Runs tools, manages jobs, handles concurrency
- **Plugin Layer**: Wraps external tools with uniform interface
- **Parser Layer**: Extracts structured data from tool output
- **Storage Layer**: Persists data to SQLite with encryption support

### 2. Fail-Safe Design

- **Graceful Degradation**: If parsers fail, raw logs are preserved
- **Corruption Recovery**: Job queue automatically recovers from corrupted state
- **Retry Logic**: Database operations use exponential backoff
- **Backward Compatibility**: Encrypted data falls back to plaintext during migration

### 3. Extensibility

- **Plugin Base Class**: New tools inherit from `PluginBase`
- **Parser Pattern**: Each tool has a dedicated parser in `souleyez/parsers/`
- **Migration System**: Schema changes are versioned and tracked
- **Modular Managers**: Each data type has a dedicated manager class

### 4. Security-First

- **Master Password**: Never stored, derived on-demand using PBKDF2
- **Encryption Key**: Exists only in memory during unlock
- **File Permissions**: Crypto config restricted to owner (0o600)
- **Audit Trail**: All findings and credentials track creation time and source tool

---

## Core Components

### 1. Engagement Manager (`souleyez/storage/engagements.py`)

**Purpose**: Manages penetration testing engagements (workspaces).

**Key Responsibilities**:
- Create, list, delete engagements
- Track current engagement via `~/.souleyez/current_engagement`
- Calculate engagement statistics (hosts, services, findings)
- Cascade delete all associated data

**Data Isolation**: All entities (hosts, services, findings, credentials) are scoped to an engagement.

### 2. Database Layer (`souleyez/storage/database.py`)

**Purpose**: Provides SQLite connection management with concurrency support.

**Features**:
- Singleton pattern for connection pooling
- WAL (Write-Ahead Logging) mode for concurrent reads/writes
- 30-second busy timeout with exponential backoff retry
- Row factory for dict-like access
- Schema loading from `schema.sql`

**Location**: `~/.souleyez/souleyez.db`

### 3. Credential System

#### Credentials Manager (`souleyez/storage/credentials.py`)

Stores and retrieves discovered credentials with mandatory encryption.

**Schema**:
```sql
CREATE TABLE credentials (
    id INTEGER PRIMARY KEY,
    engagement_id INTEGER NOT NULL,
    host_id INTEGER,
    service TEXT,
    port INTEGER,
    protocol TEXT DEFAULT 'tcp',
    username TEXT,           -- Encrypted
    password TEXT,           -- Encrypted
    credential_type TEXT DEFAULT 'user',
    status TEXT DEFAULT 'untested',
    tool TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Status Values**: `untested`, `valid`, `invalid`, `discovered`

#### Credential Tester (`souleyez/core/credential_tester.py`)

Tests discovered credentials against target hosts.

**Supported Services**:
- SSH (port 22) - Uses `sshpass`
- SMB (ports 139, 445) - Uses `smbclient`
- FTP (port 21)
- RDP (port 3389)
- MySQL (port 3306)
- PostgreSQL (port 5432)

**Workflow**:
1. Fetch credentials for engagement
2. Test against all hosts with matching services
3. Update credential status (valid/invalid)
4. Create HIGH/MEDIUM severity findings for valid credentials

### 4. Findings System (`souleyez/storage/findings.py`)

Tracks security vulnerabilities and notable discoveries.

**Schema**:
```sql
CREATE TABLE findings (
    id INTEGER PRIMARY KEY,
    engagement_id INTEGER NOT NULL,
    host_id INTEGER,
    service_id INTEGER,
    finding_type TEXT NOT NULL,
    severity TEXT DEFAULT 'info',
    title TEXT NOT NULL,
    description TEXT,
    evidence TEXT,
    refs TEXT,
    port INTEGER,
    path TEXT,
    tool TEXT,
    scan_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Severity Levels**: `critical`, `high`, `medium`, `low`, `info`

**Finding Types**:
- `vuln` - Vulnerability
- `credential` - Valid credential discovered
- `config` - Misconfiguration
- `exposure` - Information disclosure
- `service` - Service detection

### 5. Job Execution Engine (`souleyez/engine/background.py`)

**Purpose**: Manages asynchronous tool execution with persistent queue.

**Architecture**:
```
┌──────────────────┐
│  User Enqueues   │
│  Tool Command    │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Job Queue (data/jobs/jobs.json)    │
│  ┌─────────────────────────────┐    │
│  │ Job 1: nmap 10.0.0.0/24     │    │
│  │ Job 2: gobuster http://...  │    │
│  │ Job 3: nikto -h target      │    │
│  └─────────────────────────────┘    │
└────────┬────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  Background Worker Process           │
│  ┌────────────────────────────────┐  │
│  │ 1. Dequeue next pending job    │  │
│  │ 2. Load plugin for tool        │  │
│  │ 3. Execute: plugin.run()       │  │
│  │ 4. Log to data/jobs/<id>.log   │  │
│  │ 5. Update job status           │  │
│  │ 6. Invoke result handler       │  │
│  └────────────────────────────────┘  │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  Result Handler                      │
│  ┌────────────────────────────────┐  │
│  │ 1. Detect tool type            │  │
│  │ 2. Load parser                 │  │
│  │ 3. Parse output                │  │
│  │ 4. Insert hosts/services       │  │
│  │ 5. Insert findings             │  │
│  │ 6. Trigger tool chaining       │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

**Job States**:
- `pending` - Queued, not started
- `running` - Currently executing
- `completed` - Finished successfully
- `failed` - Execution failed

**Key Features**:
- Plugin-first execution: Calls `plugin.run(target, args, label, log_path)`
- Fallback to subprocess for tools without plugins
- Per-job logging to `data/jobs/<job_id>.log`
- Automatic result parsing on completion
- 1-hour timeout per job
- Crash recovery (job queue persists to disk)

### 6. Plugin System (`souleyez/plugins/`)

**Base Class**: `souleyez/plugins/plugin_base.py`

Each plugin implements:
```python
class PluginBase:
    def run(self, target: str, args: List[str], label: str, log_path: str) -> int:
        """Execute tool and return exit code"""
        pass

    def validate(self, target: str) -> bool:
        """Validate target is appropriate for this tool"""
        pass
```

**Available Plugins**:
- **Network**: nmap, masscan
- **Web**: nikto, gobuster, wpscan, sqlmap
- **OSINT**: theharvester, whois, dnsrecon
- **Credentials**: hydra, enum4linux
- **Exploitation**: msf_auxiliary (Metasploit wrappers)
- **SMB**: smbmap

**Plugin Benefits**:
- Standardized command construction
- Target validation
- Consistent logging format
- Integration with job system

---

## Data Models & Relationships

### Entity Relationship Diagram

```
┌────────────────┐
│  Engagements   │
│  ────────────  │
│  id (PK)       │
│  name (UNIQUE) │
│  description   │
│  created_at    │
└────┬───────────┘
     │
     │ 1:N
     │
     ▼
┌─────────────────┐         ┌──────────────────┐
│     Hosts       │         │    Findings      │
│  ─────────────  │         │  ──────────────  │
│  id (PK)        │◄────────│  host_id (FK)    │
│  engagement_id  │    1:N  │  engagement_id   │
│  ip_address     │         │  finding_type    │
│  hostname       │         │  severity        │
│  os_name        │         │  title           │
│  status         │         │  description     │
└────┬────────────┘         └──────────────────┘
     │
     │ 1:N
     │
     ▼
┌─────────────────┐
│    Services     │
│  ─────────────  │
│  id (PK)        │
│  host_id (FK)   │
│  port           │
│  protocol       │
│  service_name   │
│  state          │
└─────────────────┘

┌─────────────────┐
│  Credentials    │
│  ─────────────  │
│  id (PK)        │
│  engagement_id  │
│  host_id (FK)   │
│  service        │
│  username       │◄── Encrypted
│  password       │◄── Encrypted
│  status         │
└─────────────────┘

┌─────────────────┐
│  Web Paths      │
│  ─────────────  │
│  id (PK)        │
│  host_id (FK)   │
│  url            │
│  status_code    │
│  redirect       │
└─────────────────┘

┌─────────────────┐
│  SMB Shares     │
│  ─────────────  │
│  id (PK)        │
│  host_id (FK)   │
│  share_name     │
│  permissions    │
│  readable       │
└────┬────────────┘
     │
     │ 1:N
     ▼
┌─────────────────┐
│   SMB Files     │
│  ─────────────  │
│  id (PK)        │
│  share_id (FK)  │
│  path           │
│  size           │
└─────────────────┘
```

### Key Relationships

1. **Engagement → Hosts** (1:N)
   - Each engagement contains multiple hosts
   - Unique constraint: `(engagement_id, ip_address)`

2. **Host → Services** (1:N)
   - Each host has multiple services
   - Unique constraint: `(host_id, port, protocol)`

3. **Engagement → Findings** (1:N)
   - Findings are scoped to engagements
   - Optional foreign key to specific host

4. **Host → SMB Shares → SMB Files** (1:N:N)
   - SMB enumeration creates hierarchical structure

5. **Engagement → Credentials** (1:N)
   - Credentials can optionally reference specific host

### Data Flow Example: Nmap Scan

```
1. User runs: souleyez run nmap 10.0.0.1-10

2. Job enqueued:
   - tool: "nmap"
   - target: "10.0.0.1-10"
   - engagement_id: 42

3. Worker executes nmap plugin:
   - Constructs command: nmap -sV -sC 10.0.0.1-10
   - Logs to: data/jobs/123.log
   - Returns exit code

4. Result handler invoked:
   - Reads log file
   - Calls nmap_parser.parse_nmap_text(output)

5. Parser returns:
   {
     "hosts": [
       {
         "ip": "10.0.0.5",
         "status": "up",
         "os": "Linux 5.x",
         "services": [
           {"port": 22, "service": "ssh", "version": "OpenSSH 8.2"}
         ]
       }
     ]
   }

6. Result handler inserts:
   - Host record: engagement_id=42, ip=10.0.0.5, status=up
   - Service record: host_id=<new_host>, port=22, service_name=ssh
   - Finding (info): "SSH Service Detected on 10.0.0.5:22"

7. Tool chaining triggered:
   - Detects SSH service on port 22
   - Auto-enqueues: msf_auxiliary ssh_version 10.0.0.5
```

---

## Credential Encryption Architecture

### Overview

souleyez implements **mandatory at-rest encryption** for discovered credentials using **Fernet** (symmetric encryption based on AES-128-CBC + HMAC-SHA256). Encryption is configured during the first-run setup wizard.

**Note**: The README mentions AES-256, but the actual implementation uses **Fernet** which is AES-128 in CBC mode with HMAC authentication.

### Cryptographic Components

**File**: `souleyez/storage/crypto.py`

#### 1. Master Password Derivation

```
User Master Password
        │
        ▼
┌────────────────────────────────────┐
│  PBKDF2-HMAC-SHA256                │
│  • Salt: 32 bytes (256-bit)        │
│  • Iterations: 480,000             │
│  • Output: 32 bytes                │
└────────┬───────────────────────────┘
         │
         ▼
    Encryption Key
    (Base64-encoded)
         │
         ▼
┌────────────────────────────────────┐
│  Fernet Instance                   │
│  • AES-128-CBC encryption          │
│  • HMAC-SHA256 authentication      │
└────────────────────────────────────┘
```

#### 2. Key Management

**Storage**: `~/.souleyez/crypto.json`
```json
{
  "salt": "base64-encoded-32-byte-salt",
  "encryption_enabled": true
}
```

**Security Properties**:
- Master password is **never stored** (cannot be recovered if lost)
- Encryption key derived on-demand during unlock
- Key exists only in memory (`CryptoManager._fernet`)
- Config file permissions: `0o600` (owner-only)
- Salt is randomly generated on first initialization

#### 3. Encryption Flow

```python
# Enable encryption
crypto = CryptoManager()
crypto.enable_encryption(master_password)

# Unlock (session-based)
crypto.unlock(master_password)  # Derives key, stores in memory

# Encrypt credential field
encrypted_username = crypto.encrypt("admin")
# Returns: "gAAAAABh3k2..." (Fernet token)

# Decrypt credential field
plaintext = crypto.decrypt("gAAAAABh3k2...")
# Returns: "admin"

# Lock (clear key from memory)
crypto.lock()
```

#### 4. Integration with Credentials Manager

**File**: `souleyez/storage/credentials.py`

```python
class CredentialsManager:
    def add_credential(self, username, password, ...):
        # Automatically encrypt if encryption enabled
        encrypted_username = self._encrypt_field(username)
        encrypted_password = self._encrypt_field(password)

        # Store encrypted values in database
        self.db.insert("credentials", {
            "username": encrypted_username,
            "password": encrypted_password,
            ...
        })

    def _encrypt_field(self, value):
        if self.crypto.is_encryption_enabled():
            if not self.crypto.is_unlocked():
                raise RuntimeError("Locked! Call unlock() first.")
            return self.crypto.encrypt(value)
        return value  # Plaintext if encryption disabled
```

### Unlock Workflow (CLI)

**File**: `souleyez/main.py:1167`

```
User runs: souleyez creds list
         │
         ▼
┌────────────────────────────────────┐
│  Check if encryption enabled?      │
└────┬───────────────────────────────┘
     │ Yes
     ▼
┌────────────────────────────────────┐
│  Check if already unlocked?        │
└────┬───────────────────────────────┘
     │ No
     ▼
┌────────────────────────────────────┐
│  Prompt: Enter master password     │
│  Max 3 attempts                    │
└────┬───────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│  crypto.unlock(password)           │
│  • Derive key from password        │
│  • Test with encrypt/decrypt       │
│  • Store Fernet instance in memory │
└────┬───────────────────────────────┘
     │ Success
     ▼
┌────────────────────────────────────┐
│  Fetch credentials from DB         │
│  • Decrypt username field          │
│  • Decrypt password field          │
│  • Display plaintext to user       │
└────────────────────────────────────┘
```

### Dashboard Masking (No Decryption)

**File**: `souleyez/ui/dashboard.py`

```python
def mask_credential(value):
    """Mask credential without decrypting."""
    if value is None or value == "":
        return "?"

    # Fernet tokens start with 'gAAAAA'
    if isinstance(value, str) and len(value) > 20:
        return "••••••••"

    return "••••••••"
```

**Design**: Dashboard never decrypts credentials to prevent accidental exposure.

### Migration Script

**File**: `migrate_credentials.py`

Purpose: Encrypt existing plaintext credentials.

```bash
python3 migrate_credentials.py
# Prompts for new master password
# Encrypts all credentials in database
```

### Security Considerations

**Strengths**:
- Industry-standard Fernet encryption (AES-128-CBC + HMAC)
- OWASP-recommended PBKDF2 iterations (480k)
- Password never stored on disk
- Session-based unlock (key cleared on exit)
- File permissions enforce owner-only access

**Limitations**:
- No password recovery mechanism (lost password = lost data)
- Single-user system (no multi-user key sharing)
- Metadata not encrypted (host IPs, service names visible)
- No audit logging of access
- No hardware key support (planned)

**Threat Model**:
- **Protects Against**: Disk theft, unauthorized file access, database backups
- **Does Not Protect Against**: Memory dumps, live system compromise, keyloggers

---

## Parser Architecture

### Design Pattern

Each security tool has a dedicated parser that transforms raw output into structured data.

**Location**: `souleyez/parsers/`

### Parser Interface

```python
def parse_<tool>_text(output: str) -> Dict[str, Any]:
    """
    Parse tool output into structured data.

    Returns:
        {
            'hosts': [...],
            'services': [...],
            'findings': [...],
            'credentials': [...],
            'error': "..." (optional)
        }
    """
```

### Available Parsers

| Parser | Input Format | Output Entities |
|--------|--------------|-----------------|
| `nmap_parser.py` | Text output | hosts, services, OS detection |
| `msf_parser.py` | Auxiliary output | services, findings, credentials |
| `nikto_parser.py` | JSON | web findings, vulnerabilities |
| `gobuster_parser.py` | Text | web paths, status codes |
| `smbmap_parser.py` | Text | SMB shares, files |
| `enum4linux_parser.py` | Text | users, groups, shares |
| `hydra_parser.py` | Text | valid credentials |
| `sqlmap_parser.py` | Text | SQL injection findings |
| `wpscan_parser.py` | JSON | WordPress vulns, themes, plugins |
| `theharvester_parser.py` | JSON | emails, subdomains, OSINT |
| `whois_parser.py` | Text | domain registration, nameservers |
| `dnsrecon_parser.py` | JSON | DNS records, zone transfers |

### Example: Nmap Parser

**File**: `souleyez/parsers/nmap_parser.py`

**Input** (Text):
```
Nmap scan report for 10.0.0.5
Host is up (0.0015s latency).
PORT    STATE SERVICE VERSION
22/tcp  open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.1
80/tcp  open  http    Apache httpd 2.4.41
OS details: Linux 5.4
```

**Parsing Logic**:
1. Split output into lines
2. Detect "Nmap scan report for" → Extract IP/hostname
3. Detect "Host is up/down" → Extract status
4. Regex match service lines: `^\d+/(tcp|udp)`
5. Extract port, protocol, state, service name, version
6. Detect OS lines: "Running:" or "OS details:"

**Output** (Structured):
```python
{
  "hosts": [
    {
      "ip": "10.0.0.5",
      "hostname": None,
      "status": "up",
      "os": "Linux 5.4",
      "services": [
        {
          "port": 22,
          "protocol": "tcp",
          "state": "open",
          "service": "ssh",
          "version": "OpenSSH 8.2p1 Ubuntu 4ubuntu0.1"
        },
        {
          "port": 80,
          "protocol": "tcp",
          "state": "open",
          "service": "http",
          "version": "Apache httpd 2.4.41"
        }
      ]
    }
  ]
}
```

### Example: Metasploit Parser

**File**: `souleyez/parsers/msf_parser.py`

Metasploit auxiliary modules have specialized parsers:

#### SSH Version Detection
```
Module: auxiliary/scanner/ssh/ssh_version
Target: 10.0.0.5

[*] 10.0.0.5:22 - SSH server version: SSH-2.0-OpenSSH_4.7p1 Debian-8ubuntu1
[*] 10.0.0.5:22 - os.version: Ubuntu
[!] 10.0.0.5:22 - Deprecated encryption.encryption 3des-cbc
```

**Parser Output**:
```python
{
  "services": [
    {"port": 22, "service_name": "ssh", "service_version": "OpenSSH_4.7p1"}
  ],
  "findings": [
    {
      "title": "SSH Deprecated Encryption Algorithms",
      "severity": "medium",
      "description": "SSH server supports deprecated encryption: 3des-cbc",
      "port": 22,
      "service": "ssh"
    }
  ]
}
```

#### Login Success
```
Module: auxiliary/scanner/ssh/ssh_login
Target: 10.0.0.82

[+] 10.0.0.82:22 - Success: 'admin:password123'
```

**Parser Output**:
```python
{
  "findings": [
    {
      "title": "SSH Valid Credentials Found",
      "severity": "critical",
      "description": "Valid ssh credentials: admin:password123",
      "port": 22
    }
  ],
  "credentials": [
    {
      "username": "admin",
      "password": "password123",
      "service": "ssh",
      "port": 22,
      "status": "valid"
    }
  ]
}
```

### Parser Routing

**File**: `souleyez/engine/result_handler.py`

```python
def handle_result(job_id, tool, log_path):
    # Route to appropriate parser
    if tool == "nmap":
        from souleyez.parsers.nmap_parser import parse_nmap_log
        data = parse_nmap_log(log_path)

    elif tool == "msf_auxiliary":
        from souleyez.parsers.msf_parser import parse_msf_log
        data = parse_msf_log(log_path)

    # ... other tools

    # Insert parsed data into database
    insert_hosts(data.get('hosts', []))
    insert_services(data.get('services', []))
    insert_findings(data.get('findings', []))
    insert_credentials(data.get('credentials', []))
```

### Error Handling

Parsers follow fail-safe design:
- Return `{"error": "..."}` on parse failure
- Preserve raw logs even if parsing fails
- Gracefully handle partial data
- Strip ANSI escape codes before parsing

---

## Job Execution Engine

### Architecture

**File**: `souleyez/engine/background.py`

### Job Queue (File-Backed)

**Location**: `data/jobs/jobs.json`

**Format**:
```json
[
  {
    "id": 123,
    "tool": "nmap",
    "target": "10.0.0.0/24",
    "args": ["-sV", "-sC"],
    "label": "Initial scan",
    "status": "running",
    "engagement_id": 42,
    "created_at": "2025-10-29T10:15:00Z",
    "started_at": "2025-10-29T10:15:05Z",
    "log_path": "data/jobs/123.log"
  }
]
```

**Design Benefits**:
- No external dependencies (Redis, RabbitMQ, etc.)
- Survives crashes (persists to disk)
- Simple atomic file replacement
- Automatic corruption recovery

### Worker Process

**Execution Flow**:

```
1. Start worker: python -m souleyez.engine.background --fg
2. Loop forever:
   a. Read jobs.json
   b. Find next pending job
   c. Mark job as running
   d. Load plugin for tool
   e. Execute: plugin.run(target, args, label, log_path)
   f. Capture exit code
   g. Update job status (completed/failed)
   h. Invoke result handler
   i. Sleep 1 second
```

**Plugin Execution**:
```python
# Load plugin
from souleyez.plugins.nmap import NmapPlugin
plugin = NmapPlugin()

# Execute
exit_code = plugin.run(
    target="10.0.0.1-10",
    args=["-sV", "-sC"],
    label="Network scan",
    log_path="data/jobs/123.log"
)
```

**Fallback Execution** (if plugin not available):
```python
# Direct subprocess execution
cmd = ["nmap", "-sV", "-sC", "10.0.0.1-10"]
proc = subprocess.run(
    cmd,
    stdout=log_file,
    stderr=subprocess.STDOUT,
    timeout=3600
)
exit_code = proc.returncode
```

### Concurrency Model

**Current**: Single-threaded worker (one job at a time)
- Simple, predictable
- No race conditions
- Easy to debug

**Future**: Multi-threaded worker pool
- Parallel tool execution
- Configurable worker count
- Job priority system

### Timeout Handling

**Default**: 1 hour per job (`JOB_TIMEOUT_SECONDS = 3600`)

**Behavior**:
- If job exceeds timeout, process is killed
- Job marked as `failed`
- Log contains timeout message

### Logging

**Worker Log**: `data/logs/worker.log`
- Worker start/stop events
- Job start/complete events
- Errors and warnings

**Per-Job Logs**: `data/jobs/<job_id>.log`
- Tool stdout/stderr
- Timestamps
- Exit codes

---

## Tool Chaining System

### Overview

**Purpose**: Automatically trigger follow-up scans based on discoveries.

**File**: `souleyez/core/tool_chaining.py`

### Chaining Rules

| Discovery | Auto-Triggered Tool |
|-----------|---------------------|
| Open port 80/443/8080 | `nikto` web vulnerability scanner |
| Open port 80/443/8080 | `gobuster` directory brute-force |
| Open port 445 (SMB) | `msf_auxiliary smb_enumshares` |
| Open port 445 (SMB) | `enum4linux` SMB enumeration |
| WordPress detected | `wpscan` WordPress scanner |
| Open port 21 (FTP) | `msf_auxiliary ftp_version` |
| Open port 22 (SSH) | `msf_auxiliary ssh_version` |
| Open port 25 (SMTP) | `msf_auxiliary smtp_version` |
| Open port 3306 (MySQL) | `msf_auxiliary mysql_version` |
| Open port 5432 (PostgreSQL) | `msf_auxiliary postgres_version` |

### Workflow

```
1. Nmap discovers port 80 on 10.0.0.5
2. Result handler inserts service record
3. Tool chaining checks service port
4. Port 80 detected → HTTP service
5. Auto-enqueue jobs:
   - nikto -h http://10.0.0.5
   - gobuster dir -u http://10.0.0.5 -w wordlist.txt
```

### Configuration

**Toggle**: Dashboard `[a]` key or config file

**Status**: Displayed in dashboard header

### Deduplication

Prevents duplicate jobs:
- Check if job already exists for (tool, target, engagement)
- Skip enqueuing if already pending/running

---

## Technology Stack

### Core Technologies

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.8+ |
| Database | SQLite | 3 |
| Encryption | cryptography (Fernet) | Latest |
| CLI Framework | Click | 8.x |
| UI Framework | curses (built-in) | - |
| Concurrency | threading | Built-in |

### Key Libraries

```
click>=8.0.0           # CLI framework
cryptography>=41.0.0   # Fernet encryption
requests>=2.28.0       # HTTP requests
python-whois>=0.8.0    # WHOIS lookups
```

### External Tool Dependencies

**Network**:
- nmap
- masscan

**Web**:
- nikto
- gobuster
- wpscan
- sqlmap

**Exploitation**:
- msfconsole (Metasploit Framework)

**Credentials**:
- hydra
- enum4linux
- sshpass
- smbclient

**OSINT**:
- theHarvester
- whois
- dnsrecon

---

## Directory Structure

```
souleyez_app/
├── souleyez/                 # Main package
│   ├── core/                   # Core business logic
│   │   ├── credential_tester.py
│   │   ├── cve_matcher.py
│   │   ├── msf_integration.py
│   │   ├── parser_handler.py
│   │   ├── tool_chaining.py
│   │   └── vuln_correlation.py
│   ├── engine/                 # Job execution
│   │   ├── background.py       # Job queue & worker
│   │   ├── base.py
│   │   ├── loader.py           # Plugin loader
│   │   ├── manager.py
│   │   ├── result_handler.py   # Parser routing
│   │   └── worker_manager.py
│   ├── importers/              # External data import
│   │   ├── msf_importer.py
│   │   └── smart_importer.py
│   ├── parsers/                # Tool output parsers
│   │   ├── nmap_parser.py
│   │   ├── msf_parser.py
│   │   ├── nikto_parser.py
│   │   ├── gobuster_parser.py
│   │   ├── smbmap_parser.py
│   │   ├── enum4linux_parser.py
│   │   ├── hydra_parser.py
│   │   ├── sqlmap_parser.py
│   │   ├── wpscan_parser.py
│   │   ├── theharvester_parser.py
│   │   ├── whois_parser.py
│   │   └── dnsrecon_parser.py
│   ├── plugins/                # Tool wrappers
│   │   ├── plugin_base.py
│   │   ├── nmap.py
│   │   ├── nikto.py
│   │   ├── gobuster.py
│   │   ├── wpscan.py
│   │   ├── sqlmap.py
│   │   ├── hydra.py
│   │   ├── enum4linux.py
│   │   ├── smbmap.py
│   │   ├── msf_auxiliary.py
│   │   ├── theharvester.py
│   │   ├── whois.py
│   │   └── dnsrecon.py
│   ├── reporting/              # Report generation
│   │   └── generator.py
│   ├── storage/                # Data layer
│   │   ├── database.py         # SQLite connection
│   │   ├── schema.sql          # Database schema
│   │   ├── engagements.py      # Engagement manager
│   │   ├── hosts.py            # Host manager
│   │   ├── findings.py         # Findings manager
│   │   ├── credentials.py      # Credentials manager
│   │   ├── osint.py            # OSINT data manager
│   │   ├── crypto.py           # Encryption manager
│   │   └── migrations/         # Schema migrations
│   │       ├── migration_manager.py
│   │       └── 001_add_credential_enhancements.py
│   ├── ui/                     # User interfaces
│   │   ├── dashboard.py        # Live dashboard (curses)
│   │   ├── interactive.py      # Interactive menu
│   │   └── terminal.py         # Terminal utilities
│   ├── main.py                 # CLI entry point
│   └── config.py               # Configuration
├── docs/                       # Documentation (this file!)
│   ├── architecture.md
│   └── adr/                    # Architecture Decision Records
│       ├── 001-ollama-vs-cloud-llm.md
│       ├── 002-master-password-approach.md
│       └── 003-database-schema-design.md
├── data/                       # Runtime data
│   ├── jobs/                   # Job queue & logs
│   │   ├── jobs.json
│   │   └── <job_id>.log
│   └── logs/                   # Application logs
│       └── worker.log
├── tests/                      # Unit tests
├── migrate_credentials.py      # Encryption migration script
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Package configuration
├── setup.py                   # Installation script
├── README.md
├── SECURITY.md                # Security documentation
├── AUTO_CHAINING_GUIDE.md     # Tool chaining guide
├── MIGRATIONS.md              # Migration system docs
└── LICENSE
```

### User Data Directory

**Location**: `~/.souleyez/`

```
~/.souleyez/
├── souleyez.db              # SQLite database
├── crypto.json                # Encryption config (salt, enabled flag)
└── current_engagement         # Current workspace ID
```

---

## Security Considerations

### Threat Model

**Assumptions**:
- Operator has physical access to their own machine
- Operator is authorized to perform penetration testing
- souleyez runs on operator's workstation (not shared server)

**Threats Addressed**:
- ✓ Unauthorized access to credentials database (encryption at rest)
- ✓ Accidental credential exposure in screenshots (dashboard masking)
- ✓ Credential theft from backups (encrypted database)

**Threats NOT Addressed**:
- ✗ Memory dumps (keys exist in RAM during unlock)
- ✗ Keyloggers (master password entered via keyboard)
- ✗ Live system compromise (if attacker has shell, game over)
- ✗ Multi-user isolation (designed for single-user use)

### Best Practices

1. **Enable Encryption**: Run `python3 migrate_credentials.py` before storing credentials
2. **Strong Master Password**: Use 12+ characters, mixed case, symbols
3. **Password Manager**: Store master password in KeePassXC or similar
4. **File Permissions**: Ensure `~/.souleyez/` is owner-only (`chmod 700`)
5. **Secure Backups**: Encrypt backups of `~/.souleyez/souleyez.db`
6. **Separate Engagements**: Use different workspaces for different clients
7. **Clean Up**: Delete engagements when testing complete

### Known Limitations

1. **No Password Recovery**: Lost master password = lost encrypted credentials
2. **No Audit Logging**: No record of who accessed credentials when
3. **Single-User Design**: No multi-user access control
4. **No HSM Support**: Keys managed in software only (no hardware security modules)
5. **Metadata Unencrypted**: IP addresses, service names visible in plaintext

### Roadmap

**Planned Security Enhancements**:
- Hardware key support (YubiKey, TPM)
- Audit logging for credential access
- Multi-user access control with roles
- Automated credential rotation tracking
- Integration with corporate password vaults

---

## Appendix: Engagement Lifecycle

### Phase 1: Initialization

```bash
# Create engagement
souleyez workspace create acme-pentest

# Set as active
souleyez workspace use acme-pentest

# Note: Encryption is configured during the setup wizard (mandatory)
# Credentials are automatically encrypted with your vault master password
```

### Phase 2: Discovery

```bash
# Initial network scan
souleyez run nmap 10.0.0.0/24

# Wait for auto-chaining to trigger follow-ups
# Dashboard shows progress in real-time
souleyez dashboard
```

**Auto-triggered tools**:
- Nikto scans web servers
- Gobuster brute-forces directories
- SMBMap enumerates shares
- MSF modules fingerprint services

### Phase 3: Enumeration

```bash
# View discovered hosts
souleyez hosts list

# View open services
souleyez services list

# Run manual tools
souleyez run enum4linux 10.0.0.5
souleyez run hydra ssh://10.0.0.5
```

### Phase 4: Analysis

```bash
# View findings
souleyez findings list --severity high

# View credentials (prompts for master password)
souleyez creds list --status valid

# Test credentials
souleyez test-creds --engagement acme-pentest
```

### Phase 5: Reporting

```bash
# Generate HTML report
souleyez report generate acme-pentest

# Export to Metasploit
souleyez export msf acme-pentest
```

### Phase 6: Cleanup

```bash
# Archive engagement
souleyez workspace archive acme-pentest

# Or delete (WARNING: irreversible)
souleyez workspace delete acme-pentest
```

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-29 | Initial architecture documentation |

---

**Authors**: y0d8 & S0ul H@ck3r$
**License**: See [LICENSE](../LICENSE)
**Contact**: See [README.md](../README.md) for support channels
