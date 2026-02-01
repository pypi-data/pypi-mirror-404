"""
Migration: Add mac_address and os_accuracy columns to hosts table

This migration adds support for storing MAC addresses and OS detection
confidence scores from Nmap scans.
"""


def upgrade(db):
    """Add mac_address and os_accuracy columns to hosts table."""
    # Check if columns already exist
    cursor = db.execute("PRAGMA table_info(hosts)")
    columns = [row[1] for row in cursor.fetchall()]

    if "mac_address" not in columns:
        db.execute("""
            ALTER TABLE hosts
            ADD COLUMN mac_address TEXT DEFAULT NULL
        """)

    if "os_accuracy" not in columns:
        db.execute("""
            ALTER TABLE hosts
            ADD COLUMN os_accuracy INTEGER DEFAULT NULL
        """)


def downgrade(db):
    """
    SQLite doesn't support DROP COLUMN before version 3.35.0.
    For now, downgrade is not supported.
    """
    raise NotImplementedError(
        "Downgrade not supported for SQLite ALTER TABLE ADD COLUMN"
    )
