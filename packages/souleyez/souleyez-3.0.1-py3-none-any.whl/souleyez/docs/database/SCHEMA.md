# Database Schema Documentation

## Overview
SoulEyez uses SQLite for data storage with a normalized relational schema designed for penetration testing workflow management.

**Schema Version**: 1.0  
**Database File**: `~/.souleyez/souleyez.db` (configurable)  
**Format**: SQLite 3  
**Foreign Keys**: Enabled by default

## Tables

### engagements
Top-level container for penetration test engagements.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment unique ID |
| name | TEXT | UNIQUE, NOT NULL | Engagement identifier |
| description | TEXT | | Optional engagement description |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

**Purpose**: Isolates data between different security assessments  
**Relationships**: Parent to hosts, findings, and osint_data

---

### hosts
Individual hosts/targets discovered during an engagement.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment unique ID |
| engagement_id | INTEGER | FK → engagements, NOT NULL | Parent engagement |
| ip_address | TEXT | NOT NULL | IP address |
| hostname | TEXT | | Resolved hostname |
| os_name | TEXT | | Detected operating system |
| os_accuracy | INTEGER | | OS detection confidence (0-100) |
| mac_address | TEXT | | MAC address (if available) |
| status | TEXT | DEFAULT 'up' | Host status (up/down) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Discovery timestamp |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

**Unique Constraint**: (engagement_id, ip_address) - prevents duplicate IPs per engagement  
**Foreign Keys**:
- engagement_id → engagements(id) ON DELETE CASCADE

**Purpose**: Tracks all discovered targets  
**Relationships**: Parent to services, findings, web_paths, smb_shares

---

### services
Network services running on hosts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment unique ID |
| host_id | INTEGER | FK → hosts, NOT NULL | Parent host |
| port | INTEGER | NOT NULL | Port number |
| protocol | TEXT | DEFAULT 'tcp' | Protocol (tcp/udp) |
| state | TEXT | DEFAULT 'open' | Port state |
| service_name | TEXT | | Service name (http, ssh, etc) |
| service_version | TEXT | | Service version string |
| service_product | TEXT | | Product name |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Discovery timestamp |

**Unique Constraint**: (host_id, port, protocol) - prevents duplicate services per host  
**Foreign Keys**:
- host_id → hosts(id) ON DELETE CASCADE

**Purpose**: Tracks discovered network services for vulnerability assessment  
**Relationships**: Parent to findings

---

### findings
Security findings and vulnerabilities discovered.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment unique ID |
| engagement_id | INTEGER | FK → engagements, NOT NULL | Parent engagement |
| host_id | INTEGER | FK → hosts | Related host (optional) |
| service_id | INTEGER | FK → services | Related service (optional) |
| finding_type | TEXT | NOT NULL | Finding category |
| severity | TEXT | DEFAULT 'info' | Severity level (critical/high/medium/low/info) |
| title | TEXT | NOT NULL | Finding title |
| description | TEXT | | Detailed description |
| evidence | TEXT | | Supporting evidence |
| refs | TEXT | | References (CVEs, URLs) |
| port | INTEGER | | Associated port number |
| path | TEXT | | Associated URL path |
| tool | TEXT | | Tool that discovered finding |
| scan_id | INTEGER | | Scan session identifier |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Discovery timestamp |

**Foreign Keys**:
- engagement_id → engagements(id) ON DELETE CASCADE
- host_id → hosts(id) ON DELETE SET NULL
- service_id → services(id) ON DELETE SET NULL

**Purpose**: Central repository for all security findings  
**Note**: host_id and service_id use SET NULL to preserve findings even if target is deleted

---

### web_paths
Discovered web paths and directories.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment unique ID |
| host_id | INTEGER | FK → hosts, NOT NULL | Parent host |
| url | TEXT | NOT NULL | Full URL path |
| status_code | INTEGER | | HTTP response code |
| content_length | INTEGER | | Response size in bytes |
| redirect | TEXT | | Redirect target (if applicable) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Discovery timestamp |

**Foreign Keys**:
- host_id → hosts(id) ON DELETE CASCADE

**Purpose**: Tracks web application structure from directory brute-forcing  
**Use Case**: Gobuster, dirb, dirbuster results

---

### osint_data
OSINT (Open Source Intelligence) information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment unique ID |
| engagement_id | INTEGER | FK → engagements, NOT NULL | Parent engagement |
| data_type | TEXT | NOT NULL | Data category (email, domain, ip, etc) |
| value | TEXT | NOT NULL | OSINT value |
| source | TEXT | | Data source tool/service |
| summary | TEXT | | Brief summary |
| content | TEXT | | Full content/details |
| metadata | TEXT | | Additional JSON metadata |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Discovery timestamp |

**Foreign Keys**:
- engagement_id → engagements(id) ON DELETE CASCADE

**Purpose**: Stores reconnaissance data from OSINT tools  
**Use Case**: theHarvester, Shodan, DNS enumeration results

---

### smb_shares
SMB/CIFS network shares discovered.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment unique ID |
| host_id | INTEGER | FK → hosts, NOT NULL | Parent host |
| share_name | TEXT | NOT NULL | Share name |
| share_type | TEXT | | Share type |
| permissions | TEXT | | Access permissions |
| comment | TEXT | | Share comment/description |
| readable | INTEGER | DEFAULT 0 | 1 if readable, 0 otherwise |
| writable | INTEGER | DEFAULT 0 | 1 if writable, 0 otherwise |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Discovery timestamp |

**Unique Constraint**: (host_id, share_name) - prevents duplicate shares per host  
**Foreign Keys**:
- host_id → hosts(id) ON DELETE CASCADE

**Purpose**: Tracks accessible SMB shares for data exfiltration opportunities  
**Use Case**: enum4linux, smbclient, CrackMapExec results

---

### smb_files
Files within SMB shares.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment unique ID |
| share_id | INTEGER | FK → smb_shares, NOT NULL | Parent share |
| path | TEXT | NOT NULL | File path within share |
| size | INTEGER | | File size in bytes |
| timestamp | TEXT | | File modification timestamp |
| is_directory | INTEGER | DEFAULT 0 | 1 if directory, 0 if file |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Discovery timestamp |

**Foreign Keys**:
- share_id → smb_shares(id) ON DELETE CASCADE

**Purpose**: Catalogs interesting files in SMB shares  
**Use Case**: Tracks files discovered during SMB enumeration

---

## Indexes

### Performance Indexes (14 total)

| Index Name | Table | Columns | Purpose |
|------------|-------|---------|---------|
| idx_hosts_engagement | hosts | engagement_id | Fast host lookup by engagement |
| idx_hosts_ip | hosts | ip_address | Fast host lookup by IP |
| idx_services_host | services | host_id | Fast service lookup by host |
| idx_services_port | services | port | Find all hosts with specific port open |
| idx_services_name | services | service_name | Find hosts running specific service |
| idx_findings_engagement | findings | engagement_id | Fast finding lookup by engagement |
| idx_findings_host | findings | host_id | Fast finding lookup by host |
| idx_findings_severity | findings | severity | Filter findings by severity |
| idx_web_paths_host | web_paths | host_id | Fast path lookup by host |
| idx_web_paths_url | web_paths | url | Search for specific URLs |
| idx_osint_engagement | osint_data | engagement_id | Fast OSINT lookup by engagement |
| idx_osint_type | osint_data | data_type | Filter OSINT by type |
| idx_smb_shares_host | smb_shares | host_id | Fast share lookup by host |
| idx_smb_files_share | smb_files | share_id | Fast file lookup by share |

---

## Relationships Summary

```
engagements (1) ──────── (*) hosts
    │                       │
    │                       ├──── (*) services
    │                       │         │
    │                       │         └──── (*) findings
    │                       │
    │                       ├──── (*) web_paths
    │                       │
    │                       └──── (*) smb_shares
    │                                   │
    │                                   └──── (*) smb_files
    │
    ├──── (*) findings
    │
    └──── (*) osint_data
```

---

## Data Integrity

### Foreign Key Behavior

**CASCADE DELETE**: Child records automatically deleted
- Deleting engagement → removes hosts, findings, osint_data
- Deleting host → removes services, web_paths, smb_shares
- Deleting service → sets findings.service_id to NULL
- Deleting smb_share → removes smb_files

**SET NULL**: Child records preserved, FK nulled
- Deleting host → findings kept with host_id=NULL
- Deleting service → findings kept with service_id=NULL

### Unique Constraints

Prevent duplicate data entry:
- Engagement names must be globally unique
- IP addresses must be unique per engagement
- Service ports must be unique per host/protocol combination
- SMB share names must be unique per host

---

## Migration System

Schema changes are managed through the migration system. See [MIGRATIONS.md](./MIGRATIONS.md) for details.

Current schema defined in: `souleyez/storage/schema.sql`

---

## See Also

- [Schema ERD Diagram](./SCHEMA_ERD.md) - Visual relationship diagram
- [Migration Guide](./MIGRATIONS.md) - How to update schema
- [Database API](../../souleyez/storage/README.md) - Python API documentation
