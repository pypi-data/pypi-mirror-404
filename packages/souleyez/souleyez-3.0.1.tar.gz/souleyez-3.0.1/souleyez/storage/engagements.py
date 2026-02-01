#!/usr/bin/env python3
"""
souleyez.storage.engagements - Engagement management
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .database import get_db

ENGAGEMENT_FILE = Path.home() / ".souleyez" / "current_engagement"


class EngagementManager:
    def __init__(self):
        self.db = get_db()

    def create(
        self, name: str, description: str = "", engagement_type: str = "custom"
    ) -> int:
        """Create new engagement with current user as owner."""
        # Check if engagement already exists
        existing = self.get(name)
        if existing:
            raise ValueError(f"Engagement '{name}' already exists")

        # Get current user as owner
        from souleyez.auth import get_current_user

        user = get_current_user()
        owner_id = user.id if user else None

        eng_id = self.db.insert(
            "engagements",
            {
                "name": name,
                "description": description,
                "engagement_type": engagement_type,
                "owner_id": owner_id,
            },
        )

        # Audit log
        from souleyez.auth.audit import AuditAction, audit_log

        audit_log(
            AuditAction.ENGAGEMENT_CREATED,
            resource_type="engagement",
            resource_id=eng_id,
            details={"name": name, "type": engagement_type},
        )

        return eng_id

    def create_engagement(
        self, name: str, description: str = "", engagement_type: str = "custom"
    ) -> int:
        """Alias for create() for compatibility."""
        return self.create(name, description, engagement_type)

    def list(self, user_filtered: bool = True) -> List[Dict[str, Any]]:
        """
        List engagements.

        Args:
            user_filtered: If True, only show engagements user has access to.
                          If False, show all (for admin operations).
        """
        if not user_filtered:
            return self.db.execute("SELECT * FROM engagements ORDER BY created_at DESC")

        from souleyez.auth import get_current_user

        user = get_current_user()
        if not user:
            return []

        from souleyez.auth.engagement_access import EngagementAccessManager

        access_mgr = EngagementAccessManager(self.db.db_path)
        return access_mgr.get_accessible_engagements(user.id, user.role)

    def list_all(self) -> List[Dict[str, Any]]:
        """Alias for list() for compatibility."""
        return self.list()

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        """Get engagement by name."""
        return self.db.execute_one("SELECT * FROM engagements WHERE name = ?", (name,))

    def get_by_id(self, engagement_id: int) -> Optional[Dict[str, Any]]:
        """Get engagement by ID."""
        return self.db.execute_one(
            "SELECT * FROM engagements WHERE id = ?", (engagement_id,)
        )

    def update(self, engagement_id: int, fields: Dict[str, Any]) -> bool:
        """Update engagement fields."""
        if not fields:
            return False

        eng = self.get_by_id(engagement_id)
        if not eng:
            return False

        set_clauses = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [engagement_id]

        self.db.execute(
            f"UPDATE engagements SET {set_clauses}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            tuple(values),
        )
        return True

    def set_current(self, name: str) -> bool:
        """Set current engagement."""
        eng = self.get(name)
        if not eng:
            return False

        ENGAGEMENT_FILE.parent.mkdir(parents=True, exist_ok=True)
        ENGAGEMENT_FILE.write_text(str(eng["id"]))
        return True

    def get_current(self) -> Optional[Dict[str, Any]]:
        """Get current engagement."""
        if not ENGAGEMENT_FILE.exists():
            # Create default engagement
            default_id = self.create("default", "Default engagement")
            self.set_current("default")
            return self.get_by_id(default_id)

        try:
            engagement_id = int(ENGAGEMENT_FILE.read_text().strip())
            result = self.get_by_id(engagement_id)
            if result:
                return result
            # Engagement ID in file doesn't exist in DB, reset to default
        except (ValueError, TypeError):
            # File contains invalid data, reset to default
            pass

        # Reset to default engagement - use existing or create new
        default_eng = self.get("default")
        if default_eng:
            default_id = default_eng["id"]
        else:
            default_id = self.create("default", "Default engagement")
        self.set_current("default")
        return self.get_by_id(default_id)

    def delete(self, name: str) -> bool:
        """Delete engagement and all associated data."""
        eng = self.get(name)
        if not eng:
            return False

        # Delete associated data in correct order (respecting foreign keys)

        # 1. Delete execution log entries for this engagement
        self.db.execute(
            "DELETE FROM execution_log WHERE engagement_id = ?", (eng["id"],)
        )

        # 2. Delete SQLi data (CASCADE chain: databases → tables → columns & dumped_data)
        self.db.execute(
            """
            DELETE FROM sqli_databases
            WHERE engagement_id = ?
        """,
            (eng["id"],),
        )

        # 3. Delete screenshots (references engagement, host, finding)
        self.db.execute("DELETE FROM screenshots WHERE engagement_id = ?", (eng["id"],))

        # 4. Delete deliverables (references engagement_id)
        self.db.execute(
            "DELETE FROM deliverables WHERE engagement_id = ?", (eng["id"],)
        )

        # 5. Delete SMB files (references smb_shares)
        self.db.execute(
            """
            DELETE FROM smb_files
            WHERE share_id IN (
                SELECT id FROM smb_shares
                WHERE host_id IN (
                    SELECT id FROM hosts WHERE engagement_id = ?
                )
            )
        """,
            (eng["id"],),
        )

        # 6. Delete SMB shares (references hosts)
        self.db.execute(
            """
            DELETE FROM smb_shares
            WHERE host_id IN (SELECT id FROM hosts WHERE engagement_id = ?)
        """,
            (eng["id"],),
        )

        # 7. Delete web paths (references hosts)
        self.db.execute(
            """
            DELETE FROM web_paths
            WHERE host_id IN (SELECT id FROM hosts WHERE engagement_id = ?)
        """,
            (eng["id"],),
        )

        # 8. Delete credentials (references hosts)
        self.db.execute(
            """
            DELETE FROM credentials
            WHERE host_id IN (SELECT id FROM hosts WHERE engagement_id = ?)
            OR engagement_id = ?
        """,
            (eng["id"], eng["id"]),
        )

        # 9. Delete findings (references engagement_id)
        self.db.execute("DELETE FROM findings WHERE engagement_id = ?", (eng["id"],))

        # 10. Delete OSINT data (references engagement_id)
        self.db.execute("DELETE FROM osint_data WHERE engagement_id = ?", (eng["id"],))

        # 11. Delete services (references hosts)
        self.db.execute(
            """
            DELETE FROM services
            WHERE host_id IN (SELECT id FROM hosts WHERE engagement_id = ?)
        """,
            (eng["id"],),
        )

        # 12. Delete hosts (now all foreign key references are gone)
        self.db.execute("DELETE FROM hosts WHERE engagement_id = ?", (eng["id"],))

        # 13. Finally delete the engagement itself
        self.db.execute("DELETE FROM engagements WHERE id = ?", (eng["id"],))

        # Audit log
        from souleyez.auth.audit import AuditAction, audit_log

        audit_log(
            AuditAction.ENGAGEMENT_DELETED,
            resource_type="engagement",
            resource_id=eng["id"],
            details={"name": name},
        )

        # Clean up orphaned pending chains for deleted engagement
        try:
            from souleyez.core.pending_chains import purge_orphaned_chains

            purge_orphaned_chains()
        except Exception:
            pass  # Non-critical cleanup

        return True

    def stats(self, engagement_id: int) -> Dict[str, int]:
        """Get engagement statistics (live hosts only)."""
        # Only count live hosts (status='up')
        hosts = self.db.execute_one(
            "SELECT COUNT(*) as count FROM hosts WHERE engagement_id = ? AND status = 'up'",
            (engagement_id,),
        )
        # Only count services on live hosts
        services = self.db.execute_one(
            "SELECT COUNT(*) as count FROM services WHERE host_id IN (SELECT id FROM hosts WHERE engagement_id = ? AND status = 'up')",
            (engagement_id,),
        )
        findings = self.db.execute_one(
            "SELECT COUNT(*) as count FROM findings WHERE engagement_id = ?",
            (engagement_id,),
        )

        return {
            "hosts": hosts["count"] if hosts else 0,
            "services": services["count"] if services else 0,
            "findings": findings["count"] if findings else 0,
        }

    # =========================================================================
    # Access Control Methods
    # =========================================================================

    def can_access(self, engagement_id: int) -> bool:
        """Check if current user can access this engagement."""
        from souleyez.auth import get_current_user

        user = get_current_user()
        if not user:
            return False

        from souleyez.auth.engagement_access import EngagementAccessManager

        access_mgr = EngagementAccessManager(self.db.db_path)
        return access_mgr.can_access(engagement_id, user.id, user.role)

    def can_edit(self, engagement_id: int) -> bool:
        """Check if current user can edit this engagement."""
        from souleyez.auth import get_current_user

        user = get_current_user()
        if not user:
            return False

        from souleyez.auth.engagement_access import EngagementAccessManager

        access_mgr = EngagementAccessManager(self.db.db_path)
        return access_mgr.can_edit(engagement_id, user.id, user.role)

    def can_delete_engagement(self, engagement_id: int) -> bool:
        """Check if current user can delete this engagement."""
        from souleyez.auth import get_current_user

        user = get_current_user()
        if not user:
            return False

        from souleyez.auth.engagement_access import EngagementAccessManager

        access_mgr = EngagementAccessManager(self.db.db_path)
        return access_mgr.can_delete(engagement_id, user.id, user.role)
