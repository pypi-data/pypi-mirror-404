"""
Migration 027: Multi-SIEM Persistence

Changes wazuh_config table to support multiple SIEM configs per engagement.
- Removes UNIQUE constraint on engagement_id
- Adds UNIQUE constraint on (engagement_id, siem_type)
- Allows each engagement to have separate configs for Wazuh, Splunk, etc.
"""

import os


def upgrade(conn):
    """Migrate to multi-SIEM persistence."""
    cursor = conn.cursor()

    # Check if siem_type column exists (from migration 025)
    cursor.execute("PRAGMA table_info(wazuh_config)")
    columns = [col[1] for col in cursor.fetchall()]

    if "siem_type" not in columns:
        cursor.execute(
            "ALTER TABLE wazuh_config ADD COLUMN siem_type TEXT DEFAULT 'wazuh'"
        )
    if "config_json" not in columns:
        cursor.execute("ALTER TABLE wazuh_config ADD COLUMN config_json TEXT")

    # Create new table with correct constraint
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS siem_config_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id INTEGER NOT NULL,
            siem_type TEXT NOT NULL DEFAULT 'wazuh',
            api_url TEXT,
            api_user TEXT,
            api_password TEXT,
            indexer_url TEXT,
            indexer_user TEXT DEFAULT 'admin',
            indexer_password TEXT,
            verify_ssl BOOLEAN DEFAULT 0,
            enabled BOOLEAN DEFAULT 1,
            config_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
            UNIQUE(engagement_id, siem_type)
        )
    """)

    # Copy existing data
    cursor.execute("""
        INSERT OR IGNORE INTO siem_config_new (
            id, engagement_id, siem_type, api_url, api_user, api_password,
            indexer_url, indexer_user, indexer_password, verify_ssl, enabled,
            config_json, created_at, updated_at
        )
        SELECT
            id, engagement_id, COALESCE(siem_type, 'wazuh'), api_url, api_user, api_password,
            indexer_url, indexer_user, indexer_password, verify_ssl, enabled,
            config_json, created_at, updated_at
        FROM wazuh_config
    """)

    # Drop old table and rename new one
    cursor.execute("DROP TABLE wazuh_config")
    cursor.execute("ALTER TABLE siem_config_new RENAME TO wazuh_config")

    # Recreate index
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_wazuh_config_engagement ON wazuh_config(engagement_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_wazuh_config_siem_type ON wazuh_config(siem_type)"
    )

    conn.commit()

    if not os.environ.get("SOULEYEZ_MIGRATION_SILENT"):
        print("Migration 027: Multi-SIEM persistence enabled")


def downgrade(conn):
    """Revert to single SIEM per engagement (lossy - keeps only first config per engagement)."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wazuh_config_old (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id INTEGER NOT NULL UNIQUE,
            api_url TEXT NOT NULL,
            api_user TEXT NOT NULL,
            api_password TEXT,
            indexer_url TEXT,
            indexer_user TEXT DEFAULT 'admin',
            indexer_password TEXT,
            verify_ssl BOOLEAN DEFAULT 0,
            enabled BOOLEAN DEFAULT 1,
            siem_type TEXT DEFAULT 'wazuh',
            config_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
        )
    """)

    # Copy only first config per engagement
    cursor.execute("""
        INSERT OR IGNORE INTO wazuh_config_old (
            engagement_id, api_url, api_user, api_password,
            indexer_url, indexer_user, indexer_password, verify_ssl, enabled,
            siem_type, config_json, created_at, updated_at
        )
        SELECT
            engagement_id, api_url, api_user, api_password,
            indexer_url, indexer_user, indexer_password, verify_ssl, enabled,
            siem_type, config_json, created_at, updated_at
        FROM wazuh_config
        GROUP BY engagement_id
    """)

    cursor.execute("DROP TABLE wazuh_config")
    cursor.execute("ALTER TABLE wazuh_config_old RENAME TO wazuh_config")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_wazuh_config_engagement ON wazuh_config(engagement_id)"
    )

    conn.commit()
    print("Migration 027: Reverted to single SIEM per engagement")
