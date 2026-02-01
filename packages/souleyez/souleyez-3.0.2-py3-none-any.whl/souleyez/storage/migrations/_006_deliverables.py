"""
Migration 006: Add deliverables tracking table.
"""


def upgrade(db):
    """Add deliverables tracking table."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS deliverables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            target_type TEXT NOT NULL,
            target_value INTEGER,
            current_value INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            auto_validate BOOLEAN DEFAULT 0,
            validation_query TEXT,
            priority TEXT DEFAULT 'medium',
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id)
        )
    """)

    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_deliverables_engagement ON deliverables(engagement_id)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_deliverables_status ON deliverables(status)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_deliverables_category ON deliverables(category)"
    )


def downgrade(db):
    """Rollback deliverables table."""
    db.execute("DROP TABLE IF EXISTS deliverables")
