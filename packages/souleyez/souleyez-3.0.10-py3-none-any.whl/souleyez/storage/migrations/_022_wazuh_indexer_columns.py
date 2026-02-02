"""
Migration 022: Add Wazuh Indexer credential columns

Adds indexer_url, indexer_user, indexer_password columns to wazuh_config
for separate Indexer API authentication.
"""

MIGRATION_ID = 22
DESCRIPTION = "Add Wazuh Indexer credential columns"


def upgrade(conn):
    """Apply migration"""
    cursor = conn.cursor()

    # Check if columns already exist (in case of fresh install with updated 021)
    cursor.execute("PRAGMA table_info(wazuh_config)")
    columns = [col[1] for col in cursor.fetchall()]

    if "indexer_url" not in columns:
        cursor.execute("ALTER TABLE wazuh_config ADD COLUMN indexer_url TEXT")

    if "indexer_user" not in columns:
        cursor.execute(
            "ALTER TABLE wazuh_config ADD COLUMN indexer_user TEXT DEFAULT 'admin'"
        )

    if "indexer_password" not in columns:
        cursor.execute("ALTER TABLE wazuh_config ADD COLUMN indexer_password TEXT")

    conn.commit()


def downgrade(conn):
    """Revert migration - SQLite doesn't support DROP COLUMN easily, so we skip"""
    pass
