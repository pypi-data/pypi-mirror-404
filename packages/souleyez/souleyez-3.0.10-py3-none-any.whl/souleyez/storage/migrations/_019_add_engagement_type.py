"""
Migration 019: Add Engagement Type Field

Adds engagement_type column to track the type of engagement (pentest, bug bounty, CTF, etc.)
"""

MIGRATION_ID = 19
DESCRIPTION = "Add engagement_type column to engagements table"


def upgrade(conn):
    """Apply migration"""
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(engagements)")
    columns = [row[1] for row in cursor.fetchall()]

    # Add engagement_type column only if it doesn't exist
    if "engagement_type" not in columns:
        cursor.execute("""
            ALTER TABLE engagements ADD COLUMN engagement_type TEXT DEFAULT 'custom'
        """)

    # Create index for faster lookups by type
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_engagements_type
        ON engagements(engagement_type)
    """)

    conn.commit()


def downgrade(conn):
    """Revert migration"""
    cursor = conn.cursor()

    # SQLite doesn't support DROP COLUMN directly
    # Would need to recreate table, but for now we'll just drop the index
    cursor.execute("DROP INDEX IF EXISTS idx_engagements_type")

    conn.commit()
