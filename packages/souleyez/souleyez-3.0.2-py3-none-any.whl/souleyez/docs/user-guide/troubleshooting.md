# Troubleshooting Guide

## Overview

This guide covers common issues and their solutions. Issues are organized by category for quick reference.

---

## Installation Issues

### "command not found: souleyez"

**Symptoms**: The `souleyez` command is not recognized after installation.

**Common Causes**:
1. Installation didn't complete successfully
2. Virtual environment not activated (if using source install)
3. PATH not updated

**Solutions**:

```bash
# Solution 1: Verify installation
pip show souleyez

# Solution 2: Activate virtual environment (if using source install)
source venv/bin/activate

# Solution 3: Reinstall
pip install souleyez

# Solution 4: Check if installed
which souleyez
```

### "Import error" on startup

**Symptoms**: 
```
Import error: No module named 'click'
ImportError: cannot import name 'EngagementManager'
```

**Cause**: Missing dependencies or broken installation.

**Solution**:
```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# If still failing, clean install:
pip uninstall souleyez
rm -rf souleyez.egg-info
pip install -e .
```

### Permission denied during installation

**Symptoms**: `Permission denied` errors during installation.

**Solution**:
```bash
# Use pip with --user flag
pip install --user souleyez

# Or create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install souleyez
```

---

## Database Issues

### "database is locked"

**Symptoms**: 
```
sqlite3.OperationalError: database is locked
```

**Cause**: Multiple processes accessing database simultaneously.

**Solution**:
```bash
# Check for running souleyez processes
ps aux | grep souleyez

# Kill all souleyez processes
pkill -f souleyez

# Restart and try again
souleyez dashboard
```

### Database corruption

**Symptoms**: Crashes, SQL errors, data inconsistencies.

**Solution**:
```bash
# Step 1: Backup current database
cp ~/.souleyez/souleyez.db ~/.souleyez/souleyez.db.corrupt-$(date +%Y%m%d)

# Step 2: Try SQLite integrity check
sqlite3 ~/.souleyez/souleyez.db "PRAGMA integrity_check;"

# Step 3: If corrupted, export and rebuild
sqlite3 ~/.souleyez/souleyez.db .dump > backup.sql
rm ~/.souleyez/souleyez.db
sqlite3 ~/.souleyez/souleyez.db < backup.sql

# Step 4: If beyond repair, start fresh
mv ~/.souleyez/souleyez.db ~/.souleyez/souleyez.db.old
souleyez interactive  # Creates new DB
```

### Cannot find database file

**Symptoms**: 
```
Error: database file not found
```

**Solution**:
```bash
# Create user data directory if missing
mkdir -p ~/.souleyez

# Initialize database by running any command
souleyez engagement list

# Verify database exists
ls -la ~/.souleyez/souleyez.db
```

---

## Engagement Issues

### "No active engagement"

**Symptoms**: Commands fail with "No active engagement set"

**Cause**: No engagement selected as current workspace.

**Solution**:
```bash
# List available engagements
souleyez engagement list

# If none exist, create one
souleyez engagement create "My Engagement"

# Set as active
souleyez engagement use "My Engagement"
```

### Cannot switch engagements

**Symptoms**: `engagement use` command fails or doesn't switch.

**Solution**:
```bash
# Verify engagement exists (exact name match required)
souleyez engagement list

# Use exact name with quotes if contains spaces
souleyez engagement use "Client ABC Pentest"

# Check active engagement
souleyez engagement list
# Look for the asterisk (*) marker
```

---

## Job Execution Issues

### Jobs not starting

**Symptoms**: Jobs stay in "queued" status indefinitely.

**Cause**: Background worker not running.

**Solution**:
```bash
# Check worker status
souleyez worker status

# Start worker if not running
souleyez worker start

# Verify worker is running
ps aux | grep worker_loop
```

### Job fails immediately

**Symptoms**: Job shows "failed" status right after creation.

**Possible Causes & Solutions**:

#### Cause 1: Tool not installed
```bash
# Check if tool exists
which nmap nikto gobuster

# Install missing tool
sudo apt install -y nmap
```

#### Cause 2: Invalid arguments
```bash
# View job output to see error
souleyez jobs get <job_id> --output

# Check tool syntax
nmap --help
```

#### Cause 3: Permission issues
```bash
# Some tools need root
sudo souleyez jobs enqueue nmap 192.168.1.0/24 -a "-sS"

# Or configure sudoers (advanced)
```

### Job output is empty

**Symptoms**: Job completes but no results stored.

**Cause**: Parser not recognizing tool output format.

**Solution**:
```bash
# Check raw job log (location may vary)
cat ~/.souleyez/artifacts/<job_id>.log

# If log is empty, tool didn't produce output
# If log has data but not parsed, parser may need updating

# Manually add findings if needed
souleyez findings add "<title>" --severity <level> --host <ip>
```

### Cannot view job logs

**Symptoms**: `jobs get --output` shows nothing or errors.

**Solution**:
```bash
# Check if log file exists
ls -la ~/.souleyez/artifacts/

# View log directly
cat ~/.souleyez/artifacts/<job_id>.log

# If missing, job may not have run yet
souleyez jobs get <job_id>  # Check status
```

---

## Worker Issues

### Worker keeps dying

**Symptoms**: Worker starts but stops after a few seconds.

**Solution**:
```bash
# Check worker logs
tail -f ~/.souleyez/souleyez.log

# Look for error messages
# Common issues: import errors, permission problems, database locks

# Kill all workers and restart fresh
pkill -f worker_loop
souleyez worker start
```

### Multiple workers running

**Symptoms**: Duplicate job execution, weird behavior.

**Solution**:
```bash
# Check for multiple workers
ps aux | grep worker_loop

# Kill all workers
pkill -f worker_loop

# Wait a few seconds
sleep 3

# Start single worker
souleyez worker start
```

---

## Dashboard Issues

### Dashboard not updating

**Symptoms**: Dashboard shows old data, doesn't refresh.

**Solution**:
```bash
# Press 'q' to exit and restart
souleyez dashboard

# Adjust refresh interval
souleyez dashboard -r 3  # 3 second refresh

# Check if worker is running (dashboard shows worker status)
souleyez worker status
```

### Dashboard rendering issues

**Symptoms**: Garbled text, weird characters, misaligned columns.

**Cause**: Terminal encoding or size issues.

**Solution**:
```bash
# Ensure UTF-8 encoding
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Resize terminal to minimum 80 columns
# Or maximize terminal window

# Use simpler terminal if issues persist
TERM=xterm souleyez dashboard
```

### Hotkeys not working

**Symptoms**: Pressing 'h', 't', 'm', etc. doesn't respond.

**Cause**: Terminal input handling issues.

**Solution**:
```bash
# Restart dashboard
# Exit with 'q' and relaunch

# Try different terminal emulator
# Some terminals (like older 'screen') have limitations

# Update terminal settings
stty sane
```

---

## Tool Integration Issues

### "Tool not found" errors

**Symptoms**: 
```
Error: nmap not found in PATH
```

**Solution**:
```bash
# Install the tool
sudo apt install -y nmap

# Verify installation
which nmap
nmap --version

# If installed but still not found, check PATH
echo $PATH
```

### Tool runs but produces no results

**Symptoms**: Job completes successfully but no hosts/findings added.

**Cause**: Parser doesn't recognize output format or tool version mismatch.

**Solution**:
```bash
# Check tool version
nmap --version

# Check raw output
souleyez jobs get <job_id> --output

# If output looks good but not parsed:
# - Report issue on GitHub
# - Manually add findings from raw output
```

### nmap requires root privileges

**Symptoms**: 
```
You requested a scan type which requires root privileges.
```

**Solution**:
```bash
# Option 1: Run with sudo
sudo souleyez jobs enqueue nmap 192.168.1.0/24 -a "-sS"

# Option 2: Use unprivileged scan types
souleyez jobs enqueue nmap 192.168.1.0/24 -a "-sT"  # TCP connect

# Option 3: Configure sudoers (advanced)
# Add to /etc/sudoers:
# yourusername ALL=(ALL) NOPASSWD: /usr/bin/nmap
```

---

## Credential Management Issues

### Cannot decrypt credentials

**Symptoms**: 
```
Error: Invalid password or corrupted data
```

**Cause**: Wrong master password or encryption key mismatch.

**Solution**:
```bash
# Verify you're using correct password
souleyez creds list
# Enter password carefully

# If password is truly lost, credentials cannot be recovered
# This is by design for security

# You can reset encryption (loses all existing encrypted creds)
# Backup first!
cp ~/.souleyez/souleyez.db ~/.souleyez/souleyez.db.backup
python3 migrate_credentials.py --reset
```

### Credentials not showing

**Symptoms**: `creds list` shows nothing despite discoveries.

**Cause**: Parser didn't extract credentials or wrong engagement active.

**Solution**:
```bash
# Verify correct engagement
souleyez engagement list

# Check if credentials exist in database
sqlite3 ~/.souleyez/souleyez.db "SELECT * FROM credentials;"

# Manually add if needed
souleyez creds add <username> <password> --host <ip>
```

---

## Performance Issues

### Slow dashboard refresh

**Symptoms**: Dashboard takes long time to update.

**Cause**: Large database, many jobs, complex queries.

**Solution**:
```bash
# Increase refresh interval
souleyez dashboard -r 10  # 10 seconds

# Archive old engagements
# TODO: Need archive feature

# Vacuum database to reclaim space
sqlite3 ~/.souleyez/souleyez.db "VACUUM;"
```

### High CPU usage

**Symptoms**: souleyez using significant CPU.

**Cause**: Worker running resource-intensive tools.

**Solution**:
```bash
# Check what's running
souleyez jobs list --status running

# Limit concurrent jobs (not yet implemented)
# For now, queue jobs sequentially
```

---

## Network/Connectivity Issues

### Cannot reach target hosts

**Symptoms**: All scans fail with network errors.

**Solution**:
```bash
# Verify network connectivity
ping <target>

# Check if target is filtering
nmap -Pn <target>

# Verify you're on correct network
ip addr show
route -n
```

### Firewall blocking scans

**Symptoms**: Scans timeout or return no results.

**Solution**:
```bash
# Check local firewall
sudo iptables -L

# Adjust scan timing to avoid detection
souleyez jobs enqueue nmap <target> -a "-T2"  # Slower, stealthier

# Use different scan techniques
souleyez jobs enqueue nmap <target> -a "-sT -Pn"
```

---

## Reporting Issues

### Report generation fails

**Symptoms**: `report generate` command errors.

**Cause**: Missing data, template issues, or permission problems.

**Solution**:
```bash
# Verify engagement has data
souleyez hosts list
souleyez findings list

# Check reports directory exists and is writable
mkdir -p reports
chmod 755 reports

# Try generating again
souleyez report generate "Test Report"

# Check report output
ls -la reports/
```

---

## Advanced Troubleshooting

### Enable debug logging

```bash
# Set environment variable
export SOULEYEZ_DEBUG=1

# Run command
souleyez dashboard

# Check logs
tail -f ~/.souleyez/souleyez.log
```

### Manual database inspection

```bash
# Open database
sqlite3 ~/.souleyez/souleyez.db

# List tables
.tables

# View schema
.schema engagements

# Query data
SELECT * FROM engagements;
SELECT * FROM hosts LIMIT 10;

# Exit
.quit
```

### Check file permissions

```bash
# Verify user data directory
ls -la ~/.souleyez/

# Fix permissions if needed
chmod -R 755 ~/.souleyez/
chmod 644 ~/.souleyez/souleyez.db
```

### Clean slate (nuclear option)

If all else fails, start fresh:

```bash
# Backup everything first!
cp -r ~/.souleyez ~/.souleyez.backup.$(date +%Y%m%d)

# Remove all data
rm -rf ~/.souleyez/

# Reinstall
pip uninstall souleyez
rm -rf souleyez.egg-info
pip install -e .

# Initialize fresh
souleyez engagement create "Test"
```

---

## Getting Help

If this guide doesn't solve your issue:

### Before Asking for Help

Gather this information:
```bash
# System info
uname -a
python3 --version

# Installation details
pip show souleyez
pip list

# Error messages
# Copy full error output

# What you tried
# List troubleshooting steps already attempted
```

### Where to Get Help

1. **GitHub Issues**: https://github.com/y0d8/souleyez_app/issues
   - Search existing issues first
   - Include gathered information above
   - Label appropriately (bug, question, etc.)

2. **Documentation**: 
   - [Installation Guide](installation.md)
   - [Getting Started](getting-started.md)
   - [Security Guide](../security/best-practices.md)

3. **Built-in Help**:
   ```bash
   souleyez --help
   souleyez <command> --help
   ```

---

## Common Error Messages Reference

| Error Message | Likely Cause | Quick Fix |
|--------------|--------------|-----------|
| `No active engagement` | No engagement selected | `souleyez engagement use <name>` |
| `database is locked` | Multiple processes | `pkill -f souleyez` |
| `Tool not found` | Missing security tool | `sudo apt install <tool>` |
| `Permission denied` | Need root privileges | Run with `sudo` |
| `Worker not running` | Background worker stopped | `souleyez worker start` |
| `Import error` | Missing dependencies | `pip install -e .` |
| `Invalid password` | Wrong encryption password | Re-enter correct password |

---

## Prevention Tips

### Regular Maintenance

```bash
# Weekly: Check worker status
souleyez worker status

# Monthly: Backup database
cp ~/.souleyez/souleyez.db ~/backups/souleyez-$(date +%Y%m%d).db

# Monthly: Vacuum database
sqlite3 ~/.souleyez/souleyez.db "VACUUM;"

# After updates: Restart worker
pkill -f worker_loop
souleyez worker start
```

### Best Practices

1. **One engagement at a time**: Reduces confusion
2. **Use meaningful names**: Makes troubleshooting easier
3. **Monitor dashboard**: Catch issues early
4. **Check logs regularly**: `tail -f ~/.souleyez/souleyez.log`
5. **Keep tools updated**: `sudo apt update && sudo apt upgrade`

---

## Still Stuck?

Open a detailed issue: https://github.com/y0d8/souleyez_app/issues/new

Include:
- Operating system and version
- Python version
- Full error message
- Steps to reproduce
- What you've already tried
