# Credential Encryption Key Management Guide

## Overview

This guide covers everything you need to know about managing encryption keys in souleyez, from initial setup to advanced scenarios.

---

## Quick Reference

| Operation | Command | Time |
|-----------|---------|------|
| Initial setup | `souleyez interactive` (setup wizard) | 5 min |
| View encrypted creds | `souleyez creds list` | Instant |
| Check encryption status | Python API | Instant |
| Backup crypto config | `cp ~/.souleyez/crypto.json backup/` | Instant |
| Change password | `souleyez db change-password` | 1 min |

> **Note:** Encryption is mandatory and configured during the first-run setup wizard.

---

## Understanding the Encryption System

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Master Password                    │
│              (memorized by user)                    │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│              PBKDF2-HMAC-SHA256                     │
│          480,000 iterations + Salt                  │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│              Encryption Key (32 bytes)              │
│              (derived, never stored)                │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│              Fernet Cipher Instance                 │
│           (AES-128-CBC + HMAC-SHA256)               │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│           Encrypted Credentials (stored)            │
│              data/souleyez.db                     │
└─────────────────────────────────────────────────────┘
```

### Key Components

**1. Master Password**
- Known only to user
- Never stored anywhere
- Minimum 12 characters (required)
- Must include: uppercase, lowercase, number, special character
- Used to derive encryption key

**2. Salt**
- 32 bytes (256 bits)
- Randomly generated per installation
- Stored in `~/.souleyez/crypto.json`
- Makes rainbow table attacks impossible

**3. Encryption Key**
- 32 bytes (256 bits)
- Derived via PBKDF2 with 480,000 iterations
- Never persisted to disk
- Exists only in memory during session

**4. Fernet Cipher**
- Symmetric encryption (same key encrypts and decrypts)
- Combines AES-128-CBC + HMAC-SHA256
- Provides confidentiality and integrity
- Base64-encoded output

---

## Initial Setup

### Encryption via Setup Wizard (Recommended)

Encryption is configured automatically during the first-run setup wizard:

```bash
souleyez interactive
```

**What happens:**
1. Setup wizard prompts for vault master password
2. Password must meet requirements (12+ chars, mixed case, number, special)
3. Password confirmation required
4. Generates random 32-byte salt
5. Derives encryption key from password + salt
6. All future credentials are automatically encrypted

### Legacy: Migration Script

For existing installations or manual setup:

```bash
python3 migrate_credentials.py
```

**What happens:**
1. Checks if encryption already enabled (fails if yes)
2. Prompts for master password (twice for confirmation)
3. Validates password (minimum 12 characters)
4. Generates random 32-byte salt
5. Derives encryption key from password + salt
6. Encrypts all existing credentials in database
7. Saves configuration to `~/.souleyez/crypto.json`

**Output:**
```
🔐 Credential Encryption Migration
==================================================

This will encrypt all stored credentials with a master password.
You will need this password to access credentials in the future.

Enter new master password: ********
Confirm master password: ********

⏳ Enabling encryption...
✅ Encryption enabled!

⏳ Fetching credentials...
📝 Found 15 credentials to encrypt

⏳ Encrypting credentials...
  ✓ Credential 1 of 15
  ✓ Credential 2 of 15
  ...
  ✓ Credential 15 of 15

✅ Migration complete! All credentials encrypted.
```

### Step 2: Verify Encryption

Check that encryption is enabled:

```python
from souleyez.storage.crypto import get_crypto_manager

crypto = get_crypto_manager()
print(f"Encryption enabled: {crypto.is_encryption_enabled()}")
```

**Expected output:**
```
Encryption enabled: True
```

### Step 3: Test Access

Try viewing credentials:

```bash
souleyez creds list
```

You'll be prompted for your master password:

```
🔐 Master password required to decrypt credentials.
Enter master password: ********

Username: admin
Password: SuperSecret123
Host: 192.168.1.100
Service: ssh
```

---

## Daily Usage

### Viewing Encrypted Credentials

**CLI:**

```bash
# Prompts for password, then displays
souleyez creds list
```

**Dashboard:**

```bash
# Shows masked credentials (no password prompt)
souleyez dashboard
```

**Output in dashboard:**
```
CREDENTIALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Username: ••••••••
Password: ••••••••
Host: 192.168.1.100
Service: ssh
```

### Password Prompt Behavior

**First Access:**
- Prompts for master password
- Maximum 3 attempts
- Fails after 3 incorrect passwords

**Session Persistence:**
- Password stays in memory for CLI session
- No re-prompt for same souleyez process
- Cleared when process exits

**Security:**
- Key derived from password stays in memory
- No timeout (TODO: implement auto-lock)
- Logout = key cleared

---

## Configuration Files

### crypto.json Structure

**Location:** `~/.souleyez/crypto.json`

**Content:**
```json
{
  "salt": "8vM3k2L9pQ7xR5nW1cB4hT6yE0aF2gH8jK3mN5vP9sZ==",
  "encryption_enabled": true
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `salt` | string | Base64-encoded 32-byte salt |
| `encryption_enabled` | boolean | Whether encryption is active |

**Permissions:**
```bash
ls -la ~/.souleyez/crypto.json
-rw------- 1 user user 123 Oct 29 10:00 crypto.json
```

**Important:** File must be readable only by owner (600 permissions)

---

## Backup and Recovery

### What to Backup

**Essential:**
- ✅ `~/.souleyez/crypto.json` (salt + config)
- ✅ `data/souleyez.db` (encrypted credentials)
- ✅ Master password (in password manager)

**Optional:**
- Job logs (`data/jobs/`)
- Reports (`reports/`)

### Backup Procedure

```bash
# Create backup directory
mkdir -p ~/souleyez_backups/$(date +%Y%m%d)

# Backup crypto config
cp ~/.souleyez/crypto.json ~/souleyez_backups/$(date +%Y%m%d)/

# Backup database
cp data/souleyez.db ~/souleyez_backups/$(date +%Y%m%d)/

# Create archive
cd ~/souleyez_backups
tar czf souleyez_backup_$(date +%Y%m%d).tar.gz $(date +%Y%m%d)/

# Verify archive
tar tzf souleyez_backup_$(date +%Y%m%d).tar.gz
```

**Automated backup script:**

```bash
#!/bin/bash
# backup_souleyez.sh

BACKUP_DIR="$HOME/souleyez_backups"
DATE=$(date +%Y%m%d)
BACKUP_PATH="$BACKUP_DIR/$DATE"

mkdir -p "$BACKUP_PATH"

cp ~/.souleyez/crypto.json "$BACKUP_PATH/"
cp data/souleyez.db "$BACKUP_PATH/"

cd "$BACKUP_DIR"
tar czf "souleyez_backup_$DATE.tar.gz" "$DATE/"
rm -rf "$DATE"

echo "✅ Backup complete: souleyez_backup_$DATE.tar.gz"
```

### Recovery Procedure

**Scenario: Lost database or crypto config**

```bash
# Extract backup
cd ~/souleyez_backups
tar xzf souleyez_backup_20251029.tar.gz

# Restore crypto config
cp 20251029/crypto.json ~/.souleyez/

# Restore database
cp 20251029/souleyez.db data/

# Set permissions
chmod 600 ~/.souleyez/crypto.json
chmod 600 data/souleyez.db

# Verify
souleyez creds list
```

---

## Advanced Operations

### Changing Master Password

**Current Status:** Manual process (automated tool TODO)

**Procedure:**

```python
#!/usr/bin/env python3
"""
change_password.py - Change encryption master password
"""
import getpass
from souleyez.storage.crypto import get_crypto_manager
from souleyez.storage.database import get_db

crypto = get_crypto_manager()
db = get_db()

# Step 1: Unlock with old password
print("Enter current master password:")
old_password = getpass.getpass()

if not crypto.unlock(old_password):
    print("❌ Incorrect password!")
    exit(1)

print("✅ Unlocked")

# Step 2: Get all encrypted credentials
credentials = db.execute("SELECT id, username, password FROM credentials")
decrypted = []

for cred in credentials:
    decrypted.append({
        'id': cred['id'],
        'username': crypto.decrypt(cred['username']) if cred['username'] else None,
        'password': crypto.decrypt(cred['password']) if cred['password'] else None
    })

print(f"Decrypted {len(decrypted)} credentials")

# Step 3: Get new password
print("\nEnter new master password:")
new_password = getpass.getpass()
confirm = getpass.getpass("Confirm new password: ")

if new_password != confirm:
    print("❌ Passwords don't match!")
    exit(1)

# Step 4: Re-enable encryption with new password
crypto.disable_encryption()
crypto.enable_encryption(new_password)

# Step 5: Re-encrypt all credentials
for cred in decrypted:
    encrypted_username = crypto.encrypt(cred['username']) if cred['username'] else None
    encrypted_password = crypto.encrypt(cred['password']) if cred['password'] else None
    
    db.execute(
        "UPDATE credentials SET username = ?, password = ? WHERE id = ?",
        (encrypted_username, encrypted_password, cred['id'])
    )

print(f"✅ Password changed! {len(decrypted)} credentials re-encrypted.")
```

**Usage:**
```bash
python3 change_password.py
```

---

### Disabling Encryption

**⚠️ WARNING:** This converts credentials back to plaintext!

**Procedure:**

```python
#!/usr/bin/env python3
"""
disable_encryption.py - Disable credential encryption
"""
import getpass
from souleyez.storage.crypto import get_crypto_manager
from souleyez.storage.database import get_db

crypto = get_crypto_manager()
db = get_db()

print("⚠️  WARNING: This will DECRYPT all credentials!")
print("   Credentials will be stored in PLAINTEXT.")
confirm = input("Type 'YES' to continue: ")

if confirm != "YES":
    print("Cancelled")
    exit(0)

# Unlock
password = getpass.getpass("Enter master password: ")
if not crypto.unlock(password):
    print("❌ Incorrect password!")
    exit(1)

# Decrypt all credentials
credentials = db.execute("SELECT id, username, password FROM credentials")

for cred in credentials:
    decrypted_username = crypto.decrypt(cred['username']) if cred['username'] else None
    decrypted_password = crypto.decrypt(cred['password']) if cred['password'] else None
    
    db.execute(
        "UPDATE credentials SET username = ?, password = ? WHERE id = ?",
        (decrypted_username, decrypted_password, cred['id'])
    )

# Disable encryption
crypto.disable_encryption()

print(f"✅ Encryption disabled. {len(credentials)} credentials now in plaintext.")
```

---

### Rotating Salt

**When to rotate:**
- Salt compromise suspected
- Changing master password
- Migrating to new system

**Procedure:**

1. Decrypt all credentials with old salt
2. Generate new salt
3. Re-encrypt with new salt + same/new password

**Note:** This is essentially the password change procedure with new salt generation.

---

## Multi-System Scenarios

### Scenario 1: Using Multiple Computers

**Problem:** Want to use souleyez on laptop and desktop

**Solution:** Separate instances (recommended)

```bash
# Laptop
python3 migrate_credentials.py
# Password: LaptopSecurePassword123

# Desktop
python3 migrate_credentials.py
# Password: DesktopSecurePassword456
```

**Why separate?**
- Different threat models (laptop more vulnerable)
- Independent key management
- No sync issues

---

### Scenario 2: Shared Database (NOT RECOMMENDED)

**Problem:** Want to share database between systems

**Solution:** Copy crypto.json + database, use same password

```bash
# System A (original)
scp ~/.souleyez/crypto.json systemB:~/.souleyez/
scp data/souleyez.db systemB:~/souleyez_app/data/

# System B
# Use same master password as System A
souleyez creds list
```

**Risks:**
- Password compromise on one system = all systems compromised
- Sync conflicts if both systems modify database
- Increased attack surface

**Better alternative:** Export/import specific engagements

---

### Scenario 3: Team Collaboration

**Problem:** Multiple team members need access

**Solution:** Individual instances + exports

```bash
# Team member A
souleyez report generate "Engagement Report"

# Share report, not database
scp reports/engagement_report.html member_b@host:/tmp/

# Member B reviews report, runs own scans if needed
```

**Why not share database?**
- Each member should have own master password
- Separate audit trails
- No shared secrets

---

## Troubleshooting

### Error: "Crypto manager is locked"

**Cause:** Encryption enabled but not unlocked

**Solution:**
```bash
souleyez creds list
# Enter password when prompted
```

---

### Error: "Invalid token" or "Incorrect password"

**Cause:** Wrong password or corrupted ciphertext

**Solutions:**

1. **Try again carefully:**
   ```bash
   souleyez creds list
   # Enter password slowly
   ```

2. **Verify encryption status:**
   ```python
   from souleyez.storage.crypto import get_crypto_manager
   crypto = get_crypto_manager()
   print(f"Enabled: {crypto.is_encryption_enabled()}")
   ```

3. **Check for corruption:**
   ```bash
   sqlite3 data/souleyez.db
   sqlite> SELECT username FROM credentials LIMIT 1;
   # Should see base64 string if encrypted
   ```

4. **Restore from backup** (if available)

---

### Error: "Corrupted crypto config"

**Cause:** `crypto.json` damaged or modified

**Solution:**

```bash
# Backup corrupted config
mv ~/.souleyez/crypto.json ~/.souleyez/crypto.json.broken

# Initialize new config
python3 -c "
from souleyez.storage.crypto import get_crypto_manager
crypto = get_crypto_manager()
print('Config regenerated')
"

# Re-enable encryption (will need to re-encrypt credentials)
python3 migrate_credentials.py
```

**Note:** Old encrypted credentials cannot be decrypted with new salt!

---

## Security Best Practices

### Password Selection

**DO:**
- ✅ Use 12+ characters
- ✅ Mix uppercase, lowercase, numbers, symbols
- ✅ Use password manager to generate
- ✅ Make it memorable but unique

**DON'T:**
- ❌ Use dictionary words
- ❌ Reuse passwords from other services
- ❌ Write it on paper (unless securely stored)
- ❌ Share with anyone

**Examples:**

```
Good:    Tr0ut-F1sh!ng-B0at$42
Good:    MyD0g'sN@me&B1rthY3ar!99
Bad:     password123
Bad:     souleyez2024
```

### Key Management

**DO:**
- ✅ Store password in password manager (LastPass, 1Password, Bitwarden)
- ✅ Backup `crypto.json` to secure location
- ✅ Use unique password per souleyez instance
- ✅ Test recovery procedure regularly

**DON'T:**
- ❌ Store password in plaintext file
- ❌ Email password to yourself
- ❌ Save password in browser
- ❌ Share password via chat/IM

### Operational Security

**DO:**
- ✅ Lock screen when away
- ✅ Log out of souleyez when done
- ✅ Enable disk encryption (LUKS/FileVault)
- ✅ Regular security updates

**DON'T:**
- ❌ Run souleyez on shared/public computers
- ❌ Leave terminal unlocked
- ❌ Store database on unencrypted USB drives
- ❌ Copy database to cloud storage (unless encrypted)

---

## Implementation Details

### Key Derivation Function

**Algorithm:** PBKDF2-HMAC-SHA256

**Code:**
```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=self._salt,
    iterations=480000,
    backend=default_backend()
)

key = kdf.derive(password.encode('utf-8'))
```

**Why 480,000 iterations?**
- OWASP 2023 recommendation
- Balances security and performance
- ~200ms on modern hardware
- Makes brute-force attacks expensive

---

### Encryption Algorithm

**Algorithm:** Fernet (AES-128-CBC + HMAC-SHA256)

**Code:**
```python
from cryptography.fernet import Fernet
import base64

# Create Fernet instance
key = base64.urlsafe_b64encode(derived_key)
fernet = Fernet(key)

# Encrypt
plaintext = "admin"
ciphertext = fernet.encrypt(plaintext.encode('utf-8'))

# Decrypt
decrypted = fernet.decrypt(ciphertext).decode('utf-8')
```

**Fernet Format:**
```
Version (1 byte) | Timestamp (8 bytes) | IV (16 bytes) | Ciphertext (variable) | HMAC (32 bytes)
```

---

## Compliance and Standards

**Follows:**
- ✅ OWASP Password Storage Cheat Sheet (2023)
- ✅ NIST SP 800-132 (PBKDF2 recommendations)
- ✅ NIST SP 800-38A (AES-CBC mode)
- ✅ FIPS 197 (AES standard)
- ✅ RFC 2104 (HMAC specification)

---

## FAQ

**Q: Can I use the same password on multiple systems?**  
A: Yes, but not recommended. Each system should have unique password.

**Q: What happens if I forget my password?**  
A: Encrypted credentials are permanently lost. No recovery possible.

**Q: Can I decrypt without the password?**  
A: No. That's the whole point of encryption!

**Q: Is encryption enabled by default?**  
A: No. You must explicitly enable it with `migrate_credentials.py`.

**Q: Can someone crack my password?**  
A: With a strong password (12+ chars), cracking is computationally infeasible.

**Q: What if my system is compromised?**  
A: Attacker may extract key from memory. Encryption protects at-rest data only.

**Q: Can I automate password entry?**  
A: Not recommended. Defeats purpose of password protection.

---

## See Also

- [Threat Model](threat-model.md)
- [Security Best Practices](best-practices.md)
- [Secure Defaults](secure-defaults.md)
- [SECURITY.md](../../SECURITY.md)
