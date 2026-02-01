"""
Migration 007: Add deliverable templates system
"""


def upgrade(conn):
    """Add deliverable templates table."""

    # Templates table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS deliverable_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            framework TEXT,
            engagement_type TEXT,
            deliverables_json TEXT NOT NULL,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_builtin INTEGER DEFAULT 0
        )
    """)

    # Index for faster lookups
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_templates_framework
        ON deliverable_templates(framework, engagement_type)
    """)

    print("✅ Migration 007: Deliverable templates table created")


def downgrade(conn):
    """Remove deliverable templates table."""
    conn.execute("DROP TABLE IF EXISTS deliverable_templates")
    conn.execute("DROP INDEX IF EXISTS idx_templates_framework")
    print("✅ Migration 007: Rolled back")
