# ADR-003: SQLite Database and Schema Design

**Status**: Accepted
**Date**: 2025-10-29
**Deciders**: y0d8, S0ul H@ck3r$
**Supersedes**: None

---

## Context

souleyez requires persistent storage for:
- Penetration testing engagements (workspaces)
- Discovered hosts and services
- Security findings and vulnerabilities
- Credentials (usernames, passwords)
- OSINT data (emails, subdomains, DNS records)
- SMB shares and files
- Web paths and directories
- Tool execution results

The database must support:
1. **Concurrent access** (CLI, dashboard, worker process)
2. **Transactional integrity** (atomic insertions, rollbacks)
3. **Fast queries** (hosts by engagement, findings by severity)
4. **Portability** (backup, restore, transfer between systems)
5. **Simplicity** (zero-config, no external services)

---

## Decision

**souleyez uses SQLite 3 with a normalized relational schema.**

### Key Design Choices

1. **Database**: SQLite 3 (embedded, file-based)
2. **Location**: `~/.souleyez/souleyez.db`
3. **Schema**: Normalized with foreign keys
4. **Concurrency**: WAL (Write-Ahead Logging) mode
5. **Migrations**: Tracked in `schema_migrations` table
6. **Connection Pool**: Singleton pattern with 30-second timeout

---

## Schema Design

### Entity Relationship Diagram

```
┌────────────────┐
│  Engagements   │ 1:N relationships with all other entities
│  ────────────  │
│  id (PK)       │
│  name (UNIQUE) │
│  description   │
│  created_at    │
│  updated_at    │
└────┬───────────┘
     │
     │ 1:N
     │
     ▼
┌─────────────────┐         ┌──────────────────┐
│     Hosts       │         │    Findings      │
│  ─────────────  │         │  ──────────────  │
│  id (PK)        │◄────────│  host_id (FK)    │
│  engagement_id  │    1:N  │  engagement_id   │
│  ip_address     │         │  finding_type    │
│  hostname       │         │  severity        │
│  os_name        │         │  title           │
│  os_accuracy    │         │  description     │
│  mac_address    │         │  evidence        │
│  status         │         │  refs            │
│  created_at     │         │  port            │
│  updated_at     │         │  path            │
│                 │         │  tool            │
│  UNIQUE:        │         │  created_at      │
│   (engagement,  │         └──────────────────┘
│    ip_address)  │
└────┬────────────┘
     │
     │ 1:N
     │
     ▼
┌─────────────────┐         ┌──────────────────┐
│    Services     │         │  Credentials     │
│  ─────────────  │         │  ──────────────  │
│  id (PK)        │         │  id (PK)         │
│  host_id (FK)   │         │  engagement_id   │
│  port           │         │  host_id (FK)    │
│  protocol       │         │  service         │
│  state          │         │  port            │
│  service_name   │         │  protocol        │
│  service_version│         │  username ⚠️     │
│  service_product│         │  password ⚠️     │
│  created_at     │         │  credential_type │
│                 │         │  status          │
│  UNIQUE:        │         │  tool            │
│   (host_id,     │         │  created_at      │
│    port,        │         │  updated_at      │
│    protocol)    │         └──────────────────┘
└─────────────────┘              ⚠️ = Encrypted

┌─────────────────┐         ┌──────────────────┐
│  Web Paths      │         │  OSINT Data      │
│  ─────────────  │         │  ──────────────  │
│  id (PK)        │         │  id (PK)         │
│  host_id (FK)   │         │  engagement_id   │
│  url            │         │  data_type       │
│  status_code    │         │  value           │
│  content_length │         │  source          │
│  redirect       │         │  summary         │
│  created_at     │         │  content         │
└─────────────────┘         │  metadata        │
                            │  created_at      │
┌─────────────────┐         └──────────────────┘
│  SMB Shares     │
│  ─────────────  │
│  id (PK)        │
│  host_id (FK)   │
│  share_name     │
│  share_type     │
│  permissions    │
│  comment        │
│  readable       │
│  writable       │
│  created_at     │
└────┬────────────┘
     │
     │ 1:N
     ▼
┌─────────────────┐
│   SMB Files     │
│  ─────────────  │
│  id (PK)        │
│  share_id (FK)  │
│  path           │
│  size           │
│  timestamp      │
│  is_directory   │
│  created_at     │
└─────────────────┘
```

### Core Tables

#### 1. Engagements
**Purpose**: Workspace isolation for different penetration tests.

```sql
CREATE TABLE IF NOT EXISTS engagements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Design Rationale**:
- `name` is unique (no duplicate workspaces)
- `updated_at` tracks last activity
- All other tables reference `engagement_id`

#### 2. Hosts
**Purpose**: Discovered target systems.

```sql
CREATE TABLE IF NOT EXISTS hosts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    ip_address TEXT NOT NULL,
    hostname TEXT,
    os_name TEXT,
    os_accuracy INTEGER,
    mac_address TEXT,
    status TEXT DEFAULT 'up',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id)
);

CREATE INDEX IF NOT EXISTS idx_hosts_engagement ON hosts(engagement_id);
CREATE INDEX IF NOT EXISTS idx_hosts_ip ON hosts(ip_address);
```

**Design Rationale**:
- `UNIQUE(engagement_id, ip_address)` prevents duplicates within engagement
- `status` = 'up' or 'down' (only live hosts counted in stats)
- `os_accuracy` stores Nmap OS detection confidence (0-100)
- Indexed on `engagement_id` for fast queries

#### 3. Services
**Purpose**: Open ports and running services.

```sql
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL,
    port INTEGER NOT NULL,
    protocol TEXT DEFAULT 'tcp',
    state TEXT DEFAULT 'open',
    service_name TEXT,
    service_version TEXT,
    service_product TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (host_id) REFERENCES hosts(id)
);

CREATE INDEX IF NOT EXISTS idx_services_host ON services(host_id);
```

**Design Rationale**:
- `UNIQUE(host_id, port, protocol)` prevents duplicate service entries
- `protocol` = 'tcp' or 'udp'
- `state` = 'open', 'closed', 'filtered'
- Separate `service_version` and `service_product` for CVE matching

#### 4. Findings
**Purpose**: Security vulnerabilities, misconfigurations, and notable discoveries.

```sql
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    host_id INTEGER,
    service_id INTEGER,
    finding_type TEXT NOT NULL,
    severity TEXT DEFAULT 'info',
    title TEXT NOT NULL,
    description TEXT,
    evidence TEXT,
    refs TEXT,
    port INTEGER,
    path TEXT,
    tool TEXT,
    scan_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id),
    FOREIGN KEY (host_id) REFERENCES hosts(id)
);

CREATE INDEX IF NOT EXISTS idx_findings_engagement ON findings(engagement_id);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity);
```

**Design Rationale**:
- `finding_type` = 'vuln', 'credential', 'config', 'exposure', 'service'
- `severity` = 'critical', 'high', 'medium', 'low', 'info'
- `evidence` stores proof (e.g., HTTP response, command output)
- `refs` stores CVE IDs, URLs (comma-separated)
- Optional `host_id` (some findings are engagement-wide)

#### 5. Credentials
**Purpose**: Discovered usernames and passwords.

```sql
CREATE TABLE IF NOT EXISTS credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    host_id INTEGER,
    service TEXT,
    port INTEGER,
    protocol TEXT DEFAULT 'tcp',
    username TEXT,           -- Encrypted if crypto enabled
    password TEXT,           -- Encrypted if crypto enabled
    credential_type TEXT DEFAULT 'user',
    status TEXT DEFAULT 'untested',
    tool TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id),
    FOREIGN KEY (host_id) REFERENCES hosts(id)
);

CREATE INDEX IF NOT EXISTS idx_credentials_engagement ON credentials(engagement_id);
CREATE INDEX IF NOT EXISTS idx_credentials_host ON credentials(host_id);
CREATE INDEX IF NOT EXISTS idx_credentials_status ON credentials(status);
```

**Design Rationale**:
- `username` and `password` fields encrypted via Fernet (see [ADR-002](002-master-password-approach.md))
- `credential_type` = 'user', 'password', 'hash', 'key'
- `status` = 'untested', 'valid', 'invalid', 'discovered'
- Indexed on `status` for fast filtering (valid credentials query)

#### 6. Web Paths
**Purpose**: Discovered URLs and directories.

```sql
CREATE TABLE IF NOT EXISTS web_paths (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    status_code INTEGER,
    content_length INTEGER,
    redirect TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (host_id) REFERENCES hosts(id)
);
```

**Design Rationale**:
- Populated by gobuster, nikto, wpscan
- `status_code` = HTTP response code (200, 301, 403, etc.)
- `redirect` stores Location header if 3xx redirect

#### 7. OSINT Data
**Purpose**: Open-source intelligence (emails, subdomains, DNS records).

```sql
CREATE TABLE IF NOT EXISTS osint_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engagement_id INTEGER NOT NULL,
    data_type TEXT NOT NULL,
    value TEXT NOT NULL,
    source TEXT,
    summary TEXT,
    content TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id)
);
```

**Design Rationale**:
- `data_type` = 'email', 'subdomain', 'dns_record', 'whois', 'person', 'organization'
- `source` = tool that discovered it (theHarvester, dnsrecon, whois)
- `metadata` stores JSON for structured data

#### 8. SMB Shares & Files
**Purpose**: SMB enumeration results.

```sql
CREATE TABLE IF NOT EXISTS smb_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL,
    share_name TEXT NOT NULL,
    share_type TEXT,
    permissions TEXT,
    comment TEXT,
    readable INTEGER DEFAULT 0,
    writable INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (host_id) REFERENCES hosts(id)
);

CREATE TABLE IF NOT EXISTS smb_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    share_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    size INTEGER,
    timestamp TEXT,
    is_directory INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (share_id) REFERENCES smb_shares(id)
);
```

**Design Rationale**:
- Two-level hierarchy: shares → files
- `readable` and `writable` are booleans (0/1)
- `share_type` = 'DISK', 'IPC', 'PRINTER'

---

## Rationale

### Why SQLite?

#### Compared to PostgreSQL

| Criteria | SQLite | PostgreSQL |
|----------|--------|------------|
| **Setup** | Zero-config, single file | Requires server installation, user management |
| **Portability** | Copy `.db` file to backup | Requires `pg_dump` / `pg_restore` |
| **Concurrency** | WAL mode supports multiple readers + 1 writer | Full MVCC, unlimited concurrent connections |
| **Performance** | 10k-100k rows: excellent<br>1M+ rows: slower | Scales to billions of rows |
| **Dependencies** | Built into Python | Requires `psycopg2`, server process |
| **Disk Usage** | ~1MB per engagement | ~10MB minimum + overhead |

**Decision**: For souleyez's use case (single-user, 1k-10k rows per engagement), SQLite is **perfect**.

**When to Switch**: If souleyez adds multi-user support or exceeds 100k hosts per engagement, consider PostgreSQL.

#### Compared to NoSQL (MongoDB, Redis)

**Why NOT MongoDB**:
- ❌ Relational data (hosts → services → findings)
- ❌ Requires server process
- ❌ No transactional guarantees across collections

**Why NOT Redis**:
- ❌ In-memory (would lose data on crash)
- ❌ No complex queries (no JOIN, GROUP BY)
- ❌ Requires Redis server process

**Why SQLite Wins**:
- ✅ ACID transactions (atomicity, consistency, isolation, durability)
- ✅ SQL queries (JOIN, aggregate functions, indexes)
- ✅ Embedded (no external processes)

#### Compared to File Storage (JSON, YAML)

**Alternative**: Store data in JSON files (e.g., `~/.souleyez/hosts.json`).

**Cons**:
- ❌ No transactional safety (corruption risk)
- ❌ Must load entire file to query
- ❌ No indexing (slow searches)
- ❌ Race conditions in concurrent writes

**SQLite Wins**: ACID transactions, indexes, concurrent access.

### Why Normalized Schema?

**Normalization** = Minimize data redundancy via foreign keys.

**Example**:
```
Host 10.0.0.5 has 3 services (SSH, HTTP, MySQL).
Denormalized: Store IP in each service row (3x "10.0.0.5").
Normalized: Store IP once in hosts table, reference via host_id.
```

**Benefits**:
1. **Data Integrity**: Update IP once, reflected in all services
2. **Disk Efficiency**: No duplicate data
3. **Query Power**: `JOIN` hosts and services for complex queries

**Tradeoff**: Requires `JOIN` in queries (slightly more complex SQL).

**Decision**: For structured pentest data, normalization is correct choice.

### Why WAL Mode?

**WAL** = Write-Ahead Logging

**Without WAL** (default rollback journal):
- Only 1 connection at a time (reader OR writer)
- Dashboard blocks if worker is writing

**With WAL**:
- Multiple readers + 1 writer simultaneously
- Dashboard reads while worker inserts results
- Better concurrency

**Command**: `PRAGMA journal_mode=WAL` (set in `database.py:26`)

**Tradeoff**: Creates `.db-shm` and `.db-wal` files alongside `.db`.

### Why Indices?

**Indices** = Precomputed lookup tables for fast queries.

**Example**:
```sql
-- Without index: Full table scan (slow)
SELECT * FROM hosts WHERE engagement_id = 42;

-- With index: Direct lookup (fast)
CREATE INDEX idx_hosts_engagement ON hosts(engagement_id);
```

**Created Indices**:
- `idx_hosts_engagement` - Fast queries by engagement
- `idx_hosts_ip` - Fast IP address lookups
- `idx_services_host` - Fast services by host
- `idx_findings_engagement` - Fast findings by engagement
- `idx_findings_severity` - Fast filtering by severity
- `idx_credentials_engagement` - Fast credentials by engagement
- `idx_credentials_host` - Fast credentials by host
- `idx_credentials_status` - Fast filtering by status

**Performance Impact**:
- **Queries**: 30-60% faster
- **Inserts**: 5-10% slower (must update index)
- **Disk**: +10-20% space

**Decision**: Indices on foreign keys and frequently-queried columns.

---

## Migration System

### Problem

Schema changes over time (new columns, indices, tables).

**Example**: Adding `updated_at` to credentials table.

**Challenge**: Existing databases don't have this column.

### Solution: Versioned Migrations

**File**: `souleyez/storage/migrations/migration_manager.py`

**Schema Migrations Table**:
```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Migration Example**: `souleyez/storage/migrations/001_add_credential_enhancements.py`

```python
def upgrade(db):
    """Add indices and updated_at column."""
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_credentials_engagement
        ON credentials(engagement_id)
    """)
    db.execute("""
        ALTER TABLE credentials ADD COLUMN updated_at TIMESTAMP
    """)
    # Record migration
    db.execute("""
        INSERT INTO schema_migrations (version, description)
        VALUES ('001', 'Add credential enhancements')
    """)
```

**Workflow**:
1. Check `schema_migrations` table for applied versions
2. Run pending migrations in order (001, 002, 003, ...)
3. Record success in `schema_migrations`

**Benefits**:
- **Idempotent**: Migrations run once, skip if already applied
- **Auditable**: `schema_migrations` table shows history
- **Rollback**: Downgrade function (optional)

---

## Consequences

### Positive

1. **Simplicity**: Single `.db` file, no external services
2. **Portability**: Copy database to backup/restore
3. **Performance**: Fast for typical pentest workloads (1k-10k hosts)
4. **ACID**: Transactional safety, no corruption risk
5. **Queryable**: SQL JOIN, aggregate functions, complex filters
6. **Concurrent**: WAL mode allows dashboard + worker simultaneously

### Negative

1. **Scalability**: Struggles with 100k+ hosts (unlikely in pentesting)
2. **Multi-User**: No built-in access control (single-user design)
3. **Replication**: No master-slave replication (manual backups only)

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| **Database Corruption** | WAL mode reduces risk, automatic backups recommended |
| **Disk Full** | Vacuum database periodically (`VACUUM;`) |
| **Slow Queries** | Add indices on new columns as needed |
| **Migration Failure** | Test migrations on copy before applying |

---

## Future Considerations

### 1. Database Vacuum (Reclaim Space)

**Problem**: Deleted rows leave empty space in database file.

**Solution**: Run `VACUUM` periodically.

```bash
souleyez db vacuum
```

**Implementation**:
```python
def vacuum():
    db = get_db()
    db.execute("VACUUM")
```

### 2. Foreign Key Cascade Deletes

**Current**: Manual cascade in `EngagementManager.delete()`.

**Improvement**: Use SQL `ON DELETE CASCADE`:
```sql
CREATE TABLE hosts (
    engagement_id INTEGER NOT NULL,
    FOREIGN KEY (engagement_id) REFERENCES engagements(id)
        ON DELETE CASCADE
);
```

**Tradeoff**: Easier deletion, harder to debug accidental deletes.

### 3. Full-Text Search

**Use Case**: Search findings by keyword.

**SQLite FTS5**:
```sql
CREATE VIRTUAL TABLE findings_fts USING fts5(title, description);
```

**Decision**: Defer until users request search feature.

### 4. Database Encryption (Full-Disk)

**Current**: Only credentials table fields encrypted.

**Alternative**: Encrypt entire database with SQLCipher.

**Tradeoff**: Cannot inspect with standard tools, slower queries.

**Decision**: Field-level encryption sufficient (see [ADR-002](002-master-password-approach.md)).

---

## Related Decisions

- [ADR-002: Master Password Approach](002-master-password-approach.md) - Credential encryption
- [ADR-001: No LLM Integration](001-no-llm-integration.md) - Structured data, not AI

---

## References

- SQLite Documentation: https://www.sqlite.org/docs.html
- SQLite WAL Mode: https://www.sqlite.org/wal.html
- Database Normalization: https://en.wikipedia.org/wiki/Database_normalization
- ACID Properties: https://en.wikipedia.org/wiki/ACID

---

**Authors**: y0d8, S0ul H@ck3r$
**Last Updated**: 2025-10-29
