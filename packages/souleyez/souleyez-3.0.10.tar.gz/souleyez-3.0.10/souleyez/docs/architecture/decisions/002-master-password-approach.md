# ADR-002: Master Password Encryption Approach

**Status**: Accepted
**Date**: 2025-10-29
**Deciders**: y0d8, S0ul H@ck3r$
**Supersedes**: None

---

## Context

Penetration testing tools discover sensitive credentials (usernames, passwords, API keys) during engagements. These must be stored securely to:

1. **Prevent unauthorized access** if the operator's laptop is stolen
2. **Comply with client NDAs** requiring encryption at rest
3. **Meet security standards** (PCI-DSS, SOC 2) for credential handling

souleyez needs a **credential encryption strategy** that balances security with usability.

---

## Decision

**souleyez uses master password-based encryption with PBKDF2 key derivation and Fernet (AES-128-CBC + HMAC-SHA256) symmetric encryption.**

### Key Design Choices

1. **Master Password**: User-provided passphrase (never stored)
2. **Key Derivation**: PBKDF2-HMAC-SHA256 with 480,000 iterations
3. **Encryption**: Fernet (AES-128 in CBC mode + HMAC authentication)
4. **Scope**: Encrypts `credentials.username` and `credentials.password` fields only
5. **Unlock**: Session-based (key lives in memory, cleared on exit)
6. **Mandatory**: Encryption is configured during setup wizard

---

## Implementation Details

### Cryptographic Components

**File**: `souleyez/storage/crypto.py`

```
User Master Password (plaintext)
         │
         ▼
┌────────────────────────────────────────┐
│  PBKDF2-HMAC-SHA256                    │
│  • Algorithm: SHA-256                  │
│  • Salt: 32 bytes (random, stored)     │
│  • Iterations: 480,000 (OWASP 2023)    │
│  • Output: 32 bytes                    │
└────────┬───────────────────────────────┘
         │
         ▼
    Derived Key (32 bytes)
         │
         ▼
┌────────────────────────────────────────┐
│  Base64 URL-Safe Encoding              │
└────────┬───────────────────────────────┘
         │
         ▼
    Fernet Encryption Key
         │
         ▼
┌────────────────────────────────────────┐
│  Fernet Instance (singleton)           │
│  • Encryption: AES-128-CBC             │
│  • Authentication: HMAC-SHA256         │
│  • Timestamp: Included in ciphertext   │
└────────────────────────────────────────┘
```

### Storage Structure

**Config File**: `~/.souleyez/crypto.json`
```json
{
  "salt": "base64-encoded-32-byte-salt",
  "encryption_enabled": true
}
```

**File Permissions**: `0o600` (readable only by owner)

**Database Schema**: `~/.souleyez/souleyez.db`
```sql
CREATE TABLE credentials (
    username TEXT,  -- Stores Fernet token if encrypted
    password TEXT   -- Stores Fernet token if encrypted
);
```

### Unlock Flow

```
1. User runs: souleyez creds list
2. Check if encryption enabled? → YES
3. Check if already unlocked? → NO
4. Prompt: "Enter master password: "
5. Derive key: PBKDF2(password, salt, 480000)
6. Test key: encrypt("test") → decrypt() → verify
7. Store Fernet instance in memory (CryptoManager._fernet)
8. Fetch encrypted credentials from database
9. Decrypt each field: Fernet.decrypt(ciphertext)
10. Display plaintext credentials
11. On exit: CryptoManager.lock() → _fernet = None
```

### Security Properties

| Property | Implementation |
|----------|----------------|
| **Confidentiality** | AES-128-CBC encryption |
| **Integrity** | HMAC-SHA256 authentication tag |
| **Key Derivation** | PBKDF2-HMAC-SHA256 (480k iterations) |
| **Salt** | 32-byte random salt (unique per installation) |
| **Key Storage** | Memory-only (never written to disk) |
| **Password Storage** | Never stored (derived on-demand) |
| **Session Management** | Unlocked for CLI invocation, locked on exit |
| **Backward Compatibility** | Graceful fallback to plaintext (InvalidToken exception) |

---

## Rationale

### Why Master Password?

#### Compared to Hardware Tokens (YubiKey, TPM)

**Pros of Master Password**:
- ✅ **Zero Dependencies**: No hardware required
- ✅ **Cross-Platform**: Works on any Linux system
- ✅ **Portable**: Operator can use same password on multiple machines
- ✅ **Simple Setup**: No driver installation or device pairing
- ✅ **Cost**: Free (hardware tokens cost $50-100)

**Cons of Master Password**:
- ❌ **Phishing Risk**: Password can be typed into fake prompts
- ❌ **Keylogger Risk**: Compromised system can capture password
- ❌ **Memory Dump Risk**: Key exists in RAM during unlock

**Decision**: For a penetration testing tool used by **trusted operators on their own machines**, master password is sufficient. Hardware tokens are overkill for this threat model.

#### Compared to SSH Key-Based Encryption

**Alternative**: Use operator's SSH private key to encrypt credentials.

**Pros**:
- ✅ Reuse existing SSH key infrastructure
- ✅ No additional password to remember

**Cons**:
- ❌ Ties credential encryption to SSH key (bad separation of concerns)
- ❌ If SSH key is compromised, credentials are also compromised
- ❌ Difficult to rotate encryption key without rotating SSH key
- ❌ SSH keys often unencrypted or use weak passphrases

**Decision**: Master password provides **independent key management** decoupled from SSH infrastructure.

#### Compared to OS Keychain (Gnome Keyring, KWallet)

**Alternative**: Store master password in OS keychain, auto-unlock.

**Pros**:
- ✅ No password prompts (unlocks with user login)
- ✅ OS-managed encryption

**Cons**:
- ❌ Platform-specific (Linux, macOS, Windows all different)
- ❌ Requires D-Bus or platform-specific APIs
- ❌ Auto-unlock reduces security (anyone with user session access)
- ❌ Difficult to audit keychain access

**Decision**: Explicit password prompts are **intentionally secure**. Operators should consciously unlock credentials, not auto-unlock.

#### Compared to Cloud Key Management (AWS KMS, HashiCorp Vault)

**Alternative**: Store encryption key in external KMS.

**Pros**:
- ✅ Centralized key management
- ✅ Audit logging of key access
- ✅ Key rotation support

**Cons**:
- ❌ Requires internet connection (breaks offline pentesting)
- ❌ Cloud dependency (against souleyez's local-first philosophy)
- ❌ Complex setup (IAM roles, authentication)
- ❌ Vendor lock-in
- ❌ Cost ($1-10/month per key)

**Decision**: Penetration testing often occurs in **air-gapped or offline environments**. Cloud KMS is incompatible.

### Why PBKDF2 (Not Argon2 or scrypt)?

**PBKDF2-HMAC-SHA256** is chosen over modern alternatives:

| Algorithm | Pros | Cons |
|-----------|------|------|
| **PBKDF2** | ✅ NIST-approved<br>✅ Widely supported<br>✅ Python stdlib (cryptography lib)<br>✅ Tunable iterations | ❌ Less memory-hard than Argon2 |
| **Argon2** | ✅ Memory-hard (resists GPU attacks)<br>✅ Winner of Password Hashing Competition | ❌ Requires external library<br>❌ More complex configuration |
| **scrypt** | ✅ Memory-hard | ❌ Difficult to tune correctly<br>❌ Less standardized |

**Decision**: PBKDF2 with **480,000 iterations** (OWASP 2023 recommendation) provides sufficient security for the threat model. Argon2 would be better against GPU-based attacks, but:
- Our threat is **laptop theft**, not online password cracking
- Attacker needs physical access + ability to extract database
- At that point, they can extract RAM dumps too

**Future**: If moving to Argon2, update `crypto.py` and bump migration version.

### Why Fernet (Not Raw AES)?

**Fernet** is a high-level encryption standard that combines:
- AES-128-CBC encryption
- HMAC-SHA256 authentication
- Timestamp (for TTL support, though we don't use it)
- Base64 encoding

**Pros**:
- ✅ **Authentication**: HMAC prevents tampering (encrypt-then-MAC)
- ✅ **Standard**: Well-defined spec (cryptography.io)
- ✅ **Simple API**: `encrypt()` / `decrypt()` (no IV management)
- ✅ **Audited**: Part of widely-reviewed cryptography library

**Cons**:
- ❌ AES-128 (not AES-256, though 128-bit is still secure)

**Alternatives Considered**:
- **Raw AES-GCM**: More complex (requires IV generation), but authenticated encryption
- **ChaCha20-Poly1305**: Faster on non-AES-NI CPUs, but less standardized

**Decision**: Fernet is the **safe, simple choice** for application-level encryption.

### Why Mandatory Encryption?

Encryption is **required** and configured during the setup wizard.

**Rationale**:
1. **Security First**: As a security company, we cannot allow plaintext credential storage
2. **Consistency**: All users have the same security baseline
3. **Compliance**: Encrypted storage is expected for professional pentesting tools
4. **Simplicity**: One-time setup during wizard, no migration scripts needed

**Default Behavior**: Credentials are **always encrypted** with the vault master password.

**Password Requirements**:
- At least 12 characters
- Mix of uppercase and lowercase
- At least one number
- At least one special character

---

## Consequences

### Positive

1. **Security**:
   - Encryption at rest protects against laptop theft
   - PBKDF2 with 480k iterations resists brute-force attacks
   - HMAC authentication prevents tampering

2. **Simplicity**:
   - No external dependencies (hardware tokens, cloud KMS)
   - Works offline
   - Single Python library (`cryptography`)

3. **Usability**:
   - Password-based (familiar UX)
   - Session-based unlock (enter password once per session)
   - Dashboard masking prevents accidental exposure

4. **Compliance**:
   - Meets PCI-DSS requirement 3.4 (protect stored credentials)
   - Satisfies most client NDA encryption clauses

### Negative

1. **Password Recovery**: No way to recover lost master password (data loss risk)
2. **Threat Model Limitations**: Does not protect against:
   - Memory dumps (key in RAM during unlock)
   - Keyloggers on compromised systems
   - Live system compromise (attacker can unlock if operator is logged in)
3. **AES-128**: Fernet uses AES-128, not AES-256 (though 128-bit is sufficient for non-government use)
4. **Single-User**: No multi-user access control or key sharing

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| **Lost Password** | Document password in operator's password manager (KeePassXC) |
| **Weak Password** | Enforce 8-character minimum, warn users about strength |
| **Keylogger** | Assume operator's workstation is secure (required for pentest work) |
| **Memory Dump** | Accept as inherent risk (impractical to protect against) |
| **Database Backup** | Encrypted credentials remain encrypted in backups (secure by default) |

---

## Alternatives Considered

### 1. Age (File Encryption Tool)

**Idea**: Use `age` (modern, simple encryption tool) to encrypt database file.

**Pros**:
- Simple CLI: `age -e -o souleyez.db.age souleyez.db`
- Support for multiple recipients (public key)

**Cons**:
- Encrypts entire database (cannot query without decryption)
- Requires decryption before each use (slow)
- No field-level encryption (all-or-nothing)

**Verdict**: **Rejected** - Need queryable database.

### 2. SQLCipher (Encrypted SQLite)

**Idea**: Replace SQLite with SQLCipher (encrypted SQLite fork).

**Pros**:
- Transparent encryption (entire database)
- Queryable while encrypted (page-level encryption)
- Standard SQLite API

**Cons**:
- Requires compiling SQLCipher or binary distribution
- Password prompt on every connection (no session unlock)
- Cannot inspect database with standard SQLite tools
- More complex installation

**Verdict**: **Rejected** - Too complex for installation. Field-level encryption is sufficient.

### 3. Envelope Encryption (Data Key + Master Key)

**Idea**: Generate random data encryption key (DEK), encrypt DEK with master password.

```
Master Password → Master Key (PBKDF2)
Master Key → Encrypt(DEK)
DEK → Encrypt(Credentials)
```

**Pros**:
- Faster password changes (only re-encrypt DEK, not all data)
- Key rotation without re-encrypting data

**Cons**:
- More complex implementation
- Additional key management
- Overkill for single-user tool

**Verdict**: **Deferred** - Consider for future multi-user version.

### 4. No Encryption

**Idea**: Store credentials in plaintext, rely on OS file permissions.

**Pros**:
- Simplest implementation
- No password prompts
- Faster queries

**Cons**:
- ❌ **Unacceptable**: Laptop theft exposes all credentials
- ❌ Violates most client NDAs
- ❌ Fails PCI-DSS compliance

**Verdict**: **Rejected** - Security requirement.

---

## Future Considerations

### Hardware Token Support (Phase 2)

**When**: If users request YubiKey/TPM support (3+ GitHub issues).

**Design**:
- Use FIDO2 HMAC-Secret extension to derive encryption key
- Master password as fallback (if no hardware token present)
- Optional: Require BOTH password AND hardware token (2FA)

**Implementation**:
```python
# Use YubiKey to derive key
hmac_secret = yubikey.get_hmac_secret(challenge="souleyez")
key = PBKDF2(hmac_secret, salt, 100000)
```

### Audit Logging (Phase 3)

**When**: Multi-user support or enterprise deployments.

**Design**:
- Log all credential access events
- Store in append-only log file
- Include: timestamp, user, credential_id, action (view/test)

**Schema**:
```sql
CREATE TABLE audit_log (
    timestamp TEXT,
    user TEXT,
    credential_id INTEGER,
    action TEXT
);
```

### Key Rotation (Phase 3)

**When**: Operators need to change master password without data loss.

**Current Limitation**: Changing password requires manual re-encryption:
1. Unlock with old password
2. Decrypt all credentials
3. Generate new salt
4. Encrypt with new password

**Improvement**: Add `souleyez creds rotate-password` command.

---

## Related Decisions

- [ADR-001: No LLM Integration](001-no-llm-integration.md) - Privacy-first design
- [ADR-003: SQLite Database Choice](003-database-schema-design.md) - Queryable encrypted fields

---

## References

- OWASP Password Storage Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- NIST SP 800-132 (PBKDF2 Recommendations): https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-132.pdf
- Fernet Specification: https://github.com/fernet/spec/blob/master/Spec.md
- Cryptography Library Docs: https://cryptography.io/en/latest/fernet/

---

**Authors**: y0d8, S0ul H@ck3r$
**Last Updated**: 2025-10-29
