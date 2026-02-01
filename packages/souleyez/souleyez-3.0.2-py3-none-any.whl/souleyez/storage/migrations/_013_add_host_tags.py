"""
Migration: Add tags column to hosts table

This migration adds support for host tagging, allowing users to
categorize and organize hosts with custom labels.
"""


def upgrade(db):
    """Add tags column to hosts table."""
    # Check if column already exists
    cursor = db.execute("PRAGMA table_info(hosts)")
    columns = [row[1] for row in cursor.fetchall()]

    if "tags" not in columns:
        db.execute("""
            ALTER TABLE hosts
            ADD COLUMN tags TEXT DEFAULT NULL
        """)
    # If column already exists, migration is idempotent - do nothing


def downgrade(db):
    """
    SQLite doesn't support DROP COLUMN before version 3.35.0.
    For now, downgrade is not supported.
    """
    raise NotImplementedError(
        "Downgrade not supported for SQLite ALTER TABLE ADD COLUMN"
    )
