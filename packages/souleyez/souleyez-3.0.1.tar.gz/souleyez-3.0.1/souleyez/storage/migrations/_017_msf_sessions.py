"""
Migration 017: Add MSF Sessions Tracking

Adds table for tracking Metasploit Framework sessions synchronized from MSF database.
"""

MIGRATION_ID = 17
DESCRIPTION = "Add MSF sessions tracking table"


def upgrade(conn):
    """Apply migration"""
    cursor = conn.cursor()

    # Create msf_sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS msf_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id INTEGER NOT NULL,
            host_id INTEGER NOT NULL,
            msf_session_id INTEGER NOT NULL,
            session_type TEXT,
            via_exploit TEXT,
            via_payload TEXT,
            platform TEXT,
            arch TEXT,
            username TEXT,
            port INTEGER,
            tunnel_peer TEXT,
            opened_at TIMESTAMP,
            closed_at TIMESTAMP,
            close_reason TEXT,
            last_seen TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
            FOREIGN KEY (host_id) REFERENCES hosts(id) ON DELETE CASCADE,
            UNIQUE(engagement_id, msf_session_id)
        )
    """)

    # Create index for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_msf_sessions_engagement
        ON msf_sessions(engagement_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_msf_sessions_host
        ON msf_sessions(host_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_msf_sessions_active
        ON msf_sessions(is_active)
    """)

    conn.commit()


def downgrade(conn):
    """Revert migration"""
    cursor = conn.cursor()

    cursor.execute("DROP INDEX IF EXISTS idx_msf_sessions_active")
    cursor.execute("DROP INDEX IF EXISTS idx_msf_sessions_host")
    cursor.execute("DROP INDEX IF EXISTS idx_msf_sessions_engagement")
    cursor.execute("DROP TABLE IF EXISTS msf_sessions")

    conn.commit()
