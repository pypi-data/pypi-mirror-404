#!/usr/bin/env python3
"""
souleyez.storage.osint - OSINT data management
"""

from typing import Any, Dict, List, Optional

from .database import get_db


class OsintManager:
    """Manages OSINT data (emails, subdomains, URLs, etc.) in the database."""

    def __init__(self):
        self.db = get_db()

    def add_osint_data(
        self,
        engagement_id: int,
        data_type: str,
        value: str,
        source: str = None,
        target: str = None,
        summary: str = None,
        content: str = None,
        metadata: str = None,
    ) -> int:
        """
        Add OSINT data to the database.

        Args:
            engagement_id: Engagement ID
            data_type: Type of data (email, host, ip, url, asn, domain_info, etc.)
            value: The actual data value (simple) or target identifier
            source: Source tool/method (e.g., 'theHarvester', 'whois')
            target: The domain/URL this data was collected for
            summary: Optional brief summary of the data
            content: Optional full content/details (JSON or text)
            metadata: Optional additional metadata (JSON)

        Returns:
            OSINT data ID
        """
        # Check if this exact entry already exists
        existing = self.db.execute_one(
            "SELECT id FROM osint_data WHERE engagement_id = ? AND data_type = ? AND value = ?",
            (engagement_id, data_type, value),
        )

        if existing:
            # Update source and other fields if provided
            updates = []
            params = []
            if source:
                updates.append("source = ?")
                params.append(source)
            if target:
                updates.append("target = ?")
                params.append(target)
            if summary:
                updates.append("summary = ?")
                params.append(summary)
            if content:
                updates.append("content = ?")
                params.append(content)
            if metadata:
                updates.append("metadata = ?")
                params.append(metadata)

            if updates:
                params.append(existing["id"])
                self.db.execute(
                    f"UPDATE osint_data SET {', '.join(updates)} WHERE id = ?",
                    tuple(params),
                )
            return existing["id"]

        # Insert new data
        data = {"engagement_id": engagement_id, "data_type": data_type, "value": value}

        if source:
            data["source"] = source
        if target:
            data["target"] = target
        if summary:
            data["summary"] = summary
        if content:
            data["content"] = content
        if metadata:
            data["metadata"] = metadata

        return self.db.insert("osint_data", data)

    def bulk_add_osint_data(
        self,
        engagement_id: int,
        data_type: str,
        values: List[str],
        source: str = None,
        target: str = None,
    ) -> int:
        """
        Add multiple OSINT data entries of the same type.

        Args:
            engagement_id: Engagement ID
            data_type: Type of data
            values: List of values to add
            source: Source tool/method
            target: The domain/URL this data was collected for

        Returns:
            Number of new entries added
        """
        count = 0
        for value in values:
            # Check if exists
            existing = self.db.execute_one(
                "SELECT id FROM osint_data WHERE engagement_id = ? AND data_type = ? AND value = ?",
                (engagement_id, data_type, value),
            )
            if not existing:
                self.add_osint_data(engagement_id, data_type, value, source, target)
                count += 1
        return count

    def get_osint_data(self, osint_id: int) -> Optional[Dict[str, Any]]:
        """Get OSINT data by ID."""
        query = "SELECT * FROM osint_data WHERE id = ?"
        return self.db.execute_one(query, (osint_id,))

    def list_osint_data(
        self, engagement_id: int, data_type: str = None, source: str = None
    ) -> List[Dict[str, Any]]:
        """
        List OSINT data with optional filters.

        Args:
            engagement_id: Engagement ID
            data_type: Filter by data type (optional)
            source: Filter by source (optional)

        Returns:
            List of OSINT data dicts
        """
        query = "SELECT * FROM osint_data WHERE engagement_id = ?"
        params = [engagement_id]

        if data_type:
            query += " AND data_type = ?"
            params.append(data_type)

        if source:
            query += " AND source = ?"
            params.append(source)

        query += " ORDER BY created_at DESC"

        return self.db.execute(query, tuple(params))

    def get_osint_summary(self, engagement_id: int) -> Dict[str, int]:
        """
        Get summary of OSINT data by type.

        Returns:
            Dict with counts: {'email': 10, 'host': 25, ...}
        """
        query = """
            SELECT data_type, COUNT(*) as count
            FROM osint_data
            WHERE engagement_id = ?
            GROUP BY data_type
        """
        results = self.db.execute(query, (engagement_id,))

        summary = {}
        for row in results:
            data_type = row.get("data_type", "unknown")
            count = row.get("count", 0)
            summary[data_type] = count

        return summary

    def delete_osint_data(self, osint_id: int) -> bool:
        """Delete OSINT data entry."""
        try:
            self.db.execute("DELETE FROM osint_data WHERE id = ?", (osint_id,))
            return True
        except Exception:
            return False
