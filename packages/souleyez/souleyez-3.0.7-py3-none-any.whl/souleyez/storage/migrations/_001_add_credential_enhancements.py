#!/usr/bin/env python3
"""
Migration 001: Add credential enhancements
- Adds indices for better performance
- Adds created_at/updated_at tracking
"""

import os
import sqlite3


def upgrade(conn: sqlite3.Connection):
    """Apply migration."""
    cursor = conn.cursor()

    # Check if we should suppress output (silent mode)
    silent = os.environ.get("SOULEYEZ_MIGRATION_SILENT", "0") == "1"

    # Add indices for credentials table
    if not silent:
        print("  → Creating index on credentials(engagement_id)")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_credentials_engagement
        ON credentials(engagement_id)
    """)

    if not silent:
        print("  → Creating index on credentials(host_id)")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_credentials_host
        ON credentials(host_id)
    """)

    if not silent:
        print("  → Creating index on credentials(status)")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_credentials_status
        ON credentials(status)
    """)

    # Add updated_at column if it doesn't exist
    try:
        cursor.execute("SELECT updated_at FROM credentials LIMIT 1")
    except sqlite3.OperationalError:
        if not silent:
            print("  → Adding updated_at column to credentials table")
        cursor.execute("""
            ALTER TABLE credentials
            ADD COLUMN updated_at TIMESTAMP
        """)
        # Set default value for existing rows
        cursor.execute("""
            UPDATE credentials
            SET updated_at = CURRENT_TIMESTAMP
            WHERE updated_at IS NULL
        """)

    conn.commit()
    if not silent:
        print("  ✅ Migration completed")


def downgrade(conn: sqlite3.Connection):
    """Rollback migration (optional)."""
    cursor = conn.cursor()

    # Drop indices
    cursor.execute("DROP INDEX IF EXISTS idx_credentials_engagement")
    cursor.execute("DROP INDEX IF EXISTS idx_credentials_host")
    cursor.execute("DROP INDEX IF EXISTS idx_credentials_status")

    # Note: Cannot drop columns in SQLite easily
    # Would need to recreate table without updated_at column

    conn.commit()
