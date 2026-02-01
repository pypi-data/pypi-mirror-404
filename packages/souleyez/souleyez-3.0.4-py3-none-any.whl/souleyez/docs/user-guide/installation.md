# Installation Guide

## Overview

This guide walks you through installing souleyez on your system. The process takes approximately 5-10 minutes.

## Prerequisites

### System Requirements

| Component | Minimum | Recommended | Heavy Workloads (Llama + Multiple Tools) |
|-----------|---------|-------------|-------------------------------------------|
| **CPU** | 2 cores | 4 cores | 8+ cores (multi-threaded for Llama inference) |
| **RAM** | 4GB | 8GB | 16GB+ (Llama 7B: 8GB, Llama 13B: 16GB, Llama 70B: 64GB+) |
| **GPU** | None | Optional | NVIDIA GPU with 8GB+ VRAM (for accelerated Llama) |
| **Disk Space** | 10GB | 50GB | 100GB+ (Llama models: 4-40GB each) |
| **Network** | 10 Mbps | 100 Mbps | 1 Gbps (for large-scale scanning) |

**Notes:**
- **Llama Model Sizes**: Llama 7B (~4GB), Llama 13B (~8GB), Llama 70B (~40GB)
- **GPU Acceleration**: CUDA-compatible NVIDIA GPU significantly speeds up Llama inference (10-50x faster)
- **RAM Usage**: Running multiple heavy tools (Metasploit, SQLMap, Hashcat) simultaneously requires additional RAM
- **Disk I/O**: SSD recommended for database operations and log processing

> **🐉 Kali Linux Recommended**
>
> SoulEyez performs significantly better on **Kali Linux** than other distributions:
> - All pentesting tools pre-installed and optimized
> - Metasploit database and RPC already configured
> - Security-focused kernel and networking stack
> - No dependency hunting or version conflicts
> - Wordlists, databases, and tool configs ready to go
>
> While Ubuntu and other Debian-based distros are supported, you may experience slower setup times and occasional tool compatibility issues.

### Software Requirements

- **Operating System**: Linux (Kali Linux recommended, any Debian-based distro supported)
- **Python**: 3.8 or higher (tested with Python 3.13.7)
- **pipx**: Python application installer (handles PATH automatically)
- **Git**: For cloning the repository (optional, for source install)
- **System Access**: sudo/root privileges for installing system packages

## Installation Methods

### Method 1: pipx install (Recommended)

pipx is the Python community's recommended way to install CLI applications. It handles PATH configuration automatically and creates isolated environments.

```bash
# One-time setup
sudo apt install pipx
pipx ensurepath
source ~/.bashrc    # Kali Linux: use 'source ~/.zshrc' instead

# Install SoulEyez
pipx install souleyez
```

> **Kali Linux users:** Kali uses zsh by default. Use `source ~/.zshrc` instead of `source ~/.bashrc`

On first run, SoulEyez will prompt you to install pentesting tools (nmap, sqlmap, gobuster, etc.).

```bash
souleyez dashboard
```

**Upgrading:**
```bash
pipx upgrade souleyez
```

**Uninstalling:**
```bash
pipx uninstall souleyez
```

---

### Method 2: From Source (Developers/Contributors)

For developers who want to modify the source code:

```bash
# Clone the repository
git clone https://github.com/cyber-soul-security/SoulEyez.git
cd SoulEyez

# Install python3-venv if not already installed
sudo apt install python3-venv

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install souleyez
pip install -e .
```

**What this does:**
1. Creates an isolated Python environment in the `venv/` folder
2. Installs souleyez and dependencies without affecting system Python
3. Makes the `souleyez` command available when the virtual environment is activated

**Using souleyez after installation:**
```bash
# Every time you open a new terminal, activate the virtual environment first:
cd souleyez
source venv/bin/activate

# Now you can run souleyez commands
souleyez --version
souleyez dashboard

# When done, deactivate the virtual environment
deactivate
```


## Verify Installation

After installation, verify everything works:

```bash
souleyez --version
souleyez --help
```

**If using source installation (Method 2)**, activate the virtual environment first:
```bash
cd souleyez
source venv/bin/activate
souleyez --version
```

## First Run Experience

When you launch SoulEyez for the first time:

```bash
souleyez interactive
```

**You'll be guided through the Setup Wizard:**

1. **Welcome Banner** - The SoulEyez ASCII art logo and introduction
2. **Encryption Setup** - Create a vault master password (mandatory)
3. **Create Engagement** - Set up your first project with name and type
4. **Tool Availability** - Check which security tools are installed
5. **AI Features** - Configure Ollama for AI features (optional)
6. **Summary & Tutorial** - Review settings and option to run interactive tutorial

**Encryption is mandatory** - you'll create a master password that encrypts all credentials.

**Password Requirements:**
- At least 12 characters
- Mix of uppercase and lowercase
- At least one number
- At least one special character (!@#$%^&*)

> ⚠️ **Important**: If you lose this password, encrypted credentials cannot be recovered!

**After the wizard completes**, you'll enter the main interactive menu where you can start scanning.

## Security Tools Installation

SoulEyez orchestrates external security tools. Install the ones you need:

### Network Scanning
```bash
sudo apt install -y nmap
```

### Web Application Testing
```bash
sudo apt install -y nikto gobuster dirb
```

### SMB/Windows Enumeration
```bash
sudo apt install -y enum4linux smbmap smbclient
```

### SQL Injection
```bash
sudo apt install -y sqlmap
```

### OSINT
```bash
sudo apt install -y theharvester
```

### Exploitation Framework
```bash
sudo apt install -y metasploit-framework
```

### Vulnerability Scanning

**Nuclei** - Modern vulnerability scanner with 5000+ templates (NOT available via apt):

**Method 1: Using Go (Recommended)**
```bash
# Install Go if not already installed
sudo apt install -y golang-go

# Install nuclei
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Add Go bin to PATH (add to ~/.bashrc or ~/.zshrc)
echo 'export PATH=$PATH:~/go/bin' >> ~/.bashrc
source ~/.bashrc

# Verify installation
nuclei -version

# Update templates (important!)
nuclei -update-templates
```

**Method 2: Download Pre-built Binary**
```bash
# Download latest release
wget https://github.com/projectdiscovery/nuclei/releases/download/v3.5.1/nuclei_3.5.1_linux_amd64.zip

# Unzip
unzip nuclei_3.5.1_linux_amd64.zip

# Move to system PATH
sudo mv nuclei /usr/local/bin/

# Verify installation
nuclei -version

# Update templates (important!)
nuclei -update-templates
```

### Web Crawling (Katana)

**Katana** - Web crawler for parameter and endpoint discovery:

Katana crawls web applications to discover URLs with parameters, forms, and JavaScript-rendered endpoints. It's essential for finding attack surface before running injection tests.

> **Note**: Katana requires Chromium for headless browser mode (enabled by default).

```bash
# Install Go and Chromium first
sudo apt install -y golang-go chromium

# Install katana via Go
go install github.com/projectdiscovery/katana/cmd/katana@latest

# Add Go bin to PATH if not already done
echo 'export PATH=$PATH:~/go/bin' >> ~/.zshrc   # Kali uses zsh
source ~/.zshrc

# Verify installation
katana -version
```

### Directory Bruteforcing

**Gobuster** - Fast directory/file & DNS brute-forcer:

> **Note**: The `souleyez setup` command automatically installs gobuster v3.x on Ubuntu/Debian. The manual instructions below are for reference only.

```bash
# Recommended: Let souleyez handle installation
souleyez setup

# Verify installation
gobuster version
# Should show "gobuster v3.x"
```

<details>
<summary>Manual Installation (if needed)</summary>

The `apt` version of gobuster on Ubuntu/Debian is v2.x which is incompatible. If `souleyez setup` fails, install manually:

**Method 1: Download Pre-built Binary**
```bash
# Remove old version if installed via apt
sudo apt remove gobuster

# Download latest release (AMD64)
wget https://github.com/OJ/gobuster/releases/download/v3.6.0/gobuster_Linux_x86_64.tar.gz
tar xzf gobuster_Linux_x86_64.tar.gz
sudo mv gobuster /usr/local/bin/

# For ARM64 systems:
wget https://github.com/OJ/gobuster/releases/download/v3.6.0/gobuster_Linux_arm64.tar.gz
tar xzf gobuster_Linux_arm64.tar.gz
sudo mv gobuster /usr/local/bin/
```

**Method 2: Using Go**
```bash
sudo apt install -y golang-go
go install github.com/OJ/gobuster/v3@latest
echo 'export PATH=$PATH:~/go/bin' >> ~/.bashrc
source ~/.bashrc
```
</details>

> **Note**: Kali Linux includes gobuster v3.x by default - no additional setup required.

## Database Initialization

The SQLite database is automatically created on first run:

```bash
souleyez interactive
```

**Database location**: `~/.souleyez/souleyez.db`

## Next Steps

After installation, you're ready to start! The fastest way to get up and running:

### Recommended: Use Interactive Mode

```bash
souleyez interactive
```

This launches the user-friendly menu interface where you can:
1. Complete the setup wizard (on first run)
2. Run scans with presets
3. View results in the Command Center
4. Manage engagements and findings

See the **[Getting Started Guide](getting-started.md)** for a complete walkthrough.

### Alternative: Command Line Interface

If you prefer CLI or need automation:

```bash
# Create engagement
souleyez engagement create "My First Test"

# Activate it
souleyez engagement use "My First Test"

# Enqueue a scan
souleyez jobs enqueue nmap 192.168.1.1 -a "-sV" -l "Service Detection"

# View results
souleyez hosts list
souleyez findings list
```

### Monitoring: Real-Time Dashboard

For read-only monitoring of running jobs:

```bash
souleyez dashboard
```

The dashboard auto-refreshes and shows:
- Active jobs and their progress
- Recently discovered hosts
- Latest findings
- Job queue status

**Note**: The dashboard is read-only. Use `souleyez interactive` or CLI commands to create jobs and manage data.

## Directory Structure

After installation, your directory structure:

```
# Installation directory (source code)
souleyez/
├── docs/                 # Documentation
├── souleyez/              # Source code
├── tests/                # Test suite
├── requirements.txt      # Python dependencies
└── pyproject.toml        # Package configuration

# User data directory (created on first run)
~/.souleyez/
├── souleyez.db            # SQLite database
├── config.json           # Application configuration
├── souleyez.log           # Application logs
├── artifacts/            # Scan output files
└── scans/                # Historical scan data
```

## Troubleshooting

### "command not found: souleyez"

**Cause**: Virtual environment not activated (Method 4) or installation incomplete.

**Solution**:
```bash
# For virtual environment installation
cd souleyez
source venv/bin/activate

# Verify installation
which souleyez

# If still not found, reinstall
pip install -e .
```

### "externally-managed-environment" error

**Cause**: Trying to install globally on Kali Linux or modern Python (PEP 668 protection).

**Solution**: Use Method 2 (pipx from PyPI) or Method 4 (from source with venv) from the installation section above.

**DO NOT** use `--break-system-packages` - this can break your system Python and critical OS tools.

### "Import error" when running commands

**Cause**: Missing dependencies.

**Solution**:
```bash
pip install --upgrade pip
pip install -e .
```

### Permission errors with system tools

**Cause**: Some tools (nmap, metasploit) require root privileges.

**Solution**:
```bash
# Run with sudo when needed
sudo souleyez run nmap 192.168.1.0/24

# Or configure sudoers for passwordless access (advanced)
```

### Database locked errors

**Cause**: Multiple souleyez instances accessing database simultaneously.

**Solution**:
```bash
# Check for running processes
ps aux | grep souleyez

# Kill if needed
pkill -f souleyez

# Database is located at
ls -la ~/.souleyez/souleyez.db
```

### SMBMap pickle error on Ubuntu/Debian (non-Kali)

**Cause**: SMBMap installed via pipx with incompatible impacket version causes multiprocessing pickle errors.

**Error example**:
```
multiprocessing.pool.MaybeEncodingError: Error sending result: '...'
Reason: 'AttributeError("Can't pickle local object 'Structure.__init__.<locals>.<lambda>'")'
```

**Solution**:
```bash
# Reinstall smbmap with compatible impacket version
pipx uninstall smbmap
pipx install smbmap --pip-args="impacket==0.10.0"

# Verify it works
smbmap -H <target-ip>
```

**Why this happens**: Newer impacket versions (0.11.0+) use lambda functions that Python 3.10's multiprocessing can't pickle. Kali Linux uses apt-installed smbmap with system impacket which doesn't have this issue.

---

### "No module named 'pyasn1'" error with impacket tools

**Cause**: Conflict between system-installed impacket (via apt) and pip-installed version.

**Error example**:
```
File "/usr/share/doc/python3-impacket/examples/GetNPUsers.py", line 38, in <module>
    from pyasn1.codec.der import decoder, encoder
ModuleNotFoundError: No module named 'pyasn1'
```

**Solution** (Choose ONE):

**Option 1: Use Makefile (Recommended)**
```bash
cd souleyez
source venv/bin/activate  # If using venv
make reinstall  # Forces dependency refresh
```

**Option 2: Manual dependency refresh**
```bash
cd souleyez
source venv/bin/activate  # If using venv
pip install -r requirements.txt --force-reinstall
```

**Option 3: Remove system impacket (if installed)**
```bash
sudo apt remove python3-impacket
pip install -r requirements.txt
```

**Why this happens**: The system `python3-impacket` package installs command-line tools that use the system Python, which doesn't have pyasn1. When you reinstall souleyez with `pip install -e .`, pip sees impacket is "already installed" and skips reinstalling it. The Makefile or manual refresh ensures dependencies are always current.

## Updating souleyez

To update to the latest version:

**If using pipx (Method 1):**
```bash
pipx upgrade souleyez
```

**If using source installation (Method 2):**
```bash
cd souleyez
source venv/bin/activate
git pull origin main
pip install -e .
```

## Uninstallation

**If using pipx (Method 1):**
```bash
pipx uninstall souleyez
```

**If using source installation (Method 2):**
```bash
deactivate  # If virtual environment is active
rm -rf souleyez
```

**To also remove your data:**
```bash
rm -rf ~/.souleyez
```

See [Uninstall Guide](uninstall.md) for more options.

## Next Steps

- Read the [Getting Started Guide](getting-started.md)
- Review [Dependencies](dependencies.md) for detailed version info
- Check [Troubleshooting](troubleshooting.md) for common issues
- Explore [Security Best Practices](../security/best-practices.md)

## Support

**Issues**: https://github.com/cyber-soul-security/SoulEyez/issues  
**Security Concerns**: See [SECURITY.md](../../SECURITY.md)
