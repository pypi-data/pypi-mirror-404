# Secure Defaults and Hardening Options

## Overview

This document describes souleyez's default security configuration and optional hardening measures for high-security environments.

---

## Default Security Posture

### Out-of-the-Box Configuration

souleyez ships with secure defaults that balance usability and security:

| Feature | Default | Security Level | Justification |
|---------|---------|----------------|---------------|
| Credential encryption | ❌ Disabled | Low | Opt-in for usability |
| Database permissions | ✅ 600 (user-only) | High | Prevents other users reading |
| Log file permissions | ✅ 600 (user-only) | High | Protects sensitive output |
| Config file permissions | ✅ 600 (user-only) | High | Protects crypto config |
| Root execution | ⚠️ Allowed (tools may need) | Medium | Some tools require root |
| Tool path verification | ❌ Disabled | Low | Uses system PATH |
| Auto-chaining | ✅ Enabled | Medium | Convenience feature |
| Worker auto-start | ✅ Enabled | Medium | Background processing |

### Default File Permissions

```bash
# Database
-rw------- 1 user user  data/souleyez.db

# Crypto config
-rw------- 1 user user  ~/.souleyez/crypto.json

# Job logs
-rw------- 1 user user  data/jobs/*.log

# Reports (readable for sharing)
-rw-r--r-- 1 user user  reports/*.html
```

---

## Recommended Security Configuration

### Baseline Security (All Users)

**1. Enable Credential Encryption**

```bash
python3 migrate_credentials.py
```

**Why:** Protects credentials if database is stolen

**Cost:** Password prompt when viewing credentials

---

**2. Use Strong Master Password**

```bash
# Good examples
Tr0ut-F1sh!ng-B0at$42
MyD0g'sN@me&B1rthY3ar!99

# Bad examples
password123
souleyez2024
```

**Why:** Weak passwords can be brute-forced

**Cost:** Harder to remember (use password manager)

---

**3. Verify File Permissions**

```bash
# Check permissions
ls -la data/souleyez.db
ls -la ~/.souleyez/crypto.json
ls -la data/jobs/

# Fix if needed
chmod 600 data/souleyez.db
chmod 600 ~/.souleyez/crypto.json
chmod 600 data/jobs/*.log
```

**Why:** Prevents other users from reading data

**Cost:** None

---

**4. Regular Backups**

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="$HOME/souleyez_backups"
DATE=$(date +%Y%m%d)

mkdir -p "$BACKUP_DIR"
tar czf "$BACKUP_DIR/backup_$DATE.tar.gz" \
    ~/.souleyez/crypto.json \
    data/souleyez.db

# Keep only last 30 days
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +30 -delete
```

**Why:** Recovery from data loss or corruption

**Cost:** Disk space, backup time

---

### Enhanced Security (Teams/Enterprises)

**5. Dedicated User Account**

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash souleyez_user

# Switch to user
sudo su - souleyez_user

# Install souleyez
pip install souleyez
```

**Why:** Isolates souleyez from other processes

**Cost:** More complex setup

---

**6. Filesystem Isolation**

```bash
# Create separate partition
sudo mkfs.ext4 /dev/sdb1
sudo mkdir /opt/souleyez_data

# Mount with noexec, nosuid
sudo mount -o noexec,nosuid /dev/sdb1 /opt/souleyez_data

# Add to /etc/fstab
/dev/sdb1 /opt/souleyez_data ext4 noexec,nosuid,nodev 0 2

# Move data directory
mv data /opt/souleyez_data/
ln -s /opt/souleyez_data/data data
```

**Why:** Limits impact of compromise

**Cost:** Requires additional disk, complex setup

---

**7. Network Segmentation**

```bash
# Use dedicated VLAN for scanning
# Configure network interface
sudo ip link add link eth0 name eth0.100 type vlan id 100
sudo ip addr add 10.100.0.10/24 dev eth0.100
sudo ip link set eth0.100 up

# Route scans through VLAN
souleyez jobs enqueue nmap 10.100.0.0/24
```

**Why:** Isolates scanning traffic

**Cost:** Network infrastructure changes

---

**8. Full-Disk Encryption**

```bash
# Linux (LUKS)
sudo cryptsetup luksFormat /dev/sdb1
sudo cryptsetup open /dev/sdb1 encrypted_disk
sudo mkfs.ext4 /dev/mapper/encrypted_disk

# macOS (FileVault)
# System Preferences > Security & Privacy > FileVault > Turn On

# Windows (BitLocker)
# Control Panel > BitLocker Drive Encryption > Turn On
```

**Why:** Protects data if physical access gained

**Cost:** Performance overhead (~5-10%)

---

## Hardening Options

### Option 1: Disable Auto-Chaining

**Default:** Enabled

**Risk:** Automated scans may be more noisy or unauthorized

**Disable:**

Via dashboard: Press `[a]` to toggle

Via code:
```python
# souleyez/config.py
AUTO_CHAINING_ENABLED = False
```

**Trade-off:** Manual tool selection required

---

### Option 2: Use Absolute Tool Paths

**Default:** Uses system PATH

**Risk:** Malicious tools in PATH could be executed

**Harden:**

Create plugin wrapper:

```python
# souleyez/plugins/nmap.py

TOOL_PATH = "/usr/bin/nmap"  # Absolute path

def run(self, target, args, label, log_path):
    cmd = [TOOL_PATH, target] + args
    # ... execution logic
```

**Trade-off:** Less flexible, requires maintenance

---

### Option 3: Restrict Tool Whitelist

**Default:** Any tool can be executed

**Risk:** Unintended tool execution

**Harden:**

```python
# souleyez/config.py

ALLOWED_TOOLS = [
    'nmap',
    'nikto',
    'gobuster',
    'sqlmap',
    # Add only tools you use
]

# souleyez/engine/background.py
def enqueue_job(tool, target, args, label):
    if tool not in ALLOWED_TOOLS:
        raise ValueError(f"Tool '{tool}' not in whitelist")
    # ... normal logic
```

**Trade-off:** Reduced flexibility

---

### Option 4: Enable Audit Logging

**Default:** Basic logging only

**Risk:** No audit trail of actions

**Harden:**

```python
# souleyez/utils/audit.py

import logging
import datetime

audit_log = logging.getLogger('souleyez.audit')
audit_log.setLevel(logging.INFO)
handler = logging.FileHandler('data/logs/audit.log')
audit_log.addHandler(handler)

def log_action(action, user, engagement, details):
    audit_log.info(f"{datetime.datetime.now()} | {user} | {engagement} | {action} | {details}")

# Usage in code
from souleyez.utils.audit import log_action

def enqueue_job(tool, target, args, label):
    log_action('JOB_ENQUEUE', os.getuser(), get_current_engagement(), f"{tool} {target}")
    # ... normal logic
```

**Trade-off:** Increased disk usage, slight performance impact

---

### Option 5: Implement Session Timeouts

**Default:** No timeout (key stays in memory)

**Risk:** Unattended session could be used

**Harden:**

```python
# souleyez/storage/crypto.py

import time

class CryptoManager:
    SESSION_TIMEOUT = 900  # 15 minutes
    
    def __init__(self):
        self._last_unlock = None
        # ... existing init
    
    def unlock(self, password):
        success = # ... existing unlock logic
        if success:
            self._last_unlock = time.time()
        return success
    
    def _check_timeout(self):
        if self._last_unlock and (time.time() - self._last_unlock) > self.SESSION_TIMEOUT:
            self.lock()
            raise TimeoutError("Session expired. Please unlock again.")
    
    def encrypt(self, plaintext):
        self._check_timeout()
        # ... existing encrypt logic
    
    def decrypt(self, ciphertext):
        self._check_timeout()
        # ... existing decrypt logic
```

**Trade-off:** More frequent password prompts

---

### Option 6: Secure Log Redaction

**Default:** Full tool output logged

**Risk:** Credentials or tokens in logs

**Harden:**

```python
# souleyez/utils/redaction.py

import re

REDACTION_PATTERNS = [
    (r'password[:\s]*\S+', 'password: [REDACTED]'),
    (r'token[:\s]*\S+', 'token: [REDACTED]'),
    (r'api[_-]?key[:\s]*\S+', 'api_key: [REDACTED]'),
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL REDACTED]'),
]

def redact_sensitive(text):
    """Redact sensitive information from text."""
    for pattern, replacement in REDACTION_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

# Usage in result handler
def save_job_log(job_id, output):
    redacted = redact_sensitive(output)
    with open(f"data/jobs/{job_id}.log", 'w') as f:
        f.write(redacted)
```

**Trade-off:** Harder to debug, may redact useful data

---

### Option 7: Database Integrity Checks

**Default:** No integrity verification

**Risk:** Silent data tampering

**Harden:**

```python
# souleyez/storage/integrity.py

import hmac
import hashlib

SECRET_KEY = b"your-secret-key"  # Store securely

def generate_hmac(data):
    """Generate HMAC for data integrity."""
    h = hmac.new(SECRET_KEY, data.encode('utf-8'), hashlib.sha256)
    return h.hexdigest()

def verify_hmac(data, expected_hmac):
    """Verify data integrity."""
    actual_hmac = generate_hmac(data)
    return hmac.compare_digest(actual_hmac, expected_hmac)

# Usage
def save_finding(title, description, severity):
    data = f"{title}|{description}|{severity}"
    integrity_hash = generate_hmac(data)
    
    db.execute(
        "INSERT INTO findings (title, description, severity, integrity_hash) VALUES (?, ?, ?, ?)",
        (title, description, severity, integrity_hash)
    )

def get_finding(finding_id):
    finding = db.execute_one("SELECT * FROM findings WHERE id = ?", (finding_id,))
    
    data = f"{finding['title']}|{finding['description']}|{finding['severity']}"
    if not verify_hmac(data, finding['integrity_hash']):
        raise IntegrityError("Finding has been tampered with!")
    
    return finding
```

**Trade-off:** Storage overhead, performance impact

---

### Option 8: Read-Only Mode

**Default:** Full read/write access

**Risk:** Accidental or malicious data modification

**Harden:**

```python
# souleyez/config.py
READ_ONLY_MODE = True

# souleyez/storage/database.py
def insert(self, table, data):
    if READ_ONLY_MODE:
        raise PermissionError("Database is in read-only mode")
    # ... normal insert

def execute(self, query, params=()):
    if READ_ONLY_MODE and query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
        raise PermissionError("Database is in read-only mode")
    # ... normal execute
```

**Use case:** Reviewing archived engagements

**Trade-off:** Cannot run new scans or modify data

---

## Environment-Specific Hardening

### Single-User Laptop

**Priority:** Protect against physical theft

**Recommendations:**
1. ✅ Full-disk encryption (LUKS/FileVault/BitLocker)
2. ✅ Strong screen lock password
3. ✅ Auto-lock after 5 minutes idle
4. ✅ Credential encryption enabled
5. ⚠️ VPN for remote targets (if applicable)

**Skip:**
- Dedicated user account (single user)
- Filesystem isolation (overkill)
- Network segmentation (no local network)

---

### Team Workstation

**Priority:** Multi-user separation

**Recommendations:**
1. ✅ Dedicated user per team member
2. ✅ Separate databases per user
3. ✅ File permissions strictly enforced
4. ✅ Audit logging enabled
5. ✅ Centralized backup solution

**Skip:**
- Full-disk encryption (if in secure facility)

---

### Enterprise Scanning Server

**Priority:** Compliance and auditability

**Recommendations:**
1. ✅ Dedicated VM or container per engagement
2. ✅ Network segmentation (scanning VLAN)
3. ✅ Centralized logging (syslog/SIEM)
4. ✅ Read-only mode for archived engagements
5. ✅ Regular security audits
6. ✅ Integrity checks on all data
7. ✅ Hardware security keys (YubiKey) for auth (TODO)

**Skip:**
- Interactive dashboard (CLI automation preferred)

---

### Cloud/VPS Instance

**Priority:** Remote access security

**Recommendations:**
1. ✅ SSH key authentication only (disable password)
2. ✅ Firewall (block all except SSH port)
3. ✅ Full-disk encryption
4. ✅ Regular security updates
5. ✅ Credential encryption enabled
6. ⚠️ Consider VPN for all scanner traffic

**Configuration:**

```bash
# SSH hardening
sudo vi /etc/ssh/sshd_config

PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no

# Firewall
sudo ufw default deny incoming
sudo ufw allow 22/tcp
sudo ufw enable

# Automatic updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

**Skip:**
- GUI/dashboard (SSH terminal only)

---

## Compliance Configurations

### GDPR Compliance (EU)

**Requirements:**
- Right to erasure
- Data encryption
- Audit trails
- Data minimization

**Implementation:**

```python
# Engagement deletion (right to erasure)
def delete_engagement_gdpr_compliant(engagement_name):
    em = EngagementManager()
    eng = em.get(engagement_name)
    
    # Log deletion for audit
    log_action('ENGAGEMENT_DELETE', os.getuser(), engagement_name, 'GDPR erasure request')
    
    # Secure delete (overwrite before unlink)
    for log_file in glob.glob(f"data/jobs/*.log"):
        with open(log_file, 'wb') as f:
            f.write(os.urandom(os.path.getsize(log_file)))
        os.unlink(log_file)
    
    # Delete from database
    em.delete(engagement_name)
    
    print(f"✅ Engagement '{engagement_name}' erased (GDPR compliant)")
```

**Data Minimization:**
- Only store necessary fields
- Redact PII in logs
- Auto-delete old engagements

---

### HIPAA Compliance (US Healthcare)

**Requirements:**
- Encryption at rest and in transit
- Access controls
- Audit logging
- Secure disposal

**Implementation:**

```python
# Encrypt all data (not just credentials)
ENCRYPT_ALL_FIELDS = True

# Audit all access
def get_finding(finding_id):
    log_action('FINDING_ACCESS', os.getuser(), get_current_engagement(), f"Finding {finding_id}")
    return db.execute_one("SELECT * FROM findings WHERE id = ?", (finding_id,))

# Secure deletion
def secure_delete_engagement(engagement_name):
    # DOD 5220.22-M standard (7-pass overwrite)
    # ... implementation
    pass
```

**Network:**
- All scanning through encrypted VPN
- No cloud storage without encryption

---

### PCI-DSS Compliance (Payment Card Industry)

**Requirements:**
- Strong access controls
- Encrypted cardholder data
- Regular security testing
- Restricted network access

**Implementation:**

- Dedicated scanning network (isolated VLAN)
- Session timeout (15 minutes)
- Strong password policy (12+ chars)
- Quarterly security audits
- Two-factor authentication (TODO)

---

## Security Checklist

### Initial Setup

- [ ] Enable credential encryption
- [ ] Set strong master password (12+ chars)
- [ ] Verify file permissions (600 on sensitive files)
- [ ] Configure automated backups
- [ ] Test recovery procedure

### Daily Operations

- [ ] Lock screen when away
- [ ] Log out of souleyez when done
- [ ] Review findings before acting
- [ ] Verify target authorization

### Weekly

- [ ] Review audit logs (if enabled)
- [ ] Check for security updates
- [ ] Verify backup integrity

### Monthly

- [ ] Rotate credentials on targets
- [ ] Archive old engagements
- [ ] Review user access (if multi-user)
- [ ] Test disaster recovery

### Quarterly

- [ ] Security audit of souleyez installation
- [ ] Review hardening configuration
- [ ] Update threat model
- [ ] Penetration test of scanning infrastructure

---

## Testing Security Configuration

### 1. Verify Encryption

```bash
# Should prompt for password
souleyez creds list

# Check database (should see encrypted data)
sqlite3 data/souleyez.db "SELECT username FROM credentials LIMIT 1;"
# Output: gAAAAABl... (base64 Fernet ciphertext)
```

### 2. Test File Permissions

```bash
# Create test user
sudo useradd testuser

# Try to access database as test user
sudo -u testuser cat data/souleyez.db
# Should fail: Permission denied
```

### 3. Verify Backup/Recovery

```bash
# Create backup
./backup_souleyez.sh

# Delete data
rm -rf data/ ~/.souleyez/

# Restore
tar xzf ~/souleyez_backups/backup_20251029.tar.gz
# ... restore files

# Verify
souleyez creds list
```

### 4. Test Session Timeout (if enabled)

```bash
# Unlock
souleyez creds list

# Wait for timeout (15 min)
sleep 901

# Try to access again (should require password)
souleyez creds list
```

---

## Performance Impact

| Hardening Option | Performance Impact | Recommendation |
|-----------------|-------------------|----------------|
| Credential encryption | Negligible | Enable always |
| Full-disk encryption | 5-10% I/O overhead | Enable for laptops |
| Audit logging | 1-2% overhead | Enable for teams |
| Integrity checks | 5% overhead | Enable for compliance |
| Session timeouts | Negligible | Enable for shared systems |
| Log redaction | 1% overhead | Enable by default |

---

## See Also

- [Threat Model](threat-model.md)
- [Credential Encryption](credential-encryption.md)
- [Security Best Practices](best-practices.md)
- [SECURITY.md](../../SECURITY.md)
