"""
Timeline tracking and velocity calculations for deliverables.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .database import get_db


class TimelineTracker:
    """Track time spent on deliverables and predict completion."""

    def __init__(self):
        self.db = get_db()

    def start_deliverable(self, deliverable_id: int):
        """Mark deliverable as started (sets started_at timestamp)."""
        self.db.execute(
            "UPDATE deliverables SET started_at = CURRENT_TIMESTAMP, status = 'in_progress' WHERE id = ?",
            (deliverable_id,),
        )

        # Log activity
        try:
            from .team_collaboration import TeamCollaboration

            deliverable = self.db.execute_one(
                "SELECT engagement_id FROM deliverables WHERE id = ?", (deliverable_id,)
            )
            if deliverable:
                tc = TeamCollaboration()
                tc.log_activity(deliverable_id, deliverable["engagement_id"], "started")
        except:
            pass  # Fail silently if team collaboration not available

    def complete_deliverable(self, deliverable_id: int, actual_hours: float = None):
        """
        Mark deliverable as completed.

        Args:
            deliverable_id: Target deliverable
            actual_hours: Optional manual time entry (hours)
        """
        if actual_hours is not None:
            self.db.execute(
                """UPDATE deliverables 
                   SET completed_at = CURRENT_TIMESTAMP, 
                       status = 'completed',
                       actual_hours = ?
                   WHERE id = ?""",
                (actual_hours, deliverable_id),
            )
        else:
            # Auto-calculate from started_at
            deliverable = self.db.execute_one(
                "SELECT started_at, engagement_id FROM deliverables WHERE id = ?",
                (deliverable_id,),
            )

            engagement_id = deliverable.get("engagement_id") if deliverable else None

            if deliverable and deliverable.get("started_at"):
                started = datetime.fromisoformat(
                    deliverable["started_at"].replace("Z", "+00:00")
                )
                completed = datetime.now()
                hours = (completed - started).total_seconds() / 3600

                self.db.execute(
                    """UPDATE deliverables 
                       SET completed_at = CURRENT_TIMESTAMP,
                           status = 'completed',
                           actual_hours = ?
                       WHERE id = ?""",
                    (hours, deliverable_id),
                )
            else:
                # No started_at, just mark complete
                self.db.execute(
                    "UPDATE deliverables SET completed_at = CURRENT_TIMESTAMP, status = 'completed' WHERE id = ?",
                    (deliverable_id,),
                )

        # Log activity
        try:
            from .team_collaboration import TeamCollaboration

            deliverable = self.db.execute_one(
                "SELECT engagement_id FROM deliverables WHERE id = ?", (deliverable_id,)
            )
            if deliverable:
                tc = TeamCollaboration()
                tc.log_activity(
                    deliverable_id, deliverable["engagement_id"], "completed"
                )
        except:
            pass  # Fail silently

    def set_blocker(self, deliverable_id: int, blocker: str):
        """Set blocker text for a deliverable."""
        self.db.execute(
            "UPDATE deliverables SET blocker = ?, status = 'pending' WHERE id = ?",
            (blocker, deliverable_id),
        )

    def clear_blocker(self, deliverable_id: int):
        """Clear blocker for a deliverable."""
        self.db.execute(
            "UPDATE deliverables SET blocker = NULL WHERE id = ?", (deliverable_id,)
        )

    def get_phase_breakdown(self, engagement_id: int) -> Dict:
        """
        Get time breakdown by PTES phase.

        Returns:
            Dict with phase stats (count, completed, hours, etc.)
        """
        phases = [
            "reconnaissance",
            "enumeration",
            "exploitation",
            "post_exploitation",
            "techniques",
        ]

        breakdown = {}

        for phase in phases:
            deliverables = self.db.execute(
                """SELECT COUNT(*) as total,
                          SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                          SUM(estimated_hours) as estimated_hours,
                          SUM(actual_hours) as actual_hours
                   FROM deliverables 
                   WHERE engagement_id = ? AND category = ?""",
                (engagement_id, phase),
            )

            if deliverables:
                stats = deliverables[0]
                breakdown[phase] = {
                    "total": stats["total"] or 0,
                    "completed": stats["completed"] or 0,
                    "estimated_hours": stats["estimated_hours"] or 0,
                    "actual_hours": stats["actual_hours"] or 0,
                    "completion_rate": (
                        (stats["completed"] / stats["total"] * 100)
                        if stats["total"] > 0
                        else 0
                    ),
                }

        return breakdown

    def calculate_velocity(self, engagement_id: int) -> Dict:
        """
        Calculate delivery velocity (deliverables per hour).

        Returns:
            Dict with velocity metrics
        """
        stats = self.db.execute_one(
            """SELECT 
                   COUNT(*) as total_deliverables,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_deliverables,
                   SUM(actual_hours) as total_hours,
                   AVG(actual_hours) as avg_hours_per_deliverable
               FROM deliverables 
               WHERE engagement_id = ? AND actual_hours > 0""",
            (engagement_id,),
        )

        if not stats or not stats["total_hours"]:
            return {
                "velocity": 0,
                "avg_hours_per_deliverable": 0,
                "total_hours": 0,
                "completed_deliverables": 0,
            }

        velocity = (
            stats["completed_deliverables"] / stats["total_hours"]
            if stats["total_hours"] > 0
            else 0
        )

        return {
            "velocity": velocity,  # deliverables per hour
            "avg_hours_per_deliverable": stats["avg_hours_per_deliverable"] or 0,
            "total_hours": stats["total_hours"] or 0,
            "completed_deliverables": stats["completed_deliverables"] or 0,
        }

    def project_completion(self, engagement_id: int) -> Dict:
        """
        Project completion date based on current velocity.

        Returns:
            Dict with projection data
        """
        # Get total and remaining deliverables
        totals = self.db.execute_one(
            """SELECT 
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                   SUM(CASE WHEN status != 'completed' THEN 1 ELSE 0 END) as remaining
               FROM deliverables 
               WHERE engagement_id = ?""",
            (engagement_id,),
        )

        if not totals or totals["remaining"] == 0:
            return {
                "status": "complete",
                "remaining_deliverables": 0,
                "projected_hours": 0,
                "projected_date": None,
            }

        velocity = self.calculate_velocity(engagement_id)

        if velocity["velocity"] == 0:
            # No historical data, use average estimate
            avg_estimate = velocity["avg_hours_per_deliverable"]
            if avg_estimate == 0:
                avg_estimate = 2.0  # Default assumption: 2 hours per deliverable

            projected_hours = totals["remaining"] * avg_estimate
        else:
            # Use velocity to project
            projected_hours = totals["remaining"] / velocity["velocity"]

        # Calculate projected completion date (assuming 8-hour work days)
        work_days = projected_hours / 8
        projected_date = datetime.now() + timedelta(days=work_days)

        return {
            "status": "in_progress",
            "remaining_deliverables": totals["remaining"],
            "projected_hours": round(projected_hours, 1),
            "projected_days": round(work_days, 1),
            "projected_date": projected_date.strftime("%Y-%m-%d"),
            "velocity": round(velocity["velocity"], 2),
        }

    def get_blockers(self, engagement_id: int) -> List[Dict]:
        """Get all deliverables with blockers."""
        return self.db.execute(
            """SELECT id, title, blocker, priority
               FROM deliverables 
               WHERE engagement_id = ? AND blocker IS NOT NULL AND blocker != ''
               ORDER BY 
                   CASE priority 
                       WHEN 'critical' THEN 1
                       WHEN 'high' THEN 2
                       WHEN 'medium' THEN 3
                       WHEN 'low' THEN 4
                       ELSE 5
                   END""",
            (engagement_id,),
        )

    def get_in_progress(self, engagement_id: int) -> List[Dict]:
        """Get all in-progress deliverables with time stats."""
        return self.db.execute(
            """SELECT id, title, category, priority, started_at, estimated_hours, actual_hours
               FROM deliverables 
               WHERE engagement_id = ? AND status = 'in_progress'
               ORDER BY started_at DESC""",
            (engagement_id,),
        )

    def get_timeline_summary(self, engagement_id: int) -> Dict:
        """Get comprehensive timeline summary."""
        phase_breakdown = self.get_phase_breakdown(engagement_id)
        velocity = self.calculate_velocity(engagement_id)
        projection = self.project_completion(engagement_id)
        blockers = self.get_blockers(engagement_id)
        in_progress = self.get_in_progress(engagement_id)

        return {
            "phase_breakdown": phase_breakdown,
            "velocity": velocity,
            "projection": projection,
            "blockers": blockers,
            "in_progress": in_progress,
        }

    def update_engagement_hours(self, engagement_id: int):
        """Update total hours on engagement based on deliverables."""
        stats = self.db.execute_one(
            """SELECT 
                   SUM(estimated_hours) as total_estimated,
                   SUM(actual_hours) as total_actual
               FROM deliverables 
               WHERE engagement_id = ?""",
            (engagement_id,),
        )

        if stats:
            self.db.execute(
                """UPDATE engagements 
                   SET estimated_hours = ?, actual_hours = ?
                   WHERE id = ?""",
                (
                    stats["total_estimated"] or 0,
                    stats["total_actual"] or 0,
                    engagement_id,
                ),
            )
