#!/usr/bin/env python3
"""
souleyez.integrations.wazuh.host_mapper - Map Wazuh agents to SoulEyez hosts

Maps Wazuh agent IPs to SoulEyez hosts for vulnerability correlation.
"""

from typing import Dict, List, Optional, Tuple

from souleyez.log_config import get_logger
from souleyez.storage.database import get_db

logger = get_logger(__name__)


class WazuhHostMapper:
    """Maps Wazuh agents to SoulEyez hosts by IP address."""

    def __init__(self):
        self.db = get_db()

    def map_agent_to_host(self, engagement_id: int, agent_ip: str) -> Optional[int]:
        """
        Find SoulEyez host_id matching an agent IP.

        Args:
            engagement_id: Engagement ID
            agent_ip: Wazuh agent IP address

        Returns:
            host_id if found, None otherwise
        """
        if not agent_ip:
            return None

        query = """
            SELECT id FROM hosts
            WHERE engagement_id = ? AND ip_address = ?
        """
        result = self.db.execute_one(query, (engagement_id, agent_ip))

        if result:
            return result["id"]

        return None

    def auto_map_all(self, engagement_id: int) -> Dict[str, Optional[int]]:
        """
        Map all Wazuh vulnerabilities to hosts by agent IP.

        Args:
            engagement_id: Engagement ID

        Returns:
            Dict mapping agent_ip -> host_id (or None if unmapped)
        """
        # Get all unique agent IPs from wazuh_vulnerabilities
        agent_query = """
            SELECT DISTINCT agent_ip
            FROM wazuh_vulnerabilities
            WHERE engagement_id = ? AND agent_ip IS NOT NULL
        """
        agents = self.db.execute(agent_query, (engagement_id,))

        mapping = {}
        for agent in agents:
            agent_ip = agent.get("agent_ip")
            if agent_ip:
                host_id = self.map_agent_to_host(engagement_id, agent_ip)
                mapping[agent_ip] = host_id

                # Update vulnerabilities with host_id
                if host_id:
                    self._update_vuln_host_mapping(engagement_id, agent_ip, host_id)

        return mapping

    def _update_vuln_host_mapping(
        self, engagement_id: int, agent_ip: str, host_id: int
    ) -> int:
        """
        Update all vulnerabilities from an agent IP with the host_id.

        Returns:
            Number of rows updated
        """
        query = """
            UPDATE wazuh_vulnerabilities
            SET host_id = ?
            WHERE engagement_id = ? AND agent_ip = ? AND (host_id IS NULL OR host_id != ?)
        """
        self.db.execute(query, (host_id, engagement_id, agent_ip, host_id))

        # Get count
        count_query = """
            SELECT COUNT(*) as count
            FROM wazuh_vulnerabilities
            WHERE engagement_id = ? AND agent_ip = ? AND host_id = ?
        """
        result = self.db.execute_one(count_query, (engagement_id, agent_ip, host_id))
        return result.get("count", 0) if result else 0

    def get_unmapped_agents(self, engagement_id: int) -> List[Dict[str, any]]:
        """
        List agent IPs that couldn't be mapped to hosts.

        Returns:
            List of dicts with agent info and vuln counts
        """
        query = """
            SELECT
                agent_id,
                agent_name,
                agent_ip,
                COUNT(*) as vuln_count
            FROM wazuh_vulnerabilities
            WHERE engagement_id = ? AND host_id IS NULL
            GROUP BY agent_id, agent_name, agent_ip
            ORDER BY vuln_count DESC
        """
        return self.db.execute(query, (engagement_id,))

    def get_mapped_agents(self, engagement_id: int) -> List[Dict[str, any]]:
        """
        List agent IPs that are mapped to hosts.

        Returns:
            List of dicts with agent info, host info, and vuln counts
        """
        query = """
            SELECT
                wv.agent_id,
                wv.agent_name,
                wv.agent_ip,
                wv.host_id,
                h.hostname as host_name,
                COUNT(*) as vuln_count
            FROM wazuh_vulnerabilities wv
            JOIN hosts h ON wv.host_id = h.id
            WHERE wv.engagement_id = ? AND wv.host_id IS NOT NULL
            GROUP BY wv.agent_id, wv.agent_name, wv.agent_ip, wv.host_id, h.hostname
            ORDER BY vuln_count DESC
        """
        return self.db.execute(query, (engagement_id,))

    def get_mapping_stats(self, engagement_id: int) -> Dict[str, int]:
        """
        Get mapping statistics.

        Returns:
            Dict with counts of mapped/unmapped vulns
        """
        query = """
            SELECT
                SUM(CASE WHEN host_id IS NOT NULL THEN 1 ELSE 0 END) as mapped,
                SUM(CASE WHEN host_id IS NULL THEN 1 ELSE 0 END) as unmapped,
                COUNT(*) as total
            FROM wazuh_vulnerabilities
            WHERE engagement_id = ?
        """
        result = self.db.execute_one(query, (engagement_id,))

        if result:
            return {
                "mapped": result.get("mapped", 0) or 0,
                "unmapped": result.get("unmapped", 0) or 0,
                "total": result.get("total", 0) or 0,
            }

        return {"mapped": 0, "unmapped": 0, "total": 0}

    def manual_map(
        self, engagement_id: int, agent_ip: str, host_id: int
    ) -> Tuple[bool, int]:
        """
        Manually map an agent IP to a host.

        Args:
            engagement_id: Engagement ID
            agent_ip: Agent IP to map
            host_id: Host ID to map to

        Returns:
            Tuple of (success, vulns_updated)
        """
        # Verify host exists
        host_query = "SELECT id FROM hosts WHERE id = ? AND engagement_id = ?"
        host = self.db.execute_one(host_query, (host_id, engagement_id))

        if not host:
            logger.warning(f"Host {host_id} not found in engagement {engagement_id}")
            return (False, 0)

        # Update all vulns with this agent IP
        count = self._update_vuln_host_mapping(engagement_id, agent_ip, host_id)

        logger.info(f"Mapped agent {agent_ip} to host {host_id}, updated {count} vulns")
        return (True, count)

    def unmap(self, engagement_id: int, agent_ip: str) -> int:
        """
        Remove host mapping for an agent IP.

        Returns:
            Number of vulns updated
        """
        query = """
            UPDATE wazuh_vulnerabilities
            SET host_id = NULL
            WHERE engagement_id = ? AND agent_ip = ?
        """
        self.db.execute(query, (engagement_id, agent_ip))

        count_query = """
            SELECT COUNT(*) as count
            FROM wazuh_vulnerabilities
            WHERE engagement_id = ? AND agent_ip = ? AND host_id IS NULL
        """
        result = self.db.execute_one(count_query, (engagement_id, agent_ip))
        return result.get("count", 0) if result else 0

    def suggest_mappings(self, engagement_id: int) -> List[Dict[str, any]]:
        """
        Suggest possible mappings for unmapped agents based on IP similarity.

        This helps when agents have slightly different IPs (e.g., NAT situations).

        Returns:
            List of suggestions with agent_ip, possible_host_id, confidence
        """
        # Get unmapped agent IPs
        unmapped = self.get_unmapped_agents(engagement_id)

        # Get all hosts in engagement
        hosts_query = """
            SELECT id, ip_address, hostname
            FROM hosts
            WHERE engagement_id = ?
        """
        hosts = self.db.execute(hosts_query, (engagement_id,))

        suggestions = []

        for agent in unmapped:
            agent_ip = agent.get("agent_ip")
            if not agent_ip:
                continue

            # Try to find hosts in same subnet
            agent_parts = agent_ip.split(".")
            if len(agent_parts) != 4:
                continue

            agent_subnet = ".".join(agent_parts[:3])

            for host in hosts:
                host_ip = host.get("ip_address")
                if not host_ip:
                    continue

                host_parts = host_ip.split(".")
                if len(host_parts) != 4:
                    continue

                host_subnet = ".".join(host_parts[:3])

                # Same subnet = possible match
                if agent_subnet == host_subnet:
                    suggestions.append(
                        {
                            "agent_ip": agent_ip,
                            "agent_name": agent.get("agent_name"),
                            "suggested_host_id": host["id"],
                            "suggested_host_ip": host_ip,
                            "suggested_host_name": host.get("hostname"),
                            "confidence": "medium",
                            "reason": "Same subnet",
                        }
                    )

        return suggestions
