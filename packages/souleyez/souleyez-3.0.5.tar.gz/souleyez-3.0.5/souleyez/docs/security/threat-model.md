# Security Threat Model and Assumptions

## Overview

This document outlines the security assumptions, threat model, and design decisions for souleyez. Understanding these limitations is critical for secure deployment.

---

## Security Scope

### What SoulEyez Protects

✅ **In Scope:**
- Credential storage (via encryption)
- Local database integrity
- Process isolation
- Tool execution sandboxing
- Engagement data separation

❌ **Out of Scope:**
- Network traffic encryption (use VPN/SSH tunnels)
- Operating system security
- Physical access to the system
- Memory dumps/swap analysis
- Side-channel attacks
- Targeted malware/rootkits

---

## Threat Model

### Assumed Attacker Capabilities

**Low-Privilege Local Attacker:**
- Can read files with user permissions
- Cannot elevate privileges
- Cannot access other user accounts
- Cannot modify system files

**Network Attacker:**
- Can observe network traffic
- Cannot compromise endpoints
- Cannot access local files

### Trust Boundaries

```
┌─────────────────────────────────────┐
│     Trusted Zone (User Context)     │
│  - souleyez application           │
│  - SQLite database                  │
│  - Security tools (nmap, etc.)      │
│  - User's home directory            │
└─────────────────────────────────────┘
           ↑
           │ Trust Boundary
           ↓
┌─────────────────────────────────────┐
│   Untrusted Zone (External)         │
│  - Network targets                  │
│  - Tool outputs                     │
│  - Imported data                    │
│  - Internet services                │
└─────────────────────────────────────┘
```

---

## Security Assumptions

### Environmental Assumptions

1. **Single-User System**
   - One user per souleyez instance
   - User has exclusive access to home directory
   - No untrusted users on system

2. **Secure Operating System**
   - OS is up-to-date with security patches
   - Standard Linux filesystem permissions enforced
   - No compromised system services

3. **Physical Security**
   - System is physically secure
   - Disk encryption (LUKS/FileVault) recommended but not required
   - Screen lock enabled when unattended

4. **Trusted Tools**
   - Security tools (nmap, nikto, etc.) are legitimate
   - Tools installed via official repositories
   - No malicious tool versions

### User Responsibilities

**Users Must:**
- Choose strong master passwords (12+ characters)
- Protect master password (use password manager)
- Secure their system and user account
- Review and understand scan results
- Follow responsible disclosure for findings

**Users Must Not:**
- Share master passwords
- Run souleyez as root
- Store master password in plaintext
- Scan unauthorized targets
- Share encrypted databases between users

---

## Attack Scenarios

### Scenario 1: Local File Access

**Attacker Goal:** Access stored credentials

**Without Encryption:**
- ❌ **Vulnerable**: Credentials stored in plaintext SQLite database
- Attacker can read `data/souleyez.db` directly
- All usernames and passwords exposed

**With Encryption:**
- ✅ **Protected**: Credentials encrypted with Fernet (AES-128)
- Requires master password to decrypt
- Salt stored separately, password never persisted

**Mitigation:**
- Enable credential encryption
- Use strong master password
- Secure file permissions (600 on database)
- Consider full-disk encryption

---

### Scenario 2: Process Memory Dump

**Attacker Goal:** Extract master password or encryption key from memory

**Risk Level:** Medium

**Vulnerability:**
- Master password held in memory during active session
- Encryption key derived and cached
- Tools like `gcore` can dump process memory

**Current State:**
- ❌ No memory protection mechanisms
- ❌ Key not zeroed after use
- ❌ No anti-debugging measures

**Mitigation:**
- Log out when not using souleyez
- Use `mlock()` to prevent swapping (TODO)
- Implement key auto-expiration (TODO)
- Consider hardware security keys (TODO)

**Acceptance:**
- Defending against memory dumps requires root privileges
- Out of scope for user-space application
- Users with root can already access everything

---

### Scenario 3: Malicious Tool Output

**Attacker Goal:** Inject malicious data via tool output

**Risk Level:** Low to Medium

**Vulnerability:**
- Parsers process untrusted tool output
- SQL injection via unsanitized strings
- Path traversal via file references

**Protections:**
- ✅ Parameterized SQL queries (prevents SQL injection)
- ✅ Input validation in parsers
- ⚠️ Limited path sanitization (needs review)

**Mitigation:**
- Use official tool versions from trusted sources
- Review unusual findings before acting
- Sandbox tool execution (TODO)

---

### Scenario 4: Database Tampering

**Attacker Goal:** Modify engagement data or findings

**Risk Level:** Low

**Vulnerability:**
- SQLite database is just a file
- No built-in integrity checks
- File-level access = full control

**Current State:**
- ❌ No database integrity verification
- ❌ No audit logging
- ❌ No tampering detection

**Mitigation:**
- Secure file permissions (600)
- Regular backups with checksums
- Implement HMAC for critical tables (TODO)

**Acceptance:**
- If attacker has file access, they control user's data
- Standard for SQLite applications
- Enterprise use should implement external auditing

---

### Scenario 5: Tool Execution Hijacking

**Attacker Goal:** Execute malicious code via tool names

**Risk Level:** High

**Vulnerability:**
- Tools executed via subprocess with user permissions
- PATH environment variable controls tool resolution
- Malicious `nmap` in PATH could be executed

**Example:**
```bash
# Attacker creates malicious nmap
echo '#!/bin/bash\nrm -rf ~' > /tmp/nmap
chmod +x /tmp/nmap
export PATH=/tmp:$PATH

# souleyez executes malicious nmap
souleyez jobs enqueue nmap 192.168.1.1
```

**Protections:**
- ⚠️ Uses system PATH (standard behavior)
- ❌ No absolute path verification
- ❌ No tool signature verification

**Mitigation:**
- Use absolute paths in plugins (e.g., `/usr/bin/nmap`)
- Verify tool checksums before execution (TODO)
- Implement allowed-tools whitelist (TODO)

**User Responsibility:**
- Don't run souleyez with attacker-controlled PATH
- Verify tool installations
- Use tools from official repositories

---

### Scenario 6: Log File Information Leakage

**Attacker Goal:** Extract sensitive data from log files

**Risk Level:** Medium

**Vulnerability:**
- Job logs contain full tool output
- May include credentials, API keys, session tokens
- Logs stored in plaintext

**Example:**
```
# Hydra output in log
[22][ssh] host: 192.168.1.100   login: admin   password: SuperSecret123
```

**Current State:**
- ❌ Logs not encrypted
- ❌ Sensitive data not redacted
- ⚠️ File permissions set to 600 (user-only)

**Mitigation:**
- Secure log directory permissions
- Rotate and archive old logs
- Consider log encryption (TODO)
- Implement sensitive data redaction (TODO)

---

## Data Protection

### Sensitive Data Types

| Data Type | Storage | Protection | Risk |
|-----------|---------|------------|------|
| Credentials | Database | Mandatory encryption (Fernet/AES-128) | High |
| Job logs | Plaintext files | File permissions | Medium |
| Targets | Database | Plaintext | Low |
| Findings | Database | Plaintext | Medium |
| OSINT data | Database | Plaintext | Low |
| Engagement names | Database | Plaintext | Low |

### Data Flow

```
Security Tool
    ↓ (stdout/stderr)
Job Log (plaintext)
    ↓ (parse)
Structured Data
    ↓ (store)
SQLite Database
    ↓ (read)
CLI/Dashboard
```

**Encryption Points:**
- Credentials: Encrypted at rest (optional)
- Job logs: Plaintext (sensitive data may leak)
- Database: Plaintext except credentials

---

## Cryptographic Design

### Credential Encryption

**Algorithm:** Fernet (AES-128-CBC + HMAC-SHA256)

**Why Fernet?**
- ✅ Authenticated encryption (prevents tampering)
- ✅ Standard Python library (`cryptography`)
- ✅ Secure defaults (no configuration errors)
- ✅ Includes timestamp for expiration (not used)

**Key Derivation:** PBKDF2-HMAC-SHA256

**Parameters:**
- Iterations: 480,000 (OWASP 2023 recommendation)
- Salt: 32 bytes (randomly generated per installation)
- Hash: SHA-256
- Key length: 32 bytes

**Why PBKDF2?**
- ✅ NIST approved (SP 800-132)
- ✅ Widely supported
- ✅ Configurable iteration count
- ⚠️ Less memory-hard than Argon2 (acceptable tradeoff)

### Security Properties

**Confidentiality:**
- AES-128 provides 128-bit security
- Sufficient for credential storage
- Not subject to quantum attacks (for now)

**Integrity:**
- HMAC-SHA256 prevents tampering
- Detects corrupted ciphertexts
- Fails securely (decryption aborts)

**Authentication:**
- Master password authenticates user
- No password = no access
- 3 failed attempts = lockout

---

## Known Limitations

### 1. Master Password Recovery

**Issue:** Master password cannot be recovered if forgotten

**Why:** Password never stored, only used to derive key

**Impact:** Encrypted credentials permanently lost

**Mitigation:** Use password manager, keep backups

---

### 2. Memory Exposure

**Issue:** Keys and passwords in process memory

**Why:** Required for decryption operations

**Impact:** Memory dumps can extract secrets

**Mitigation:** Minimize unlock duration, log out when idle

---

### 3. Swap File Exposure

**Issue:** Memory may be swapped to disk

**Why:** OS controls virtual memory

**Impact:** Secrets may persist in swap

**Mitigation:** Disable swap, use encrypted swap, or use `mlock()` (TODO)

---

### 4. Multi-User Systems

**Issue:** Other users may access files if permissions wrong

**Why:** Standard Unix file permissions

**Impact:** Database and logs accessible to privileged users

**Mitigation:** Use dedicated user accounts, check permissions

---

### 5. Root Access

**Issue:** Root can access all user data

**Why:** Root has full system control

**Impact:** Encryption provides no protection against root

**Mitigation:** Trust your root user, use dedicated systems

---

## Security Roadmap

### Short-Term (Next Release)

- [ ] Memory protection (`mlock()` for keys)
- [ ] Absolute tool paths in plugins
- [ ] Log file sensitive data redaction
- [ ] Database integrity checks (HMAC)

### Medium-Term (6 months)

- [ ] Hardware security key support (YubiKey)
- [ ] Key expiration/timeout
- [ ] Audit logging
- [ ] Tool signature verification

### Long-Term (Future)

- [ ] Argon2 key derivation (more memory-hard)
- [ ] Per-engagement encryption keys
- [ ] Zero-knowledge proof of authorization
- [ ] Credential sharing (public key crypto)

---

## Compliance

### Standards Followed

- ✅ **OWASP Password Storage Cheat Sheet** (2023)
- ✅ **NIST SP 800-132** (PBKDF2 recommendations)
- ✅ **FIPS 197** (AES encryption standard)
- ✅ **RFC 6070** (PBKDF2 test vectors)

### Best Practices

- Password never stored in plaintext
- High iteration count (480k iterations)
- Random salt per installation
- Authenticated encryption (Fernet)
- Secure defaults (encryption opt-in)

---

## Deployment Recommendations

### For Individual Pentesters

- ✅ Enable credential encryption
- ✅ Use full-disk encryption (LUKS/BitLocker)
- ✅ Strong master password (12+ characters)
- ✅ Password manager for master password
- ✅ Regular backups to encrypted storage

### For Teams

- ✅ Separate instance per team member
- ✅ Separate databases (no sharing)
- ✅ Centralized reporting via exports
- ⚠️ Consider dedicated VM per engagement
- ⚠️ Use VPN for remote scanning

### For Enterprises

- ✅ Dedicated scanning infrastructure
- ✅ Network segmentation
- ✅ Centralized audit logging (external)
- ✅ Database encryption at rest (disk-level)
- ✅ Regular security audits
- ⚠️ Consider commercial alternatives with compliance features

---

## Incident Response

### If Master Password Compromised

1. **Immediately**: Change master password (TODO: tool support)
2. **Rotate**: Change all stored credentials on target systems
3. **Audit**: Review access logs for unauthorized access
4. **Report**: Document incident per policy

### If Database Stolen

1. **Assume**: All plaintext data compromised
2. **If encrypted**: Credentials safe if strong password used
3. **Rotate**: Change credentials on target systems (if weak password)
4. **Monitor**: Watch for unauthorized access to targets

### If System Compromised

1. **Assume**: All data compromised (attacker is root)
2. **Contain**: Disconnect system from network
3. **Investigate**: Determine scope of compromise
4. **Recover**: Restore from clean backup or reinstall
5. **Rotate**: All credentials and keys

---

## Security Contact

**Reporting Vulnerabilities:**

Please **DO NOT** report security vulnerabilities via public GitHub issues.

**Contact:**
- Email: security@souleyez.dev (TODO)
- PGP Key: [TODO]
- Expected response: 48 hours

**Coordinated Disclosure:**
- Report issue privately
- Allow 90 days for patch
- Public disclosure after fix released

---

## See Also

- [Credential Encryption Guide](credential-encryption.md)
- [Security Best Practices](best-practices.md)
- [Secure Defaults](secure-defaults.md)
- [SECURITY.md](../../SECURITY.md)
