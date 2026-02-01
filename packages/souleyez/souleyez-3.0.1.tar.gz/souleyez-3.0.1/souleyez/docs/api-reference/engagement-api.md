# Engagement Management API Reference

## Overview

The Engagement API provides programmatic access to workspace management, allowing you to organize penetration testing engagements, track statistics, and manage data isolation.

## Architecture

Engagements use:
- **SQLite Database**: `data/souleyez.db`
- **Current Engagement File**: `~/.souleyez/current_engagement`
- **Data Isolation**: All data (hosts, services, findings) scoped to engagement

---

## Python API

### EngagementManager Class

**Module:** `souleyez.storage.engagements`

**Import:**
```python
from souleyez.storage.engagements import EngagementManager
```

---

### Methods

#### create()

Create a new engagement.

**Signature:**
```python
def create(name: str, description: str = "") -> int
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | str | Yes | Unique engagement name |
| `description` | str | No | Engagement description |

**Returns:** `int` - Engagement ID

**Raises:** `ValueError` if engagement name already exists

**Example:**
```python
em = EngagementManager()
eng_id = em.create("ACME Corp", "Internal network assessment")
print(f"Created engagement ID: {eng_id}")
```

---

#### list()

List all engagements.

**Signature:**
```python
def list() -> List[Dict[str, Any]]
```

**Returns:** List of engagement dictionaries

**Example:**
```python
em = EngagementManager()
engagements = em.list()

for eng in engagements:
    print(f"{eng['id']}: {eng['name']} - {eng['description']}")
```

**Return Structure:**
```python
[
    {
        'id': 1,
        'name': 'ACME Corp',
        'description': 'Internal network assessment',
        'created_at': '2025-10-29 10:00:00'
    },
    {
        'id': 2,
        'name': 'Client XYZ',
        'description': 'External pentest',
        'created_at': '2025-10-28 15:30:00'
    }
]
```

---

#### get()

Get engagement by name.

**Signature:**
```python
def get(name: str) -> Optional[Dict[str, Any]]
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | str | Yes | Engagement name |

**Returns:** Engagement dict or `None` if not found

**Example:**
```python
em = EngagementManager()
eng = em.get("ACME Corp")

if eng:
    print(f"Found: {eng['name']}")
else:
    print("Not found")
```

---

#### get_by_id()

Get engagement by ID.

**Signature:**
```python
def get_by_id(engagement_id: int) -> Optional[Dict[str, Any]]
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `engagement_id` | int | Yes | Engagement ID |

**Returns:** Engagement dict or `None` if not found

**Example:**
```python
em = EngagementManager()
eng = em.get_by_id(1)
```

---

#### set_current()

Set active engagement.

**Signature:**
```python
def set_current(name: str) -> bool
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | str | Yes | Engagement name to activate |

**Returns:** `True` if successful, `False` if engagement not found

**Example:**
```python
em = EngagementManager()
if em.set_current("ACME Corp"):
    print("Switched to ACME Corp")
else:
    print("Engagement not found")
```

**Side Effects:**
- Writes engagement ID to `~/.souleyez/current_engagement`
- All subsequent operations use this engagement

---

#### get_current()

Get current active engagement.

**Signature:**
```python
def get_current() -> Optional[Dict[str, Any]]
```

**Returns:** Current engagement dict or `None`

**Example:**
```python
em = EngagementManager()
current = em.get_current()

if current:
    print(f"Current: {current['name']}")
else:
    print("No engagement selected")
```

**Behavior:**
- If no engagement file exists, creates "default" engagement automatically
- Returns engagement details from database

---

#### delete()

Delete engagement and all associated data.

**Signature:**
```python
def delete(name: str) -> bool
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | str | Yes | Engagement name to delete |

**Returns:** `True` if successful, `False` if not found

**Example:**
```python
em = EngagementManager()
if em.delete("Old Project"):
    print("Deleted successfully")
else:
    print("Engagement not found")
```

**Cascading Deletes:**
- Hosts (and their services)
- Findings
- OSINT data
- Credentials (TODO: verify)
- Web paths (TODO: verify)

**Warning:** This is irreversible!

---

#### stats()

Get engagement statistics.

**Signature:**
```python
def stats(engagement_id: int) -> Dict[str, int]
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `engagement_id` | int | Yes | Engagement ID |

**Returns:** Statistics dictionary

**Example:**
```python
em = EngagementManager()
stats = em.stats(1)

print(f"Hosts: {stats['hosts']}")
print(f"Services: {stats['services']}")
print(f"Findings: {stats['findings']}")
```

**Return Structure:**
```python
{
    'hosts': 12,      # Only 'up' status hosts
    'services': 45,   # Services on live hosts
    'findings': 8     # All findings
}
```

**Note:** Only counts hosts with `status='up'`

---

## Database Schema

### engagements Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| `name` | TEXT | UNIQUE, NOT NULL | Engagement name |
| `description` | TEXT | | Description |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE INDEX on `name`

---

## Integration Examples

### Script: Create Engagement and Run Scans

```python
#!/usr/bin/env python3
from souleyez.storage.engagements import EngagementManager
from souleyez.engine.background import enqueue_job

# Create engagement
em = EngagementManager()
eng_id = em.create("Automated Scan", "Scheduled network scan")
em.set_current("Automated Scan")

# Enqueue jobs
targets = ["192.168.1.0/24", "10.0.0.0/24"]
for target in targets:
    job_id = enqueue_job("nmap", target, ["-sn"], f"Discovery {target}")
    print(f"Enqueued job {job_id} for {target}")
```

---

### Script: List Engagements with Stats

```python
#!/usr/bin/env python3
from souleyez.storage.engagements import EngagementManager

em = EngagementManager()
current = em.get_current()

print("=" * 70)
print(f"{'Name':<20} {'Hosts':<8} {'Services':<10} {'Findings':<10}")
print("=" * 70)

for eng in em.list():
    stats = em.stats(eng['id'])
    marker = "*" if current and eng['id'] == current['id'] else " "
    print(f"{marker} {eng['name']:<18} {stats['hosts']:<8} {stats['services']:<10} {stats['findings']:<10}")
```

---

### Script: Export Engagement Data

```python
#!/usr/bin/env python3
import json
from souleyez.storage.engagements import EngagementManager
from souleyez.storage.database import get_db

em = EngagementManager()
db = get_db()

eng = em.get("ACME Corp")
if not eng:
    print("Engagement not found")
    exit(1)

# Get all data
data = {
    'engagement': eng,
    'stats': em.stats(eng['id']),
    'hosts': db.execute("SELECT * FROM hosts WHERE engagement_id = ?", (eng['id'],)),
    'services': db.execute("""
        SELECT s.* FROM services s
        JOIN hosts h ON s.host_id = h.id
        WHERE h.engagement_id = ?
    """, (eng['id'],)),
    'findings': db.execute("SELECT * FROM findings WHERE engagement_id = ?", (eng['id'],))
}

# Export to JSON
with open(f"{eng['name']}_export.json", 'w') as f:
    json.dump(data, f, indent=2, default=str)

print(f"Exported to {eng['name']}_export.json")
```

---

### Script: Archive Old Engagements

```python
#!/usr/bin/env python3
from datetime import datetime, timedelta
from souleyez.storage.engagements import EngagementManager

em = EngagementManager()
cutoff = datetime.now() - timedelta(days=90)

for eng in em.list():
    created = datetime.strptime(eng['created_at'], '%Y-%m-%d %H:%M:%S')
    
    if created < cutoff:
        stats = em.stats(eng['id'])
        
        # Only archive if no data
        if stats['hosts'] == 0 and stats['findings'] == 0:
            print(f"Archiving: {eng['name']} (created {eng['created_at']})")
            em.delete(eng['name'])
        else:
            print(f"Skipping: {eng['name']} (has data)")
```

---

## REST API

> **TODO:** REST API not yet implemented

Future REST API will provide:
- GET /api/engagements
- POST /api/engagements
- GET /api/engagements/{id}
- DELETE /api/engagements/{id}
- GET /api/engagements/{id}/stats

---

## CLI Integration

All CLI commands use the EngagementManager internally:

```bash
# Calls: em.create(name, description)
souleyez engagement create "Name" -d "Description"

# Calls: em.list(), em.get_current(), em.stats(id)
souleyez engagement list

# Calls: em.set_current(name)
souleyez engagement use "Name"

# Calls: em.get_current(), em.stats(id)
souleyez engagement current

# Calls: em.get(name), em.delete(name)
souleyez engagement delete "Name"
```

---

## Best Practices

### 1. Always Check Current Engagement

```python
em = EngagementManager()
current = em.get_current()

if not current:
    print("No engagement selected!")
    exit(1)
```

### 2. Validate Before Delete

```python
em = EngagementManager()
eng = em.get(name)

if eng:
    stats = em.stats(eng['id'])
    if stats['hosts'] > 0 or stats['findings'] > 0:
        print(f"Warning: Deleting {stats['hosts']} hosts and {stats['findings']} findings!")
        # Get confirmation
```

### 3. Use Descriptive Names

```python
# Good
em.create("ACME Corp Q4 2025 Internal", "Quarterly internal assessment")

# Bad
em.create("test", "")
```

### 4. Set Engagement Before Operations

```python
em = EngagementManager()
em.create("New Project", "")
em.set_current("New Project")  # Critical!

# Now enqueue jobs, add hosts, etc.
```

---

## Error Handling

### ValueError: Duplicate Name

```python
try:
    em.create("ACME Corp", "Description")
except ValueError as e:
    print(f"Error: {e}")
    # Engagement already exists
```

### None Returns

```python
eng = em.get("Nonexistent")
if eng is None:
    print("Engagement not found")
```

---

## Thread Safety

**Warning:** EngagementManager is **not thread-safe**.

For concurrent access:
- Use process-level isolation (separate CLI invocations)
- Implement locking at application level
- Consider database-level locking

---

## Performance Considerations

### Stats Query Performance

`stats()` performs 3 database queries:
1. Count live hosts
2. Count services on live hosts  
3. Count findings

For many engagements, consider caching or batch queries.

### Large Deletes

`delete()` performs cascading deletes. For engagements with thousands of records, this may be slow.

---

## Migration Notes

### From Legacy System

If migrating from workspace-less system:

```python
from souleyez.storage.engagements import EngagementManager
from souleyez.storage.database import get_db

em = EngagementManager()
db = get_db()

# Create default engagement
eng_id = em.create("Legacy Data", "Migrated from old system")

# Update all orphaned records
db.execute("UPDATE hosts SET engagement_id = ? WHERE engagement_id IS NULL", (eng_id,))
db.execute("UPDATE findings SET engagement_id = ? WHERE engagement_id IS NULL", (eng_id,))
```

---

## See Also

- [CLI Commands Reference](cli-commands.md)
- [Getting Started Guide](../user-guide/getting-started.md)
- [Database Schema](../architecture/database-schema.md) (TODO)
- [Integration Guide](integration-guide.md)
