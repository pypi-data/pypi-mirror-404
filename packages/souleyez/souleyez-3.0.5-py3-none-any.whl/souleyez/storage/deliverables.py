"""
Deliverable tracking and acceptance criteria management.
"""

from typing import Dict, List, Optional

from .database import get_db


class DeliverableManager:
    """Manage engagement deliverables and acceptance criteria."""

    def __init__(self):
        self.db = get_db()

    def add_deliverable(
        self,
        engagement_id: int,
        category: str,
        title: str,
        description: str = None,
        target_type: str = "manual",
        target_value: int = None,
        auto_validate: bool = False,
        validation_query: str = None,
        priority: str = "medium",
    ) -> int:
        """
        Add a deliverable to an engagement.

        Args:
            engagement_id: Engagement ID
            category: Category (reconnaissance, enumeration, exploitation, post_exploitation, techniques)
            title: Deliverable title (e.g., "Enumerate 5+ users")
            description: Optional description
            target_type: 'count', 'boolean', or 'manual'
            target_value: Target value for count types
            auto_validate: Enable automatic validation
            validation_query: SQL query for auto-validation
            priority: 'critical', 'high', 'medium', 'low'

        Returns:
            Deliverable ID
        """
        deliverable_id = self.db.insert(
            "deliverables",
            {
                "engagement_id": engagement_id,
                "category": category,
                "title": title,
                "description": description,
                "target_type": target_type,
                "target_value": target_value,
                "auto_validate": auto_validate,
                "validation_query": validation_query,
                "priority": priority,
            },
        )

        return deliverable_id

    def list_deliverables(
        self, engagement_id: int, category: str = None, status: str = None
    ) -> List[Dict]:
        """
        List deliverables for engagement.

        Args:
            engagement_id: Engagement ID
            category: Optional filter by category
            status: Optional filter by status

        Returns:
            List of deliverable records
        """
        query = "SELECT * FROM deliverables WHERE engagement_id = ?"
        params = [engagement_id]

        if category:
            query += " AND category = ?"
            params.append(category)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY priority DESC, created_at ASC"

        return self.db.execute(query, tuple(params))

    def get_deliverable(self, deliverable_id: int) -> Optional[Dict]:
        """Get deliverable by ID."""
        return self.db.execute_one(
            "SELECT * FROM deliverables WHERE id = ?", (deliverable_id,)
        )

    def update_deliverable(
        self,
        deliverable_id: int,
        current_value: int = None,
        status: str = None,
        completed_at: str = None,
    ) -> bool:
        """Update deliverable progress."""
        updates = {}

        if current_value is not None:
            updates["current_value"] = current_value

        if status:
            updates["status"] = status

        if completed_at:
            updates["completed_at"] = completed_at

        if not updates:
            return False

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [deliverable_id]

        self.db.execute(
            f"UPDATE deliverables SET {set_clause} WHERE id = ?", tuple(values)
        )

        return True

    def mark_complete(self, deliverable_id: int) -> bool:
        """Mark deliverable as completed."""
        from datetime import datetime

        return self.update_deliverable(
            deliverable_id, status="completed", completed_at=datetime.now().isoformat()
        )

    def mark_failed(self, deliverable_id: int) -> bool:
        """Mark deliverable as failed."""
        return self.update_deliverable(deliverable_id, status="failed")

    def validate_all(self, engagement_id: int) -> Dict:
        """
        Validate all auto-validated deliverables for engagement.

        Returns:
            {
                'updated': 5,
                'completed': 2,
                'in_progress': 3,
                'failed': 0
            }
        """
        deliverables = self.list_deliverables(engagement_id)
        stats = {
            "updated": 0,
            "completed": 0,
            "in_progress": 0,
            "pending": 0,
            "failed": 0,
        }

        for d in deliverables:
            if not d["auto_validate"]:
                continue

            result = self._validate_deliverable(d)

            if result["updated"]:
                stats["updated"] += 1
                stats[result["status"]] += 1

        return stats

    def _validate_deliverable(self, deliverable: Dict) -> Dict:
        """
        Validate a single deliverable.

        Returns:
            {
                'updated': True/False,
                'current_value': 5,
                'target_value': 10,
                'status': 'in_progress'
            }
        """
        if not deliverable["validation_query"]:
            return {"updated": False}

        try:
            result = self.db.execute_one(deliverable["validation_query"])

            if not result:
                return {"updated": False}

            current_value = result.get("count") or result.get("value") or 0

            target_type = deliverable["target_type"]
            target_value = deliverable["target_value"]

            if target_type == "count":
                if current_value >= target_value:
                    status = "completed"
                elif current_value > 0:
                    status = "in_progress"
                else:
                    status = "pending"
            elif target_type == "boolean":
                status = "completed" if current_value > 0 else "pending"
            else:
                status = "pending"

            completed_at = None
            if status == "completed" and deliverable["status"] != "completed":
                from datetime import datetime

                completed_at = datetime.now().isoformat()

            self.update_deliverable(
                deliverable["id"],
                current_value=current_value,
                status=status,
                completed_at=completed_at,
            )

            return {
                "updated": True,
                "current_value": current_value,
                "target_value": target_value,
                "status": status,
            }

        except Exception as e:
            print(f"Validation error for deliverable {deliverable['id']}: {e}")
            return {"updated": False}

    def get_summary(self, engagement_id: int) -> Dict:
        """
        Get deliverable summary for engagement.

        Returns:
            {
                'total': 10,
                'completed': 5,
                'in_progress': 3,
                'pending': 2,
                'failed': 0,
                'completion_rate': 0.5,
                'by_category': {...}
            }
        """
        deliverables = self.list_deliverables(engagement_id)

        summary = {
            "total": len(deliverables),
            "completed": 0,
            "in_progress": 0,
            "pending": 0,
            "failed": 0,
            "by_category": {},
        }

        for d in deliverables:
            status = d["status"]
            summary[status] += 1

            category = d["category"]
            if category not in summary["by_category"]:
                summary["by_category"][category] = {
                    "total": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "pending": 0,
                }

            summary["by_category"][category]["total"] += 1
            summary["by_category"][category][status] += 1

        if summary["total"] > 0:
            summary["completion_rate"] = summary["completed"] / summary["total"]
        else:
            summary["completion_rate"] = 0.0

        return summary

    def create_default_deliverables(self, engagement_id: int) -> int:
        """
        Create default deliverables for a new engagement.

        Returns:
            Number of deliverables created
        """
        defaults = [
            {
                "category": "reconnaissance",
                "title": "Identify 5+ live hosts",
                "target_type": "count",
                "target_value": 5,
                "auto_validate": True,
                "validation_query": f"SELECT COUNT(*) as count FROM hosts WHERE engagement_id = {engagement_id} AND status = 'up'",
                "priority": "high",
            },
            {
                "category": "reconnaissance",
                "title": "Enumerate 10+ services",
                "target_type": "count",
                "target_value": 10,
                "auto_validate": True,
                "validation_query": f"SELECT COUNT(*) as count FROM services s JOIN hosts h ON s.host_id = h.id WHERE h.engagement_id = {engagement_id}",
                "priority": "medium",
            },
            {
                "category": "enumeration",
                "title": "Enumerate 5+ user accounts",
                "target_type": "count",
                "target_value": 5,
                "auto_validate": True,
                "validation_query": f"SELECT COUNT(DISTINCT username) as count FROM credentials WHERE engagement_id = {engagement_id} AND username IS NOT NULL",
                "priority": "high",
            },
            {
                "category": "exploitation",
                "title": "Obtain 3+ valid credentials",
                "target_type": "count",
                "target_value": 3,
                "auto_validate": True,
                "validation_query": f"SELECT COUNT(*) as count FROM credentials WHERE engagement_id = {engagement_id} AND status = 'valid'",
                "priority": "critical",
            },
            {
                "category": "exploitation",
                "title": "Compromise 2+ hosts",
                "target_type": "count",
                "target_value": 2,
                "auto_validate": True,
                "validation_query": f"SELECT COUNT(*) as count FROM hosts WHERE engagement_id = {engagement_id} AND access_level != 'none'",
                "priority": "critical",
            },
            {
                "category": "post_exploitation",
                "title": "Extract database contents",
                "target_type": "count",
                "target_value": 1,
                "auto_validate": True,
                "validation_query": f"SELECT COUNT(*) as count FROM sqli_databases WHERE engagement_id = {engagement_id}",
                "priority": "high",
            },
            {
                "category": "techniques",
                "title": "Demonstrate privilege escalation",
                "target_type": "manual",
                "auto_validate": False,
                "priority": "high",
                "description": "Escalate from user to root/admin on at least one system",
            },
            {
                "category": "techniques",
                "title": "Perform lateral movement",
                "target_type": "manual",
                "auto_validate": False,
                "priority": "medium",
                "description": "Move from one compromised host to another",
            },
        ]

        count = 0
        for d in defaults:
            self.add_deliverable(engagement_id, **d)
            count += 1

        return count

    def delete_deliverable(self, deliverable_id: int) -> bool:
        """Delete a deliverable."""
        self.db.execute("DELETE FROM deliverables WHERE id = ?", (deliverable_id,))
        return True
