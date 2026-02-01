"""
Migration 009: Add CrackMapExec tables for Windows/AD enumeration results.
"""


def upgrade(db):
    """Add CrackMapExec result tables."""
    # Tables already exist in schema.sql (smb_shares, smb_files)
    # This migration is a no-op to maintain migration numbering consistency
    pass


def downgrade(db):
    """Rollback CrackMapExec tables."""
    # Tables are managed by schema.sql, not migrations
    pass
