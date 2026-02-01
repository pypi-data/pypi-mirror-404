"""
Migration 026: Add Engagement Scope Validation

Tables created:
- engagement_scope: Structured scope definitions (CIDR, domains, URLs)
- scope_validation_log: Audit trail of scope validation decisions

Columns added:
- engagements.scope_enforcement: Enforcement mode (off, warn, block)
- hosts.scope_status: Host scope status (in_scope, out_of_scope, unknown)
"""

import os


def upgrade(conn):
    """Add scope validation tables and columns."""

    # Engagement scope definitions table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS engagement_scope (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id INTEGER NOT NULL,
            scope_type TEXT NOT NULL,
            value TEXT NOT NULL,
            is_excluded BOOLEAN DEFAULT 0,
            description TEXT,
            added_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
            UNIQUE(engagement_id, scope_type, value)
        )
    """)

    # Scope validation audit log
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scope_validation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id INTEGER NOT NULL,
            job_id INTEGER,
            target TEXT NOT NULL,
            validation_result TEXT NOT NULL,
            action_taken TEXT NOT NULL,
            matched_scope_id INTEGER,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
        )
    """)

    # Add scope_enforcement column to engagements
    try:
        conn.execute(
            "ALTER TABLE engagements ADD COLUMN scope_enforcement TEXT DEFAULT 'off'"
        )
    except Exception:
        pass  # Column may already exist

    # Add scope_status column to hosts
    try:
        conn.execute("ALTER TABLE hosts ADD COLUMN scope_status TEXT DEFAULT 'unknown'")
    except Exception:
        pass  # Column may already exist

    # Indexes for performance
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_scope_engagement ON engagement_scope(engagement_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_scope_type ON engagement_scope(scope_type)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_scope_log_engagement ON scope_validation_log(engagement_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_scope_log_result ON scope_validation_log(validation_result)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_scope_log_timestamp ON scope_validation_log(created_at DESC)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_hosts_scope_status ON hosts(scope_status)"
    )

    conn.commit()

    if not os.environ.get("SOULEYEZ_MIGRATION_SILENT"):
        print("Migration 026: Engagement scope validation tables created")


def downgrade(conn):
    """Remove scope validation tables."""
    conn.execute("DROP TABLE IF EXISTS scope_validation_log")
    conn.execute("DROP TABLE IF EXISTS engagement_scope")
    conn.execute("DROP INDEX IF EXISTS idx_scope_engagement")
    conn.execute("DROP INDEX IF EXISTS idx_scope_type")
    conn.execute("DROP INDEX IF EXISTS idx_scope_log_engagement")
    conn.execute("DROP INDEX IF EXISTS idx_scope_log_result")
    conn.execute("DROP INDEX IF EXISTS idx_scope_log_timestamp")
    conn.execute("DROP INDEX IF EXISTS idx_hosts_scope_status")
    # Note: Cannot easily drop columns in SQLite, they remain but unused
    print("Migration 026: Engagement scope validation tables dropped")
