"""
Migration 021: Add Wazuh SIEM Integration tables

Adds tables for storing Wazuh connection configuration and
detection validation results.
"""

MIGRATION_ID = 21
DESCRIPTION = "Add Wazuh SIEM integration tables"


def upgrade(conn):
    """Apply migration"""
    cursor = conn.cursor()

    # Wazuh connection configuration
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wazuh_config (
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
        )
    """)

    # Detection validation results per job
    # Note: job_id references jobs.json (file-based), not a SQLite table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detection_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            engagement_id INTEGER NOT NULL,
            attack_type TEXT,
            target_ip TEXT,
            target_port INTEGER,
            source_ip TEXT,
            attack_start TIMESTAMP,
            attack_end TIMESTAMP,
            detection_status TEXT DEFAULT 'pending',
            alerts_count INTEGER DEFAULT 0,
            wazuh_alerts_json TEXT,
            rule_ids TEXT,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
        )
    """)

    # Indexes
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_wazuh_config_engagement ON wazuh_config(engagement_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_detection_results_job ON detection_results(job_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_detection_results_engagement ON detection_results(engagement_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_detection_results_status ON detection_results(detection_status)"
    )

    conn.commit()


def downgrade(conn):
    """Revert migration"""
    cursor = conn.cursor()

    cursor.execute("DROP INDEX IF EXISTS idx_detection_results_status")
    cursor.execute("DROP INDEX IF EXISTS idx_detection_results_engagement")
    cursor.execute("DROP INDEX IF EXISTS idx_detection_results_job")
    cursor.execute("DROP INDEX IF EXISTS idx_wazuh_config_engagement")
    cursor.execute("DROP TABLE IF EXISTS detection_results")
    cursor.execute("DROP TABLE IF EXISTS wazuh_config")

    conn.commit()
