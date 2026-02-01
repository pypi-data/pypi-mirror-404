# Integration Guide for Adding New Tool Parsers

## Overview

This guide walks you through the complete process of integrating a new security tool into souleyez, from parser creation to testing.

---

## Integration Checklist

- [ ] Understand tool output format
- [ ] Create parser module
- [ ] Register parser in result handler
- [ ] Create tool plugin (optional)
- [ ] Write tests
- [ ] Update documentation
- [ ] Submit pull request

---

## Prerequisites

**Required Knowledge:**
- Python 3.8+
- Regular expressions
- Tool output formats
- Database basics

**Tools:**
- Text editor/IDE
- Security tool to integrate
- Test target/environment

---

## Step 1: Analyze Tool Output

### 1.1 Run Tool and Capture Output

```bash
# Example: New tool called "portscan"
portscan 192.168.1.100 > sample_output.txt
```

### 1.2 Study Output Format

**Example Output:**
```
PortScan v1.0 - Network Scanner
Target: 192.168.1.100
Scanning...

OPEN PORTS:
Port 22   - SSH    - OpenSSH 8.2
Port 80   - HTTP   - Apache 2.4
Port 443  - HTTPS  - Apache 2.4

Scan completed in 5.2 seconds
```

### 1.3 Identify Key Data

**What to extract:**
- Target IP/hostname
- Open ports
- Service names
- Service versions
- Additional metadata

---

## Step 2: Create Parser Module

### 2.1 Create Parser File

**Location:** `souleyez/parsers/portscan_parser.py`

```python
#!/usr/bin/env python3
"""
souleyez.parsers.portscan_parser

Parses PortScan output into structured data.
"""
import re
from typing import Dict, List, Any, Optional


def parse_portscan_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse PortScan text output.
    
    Args:
        output: Raw PortScan output text
        target: Target IP/hostname from job
        
    Returns:
        Dict with structure:
        {
            'hosts': [
                {
                    'ip': '192.168.1.100',
                    'hostname': None,
                    'status': 'up',
                    'services': [
                        {
                            'port': 22,
                            'protocol': 'tcp',
                            'state': 'open',
                            'service': 'ssh',
                            'version': 'OpenSSH 8.2'
                        }
                    ]
                }
            ]
        }
    """
    result = {
        'hosts': []
    }
    
    # Extract target
    target_match = re.search(r'Target:\s+(\S+)', output)
    if not target_match:
        return result
    
    target_ip = target_match.group(1)
    
    # Initialize host
    host = {
        'ip': target_ip,
        'hostname': None,
        'status': 'up',
        'services': []
    }
    
    # Extract services
    # Pattern: "Port 22   - SSH    - OpenSSH 8.2"
    service_pattern = r'Port\s+(\d+)\s+-\s+(\S+)\s+-\s+(.+)'
    
    for line in output.split('\n'):
        match = re.match(service_pattern, line)
        if match:
            port = int(match.group(1))
            service_name = match.group(2).lower()
            version = match.group(3).strip()
            
            service = {
                'port': port,
                'protocol': 'tcp',  # Assume TCP unless tool specifies
                'state': 'open',
                'service': service_name,
                'version': version
            }
            
            host['services'].append(service)
    
    # Only add host if services found
    if host['services']:
        result['hosts'].append(host)
    
    return result
```

### 2.2 Parser Template

Use this template for all parsers:

```python
#!/usr/bin/env python3
"""
souleyez.parsers.<tool>_parser

Brief description of what tool does.
"""
import re
from typing import Dict, List, Any, Optional


def parse_<tool>_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse <Tool> output.
    
    Args:
        output: Raw tool output text
        target: Target from job (IP, URL, domain, etc.)
        
    Returns:
        Dict with structured data
    """
    # Initialize result structure
    result = {
        'hosts': [],
        'findings': [],
        # Add other relevant keys
    }
    
    # Parse logic here
    lines = output.split('\n')
    for line in lines:
        line = line.strip()
        # Parsing code
    
    return result
```

---

## Step 3: Register Parser

### 3.1 Update Result Handler

**File:** `souleyez/engine/result_handler.py`

**Add to PARSER_MAP:**

```python
PARSER_MAP = {
    'nmap': 'souleyez.parsers.nmap_parser.parse_nmap_text',
    'nikto': 'souleyez.parsers.nikto_parser.parse_nikto_output',
    'gobuster': 'souleyez.parsers.gobuster_parser.parse_gobuster_output',
    'portscan': 'souleyez.parsers.portscan_parser.parse_portscan_output',  # NEW
    # ... other parsers
}
```

### 3.2 How Parser is Called

When a job completes, the result handler:

1. Reads job log file
2. Looks up parser in PARSER_MAP
3. Calls parser function with output
4. Stores structured data in database

```python
# Pseudocode of result handling
def handle_job_result(job):
    log_output = read_log(job['log'])
    parser_func = get_parser(job['tool'])
    
    if parser_func:
        data = parser_func(log_output, job['target'])
        store_in_database(data, job['engagement_id'])
```

---

## Step 4: Create Tool Plugin (Optional)

Plugins provide:
- Custom execution logic
- Argument preprocessing
- Real-time output handling
- Better integration

### 4.1 Create Plugin File

**Location:** `souleyez/plugins/portscan.py`

```python
#!/usr/bin/env python3
"""
souleyez.plugins.portscan

Plugin for PortScan integration.
"""
import subprocess
from pathlib import Path


class PortScanPlugin:
    """Plugin for PortScan tool."""
    
    name = "portscan"
    description = "Network port scanner"
    
    def run(self, target: str, args: list, label: str, log_path: str) -> int:
        """
        Execute portscan with custom logic.
        
        Args:
            target: Target IP/hostname
            args: Additional arguments
            label: Job label
            log_path: Path to write log output
            
        Returns:
            Exit code (0 = success)
        """
        # Build command
        cmd = ['portscan', target] + args
        
        # Execute and capture output
        with open(log_path, 'w') as log_file:
            result = subprocess.run(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                timeout=300
            )
        
        return result.returncode
    
    def presets(self) -> dict:
        """
        Return common command presets.
        
        Returns:
            Dict of preset_name: args_list
        """
        return {
            'Quick Scan': ['-fast'],
            'Full Scan': ['-all-ports'],
            'Stealth Scan': ['-stealth', '-slow']
        }
    
    def validate_target(self, target: str) -> bool:
        """
        Validate target format.
        
        Args:
            target: Target to validate
            
        Returns:
            True if valid, False otherwise
        """
        import re
        # Check if valid IP or hostname
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        return bool(re.match(ip_pattern, target)) or len(target) > 0
```

### 4.2 Register Plugin

**File:** `souleyez/engine/loader.py`

```python
PLUGINS = {
    'nmap': NmapPlugin,
    'nikto': NiktoPlugin,
    'portscan': PortScanPlugin,  # NEW
    # ... other plugins
}
```

---

## Step 5: Write Tests

### 5.1 Create Test File

**Location:** `tests/parsers/test_portscan_parser.py`

```python
#!/usr/bin/env python3
"""
Tests for PortScan parser.
"""
import pytest
from souleyez.parsers.portscan_parser import parse_portscan_output


def test_parse_basic_output():
    """Test parsing basic PortScan output."""
    output = """
PortScan v1.0 - Network Scanner
Target: 192.168.1.100
Scanning...

OPEN PORTS:
Port 22   - SSH    - OpenSSH 8.2
Port 80   - HTTP   - Apache 2.4
Port 443  - HTTPS  - Apache 2.4

Scan completed in 5.2 seconds
"""
    
    result = parse_portscan_output(output, "192.168.1.100")
    
    # Assertions
    assert len(result['hosts']) == 1
    assert result['hosts'][0]['ip'] == '192.168.1.100'
    assert result['hosts'][0]['status'] == 'up'
    assert len(result['hosts'][0]['services']) == 3
    
    # Check first service
    service = result['hosts'][0]['services'][0]
    assert service['port'] == 22
    assert service['service'] == 'ssh'
    assert service['version'] == 'OpenSSH 8.2'


def test_parse_empty_output():
    """Test parsing empty output."""
    output = ""
    result = parse_portscan_output(output)
    assert result['hosts'] == []


def test_parse_no_services():
    """Test parsing output with no open ports."""
    output = """
PortScan v1.0
Target: 192.168.1.100
No open ports found
"""
    
    result = parse_portscan_output(output, "192.168.1.100")
    assert len(result['hosts']) == 0  # No host if no services


def test_parse_multiple_hosts():
    """Test parsing multiple hosts (if tool supports)."""
    # TODO: Add test case
    pass
```

### 5.2 Run Tests

```bash
# Run all parser tests
pytest tests/parsers/

# Run specific test
pytest tests/parsers/test_portscan_parser.py

# Run with coverage
pytest --cov=souleyez.parsers tests/parsers/
```

---

## Step 6: Integration Testing

### 6.1 Manual End-to-End Test

```bash
# 1. Create test engagement
souleyez engagement create "Parser Test"
souleyez engagement use "Parser Test"

# 2. Run tool via souleyez
souleyez jobs enqueue portscan 192.168.1.100 -l "Test Scan"

# 3. Check job status
souleyez jobs list

# 4. Verify data was stored
souleyez hosts list
souleyez services list

# 5. Check raw output
souleyez jobs show <job_id>
```

### 6.2 Verify Database Storage

```bash
sqlite3 data/souleyez.db

sqlite> SELECT * FROM hosts WHERE engagement_id = 1;
sqlite> SELECT * FROM services WHERE host_id = 1;
sqlite> .quit
```

---

## Step 7: Documentation

### 7.1 Update Parser Formats Doc

**File:** `docs/api-reference/parser-formats.md`

**Add section:**

```markdown
### portscan_parser

**Function:** `parse_portscan_output(output: str, target: str = "") -> Dict[str, Any]`

**Input:** PortScan text output

**Expected Arguments:**
- Target IP or hostname

**Output Structure:**
[Document your parser's output structure]

**Database Storage:**
- Creates/updates records in `hosts` table
- Creates records in `services` table

**Example Input:**
[Provide example]
```

### 7.2 Update CLI Commands Doc

If tool has special commands or presets, document in:
**File:** `docs/api-reference/cli-commands.md`

---

## Step 8: Submit Pull Request

### 8.1 Git Workflow

```bash
# Create feature branch
git checkout -b feature/add-portscan-parser

# Add files
git add souleyez/parsers/portscan_parser.py
git add souleyez/plugins/portscan.py
git add tests/parsers/test_portscan_parser.py
git add docs/api-reference/parser-formats.md

# Commit with descriptive message
git commit -m "Add PortScan parser and plugin

- Created parser for PortScan output
- Added plugin with presets
- Added comprehensive tests
- Updated documentation"

# Push branch
git push origin feature/add-portscan-parser

# Create pull request on GitHub
```

### 8.2 PR Description Template

```markdown
## Description
Adds support for PortScan tool integration.

## Changes
- [ ] Parser module (`portscan_parser.py`)
- [ ] Plugin module (`portscan.py`) [if applicable]
- [ ] Unit tests
- [ ] Documentation updates

## Testing
- Tested with PortScan v1.0
- All tests passing
- Manual integration test completed

## Sample Output
[Paste sample tool output]

## Related Issues
Closes #123
```

---

## Common Patterns

### Pattern 1: Extract IP Addresses

```python
import re

def extract_ip(text: str) -> Optional[str]:
    """Extract first IPv4 address from text."""
    match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', text)
    return match.group(0) if match else None
```

### Pattern 2: Parse Key-Value Lines

```python
def parse_metadata(lines: List[str]) -> Dict[str, str]:
    """Parse 'Key: Value' formatted lines."""
    metadata = {}
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip().lower()] = value.strip()
    return metadata
```

### Pattern 3: Handle Multiple Sections

```python
def parse_sections(output: str) -> Dict[str, List[str]]:
    """Parse output with multiple sections."""
    sections = {}
    current_section = None
    
    for line in output.split('\n'):
        if line.isupper() and line.endswith(':'):
            # New section header
            current_section = line[:-1].lower()
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(line)
    
    return sections
```

### Pattern 4: Severity Mapping

```python
def map_severity(description: str) -> str:
    """Map finding description to severity level."""
    desc_lower = description.lower()
    
    if any(word in desc_lower for word in ['critical', 'exploit', 'rce']):
        return 'critical'
    elif any(word in desc_lower for word in ['high', 'sql injection', 'xss']):
        return 'high'
    elif any(word in desc_lower for word in ['medium', 'csrf', 'weak']):
        return 'medium'
    elif any(word in desc_lower for word in ['low', 'info disclosure']):
        return 'low'
    else:
        return 'info'
```

---

## Troubleshooting

### Issue: Parser Not Being Called

**Check:**
1. Parser registered in `PARSER_MAP`?
2. Tool name matches exactly?
3. Parser function signature correct?

**Debug:**
```python
# Add logging to result_handler.py
import logging
logging.debug(f"Looking up parser for tool: {tool_name}")
logging.debug(f"Found parser: {parser_func}")
```

### Issue: Data Not Stored in Database

**Check:**
1. Parser returning correct structure?
2. Host has 'ip' field?
3. Services have required fields (port, protocol, state)?

**Debug:**
```python
# Print parser output
result = parse_tool_output(output, target)
print(f"Parser result: {result}")
```

### Issue: Regex Not Matching

**Check:**
1. Sample output matches real output?
2. Whitespace differences?
3. Tool version differences?

**Debug:**
```python
# Test regex interactively
import re
pattern = r'Port\s+(\d+)'
test_line = "Port 22   - SSH"
match = re.match(pattern, test_line)
print(f"Match: {match}")
if match:
    print(f"Groups: {match.groups()}")
```

---

## Best Practices

### 1. Fail Gracefully

```python
def parse_tool_output(output: str, target: str = "") -> Dict[str, Any]:
    result = {'hosts': [], 'findings': []}
    
    try:
        # Parsing logic
        pass
    except Exception as e:
        # Log error but return partial results
        import logging
        logging.error(f"Parser error: {e}")
        result['parse_error'] = str(e)
    
    return result
```

### 2. Validate Input

```python
if not output or not output.strip():
    return {'hosts': [], 'findings': []}

if 'error' in output.lower() or 'failed' in output.lower():
    # Tool reported error, minimal parsing
    return {'hosts': [], 'findings': []}
```

### 3. Normalize Data

```python
# Consistent formatting
service_name = service_name.lower().strip()
ip_address = ip_address.strip()
port = int(port)  # Ensure integer
```

### 4. Document Edge Cases

```python
def parse_tool_output(output: str, target: str = "") -> Dict[str, Any]:
    """
    Parse tool output.
    
    Edge cases handled:
    - Multiple hosts in output
    - Missing version information
    - IPv6 addresses (converted to IPv4 if possible)
    - Tool errors/warnings (logged but not fatal)
    """
    pass
```

---

## Example: Complete Integration

See complete example in `docs/examples/parser-integration-example.md` (TODO)

---

## Getting Help

- **GitHub Discussions**: Ask integration questions
- **Discord/Slack**: Real-time help (if available)
- **Email**: security@souleyez.dev (TODO)

---

## See Also

- [Parser Formats Reference](parser-formats.md)
- [CLI Commands Reference](cli-commands.md)
- [Developer Guide](../developer-guide/contributor-setup.md)
- [Testing Guide](../developer-guide/testing-guide.md) (TODO)
