#!/usr/bin/env python3
"""
Migration 002: Add status tracking fields to hosts and credentials tables
"""


def upgrade(conn):
    """Add notes and tracking fields."""

    # Helper to check if column exists
    def column_exists(table, column):
        cursor = conn.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        return column in columns

    # Add columns to credentials table if they don't exist
    if not column_exists("credentials", "notes"):
        conn.execute("ALTER TABLE credentials ADD COLUMN notes TEXT")
    if not column_exists("credentials", "last_tested"):
        conn.execute("ALTER TABLE credentials ADD COLUMN last_tested TIMESTAMP")

    # Add columns to hosts table if they don't exist
    if not column_exists("hosts", "access_level"):
        conn.execute("ALTER TABLE hosts ADD COLUMN access_level TEXT DEFAULT 'none'")
    if not column_exists("hosts", "notes"):
        conn.execute("ALTER TABLE hosts ADD COLUMN notes TEXT")


def downgrade(conn):
    """
    SQLite doesn't support DROP COLUMN easily.
    Would need to recreate tables without these columns.
    """
    raise NotImplementedError(
        "Downgrade not supported for SQLite ALTER TABLE ADD COLUMN"
    )
