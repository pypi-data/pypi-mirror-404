"""
Migration 005: Add screenshots table for visual evidence management.
"""


def upgrade(db):
    """Add screenshots table."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS screenshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id INTEGER NOT NULL,
            host_id INTEGER,
            finding_id INTEGER,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            title TEXT,
            description TEXT,
            file_size INTEGER,
            mime_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id),
            FOREIGN KEY (host_id) REFERENCES hosts(id),
            FOREIGN KEY (finding_id) REFERENCES findings(id)
        )
    """)

    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_screenshots_engagement ON screenshots(engagement_id)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_screenshots_host ON screenshots(host_id)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_screenshots_finding ON screenshots(finding_id)"
    )


def downgrade(db):
    """Rollback screenshots table."""
    db.execute("DROP TABLE IF EXISTS screenshots")
