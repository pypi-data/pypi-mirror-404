"""
Migration 020: Add RBAC (Role-Based Access Control) tables

Tables created:
- users: User accounts with roles and licensing tiers
- sessions: Active login sessions
- audit_log: Security audit trail
- engagement_permissions: Team access to engagements
"""

import hashlib
import os
import secrets


def upgrade(conn):
    """Add RBAC tables."""

    # Users table - core user accounts
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL DEFAULT 'analyst',
            tier TEXT NOT NULL DEFAULT 'FREE',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            license_key TEXT,
            license_expires_at TIMESTAMP,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP
        )
    """)

    # Sessions table - active login sessions
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token_hash TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Audit log - immutable security trail
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT,
            username TEXT,
            action TEXT NOT NULL,
            resource_type TEXT,
            resource_id TEXT,
            details TEXT,
            ip_address TEXT,
            success BOOLEAN DEFAULT TRUE
        )
    """)

    # Engagement permissions - team access control
    conn.execute("""
        CREATE TABLE IF NOT EXISTS engagement_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            permission_level TEXT NOT NULL DEFAULT 'viewer',
            granted_by TEXT,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (engagement_id) REFERENCES engagements(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(engagement_id, user_id)
        )
    """)

    # Add owner_id to engagements table
    try:
        conn.execute("ALTER TABLE engagements ADD COLUMN owner_id TEXT")
    except Exception:
        pass  # Column may already exist

    # Indexes for performance
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token_hash)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id, timestamp DESC)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action, timestamp DESC)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_engagement_perms ON engagement_permissions(user_id, engagement_id)"
    )

    conn.commit()

    # Check if we should print (not in silent mode)
    if not os.environ.get("SOULEYEZ_MIGRATION_SILENT"):
        print("✅ Migration 020: RBAC tables created")


def downgrade(conn):
    """Remove RBAC tables."""
    conn.execute("DROP TABLE IF EXISTS engagement_permissions")
    conn.execute("DROP TABLE IF EXISTS audit_log")
    conn.execute("DROP TABLE IF EXISTS sessions")
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute("DROP INDEX IF EXISTS idx_sessions_user")
    conn.execute("DROP INDEX IF EXISTS idx_sessions_token")
    conn.execute("DROP INDEX IF EXISTS idx_sessions_expires")
    conn.execute("DROP INDEX IF EXISTS idx_audit_user")
    conn.execute("DROP INDEX IF EXISTS idx_audit_action")
    conn.execute("DROP INDEX IF EXISTS idx_audit_timestamp")
    conn.execute("DROP INDEX IF EXISTS idx_engagement_perms")
    print("✅ Migration 020: RBAC tables dropped")
