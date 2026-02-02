# SoulEyez — AI-Powered Penetration Testing Platform

[![CI](https://github.com/cyber-soul-security/souleyez/actions/workflows/python-ci.yml/badge.svg)](https://github.com/cyber-soul-security/souleyez/actions/workflows/python-ci.yml)
[![codecov](https://codecov.io/gh/cyber-soul-security/souleyez/branch/main/graph/badge.svg)](https://codecov.io/gh/cyber-soul-security/souleyez)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

---

## What is SoulEyez?

**SoulEyez is your penetration testing command center.** Instead of juggling dozens of terminal windows and text files, SoulEyez gives you one organized place to:

- **Run security scans** — Execute tools like Nmap, Gobuster, SQLMap with simple commands
- **Auto-discover next steps** — When one scan finds something interesting, SoulEyez automatically suggests (or runs) the next logical tool
- **Stay organized** — Keep all your targets, findings, and credentials in one searchable database
- **Generate reports** — Export professional reports when you're done

---

## Who is this for?

- **Security professionals** conducting authorized penetration tests
- **CTF players** who want better organization during competitions
- **Students** learning penetration testing methodology

> **Important:** Only use SoulEyez on systems you have explicit authorization to test. Unauthorized scanning or exploitation is illegal.

---

## Features

### Core Capabilities

- 🎯 **Interactive Dashboard** — Real-time engagement monitoring with live updates
- 🔗 **Smart Tool Chaining** — Automatic follow-up scans based on discoveries
- 📊 **Findings Management** — Track and categorize vulnerabilities by severity
- 🔑 **Credential Vault** — Encrypted storage for discovered credentials
- 🌐 **Network Mapping** — Host discovery and service enumeration
- 📈 **Progress Tracking** — Monitor scan completion and tool execution
- 💾 **SQLite Storage** — Local database for all engagement data
- 🔄 **Background Jobs** — Queue-based tool execution with status monitoring

### Integrated Tools (40+)

- **Reconnaissance**: nmap, masscan, theHarvester, whois, dnsrecon
- **Web Testing**: nikto, gobuster, ffuf, sqlmap, nuclei, wpscan
- **Enumeration**: enum4linux-ng, smbmap, crackmapexec, snmpwalk
- **Exploitation**: Metasploit integration, searchsploit
- **Password Attacks**: hydra, hashcat, john
- **Post-Exploitation**: impacket suite, bloodhound

### Pentest Workflow & Intelligence

- 📁 **Evidence Vault** — Unified artifact collection organized by PTES phases
- 🎯 **Attack Surface Dashboard** — Track what's exploited vs pending with priority scoring
- 💣 **Exploit Suggestions** — Automatic CVE/Metasploit recommendations for discovered services
- 🔗 **Correlation Engine** — Cross-phase attack tracking and gap analysis
- 📝 **Report Generator** — Professional reports in Markdown/HTML/PDF formats
- ✅ **Deliverable Tracking** — Manage testing requirements and acceptance criteria
- 📸 **Screenshot Management** — Organized visual evidence by methodology phase

### SIEM Integration

- 🛡️ **SIEM Connectors** — Connect to Wazuh, Splunk, and other SIEM platforms
- ✓ **Detection Validation** — Verify if your attacks triggered SIEM alerts
- 🔍 **Vulnerability Management** — View CVEs from SIEM vulnerability data
- ⚖️ **Gap Analysis** — Compare passive (SIEM) vs active (scan) findings
- 🗺️ **MITRE ATT&CK Reports** — Detection coverage heatmaps by technique
- 📡 **Real-time Alerts** — Monitor SIEM alerts during live engagements

### FREE vs PRO

| Feature | FREE | PRO |
|---------|------|-----|
| Core features (scans, findings, credentials) | ✅ | ✅ |
| Report generation | ✅ | ✅ |
| AI-powered suggestions & auto-chaining | ❌ | ✅ |
| Metasploit integration & exploit suggestions | ❌ | ✅ |
| SIEM integration & detection validation | ❌ | ✅ |
| MITRE ATT&CK reports | ❌ | ✅ |

---

## Quick Start

### Step 1: Install Prerequisites

```bash
sudo apt install pipx    # Install pipx
pipx ensurepath          # Add pipx apps to your PATH
source ~/.bashrc         # Reload shell (Kali: use ~/.zshrc)
```

### Step 2: Install SoulEyez

```bash
pipx install souleyez
```

### Step 3: Launch SoulEyez

```bash
souleyez interactive
```

### Step 4: First-Time Setup

On your first run, the setup wizard guides you through:

1. **Vault Password** — Create a master password that encrypts sensitive data
2. **First Engagement** — Set up your first project and select engagement type
3. **Tool Check** — Detect and optionally install missing security tools
4. **AI Setup** — Configure Ollama for AI features (optional)
5. **Tutorial** — Option to run the interactive tutorial (recommended)

### Step 5: You're Ready!

Once setup completes, you'll see the main menu.

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Ubuntu 22.04+ | Kali Linux |
| **Python** | 3.9+ | 3.11+ |
| **RAM** | 4GB | 8GB+ |
| **Disk** | 10GB | 50GB+ |

### Supported Operating Systems

| OS | Status | Notes |
|----|--------|-------|
| **Kali Linux** | ✅ Recommended | All pentesting tools pre-installed |
| **Ubuntu 22.04+** | ✅ Supported | Tools installed via `souleyez setup` |
| **Parrot OS** | ✅ Supported | Security-focused distro |
| **Debian 12+** | ✅ Supported | Stable base system |
| **macOS/Windows** | ❌ Not Supported | Use Linux in a VM |

---

## Common Commands

| Command | What it does |
|---------|--------------|
| `souleyez interactive` | Launch the main interface |
| `souleyez dashboard` | Real-time monitoring view |
| `souleyez doctor` | Check if everything is set up correctly |
| `souleyez setup` | Install/update pentesting tools |
| `souleyez --help` | Show all available commands |

---

## Security & Encryption

SoulEyez encrypts all stored credentials using **Fernet (AES-128-CBC + HMAC-SHA256)** with PBKDF2 key derivation (600k iterations).

- Master password is never stored (cannot be recovered if lost)
- Credentials encrypted at rest with industry-standard cryptography
- Sensitive data is masked in the UI until explicitly revealed

See [SECURITY.md](SECURITY.md) for complete security guidelines.

---

## Documentation

- **[Getting Started](souleyez/docs/user-guide/getting-started.md)** — Your first engagement in 10 minutes
- **[Installation Guide](souleyez/docs/user-guide/installation.md)** — Detailed setup instructions
- **[Workflows](souleyez/docs/user-guide/workflows.md)** — Complete pentesting workflows
- **[Auto-Chaining](souleyez/docs/user-guide/auto-chaining.md)** — Automatic follow-up scans
- **[Configuration](souleyez/docs/user-guide/configuration.md)** — All configuration options
- **[Troubleshooting](souleyez/docs/user-guide/troubleshooting.md)** — Common issues and fixes

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "command not found: souleyez" | Run `pipx ensurepath` then restart terminal |
| "Tool not found" errors | Run `souleyez setup` to install missing tools |
| Forgot vault password | Data is encrypted — start fresh with `rm -rf ~/.souleyez` |
| Something seems broken | Run `souleyez doctor` to diagnose |

---

## Glossary

New to pentesting? Here are some common terms:

| Term | Meaning |
|------|---------|
| **Engagement** | A project or assessment — contains all data for one test |
| **Target/Host** | A computer, server, or device you're testing |
| **Finding** | A security issue or vulnerability you discovered |
| **Credential** | Username/password combo found during testing |

---

## Support & Feedback

- **Issues**: https://github.com/cyber-soul-security/souleyez/issues
- **Security Issues**: cysoul.secit@gmail.com (see [SECURITY.md](SECURITY.md))
- **General**: cysoul.secit@gmail.com

---

## License

See [LICENSE](LICENSE) for details.

---

**Version**: 2.43.21 | **Maintainer**: [CyberSoul Security](https://www.cybersoulsecurity.com)
