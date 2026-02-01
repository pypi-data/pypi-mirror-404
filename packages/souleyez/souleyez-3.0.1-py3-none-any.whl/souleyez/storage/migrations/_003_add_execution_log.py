#!/usr/bin/env python3
"""
Migration 003: Add execution_log table for tracking AI-driven executions
"""

import os
import sqlite3


def upgrade(conn):
    """Apply migration - add execution_log table."""
    cursor = conn.cursor()

    # Check if we should suppress output (silent mode)
    silent = os.environ.get("SOULEYEZ_MIGRATION_SILENT", "0") == "1"

    # Create execution_log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS execution_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id INTEGER NOT NULL,
            recommendation_id TEXT,
            action TEXT NOT NULL,
            command TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            auto_approved BOOLEAN DEFAULT 0,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exit_code INTEGER,
            stdout TEXT,
            stderr TEXT,
            success BOOLEAN,
            feedback_applied TEXT,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id)
        )
    """)

    # Create index for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_execution_engagement 
        ON execution_log(engagement_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_execution_timestamp 
        ON execution_log(executed_at DESC)
    """)

    conn.commit()
    if not silent:
        print("✓ Migration 003: execution_log table created")


def downgrade(conn):
    """Rollback migration."""
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS execution_log")
    cursor.execute("DROP INDEX IF EXISTS idx_execution_engagement")
    cursor.execute("DROP INDEX IF EXISTS idx_execution_timestamp")

    conn.commit()
    print("✓ Migration 003: execution_log table dropped")
