"""
Migration 018: Add Target Column to OSINT Data

Adds target column to track which domain/URL the OSINT data was collected from.
"""

MIGRATION_ID = 18
DESCRIPTION = "Add target column to osint_data table"


def upgrade(conn):
    """Apply migration"""
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(osint_data)")
    columns = [row[1] for row in cursor.fetchall()]

    # Add target column only if it doesn't exist
    if "target" not in columns:
        cursor.execute("""
            ALTER TABLE osint_data ADD COLUMN target TEXT
        """)

    # Create index for faster lookups by target
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_osint_target
        ON osint_data(target)
    """)

    conn.commit()


def downgrade(conn):
    """Revert migration"""
    cursor = conn.cursor()

    # SQLite doesn't support DROP COLUMN directly
    # Would need to recreate table, but for now we'll just drop the index
    cursor.execute("DROP INDEX IF EXISTS idx_osint_target")

    conn.commit()
