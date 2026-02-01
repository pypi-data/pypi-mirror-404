# Parser Output Formats and Expected Inputs

## Overview

SoulEyez parsers convert raw tool output into structured data that's stored in the database. This document defines input expectations and output formats for all parsers.

---

## Parser Architecture

### Flow

```
Tool Output (text) → Parser → Structured Data → Database Storage
```

### Parser Location

**Module:** `souleyez.parsers`

**Files:**
- `nmap_parser.py`
- `nikto_parser.py`
- `gobuster_parser.py`
- `sqlmap_parser.py`
- `enum4linux_parser.py`
- `smbmap_parser.py`
- `hydra_parser.py`
- `theharvester_parser.py`
- `wpscan_parser.py`
- `whois_parser.py`
- `dnsrecon_parser.py`
- `msf_parser.py`

---

## Common Parser Interface

All parsers should follow this pattern:

```python
def parse_<tool>_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse tool output into structured data.
    
    Args:
        output: Raw tool output text
        target: Target from job (for context)
    
    Returns:
        Dict with structured data
    """
    pass
```

---

## Network Scanners

### nmap_parser

**Function:** `parse_nmap_text(output: str) -> Dict[str, Any]`

**Input:** Nmap text output (plain text format, not XML)

**Expected Nmap Arguments:**
- Any scan type: `-sS`, `-sT`, `-sU`, `-sn`, etc.
- Service detection: `-sV`
- OS detection: `-O`
- Default scripts: `-sC`
- All formats work, but text is parsed

**Output Structure:**

```python
{
    'hosts': [
        {
            'ip': '192.168.1.100',
            'hostname': 'webserver.local',
            'status': 'up',  # 'up', 'down', 'unknown'
            'os': 'Linux 5.x',  # if detected
            'services': [
                {
                    'port': 22,
                    'protocol': 'tcp',
                    'state': 'open',
                    'service': 'ssh',
                    'version': 'OpenSSH 8.2p1 Ubuntu 4ubuntu0.1'
                },
                {
                    'port': 80,
                    'protocol': 'tcp',
                    'state': 'open',
                    'service': 'http',
                    'version': 'Apache httpd 2.4.41'
                }
            ]
        }
    ]
}
```

**Database Storage:**
- Creates/updates records in `hosts` table
- Creates records in `services` table
- Sets host status (up/down)

**Example Input:**

```
Nmap scan report for 192.168.1.100
Host is up (0.00050s latency).
Not shown: 998 closed ports
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.1
80/tcp open  http    Apache httpd 2.4.41
```

**Edge Cases:**
- Host down: `status='down'`, no services
- Filtered ports: Included with `state='filtered'`
- Hostname with IP: Parses both
- Multiple hosts: Returns array

---

## Web Scanners

### nikto_parser

**Function:** `parse_nikto_output(output: str, target: str = "") -> Dict[str, Any]`

**Input:** Nikto text output

**Expected Nikto Arguments:**
- `-h <target>` - Target host/URL
- Output format: Default text (not XML/JSON)

**Output Structure:**

```python
{
    'target_ip': '44.228.249.3',
    'target_host': 'testphp.vulnweb.com',
    'target_port': 80,
    'server': 'nginx/1.19.0',
    'findings': [
        {
            'path': '/admin',
            'description': 'Admin login page found',
            'reference': 'https://cve.mitre.org/...',  # if present
            'severity': 'medium'  # 'info', 'low', 'medium', 'high'
        }
    ]
}
```

**Database Storage:**
- Creates records in `findings` table
- Associates with target host
- Stores web paths in `web_paths` table

**Example Input:**

```
+ Target IP:          44.228.249.3
+ Target Hostname:    testphp.vulnweb.com
+ Target Port:        80
+ Server: nginx/1.19.0
+ /admin: Admin login page found. See: https://example.com/ref
+ /config.php: PHP configuration file may contain sensitive data
```

**Severity Detection:**
- Keywords: "vulnerable", "exploit", "injection" → high
- Keywords: "exposed", "misconfiguration" → medium
- Keywords: "found", "identified" → low
- Default: info

---

### gobuster_parser

**Function:** `parse_gobuster_output(output: str, target: str = "") -> Dict[str, Any]`

**Input:** Gobuster directory enumeration output

**Expected Gobuster Arguments:**
- `dir` mode
- `-u <url>` - Target URL
- `-w <wordlist>` - Wordlist path

**Output Structure:**

```python
{
    'target_url': 'http://example.com',
    'paths': [
        {
            'path': '/admin',
            'status_code': 200,
            'size': 1234,
            'redirect': None  # or redirect URL
        },
        {
            'path': '/images',
            'status_code': 301,
            'size': 169,
            'redirect': 'http://example.com/images/'
        }
    ]
}
```

**Database Storage:**
- Creates records in `web_paths` table
- Associates with target host
- Stores status codes and sizes

**Example Input:**

```
===============================================================
Gobuster v3.8
===============================================================
[+] Url:                     http://example.com
[+] Method:                  GET
[+] Threads:                 10
===============================================================
/admin                (Status: 200) [Size: 1234]
/images               (Status: 301) [Size: 169] [--> http://example.com/images/]
/cgi-bin/             (Status: 403) [Size: 276]
```

---

### sqlmap_parser

**Function:** `parse_sqlmap_output(output: str, target: str = "") -> Dict[str, Any]`

**Input:** SQLMap text output

**Expected SQLMap Arguments:**
- `-u <url>` - Target URL
- Any injection techniques

**Output Structure:**

```python
{
    'target_url': 'http://example.com/page.php?id=1',
    'vulnerable': True,
    'injection_type': 'boolean-based blind',
    'database_type': 'MySQL',
    'findings': [
        {
            'parameter': 'id',
            'injection_type': 'boolean-based blind',
            'payload': "1 AND 1=1",
            'description': 'SQL injection vulnerability found',
            'severity': 'critical'
        }
    ],
    'databases': ['information_schema', 'mysql', 'webapp_db'],
    'tables': [],  # if enumerated
    'columns': []  # if enumerated
}
```

**Database Storage:**
- Creates critical finding for SQL injection
- Stores extracted databases/tables/columns
- Associates with target host/service

**Example Input:**

```
[*] testing for SQL injection on GET parameter 'id'
[INFO] GET parameter 'id' appears to be 'MySQL >= 5.0 AND error-based' injectable
[INFO] the back-end DBMS is MySQL
web application technology: PHP 5.6.40, Apache 2.4.41
back-end DBMS: MySQL >= 5.0
available databases [3]:
[*] information_schema
[*] mysql
[*] webapp_db
```

---

## Windows/SMB Tools

### enum4linux_parser

**Function:** `parse_enum4linux_output(output: str, target: str = "") -> Dict[str, Any]`

**Input:** Enum4linux text output

**Output Structure:**

```python
{
    'target': '192.168.1.100',
    'workgroup': 'WORKGROUP',
    'server_name': 'WIN-SERVER',
    'os': 'Windows 10',
    'users': ['Administrator', 'Guest', 'user1'],
    'shares': [
        {
            'name': 'IPC$',
            'type': 'IPC',
            'comment': 'Remote IPC'
        },
        {
            'name': 'C$',
            'type': 'Disk',
            'comment': 'Default share'
        }
    ],
    'groups': ['Domain Users', 'Administrators']
}
```

**Database Storage:**
- Updates host with OS info
- Stores shares in `smb_shares` table
- Stores users in `credentials` table (with placeholder password)
- Creates findings for open shares

---

### smbmap_parser

**Function:** `parse_smbmap_output(output: str, target: str = "") -> Dict[str, Any]`

**Input:** SMBMap text output

**Output Structure:**

```python
{
    'target': '192.168.1.100',
    'shares': [
        {
            'name': 'ADMIN$',
            'permissions': 'NO ACCESS',
            'comment': 'Remote Admin'
        },
        {
            'name': 'Data',
            'permissions': 'READ, WRITE',
            'comment': 'Shared Data'
        }
    ]
}
```

**Database Storage:**
- Creates records in `smb_shares` table
- Creates findings for writable shares

---

## Password Tools

### hydra_parser

**Function:** `parse_hydra_output(output: str, target: str = "") -> Dict[str, Any]`

**Input:** Hydra text output

**Output Structure:**

```python
{
    'target': '192.168.1.100',
    'service': 'ssh',
    'port': 22,
    'credentials': [
        {
            'username': 'admin',
            'password': 'password123',
            'status': 'valid'
        }
    ],
    'attempts': 150,
    'found': 1
}
```

**Database Storage:**
- Creates records in `credentials` table
- Creates findings for weak credentials
- Associates with target service

**Example Input:**

```
[22][ssh] host: 192.168.1.100   login: admin   password: password123
[STATUS] 150.00 tries/min, 150 tries in 00:01h
[STATUS] Found 1 valid password
```

---

## OSINT Tools

### theharvester_parser

**Function:** `parse_theharvester_output(output: str, target: str = "") -> Dict[str, Any]`

**Input:** theHarvester text output

**Output Structure:**

```python
{
    'domain': 'example.com',
    'emails': [
        'admin@example.com',
        'support@example.com'
    ],
    'hosts': [
        'mail.example.com',
        'www.example.com'
    ],
    'ips': [
        '192.0.2.1',
        '192.0.2.2'
    ],
    'subdomains': [
        'mail.example.com',
        'www.example.com',
        'ftp.example.com'
    ]
}
```

**Database Storage:**
- Creates records in `osint_data` table
- Creates host records for discovered IPs
- Stores emails and subdomains

---

### whois_parser

**Function:** `parse_whois_output(output: str, target: str = "") -> Dict[str, Any]`

**Input:** WHOIS text output

**Output Structure:**

```python
{
    'domain': 'example.com',
    'registrar': 'Example Registrar Inc.',
    'creation_date': '2000-01-01',
    'expiration_date': '2026-01-01',
    'name_servers': ['ns1.example.com', 'ns2.example.com'],
    'emails': ['admin@example.com']
}
```

**Database Storage:**
- Creates records in `osint_data` table
- Stores WHOIS metadata

---

### dnsrecon_parser

**Function:** `parse_dnsrecon_output(output: str, target: str = "") -> Dict[str, Any]`

**Input:** DNSRecon text output

**Output Structure:**

```python
{
    'domain': 'example.com',
    'records': [
        {
            'type': 'A',
            'name': 'example.com',
            'address': '192.0.2.1'
        },
        {
            'type': 'MX',
            'name': 'example.com',
            'address': 'mail.example.com',
            'priority': 10
        }
    ],
    'zone_transfer': False,
    'subdomains': ['www.example.com', 'mail.example.com']
}
```

**Database Storage:**
- Creates host records for discovered IPs
- Stores DNS records in `osint_data` table
- Creates findings if zone transfer successful

---

## WordPress Tools

### wpscan_parser

**Function:** `parse_wpscan_output(output: str, target: str = "") -> Dict[str, Any]`

**Input:** WPScan text output

**Output Structure:**

```python
{
    'target_url': 'http://example.com',
    'wordpress_version': '5.8.0',
    'theme': {
        'name': 'twentytwentyone',
        'version': '1.4',
        'vulnerabilities': []
    },
    'plugins': [
        {
            'name': 'contact-form-7',
            'version': '5.4.2',
            'vulnerabilities': [
                {
                    'title': 'XSS Vulnerability',
                    'references': ['https://wpvulndb.com/...']
                }
            ]
        }
    ],
    'users': ['admin', 'editor']
}
```

**Database Storage:**
- Creates findings for vulnerabilities
- Stores usernames in credentials table
- Associates with target host

---

## Metasploit

### msf_parser

**Function:** `parse_msf_xml(xml_data: str) -> Dict[str, Any]`

**Input:** Metasploit XML export

**Output Structure:**

```python
{
    'hosts': [...],      # Similar to nmap format
    'services': [...],
    'credentials': [...],
    'loots': [...]       # Captured data/files
}
```

**Database Storage:**
- Imports into all relevant tables
- Creates host, service, credential records
- Stores loot references

---

## Parser Best Practices

### 1. Handle Partial Output

```python
def parse_tool_output(output: str, target: str = "") -> Dict[str, Any]:
    result = {
        'hosts': [],
        'findings': []
    }
    
    try:
        # Parse logic
        pass
    except Exception as e:
        # Log error but return partial results
        result['parse_error'] = str(e)
    
    return result
```

### 2. Normalize Data

```python
# Always lowercase service names
service_name = line_match.group(1).lower()

# Standardize severity
severity_map = {
    'critical': 'critical',
    'high': 'high',
    'medium': 'medium',
    'low': 'low',
    'info': 'info',
    'informational': 'info'
}
```

### 3. Extract IPs and Hostnames

```python
import re

def extract_ip(text: str) -> Optional[str]:
    match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', text)
    return match.group(0) if match else None
```

### 4. Handle Tool Version Differences

```python
# Check for both old and new format
if 'Host is up' in line or 'host up' in line:
    current_host['status'] = 'up'
```

---

## Adding New Parsers

### Step 1: Create Parser File

```python
# souleyez/parsers/newtool_parser.py

def parse_newtool_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse NewTool output.
    
    Args:
        output: Raw tool output
        target: Target from job
        
    Returns:
        Structured data dict
    """
    result = {
        'target': target,
        'findings': []
    }
    
    # Parse logic here
    
    return result
```

### Step 2: Register Parser

```python
# souleyez/engine/result_handler.py

PARSER_MAP = {
    'nmap': 'souleyez.parsers.nmap_parser.parse_nmap_text',
    'nikto': 'souleyez.parsers.nikto_parser.parse_nikto_output',
    'newtool': 'souleyez.parsers.newtool_parser.parse_newtool_output',
}
```

### Step 3: Test Parser

```python
# tests/test_newtool_parser.py

def test_parse_newtool_basic():
    output = """
    NewTool output here
    """
    result = parse_newtool_output(output, "192.168.1.100")
    
    assert result['target'] == "192.168.1.100"
    assert len(result['findings']) > 0
```

---

## Testing Parsers

### Manual Testing

```bash
# Run tool and save output
nmap -sV 192.168.1.100 > test_output.txt

# Test parser
python3 -c "
from souleyez.parsers.nmap_parser import parse_nmap_text
with open('test_output.txt') as f:
    result = parse_nmap_text(f.read())
print(result)
"
```

### Unit Testing

See: `tests/parsers/` directory

---

## Troubleshooting

### Parser Not Extracting Data

**Check:**
1. Tool output format changed?
2. Regex patterns match?
3. Tool version compatibility?

**Debug:**
```python
# Add debug prints
print(f"DEBUG: Line: {line}")
print(f"DEBUG: Match: {match}")
```

### Encoding Issues

```python
# Handle different encodings
try:
    output_decoded = output.decode('utf-8')
except UnicodeDecodeError:
    output_decoded = output.decode('latin-1', errors='replace')
```

---

## See Also

- [Integration Guide](integration-guide.md)
- [CLI Commands](cli-commands.md)
- [Developer Guide](../developer-guide/contributor-setup.md)
