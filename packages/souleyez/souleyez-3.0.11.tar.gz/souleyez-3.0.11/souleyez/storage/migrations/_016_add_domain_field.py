"""
Migration: Add domain column to hosts table

This migration adds support for storing Windows domain names discovered
by tools like CrackMapExec/NetExec, which is needed for Active Directory
attacks like GetNPUsers.
"""


def upgrade(db):
    """Add domain column to hosts table."""
    # Check if column already exists
    cursor = db.execute("PRAGMA table_info(hosts)")
    columns = [row[1] for row in cursor.fetchall()]

    if "domain" not in columns:
        db.execute("""
            ALTER TABLE hosts
            ADD COLUMN domain TEXT DEFAULT NULL
        """)


def downgrade(db):
    """
    SQLite doesn't support DROP COLUMN before version 3.35.0.
    For now, downgrade is not supported.
    """
    raise NotImplementedError(
        "Downgrade not supported for SQLite ALTER TABLE ADD COLUMN"
    )
