"""
Migration 025: Add Multi-SIEM Support

Adds siem_type and config_json columns to wazuh_config for supporting
multiple SIEM platforms (Splunk, Elastic, Sentinel) alongside Wazuh.
"""

MIGRATION_ID = 25
DESCRIPTION = "Add multi-SIEM support columns"


def upgrade(conn):
    """Apply migration"""
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(wazuh_config)")
    columns = [col[1] for col in cursor.fetchall()]

    # Add siem_type column (default 'wazuh' for backwards compatibility)
    if "siem_type" not in columns:
        cursor.execute(
            "ALTER TABLE wazuh_config ADD COLUMN siem_type TEXT DEFAULT 'wazuh'"
        )

    # Add config_json for storing SIEM-specific configuration
    # This allows flexible storage of different fields per SIEM type
    if "config_json" not in columns:
        cursor.execute("ALTER TABLE wazuh_config ADD COLUMN config_json TEXT")

    conn.commit()


def downgrade(conn):
    """Revert migration - SQLite doesn't support DROP COLUMN easily"""
    pass
