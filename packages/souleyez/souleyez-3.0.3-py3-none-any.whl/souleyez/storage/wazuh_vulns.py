#!/usr/bin/env python3
"""
souleyez.storage.wazuh_vulns - Wazuh vulnerabilities database operations

Stores vulnerabilities discovered by Wazuh agents for gap analysis
between passive (agent-based) and active (scan-based) detection.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from .database import get_db


class WazuhVulnsManager:
    """Manages Wazuh vulnerabilities in the database."""

    def __init__(self):
        self.db = get_db()

    def upsert_vulnerability(
        self,
        engagement_id: int,
        agent_id: str,
        cve_id: str,
        package_name: str = None,
        agent_name: str = None,
        agent_ip: str = None,
        name: str = None,
        severity: str = None,
        cvss_score: float = None,
        cvss_version: str = None,
        package_version: str = None,
        package_architecture: str = None,
        detection_time: datetime = None,
        published_date: str = None,
        reference_urls: List[str] = None,
        raw_data: dict = None,
    ) -> int:
        """
        Insert or update a Wazuh vulnerability.

        Uses UNIQUE constraint on (engagement_id, agent_id, cve_id, package_name)
        to prevent duplicates.

        Returns:
            Vulnerability ID
        """
        # Check for existing
        query = """
            SELECT id FROM wazuh_vulnerabilities
            WHERE engagement_id = ?
                AND agent_id = ?
                AND cve_id = ?
                AND COALESCE(package_name, '') = ?
        """
        existing = self.db.execute_one(
            query, (engagement_id, agent_id, cve_id, package_name or "")
        )

        data = {
            "engagement_id": engagement_id,
            "agent_id": agent_id,
            "cve_id": cve_id,
            "package_name": package_name,
            "agent_name": agent_name,
            "agent_ip": agent_ip,
            "name": name,
            "severity": severity,
            "cvss_score": cvss_score,
            "cvss_version": cvss_version,
            "package_version": package_version,
            "package_architecture": package_architecture,
            "detection_time": detection_time,
            "published_date": published_date,
            "reference_urls": json.dumps(reference_urls) if reference_urls else None,
            "raw_data": json.dumps(raw_data) if raw_data else None,
            "synced_at": datetime.now().isoformat(),
        }

        if existing:
            # Update existing
            vuln_id = existing["id"]
            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            update_query = f"UPDATE wazuh_vulnerabilities SET {set_clause} WHERE id = ?"
            params = list(data.values()) + [vuln_id]
            self.db.execute(update_query, tuple(params))
            return vuln_id
        else:
            # Insert new
            return self.db.insert("wazuh_vulnerabilities", data)

    def get_vulnerability(self, vuln_id: int) -> Optional[Dict[str, Any]]:
        """Get a vulnerability by ID."""
        query = "SELECT * FROM wazuh_vulnerabilities WHERE id = ?"
        result = self.db.execute_one(query, (vuln_id,))
        if result:
            return self._deserialize(result)
        return None

    def list_vulnerabilities(
        self,
        engagement_id: int,
        host_id: int = None,
        agent_id: str = None,
        agent_ip: str = None,
        severity: str = None,
        cve_id: str = None,
        status: str = None,
        verified_only: bool = False,
        limit: int = None,
    ) -> List[Dict[str, Any]]:
        """
        List vulnerabilities with optional filters.

        Args:
            engagement_id: Engagement ID
            host_id: Filter by mapped host ID
            agent_id: Filter by Wazuh agent ID
            agent_ip: Filter by agent IP
            severity: Filter by severity (Critical, High, Medium, Low)
            cve_id: Filter by CVE ID
            status: Filter by status (open, confirmed, exploited, false_positive)
            verified_only: Only show vulns verified by scan
            limit: Maximum results

        Returns:
            List of vulnerability dicts
        """
        query = """
            SELECT
                wv.*,
                h.ip_address as host_ip,
                h.hostname as host_name
            FROM wazuh_vulnerabilities wv
            LEFT JOIN hosts h ON wv.host_id = h.id
            WHERE wv.engagement_id = ?
        """
        params = [engagement_id]

        if host_id:
            query += " AND wv.host_id = ?"
            params.append(host_id)

        if agent_id:
            query += " AND wv.agent_id = ?"
            params.append(agent_id)

        if agent_ip:
            query += " AND wv.agent_ip = ?"
            params.append(agent_ip)

        if severity:
            query += " AND LOWER(wv.severity) = LOWER(?)"
            params.append(severity)

        if cve_id:
            query += " AND wv.cve_id LIKE ?"
            params.append(f"%{cve_id}%")

        if status:
            query += " AND wv.status = ?"
            params.append(status)

        if verified_only:
            query += " AND wv.verified_by_scan = 1"

        query += " ORDER BY wv.cvss_score DESC, wv.synced_at DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        results = self.db.execute(query, tuple(params))
        return [self._deserialize(r) for r in results]

    def get_summary(self, engagement_id: int) -> Dict[str, Any]:
        """
        Get summary of vulnerabilities by severity.

        Returns:
            Dict with counts and stats
        """
        query = """
            SELECT
                severity,
                COUNT(*) as count,
                SUM(CASE WHEN verified_by_scan = 1 THEN 1 ELSE 0 END) as verified_count
            FROM wazuh_vulnerabilities
            WHERE engagement_id = ?
            GROUP BY severity
        """
        results = self.db.execute(query, (engagement_id,))

        summary = {
            "total": 0,
            "verified": 0,
            "by_severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
        }

        for row in results:
            severity = row.get("severity", "Low")
            count = row.get("count", 0)
            verified = row.get("verified_count", 0)

            summary["total"] += count
            summary["verified"] += verified

            if severity in summary["by_severity"]:
                summary["by_severity"][severity] = count

        return summary

    def get_unique_cves(self, engagement_id: int) -> List[str]:
        """Get list of unique CVE IDs in engagement."""
        query = """
            SELECT DISTINCT cve_id
            FROM wazuh_vulnerabilities
            WHERE engagement_id = ? AND cve_id IS NOT NULL
            ORDER BY cve_id
        """
        results = self.db.execute(query, (engagement_id,))
        return [row["cve_id"] for row in results if row.get("cve_id")]

    def get_unique_agents(self, engagement_id: int) -> List[Dict[str, str]]:
        """Get list of unique agents with vuln counts."""
        query = """
            SELECT
                agent_id,
                agent_name,
                agent_ip,
                COUNT(*) as vuln_count
            FROM wazuh_vulnerabilities
            WHERE engagement_id = ?
            GROUP BY agent_id, agent_name, agent_ip
            ORDER BY vuln_count DESC
        """
        return self.db.execute(query, (engagement_id,))

    def update_status(
        self,
        vuln_id: int,
        status: str,
        verified_by_scan: bool = None,
        matched_finding_id: int = None,
    ) -> bool:
        """
        Update vulnerability status.

        Args:
            vuln_id: Vulnerability ID
            status: New status (open, confirmed, exploited, false_positive)
            verified_by_scan: Whether verified by active scan
            matched_finding_id: Link to matching finding from scan

        Returns:
            True if update succeeded
        """
        updates = {"status": status}

        if verified_by_scan is not None:
            updates["verified_by_scan"] = 1 if verified_by_scan else 0

        if matched_finding_id is not None:
            updates["matched_finding_id"] = matched_finding_id

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        query = f"UPDATE wazuh_vulnerabilities SET {set_clause} WHERE id = ?"
        params = list(updates.values()) + [vuln_id]

        try:
            self.db.execute(query, tuple(params))
            return True
        except Exception:
            return False

    def map_to_host(self, engagement_id: int, agent_ip: str, host_id: int) -> int:
        """
        Map all vulnerabilities from an agent IP to a host.

        Args:
            engagement_id: Engagement ID
            agent_ip: Agent IP address
            host_id: Host ID to map to

        Returns:
            Number of vulns updated
        """
        query = """
            UPDATE wazuh_vulnerabilities
            SET host_id = ?
            WHERE engagement_id = ? AND agent_ip = ?
        """
        self.db.execute(query, (host_id, engagement_id, agent_ip))

        # Get count of updated rows
        count_query = """
            SELECT COUNT(*) as count
            FROM wazuh_vulnerabilities
            WHERE engagement_id = ? AND agent_ip = ? AND host_id = ?
        """
        result = self.db.execute_one(count_query, (engagement_id, agent_ip, host_id))
        return result.get("count", 0) if result else 0

    def get_unmapped(self, engagement_id: int) -> List[Dict[str, Any]]:
        """Get vulnerabilities not mapped to any host."""
        query = """
            SELECT DISTINCT agent_id, agent_name, agent_ip, COUNT(*) as vuln_count
            FROM wazuh_vulnerabilities
            WHERE engagement_id = ? AND host_id IS NULL
            GROUP BY agent_id, agent_name, agent_ip
        """
        return self.db.execute(query, (engagement_id,))

    def delete_by_agent(self, engagement_id: int, agent_id: str) -> bool:
        """Delete all vulnerabilities from a specific agent."""
        try:
            self.db.execute(
                "DELETE FROM wazuh_vulnerabilities WHERE engagement_id = ? AND agent_id = ?",
                (engagement_id, agent_id),
            )
            return True
        except Exception:
            return False

    def delete_all(self, engagement_id: int) -> bool:
        """Delete all vulnerabilities for an engagement."""
        try:
            self.db.execute(
                "DELETE FROM wazuh_vulnerabilities WHERE engagement_id = ?",
                (engagement_id,),
            )
            return True
        except Exception:
            return False

    # Sync metadata operations

    def get_sync_status(self, engagement_id: int) -> Optional[Dict[str, Any]]:
        """Get last sync status for engagement."""
        query = "SELECT * FROM wazuh_vuln_sync WHERE engagement_id = ?"
        return self.db.execute_one(query, (engagement_id,))

    def update_sync_status(
        self,
        engagement_id: int,
        count: int,
        status: str = "success",
        errors: List[str] = None,
    ) -> None:
        """Update sync status after a sync operation."""
        existing = self.get_sync_status(engagement_id)

        data = {
            "engagement_id": engagement_id,
            "last_sync_at": datetime.now().isoformat(),
            "last_sync_count": count,
            "last_sync_status": status,
            "last_sync_errors": json.dumps(errors) if errors else None,
        }

        if existing:
            set_clause = ", ".join(
                [f"{k} = ?" for k in data.keys() if k != "engagement_id"]
            )
            query = f"UPDATE wazuh_vuln_sync SET {set_clause} WHERE engagement_id = ?"
            params = [v for k, v in data.items() if k != "engagement_id"] + [
                engagement_id
            ]
            self.db.execute(query, tuple(params))
        else:
            self.db.insert("wazuh_vuln_sync", data)

    def is_stale(self, engagement_id: int, max_age_hours: int = 1) -> bool:
        """
        Check if sync data is stale and needs refresh.

        Args:
            engagement_id: Engagement ID
            max_age_hours: Maximum age in hours before considered stale

        Returns:
            True if stale or never synced
        """
        sync_status = self.get_sync_status(engagement_id)

        if not sync_status or not sync_status.get("last_sync_at"):
            return True

        last_sync = sync_status["last_sync_at"]
        if isinstance(last_sync, str):
            try:
                last_sync = datetime.fromisoformat(last_sync)
            except ValueError:
                return True

        age = datetime.now() - last_sync
        return age.total_seconds() > (max_age_hours * 3600)

    def _deserialize(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize JSON fields."""
        result = dict(row)

        if result.get("reference_urls"):
            try:
                result["reference_urls"] = json.loads(result["reference_urls"])
            except (json.JSONDecodeError, TypeError):
                result["reference_urls"] = []

        if result.get("raw_data"):
            try:
                result["raw_data"] = json.loads(result["raw_data"])
            except (json.JSONDecodeError, TypeError):
                result["raw_data"] = {}

        return result
