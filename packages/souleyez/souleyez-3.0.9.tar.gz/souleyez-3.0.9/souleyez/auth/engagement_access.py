"""
souleyez.auth.engagement_access - Engagement-level access control

Permission levels:
- owner: Full control, can delete, can manage team
- editor: Can run scans, add findings, but can't delete engagement
- viewer: Read-only access to engagement data
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from souleyez.auth import Role, get_current_user


class EngagementPermission(Enum):
    """Permission levels for engagement access."""

    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


@dataclass
class EngagementAccess:
    """Represents a user's access to an engagement."""

    engagement_id: int
    user_id: str
    permission_level: EngagementPermission
    granted_by: Optional[str]
    granted_at: datetime


class EngagementAccessManager:
    """Manages user access to engagements."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================================
    # Access Checking
    # =========================================================================

    def get_user_permission(
        self, engagement_id: int, user_id: str
    ) -> Optional[EngagementPermission]:
        """
        Get user's permission level for an engagement.

        Returns None if user has no access.
        """
        conn = self._get_conn()

        # First check if user is the owner
        row = conn.execute(
            "SELECT owner_id FROM engagements WHERE id = ?", (engagement_id,)
        ).fetchone()

        if row and row["owner_id"] == user_id:
            conn.close()
            return EngagementPermission.OWNER

        # Check engagement_permissions table
        row = conn.execute(
            "SELECT permission_level FROM engagement_permissions WHERE engagement_id = ? AND user_id = ?",
            (engagement_id, user_id),
        ).fetchone()
        conn.close()

        if row:
            return EngagementPermission(row["permission_level"])

        return None

    def can_access(self, engagement_id: int, user_id: str, user_role: Role) -> bool:
        """Check if user can access an engagement (any level)."""
        # Admins can access everything
        if user_role == Role.ADMIN:
            return True

        return self.get_user_permission(engagement_id, user_id) is not None

    def can_edit(self, engagement_id: int, user_id: str, user_role: Role) -> bool:
        """Check if user can edit an engagement (owner or editor)."""
        if user_role == Role.ADMIN:
            return True

        perm = self.get_user_permission(engagement_id, user_id)
        return perm in (EngagementPermission.OWNER, EngagementPermission.EDITOR)

    def can_delete(self, engagement_id: int, user_id: str, user_role: Role) -> bool:
        """Check if user can delete an engagement (owner only, or admin)."""
        if user_role == Role.ADMIN:
            return True

        perm = self.get_user_permission(engagement_id, user_id)
        return perm == EngagementPermission.OWNER

    def can_manage_team(
        self, engagement_id: int, user_id: str, user_role: Role
    ) -> bool:
        """Check if user can add/remove team members (owner only, or admin)."""
        if user_role == Role.ADMIN:
            return True

        perm = self.get_user_permission(engagement_id, user_id)
        return perm == EngagementPermission.OWNER

    # =========================================================================
    # Engagement Queries (Filtered by Access)
    # =========================================================================

    def get_accessible_engagements(
        self, user_id: str, user_role: Role
    ) -> List[Dict[str, Any]]:
        """
        Get all engagements the user can access.

        Returns engagements with permission_level included.
        """
        conn = self._get_conn()

        if user_role == Role.ADMIN:
            # Admins see everything
            rows = conn.execute("""
                SELECT e.*, 'admin' as permission_level
                FROM engagements e
                ORDER BY e.created_at DESC
            """).fetchall()
        else:
            # Non-admins see owned + shared engagements
            rows = conn.execute(
                """
                SELECT e.*,
                    CASE
                        WHEN e.owner_id = ? THEN 'owner'
                        ELSE COALESCE(ep.permission_level, 'none')
                    END as permission_level
                FROM engagements e
                LEFT JOIN engagement_permissions ep
                    ON e.id = ep.engagement_id AND ep.user_id = ?
                WHERE e.owner_id = ?
                   OR ep.user_id = ?
                   OR e.owner_id IS NULL
                ORDER BY e.created_at DESC
            """,
                (user_id, user_id, user_id, user_id),
            ).fetchall()

        conn.close()
        return [dict(row) for row in rows]

    # =========================================================================
    # Team Management
    # =========================================================================

    def add_team_member(
        self,
        engagement_id: int,
        user_id: str,
        permission_level: EngagementPermission,
        granted_by: str,
    ) -> tuple[bool, str]:
        """
        Add a user to an engagement's team.

        Returns:
            (success, error_message)
        """
        if permission_level == EngagementPermission.OWNER:
            return False, "Cannot add someone as owner. Transfer ownership instead."

        try:
            conn = self._get_conn()
            conn.execute(
                """
                INSERT OR REPLACE INTO engagement_permissions
                (engagement_id, user_id, permission_level, granted_by, granted_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    engagement_id,
                    user_id,
                    permission_level.value,
                    granted_by,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            conn.close()
            return True, ""
        except Exception as e:
            return False, str(e)

    def remove_team_member(self, engagement_id: int, user_id: str) -> tuple[bool, str]:
        """Remove a user from an engagement's team."""
        try:
            conn = self._get_conn()

            # Can't remove the owner via this method
            row = conn.execute(
                "SELECT owner_id FROM engagements WHERE id = ?", (engagement_id,)
            ).fetchone()

            if row and row["owner_id"] == user_id:
                conn.close()
                return False, "Cannot remove the owner. Transfer ownership first."

            result = conn.execute(
                "DELETE FROM engagement_permissions WHERE engagement_id = ? AND user_id = ?",
                (engagement_id, user_id),
            )
            conn.commit()
            conn.close()

            if result.rowcount == 0:
                return False, "User is not a team member"

            return True, ""
        except Exception as e:
            return False, str(e)

    def get_team_members(self, engagement_id: int) -> List[Dict[str, Any]]:
        """Get all team members for an engagement."""
        conn = self._get_conn()

        # Get owner
        owner_row = conn.execute(
            """
            SELECT u.id, u.username, u.email, 'owner' as permission_level,
                   e.created_at as granted_at, NULL as granted_by
            FROM engagements e
            JOIN users u ON e.owner_id = u.id
            WHERE e.id = ?
        """,
            (engagement_id,),
        ).fetchone()

        # Get other team members
        member_rows = conn.execute(
            """
            SELECT u.id, u.username, u.email, ep.permission_level,
                   ep.granted_at, ep.granted_by
            FROM engagement_permissions ep
            JOIN users u ON ep.user_id = u.id
            WHERE ep.engagement_id = ?
            ORDER BY ep.granted_at
        """,
            (engagement_id,),
        ).fetchall()

        conn.close()

        members = []
        if owner_row:
            members.append(dict(owner_row))
        members.extend([dict(row) for row in member_rows])

        return members

    def transfer_ownership(
        self, engagement_id: int, new_owner_id: str, transferred_by: str
    ) -> tuple[bool, str]:
        """Transfer engagement ownership to another user."""
        try:
            conn = self._get_conn()

            # Get current owner
            row = conn.execute(
                "SELECT owner_id FROM engagements WHERE id = ?", (engagement_id,)
            ).fetchone()

            if not row:
                conn.close()
                return False, "Engagement not found"

            old_owner_id = row["owner_id"]

            # Update owner
            conn.execute(
                "UPDATE engagements SET owner_id = ? WHERE id = ?",
                (new_owner_id, engagement_id),
            )

            # Remove new owner from permissions table (they're now owner)
            conn.execute(
                "DELETE FROM engagement_permissions WHERE engagement_id = ? AND user_id = ?",
                (engagement_id, new_owner_id),
            )

            # Add old owner as editor (so they don't lose access)
            if old_owner_id:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO engagement_permissions
                    (engagement_id, user_id, permission_level, granted_by, granted_at)
                    VALUES (?, ?, 'editor', ?, ?)
                """,
                    (
                        engagement_id,
                        old_owner_id,
                        transferred_by,
                        datetime.now().isoformat(),
                    ),
                )

            conn.commit()
            conn.close()
            return True, ""
        except Exception as e:
            return False, str(e)

    # =========================================================================
    # Migration Helper
    # =========================================================================

    def assign_orphan_engagements(self, admin_user_id: str) -> int:
        """
        Assign all engagements without an owner to the admin.
        Called during migration from single-user to multi-user.

        Returns number of engagements updated.
        """
        conn = self._get_conn()
        result = conn.execute(
            "UPDATE engagements SET owner_id = ? WHERE owner_id IS NULL",
            (admin_user_id,),
        )
        conn.commit()
        count = result.rowcount
        conn.close()
        return count
