"""
Migration 012: Add team collaboration features
"""


def upgrade(conn):
    """Add team collaboration tables."""

    # Add columns to deliverables table for team collaboration
    try:
        conn.execute("ALTER TABLE deliverables ADD COLUMN assigned_to TEXT")
    except Exception:
        pass  # Column may already exist

    try:
        conn.execute("ALTER TABLE deliverables ADD COLUMN blocker TEXT")
    except Exception:
        pass  # Column may already exist

    # Activity log for tracking who did what
    conn.execute("""
        CREATE TABLE IF NOT EXISTS deliverable_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deliverable_id INTEGER NOT NULL,
            engagement_id INTEGER NOT NULL,
            user TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (deliverable_id) REFERENCES deliverables(id) ON DELETE CASCADE,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE
        )
    """)

    # Index for faster activity queries
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_activity_deliverable
        ON deliverable_activity(deliverable_id, created_at DESC)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_activity_engagement
        ON deliverable_activity(engagement_id, created_at DESC)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_activity_user
        ON deliverable_activity(user, created_at DESC)
    """)

    # Comments on deliverables
    conn.execute("""
        CREATE TABLE IF NOT EXISTS deliverable_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deliverable_id INTEGER NOT NULL,
            user TEXT NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (deliverable_id) REFERENCES deliverables(id) ON DELETE CASCADE
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_comments_deliverable
        ON deliverable_comments(deliverable_id, created_at DESC)
    """)

    print("✅ Migration 012: Team collaboration tables created")


def downgrade(conn):
    """Remove team collaboration tables."""
    conn.execute("DROP TABLE IF EXISTS deliverable_activity")
    conn.execute("DROP TABLE IF EXISTS deliverable_comments")
    conn.execute("DROP INDEX IF EXISTS idx_activity_deliverable")
    conn.execute("DROP INDEX IF EXISTS idx_activity_engagement")
    conn.execute("DROP INDEX IF EXISTS idx_activity_user")
    conn.execute("DROP INDEX IF EXISTS idx_comments_deliverable")
    print("✅ Migration 012: Rolled back")
