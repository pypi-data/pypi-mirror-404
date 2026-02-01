# SIEM Integration Guide

SoulEyez integrates with multiple SIEM platforms to provide comprehensive security monitoring capabilities:
- **Detection Validation** - Correlate attacks with SIEM alerts to identify detection gaps
- **Alert Viewing** - Browse recent security alerts from your SIEM
- **Coverage Metrics** - Quantify detection rates across your attacks

## Supported SIEMs

| SIEM | Status | Features |
|------|--------|----------|
| **Wazuh** | Full Support | Detection, Vulnerabilities, Gap Analysis |
| **Splunk** | Full Support | Detection, Alerts, Search |
| **Elastic Security** | Supported | Detection, Alerts |
| **Microsoft Sentinel** | Supported | Detection, Alerts |

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Splunk Setup](#splunk-setup)
4. [Wazuh Setup](#wazuh-setup)
5. [Elastic Setup](#elastic-setup)
6. [Sentinel Setup](#sentinel-setup)
7. [Detection Validation](#detection-validation)
8. [Attack Signatures](#attack-signatures)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Overview

### What is Detection Validation?

Detection Validation answers the critical question: **"Did the target's security monitoring detect our attack?"**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   SoulEyez      │     │      SIEM       │     │    Report       │
│   runs attack   │────▶│   checks for    │────▶│  "SQLi attack   │
│   (SQLi, nmap)  │     │   alerts        │     │   NOT detected" │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Key Benefits

- **Automated Correlation**: Automatically match attacks to SIEM alerts
- **Detection Gap Analysis**: Identify what attacks went undetected
- **Coverage Metrics**: Quantify detection coverage (e.g., "67% of attacks detected")
- **Actionable Recommendations**: Suggest missing rules and tuning improvements
- **Professional Reports**: Include detection analysis in client deliverables
- **Multi-SIEM Support**: Works with Wazuh, Splunk, Elastic, and Sentinel

### Accessing SIEM Features

From the main menu:
1. **Intelligence Hub** → `[d]` Detection Validation
2. **Intelligence Hub** → `[s]` View SIEM Alerts
3. **Settings** → `[w]` SIEM Integration (configuration)

---

## Quick Start

### 1. Configure Your SIEM

Go to **Settings** → **SIEM Integration** → **Configure**

Select your SIEM type and enter credentials:

```
┌─────────────────────────────────────────────────────────────────┐
│ SIEM Integration Configuration                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   SIEM Type: [Splunk ▼]                                        │
│                                                                 │
│   REST API URL:      https://192.168.1.111:8089                │
│   Username:          admin                                      │
│   Password:          ••••••••••                                │
│   Default Index:     main                                       │
│                                                                 │
│   [Test Connection]  [Save]                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Test Connection

After saving, test the connection to verify credentials work.

### 3. Run Attacks

Execute your penetration testing tools against targets.

### 4. Validate Detections

Go to **Intelligence Hub** → `[d]` Detection Validation to see which attacks were detected.

---

## Splunk Setup

### Architecture

SoulEyez connects to Splunk via the REST API:

| Component | Port | Purpose |
|-----------|------|---------|
| **REST API** | 8089 | Search, authentication |
| **Receiving** | 9997 | Universal Forwarder data |
| **Syslog** | 514 | Network device logs |
| **HEC** | 8088 | HTTP Event Collector |

### Prerequisites

- Splunk Enterprise or Splunk Cloud
- REST API access (port 8089)
- User account with search permissions

### Configuration in SoulEyez

1. Go to **Settings** → **SIEM Integration**
2. Select **Splunk** as SIEM type
3. Enter:
   - **REST API URL**: `https://YOUR_SPLUNK_IP:8089`
   - **Username**: Your Splunk username
   - **Password**: Your Splunk password
   - **Default Index**: `main` (or your security index)

### Setting Up Data Sources

#### Option 1: Universal Forwarder (Endpoints)

Install on Linux, Mac, or Windows endpoints to forward logs to Splunk.

**Linux Installation:**
```bash
# Download from Splunk (requires free account):
# https://www.splunk.com/en_us/download/universal-forwarder.html
# Select Linux → .tgz → your architecture (x86_64 or ARM64)
# Use the wget command Splunk provides, e.g.:
wget -O splunkforwarder.tgz "<YOUR_SPLUNK_DOWNLOAD_URL>"

# Install
sudo tar -xzf splunkforwarder.tgz -C /opt
sudo chown -R $USER:$USER /opt/splunkforwarder

# Start and accept license
/opt/splunkforwarder/bin/splunk start --accept-license

# Configure forwarding
/opt/splunkforwarder/bin/splunk add forward-server YOUR_SPLUNK_IP:9997

# Add log sources
/opt/splunkforwarder/bin/splunk add monitor /var/log/syslog -index main -sourcetype syslog
/opt/splunkforwarder/bin/splunk add monitor /var/log/auth.log -index main -sourcetype linux_secure

# Enable boot-start
/opt/splunkforwarder/bin/splunk stop
/opt/splunkforwarder/bin/splunk enable boot-start -user $USER
/opt/splunkforwarder/bin/splunk start
```

**macOS Installation:**
```bash
# Download from splunk.com (select macOS, universal2 for Apple Silicon)

# Install
sudo tar -xzf splunkforwarder-*.tgz -C /Applications
sudo chown -R $(whoami):staff /Applications/splunkforwarder

# Start and accept license
/Applications/splunkforwarder/bin/splunk start --accept-license

# Configure forwarding
/Applications/splunkforwarder/bin/splunk add forward-server YOUR_SPLUNK_IP:9997

# Add log sources
/Applications/splunkforwarder/bin/splunk add monitor /var/log/system.log -index main -sourcetype macos_system

# Enable boot-start (requires sudo to write to /Library/LaunchDaemons)
/Applications/splunkforwarder/bin/splunk stop
sudo /Applications/splunkforwarder/bin/splunk enable boot-start -user $(whoami)
/Applications/splunkforwarder/bin/splunk start
```

> **Note (zsh users):** macOS uses zsh by default. If `$USER` gives "bad substitution" errors, use `$(whoami)` instead.

**Windows Installation:**
```powershell
# Download MSI from splunk.com

# Install with forwarding configured
msiexec.exe /i splunkforwarder-*.msi RECEIVING_INDEXER="YOUR_SPLUNK_IP:9997" AGREETOLICENSE=Yes /quiet

# Add Windows Event Logs
& "C:\Program Files\SplunkUniversalForwarder\bin\splunk.exe" add monitor "WinEventLog://Security" -index main
& "C:\Program Files\SplunkUniversalForwarder\bin\splunk.exe" add monitor "WinEventLog://System" -index main
```

#### Option 2: Syslog Receiver (Network Devices)

Configure Splunk to receive syslog from routers, firewalls, and servers.

**On Splunk Server:**
```bash
# Add to inputs.conf
sudo tee -a /opt/splunk/etc/system/local/inputs.conf << 'EOF'

[udp://514]
connection_host = ip
sourcetype = syslog
index = main

[tcp://514]
connection_host = ip
sourcetype = syslog
index = main
EOF

# Restart Splunk
sudo /opt/splunk/bin/splunk restart
```

**On Linux Servers (rsyslog):**
```bash
# Send syslog to Splunk
sudo tee /etc/rsyslog.d/50-splunk.conf << 'EOF'
*.* @YOUR_SPLUNK_IP:514
EOF

sudo systemctl restart rsyslog
```

**On Network Devices:**
- Set syslog server to `YOUR_SPLUNK_IP`
- Port: `514`
- Protocol: `UDP`

#### Option 3: HTTP Event Collector (APIs/Apps)

For custom applications and cloud services.

**Enable HEC on Splunk:**
1. Settings → Data Inputs → HTTP Event Collector
2. Global Settings → Enable
3. New Token → Create token for your app

**Send events:**
```bash
curl -k https://YOUR_SPLUNK_IP:8088/services/collector/event \
  -H "Authorization: Splunk YOUR_HEC_TOKEN" \
  -d '{"event": {"message": "Test event"}, "sourcetype": "custom"}'
```

### Enable Receiving on Splunk

For Universal Forwarders to work, enable receiving:

```bash
sudo /opt/splunk/bin/splunk enable listen 9997
```

Or via Web UI: Settings → Forwarding and Receiving → Receive Data → Add port 9997

### Verify Data Flow

Search in Splunk:
```spl
index=main | stats count by host, sourcetype | sort -count
```

---

## Wazuh Setup

### Architecture

SoulEyez connects to two Wazuh components:

| Component | Port | Purpose |
|-----------|------|---------|
| **Wazuh Manager API** | 55000 | Authentication, rule queries, agent info |
| **Wazuh Indexer** | 9200 | Alert queries (Elasticsearch-compatible) |

### Prerequisites

- **Wazuh 4.x** (4.5+ recommended)
- Manager API enabled and accessible
- Indexer (OpenSearch/Elasticsearch) accessible
- API user with appropriate permissions

### Configuration in SoulEyez

1. Go to **Settings** → **SIEM Integration**
2. Select **Wazuh** as SIEM type
3. Enter:
   - **Manager API URL**: `https://YOUR_WAZUH_IP:55000`
   - **Username**: API username
   - **Password**: API password
   - **Indexer URL**: `https://YOUR_WAZUH_IP:9200`
   - **Indexer Username**: `admin` (default)
   - **Indexer Password**: Indexer password

### Wazuh-Specific Features

Wazuh includes additional features not available in other SIEMs:

#### Vulnerability Management

Sync and track CVEs from Wazuh's vulnerability scanner:
- **Intelligence Hub** → Host Detail → `[z]` Wazuh Vulns

#### Gap Analysis

Compare passive Wazuh detection vs active scan findings:
- **Intelligence Hub** → `[y]` Gap Analysis

#### Agent Configuration

For optimal detection, ensure Wazuh agents have proper logging enabled:

**Linux Agent:**
```xml
<localfile>
    <log_format>syslog</log_format>
    <location>/var/log/auth.log</location>
</localfile>
```

**Windows Agent:**
```xml
<localfile>
    <location>Security</location>
    <log_format>eventchannel</log_format>
</localfile>
```

---

## Wazuh to Splunk Forwarding

If you use **Wazuh agents** for endpoint monitoring but prefer **Splunk** as your central SIEM, you can forward Wazuh alerts to Splunk.

### Benefits

- **Unified visibility**: Wazuh alerts alongside network, cloud, and application logs
- **Cross-source correlation**: Correlate Wazuh file integrity alerts with network traffic
- **Advanced analytics**: Use Splunk's SPL, machine learning, and dashboards
- **Single pane of glass**: One platform for your SOC team

### Step 1: Create HEC Token in Splunk

1. **Settings** → **Data Inputs** → **HTTP Event Collector**
2. Click **Global Settings** → Enable HEC → Save
3. Click **New Token**:
   - **Name**: `wazuh`
   - **Source type**: Create new → `wazuh_alerts`
   - **Index**: `main` (or create a `wazuh` index)
4. Copy the **Token Value**

### Step 2: Configure Wazuh Manager

SSH to your Wazuh manager and edit the config:

```bash
sudo nano /var/ossec/etc/ossec.conf
```

Add inside the `<ossec_config>` block:

```xml
<global>
  <jsonout_output>yes</jsonout_output>
</global>

<syslog_output>
  <server>YOUR_SPLUNK_IP</server>
  <port>514</port>
  <format>json</format>
  <level>3</level>
</syslog_output>
```

> **Note**: If Splunk runs on the same machine as Wazuh manager, use `127.0.0.1`

### Step 3: Ensure Splunk Receives Syslog

Verify UDP 514 is configured in Splunk:

**Settings** → **Data Inputs** → **UDP** → Add port `514`

Or via CLI:
```bash
sudo tee -a /opt/splunk/etc/system/local/inputs.conf << 'EOF'

[udp://514]
connection_host = ip
sourcetype = syslog
index = main
EOF

sudo /opt/splunk/bin/splunk restart
```

### Step 4: Restart Wazuh Manager

```bash
sudo systemctl restart wazuh-manager
```

### Step 5: Verify Data Flow

Check Splunk for Wazuh alerts:

```spl
index=main sourcetype=syslog ossec | head 10
```

You should see JSON alerts with fields like `rule.level`, `agent.name`, `rule.description`.

### Searching Wazuh Data in Splunk

The JSON is embedded in syslog. Extract it with:

```spl
index=main sourcetype=syslog ossec
| rex field=_raw "ossec: (?<wazuh_json>\{.+\})"
| spath input=wazuh_json
| table _time, rule.level, rule.description, agent.name, agent.ip
```

### Sample Wazuh Dashboard for Splunk

Import this dashboard for visualizing Wazuh alerts in Splunk:

```xml
<dashboard version="1.1" theme="dark">
  <label>Wazuh Security Dashboard</label>
  <row>
    <panel>
      <title>Alerts by Severity</title>
      <chart>
        <search>
          <query>index=main sourcetype=syslog ossec earliest=-24h
| rex field=_raw "ossec: (?&lt;wj&gt;\{.+\})"
| spath input=wj path=rule.level output=level
| eval severity=case(
    tonumber(level)&gt;=12, "Critical",
    tonumber(level)&gt;=10, "High",
    tonumber(level)&gt;=7, "Medium",
    true(), "Low/Info")
| stats count by severity</query>
        </search>
        <option name="charting.chart">pie</option>
      </chart>
    </panel>
  </row>
</dashboard>
```

### Configure SoulEyez for Splunk

After forwarding Wazuh to Splunk, configure SoulEyez to use **Splunk** (not Wazuh directly):

1. **Settings** → **SIEM Integration**
2. Select **Splunk** as SIEM type
3. Enter Splunk REST API credentials
4. Detection validation will query Splunk for Wazuh alerts

---

## Wazuh Vulnerability Data to Splunk

Wazuh's vulnerability scanner detects CVEs on endpoints. This data is stored in the Wazuh Indexer but can be synced to Splunk for unified visibility.

### Step 1: Create Splunk Index

1. **Settings** → **Indexes** → **New Index**
2. **Name**: `wazuh_vulns`
3. Leave other settings as default
4. **Save**

### Step 2: Update HEC Token

1. **Settings** → **Data Inputs** → **HTTP Event Collector**
2. Edit your Wazuh HEC token
3. Add `wazuh_vulns` to **Allowed Indexes**
4. **Save**

### Step 3: Install Sync Script

Copy the vulnerability sync script to your Wazuh/Splunk server:

```bash
# On the Wazuh manager server
mkdir -p ~/scripts
```

Create `~/scripts/wazuh_vuln_to_splunk.py`:

```python
#!/usr/bin/env python3
"""
Wazuh Vulnerability to Splunk Forwarder

Queries Wazuh Indexer for vulnerability data and sends to Splunk HEC.
Run via cron for continuous sync.
"""

import json
import os
import sys
import urllib3
from datetime import datetime

import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONFIG = {
    "wazuh_indexer_url": os.getenv("WAZUH_INDEXER_URL", "https://127.0.0.1:9200"),
    "wazuh_indexer_user": os.getenv("WAZUH_INDEXER_USER", "admin"),
    "wazuh_indexer_pass": os.getenv("WAZUH_INDEXER_PASS", ""),
    "splunk_hec_url": os.getenv("SPLUNK_HEC_URL", "https://127.0.0.1:8088/services/collector/event"),
    "splunk_hec_token": os.getenv("SPLUNK_HEC_TOKEN", ""),
    "index_pattern": "wazuh-states-vulnerabilities-*",
    "batch_size": 100,
    "splunk_index": "wazuh_vulns",
    "splunk_sourcetype": "wazuh:vulnerabilities",
}

def get_vulnerabilities(config, since_hours=24):
    url = f"{config['wazuh_indexer_url']}/{config['index_pattern']}/_search"
    query = {
        "size": 10000,
        "query": {"range": {"vulnerability.detected_at": {"gte": f"now-{since_hours}h", "lte": "now"}}},
        "_source": ["agent.id", "agent.name", "host.os.name", "host.os.version",
                    "package.name", "package.version", "vulnerability.id",
                    "vulnerability.severity", "vulnerability.score.base",
                    "vulnerability.description", "vulnerability.detected_at",
                    "vulnerability.reference", "vulnerability.category"],
        "sort": [{"vulnerability.detected_at": "desc"}]
    }
    try:
        response = requests.post(url, json=query,
            auth=(config["wazuh_indexer_user"], config["wazuh_indexer_pass"]),
            verify=False, timeout=30)
        response.raise_for_status()
        hits = response.json().get("hits", {}).get("hits", [])
        print(f"[+] Retrieved {len(hits)} vulnerabilities")
        return [hit["_source"] for hit in hits]
    except Exception as e:
        print(f"[-] Error: {e}")
        return []

def send_to_splunk(config, vulns):
    if not vulns:
        return True
    headers = {"Authorization": f"Splunk {config['splunk_hec_token']}", "Content-Type": "application/json"}
    success = 0
    for i in range(0, len(vulns), config["batch_size"]):
        batch = vulns[i:i + config["batch_size"]]
        events = []
        for v in batch:
            events.append({
                "event": {
                    "agent_id": v.get("agent", {}).get("id"),
                    "agent_name": v.get("agent", {}).get("name"),
                    "os_name": v.get("host", {}).get("os", {}).get("name"),
                    "package_name": v.get("package", {}).get("name"),
                    "package_version": v.get("package", {}).get("version"),
                    "cve": v.get("vulnerability", {}).get("id"),
                    "severity": v.get("vulnerability", {}).get("severity"),
                    "cvss_score": v.get("vulnerability", {}).get("score", {}).get("base"),
                    "description": v.get("vulnerability", {}).get("description"),
                    "detected_at": v.get("vulnerability", {}).get("detected_at"),
                },
                "index": config["splunk_index"],
                "sourcetype": config["splunk_sourcetype"],
            })
        try:
            r = requests.post(config["splunk_hec_url"], headers=headers,
                data="\n".join(json.dumps(e) for e in events), verify=False, timeout=30)
            if r.status_code == 200:
                success += len(batch)
        except Exception as e:
            print(f"[-] Splunk error: {e}")
    print(f"[+] Sent {success} vulnerabilities to Splunk")
    return success > 0

if __name__ == "__main__":
    if not CONFIG["wazuh_indexer_pass"] or not CONFIG["splunk_hec_token"]:
        print("[-] Set WAZUH_INDEXER_PASS and SPLUNK_HEC_TOKEN")
        sys.exit(1)
    vulns = get_vulnerabilities(CONFIG, since_hours=24)
    send_to_splunk(CONFIG, vulns)
```

### Step 4: Install Dependencies

```bash
sudo apt install python3-requests python3-urllib3
```

### Step 5: Test the Script

```bash
WAZUH_INDEXER_PASS='your_indexer_password' \
SPLUNK_HEC_TOKEN='your_hec_token' \
python3 ~/scripts/wazuh_vuln_to_splunk.py
```

### Step 6: Set Up Cron Job

```bash
# Create log directory
sudo mkdir -p /var/log/souleyez
sudo chown $USER:$USER /var/log/souleyez

# Add hourly cron job
(crontab -l 2>/dev/null; echo "0 * * * * WAZUH_INDEXER_PASS='YOUR_PASS' SPLUNK_HEC_TOKEN='YOUR_TOKEN' /usr/bin/python3 $HOME/scripts/wazuh_vuln_to_splunk.py >> /var/log/souleyez/vuln_sync.log 2>&1") | crontab -
```

### Step 7: Search Vulnerabilities in Splunk

```spl
index=wazuh_vulns sourcetype=wazuh:vulnerabilities
| stats count by severity, cve
| sort -count
```

### Sample Vulnerability Dashboard Panel

Add this to your Wazuh dashboard for vulnerability visibility:

```xml
<row>
  <panel>
    <title>All Vulnerabilities</title>
    <table>
      <search>
        <query>index=wazuh_vulns sourcetype=wazuh:vulnerabilities
| dedup cve, agent_name
| table cve, severity, cvss_score, package_name, package_version, os_name, agent_name, detected_at, description
| sort -cvss_score, -severity</query>
        <earliest>-7d@d</earliest>
        <latest>now</latest>
      </search>
      <option name="drilldown">row</option>
      <option name="count">50</option>
    </table>
  </panel>
</row>
```

---

## Elastic Setup

### Architecture

| Component | Port | Purpose |
|-----------|------|---------|
| **Elasticsearch** | 9200 | Alert storage and search |
| **Kibana** | 5601 | Optional - for manual verification |

### Configuration in SoulEyez

1. Go to **Settings** → **SIEM Integration**
2. Select **Elastic Security** as SIEM type
3. Enter:
   - **Elasticsearch URL**: `https://YOUR_ELASTIC_IP:9200`
   - **API Key** or **Username/Password**
   - **Kibana URL**: (optional) `https://YOUR_KIBANA_IP:5601`
   - **Space**: `default` (or your Kibana space)

### Alert Index

Elastic Security stores alerts in the `.siem-signals-*` index pattern.

---

## Sentinel Setup

### Architecture

Microsoft Sentinel uses Azure services:

| Component | Purpose |
|-----------|---------|
| **Log Analytics Workspace** | Alert storage and KQL queries |
| **Azure AD App Registration** | API authentication |

### Prerequisites

- Azure subscription with Sentinel enabled
- Log Analytics Workspace
- App Registration with API permissions

### Configuration in SoulEyez

1. Go to **Settings** → **SIEM Integration**
2. Select **Microsoft Sentinel** as SIEM type
3. Enter:
   - **Tenant ID**: Your Azure tenant ID
   - **Client ID**: App registration client ID
   - **Client Secret**: App registration secret
   - **Workspace ID**: Log Analytics workspace ID

### Azure AD App Permissions

Your app registration needs:
- `Log Analytics API` → `Data.Read`

---

## Detection Validation

### Running Validation

After completing attacks:

1. Go to **Intelligence Hub** → `[d]` Detection Validation
2. View results showing which attacks were detected

### Understanding Results

Each attack receives a detection status:

| Status | Meaning |
|--------|---------|
| **Detected** | SIEM generated alerts for this attack |
| **Not Detected** | No matching alerts found - detection gap! |
| **Partial** | Some expected alerts found, but not all |
| **Offline** | Tool runs locally (e.g., hashcat) - no network detection expected |

### Coverage Summary

```
┌─────────────────────────────────────────────────────────────────┐
│ Detection Coverage Summary                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ████████████░░░░░░  67%  Detection Rate                       │
│                                                                 │
│   Total Attacks:     18                                         │
│   Detected:          12  ████████████                           │
│   Not Detected:       4  ████  ← GAPS                           │
│   Offline:            2  ██                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Attack Signatures

SoulEyez maps each attack tool to expected detection patterns.

### Supported Tools

| Tool | Category | Detection Method |
|------|----------|------------------|
| **nmap** | Reconnaissance | Port scan alerts, firewall logs |
| **hydra** | Credential Access | Failed auth events, brute force alerts |
| **sqlmap** | Web Attack | WAF alerts, web server logs |
| **gobuster** | Web Attack | 404 spikes, directory scan patterns |
| **nikto** | Web Attack | Scanner user-agent, vuln probes |
| **metasploit** | Exploitation | IDS signatures, exploit patterns |
| **hashcat** | Credential Access | *Offline - no detection expected* |

### Detection Windows

Each attack type has a configurable detection window:
- **Port scans (nmap)**: 5 minutes after attack
- **Brute force (hydra)**: 10 minutes after attack
- **Web attacks (sqlmap)**: 5 minutes after attack

---

## Troubleshooting

### Connection Issues

**Error: "Connection failed"**
```
Fix:
  1. Verify network connectivity to SIEM
  2. Check firewall allows required ports
  3. Ensure SIEM service is running
```

**Error: "401 Unauthorized"**
```
Fix:
  1. Verify credentials are correct
  2. Check user has required permissions
  3. For Splunk: ensure user can run searches
```

**Error: "SSL certificate verify failed"**
```
Fix: Set "Verify SSL" to No in configuration (for self-signed certs)
```

### Detection Issues

**Problem: Attacks show "Not Detected" but alerts exist**
```
Possible causes:
  1. Time sync issue between attack host and SIEM
  2. Wrong source IP in search
  3. Detection window too short

Fix:
  1. Sync time: sudo ntpdate pool.ntp.org
  2. Verify attack source IP
  3. Manually search SIEM in wider time range
```

### Splunk-Specific Issues

**Forwarder not sending data:**
```bash
# Check forwarder status
/opt/splunkforwarder/bin/splunk list forward-server

# Should show "Active forwards" with your server
# If "inactive", check network connectivity and port 9997
```

**No data in search:**
```spl
# Check what's being indexed
index=* | stats count by index, sourcetype, host
```

---

## Best Practices

### Before the Engagement

1. **Configure SIEM connection** before starting attacks
2. **Test the connection** to ensure API access works
3. **Verify data sources** are sending logs
4. **Sync time** between attack host and SIEM/targets

### During the Engagement

1. **Run attacks from consistent IP** so SIEM can correlate
2. **Document attack times** for manual verification
3. **Periodically validate detections** to catch issues early

### After the Engagement

1. **Generate detection coverage report** for client
2. **Highlight detection gaps** with recommendations
3. **Include rule tuning suggestions** based on gaps

---

## Quick Reference

### Menu Locations

| Feature | Location |
|---------|----------|
| Configure SIEM | Settings → SIEM Integration |
| View Alerts | Intelligence Hub → `[s]` |
| Detection Validation | Intelligence Hub → `[d]` |
| Attack Signatures | Settings → SIEM Integration → Attack Signatures |

### Default Ports

| SIEM | Ports |
|------|-------|
| **Splunk** | 8089 (API), 9997 (Forwarder), 514 (Syslog), 8088 (HEC) |
| **Wazuh** | 55000 (API), 9200 (Indexer) |
| **Elastic** | 9200 (Elasticsearch), 5601 (Kibana) |
| **Sentinel** | Azure APIs (HTTPS) |

---

## Support

For issues with SIEM integration:
1. Check this guide's [Troubleshooting](#troubleshooting) section
2. Review SIEM-specific logs
3. Report bugs: https://github.com/cyber-soul-security/SoulEyez/issues
