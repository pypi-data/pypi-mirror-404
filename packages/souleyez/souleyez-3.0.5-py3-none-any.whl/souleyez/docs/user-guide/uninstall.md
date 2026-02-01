# Uninstall Guide

This guide explains how to uninstall SoulEyez and what happens to your data.

## Quick Uninstall

### Keep Your Data (Recommended)

Uninstall SoulEyez but preserve all your engagements, credentials, and findings:

```bash
souleyez uninstall
```

**What gets removed:**
- ✅ Application code
- ✅ Python packages
- ✅ CLI commands

**What's preserved:**
- ✅ Database (`~/.souleyez/souleyez.db`)
- ✅ Encryption keys (`~/.souleyez/crypto.json`)
- ✅ Logs (`~/.souleyez/souleyez.log`)
- ✅ All engagements, hosts, findings, credentials
- ✅ Configuration (`~/.souleyez/config.json`)

**Why preserve data?**
- Upgrade to newer versions without losing work
- Switch between systems and keep your data
- Try different installation methods

**Reinstalling:**
```bash
pipx install souleyez
# or
pip install souleyez

# Your data is automatically available!
souleyez interactive
```

---

### Complete Removal (Delete Everything)

Remove SoulEyez **and ALL user data** permanently:

```bash
souleyez uninstall --purge-data
```

⚠️ **WARNING:** This cannot be undone!

**What gets removed:**
- ✅ Application code
- ✅ Python packages
- ✅ **Database with all engagements**
- ✅ **Encryption keys (credentials become unrecoverable)**
- ✅ **All logs**
- ✅ **Configuration files**

**When to use this:**
- Completely finished with a project
- Switching to a different tool
- Clean slate for a new environment
- No longer need any stored data

---

## Manual Uninstall

If the `souleyez uninstall` command is not available or fails:

### Option 1: Using pipx (Recommended)

```bash
# Stop background worker (both patterns)
pkill -f "souleyez worker"
pkill -f souleyez.engine.background

# Remove application
pipx uninstall souleyez

# (Optional) Remove data
rm -rf ~/.souleyez
```

### Option 2: Using pip

```bash
# Stop background worker (both patterns)
pkill -f "souleyez worker"
pkill -f souleyez.engine.background

# Remove application
pip uninstall souleyez

# (Optional) Remove data
rm -rf ~/.souleyez
```

---

## What's in ~/.souleyez?

Understanding your user data directory:

```
~/.souleyez/
├── souleyez.db         # SQLite database (all your data)
├── crypto.json        # Master encryption key
├── config.json        # Application settings
├── souleyez.log        # Application logs
├── artifacts/         # Scan output files
├── scans/             # Historical scan data
└── current_engagement # Active workspace marker
```

**Database contents:**
- Engagements and metadata
- Discovered hosts and services
- Findings and vulnerabilities
- Credentials (encrypted)
- Job history and results
- Audit logs

**Size:** Typically 1-500 MB depending on usage

---

## Data Portability

### Backup Before Uninstall

```bash
# Backup everything
tar -czf souleyez-backup-$(date +%Y%m%d).tar.gz ~/.souleyez

# Backup just the database
cp ~/.souleyez/souleyez.db ~/souleyez-backup.db
```

### Restore on Another System

```bash
# Install SoulEyez
pipx install souleyez

# Restore data
tar -xzf souleyez-backup-YYYYMMDD.tar.gz -C ~/

# Or just restore database
cp ~/souleyez-backup.db ~/.souleyez/souleyez.db

# Verify
souleyez interactive
```

---

## Troubleshooting

### Worker Won't Stop

```bash
# Find process ID
ps aux | grep souleyez | grep -E "worker|background"

# Force kill (both patterns)
pkill -9 -f "souleyez worker"
pkill -9 -f souleyez.engine.background
```

### Permission Denied

```bash
# Check ownership
ls -la ~/.souleyez

# Fix permissions
chmod 700 ~/.souleyez
chmod 600 ~/.souleyez/*
```

### Reinstall Not Working

```bash
# Complete clean slate
pipx uninstall souleyez
rm -rf ~/.souleyez
rm -rf ~/.local/share/pipx/venvs/souleyez

# Fresh install
pipx install souleyez
```

---

## FAQ

**Q: Will uninstalling remove my pentesting tool installations?**  
A: No. SoulEyez never modifies system tools (nmap, hydra, metasploit, etc.). Those remain installed.

**Q: Can I reinstall and get my data back?**  
A: Yes! If you didn't use `--purge-data`, all your engagements and data will be available after reinstalling.

**Q: What if I forgot my master password?**  
A: Unfortunately, encrypted credentials cannot be recovered without the master password. You'll need to re-extract them from target systems.

**Q: Can I move my data to another user?**  
A: Yes, copy `~/.souleyez` to the other user's home directory and ensure proper permissions (700 for directory, 600 for files).

**Q: How do I upgrade without uninstalling?**  
A: Use `pipx upgrade souleyez` or `pip install --upgrade souleyez`. Your data is never touched during upgrades.

---

## See Also

- [Installation Guide](installation.md)
- [Getting Started](getting-started.md)
- [Backup and Recovery](../security/backup-recovery.md)
- [Data Security](../security/credential-encryption.md)

---

**Last Updated:** 2025-11-04  
**Version:** 0.8.0-dev
