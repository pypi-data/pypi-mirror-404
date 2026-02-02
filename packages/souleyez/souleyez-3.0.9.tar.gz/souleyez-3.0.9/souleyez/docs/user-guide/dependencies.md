# Dependencies and Version Requirements

## Overview

This document details all dependencies required to run souleyez, including version requirements and compatibility notes.

## Python Version Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **Tested on**: Python 3.13.7
- **Recommended**: Python 3.10+

### Version Compatibility

| Python Version | Status | Notes |
|---------------|--------|-------|
| 3.13.x | ✅ Tested | Fully supported |
| 3.12.x | ✅ Compatible | Recommended |
| 3.11.x | ✅ Compatible | Recommended |
| 3.10.x | ✅ Compatible | Minimum recommended |
| 3.9.x | ⚠️ Compatible | Limited testing |
| 3.8.x | ⚠️ Compatible | Minimum supported version |
| 3.7.x | ❌ Not Supported | EOL |

## Python Dependencies

### Core Dependencies

Defined in `requirements.txt`:

#### click >= 8.0.0
- **Purpose**: CLI framework for command-line interface
- **License**: BSD-3-Clause
- **Why we use it**: Provides decorator-based CLI with automatic help generation

#### psutil >= 5.9.0
- **Purpose**: Process and system monitoring
- **License**: BSD-3-Clause
- **Why we use it**: Worker process management, system resource monitoring

#### wcwidth >= 0.2.0
- **Purpose**: Terminal width calculations for proper text rendering
- **License**: MIT
- **Why we use it**: Dashboard UI formatting and alignment

#### rich >= 13.0.0
- **Purpose**: Enhanced terminal output and formatting
- **License**: MIT
- **Why we use it**: Beautiful console output, tables, progress bars

#### ollama >= 0.1.0
- **Purpose**: AI model integration
- **License**: MIT
- **Why we use it**: Local LLM support for AI-powered features

#### python-json-logger >= 2.0.0
- **Purpose**: Structured JSON logging
- **License**: BSD
- **Why we use it**: Machine-readable log output, better log analysis

#### defusedxml >= 0.7.0
- **Purpose**: Secure XML parsing
- **License**: PSF
- **Why we use it**: Safe parsing of tool outputs (Nmap XML, etc.)

### Cryptography Dependencies

For credential encryption (required):

#### cryptography >= 41.0.0
- **Purpose**: Fernet symmetric encryption (AES-128)
- **License**: Apache-2.0 / BSD
- **Why we use it**: Secure credential storage
- **Installation**: Automatic when running `migrate_credentials.py`

### Build Dependencies

Required for installation:

- **setuptools >= 61**: Python package building
- **wheel**: Binary package format
- **pip >= 21.0**: Package installer

## System Dependencies

### Operating System

**Supported**:
- Kali Linux (all versions)
- Debian 10+ (Buster and newer)
- Ubuntu 20.04+ (Focal and newer)
- ParrotOS Security Edition
- BlackArch Linux

**Partially Supported**:
- Other Debian-based distributions (may require adjustments)
- RedHat-based systems (untested, YMMV)

### System Packages

Required system packages:

```bash
# Core requirements
python3          # Python interpreter
python3-pip      # Python package installer
python3-venv     # Virtual environment support (optional but recommended)
git              # Version control

# Optional but recommended
sqlite3          # Database CLI tool for manual inspection
```

## External Security Tools

SoulEyez orchestrates these tools. Install as needed:

### Network Scanners

#### nmap
- **Version**: Any recent version
- **Tested with**: 7.80+
- **Installation**: `sudo apt install -y nmap`
- **Purpose**: Port scanning, service detection, OS fingerprinting

### Web Scanners

#### nikto
- **Version**: 2.1.6+
- **Installation**: `sudo apt install -y nikto`
- **Purpose**: Web vulnerability scanning

#### gobuster
- **Version**: 3.0+
- **Installation**: `sudo apt install -y gobuster`
- **Purpose**: Directory/file brute-forcing

#### dirb
- **Version**: 2.22+
- **Installation**: `sudo apt install -y dirb`
- **Purpose**: Web content scanning

### SMB/Windows Tools

#### enum4linux
- **Version**: 0.8.9+
- **Installation**: `sudo apt install -y enum4linux`
- **Purpose**: Windows/Samba enumeration

#### smbmap
- **Version**: Latest
- **Installation**: `sudo apt install -y smbmap`
- **Purpose**: SMB share enumeration

#### smbclient
- **Version**: 4.0+
- **Installation**: `sudo apt install -y smbclient`
- **Purpose**: SMB client operations

### Database Testing

#### sqlmap
- **Version**: 1.4+
- **Installation**: `sudo apt install -y sqlmap`
- **Purpose**: SQL injection detection and exploitation

### OSINT

#### theharvester
- **Version**: 3.0+
- **Installation**: `sudo apt install -y theharvester`
- **Purpose**: Email, subdomain, and host reconnaissance

### Exploitation

#### metasploit-framework
- **Version**: 6.0+
- **Installation**: `sudo apt install -y metasploit-framework`
- **Purpose**: Exploitation framework integration

## Version Checking

### Check Python Dependencies

```bash
# List installed packages
pip list

# Check specific package
pip show click

# Verify all requirements
pip check
```

### Check External Tools

```bash
# Check tool availability
which nmap nikto gobuster sqlmap

# Check versions
nmap --version
nikto -Version
sqlmap --version
```

### System Requirements Check Script

TODO: Add automated dependency checker script

```bash
# Future feature
souleyez doctor
```

## Dependency Installation

### All Python Dependencies

```bash
# From requirements.txt
pip install -r requirements.txt

# Or via setup
pip install -e .
```

### All Security Tools (Kali/Debian)

```bash
sudo apt update
sudo apt install -y \
    nmap \
    nikto \
    gobuster \
    dirb \
    enum4linux \
    smbmap \
    smbclient \
    sqlmap \
    theharvester \
    metasploit-framework
```

## Compatibility Notes

### SQLite Version
- **Minimum**: 3.31.0+
- **Recommended**: 3.35.0+
- Ships with Python, no separate installation needed

### Terminal Requirements
- **UTF-8 support**: Required for dashboard UI
- **Color support**: Recommended but not required
- **Minimum width**: 80 columns recommended

### Network Requirements
- No internet connection required for local operations
- Internet needed for:
  - Tool updates (`apt update`)
  - OSINT modules (theharvester)
  - External target scanning

## Known Issues

### Debian/Ubuntu Python Package Conflicts

If using system Python packages alongside pip:
```bash
# Use virtual environment to avoid conflicts
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Kali Linux Rolling Updates

Kali's rolling updates may cause tool version changes:
```bash
# Pin specific versions if needed
sudo apt-mark hold nmap
```

### macOS Compatibility

Currently unsupported due to:
- System tool availability differences
- Path handling inconsistencies
- Testing limitations

**Status**: Experimental, use at own risk

### Windows Compatibility

Not supported. Use WSL2 (Windows Subsystem for Linux):
```bash
# In WSL2
sudo apt update
pip install souleyez
```

## Dependency Security

### Vulnerability Scanning

We recommend regular dependency audits:

```bash
# Check for known vulnerabilities
pip install safety
safety check

# Or use pip-audit
pip install pip-audit
pip-audit
```

### Update Policy

- **Security patches**: Applied immediately
- **Minor updates**: Monthly review
- **Major updates**: Tested before adoption

## Next Steps

- Continue with [Installation Guide](installation.md)
- Review [Troubleshooting](troubleshooting.md)
- Check [Getting Started](getting-started.md)

## Support

For dependency-related issues:
- **GitHub Issues**: https://github.com/y0d8/souleyez_app/issues
- **Label**: `dependencies`
