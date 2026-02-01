"""
Migration 011: Timeline tracking for deliverables and engagements
"""


def upgrade(conn):
    """Add timeline tracking columns."""

    # Add timeline columns to deliverables
    try:
        conn.execute("ALTER TABLE deliverables ADD COLUMN started_at TIMESTAMP")
    except Exception:
        pass  # Column might already exist

    try:
        conn.execute("ALTER TABLE deliverables ADD COLUMN completed_at TIMESTAMP")
    except Exception:
        pass

    try:
        conn.execute(
            "ALTER TABLE deliverables ADD COLUMN estimated_hours FLOAT DEFAULT 0"
        )
    except Exception:
        pass

    try:
        conn.execute("ALTER TABLE deliverables ADD COLUMN actual_hours FLOAT DEFAULT 0")
    except Exception:
        pass

    try:
        conn.execute("ALTER TABLE deliverables ADD COLUMN blocker TEXT")
    except Exception:
        pass

    try:
        conn.execute("ALTER TABLE deliverables ADD COLUMN assigned_to TEXT")
    except Exception:
        pass

    # Add engagement type to engagements
    try:
        conn.execute(
            "ALTER TABLE engagements ADD COLUMN engagement_type TEXT DEFAULT 'network'"
        )
    except Exception:
        pass

    try:
        conn.execute(
            "ALTER TABLE engagements ADD COLUMN estimated_hours FLOAT DEFAULT 0"
        )
    except Exception:
        pass

    try:
        conn.execute("ALTER TABLE engagements ADD COLUMN actual_hours FLOAT DEFAULT 0")
    except Exception:
        pass

    print("✅ Migration 011: Timeline tracking columns added")


def downgrade(conn):
    """Downgrade not supported for ALTER TABLE operations."""
    print("⚠️  Migration 011: Downgrade not supported (ALTER TABLE operations)")
