# Metasploit Framework Integration

SoulEyez integrates with Metasploit Framework to provide bidirectional data synchronization and exploit result tracking.

## Quick Start

### Important Trade-offs

The MSF integration accesses Metasploit's PostgreSQL database **directly** for fast data import.

| Benefits | Risks |
|----------|-------|
| Fast bulk import of hosts, services, vulns, creds, sessions | May break with MSF updates |
| Works without MSF console running | Tested with MSF 6.2-6.4 only |
| Import historical engagement data | Not officially supported by MSF |
| Automatic exploit result tracking | Uses internal database structure |

### Built-in Protections

- Automatic version checking on connect
- Schema validation before operations
- Graceful error handling with helpful messages
- Suggests XML export as fallback when errors occur
- Optional dependencies (won't affect base installation)

### When to Use Database Integration

**Use MSF Database Integration if:**
- You run MSF locally
- You're okay with occasional maintenance
- You want fast bulk imports
- You're comfortable troubleshooting

**Use XML Export Instead if:**
- You need guaranteed stability
- Working with production MSF
- Prefer officially supported methods
- Want zero maintenance burden

---

## Installation

MSF integration dependencies are included in the base installation:

```bash
# Clone and install
git clone https://github.com/cyber-soul-security/SoulEyez.git
cd SoulEyez
pip install -e .
```

All required dependencies (including psycopg2-binary and msgpack for MSF integration) are automatically installed.

## Accessing MSF Integration

MSF Integration is a premium feature accessible from the main menu:

```
Main Menu -> [m] MSF Integration
```

The MSF Integration menu is organized into sections:
- **IMPORT** - Import data from MSF database
- **SYNC** - Synchronize exploit results and sessions
- **RESOURCE SCRIPTS** - Generate Metasploit resource (.rc) files
- **EXPORT** - Export SoulEyez data to MSF format
- **CONFIGURATION** - Database and RPC settings
- **NAVIGATION** - Back to main menu

The status bar shows your current engagement, host/service counts, msfconsole availability, and script count.

## Features

### 1. Import MSF Data

Import hosts, services, vulnerabilities, credentials, and sessions from your MSF workspace into SoulEyez.

**Access:** Main Menu -> `[m]` MSF Integration -> Import section

**Requirements:**
- MSF PostgreSQL database running
- Database credentials (default: localhost:5432, db=msf, user=msf)

**What it imports:**
- Hosts and OS information
- Services and version info
- Vulnerabilities with CVE references
- Captured credentials
- Active and closed sessions

### 2. Sync Exploit Results

Automatically update exploit attempt status based on MSF session creation and vulnerability exploitation.

**Access:** Main Menu -> `[m]` MSF Integration -> Sync section

**How it works:**
- Queries MSF for successful exploits
- Finds sessions created by specific exploits
- Updates SoulEyez exploit status to "SUCCESS"
- Links exploit attempts to their results

**Example:**
```
Before Sync:
ID   STATUS  EXPLOIT
1    -       vsftpd 2.3.4 Backdoor

After Sync (session created in MSF):
ID   STATUS  EXPLOIT
1    OK      vsftpd 2.3.4 Backdoor - Session 1 created
```

### 3. View Active Sessions

Monitor and view active MSF sessions with detailed information.

**Access:** Main Menu -> `[m]` MSF Integration -> Sessions section

**Information shown:**
- Session ID and type (shell, meterpreter, etc.)
- Target host and port
- Exploit and payload used
- Platform and architecture
- Session status and timestamps

## Configuration

### MSF Database Access

**PostgreSQL Configuration:**
```bash
# Default MSF database settings
Host:     localhost
Port:     5432
Database: msf
Username: msf
Password: (usually empty for local)
Workspace: default
```

**Find your MSF database credentials:**
```bash
# In msfconsole
msf> db_status
```

**Setting up MSF Database Password:**

If you need to set or change the MSF database password, follow these steps:

1. **Access PostgreSQL as the postgres user:**
   ```bash
   sudo -u postgres psql
   ```

2. **Set password for the msf user:**
   ```sql
   ALTER USER msf WITH PASSWORD 'your_password_here';
   ```

3. **Exit PostgreSQL:**
   ```sql
   \q
   ```

4. **Update MSF database configuration:**
   ```bash
   # Edit the database.yml file
   nano ~/.msf4/database.yml
   ```

   Update the password field:
   ```yaml
   production:
     adapter: postgresql
     database: msf
     username: msf
     password: your_password_here
     host: localhost
     port: 5432
     pool: 5
     timeout: 5
   ```

5. **Restart MSF and verify connection:**
   ```bash
   msfconsole
   msf> db_status
   ```

**Note:** The password will be required when importing MSF data into SoulEyez.

### MSF RPC Access (Optional)

For real-time session monitoring, you can enable MSF RPC:

```bash
# Start MSF RPC daemon
msfrpcd -P your_password -U msf -a 127.0.0.1 -p 55553
```

**RPC Configuration:**
```bash
Host:     127.0.0.1
Port:     55553
Username: msf
Password: your_password
```

## Architecture

### Database Access
- Direct PostgreSQL connection to MSF database
- Fast bulk imports of historical data
- Works even when msfconsole is not running
- Read-only access (no modifications to MSF data)

### RPC API Access
- Real-time session monitoring
- Execute modules programmatically
- Manage jobs and consoles
- Requires msfrpcd daemon running

## Workflow Example

### Scenario: Exploiting VSFTPD Backdoor

**1. Run Exploit in MSF:**
```bash
msf> use exploit/unix/ftp/vsftpd_234_backdoor
msf> set RHOSTS 10.0.0.82
msf> run
[+] 10.0.0.82:21 - UID: uid=0(root) gid=0(root)
[*] Command shell session 1 opened
```

**2. Import into SoulEyez:**
- Main Menu -> `[m]` MSF Integration
- Select "Import from MSF DB"
- Select workspace: "default"
- Import: hosts, services, vulns, sessions
- Result: Host 10.0.0.82, FTP service, VSFTPD vuln, and Session 1 imported

**3. Sync Exploit Results:**
- Main Menu -> `[m]` MSF Integration
- Select "Sync Exploit Results"
- System finds Session 1 was created via vsftpd_234_backdoor
- Exploit status updated to SUCCESS

**4. View in SoulEyez:**
```
Service View -> FTP:21 on 10.0.0.82:

ID   STATUS  ACTION   SEVERITY  EXPLOIT
1    OK      SUCCESS  CRITICAL  vsftpd 2.3.4 Backdoor Command Execution
                                Session 1 (root shell) - uid=0(root)
```

## Troubleshooting

### "psycopg2 not available"
```bash
pip install psycopg2-binary
```

### "msgpack not available"
```bash
pip install msgpack
```

### "Connection failed: FATAL: password authentication failed"
Check your MSF database credentials:
```bash
# In MSF console
msf> db_status
```

### "Database not initialized" or "postgresql selected, no connection"

The Metasploit database needs to be initialized before use. SoulEyez will automatically detect this when launching msfconsole and offer to fix it.

**Manual fix:**
```bash
# Initialize the MSF database (run as non-root user)
msfdb init
```

This creates the PostgreSQL database and configures Metasploit to connect automatically.

### "PostgreSQL not running"

The PostgreSQL service needs to be running for database connectivity.

**Manual fix:**
```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Enable auto-start on boot (optional)
sudo systemctl enable postgresql
```

### "Workspace 'xyz' not found"
List available workspaces:
```bash
# In MSF console
msf> workspace -l
```

### "Schema error" or "MSF database schema may have changed"

This indicates MSF's database structure has changed (usually after a major update).

**Immediate Solutions:**

1. **Use XML Export** (most reliable):
   ```bash
   # In msfconsole
   msf> db_export -f xml /tmp/msf_export.xml

   # Import the XML in SoulEyez (if XML importer is available)
   ```

2. **Check MSF Version**:
   ```bash
   msfconsole --version
   ```
   - If version is > 6.4, the schema may have changed
   - Check SoulEyez releases for updated integration

3. **Report the Issue**:
   - Create a GitHub issue with your MSF version
   - Include the error message
   - This helps maintainers update the integration

**What the Integration Does:**
- Automatically checks MSF version on connect
- Validates database schema before operations
- Provides helpful error messages when schema changes detected
- Suggests XML export as fallback

### "MSF version X.Y has not been tested"

You'll see this warning when connecting to an untested MSF version.

**What to do:**
- If import works: Great! The schema is compatible
- If you get errors: Use XML export instead
- Report success/failure to help maintain compatibility list

## Security Considerations

### Database Access
- Credentials are requested interactively (not stored)
- Connection is local by default (localhost)
- Read-only access to MSF database
- Queries are parameterized (SQL injection safe)

### Best Practices
- Use localhost connections when possible
- Keep MSF database on trusted networks
- Use strong RPC passwords if enabling msfrpcd
- Review imported data before using in reports

## Limitations

### Database Schema Coupling
- Integration relies on MSF's PostgreSQL schema
- Major MSF updates may require code updates
- Tested with MSF 6.x series

### Alternative: XML Import

For a more stable (but manual) approach, use MSF's export feature:
```bash
# In MSF console
msf> db_export -f xml /tmp/msf_export.xml

# Then use SoulEyez XML import (if implemented)
```

## Future Enhancements

Potential improvements:
- Automatic exploit execution via RPC
- Session command execution from SoulEyez
- Live session monitoring dashboard
- MSF module search integration
- Automated attack chain execution
- Resource script generation from SoulEyez findings

## Dependencies

- `psycopg2-binary>=2.9.0` - PostgreSQL database adapter
- `msgpack>=1.0.0` - MSF RPC message serialization

Both are optional and only required for MSF integration features.
