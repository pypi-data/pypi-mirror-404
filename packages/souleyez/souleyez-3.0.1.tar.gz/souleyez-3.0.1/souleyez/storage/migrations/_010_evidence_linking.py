"""
Migration 010: Evidence linking system for deliverables
"""


def upgrade(conn):
    """Add evidence linking table."""

    conn.execute("""
        CREATE TABLE IF NOT EXISTS deliverable_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deliverable_id INTEGER NOT NULL,
            evidence_type TEXT NOT NULL,
            evidence_id INTEGER NOT NULL,
            linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            linked_by TEXT,
            notes TEXT,
            FOREIGN KEY (deliverable_id) REFERENCES deliverables(id) ON DELETE CASCADE
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_deliverable_evidence
        ON deliverable_evidence(deliverable_id, evidence_type)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_evidence_lookup
        ON deliverable_evidence(evidence_type, evidence_id)
    """)

    print("✅ Migration 010: Evidence linking system created")


def downgrade(conn):
    """Remove evidence linking system."""
    conn.execute("DROP TABLE IF EXISTS deliverable_evidence")
    conn.execute("DROP INDEX IF EXISTS idx_deliverable_evidence")
    conn.execute("DROP INDEX IF EXISTS idx_evidence_lookup")
    print("✅ Migration 010: Rolled back")
