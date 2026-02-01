"""
Migration 008: Add nuclei findings table for vulnerability scan results.
"""


def upgrade(db):
    """Add nuclei_findings table."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS nuclei_findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id INTEGER NOT NULL,
            template_id TEXT,
            name TEXT NOT NULL,
            severity TEXT CHECK(severity IN ('critical', 'high', 'medium', 'low', 'info')),
            description TEXT,
            matched_at TEXT,
            cve_id TEXT,
            cvss_score REAL,
            cwe_id TEXT,
            curl_command TEXT,
            tags TEXT,
            reference_links TEXT,
            metadata TEXT,
            found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
        )
    """)

    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_nuclei_engagement ON nuclei_findings(engagement_id)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_nuclei_severity ON nuclei_findings(severity)"
    )
    db.execute("CREATE INDEX IF NOT EXISTS idx_nuclei_cve ON nuclei_findings(cve_id)")


def downgrade(db):
    """Rollback nuclei_findings table."""
    db.execute("DROP TABLE IF EXISTS nuclei_findings")
