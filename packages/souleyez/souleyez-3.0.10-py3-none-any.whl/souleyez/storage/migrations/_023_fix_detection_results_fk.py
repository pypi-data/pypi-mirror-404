"""
Migration 023: Fix detection_results FK constraint

Removes the incorrect FOREIGN KEY (job_id) REFERENCES jobs(id) constraint.
Jobs are stored in JSON files, not SQLite, so this FK was always invalid
and causes errors when foreign_keys pragma is enabled.
"""

MIGRATION_ID = 23
DESCRIPTION = "Fix detection_results FK constraint (remove invalid jobs reference)"


def upgrade(conn):
    """Apply migration"""
    cursor = conn.cursor()

    # Check if the bad FK exists by examining the schema
    cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='detection_results'"
    )
    row = cursor.fetchone()

    if not row:
        # Table doesn't exist, nothing to fix
        return

    schema = row[0] or ""

    # Check if the bad FK to jobs table exists
    if "REFERENCES jobs" not in schema:
        # Already correct, no fix needed
        return

    # Recreate table without the bad FK
    cursor.execute("""
        CREATE TABLE detection_results_new (
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

    # Copy existing data
    cursor.execute("INSERT INTO detection_results_new SELECT * FROM detection_results")

    # Swap tables
    cursor.execute("DROP TABLE detection_results")
    cursor.execute("ALTER TABLE detection_results_new RENAME TO detection_results")

    # Recreate indexes
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
    """Revert migration - not needed, the old FK was broken anyway"""
    pass
