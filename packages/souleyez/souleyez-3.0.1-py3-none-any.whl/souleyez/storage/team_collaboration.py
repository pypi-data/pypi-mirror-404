"""
Team collaboration features for deliverables.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from .database import get_db


class TeamCollaboration:
    """Manage team collaboration on deliverables."""

    def __init__(self):
        self.db = get_db()

    def _get_current_user(self) -> str:
        """Get current username from environment or system."""
        # Try environment variable first
        user = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
        return user

    def log_activity(
        self,
        deliverable_id: int,
        engagement_id: int,
        action: str,
        details: str = None,
        user: str = None,
    ) -> int:
        """
        Log activity on a deliverable.

        Args:
            deliverable_id: Deliverable ID
            engagement_id: Engagement ID
            action: Action type (started, completed, updated, assigned, etc.)
            details: Additional details
            user: Username (defaults to current user)

        Returns:
            Activity log ID
        """
        if user is None:
            user = self._get_current_user()

        activity_id = self.db.insert(
            "deliverable_activity",
            {
                "deliverable_id": deliverable_id,
                "engagement_id": engagement_id,
                "user": user,
                "action": action,
                "details": details,
            },
        )

        return activity_id

    def get_activity(
        self,
        deliverable_id: int = None,
        engagement_id: int = None,
        user: str = None,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Get activity log.

        Args:
            deliverable_id: Filter by deliverable
            engagement_id: Filter by engagement
            user: Filter by user
            limit: Max results

        Returns:
            List of activity records
        """
        query = """
            SELECT 
                da.*,
                d.title as deliverable_title,
                d.category as deliverable_category
            FROM deliverable_activity da
            LEFT JOIN deliverables d ON da.deliverable_id = d.id
            WHERE 1=1
        """
        params = []

        if deliverable_id:
            query += " AND da.deliverable_id = ?"
            params.append(deliverable_id)

        if engagement_id:
            query += " AND da.engagement_id = ?"
            params.append(engagement_id)

        if user:
            query += " AND da.user = ?"
            params.append(user)

        query += " ORDER BY da.created_at DESC LIMIT ?"
        params.append(limit)

        return self.db.execute(query, tuple(params))

    def add_comment(self, deliverable_id: int, comment: str, user: str = None) -> int:
        """
        Add comment to deliverable.

        Args:
            deliverable_id: Deliverable ID
            comment: Comment text
            user: Username (defaults to current user)

        Returns:
            Comment ID
        """
        if user is None:
            user = self._get_current_user()

        comment_id = self.db.insert(
            "deliverable_comments",
            {"deliverable_id": deliverable_id, "user": user, "comment": comment},
        )

        return comment_id

    def get_comments(self, deliverable_id: int) -> List[Dict]:
        """
        Get comments for deliverable.

        Args:
            deliverable_id: Deliverable ID

        Returns:
            List of comments
        """
        return self.db.execute(
            """
            SELECT * FROM deliverable_comments
            WHERE deliverable_id = ?
            ORDER BY created_at ASC
            """,
            (deliverable_id,),
        )

    def delete_comment(self, comment_id: int, user: str = None) -> bool:
        """
        Delete comment (only by original author).

        Args:
            comment_id: Comment ID
            user: Username (defaults to current user)

        Returns:
            True if deleted
        """
        if user is None:
            user = self._get_current_user()

        # Verify ownership
        comment = self.db.execute_one(
            "SELECT user FROM deliverable_comments WHERE id = ?", (comment_id,)
        )

        if not comment or comment["user"] != user:
            return False

        self.db.execute("DELETE FROM deliverable_comments WHERE id = ?", (comment_id,))

        return True

    def assign_deliverable(
        self,
        deliverable_id: int,
        engagement_id: int,
        assigned_to: str,
        assigned_by: str = None,
    ) -> bool:
        """
        Assign deliverable to user.

        Args:
            deliverable_id: Deliverable ID
            engagement_id: Engagement ID
            assigned_to: Username to assign to
            assigned_by: Username doing assignment

        Returns:
            True if successful
        """
        if assigned_by is None:
            assigned_by = self._get_current_user()

        # Update deliverable
        self.db.execute(
            "UPDATE deliverables SET assigned_to = ? WHERE id = ?",
            (assigned_to, deliverable_id),
        )

        # Log activity
        details = (
            f"Assigned to {assigned_to}"
            if assigned_by != assigned_to
            else "Self-assigned"
        )
        self.log_activity(
            deliverable_id=deliverable_id,
            engagement_id=engagement_id,
            action="assigned",
            details=details,
            user=assigned_by,
        )

        return True

    def unassign_deliverable(
        self, deliverable_id: int, engagement_id: int, user: str = None
    ) -> bool:
        """
        Unassign deliverable.

        Args:
            deliverable_id: Deliverable ID
            engagement_id: Engagement ID
            user: Username doing unassignment

        Returns:
            True if successful
        """
        if user is None:
            user = self._get_current_user()

        # Update deliverable
        self.db.execute(
            "UPDATE deliverables SET assigned_to = NULL WHERE id = ?", (deliverable_id,)
        )

        # Log activity
        self.log_activity(
            deliverable_id=deliverable_id,
            engagement_id=engagement_id,
            action="unassigned",
            details="Unassigned",
            user=user,
        )

        return True

    def get_team_summary(self, engagement_id: int) -> Dict:
        """
        Get team activity summary for engagement.

        Returns:
            Dict with team statistics
        """
        # Get unique users
        users = self.db.execute(
            """
            SELECT DISTINCT user
            FROM deliverable_activity
            WHERE engagement_id = ?
            """,
            (engagement_id,),
        )

        user_list = [u["user"] for u in users]

        # Get activity count per user
        user_activity = {}
        for user_row in users:
            user = user_row["user"]

            # Count activities
            activity_count = self.db.execute_one(
                """
                SELECT COUNT(*) as count
                FROM deliverable_activity
                WHERE engagement_id = ? AND user = ?
                """,
                (engagement_id, user),
            )

            # Count assignments
            assigned_count = self.db.execute_one(
                """
                SELECT COUNT(*) as count
                FROM deliverables
                WHERE engagement_id = ? AND assigned_to = ?
                """,
                (engagement_id, user),
            )

            # Count completed
            completed_count = self.db.execute_one(
                """
                SELECT COUNT(*) as count
                FROM deliverables
                WHERE engagement_id = ? AND assigned_to = ? AND status = 'completed'
                """,
                (engagement_id, user),
            )

            user_activity[user] = {
                "activity_count": activity_count["count"] if activity_count else 0,
                "assigned_count": assigned_count["count"] if assigned_count else 0,
                "completed_count": completed_count["count"] if completed_count else 0,
            }

        return {
            "users": user_list,
            "user_activity": user_activity,
            "total_users": len(user_list),
        }

    def get_user_workload(self, engagement_id: int) -> List[Dict]:
        """
        Get workload per user.

        Returns:
            List of users with workload stats
        """
        workload = self.db.execute(
            """
            SELECT 
                assigned_to as user,
                COUNT(*) as total_assigned,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN blocker IS NOT NULL AND blocker != '' THEN 1 ELSE 0 END) as blocked
            FROM deliverables
            WHERE engagement_id = ? AND assigned_to IS NOT NULL AND assigned_to != ''
            GROUP BY assigned_to
            ORDER BY total_assigned DESC
            """,
            (engagement_id,),
        )

        return workload

    def get_recent_activity_feed(
        self, engagement_id: int, limit: int = 20
    ) -> List[Dict]:
        """
        Get recent activity feed with formatted messages.

        Returns:
            List of activity items with human-readable messages
        """
        activities = self.get_activity(engagement_id=engagement_id, limit=limit)

        feed = []
        for activity in activities:
            # Format message based on action
            action = activity["action"]
            user = activity["user"]
            title = activity.get("deliverable_title", "Unknown")
            details = activity.get("details", "")
            created_at = activity["created_at"]

            if action == "started":
                message = f"{user} started '{title}'"
            elif action == "completed":
                message = f"{user} completed '{title}'"
            elif action == "updated":
                message = f"{user} updated '{title}'"
                if details:
                    message += f" ({details})"
            elif action == "assigned":
                message = f"{user} {details} for '{title}'"
            elif action == "unassigned":
                message = f"{user} unassigned '{title}'"
            elif action == "blocker_set":
                message = f"{user} set blocker on '{title}': {details}"
            elif action == "blocker_cleared":
                message = f"{user} cleared blocker on '{title}'"
            elif action == "evidence_linked":
                message = f"{user} linked evidence to '{title}'"
                if details:
                    message += f" ({details})"
            elif action == "commented":
                message = f"{user} commented on '{title}'"
            else:
                message = f"{user} {action} '{title}'"

            feed.append(
                {
                    "id": activity["id"],
                    "message": message,
                    "action": action,
                    "user": user,
                    "deliverable_id": activity["deliverable_id"],
                    "created_at": created_at,
                    "details": details,
                }
            )

        return feed
