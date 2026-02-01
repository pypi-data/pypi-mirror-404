# Configuration Guide

## Overview

SoulEyez uses a flexible configuration system that supports:
- **JSON configuration file** at `~/.souleyez/config.json`
- **Environment variable overrides** for CI/CD and containers
- **Secure defaults** that prioritize security and privacy

## Table of Contents

1. [Configuration File Location](#configuration-file-location)
2. [Configuration Priority](#configuration-priority)
3. [Configuration Schema](#configuration-schema)
4. [Environment Variable Overrides](#environment-variable-overrides)
5. [Common Configuration Tasks](#common-configuration-tasks)
6. [Plugin Management](#plugin-management)
7. [Security Settings](#security-settings)
8. [Database Configuration](#database-configuration)
9. [Logging Configuration](#logging-configuration)
10. [Troubleshooting](#troubleshooting)

---

## Configuration File Location

**Default:** `~/.souleyez/config.json`

The configuration file is automatically created on first run with secure defaults.

### Permissions

The config file is created with `0o600` (read/write for owner only) to protect sensitive settings.

```bash
ls -la ~/.souleyez/config.json
# -rw------- 1 user user 1234 Nov 18 08:00 config.json
```

---

## Configuration Priority

Settings are applied in this order (highest to lowest):

1. **Environment Variables** (`SOULEYEZ_*`)
2. **Config File** (`~/.souleyez/config.json`)
3. **Default Values** (hardcoded in `souleyez/config.py`)

### Example

```bash
# Config file says: database.path = ~/.souleyez/souleyez.db
# Environment says:
export SOULEYEZ_DATABASE_PATH=/tmp/test.db

# Result: Uses /tmp/test.db (environment wins)
```

---

## Configuration Schema

### Default Configuration

The default `~/.souleyez/config.json` looks like this:

```json
{
  "plugins": {
    "enabled": [],
    "disabled": []
  },
  "settings": {
    "wordlists": null,
    "proxy": null,
    "threads": 10
  },
  "database": {
    "path": "~/.souleyez/souleyez.db",
    "backup_enabled": true,
    "backup_interval_hours": 24
  },
  "crypto": {
    "algorithm": "AES-256-GCM",
    "iterations": 600000,
    "key_derivation": "PBKDF2"
  },
  "logging": {
    "level": "INFO",
    "format": "json",
    "file": "~/.souleyez/souleyez.log",
    "max_bytes": 10485760,
    "backup_count": 5
  },
  "security": {
    "session_timeout_minutes": 30,
    "max_login_attempts": 5,
    "lockout_duration_minutes": 15,
    "min_password_length": 12
  },
  "ai": {
    "provider": "ollama",
    "claude_api_key": null,
    "claude_model": "claude-sonnet-4-20250514",
    "ollama_model": "llama3.1:8b"
  }
}
```

### Configuration Sections

#### 1. Plugins

Controls which tools/plugins are enabled or disabled.

```json
{
  "plugins": {
    "enabled": ["nmap", "nikto", "gobuster"],
    "disabled": ["metasploit"]
  }
}
```

#### 2. Settings

General application settings.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `wordlists` | string/null | `null` | Default wordlist path for fuzzing |
| `proxy` | string/null | `null` | HTTP proxy (e.g., `http://127.0.0.1:8080`) |
| `threads` | integer | `10` | Max concurrent threads (1-100) |

#### 3. Database

Database configuration and backup settings.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `path` | string | `~/.souleyez/souleyez.db` | SQLite database file path |
| `backup_enabled` | boolean | `true` | Enable automatic backups |
| `backup_interval_hours` | integer | `24` | Backup frequency in hours |

#### 4. Crypto

Encryption settings for credential vault.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `algorithm` | string | `AES-256-GCM` | Encryption algorithm |
| `iterations` | integer | `600000` | PBKDF2 iterations (100k-10M) |
| `key_derivation` | string | `PBKDF2` | Key derivation function |

**Security Note:** Higher iterations = slower but more secure. 600,000 is OWASP recommended minimum.

#### 5. Logging

Log file configuration.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `level` | string | `INFO` | Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL) |
| `format` | string | `json` | Log format |
| `file` | string | `~/.souleyez/souleyez.log` | Log file path |
| `max_bytes` | integer | `10485760` | Max log file size (10MB) |
| `backup_count` | integer | `5` | Number of rotated log files to keep |

#### 6. Security

Authentication and session security settings.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `session_timeout_minutes` | integer | `30` | Auto-logout after inactivity (5-1440) |
| `max_login_attempts` | integer | `5` | Failed login attempts before lockout (1-10) |
| `lockout_duration_minutes` | integer | `15` | Account lockout duration |
| `min_password_length` | integer | `12` | Minimum master password length |

#### 7. AI

AI provider configuration for recommendations and reports.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `provider` | string | `ollama` | Active AI provider (`ollama` or `claude`) |
| `claude_api_key` | string | `null` | Claude API key (encrypted) |
| `claude_model` | string | `claude-sonnet-4-20250514` | Claude model to use |
| `ollama_url` | string | `http://localhost:11434` | Ollama API endpoint (local network IPs only) |
| `ollama_model` | string | `llama3.1:8b` | Ollama model to use |
| `max_tokens` | integer | `4096` | Maximum response tokens |
| `temperature` | float | `0.3` | Response creativity (0.0-1.0) |

```json
{
  "ai": {
    "provider": "ollama",
    "claude_api_key": null,
    "claude_model": "claude-sonnet-4-20250514",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llama3.1:8b",
    "max_tokens": 4096,
    "temperature": 0.3
  }
}
```

**Privacy Note:** When using Claude, engagement data is sent to Anthropic's API. Use Ollama for sensitive engagements.

---

## Environment Variable Overrides

All configuration values can be overridden using environment variables.

### Naming Convention

`SOULEYEZ_<SECTION>_<KEY>`

- Uppercase
- Dots replaced with underscores
- Prefix: `SOULEYEZ_`

### Examples

```bash
# Database path
export SOULEYEZ_DATABASE_PATH=/tmp/test.db

# Crypto iterations
export SOULEYEZ_CRYPTO_ITERATIONS=1000000

# Logging level
export SOULEYEZ_LOGGING_LEVEL=DEBUG

# Logging file
export SOULEYEZ_LOGGING_FILE=/var/log/souleyez.log

# Session timeout
export SOULEYEZ_SECURITY_SESSION_TIMEOUT_MINUTES=60
```

### Use Cases

**Testing:**
```bash
export SOULEYEZ_DATABASE_PATH=/tmp/test.db
souleyez engagement create "Test"
```

**CI/CD:**
```bash
export SOULEYEZ_LOGGING_LEVEL=ERROR
export SOULEYEZ_DATABASE_PATH=/tmp/ci_test.db
pytest tests/
```

**Docker:**
```dockerfile
ENV SOULEYEZ_DATABASE_PATH=/data/souleyez.db
ENV SOULEYEZ_LOGGING_FILE=/var/log/souleyez.log
```

---

## Common Configuration Tasks

### Change Database Location

**Method 1: Config File**
```bash
# Edit ~/.souleyez/config.json
{
  "database": {
    "path": "/mnt/secure/souleyez.db"
  }
}
```

**Method 2: Environment Variable**
```bash
export SOULEYEZ_DATABASE_PATH=/mnt/secure/souleyez.db
```

### Set Proxy for All Tools

```bash
# Edit ~/.souleyez/config.json
{
  "settings": {
    "proxy": "http://127.0.0.1:8080"
  }
}
```

### Increase Thread Count

```bash
# Edit ~/.souleyez/config.json
{
  "settings": {
    "threads": 20
  }
}
```

**Note:** More threads = faster but more resource intensive.

### Change Session Timeout

For sensitive environments, reduce timeout:

```bash
{
  "security": {
    "session_timeout_minutes": 15
  }
}
```

For development, increase timeout:

```bash
{
  "security": {
    "session_timeout_minutes": 120
  }
}
```

### Enable Debug Logging

**Temporary (environment variable):**
```bash
export SOULEYEZ_LOGGING_LEVEL=DEBUG
souleyez dashboard
```

**Permanent (config file):**
```json
{
  "logging": {
    "level": "DEBUG"
  }
}
```

### Disable Database Backups

```json
{
  "database": {
    "backup_enabled": false
  }
}
```

---

## Plugin Management

### List All Plugins

```bash
souleyez plugins
```

### Enable a Plugin

**CLI:**
```bash
souleyez plugins enable nmap
```

**Programmatically:**
```python
from souleyez.config import enable_plugin
enable_plugin('nmap')
```

**Config File:**
```json
{
  "plugins": {
    "enabled": ["nmap", "nikto", "gobuster"]
  }
}
```

### Disable a Plugin

**CLI:**
```bash
souleyez plugins disable metasploit
```

**Config File:**
```json
{
  "plugins": {
    "disabled": ["metasploit"]
  }
}
```

### Reset Plugin Configuration

```bash
# Removes all enabled/disabled settings
# (All plugins become available based on installation)
```

**Programmatically:**
```python
from souleyez.config import reset_plugins
reset_plugins()
```

---

## Security Settings

### Strengthen Encryption

For highly sensitive data, increase PBKDF2 iterations:

```json
{
  "crypto": {
    "iterations": 1000000
  }
}
```

**Warning:** Higher values slow down login and credential access.

### Enforce Stronger Passwords

```json
{
  "security": {
    "min_password_length": 16
  }
}
```

### Reduce Login Attempts

For high-security environments:

```json
{
  "security": {
    "max_login_attempts": 3,
    "lockout_duration_minutes": 30
  }
}
```

---

## Database Configuration

### Multiple Engagements/Projects

Create separate databases per project:

```bash
# Project 1
export SOULEYEZ_DATABASE_PATH=~/projects/client1/souleyez.db
souleyez engagement create "Client 1 Internal"

# Project 2
export SOULEYEZ_DATABASE_PATH=~/projects/client2/souleyez.db
souleyez engagement create "Client 2 External"
```

### Network Storage

Store database on network drive:

```json
{
  "database": {
    "path": "/mnt/nfs/pentests/souleyez.db"
  }
}
```

**Security Warning:** Ensure network storage is encrypted and access-controlled.

### Backup Configuration

```json
{
  "database": {
    "backup_enabled": true,
    "backup_interval_hours": 6
  }
}
```

Backups are stored at: `<database_path>.backup-<timestamp>`

---

## Logging Configuration

### Reduce Log Verbosity

For production:

```json
{
  "logging": {
    "level": "WARNING"
  }
}
```

### Increase Log Retention

Keep more log files:

```json
{
  "logging": {
    "backup_count": 10
  }
}
```

### Change Log Format

Currently only JSON format is supported. Future versions may support:
- Plain text
- Structured logging
- Syslog

### Centralized Logging

Send logs to central server:

```bash
# Forward logs to remote syslog
tail -f ~/.souleyez/souleyez.log | nc syslog-server 514
```

---

## Troubleshooting

### Config File Not Found

**Solution:** SoulEyez auto-creates config on first run.

```bash
souleyez --version
# Creates ~/.souleyez/config.json with defaults
```

### Invalid Configuration

**Error:** `Invalid config file: crypto.iterations: Iterations must be between 100k and 10M`

**Solution:** Fix invalid values in config file:
```bash
# View current config
cat ~/.souleyez/config.json

# Reset to defaults
rm ~/.souleyez/config.json
souleyez --version
```

### Environment Variables Not Working

**Check:** Variable name follows convention:

```bash
# ❌ Wrong
export DATABASE_PATH=/tmp/test.db

# ✅ Correct
export SOULEYEZ_DATABASE_PATH=/tmp/test.db
```

**Verify:**
```bash
env | grep SOULEYEZ
```

### Config Changes Not Applied

**Reason:** Environment variables override config file.

**Solution:**
```bash
# Unset environment variables
unset SOULEYEZ_DATABASE_PATH
unset SOULEYEZ_LOGGING_LEVEL

# Verify
env | grep SOULEYEZ
```

### Permission Denied on Config File

**Error:** `Permission denied: ~/.souleyez/config.json`

**Solution:**
```bash
chmod 600 ~/.souleyez/config.json
```

### Corrupted Config File

**Error:** `Corrupted config file: Expecting value: line 5 column 1`

**Solution:**
```bash
# Backup corrupted file
mv ~/.souleyez/config.json ~/.souleyez/config.json.bad

# Recreate with defaults
souleyez --version

# Manually restore your settings
```

---

## Advanced Configuration

### Programmatic Access

```python
from souleyez.config import get, read_config, write_config

# Read a single value
db_path = get('database.path')
threads = get('settings.threads', default=10)

# Read entire config
config = read_config()

# Modify and save
config['settings']['threads'] = 20
write_config(config)
```

### Config Validation

All configs are validated against a schema:

```python
from souleyez.config import validate_config

config = read_config()
is_valid, errors = validate_config(config)

if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

### Legacy Config Migration

Old flat-format configs are automatically normalized:

**Old format:**
```json
{
  "enabled": ["nmap"],
  "disabled": []
}
```

**Auto-converted to:**
```json
{
  "plugins": {
    "enabled": ["nmap"],
    "disabled": []
  },
  "settings": { ... }
}
```

---

## Best Practices

### Security

1. **Never commit config files** - Add `~/.souleyez/` to `.gitignore`
2. **Use environment variables in CI/CD** - Don't hardcode secrets
3. **Restrict file permissions** - Keep config at `0o600`
4. **Regular backups** - Enable database backups
5. **Strong encryption** - Use high iteration counts (600k+)

### Organization

1. **Separate databases per project** - Use different database paths
2. **Document custom settings** - Add comments (future JSON5 support)
3. **Version control schemas** - Track config structure changes
4. **Test config changes** - Use temporary environment variables first

### Performance

1. **Adjust threads based on hardware** - More CPU cores = more threads
2. **Monitor log file size** - Reduce log level in production
3. **Disable unused plugins** - Faster startup and less memory

---

## Related Documentation

- [Security & Encryption Guide](security/credential-encryption.md) - Credential protection
- [Worker Management Guide](user-guide/worker-management.md) - Job configuration
- [Troubleshooting Guide](user-guide/troubleshooting.md) - Common issues
- [Installation Guide](user-guide/installation.md) - Initial setup

---

## Configuration Reference Quick Sheet

```bash
# Config file location
~/.souleyez/config.json

# Environment variable format
SOULEYEZ_<SECTION>_<KEY>

# Common overrides
export SOULEYEZ_DATABASE_PATH=/path/to/db
export SOULEYEZ_LOGGING_LEVEL=DEBUG
export SOULEYEZ_SECURITY_SESSION_TIMEOUT_MINUTES=60

# Plugin management
souleyez plugins enable <name>
souleyez plugins disable <name>

# Reset config to defaults
rm ~/.souleyez/config.json && souleyez --version
```

---

**Last Updated:** 2026-01-11 | **Version:** 2.43.1
