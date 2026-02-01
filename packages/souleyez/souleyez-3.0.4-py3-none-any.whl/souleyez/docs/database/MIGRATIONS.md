# Database Migrations Guide

## Overview

SoulEyez uses a custom migration system for managing database schema changes. Migrations are applied sequentially and tracked in the `schema_migrations` table.

**Why not Alembic?**: Custom lightweight solution tailored to SQLite, simpler to maintain.

## Migration Structure

### Migration Files

Location: `souleyez/storage/migrations/`  
Naming: `NNN_description.py` (e.g., `001_add_credential_enhancements.py`)

Each migration file contains two functions:
- `upgrade(conn)`: Apply schema changes
- `downgrade(conn)`: Rollback schema changes

### Example Migration

```python
#!/usr/bin/env python3
"""
Migration 002: Add performance indexes
"""
import sqlite3


def upgrade(conn: sqlite3.Connection):
    """Apply migration."""
    cursor = conn.cursor()
    
    print("  → Creating index on services(port)")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_services_port 
        ON services(port)
    """)
    
    conn.commit()
    print("  ✅ Migration completed")


def downgrade(conn: sqlite3.Connection):
    """Rollback migration."""
    cursor = conn.cursor()
    
    cursor.execute("DROP INDEX IF EXISTS idx_services_port")
    
    conn.commit()
```

---

## Running Migrations

### Check Migration Status

```python
from souleyez.storage.migrations.migration_manager import MigrationManager
from souleyez import config
from pathlib import Path

db_path = Path(config.get('database.path')).expanduser()
manager = MigrationManager(str(db_path))

# Show current status
manager.status()
```

**Output:**
```
================================================================================
DATABASE MIGRATION STATUS
================================================================================
Database: /home/user/.souleyez/souleyez.db
Applied migrations: 1
Pending migrations: 0

✅ Applied:
  [001] add_credential_enhancements (applied: 2024-10-31 12:00:00)

✅ Database is up to date!
================================================================================
```

### Apply All Pending Migrations

```python
manager.migrate()
```

**Output:**
```
Found 2 pending migration(s)
[002] Applying migration: add_performance_indexes
  → Creating index on services(port)
  → Creating index on services(service_name)
  ✅ Migration completed
[002] ✅ Successfully applied

[003] Applying migration: add_unique_constraints
  → Adding unique constraint to hosts
  ✅ Migration completed
[003] ✅ Successfully applied

✅ All 2 migration(s) applied successfully!
```

### Rollback Migrations

```python
# Rollback last migration
manager.rollback(1)

# Rollback last 3 migrations
manager.rollback(3)
```

**Output:**
```
[003] Rolling back...
[003] ✅ Rolled back successfully

[002] Rolling back...
[002] ✅ Rolled back successfully

✅ Rolled back 2 migration(s)
```

---

## Creating a New Migration

### Step 1: Create Migration File

```bash
cd souleyez/storage/migrations/

# Find next version number
ls -1 [0-9]*.py | tail -1
# Last is 001_add_credential_enhancements.py

# Create next migration
touch 002_your_change_description.py
```

### Step 2: Implement upgrade() Function

```python
#!/usr/bin/env python3
"""
Migration 002: Your change description
- What this migration does
- Why it's needed
"""
import sqlite3


def upgrade(conn: sqlite3.Connection):
    """Apply migration."""
    cursor = conn.cursor()
    
    # Example: Add a new column
    print("  → Adding new_column to findings table")
    try:
        cursor.execute("""
            ALTER TABLE findings 
            ADD COLUMN new_column TEXT
        """)
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("  ⚠️  Column already exists, skipping")
        else:
            raise
    
    # Example: Create a new table
    print("  → Creating new_table")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS new_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
    
    # Example: Add an index
    print("  → Creating index")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_new_table_name 
        ON new_table(name)
    """)
    
    conn.commit()
    print("  ✅ Migration completed")


def downgrade(conn: sqlite3.Connection):
    """Rollback migration."""
    cursor = conn.cursor()
    
    # Reverse the changes
    print("  → Dropping index")
    cursor.execute("DROP INDEX IF EXISTS idx_new_table_name")
    
    print("  → Dropping table")
    cursor.execute("DROP TABLE IF EXISTS new_table")
    
    # Note: SQLite doesn't support DROP COLUMN easily
    # For column removal, you'd need to recreate the table
    
    conn.commit()
```

### Step 3: Test on Development Database

```bash
# Backup first!
cp ~/.souleyez/souleyez.db ~/.souleyez/souleyez.db.backup

# Test migration
python3 << EOF
from souleyez.storage.migrations.migration_manager import MigrationManager
mgr = MigrationManager('/home/user/.souleyez/souleyez.db')
mgr.status()
mgr.migrate()
EOF

# Test rollback
python3 << EOF
from souleyez.storage.migrations.migration_manager import MigrationManager
mgr = MigrationManager('/home/user/.souleyez/souleyez.db')
mgr.rollback(1)
mgr.status()
EOF
```

### Step 4: Verify Changes

```bash
# Check schema
sqlite3 ~/.souleyez/souleyez.db ".schema"

# Check data integrity
sqlite3 ~/.souleyez/souleyez.db "PRAGMA integrity_check;"

# Check foreign keys
sqlite3 ~/.souleyez/souleyez.db "PRAGMA foreign_key_check;"
```

---

## Best Practices

### ✅ DO

1. **Keep migrations small and focused**
   - One logical change per migration
   - Easier to debug and rollback

2. **Always provide downgrade()**
   - Required for rollback support
   - Test rollback before committing

3. **Use idempotent operations**
   - `CREATE TABLE IF NOT EXISTS`
   - `CREATE INDEX IF NOT EXISTS`
   - Check for column existence before adding

4. **Test on copy of production data**
   - Never test migrations on production first
   - Use backup database for testing

5. **Document breaking changes**
   - Comment any changes that affect application code
   - Update relevant documentation

6. **Handle errors gracefully**
   - Catch expected errors (e.g., duplicate column)
   - Let unexpected errors propagate

### ❌ DON'T

1. **Don't modify existing migrations**
   - Once applied, migrations are immutable
   - Create a new migration to fix issues

2. **Don't delete data without backup**
   - Migrations should be reversible
   - If data loss is intentional, document it

3. **Don't skip version numbers**
   - Migrations must be sequential
   - Use next available number

4. **Don't assume column order**
   - SQLite doesn't guarantee column order
   - Use named columns in queries

---

## Common Migration Patterns

### Adding a Column

```python
def upgrade(conn):
    cursor = conn.cursor()
    
    # Check if column exists first
    try:
        cursor.execute("SELECT new_column FROM table_name LIMIT 1")
        print("  ⚠️  Column already exists")
    except sqlite3.OperationalError:
        cursor.execute("""
            ALTER TABLE table_name 
            ADD COLUMN new_column TEXT DEFAULT 'value'
        """)
        print("  ✅ Added new_column")
    
    conn.commit()
```

### Removing a Column (SQLite Workaround)

```python
def upgrade(conn):
    cursor = conn.cursor()
    
    # SQLite doesn't support DROP COLUMN
    # Must recreate table without the column
    
    # 1. Create new table without column
    cursor.execute("""
        CREATE TABLE table_name_new (
            id INTEGER PRIMARY KEY,
            keep_col TEXT
            -- dropped_col removed
        )
    """)
    
    # 2. Copy data
    cursor.execute("""
        INSERT INTO table_name_new (id, keep_col)
        SELECT id, keep_col FROM table_name
    """)
    
    # 3. Drop old table
    cursor.execute("DROP TABLE table_name")
    
    # 4. Rename new table
    cursor.execute("ALTER TABLE table_name_new RENAME TO table_name")
    
    conn.commit()
```

### Adding Foreign Key Constraint

```python
def upgrade(conn):
    cursor = conn.cursor()
    
    # SQLite requires recreating table to add FK
    
    # 1. Create new table with FK
    cursor.execute("""
        CREATE TABLE hosts_new (
            id INTEGER PRIMARY KEY,
            engagement_id INTEGER NOT NULL,
            ip_address TEXT NOT NULL,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
        )
    """)
    
    # 2. Copy data
    cursor.execute("""
        INSERT INTO hosts_new 
        SELECT * FROM hosts
    """)
    
    # 3. Drop old and rename
    cursor.execute("DROP TABLE hosts")
    cursor.execute("ALTER TABLE hosts_new RENAME TO hosts")
    
    # 4. Recreate indexes
    cursor.execute("""
        CREATE INDEX idx_hosts_engagement ON hosts(engagement_id)
    """)
    
    conn.commit()
```

### Adding an Index

```python
def upgrade(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_name 
        ON table_name(column_name)
    """)
    conn.commit()

def downgrade(conn):
    cursor = conn.cursor()
    cursor.execute("DROP INDEX IF EXISTS idx_name")
    conn.commit()
```

---

## Migration Tracking

### schema_migrations Table

Migrations are tracked in this table:

```sql
CREATE TABLE schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Do not modify this table manually!** Use the MigrationManager API.

---

## Troubleshooting

### Migration Failed Halfway

```python
# Check which migrations are applied
manager.status()

# Manually rollback if needed
manager.rollback(1)

# Fix the migration file
# Re-apply
manager.migrate()
```

### Database Corrupted

```bash
# Restore from backup
cp ~/.souleyez/souleyez.db.backup ~/.souleyez/souleyez.db

# Check integrity
sqlite3 ~/.souleyez/souleyez.db "PRAGMA integrity_check;"
```

### Migration Applied But Not Recorded

```python
# Manually insert into schema_migrations
import sqlite3
conn = sqlite3.connect('/path/to/souleyez.db')
conn.execute(
    "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
    ("002", "migration_name")
)
conn.commit()
conn.close()
```

---

## See Also

- [Schema Documentation](./SCHEMA.md) - Current database schema
- [Schema ERD](./SCHEMA_ERD.md) - Visual relationship diagram
- [Migration Manager Source](../../souleyez/storage/migrations/migration_manager.py)
